// f24-rep-log — Edge Function (Deno). Registra lo que hace el rep en su panel:
// QA del bot y llamadas. DOBLE ESCRITURA: fila en Supabase (contable, para el
// tablero de Sergio) + nota en el contacto de GHL (visible en el CRM).
//
// POR QUÉ EXISTE: antes el QA se iba a un webhook de Make → data store → nota en
// GHL. Las notas de GHL no se pueden contar en bloque, así que Sergio no podía
// medir nada. Además la org de Make agotó sus 10,000 operaciones el 2026-07-19 y
// apagó todo sin avisar. Esto no gasta ni una operación de Make.
//
// OJO: es la PRIMERA función F24 que se llama desde el navegador. Ninguna otra
// pone headers CORS. Si tocas esto, el preflight OPTIONS no es opcional.
//
// Secrets: GHL_TOKEN, F24_PANEL_KEYS. SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY
// los inyecta Supabase solo.
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const SB_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SB_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const PANEL_KEYS = Deno.env.get("F24_PANEL_KEYS") ?? "{}"; // {"Edgar":"...","Alfredo":"..."}

const ALLOWED_ORIGIN = "https://ferre24.com.mx";
const VERSION = 1;

// Cloudflare responde 1010 a peticiones a GHL sin User-Agent de navegador.
// Verificado en producción (ver f24-book-appointment). No lo quites.
const UA = "Mozilla/5.0 (compatible; SpekgenBot/1.0)";
const GHL_H = {
  Authorization: `Bearer ${GHL_TOKEN}`,
  Version: "2021-07-28",
  "Content-Type": "application/json",
  Accept: "application/json",
  "User-Agent": UA,
};
const SB_H = {
  apikey: SB_KEY,
  Authorization: `Bearer ${SB_KEY}`,
  "Content-Type": "application/json",
};

const CORS = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "content-type",
  Vary: "Origin",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

// ── enums (deben coincidir con los CHECK de _sql/001_qa_calls.sql) ──────────
const RATINGS = ["up", "down"];
const CALL_TYPES = ["proactiva", "solicitada"];
const OUTCOMES: Record<string, string> = {
  no_contesto: "No contestó",
  buzon: "Buzón / apagado",
  numero_equivocado: "Número equivocado",
  contesto_interesado: "Contestó — interesado",
  contesto_no_interesado: "Contestó — no le interesa",
  pidio_cotizacion: "Pidió cotización",
  pidio_volver_llamar: "Pidió que le llame después",
  ya_compro_otro: "Ya compró en otro lado",
  cerro_venta: "Cerró la venta",
};

// ── nota para el CRM. Mismo formato que qa_ingest.py para que el historial
// del contacto se lea parejo entre lo viejo y lo nuevo. ──────────────────────
function noteBody(p: Record<string, string>): string {
  const lead = `Lead: ${p.contact_name || "—"}${p.phone ? " · " + p.phone : ""}`;
  if (p.kind === "qa") {
    const emoji = p.rating === "up" ? "👍" : "👎";
    const label = p.rating === "up" ? "OK" : "REVISAR";
    const lines = [`[QA bot · ${p.rep}] ${emoji} ${label}`];
    if (p.category) lines.push(`Qué falló: ${p.category}`);
    if (p.comment) lines.push(`"${p.comment}"`);
    lines.push(lead);
    return lines.join("\n");
  }
  const tipo = p.call_type === "solicitada" ? "Solicitada" : "Proactiva";
  const lines = [`[Llamada · ${p.rep}] 📞 ${tipo} — ${OUTCOMES[p.outcome] ?? p.outcome}`];
  if (p.comment) lines.push(`"${p.comment}"`);
  lines.push(lead);
  return lines.join("\n");
}

