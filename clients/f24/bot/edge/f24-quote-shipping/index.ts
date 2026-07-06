// f24-quote-shipping — Supabase Edge Function (Deno)
//
// Cotiza el FLETE REAL de un envío de Ferre24 con la API de cotización de Skydropx Pro
// (cuenta propia F24), para que el bot de WhatsApp deje de escalar / usar la referencia
// interna del ~10% y le dé al cliente la tarifa real por su CP.
//
// NOTA IMPORTANTE (verificado empíricamente 2026-07-06): la API de cotización de Skydropx
// cotiza PURAMENTE por CP. Los campos area_level1/2/3 son OBLIGATORIOS (no-blank) pero su
// VALOR no altera la tarifa (probado con colonia correcta, colonia basura y hasta estado
// equivocado → misma tarifa). Por eso NO se necesita resolver la colonia real (SEPOMEX) para
// cotizar: basta el CP + rellenar los area_levels con un valor no-vacío. El estado se deriva
// del prefijo de 2 dígitos del CP (offline, nunca falla) solo por sanidad de datos.
//
// Esto es SOLO cotización — NO genera guía (eso lo hace f24-generate-guide, cuenta Envíoclick de
// Sergio). El bloqueo del "carrier service" de Skydropx en el checkout Shopify es otro tema
// (en escalamiento con soporte Skydropx) y NO afecta esta cotización directa.
//
// Modo único: quote (default). Patrón "siempre 200" para que el router de Make no se detenga:
// aun sin cobertura, regresa ok:false + un `mensaje` de fallback listo para enviar al cliente.
//
// Input (POST JSON):
//   { cp_destino: "06700",           // REQUERIDO
//     skus?: ["GPH1000W", ...],       // opcional: SKUs mencionados por el bot (products_mentioned)
//     items?: [{ sku|id, qty }],      // opcional: forma rica con cantidades
//     peso_kg?: number,               // opcional: override de peso total (kg)
//     valor?: number }                // opcional: valor declarado para el seguro
//
// Output:
//   { ok:true, cp, cheapest:{carrier,service,total,days}, alternatives:[…], parcel, mensaje }
//   { ok:false, error, mensaje }      // mensaje = fallback natural para el cliente
//
// Secrets (env; fallback constante = patrón agencia, igual que f24-generate-guide / f24-skydropx-webhook):
//   SKYDROPX_CLIENT_ID, SKYDROPX_CLIENT_SECRET  (cuenta propia Ferre24, alta 2026-07)
//   SHOPIFY_SHOP, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_API_VERSION (ya secrets del proyecto)

const SKYDROPX_BASE = (Deno.env.get("SKYDROPX_API_BASE") ?? "https://pro.skydropx.com/api/v1").replace(/\/$/, "");
const SKYDROPX_CLIENT_ID = Deno.env.get("SKYDROPX_CLIENT_ID")
  ?? "2WoPcb8tsm8UFJN9_y9CgXxcCcPmwRCHNp-hUBdPqFM";
const SKYDROPX_CLIENT_SECRET = Deno.env.get("SKYDROPX_CLIENT_SECRET")
  ?? "lDZqQqbGgqK_yQfPB_7RqsbxrE9BRCbYqjoinrpEnxI";

// Cloudflare bloquea requests sin User-Agent de navegador (403). OBLIGATORIO en todo fetch a Skydropx.
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

const SHOPIFY_SHOP = Deno.env.get("SHOPIFY_SHOP") ?? "0mtky1-q6.myshopify.com";
const SHOPIFY_CLIENT_ID = Deno.env.get("SHOPIFY_CLIENT_ID") ?? "";
const SHOPIFY_CLIENT_SECRET = Deno.env.get("SHOPIFY_CLIENT_SECRET") ?? "";
const SHOPIFY_API_VERSION = Deno.env.get("SHOPIFY_API_VERSION") ?? "2024-10";

