// f24-book-appointment — Supabase Edge Function (Deno)
//
// Agenda llamadas de asesoría de Ferre24 contra los calendarios GHL (fuente de verdad de
// disponibilidad). Reemplaza el viejo R32 "prometo la llamada en texto y escalo por correo":
// ahora el bot ofrece SLOTS REALES y agenda la cita de verdad en el calendario del asesor.
//
// Dos modos (campo `mode`):
//   - "slots" (default): consulta free-slots reales del calendario del asesor y regresa los
//       próximos horarios disponibles + un `mensaje` natural listo para ofrecer al cliente.
//   - "book": crea la cita en el calendario del asesor a la hora elegida por el cliente.
//
// Ruteo de asesor = ROUND-ROBIN DETERMINÍSTICO por contacto: hash(contactId) % 2 → Alfredo/Edgar.
// Determinístico a propósito: los modos "slots" y "book" caen SIEMPRE en el mismo asesor sin
// guardar estado, y cada cliente queda con el mismo asesor. Reparto ~50/50.
//
// Patrón "siempre 200" (igual que f24-quote-shipping): aun con error regresa ok:false + un
// `mensaje` de fallback natural, para que el router de Make no se detenga y el cliente reciba algo.
//
// Input (POST JSON):
//   { mode?: "slots" | "book",
//     contact_id: "abc123",          // REQUERIDO (GHL contactId; define el asesor)
//     start_time?: "2026-07-10T10:00:00-06:00",  // REQUERIDO en mode=book (slot elegido)
//     producto?: "Generador GP3000M" }            // opcional, para el título de la cita
//
// Output slots: { ok, mode:"slots", asesor, calendar_id, slots:[{iso,label}], mensaje }
// Output book:  { ok, mode:"book", asesor, appointment_id, start_time, mensaje }
//
// Secrets (env): GHL_TOKEN (PIT F24, ya secret del proyecto — mismo que usa f24-process-order).

const GHL_BASE = "https://services.leadconnectorhq.com";
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const GHL_VERSION = "2021-04-15"; // versión de los endpoints de calendars
const LOCATION_ID = Deno.env.get("F24_LOCATION_ID") ?? "HNuSoIl2aCXP2DXEdMVZ";
const TIMEZONE = "America/Mexico_City";
const SLOT_MINUTES = 30;
// Cloudflare (que protege services.leadconnectorhq.com) devuelve 403 error-1010 a requests sin
// User-Agent de navegador. OBLIGATORIO en todo fetch a GHL (verificado empíricamente 2026-07-09).
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

// ── Asesores + sus calendarios GHL (fuente de verdad de disponibilidad) ────────────────────────
// Override por env sin redeploy. Orden fijo → índice 0/1 estable para el round-robin.
// user_id = usuario GHL del asesor → la cita se ASIGNA a él (aparece en SU calendario personal,
// no solo en el calendario de eventos compartido).
interface Asesor { key: string; name: string; calendar_id: string; user_id: string; }
const ASESORES: Asesor[] = [
  { key: "alfredo", name: "Alfredo", calendar_id: Deno.env.get("F24_CAL_ALFREDO") ?? "hnsAK3JB7w3loc8AV45v", user_id: Deno.env.get("F24_USER_ALFREDO") ?? "1Yee3JNNWlFSk6SWFzeT" },
  { key: "edgar", name: "Edgar", calendar_id: Deno.env.get("F24_CAL_EDGAR") ?? "dnd4Ry9KJtt5Kd3NxafS", user_id: Deno.env.get("F24_USER_EDGAR") ?? "6G3VFN9NMm2J2zBGJkGC" },
];

// Hash de string estable (djb2) → índice de asesor. Determinístico por contactId.
function pickAsesor(contactId: string): Asesor {
  let h = 5381;
  const s = contactId || "x";
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return ASESORES[h % ASESORES.length];
}

function ghlHeaders() {
  return {
    Authorization: `Bearer ${GHL_TOKEN}`,
    Version: GHL_VERSION,
    "Content-Type": "application/json",
    Accept: "application/json",
    "User-Agent": UA,
  };
}

