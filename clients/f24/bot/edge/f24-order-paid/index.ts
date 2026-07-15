// f24-order-paid — Supabase Edge Function (Deno)
//
// Webhook de Shopify `orders/paid`. Cierra el círculo del checkout NORMAL (draft order → invoice_url):
// cuando el cliente PAGA en Shopify, marca la oportunidad de GHL como GANADA (status:won) con el
// valor NETO de producto (sin envío/impuestos).
//
// Por qué existe: el bot avanza la opp hasta "Link de pago enviado" (edge `f24-opp-track`), pero nada
// escuchaba el pago del checkout normal → la opp se quedaba OPEN para siempre. (La rama MercadoPago
// 9/12 MSI ya cierra su opp desde `f24-mp-webhook`; este cubre TODO lo demás — y es idempotente si
// ambos disparan sobre la misma orden.)
//
// Mapeo orden → contacto GHL: `f24-process-order` estampa "· GHL <contactId>" en `order.note` al crear
// el draft; Shopify copia esa nota a la orden real al completarse. Lo parseamos de ahí.
//
// Idempotente: marcar won repetidas veces es inocuo. Shopify puede reintentar el webhook.
// Secret: GHL_TOKEN (ya seteado a nivel proyecto, igual que las demás edge functions F24).

const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const GHL_LOC = "HNuSoIl2aCXP2DXEdMVZ";
const GHL_PIPELINE = "d8xeJjhr4wkmPv8xr5bA"; // Ventas Whatsapp

function ok(body: unknown = { ok: true }) {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
}

const H = { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json", Accept: "application/json" };

// Saca el contactId de GHL de la nota de la orden ("... · GHL abc123XYZ · CP 44100").
function contactIdFromNote(note: string): string {
  const m = /GHL\s+([A-Za-z0-9]+)/.exec(note || "");
  return m ? m[1] : "";
}

// Marca la opp del contacto como won con el valor neto. Best-effort.
async function markOppWon(contactId: string, netValue: number): Promise<string> {
  if (!GHL_TOKEN || !contactId) return "no_token_or_contact";
  const sr = await fetch(`https://services.leadconnectorhq.com/opportunities/search?location_id=${GHL_LOC}&contact_id=${contactId}&pipeline_id=${GHL_PIPELINE}&limit=1`, { headers: H });
  if (!sr.ok) return `search_${sr.status}`;
  const opp = (await sr.json())?.opportunities?.[0];
  if (!opp?.id) return "no_opp"; // no existe opp en este pipeline; no la inventamos aquí
  const body: Record<string, unknown> = { status: "won" };
  if (Number.isFinite(netValue) && netValue > 0) body.monetaryValue = netValue;
  const up = await fetch(`https://services.leadconnectorhq.com/opportunities/${opp.id}`, { method: "PUT", headers: H, body: JSON.stringify(body) });
  return up.ok ? "won" : `update_${up.status}`;
}

async function tagContact(contactId: string, tag: string, note: string) {
  if (!GHL_TOKEN || !contactId) return;
  try {
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/tags`, { method: "POST", headers: H, body: JSON.stringify({ tags: [tag] }) });
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, { method: "POST", headers: H, body: JSON.stringify({ body: note }) });
  } catch (_e) { /* best-effort */ }
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") return ok({ ok: true, service: "f24-order-paid", version: 1, pipeline: GHL_PIPELINE });
  if (req.method !== "POST") return ok({ ok: false, error: "method_not_allowed" });
  const t0 = Date.now();
  try {
    const order = await req.json();
    const tags = String(order?.tags ?? "");
    const note = String(order?.note ?? "");
    // Gate: solo órdenes del bot F24 (evita procesar órdenes ajenas si el webhook se suscribe amplio).
    const contactId = contactIdFromNote(note);
    if (!contactId) return ok({ ok: true, skip: "no_ghl_contact_in_note", tags_seen: tags.slice(0, 60) });

    // Valor NETO = producto tras descuentos, SIN envío ni impuestos.
    const net = Number(order?.current_subtotal_price ?? order?.subtotal_price ?? 0);
    const result = await markOppWon(contactId, net);
    // Paridad con la rama MercadoPago: tag + nota en el contacto.
    await tagContact(contactId, "pago-confirmado", `✅ Pago confirmado Shopify · orden ${order?.name ?? "-"} · neto $${net}`);

    console.log(`[order-paid] order=${order?.name} contact=${contactId} net=${net} result=${result}`);
    return ok({ ok: true, order: order?.name, contact: contactId, net, result, elapsed_ms: Date.now() - t0 });
  } catch (e) {
    return ok({ ok: false, error: String(e).slice(0, 300), elapsed_ms: Date.now() - t0 });
  }
});