// ── ORIGEN (bodega Marvelsa, template default en Skydropx "Ferre24 - Marvelsa (GDL)") ──────────
// Override por env sin redeploy. area_level3 no afecta la tarifa; se deja el real por sanidad.
const ORIGIN = {
  country_code: "mx",
  postal_code: Deno.env.get("SKYDROPX_ORIGIN_ZIP") ?? "45640",
  area_level1: Deno.env.get("SKYDROPX_ORIGIN_STATE") ?? "Jalisco",
  area_level2: Deno.env.get("SKYDROPX_ORIGIN_CITY") ?? "Tlajomulco de Zuniga",
  area_level3: Deno.env.get("SKYDROPX_ORIGIN_HOOD") ?? "Santa Cruz del Valle",
};

// Carriers a cotizar. Marketplace estándar F24 (mismos que ya cotiza la cuenta).
const REQUESTED_CARRIERS = ["fedex", "dhl", "estafeta", "paquetexpress", "ampm"];

// Nombres bonitos por carrier para el mensaje al cliente.
const CARRIER_LABEL: Record<string, string> = {
  fedex: "FedEx", dhl: "DHL", estafeta: "Estafeta",
  paquetexpress: "Paquetexpress", ampm: "AMPM", noventa9minutos: "99minutos",
};

// ── PARCEL (perfil por categoría — reusa la lógica validada de f24-generate-guide) ─────────────
// Shopify no guarda dimensiones (solo peso, a veces mal importado). Estrategia híbrida:
//   DIMENSIONES: perfil por keyword (product_type + título). PESO: el de Shopify si es plausible
//   vs el perfil; si no, el del perfil (auto-corrige pesos basura).
interface Profile { name: string; kg: number; length: number; width: number; height: number; }
const PROFILES: { match: RegExp; p: Profile }[] = [
  { match: /navaja|victorinox|multitool|multiusos/i, p: { name: "Navaja", kg: 0.3, length: 14, width: 10, height: 4 } },
  { match: /osmosis|ósmosis|ultrafiltr|purific|filtr|punto de uso|pou/i, p: { name: "Filtro agua", kg: 12, length: 50, width: 40, height: 35 } },
  { match: /jardin|jardín|pasto|cortaseto|orillador|sintétic|tijera|manguera|herramienta de/i, p: { name: "Jardín ligero", kg: 4, length: 40, width: 25, height: 18 } },
  { match: /generador|compresor|soldadora|compactadora|parihuela|diésel|diesel|inverter/i, p: { name: "Máquina pesada", kg: 60, length: 72, width: 56, height: 60 } },
  { match: /motobomba|bomba|sumergible|motor|hidrolavadora|desbrozadora|motosierra|podadora|soplador|ahoyadora|escarific|peinadora|barredora|presuriz|tanque|calentador|centrífuga|2t|4 tiempos|gasolina/i, p: { name: "Equipo gasolina", kg: 25, length: 56, width: 46, height: 46 } },
];
const DEFAULT_PROFILE: Profile = { name: "General", kg: 15, length: 50, width: 40, height: 35 };

function pickProfile(text: string): Profile {
  for (const { match, p } of PROFILES) if (match.test(text)) return p;
  return DEFAULT_PROFILE;
}
// Confía en el peso de Shopify si cae en [0.25×, 4×] del perfil; si no, usa el del perfil.
function saneWeight(gramsKg: number, profileKg: number): number {
  if (gramsKg > 0 && gramsKg >= profileKg * 0.25 && gramsKg <= profileKg * 4) return gramsKg;
  return profileKg;
}

interface Parcel { weight: number; length: number; width: number; height: number; box_name: string; }
interface ItemInfo { title: string; ptype: string; grams: number; qty: number; }

function computeParcel(items: ItemInfo[]): Parcel {
  let totalKg = 0;
  let big: Profile = DEFAULT_PROFILE;
  for (const it of items) {
    const prof = pickProfile(`${it.ptype} ${it.title}`);
    const unitKg = saneWeight((it.grams || 0) / 1000, prof.kg);
    const qty = it.qty > 0 ? it.qty : 1;
    totalKg += unitKg * qty;
    if (prof.length * prof.width * prof.height > big.length * big.width * big.height) big = prof;
  }
  let kg = Math.round(totalKg * 100) / 100;
  if (kg <= 0) kg = big.kg;
  return { weight: kg, length: big.length, width: big.width, height: big.height, box_name: big.name };
}