// ── Formateo de fecha/hora en es-MX, zona CDMX ─────────────────────────────────────────────────
// Etiqueta natural para ofrecer al cliente: "mañana a las 10:00 am", "el jueves a la 1:00 pm".
function slotLabel(iso: string, now = new Date()): string {
  const d = new Date(iso);
  const dayFmt = new Intl.DateTimeFormat("es-MX", { timeZone: TIMEZONE, weekday: "long", day: "numeric", month: "long" });
  const timeFmt = new Intl.DateTimeFormat("es-MX", { timeZone: TIMEZONE, hour: "numeric", minute: "2-digit", hour12: true });
  // ¿Hoy / mañana? Compara el día calendario en la zona CDMX.
  const ymd = (x: Date) => new Intl.DateTimeFormat("en-CA", { timeZone: TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(x);
  const today = ymd(now);
  const tomorrow = ymd(new Date(now.getTime() + 86400000));
  const dd = ymd(d);
  let dayPart: string;
  if (dd === today) dayPart = "hoy";
  else if (dd === tomorrow) dayPart = "mañana";
  else dayPart = "el " + dayFmt.format(d).replace(/,/g, ""); // "el jueves 10 de julio"
  const time = timeFmt.format(d).replace(/\s?a\.\s?m\./i, "am").replace(/\s?p\.\s?m\./i, "pm");
  return `${dayPart} a las ${time}`;
}

// ── GHL free-slots ─────────────────────────────────────────────────────────────────────────────
// GET /calendars/{id}/free-slots?startDate={ms}&endDate={ms}&timezone=...
// Respuesta: { "2026-07-10": { "slots": ["ISO", ...] }, ..., "traceId": "..." }
async function getFreeSlots(calendarId: string, days = 7, maxSlots = 3): Promise<string[]> {
  const now = Date.now();
  const start = now + 2 * 3600 * 1000; // GHL: allowBookingAfter 2h → arranca 2h adelante
  const end = now + days * 86400 * 1000;
  const url = `${GHL_BASE}/calendars/${calendarId}/free-slots?startDate=${start}&endDate=${end}&timezone=${encodeURIComponent(TIMEZONE)}`;
  const r = await fetch(url, { headers: ghlHeaders() });
  if (!r.ok) throw new Error(`free_slots_${r.status}:${(await r.text()).slice(0, 200)}`);
  const body = await r.json();
  // Junta todos los slots de todas las fechas, en orden cronológico, tomando 1 por día (spread)
  // hasta maxSlots — para ofrecer horarios variados y no 3 seguidos del mismo día.
  const perDay: string[][] = [];
  for (const key of Object.keys(body)) {
    if (key === "traceId" || !body[key] || !Array.isArray(body[key].slots)) continue;
    const slots = (body[key].slots as string[]).filter(Boolean).sort();
    if (slots.length) perDay.push(slots);
  }
  perDay.sort((a, b) => (a[0] < b[0] ? -1 : 1));
  const picked: string[] = [];
  // Primera pasada: 1 por día (el más temprano). Segunda pasada: rellena si faltan.
  for (const day of perDay) { if (picked.length >= maxSlots) break; picked.push(day[0]); }
  for (const day of perDay) {
    for (const s of day) { if (picked.length >= maxSlots) break; if (!picked.includes(s)) picked.push(s); }
    if (picked.length >= maxSlots) break;
  }
  return picked.slice(0, maxSlots).sort();
}

// ── GHL create appointment ─────────────────────────────────────────────────────────────────────
async function createAppointment(calendarId: string, contactId: string, startISO: string, titulo: string, userId: string) {
  const start = new Date(startISO);
  const endISO = new Date(start.getTime() + SLOT_MINUTES * 60000).toISOString();
  const payload: Record<string, unknown> = {
    calendarId,
    locationId: LOCATION_ID,
    contactId,
    startTime: startISO,
    endTime: endISO,
    title: titulo,
    appointmentStatus: "confirmed",
    ignoreDateRange: false,
    toNotify: true,
  };
  // Asigna la cita al usuario GHL del asesor → le aparece en SU calendario personal.
  if (userId) payload.assignedUserId = userId;
  const r = await fetch(`${GHL_BASE}/calendars/events/appointments`, {
    method: "POST", headers: ghlHeaders(), body: JSON.stringify(payload),
  });
  const txt = await r.text();
  if (r.status !== 200 && r.status !== 201) throw new Error(`appt_${r.status}:${txt.slice(0, 240)}`);
  const data = JSON.parse(txt || "{}");
  return data.id ?? data.appointment?.id ?? data.event?.id ?? "";
}

const FALLBACK_SLOTS = "Con gusto te agendo la llamada con un asesor. ¿Qué día y horario te acomoda mejor? Yo lo coordino.";
const FALLBACK_BOOK = "¡Va! Dejo agendada tu llamada con un asesor. Te va a marcar a este mismo número. Si prefieres otro horario, dime y lo ajusto.";

// ── Modo slots: ofrecer horarios reales ────────────────────────────────────────────────────────
async function doSlots(input: any) {
  const contactId = String(input.contact_id ?? input.contactId ?? "").trim();
  const asesor = pickAsesor(contactId);
  const isos = await getFreeSlots(asesor.calendar_id);
  if (!isos.length) {
    // Calendario sin disponibilidad publicada (o sin horario configurado) → cae al modo "dime tú".
    return { ok: false, mode: "slots", asesor: asesor.key, error: "no_slots", mensaje: FALLBACK_SLOTS };
  }
  const slots = isos.map((iso) => ({ iso, label: slotLabel(iso) }));
  // Mensaje natural con 2-3 opciones. El bot lo envía tal cual y espera que el cliente elija.
  let mensaje: string;
  if (slots.length === 1) {
    mensaje = `Con gusto. Tengo disponible ${slots[0].label} para tu llamada con un asesor. ¿Te late ese horario?`;
  } else {
    const opts = slots.map((s) => s.label).join(", o ");
    mensaje = `Con gusto te agendo la llamada con un asesor. Tengo estos horarios: ${opts}. ¿Cuál te acomoda mejor?`;
  }
  return { ok: true, mode: "slots", asesor: asesor.key, calendar_id: asesor.calendar_id, slots, mensaje };
}

// Hora numérica de un slot (0-23) en zona CDMX, para el match difuso con lo que dijo el cliente.
function slotHour24(iso: string): number {
  const h = new Intl.DateTimeFormat("en-US", { timeZone: TIMEZONE, hour: "numeric", hour12: false }).format(new Date(iso));
  return parseInt(h, 10) % 24;
}

// Resuelve la ELECCIÓN del cliente (texto libre) contra los slots ofrecidos.
// El bot NO conoce el ISO exacto — solo el texto — así que aquí lo mapeamos de vuelta.
// Estrategia: (1) índice si dijo "1/2/3"; (2) match por día (hoy/mañana/día-semana) + hora.
function resolveChoice(choiceRaw: string, slots: { iso: string; label: string }[]): string | null {
  const c = (choiceRaw || "").toLowerCase().trim();
  if (!c || !slots.length) return null;
  // (1) Índice explícito: "2", "el 2", "opción 2", "la segunda"
  const ordinales: Record<string, number> = { primer: 1, primera: 1, segundo: 2, segunda: 2, tercer: 3, tercera: 3, "último": slots.length, ultima: slots.length };
  for (const [w, n] of Object.entries(ordinales)) if (c.includes(w) && n <= slots.length) return slots[n - 1].iso;
  const soloNum = c.match(/^(?:el |la |opci[oó]n |n[uú]mero |la )?\s*([1-9])\s*$/);
  if (soloNum) { const i = parseInt(soloNum[1], 10) - 1; if (i >= 0 && i < slots.length) return slots[i].iso; }
  // (2) Match difuso por día + hora contra la etiqueta de cada slot.
  const wants = { hoy: /\bhoy\b/.test(c), manana: /\bma[nñ]ana\b/.test(c) };
  // Hora que mencionó el cliente (10, 3:30, 10am, 1 pm…) → número 0-23 aproximado con am/pm.
  const tm = c.match(/\b(\d{1,2})(?::(\d{2}))?\s*(a\.?\s?m\.?|p\.?\s?m\.?|am|pm|hrs?|horas?)?\b/);
  let wantHour: number | null = null;
  if (tm) {
    let h = parseInt(tm[1], 10);
    const mer = (tm[3] || "").replace(/[.\s]/g, "");
    if (/pm/.test(mer) && h < 12) h += 12;
    if (/am/.test(mer) && h === 12) h = 0;
    wantHour = h;
  }
  let best: { iso: string; score: number } | null = null;
  for (const s of slots) {
    const lab = s.label.toLowerCase();
    let score = 0;
    if (wants.hoy && lab.includes("hoy")) score += 2;
    if (wants.manana && lab.includes("mañana")) score += 2;
    // día de la semana ("sábado", "jueves"…) mencionado por el cliente y presente en la etiqueta
    for (const dia of ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"])
      if (c.includes(dia) && lab.includes(dia)) score += 2;
    if (wantHour !== null) {
      const sh = slotHour24(s.iso);
      if (sh === wantHour) score += 3;
      else if (Math.abs(sh - wantHour) === 12) score += 1; // confusión am/pm
    }
    if (score > 0 && (!best || score > best.score)) best = { iso: s.iso, score };
  }
  // Si mencionó una sola hora y solo un slot la tiene, con eso basta aunque no diga el día.
  return best ? best.iso : null;
}

// ── Modo book: crear la cita al horario elegido ────────────────────────────────────────────────
async function doBook(input: any) {
  const contactId = String(input.contact_id ?? input.contactId ?? "").trim();
  if (!contactId) return { ok: false, mode: "book", error: "missing_contact", mensaje: FALLBACK_BOOK };
  const asesor = pickAsesor(contactId);
  const producto = String(input.producto ?? "").trim();
  const titulo = producto ? `Llamada Ferre24 · ${producto}` : "Llamada de asesoría Ferre24";

  // El bot puede mandar el ISO exacto (start_time) o —lo normal— la elección en texto (call_choice).
  let startISO = String(input.start_time ?? input.startTime ?? "").trim();
  if (!/^\d{4}-\d{2}-\d{2}T/.test(startISO)) {
    // Re-consulta los slots reales (mismo orden determinístico) y resuelve lo que dijo el cliente.
    const isos = await getFreeSlots(asesor.calendar_id);
    const slots = isos.map((iso) => ({ iso, label: slotLabel(iso) }));
    const choice = String(input.call_choice ?? input.choice ?? input.start_time ?? "").trim();
    const resolved = resolveChoice(choice, slots);
    if (!resolved) {
      // No se pudo mapear la elección → re-ofrece los horarios en vez de agendar a ciegas.
      const opts = slots.map((s) => s.label).join(", o ");
      return { ok: false, mode: "book", error: "unresolved_choice", asesor: asesor.key,
        mensaje: slots.length ? `¿Cuál de estos te acomoda para la llamada: ${opts}? Dime el horario y lo agendo.` : FALLBACK_BOOK };
    }
    startISO = resolved;
  }

  try {
    const apptId = await createAppointment(asesor.calendar_id, contactId, startISO, titulo, asesor.user_id);
    const label = slotLabel(startISO);
    return {
      ok: true, mode: "book", asesor: asesor.key, appointment_id: apptId, start_time: startISO,
      mensaje: `¡Listo! Quedó agendada tu llamada con un asesor ${label} 📞 Te marca a este mismo número. Cualquier cosa, aquí ando.`,
    };
  } catch (e) {
    // El slot pudo ocuparse entre que se ofreció y se confirmó → pide reintentar (el bot re-ofrece).
    const msg = String(e);
    if (msg.includes("appt_4") || msg.includes("slot")) {
      return { ok: false, mode: "book", error: "slot_taken", asesor: asesor.key,
        mensaje: "Uy, ese horario se acaba de ocupar. ¿Te va otro? Dime y lo agendo." };
    }
    throw e;
  }
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") return json({ ok: true, service: "f24-book-appointment", version: 1, modes: ["slots", "book"] });
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const body = await req.json().catch(() => ({}));
    const mode = String(body.mode ?? "slots").toLowerCase();
    let result: any;
    try {
      result = mode === "book" ? await doBook(body) : await doSlots(body);
    } catch (e) {
      const fb = mode === "book" ? FALLBACK_BOOK : FALLBACK_SLOTS;
      result = { ok: false, mode, error: String(e).slice(0, 300), mensaje: fb };
    }
    return json({ ...result, elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) {
    return json({ ok: false, error: String(e).slice(0, 300), mensaje: FALLBACK_SLOTS }, 200);
  }
});
