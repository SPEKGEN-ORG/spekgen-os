// f24-generate-guide — Supabase Edge Function (Deno)
//
// "Del clic al repartidor sin que tú estés en medio" (Propuesta F24, punto 03 — core de envío).
// Cuando una orden de Shopify queda PAGADA (webhook orders/paid → Make → este function),
// genera la guía de envío AUTOMÁTICAMENTE vía la API de Envíoclick PRO (cuenta de Sergio),
// crea el fulfillment en Shopify con el tracking (notify_customer: true → Shopify manda el
// email "tu pedido va en camino"), y escribe el tracking de vuelta al contacto en GHL.
//
// Mode: generate_guide
//   body: el payload completo de la orden (orders/paid webhook body), o { order: {...} }.
//   Output: { ok, tracking_number, tracking_url, label_url, carrier, service, total, parcel, fulfillment_id }
//   Patrón "siempre 200 con ok:false" — para que el router de Make dispare la alerta sin
//   detener el scenario (mismo patrón que hc-process-order / f24-process-order).
//
// Carriers: la API de Envíoclick PRO solo cotiza el marketplace estándar
//   (Estafeta / DHL / AMPM / 99minutos / Paquetexpress). Mas Aprisa / Maximaexpress son
//   cuentas directas de Sergio que solo viven en su panel (uso manual) → NO por API.
//   Decisión Gibran 2026-06-15: órdenes online = auto con marketplace; regionales = flujo
//   local/manual de Sergio (fase 2).
//
// Secrets (Supabase → Edge Function secrets), reusa los de f24-process-order:
//   SHOPIFY_SHOP, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_API_VERSION
//   GHL_TOKEN (PIT F24)
//   ENVIOCLICK_API_KEY, ENVIOCLICK_BASE_URL
//   ENVIOCLICK_ORIGIN_* (dirección de la bodega de Sergio — ver ORIGIN abajo)

const SHOPIFY_SHOP = Deno.env.get("SHOPIFY_SHOP") ?? "0mtky1-q6.myshopify.com";
const SHOPIFY_CLIENT_ID = Deno.env.get("SHOPIFY_CLIENT_ID") ?? "";
const SHOPIFY_CLIENT_SECRET = Deno.env.get("SHOPIFY_CLIENT_SECRET") ?? "";
const SHOPIFY_API_VERSION = Deno.env.get("SHOPIFY_API_VERSION") ?? "2024-10";

const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const GHL_CF_TRACKING_URL = "PitQVTnJJ0JreENWIBtz"; // custom field "tracking_url" (mismo que f24-process-order)

// Fallback hardcodeado (patrón agencia, igual que hc-process-order con Skydropx). Idealmente
// mover a secret de Supabase ENVIOCLICK_API_KEY. Cuenta Envíoclick PRO de Sergio.
const EC_KEY = Deno.env.get("ENVIOCLICK_API_KEY") ?? "08ce279c-8afe-4be5-baed-adfffd60818c";
const EC_BASE = Deno.env.get("ENVIOCLICK_BASE_URL") ?? "https://api.envioclickpro.com/api/v1";