// ── SHOPIFY (SKU → título / product_type / peso). Best-effort: si falla, se usa DEFAULT_PROFILE. ──
let _shopTok: { value: string; exp: number } | null = null;
async function getShopifyToken(): Promise<string> {
  const now = Date.now();
  if (_shopTok && _shopTok.exp > now + 60_000) return _shopTok.value;
  const resp = await fetch(`https://${SHOPIFY_SHOP}/admin/oauth/access_token`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: SHOPIFY_CLIENT_ID, client_secret: SHOPIFY_CLIENT_SECRET, grant_type: "client_credentials" }),
  });
  if (!resp.ok) throw new Error(`shopify_oauth_${resp.status}`);
  const data = await resp.json();
  _shopTok = { value: data.access_token, exp: now + (data.expires_in ?? 86400) * 1000 };
  return data.access_token;
}

// Resuelve una lista de {sku, qty} a ItemInfo[] consultando Shopify por SKU (1 sola query GraphQL).
async function resolveItems(rawItems: { sku: string; qty: number }[]): Promise<ItemInfo[]> {
  const wanted = rawItems.filter((x) => x.sku);
  if (!wanted.length || !SHOPIFY_CLIENT_ID) {
    // Sin SKUs o sin creds → 1 ítem genérico (DEFAULT_PROFILE vía computeParcel).
    return [{ title: "", ptype: "", grams: 0, qty: 1 }];
  }
  try {
    const tok = await getShopifyToken();
    // Busca por SKU: `sku:X OR sku:Y`. En API 2024-10 el peso vive en
    // inventoryItem.measurement.weight {value,unit} (ya NO en ProductVariant.weight).
    const q = wanted.map((w) => `sku:${JSON.stringify(w.sku)}`).join(" OR ");
    const query = `{ productVariants(first: 50, query: ${JSON.stringify(q)}) { edges { node { sku inventoryItem { measurement { weight { value unit } } } product { title productType } } } } }`;
    const r = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/graphql.json`, {
      method: "POST", headers: { "X-Shopify-Access-Token": tok, "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const d = await r.json();
    const bySku: Record<string, { title: string; ptype: string; grams: number }> = {};
    for (const e of d.data?.productVariants?.edges ?? []) {
      const n = e.node;
      const meas = n.inventoryItem?.measurement?.weight;
      const w = Number(meas?.value ?? 0);
      const unit = String(meas?.unit ?? "KILOGRAMS").toUpperCase();
      const grams = unit === "KILOGRAMS" ? w * 1000 : unit === "GRAMS" ? w : unit === "POUNDS" ? w * 453.592 : unit === "OUNCES" ? w * 28.35 : w * 1000;
      if (n.sku) bySku[String(n.sku)] = { title: n.product?.title ?? "", ptype: n.product?.productType ?? "", grams };
    }
    const out: ItemInfo[] = [];
    for (const w of wanted) {
      const info = bySku[w.sku];
      out.push(info ? { ...info, qty: w.qty } : { title: w.sku, ptype: "", grams: 0, qty: w.qty });
    }
    return out.length ? out : [{ title: "", ptype: "", grams: 0, qty: 1 }];
  } catch {
    return wanted.map((w) => ({ title: w.sku, ptype: "", grams: 0, qty: w.qty }));
  }
}

// ── CP → estado (prefijo de 2 dígitos). Offline, nunca falla. Solo sanidad — no afecta tarifa. ──
const CP_STATE: [number, number, string][] = [
  [0, 16, "Ciudad de Mexico"], [20, 20, "Aguascalientes"], [21, 22, "Baja California"],
  [23, 23, "Baja California Sur"], [24, 24, "Campeche"], [25, 27, "Coahuila"], [28, 28, "Colima"],
  [29, 30, "Chiapas"], [31, 33, "Chihuahua"], [34, 35, "Durango"], [36, 38, "Guanajuato"],
  [39, 41, "Guerrero"], [42, 43, "Hidalgo"], [44, 49, "Jalisco"], [50, 57, "Estado de Mexico"],
  [58, 61, "Michoacan"], [62, 62, "Morelos"], [63, 63, "Nayarit"], [64, 67, "Nuevo Leon"],
  [68, 71, "Oaxaca"], [72, 75, "Puebla"], [76, 76, "Queretaro"], [77, 77, "Quintana Roo"],
  [78, 79, "San Luis Potosi"], [80, 82, "Sinaloa"], [83, 85, "Sonora"], [86, 86, "Tabasco"],
  [87, 89, "Tamaulipas"], [90, 90, "Tlaxcala"], [91, 96, "Veracruz"], [97, 97, "Yucatan"],
  [98, 99, "Zacatecas"],
];
function stateFromCp(cp: string): string {
  const pre = parseInt(cp.slice(0, 2), 10);
  if (!isNaN(pre)) for (const [lo, hi, name] of CP_STATE) if (pre >= lo && pre <= hi) return name;
  return "Mexico";
}

// ── SKYDROPX (OAuth client_credentials + quotation + poll rates) ────────────────────────────────
function skyHeaders(tok?: string) {
  const h: Record<string, string> = { "User-Agent": UA, "Content-Type": "application/json", "Accept": "application/json" };
  if (tok) h["Authorization"] = `Bearer ${tok}`;
  return h;
}

let _skyTok: { value: string; exp: number } | null = null;
async function getSkyToken(): Promise<string> {
  const now = Date.now();
  if (_skyTok && _skyTok.exp > now + 60_000) return _skyTok.value;
  const r = await fetch(`${SKYDROPX_BASE}/oauth/token`, {
    method: "POST", headers: skyHeaders(),
    body: JSON.stringify({
      grant_type: "client_credentials",
      client_id: SKYDROPX_CLIENT_ID, client_secret: SKYDROPX_CLIENT_SECRET,
      scope: "default orders.create",
    }),
  });
  if (!r.ok) throw new Error(`skydropx_oauth_${r.status}:${(await r.text()).slice(0, 160)}`);
  const data = await r.json();
  _skyTok = { value: data.access_token, exp: now + Number(data.expires_in ?? 3600) * 1000 };
  return data.access_token;
}

interface Rate { carrier: string; service: string; total: number; days: number; }

async function createQuotation(tok: string, cpDestino: string, parcel: Parcel): Promise<string> {
  const payload = {
    quotation: {
      address_from: { ...ORIGIN },
      address_to: {
        country_code: "mx", postal_code: cpDestino,
        // Valores no-vacíos (obligatorio) — no afectan la tarifa (cotiza por CP).
        area_level1: stateFromCp(cpDestino), area_level2: "Centro", area_level3: "Centro",
      },
      parcel: { length: parcel.length, width: parcel.width, height: parcel.height, weight: parcel.weight },
      requested_carriers: REQUESTED_CARRIERS,
    },
  };
  const r = await fetch(`${SKYDROPX_BASE}/quotations`, { method: "POST", headers: skyHeaders(tok), body: JSON.stringify(payload) });
  if (r.status !== 200 && r.status !== 201) throw new Error(`quotation_${r.status}:${(await r.text()).slice(0, 240)}`);
  const body = await r.json();
  const qid = body.id ?? body.data?.id;
  if (!qid) throw new Error("quotation_no_id");
  return qid;
}

async function pollRates(tok: string, qid: string, maxAttempts = 12): Promise<Rate[]> {
  for (let i = 0; i < maxAttempts; i++) {
    const r = await fetch(`${SKYDROPX_BASE}/quotations/${qid}`, { headers: skyHeaders(tok) });
    if (r.ok) {
      const body = await r.json();
      const rates = (body.rates ?? []) as any[];
      const priced = rates.filter((x) => (x.status ?? x.rate_status) === "price_found_internal");
      // Espera a que la cotización termine o haya suficientes tarifas para no cortar carriers lentos.
      if (priced.length && (body.is_completed || priced.length >= 3 || i >= 4)) {
        return priced.map((x) => ({
          carrier: String(x.provider_name ?? x.provider ?? "").toLowerCase(),
          service: String(x.provider_service_name ?? x.service_level_name ?? x.service_level_code ?? ""),
          total: parseFloat(x.total ?? x.amount ?? "9e9"),
          days: parseInt(String(x.days ?? x.estimated_delivery ?? "0"), 10) || 0,
        })).filter((r) => r.total < 9e8);
      }
    }
    await new Promise((res) => setTimeout(res, 1800));
  }
  return [];
}

function fmtMoney(n: number): string {
  return "$" + (Math.round(n * 100) / 100).toLocaleString("es-MX", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}
function carrierLabel(c: string): string { return CARRIER_LABEL[c] ?? (c ? c.charAt(0).toUpperCase() + c.slice(1) : "paquetería"); }

function buildMensaje(cp: string, cheapest: Rate): string {
  const dias = cheapest.days > 0
    ? (cheapest.days === 1 ? "llega en 1 día hábil" : `llega en ${cheapest.days} días hábiles`)
    : "tiempo de entrega según destino";
  return `El envío a tu CP ${cp} sale en ${fmtMoney(cheapest.total)} MXN con ${carrierLabel(cheapest.carrier)} 📦 — ${dias}. ¿Te lo armo?`;
}
const FALLBACK_MSG = "Déjame confirmar el costo exacto del envío a tu CP con el equipo y te lo paso en un momento 📦";

// ── FLOW ─────────────────────────────────────────────────────────────────────────────────────
async function quote(input: any) {
  const cp = String(input.cp_destino ?? input.codigo_postal ?? "").replace(/\D/g, "").trim();
  if (cp.length < 5) return { ok: false, error: "cp_invalido", mensaje: "¿Me confirmas tu código postal (5 dígitos)? Con eso te cotizo el envío 📦" };

  // Normaliza items: acepta items[{sku|id,qty}] o skus[string] (products_mentioned del bot).
  let rawItems: { sku: string; qty: number }[] = [];
  if (Array.isArray(input.items) && input.items.length) {
    rawItems = input.items.map((it: any) => ({ sku: String(it.sku ?? it.id ?? "").replace(/^id:/, ""), qty: parseInt(String(it.qty ?? it.quantity ?? 1), 10) || 1 }));
  } else if (Array.isArray(input.skus) && input.skus.length) {
    rawItems = input.skus.map((s: any) => ({ sku: String(s ?? "").replace(/^id:/, ""), qty: 1 }));
  } else if (Array.isArray(input.products_mentioned) && input.products_mentioned.length) {
    rawItems = input.products_mentioned.map((s: any) => ({ sku: String(s ?? "").replace(/^id:/, ""), qty: 1 }));
  }

  // Peso: override explícito si viene; si no, resolvemos por Shopify + perfiles.
  let parcel: Parcel;
  if (Number(input.peso_kg) > 0) {
    const p = DEFAULT_PROFILE;
    parcel = { weight: Number(input.peso_kg), length: p.length, width: p.width, height: p.height, box_name: "override" };
  } else {
    const items = await resolveItems(rawItems);
    parcel = computeParcel(items);
  }

  const tok = await getSkyToken();
  const qid = await createQuotation(tok, cp, parcel);
  const rates = await pollRates(tok, qid);
  if (!rates.length) return { ok: false, error: "no_rates", cp, quotation_id: qid, parcel, mensaje: FALLBACK_MSG };

  rates.sort((a, b) => a.total - b.total);
  const cheapest = rates[0];
  const alternatives = rates.slice(0, 3).map((r) => ({ carrier: carrierLabel(r.carrier), service: r.service, total: r.total, days: r.days }));

  return {
    ok: true, cp,
    cheapest: { carrier: carrierLabel(cheapest.carrier), service: cheapest.service, total: cheapest.total, days: cheapest.days },
    alternatives, parcel, quotation_id: qid,
    mensaje: buildMensaje(cp, cheapest),
  };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") return json({ ok: true, service: "f24-quote-shipping", version: 1, modes: ["quote"] });
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const body = await req.json().catch(() => ({}));
    let result: any;
    try {
      result = await quote(body);
    } catch (e) {
      // Siempre 200 con ok:false + fallback → el router de Make no se detiene y el cliente recibe algo.
      result = { ok: false, error: String(e).slice(0, 300), mensaje: FALLBACK_MSG };
    }
    return json({ ...result, elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) {
    return json({ ok: false, error: String(e).slice(0, 300), mensaje: FALLBACK_MSG }, 200);
  }
});
