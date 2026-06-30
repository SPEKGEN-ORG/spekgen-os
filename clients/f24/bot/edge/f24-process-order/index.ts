// f24-process-order — Supabase Edge Function (Deno)
//
// Convierte el objeto `order` que arma el bot de WhatsApp (Claude) en un Draft Order
// de Shopify y devuelve el invoice_url (link de pago seguro). El bot lo manda por WhatsApp.
//
// Mode: create_draft_order
//   body: {
//     mode: "create_draft_order",
//     line_items: [{ id: "GPH1000W", qty: 1 }, { id: "id:44164272259160", qty: 2 }],
//     customer: { name: "Juan Perez" },           // email YA NO se pide (es opcional aquí)
//     codigo_postal: "44100",                      // CP del cliente → se escribe en GHL
//     contact_id: "<ghl contact id>", phone: "<phone>", payment_method: "online|transferencia|msi_promo"
//   }
//   - id = SKU del catálogo, o "id:<variant_id>" cuando el producto no tiene SKU.
//   - Shopify pone el PRECIO desde la variante (no se hardcodean precios).
//   - MSI / envío / impuestos se resuelven en el checkout del invoice_url.
//
// Mode: save_cp  (guarda solo el código postal en el contacto GHL, sin crear orden)
//   body: { mode: "save_cp", contact_id: "<ghl>", codigo_postal: "44100" }
//   - Lo usa el bot cuando el cliente da su CP al preguntar por el envío (aún sin comprar).
//
// Mode: save_name  (guarda solo el firstName nativo del contacto GHL, sin crear orden)
//   body: { mode: "save_name", contact_id: "<ghl>", customer_name: "Juan" }
//   - Lo usa el bot cuando captura el nombre real ("¿con quién tengo el gusto?") para
//     reemplazar el alias basura de perfil de WhatsApp. Saneado server-side. Best-effort.
//
// Secrets (Supabase → Project Settings → Edge Functions secrets):
//   SHOPIFY_SHOP, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SHOPIFY_API_VERSION
//   (client-credentials OAuth, igual que el shopify_client.py de F24)

const SHOPIFY_SHOP = Deno.env.get("SHOPIFY_SHOP") ?? "0mtky1-q6.myshopify.com";
const SHOPIFY_CLIENT_ID = Deno.env.get("SHOPIFY_CLIENT_ID") ?? "";
const SHOPIFY_CLIENT_SECRET = Deno.env.get("SHOPIFY_CLIENT_SECRET") ?? "";
const SHOPIFY_API_VERSION = Deno.env.get("SHOPIFY_API_VERSION") ?? "2024-10";

// GHL (para escribir de vuelta el contexto de compra al contacto). Secret GHL_TOKEN = PIT F24.
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
// MercadoPago Cuenta B (9/12 MSI vía Link de Pago). Secret MP_CUENTAB_TOKEN.
const MP_TOKEN = Deno.env.get("MP_CUENTAB_TOKEN") ?? "";