// ── ORIGEN (bodega Sergio) ──────────────────────────────────────────────────
// TODO go-live: reemplazar con la dirección real de la bodega de Sergio (CP/calle/etc).
// Placeholder GDL centro mientras Gibran confirma. Override por env sin redeploy de código.
const ORIGIN = {
  zipCode:     Deno.env.get("ENVIOCLICK_ORIGIN_ZIP")        ?? "44100",
  company:     Deno.env.get("ENVIOCLICK_ORIGIN_COMPANY")    ?? "Ferre24",
  firstName:   Deno.env.get("ENVIOCLICK_ORIGIN_FIRSTNAME")  ?? "Ferre24",
  lastName:    Deno.env.get("ENVIOCLICK_ORIGIN_LASTNAME")   ?? "Almacen",
  email:       Deno.env.get("ENVIOCLICK_ORIGIN_EMAIL")      ?? "pedidos@ferre24.com.mx",
  phone:       Deno.env.get("ENVIOCLICK_ORIGIN_PHONE")      ?? "3300000000",
  street:      Deno.env.get("ENVIOCLICK_ORIGIN_STREET")     ?? "Av. Juarez",
  number:      Deno.env.get("ENVIOCLICK_ORIGIN_NUMBER")     ?? "100",
  suburb:      Deno.env.get("ENVIOCLICK_ORIGIN_SUBURB")     ?? "Centro",
  crossStreet: Deno.env.get("ENVIOCLICK_ORIGIN_CROSS")      ?? "N/A",
  reference:   Deno.env.get("ENVIOCLICK_ORIGIN_REFERENCE")  ?? "Almacen Ferre24",
};

// ── PARCEL (híbrido) ──────────────────────────────────────────────────────────
// Shopify no guarda dimensiones (solo peso), y F24 es maquinaria pesada con pesos a veces
// mal importados (ej. navajas Victorinox en "5kg"). Estrategia híbrida:
//   - DIMENSIONES: perfil por categoría (keyword sobre product_type + título).
//   - PESO: el de Shopify si es plausible vs el perfil; si no, usa el del perfil
//     (auto-corrige los pesos basura). Override fino por SKU en PACKAGE_OVERRIDES.
//   - needs_review: pedidos >70kg (flete pesado) se marcan para que Sergio los revise.
interface Profile { name: string; kg: number; length: number; width: number; height: number; }
const PROFILES: { match: RegExp; p: Profile }[] = [
  { match: /navaja|victorinox|multitool|multiusos/i, p: { name: "Navaja", kg: 0.3, length: 14, width: 10, height: 4 } },
  { match: /osmosis|ósmosis|ultrafiltr|purific|filtr|punto de uso|pou/i, p: { name: "Filtro agua", kg: 12, length: 50, width: 40, height: 35 } },
  { match: /jardin|jardín|pasto|cortaseto|orillador|sintétic|tijera|manguera|herramienta de/i, p: { name: "Jardín ligero", kg: 4, length: 40, width: 25, height: 18 } },
  { match: /generador|compresor|soldadora|compactadora|parihuela|diésel|diesel|inverter/i, p: { name: "Máquina pesada", kg: 60, length: 72, width: 56, height: 60 } },
  { match: /motobomba|bomba|sumergible|motor|hidrolavadora|desbrozadora|motosierra|podadora|soplador|ahoyadora|escarific|peinadora|barredora|presuriz|tanque|calentador|centrífuga|2t|4 tiempos|gasolina/i, p: { name: "Equipo gasolina", kg: 25, length: 56, width: 46, height: 46 } },
];
const DEFAULT_PROFILE: Profile = { name: "General", kg: 15, length: 50, width: 40, height: 35 };
// Override fino por SKU (corrección de top-sellers verificados): { "SKU": { kg, length, width, height } }
const PACKAGE_OVERRIDES: Record<string, Partial<Profile>> = {};

function pickProfile(text: string): Profile {
  for (const { match, p } of PROFILES) if (match.test(text)) return p;
  return DEFAULT_PROFILE;
}
// Confía en el peso de Shopify si cae dentro de [0.25×, 4×] del perfil; si no, usa el del perfil.
function saneWeight(gramsKg: number, profileKg: number): number {
  if (gramsKg > 0 && gramsKg >= profileKg * 0.25 && gramsKg <= profileKg * 4) return gramsKg;
  return profileKg;
}

