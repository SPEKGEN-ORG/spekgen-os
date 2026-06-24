// f24-mp-webhook — Supabase Edge Function (Deno)
//
// Webhook de MercadoPago (Cuenta B). Cuando un Link de Pago 9/12 MSI se PAGA:
//   1. MP notifica aquí (notification_url de la preference).
//   2. Verificamos el pago con la API de MP (status approved).
//   3. Creamos la orden en Shopify marcada como PAGADA (inventario + fulfillment).
//   4. Taggeamos el contacto en GHL (pago-confirmado) — cierra el círculo.
//
// external_reference de la preference: "f24msi|{contactId}|{sku:qty,sku:qty}"
// Idempotente: si ya existe una orden con tag mp-{paymentId}, no duplica.

const SHOPIFY_SHOP = Deno.env.get("SHOPIFY_SHOP") ?? "0mtky1-q6.myshopify.com";
const SHOPIFY_CLIENT_ID = Deno.env.get("SHOPIFY_CLIENT_ID") ?? "";
const SHOPIFY_CLIENT_SECRET = Deno.env.get("SHOPIFY_CLIENT_SECRET") ?? "";
const SHOPIFY_API_VERSION = Deno.env.get("SHOPIFY_API_VERSION") ?? "2024-10";
const MP_TOKEN = Deno.env.get("MP_CUENTAB_TOKEN") ?? "";
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";

function ok(body: unknown = { ok: true }) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

async function shopToken(): Promise<string> {
  const r = await fetch(`https://${SHOPIFY_SHOP}/admin/oauth/access_token`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: SHOPIFY_CLIENT_ID, client_secret: SHOPIFY_CLIENT_SECRET, grant_type: "client_credentials" }),
  });
  return (await r.json()).access_token;
}

async function gql(token: string, query: string, variables: Record<string, unknown> = {}) {
  const r = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/graphql.json`, {
    method: "POST", headers: { "X-Shopify-Access-Token": token, "Content-Type": "application/json" },
    body: JSON.stringify({ query, variables }),
  });
  return (await r.json()).data;
}

async function variantIdForSku(token: string, id: string): Promise<number | null> {
  const raw = String(id).trim();
  if (raw.toLowerCase().startsWith("id:")) {
    const n = raw.slice(3).trim();
    return /^\d+$/.test(n) ? Number(n) : null;
  }
  const d = await gql(token, `query($q:String!){productVariants(first:1,query:$q){edges{node{id}}}}`, { q: `sku:${raw}` });
  const gid = d?.productVariants?.edges?.[0]?.node?.id;
  return gid ? Number(String(gid).split("/").pop()) : null;
}

async function orderExistsForPayment(token: string, paymentId: string): Promise<boolean> {
  const d = await gql(token, `query($q:String!){orders(first:1,query:$q){edges{node{id}}}}`, { q: `tag:mp-${paymentId}` });
  return (d?.orders?.edges?.length ?? 0) > 0;
}

async function tagGhl(contactId: string, tag: string, note: string) {
  if (!GHL_TOKEN || !contactId) return;
  const h = { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json" };
  try {
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/tags`, { method: "POST", headers: h, body: JSON.stringify({ tags: [tag] }) });
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, { method: "POST", headers: h, body: JSON.stringify({ body: note }) });
  } catch (_e) { /* best-effort */ }
}

Deno.serve(async (req: Request) => {
  try {
    const url = new URL(req.url);
    // MP manda el id por query (?data.id=) o por body { data: { id } }.
    let paymentId = url.searchParams.get("data.id") || url.searchParams.get("id") || "";
    const topic = url.searchParams.get("type") || url.searchParams.get("topic") || "";
    if (req.method === "POST") {
      try {
        const b = await req.json();
        paymentId = paymentId || String(b?.data?.id ?? b?.id ?? "");
      } catch (_e) { /* sin body json */ }
    }
    if (!paymentId) return ok({ ok: true, skip: "no_payment_id" });
    if (topic && topic !== "payment") return ok({ ok: true, skip: `topic_${topic}` });

    // 1. Verificar el pago con MP
    const pr = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
      headers: { Authorization: `Bearer ${MP_TOKEN}` },
    });
    if (!pr.ok) return ok({ ok: true, skip: `mp_${pr.status}` });
    const pay = await pr.json();
    if (pay.status !== "approved") return ok({ ok: true, skip: `status_${pay.status}` });

    const extRef = String(pay.external_reference ?? "");
    if (!extRef.startsWith("f24msi|")) return ok({ ok: true, skip: "not_f24msi" });
    const [, contactId, skuList] = extRef.split("|");
    const email = pay?.payer?.email || "";

    const token = await shopToken();
    if (await orderExistsForPayment(token, paymentId)) return ok({ ok: true, skip: "already_created" });

    // 2. Resolver SKUs → variantes
    const line_items: any[] = [];
    for (const part of (skuList || "").split(",").filter(Boolean)) {
      const [sku, qty] = part.split(":");
      const vid = await variantIdForSku(token, sku);
      if (vid) line_items.push({ variant_id: vid, quantity: Math.max(1, parseInt(qty || "1", 10) || 1) });
    }
    if (!line_items.length) return ok({ ok: true, skip: "no_variants" });

    // 3. Crear la orden en Shopify marcada como PAGADA
    const orderBody: any = {
      order: {
        line_items,
        financial_status: "paid",
        tags: `bot-whatsapp,ferre24-bot,msi-mp,mp-${paymentId}`,
        note: `Pago MercadoPago 9/12 MSI · payment ${paymentId} · GHL ${contactId || "-"}`,
        ...(email ? { email } : {}),
      },
    };
    const or = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/orders.json`, {
      method: "POST", headers: { "X-Shopify-Access-Token": token, "Content-Type": "application/json" },
      body: JSON.stringify(orderBody),
    });
    const otext = await or.text();
    if (!or.ok) return ok({ ok: false, error: `shopify_${or.status}`, body: otext.slice(0, 400) });
    const order = JSON.parse(otext).order;

    // 4. Cerrar el círculo en GHL
    await tagGhl(contactId, "pago-confirmado", `✅ Pago confirmado MercadoPago (9/12 MSI) · orden ${order.name} · $${pay.transaction_amount}`);

    return ok({ ok: true, order: order.name, order_id: order.id, payment: paymentId });
  } catch (e) {
    return ok({ ok: false, error: String(e).slice(0, 400) });
  }
});
