// f24-opp-track — Edge Function (Deno). Crea/mueve la oportunidad del bot F24 en el pipeline
// "Ventas Whatsapp" de GHL según avanza la conversación. Solo AVANZA etapas (idempotente, no regresa).
// Lo llama el bot (Make) best-effort tras parsear la respuesta de Claude. Secret: GHL_TOKEN.
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const LOC = "HNuSoIl2aCXP2DXEdMVZ";
const PIPELINE = "d8xeJjhr4wkmPv8xr5bA";  // Ventas Whatsapp (creado por Pedro 2026-06-17)
const STAGES = [
  { key: "nuevo", id: "27df7384-6789-40ae-a165-5a1a42c2a3bf" },      // 0 Nuevo lead
  { key: "calificado", id: "24098db0-7f73-4037-9cb2-86081a1f3953" }, // 1 Calificado
  { key: "cotizado", id: "19ba1a33-d13c-436e-9e02-6bfdd060d6d4" },   // 2 Cotizado
  { key: "link", id: "e327d976-ceb0-42a1-8155-2b44f3fecb05" },       // 3 Link de pago enviado
];
const H = { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json", Accept: "application/json" };

function json(body: unknown, status = 200): Response { return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }); }

// Etapa objetivo según la salida de Claude.
function targetPos(action: string, intent: string, products: string): number {
  if (action === "create_order") return 3;                 // mandó link de pago
  if (products && products.trim().length > 0) return 2;     // mencionó/cotizó producto
  if (["asking", "comparing", "ready_to_buy", "quoting", "negotiating", "qualified"].includes(intent)) return 1; // calificado
  return 0;                                                 // nuevo lead
}

async function currentPos(contactId: string): Promise<number> {
  try {
    const r = await fetch(`https://services.leadconnectorhq.com/opportunities/search?location_id=${LOC}&contact_id=${contactId}&pipeline_id=${PIPELINE}&limit=1`, { headers: H });
    if (!r.ok) return -1;
    const d = await r.json();
    const opp = d?.opportunities?.[0];
    if (!opp) return -1;
    return STAGES.findIndex((s) => s.id === opp.pipelineStageId);
  } catch (_e) { return -1; }
}

Deno.serve(async (req: Request) => {
  if (req.method === "GET") return json({ ok: true, service: "f24-opp-track", version: 1, pipeline: PIPELINE, stages: STAGES.map((s) => s.key) });
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const b = await req.json();
    const contactId = String(b.contact_id ?? "").trim();
    if (!contactId || !GHL_TOKEN) return json({ ok: false, error: "no_contact", elapsed_ms: Date.now() - t0 }, 200);
    const computed = targetPos(String(b.action ?? ""), String(b.intent ?? ""), String(b.products ?? ""));
    const cur = await currentPos(contactId);
    const target = Math.max(cur, computed, 0);
    // Al CREAR (cur === -1, aún no existe opp) trae el contacto para: (a) heredar su DUEÑO —el
    // round-robin 50/50 de GHL asigna al CONTACTO en el inbound pero la opp no lo hereda sola— y
    // (b) usar su NOMBRE real en la opp. Solo en creación → nunca pisa reasignación/nombre existente.
    let assignedTo: string | undefined, contactName = "";
    if (cur === -1) {
      try {
        const cr = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, { headers: H });
        if (cr.ok) {
          const c = (await cr.json())?.contact ?? {};
          assignedTo = c.assignedTo || undefined;
          contactName = (c.contactName || [c.firstName, c.lastName].filter(Boolean).join(" ") || "").trim();
        }
      } catch (_e) { /* best-effort */ }
    }
    const name = (String(b.name ?? "").trim() || contactName || "Lead WhatsApp").slice(0, 100);
    const up = await fetch("https://services.leadconnectorhq.com/opportunities/upsert", {
      method: "POST", headers: H,
      body: JSON.stringify({ pipelineId: PIPELINE, locationId: LOC, contactId, name, status: "open", pipelineStageId: STAGES[target].id, ...(assignedTo ? { assignedTo } : {}) }),
    });
    let resp: any = null; try { resp = await up.json(); } catch { /* */ }
    console.log(`[opp-track] contact=${contactId} cur=${cur} computed=${computed} target=${STAGES[target].key} ok=${up.ok}`);
    return json({ ok: up.ok, stage: STAGES[target].key, curPos: cur, computed, target, err: up.ok ? undefined : JSON.stringify(resp).slice(0, 250), elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) { return json({ ok: false, error: String(e).slice(0, 300), elapsed_ms: Date.now() - t0 }, 200); }
});