async function sbGet(path: string): Promise<any[]> {
  const r = await fetch(`${SB_URL}/rest/v1/${path}`, { headers: SB_H });
  if (!r.ok) throw new Error(`supabase GET ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return await r.json();
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method === "GET") {
    return json({ ok: true, service: "f24-rep-log", version: VERSION, kinds: ["qa", "call"] });
  }
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);

  const t0 = Date.now();
  try {
    // Allowlist de origen. Es trivial de falsificar desde un cliente que no sea
    // navegador — no es autenticación, solo corta el ruido y los requests mal
    // ruteados. La defensa real es la validación de abajo.
    const origin = req.headers.get("Origin") ?? "";
    if (origin && origin !== ALLOWED_ORIGIN) {
      return json({ ok: false, error: "bad_origin" }, 200);
    }

    const b = await req.json().catch(() => ({}));
    const kind = String(b.kind ?? "");
    if (kind !== "qa" && kind !== "call") return json({ ok: false, error: "bad_kind" }, 200);

    const rep = String(b.rep ?? "").trim();
    // panel_key: OFUSCACIÓN, NO AUTENTICACIÓN. Cualquiera que vea el código
    // fuente del panel la tiene. Sirve para que Edgar no pueda registrar QAs a
    // nombre de Alfredo (estos datos evalúan desempeño) y para poder rotarla.
    let keys: Record<string, string> = {};
    try { keys = JSON.parse(PANEL_KEYS); } catch { /* mapa vacío = sin gate */ }
    if (Object.keys(keys).length > 0 && keys[rep] !== String(b.panel_key ?? "")) {
      return json({ ok: false, error: "bad_panel_key" }, 200);
    }

    const contactId = String(b.contact_id ?? "").trim();
    if (!/^[A-Za-z0-9_-]{10,40}$/.test(contactId)) return json({ ok: false, error: "bad_contact_id" }, 200);

    const rating = b.rating ? String(b.rating) : null;
    const callType = b.call_type ? String(b.call_type) : null;
    const outcome = b.outcome ? String(b.outcome) : null;
    if (kind === "qa" && (!rating || !RATINGS.includes(rating))) return json({ ok: false, error: "bad_rating" }, 200);
    if (kind === "call") {
      if (!outcome || !(outcome in OUTCOMES)) return json({ ok: false, error: "bad_outcome" }, 200);
      if (callType && !CALL_TYPES.includes(callType)) return json({ ok: false, error: "bad_call_type" }, 200);
    }

    // Rechazar, no truncar: si el panel manda algo raro quiero enterarme.
    const comment = String(b.comment ?? "").trim();
    const category = String(b.category ?? "").trim();
    if (comment.length > 500) return json({ ok: false, error: "comment_too_long" }, 200);
    if (category.length > 60) return json({ ok: false, error: "category_too_long" }, 200);

    // Rate limit por rep. Un rep quemando 15 pendientes de golpe NO debe tronar;
    // un script machacando el endpoint sí.
    const since = new Date(Date.now() - 10 * 60_000).toISOString();
    const recent = await sbGet(
      `f24_rep_activity?select=id&rep_name=eq.${encodeURIComponent(rep)}&created_at=gte.${since}&limit=61`,
    );
    if (recent.length >= 60) return json({ ok: false, error: "rate_limited" }, 200);

    // ── SLA congelado al momento de escribir ──────────────────────────────
    let lastInbound: string | null = null;
    try {
      const st = await sbGet(
        `f24_conversation_state?select=last_inbound_at&contact_id=eq.${encodeURIComponent(contactId)}&limit=1`,
      );
      lastInbound = st.length ? st[0].last_inbound_at : null;
    } catch (_) { /* sin estado → sin_referencia, no es fatal */ }

    let slaStatus = "sin_referencia";
    let slaHours: number | null = null;
    let slaDue: string | null = null;
    if (lastInbound && kind === "qa") {
      const li = new Date(lastInbound).getTime();
      slaHours = Math.round(((Date.now() - li) / 3_600_000) * 100) / 100;
      slaDue = new Date(li + 24 * 3_600_000).toISOString();
      slaStatus = slaHours <= 24 ? "a_tiempo" : "tarde";
    }

    const row: Record<string, unknown> = {
      kind,
      rep_name: rep,
      rep_user_id: b.rep_user_id ? String(b.rep_user_id) : null,
      contact_id: contactId,
      opp_id: b.opp_id ? String(b.opp_id) : null,
      contact_name: b.contact_name ? String(b.contact_name).slice(0, 200) : null,
      phone: b.phone ? String(b.phone).slice(0, 40) : null,
      rating: kind === "qa" ? rating : null,
      category: kind === "qa" ? (category || null) : null,
      call_type: kind === "call" ? (callType ?? "proactiva") : null,
      outcome: kind === "call" ? outcome : null,
      comment: comment || null,
      last_inbound_at: lastInbound,
      sla_due_at: slaDue,
      sla_hours: slaHours,
      sla_status: kind === "qa" ? slaStatus : null,
      source: "panel",
    };

    // 1) Supabase PRIMERO. Si esto falla, abortamos y NO escribimos la nota:
    // una nota sin fila es invisible para Sergio, que es justo lo que veníamos
    // a arreglar. Mejor que el rep reintente.
    const ins = await fetch(`${SB_URL}/rest/v1/f24_rep_activity`, {
      method: "POST",
      headers: { ...SB_H, Prefer: "return=representation" },
      body: JSON.stringify(row),
    });
    if (!ins.ok) {
      const detail = (await ins.text()).slice(0, 300);
      console.log(`[f24-rep-log] supabase insert FALLÓ ${ins.status}: ${detail}`);
      return json({ ok: false, error: "db_write_failed", detail, elapsed_ms: Date.now() - t0 }, 200);
    }
    const saved = (await ins.json())[0];

    // 2) Nota en GHL. Si falla, la fila YA está guardada: marcamos el fallo y
    // devolvemos ok:true. El conteo de Sergio sobrevive; la nota del CRM es la
    // mitad blanda.
    let noteOk = false;
    let noteErr: string | null = null;
    try {
      const nr = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, {
        method: "POST",
        headers: GHL_H,
        body: JSON.stringify({ body: noteBody({ ...b, kind, rep, comment, category, outcome: outcome ?? "" } as any) }),
      });
      noteOk = nr.ok;
      if (!nr.ok) noteErr = `ghl ${nr.status}: ${(await nr.text()).slice(0, 200)}`;
    } catch (e) {
      noteErr = String(e).slice(0, 200);
    }
    if (noteOk) {
      await fetch(`${SB_URL}/rest/v1/f24_rep_activity?id=eq.${saved.id}`, {
        method: "PATCH", headers: SB_H, body: JSON.stringify({ ghl_note_ok: true }),
      }).catch(() => {});
    } else {
      await fetch(`${SB_URL}/rest/v1/f24_rep_activity?id=eq.${saved.id}`, {
        method: "PATCH", headers: SB_H, body: JSON.stringify({ ghl_note_ok: false, ghl_note_error: noteErr }),
      }).catch(() => {});
    }

    console.log(`[f24-rep-log] ${kind} rep=${rep} contact=${contactId} sla=${slaStatus} note=${noteOk}`);
    return json({
      ok: true, id: saved.id, sla_status: slaStatus, sla_hours: slaHours,
      ghl_note_ok: noteOk, elapsed_ms: Date.now() - t0,
    });
  } catch (e) {
    console.log(`[f24-rep-log] ERROR ${String(e).slice(0, 300)}`);
    return json({ ok: false, error: String(e).slice(0, 300), elapsed_ms: Date.now() - t0 }, 200);
  }
});