interface Parcel { weight: number; length: number; width: number; height: number; box_name: string; needs_review: boolean; }
function computeParcel(order: any, typeByProductId: Record<string, string>): Parcel {
  let totalKg = 0;
  let big: Profile = DEFAULT_PROFILE;
  for (const li of order.line_items ?? []) {
    const sku = String(li.sku ?? "");
    const ptype = typeByProductId[String(li.product_id ?? "")] ?? "";
    const prof = pickProfile(`${ptype} ${li.title ?? ""}`);
    const ov = PACKAGE_OVERRIDES[sku] ?? {};
    const profKg = ov.kg ?? prof.kg;
    const gramsKg = (Number(li.grams ?? 0) || 0) / 1000;
    const unitKg = saneWeight(gramsKg, profKg);
    const qty = parseInt(String(li.quantity ?? 1), 10) || 1;
    totalKg += unitKg * qty;
    const dims = { ...prof, ...ov } as Profile;
    if (dims.length * dims.width * dims.height > big.length * big.width * big.height) big = dims;
  }
  let kg = Math.round(totalKg * 100) / 100;
  if (kg <= 0) kg = big.kg;
  return { weight: kg, length: big.length, width: big.width, height: big.height, box_name: big.name, needs_review: kg > 70 };
}

// product_type por product_id (1 sola query GraphQL). Si falta, pickProfile usa el título.
async function fetchProductTypes(order: any): Promise<Record<string, string>> {
  const ids = [...new Set((order.line_items ?? []).map((li: any) => String(li.product_id ?? "")).filter(Boolean))];
  if (!ids.length) return {};
  try {
    const tok = await getShopifyToken();
    const gids = ids.map((id) => `"gid://shopify/Product/${id}"`).join(",");
    const r = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/graphql.json`, {
      method: "POST", headers: { "X-Shopify-Access-Token": tok, "Content-Type": "application/json" },
      body: JSON.stringify({ query: `{ nodes(ids: [${gids}]) { ... on Product { id productType } } }` }),
    });
    const d = await r.json();
    const map: Record<string, string> = {};
    for (const n of d.data?.nodes ?? []) if (n?.id) map[String(n.id).split("/").pop()!] = n.productType ?? "";
    return map;
  } catch { return {}; }
}

function declaredValue(order: any): number {
  const v = parseFloat(order.subtotal_price ?? order.total_price ?? "0");
  // Envíoclick exige contentValue > 0; piso conservador para el seguro.
  return v > 0 ? Math.round(v) : 100;
}

// ── SANITIZACIÓN (Envíoclick rechaza nombres/calles con formato raro, igual que Skydropx) ──
function sanitizeName(raw: string, fallback = "Cliente"): string {
  let s = String(raw ?? "").trim();
  if (!s) s = fallback;
  s = s.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü \-]/g, " ").replace(/\s+/g, " ").trim();
  return (s || fallback).slice(0, 40);
}
function sanitizeText(raw: string, fallback = "", max = 60): string {
  let s = String(raw ?? "").trim();
  s = s.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9 #,.\-]/g, " ").replace(/\s+/g, " ").trim();
  return (s || fallback).slice(0, max);
}
function digits(raw: string, fallback = "0000000000"): string {
  const d = String(raw ?? "").replace(/\D/g, "");
  return d.length >= 10 ? d.slice(-10) : (d || fallback);
}
// "Av. Juarez 1234 Int 5" → { street: "Av. Juarez", number: "1234" } (best-effort)
function splitStreet(address1: string): { street: string; number: string } {
  const s = sanitizeText(address1, "", 80);
  const m = s.match(/^(.*?)(\d+[A-Za-z]?)\s*$/) || s.match(/^(.*?)\s(\d+)/);
  if (m) return { street: sanitizeText(m[1] || s, s, 50), number: (m[2] || "SN").slice(0, 12) };
  return { street: s || "Sin nombre", number: "SN" };
}

// ── ENVIOCLICK PRO ───────────────────────────────────────────────────────────
function ecHeaders() {
  return { "Authorization": EC_KEY, "Content-Type": "application/json" };
}

interface Rate { idRate: number; carrier: string; total: number; deliveryDays: number; service?: string; }
async function ecQuote(parcel: Parcel, destZip: string, value: number): Promise<Rate[]> {
  const payload = {
    origin_zip_code: ORIGIN.zipCode,
    destination_zip_code: destZip,
    package: {
      description: "Herramientas y ferreteria",
      contentValue: value,
      weight: parcel.weight,
      length: parcel.length,
      height: parcel.height,
      width: parcel.width,
    },
  };
  const r = await fetch(`${EC_BASE}/quotation`, { method: "POST", headers: ecHeaders(), body: JSON.stringify(payload) });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`ec_quote_${r.status}:${JSON.stringify(body).slice(0, 300)}`);
  const rates = (body.data?.rates ?? body.rates ?? []) as any[];
  return rates.map((x) => ({
    idRate: Number(x.idRate),
    carrier: String(x.carrier ?? ""),
    total: parseFloat(x.total ?? "9e9"),
    deliveryDays: parseInt(String(x.deliveryDays ?? "99"), 10),
    service: x.deliveryType ?? x.product ?? "",
  }));
}

function pickRate(rates: Rate[], express: boolean): Rate | null {
  if (!rates.length) return null;
  let pool = rates;
  if (express) {
    const fast = rates.filter((r) => r.deliveryDays <= 1);
    pool = fast.length ? fast : rates;
  }
  // Más barata del pool (regla acordada: cheapest; refinable con Sergio).
  return pool.reduce((a, b) => (a.total <= b.total ? a : b));
}

// Tracking URL público por carrier del marketplace Envíoclick (verificado contra el response
// real: el carrier viene como "99MINUTOS"/"ESTAFETA"/"DHL"/"AMPM"/"PAQUETEEXPRESS"). Si el
// carrier no mapea, Shopify usa solo el número + company. TODO: verificar 1 vez cada formato.
function buildTrackingUrl(carrier: string, tn: string): string {
  const c = (carrier || "").toUpperCase();
  if (!tn) return "";
  if (c.includes("ESTAFETA")) return `https://www.estafeta.com/Rastreo/RastreoEnvio?numero=${tn}`;
  if (c.includes("DHL")) return `https://www.dhl.com/mx-es/home/rastreo.html?tracking-id=${tn}`;
  if (c.includes("99")) return `https://web.99minutos.com/tracking/${tn}`;
  if (c.includes("PAQUETE")) return `https://www.paquetexpress.com.mx/rastreo?guia=${tn}`;
  if (c.includes("AMPM")) return `https://www.ampm.mx/rastreo?guia=${tn}`;
  return `https://www.envioclickpro.com/rastreo?guia=${tn}`;
}

interface Guide { tracking_number: string; label_url: string; label_pdf_b64: string; tracking_url: string; id_order: string; raw: any; }
async function ecCreateGuide(rate: Rate, parcel: Parcel, dest: any, value: number, reference: string): Promise<Guide> {
  const name = sanitizeName(dest.name ?? `${dest.first_name ?? ""} ${dest.last_name ?? ""}`.trim());
  const parts = name.split(" ");
  const { street, number } = splitStreet(dest.address1 ?? "");
  const payload = {
    idRate: rate.idRate,
    requestPickup: false,           // sin recolección programada; entrega en sucursal/ruta del carrier
    myShipmentReference: reference, // p.ej. "Ferre24 #1042"
    thermalLabel: false,            // PDF carta estándar
    package: {
      description: "Herramientas y ferreteria",
      contentValue: value,
      weight: parcel.weight,
      length: parcel.length,
      height: parcel.height,
      width: parcel.width,
    },
    origin: { ...ORIGIN },
    destination: {
      company: "",
      firstName: parts[0] || "Cliente",
      lastName: parts.slice(1).join(" ") || ".",
      email: String(dest.email || "").trim() || "pedidos@ferre24.com.mx",
      phone: digits(dest.phone),
      street,
      number,
      suburb: sanitizeText(dest.address2 || dest.city || "", "Centro", 50),
      crossStreet: sanitizeText(dest.address2 || "", "N/A", 50),
      reference: sanitizeText(reference, "Pedido Ferre24", 50),
      zipCode: String(dest.zip ?? "").trim(),
    },
  };
  const r = await fetch(`${EC_BASE}/shipment/request`, { method: "POST", headers: ecHeaders(), body: JSON.stringify(payload) });
  const body = await r.json().catch(() => ({}));
  if (!r.ok || (body.status && body.status !== "OK")) {
    throw new Error(`ec_guide_${r.status}:${JSON.stringify(body).slice(0, 400)}`);
  }
  // Response confirmado con guía real (2026-06-15): data.tracker = nº tracking,
  // data.url = PDF de la guía (S3), data.guide = PDF base64, data.idOrder = id Envíoclick.
  const d = body.data ?? body;
  const tracking_number = String(d.tracker ?? d.trackingNumber ?? d.tracking_number ?? "");
  const label_url = String(d.url ?? d.label ?? d.labelUrl ?? "");
  const label_pdf_b64 = String(d.guide ?? "");
  const tracking_url = buildTrackingUrl(rate.carrier, tracking_number);
  return { tracking_number, label_url, label_pdf_b64, tracking_url, id_order: String(d.idOrder ?? ""), raw: { idOrder: d.idOrder, deliveryType: d.deliveryType, deliveryDays: d.deliveryDays } };
}

// ── SHOPIFY ──────────────────────────────────────────────────────────────────
let _tok: { value: string; exp: number } | null = null;
async function getShopifyToken(): Promise<string> {
  const now = Date.now();
  if (_tok && _tok.exp > now + 60_000) return _tok.value;
  const resp = await fetch(`https://${SHOPIFY_SHOP}/admin/oauth/access_token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: SHOPIFY_CLIENT_ID, client_secret: SHOPIFY_CLIENT_SECRET, grant_type: "client_credentials" }),
  });
  if (!resp.ok) throw new Error(`shopify_oauth_${resp.status}:${(await resp.text()).slice(0, 200)}`);
  const data = await resp.json();
  _tok = { value: data.access_token, exp: now + (data.expires_in ?? 86400) * 1000 };
  return _tok.value;
}

// Crea el fulfillment con tracking. notify_customer:true → Shopify manda el email nativo
// "tu pedido va en camino" con el link de tracking (este es el "email transaccional al cliente").
async function shopifyFulfill(orderId: string | number, tn: string, trackingUrl: string, carrier: string): Promise<string | null> {
  const tok = await getShopifyToken();
  const r1 = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/orders/${orderId}/fulfillment_orders.json`, {
    headers: { "X-Shopify-Access-Token": tok },
  });
  if (!r1.ok) return null;
  const fos = ((await r1.json()).fulfillment_orders ?? []) as any[];
  const lineItemsByFo = fos
    .filter((fo) => ["open", "in_progress"].includes(fo.status))
    .map((fo) => ({
      fulfillment_order_id: fo.id,
      fulfillment_order_line_items: (fo.line_items ?? []).map((li: any) => ({ id: li.id, quantity: li.quantity })),
    }));
  if (!lineItemsByFo.length) return null;
  const payload = {
    fulfillment: {
      line_items_by_fulfillment_order: lineItemsByFo,
      tracking_info: { number: tn, url: trackingUrl, company: carrier.toUpperCase() },
      notify_customer: true,
    },
  };
  const r2 = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/fulfillments.json`, {
    method: "POST",
    headers: { "X-Shopify-Access-Token": tok, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (r2.status !== 200 && r2.status !== 201) return null;
  return String((await r2.json()).fulfillment?.id ?? "");
}

// ── GHL (escribe tracking_url de vuelta al contacto, best-effort) ─────────────
async function writeGhlTracking(contactId: string, trackingUrl: string): Promise<void> {
  if (!GHL_TOKEN || !contactId || !trackingUrl) return;
  try {
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json" },
      body: JSON.stringify({ customFields: [{ id: GHL_CF_TRACKING_URL, value: trackingUrl }] }),
    });
  } catch (_e) { /* best-effort */ }
}

// ── FLOW ─────────────────────────────────────────────────────────────────────
async function generateGuide(order: any) {
  const orderId = order.id ?? order.order_id;
  if (!orderId) return { ok: false, error: "order_id_missing" };

  const ship = order.shipping_address ?? {};
  const destZip = String(ship.zip ?? "").trim();
  if (!destZip) return { ok: false, error: "shipping_zip_missing" };

  const typeMap = await fetchProductTypes(order);
  const parcel = computeParcel(order, typeMap);
  const value = declaredValue(order);

  const rates = await ecQuote(parcel, destZip, value);
  if (!rates.length) return { ok: false, error: "no_rates", parcel };

  const shippingTitle = String(order.shipping_lines?.[0]?.title ?? "").toLowerCase();
  const express = shippingTitle.includes("express") || shippingTitle.includes("rapido");
  const rate = pickRate(rates, express);
  if (!rate) return { ok: false, error: "no_rate_selected", parcel };

  const reference = `Ferre24 ${order.name ?? `#${orderId}`}`;
  const guide = await ecCreateGuide(rate, parcel, { ...ship, email: ship.email || order.email || order.customer?.email }, value, reference);
  if (!guide.tracking_number) {
    return { ok: false, error: "guide_no_tracking", carrier: rate.carrier, parcel, ec_raw: guide.raw };
  }

  let fulfillmentId: string | null = null;
  try {
    fulfillmentId = await shopifyFulfill(orderId, guide.tracking_number, guide.tracking_url, rate.carrier);
  } catch (e) {
    fulfillmentId = `error:${(e as Error).message}`;
  }

  // GHL writeback (contact_id puede venir del note_attributes del bot, o de tags). Best-effort.
  const contactId = String(order.note_attributes?.find?.((a: any) => a.name === "ghl_contact_id")?.value ?? "");
  await writeGhlTracking(contactId, guide.tracking_url);

  return {
    ok: true,
    tracking_number: guide.tracking_number,
    tracking_url: guide.tracking_url,
    label_url: guide.label_url,
    label_pdf_b64: guide.label_pdf_b64,          // PDF de la guía (Make puede adjuntarlo al email de almacén)
    label_filename: `F24_GUIA_${guide.tracking_number}_${rate.carrier}.pdf`,
    id_order: guide.id_order,                     // id Envíoclick (registro / cancelación manual en panel)
    carrier: rate.carrier,
    service: rate.service,
    total: rate.total,
    delivery_days: rate.deliveryDays,
    parcel,
    needs_review: parcel.needs_review,   // >70kg (flete pesado) → conviene que Sergio lo revise
    fulfillment_id: fulfillmentId,
  };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") {
    return json({ ok: true, service: "f24-generate-guide", version: 1, modes: ["generate_guide"], carrier_pool: "Envioclick marketplace" });
  }
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const body = await req.json();
    const mode = String(body.mode ?? "generate_guide");
    if (mode !== "generate_guide") return json({ ok: false, error: `unknown_mode_${mode}` }, 200);
    const order = body.order ?? body;
    let result: any;
    try {
      result = await generateGuide(order);
    } catch (e) {
      // Capturar throws (Envíoclick 4xx, etc.) y devolver SIEMPRE 200 con ok:false para que
      // el router de Make dispare la alerta sin detener el scenario.
      result = { ok: false, error: String(e).slice(0, 400) };
    }
    return json({ ...result, mode, elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) {
    return json({ ok: false, error: String(e).slice(0, 400) }, 200);
  }
});