// Crea un Link de Pago de MercadoPago (Cuenta B) con hasta 12 MSI para SKUs en promo.
// Resuelve título + precio de cada línea desde Shopify, arma la preference y devuelve el init_point.
async function createMpPromoLink(shopToken: string, items: any[], contactId: string) {
  if (!MP_TOKEN) return { ok: false, error: "no_mp_token" };
  const mpItems: any[] = [];
  for (const it of items) {
    const v = await resolveVariantFull(shopToken, it.id);
    if (!v) continue;
    mpItems.push({
      title: v.title.slice(0, 250),
      quantity: Math.max(1, parseInt(String(it.qty ?? 1), 10) || 1),
      unit_price: Number(v.price),
      currency_id: "MXN",
    });
  }
  if (!mpItems.length) return { ok: false, error: "no_items_resolved" };
  // external_reference lleva contactId + los SKUs:qty para que el webhook recree la orden Shopify.
  const skuList = items.map((it: any) => `${it.id}:${Math.max(1, parseInt(String(it.qty ?? 1), 10) || 1)}`).join(",");
  const resp = await fetch("https://api.mercadopago.com/checkout/preferences", {
    method: "POST",
    headers: { Authorization: `Bearer ${MP_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      items: mpItems,
      payment_methods: { installments: 12 },
      external_reference: `f24msi|${contactId || ""}|${skuList}`,
      notification_url: "https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-mp-webhook",
    }),
  });
  const data = await resp.json();
  if (!resp.ok || !data.init_point) return { ok: false, error: `mp_${resp.status}`, body: JSON.stringify(data).slice(0, 300) };
  const total = mpItems.reduce((s, i) => s + i.unit_price * i.quantity, 0);
  return { ok: true, pay_url: data.init_point, preference_id: data.id, total: total.toFixed(2), msi: true };
}

// Resuelve SKU/id → {title, price, tags} desde Shopify (para armar el item de MercadoPago
// y para el gate de elegibilidad 9/12 vía el tag msi-912).
async function resolveVariantFull(token: string, id: string): Promise<{ title: string; price: string; tags: string[] } | null> {
  const raw = String(id).trim();
  let q: string;
  if (raw.toLowerCase().startsWith("id:")) {
    const n = raw.slice(3).trim();
    const d = await gql(token, `{ productVariant(id: "gid://shopify/ProductVariant/${n}") { price product { title tags } } }`);
    const v = d?.productVariant;
    return v ? { title: v.product?.title ?? "Producto Ferre24", price: v.price, tags: v.product?.tags ?? [] } : null;
  }
  q = `sku:${raw}`;
  const d = await gql(token, `query($q: String!) { productVariants(first: 1, query: $q) { edges { node { price product { title tags } } } } }`, { q });
  const node = d?.productVariants?.edges?.[0]?.node;
  return node ? { title: node.product?.title ?? "Producto Ferre24", price: node.price, tags: node.product?.tags ?? [] } : null;
}
const GHL_CF = {
  numero_pedido: "ePF4Tr2ejgRp9z6WpJbq",
  tracking_url: "PitQVTnJJ0JreENWIBtz",
  purchase_count: "9d8uBdAau2ziDBDhGQF6",
  last_products: "KNHoFK29lQ94AN9vDIU2",
  last_purchase_value: "RiQ6mqWUd2c3cuGHokNL",
  // CP del cliente (campo GHL Contact, TEXT, creado 2026-06-24).
  codigo_postal: "Jj7yQO00RSf83wvrRqAv",
};

function cpFieldReady(): boolean {
  return !!GHL_CF.codigo_postal && !GHL_CF.codigo_postal.startsWith("__");
}

// Escribe campos custom en un contacto GHL (merge parcial). Best-effort.
async function putGhlCustomFields(contactId: string, customFields: Array<{ id: string; value: string }>): Promise<boolean> {
  if (!GHL_TOKEN || !contactId || !customFields.length) return false;
  try {
    const r = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json" },
      body: JSON.stringify({ customFields }),
    });
    return r.ok;
  } catch (_e) {
    return false;
  }
}

// Guarda SOLO el código postal en el contacto (mode=save_cp). NO toca purchase_count ni nada más.
async function saveCpOnly(contactId: string, cp: string): Promise<{ ok: boolean; error?: string }> {
  if (!cp) return { ok: false, error: "empty_cp" };
  if (!cpFieldReady()) return { ok: false, error: "cp_field_id_not_configured" };
  if (!GHL_TOKEN || !contactId) return { ok: false, error: "no_token_or_contact" };
  const ok = await putGhlCustomFields(contactId, [{ id: GHL_CF.codigo_postal, value: cp }]);
  return ok ? { ok: true } : { ok: false, error: "ghl_write_failed" };
}

// Sanea el nombre que captura el bot ("¿con quién tengo el gusto?") antes de escribirlo.
// El bot ya mandó un nombre real; aquí solo limpiamos: trim, sin emojis, primer nombre, cap 40.
// Devuelve "" si lo que llegó no parece un nombre (puro emoji/símbolo/número) → no se escribe.
function sanitizeFirstName(raw: string): string {
  let s = String(raw ?? "").trim();
  if (!s) return "";
  // Quita emojis y símbolos sueltos; deja letras (incl. acentos/ñ), espacios, guiones, apóstrofes.
  s = s.replace(/[^\p{L}\p{M}\s'\-.]/gu, "").replace(/\s+/g, " ").trim();
  if (s.length < 2) return "";
  // Toma el primer token (firstName), capitaliza inicial, capea a 40 chars.
  const first = s.split(" ")[0].slice(0, 40);
  if (first.length < 2) return "";
  return first.charAt(0).toUpperCase() + first.slice(1);
}

// Escribe SOLO el firstName nativo del contacto GHL (mode=save_name). Best-effort.
// Lo usa el bot cuando el cliente da su nombre y el firstName actual es el alias basura de WhatsApp.
async function saveFirstName(contactId: string, rawName: string): Promise<{ ok: boolean; error?: string; first_name?: string }> {
  const name = sanitizeFirstName(rawName);
  if (!name) return { ok: false, error: "invalid_name" };
  if (!GHL_TOKEN || !contactId) return { ok: false, error: "no_token_or_contact" };
  try {
    const r = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json" },
      body: JSON.stringify({ firstName: name }),
    });
    return r.ok ? { ok: true, first_name: name } : { ok: false, error: "ghl_write_failed" };
  } catch (_e) {
    return { ok: false, error: "ghl_exception" };
  }
}

// Escribe el contexto de la orden de vuelta al contacto en GHL (numero, productos, valor,
// link, +1 a purchase_count, y CP si viene). Best-effort — si falla, no rompe la creación de la orden.
async function writeGhlContext(contactId: string, ctx: {
  numero_pedido?: string; tracking_url?: string; last_products?: string; last_purchase_value?: string;
  codigo_postal?: string;
}): Promise<void> {
  if (!GHL_TOKEN || !contactId) return;
  try {
    // Leer purchase_count actual para incrementarlo
    let count = 0;
    const g = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, {
      headers: { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", Accept: "application/json" },
    });
    if (g.ok) {
      const cj = await g.json();
      const cf = (cj.contact?.customFields ?? []).find((f: any) => f.id === GHL_CF.purchase_count);
      count = parseInt(String(cf?.value ?? "0"), 10) || 0;
    }
    const customFields = [
      { id: GHL_CF.purchase_count, value: String(count + 1) },
    ];
    if (ctx.numero_pedido) customFields.push({ id: GHL_CF.numero_pedido, value: ctx.numero_pedido });
    if (ctx.tracking_url) customFields.push({ id: GHL_CF.tracking_url, value: ctx.tracking_url });
    if (ctx.last_products) customFields.push({ id: GHL_CF.last_products, value: ctx.last_products });
    if (ctx.last_purchase_value) customFields.push({ id: GHL_CF.last_purchase_value, value: ctx.last_purchase_value });
    if (ctx.codigo_postal && cpFieldReady()) customFields.push({ id: GHL_CF.codigo_postal, value: ctx.codigo_postal });
    await putGhlCustomFields(contactId, customFields);
  } catch (_e) { /* best-effort */ }
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ── Shopify token (client-credentials OAuth, TTL 24h) ──
let _tok: { value: string; exp: number } | null = null;
async function getShopifyToken(): Promise<string> {
  const now = Date.now();
  if (_tok && _tok.exp > now + 60_000) return _tok.value;
  const resp = await fetch(`https://${SHOPIFY_SHOP}/admin/oauth/access_token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: SHOPIFY_CLIENT_ID,
      client_secret: SHOPIFY_CLIENT_SECRET,
      grant_type: "client_credentials",
    }),
  });
  if (!resp.ok) throw new Error(`shopify_oauth_${resp.status}: ${(await resp.text()).slice(0, 300)}`);
  const data = await resp.json();
  _tok = { value: data.access_token, exp: now + (data.expires_in ?? 86400) * 1000 };
  return _tok.value;
}

async function gql(token: string, query: string, variables: Record<string, unknown> = {}) {
  const resp = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/graphql.json`, {
    method: "POST",
    headers: { "X-Shopify-Access-Token": token, "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });
  const data = await resp.json();
  if (data.errors) throw new Error(`gql: ${JSON.stringify(data.errors).slice(0, 300)}`);
  return data.data;
}

// Resuelve un id de línea (SKU o "id:NUMBER") al variant_id numérico de Shopify.
async function resolveVariantId(token: string, id: string): Promise<string | null> {
  const raw = String(id).trim();
  if (raw.toLowerCase().startsWith("id:")) {
    const n = raw.slice(3).trim();
    return /^\d+$/.test(n) ? n : null;
  }
  // Buscar por SKU
  const d = await gql(
    token,
    `query($q: String!) { productVariants(first: 1, query: $q) { edges { node { id } } } }`,
    { q: `sku:${raw}` },
  );
  const edge = d?.productVariants?.edges?.[0];
  if (!edge) return null;
  return String(edge.node.id).split("/").pop() ?? null;
}

async function createDraftOrder(body: any) {
  const token = await getShopifyToken();
  const items = Array.isArray(body.line_items) ? body.line_items : [];
  if (!items.length) return { ok: false, error: "no_line_items" };

  // CP del cliente: top-level o dentro de customer. Se escribe en GHL (best-effort).
  const cp = String(body.codigo_postal ?? body.customer?.codigo_postal ?? "").trim();

  // RAMA 9/12 MSI: SKU en promo + pago a meses → Link de Pago MercadoPago Cuenta B (hasta 12 MSI).
  // GATE: solo si TODOS los items tienen el tag "msi-912" en Shopify (lo pone sync_f24_promos.py
  // desde la hoja PROMO ACTIVA). Si alguno no es elegible, cae a draft order normal (hasta 6 MSI).
  if (String(body.payment_method ?? "") === "msi_promo") {
    const elig = await Promise.all(items.map(async (it: any) => {
      const v = await resolveVariantFull(token, it.id);
      return !!v && (v.tags ?? []).includes("msi-912");
    }));
    if (items.length > 0 && elig.every(Boolean)) {
      // Guarda el CP en GHL aunque esta rama no cree draft order Shopify.
      if (body.contact_id && cp) await saveCpOnly(body.contact_id, cp);
      return await createMpPromoLink(token, items, body.contact_id || "");
    }
    // No elegibles para 9/12 → continúa al flujo de draft order Shopify (checkout normal).
  }

  // Resolver cada SKU/id a variant_id (en paralelo)
  const resolved = await Promise.all(
    items.map(async (it: any) => ({
      variant_id: await resolveVariantId(token, it.id),
      quantity: Math.max(1, parseInt(String(it.qty ?? 1), 10) || 1),
      raw: it.id,
    })),
  );
  const missing = resolved.filter((r) => !r.variant_id).map((r) => r.raw);
  const line_items = resolved
    .filter((r) => r.variant_id)
    .map((r) => ({ variant_id: Number(r.variant_id), quantity: r.quantity }));
  if (!line_items.length) return { ok: false, error: "no_variants_resolved", missing };

  const cust = body.customer ?? {};
  const nameParts = String(cust.name ?? "").trim().split(/\s+/);
  const first_name = nameParts[0] ?? "";
  const last_name = nameParts.slice(1).join(" ");

  const draft_body: any = {
    draft_order: {
      line_items, // Shopify toma el precio de cada variante automáticamente
      note: `Pedido por bot WhatsApp${body.contact_id ? ` · GHL ${body.contact_id}` : ""}${cp ? ` · CP ${cp}` : ""}`,
      tags: "bot-whatsapp,ferre24-bot",
      use_customer_default_address: false,
    },
  };
  // email es OPCIONAL: solo se agrega si el cliente lo dio (ya no se pide para el link de pago).
  if (cust.email) {
    draft_body.draft_order.email = cust.email;
    draft_body.draft_order.customer = { email: cust.email, first_name, last_name };
  }

  const url = `https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/draft_orders.json`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "X-Shopify-Access-Token": token, "Content-Type": "application/json" },
    body: JSON.stringify(draft_body),
  });
  const text = await resp.text();
  if (!resp.ok) return { ok: false, error: `shopify_${resp.status}`, body: text.slice(0, 500) };
  const data = JSON.parse(text);
  const draft = data.draft_order;

  // Populador: escribe el contexto de la orden de vuelta al contacto en GHL (best-effort).
  if (body.contact_id) {
    const prods = resolved.map((r: any) => r.raw).join(", ");
    await writeGhlContext(body.contact_id, {
      numero_pedido: draft.name,
      tracking_url: draft.invoice_url,
      last_products: prods,
      last_purchase_value: String(draft.total_price ?? ""),
      codigo_postal: cp || undefined,
    });
  }

  // Link de pago ENVUELTO (tracking de clic) — el bot manda este, no el invoice_url crudo.
  const pay_url = `https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-pay?o=${draft.id}` +
    (body.contact_id ? `&c=${body.contact_id}` : "");
  return {
    ok: true,
    pay_url,                          // ← link envuelto con tracking (usar este)
    invoice_url: draft.invoice_url,   // link crudo (fallback)
    draft_order_id: draft.id,
    name: draft.name,
    total: draft.total_price,
    missing: missing.length ? missing : undefined,
  };
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") {
    return json({ ok: true, service: "f24-process-order", version: 4, modes: ["create_draft_order", "save_cp", "save_name"] });
  }
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const body = await req.json();
    const mode = String(body.mode ?? "create_draft_order");
    if (mode === "save_cp") {
      const result = await saveCpOnly(String(body.contact_id ?? ""), String(body.codigo_postal ?? "").trim());
      return json({ ...result, mode, elapsed_ms: Date.now() - t0 }, 200);
    }
    if (mode === "save_name") {
      const result = await saveFirstName(String(body.contact_id ?? ""), String(body.customer_name ?? ""));
      return json({ ...result, mode, elapsed_ms: Date.now() - t0 }, 200);
    }
    if (mode !== "create_draft_order") return json({ ok: false, error: `unknown_mode_${mode}` }, 400);
    const result = await createDraftOrder(body);
    // Siempre 200 para que Make no auto-pause; el bot decide por result.ok / invoice_url.
    return json({ ...result, mode, elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) {
    return json({ ok: false, error: String(e).slice(0, 400) }, 200);
  }
});
