// f24-opp-track — Edge Function (Deno). Crea/mueve la oportunidad del bot F24 en el pipeline
// "Ventas Whatsapp" de GHL según avanza la conversación. Solo AVANZA etapas (idempotente, no regresa).
// Lo llama el bot (Make) best-effort tras parsear la respuesta de Claude. Secret: GHL_TOKEN.
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const LOC = "HNuSoIl2aCXP2DXEdMVZ";
const PIPELINE = "d8xeJjhr4wkmPv8xr5bA";  // Ventas Whatsapp (creado por Pedro 2026-06-17)
// Vendedores para el split 50/50 A NIVEL OPORTUNIDAD (2026-07-07). El dueño del CONTACTO pasa a
// ser el usuario "Ferre24 Bot" (abajo), NO un vendedor, para que los mensajes del bot no aparezcan
// en el inbox como si Edgar/Alfredo los hubieran mandado. Las comisiones leen opp.assignedTo, así
// que el reparto de vendedor se hace aquí sobre la OPP. (El workflow GHL "Atribucion", que asignaba
// el contacto a un vendedor, quedó DESPUBLICADO — su función se movió aquí. NO re-publicar.)
const SELLERS = ["6G3VFN9NMm2J2zBGJkGC", "1Yee3JNNWlFSk6SWFzeT"]; // Edgar, Alfredo Torres
// Usuario "Ferre24 Bot" (RgGX1Uid50v4mHf6ekVq). Se pone como DUEÑO DEL CONTACTO al crear la opp,
// para que los mensajes del bot (outbound sin userId) se pinten en el inbox de GHL como "Ferre24 Bot"
// en vez de heredar la cara de un vendedor. GHL no permite firmar mensajes de API con un userId, así
// que la única palanca de display es el dueño del contacto. Los vendedores trackean por el pipeline.
const BOT_USER = "RgGX1Uid50v4mHf6ekVq";
const STAGES = [
  { key: "nuevo", id: "27df7384-6789-40ae-a165-5a1a42c2a3bf" },      // 0 Nuevo lead
  { key: "calificado", id: "24098db0-7f73-4037-9cb2-86081a1f3953" }, // 1 Calificado
  { key: "cotizado", id: "19ba1a33-d13c-436e-9e02-6bfdd060d6d4" },   // 2 Cotizado
  { key: "link", id: "e327d976-ceb0-42a1-8155-2b44f3fecb05" },       // 3 Link de pago enviado
];
const H = { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json", Accept: "application/json" };

function json(body: unknown, status = 200): Response { return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }); }

// Round-robin 50/50 DETERMINÍSTICO por contactId: sin estado, pegajoso (un mismo contacto
// siempre cae con el mismo vendedor → re-cotizaciones no cambian de dueño), ~50/50 sobre volumen.
function pickSeller(contactId: string): string {
  let h = 0;
  for (let i = 0; i < contactId.length; i++) h = (h * 31 + contactId.charCodeAt(i)) >>> 0;
  return SELLERS[h % SELLERS.length];
}

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
  if (req.method === "GET") return json({ ok: true, service: "f24-opp-track", version: 4, pipeline: PIPELINE, stages: STAGES.map((s) => s.key), split: "opp-level 50/50 (Edgar/Alfredo)", contact_owner: "Ferre24 Bot" });
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const b = await req.json();
    const contactId = String(b.contact_id ?? "").trim();
    if (!contactId || !GHL_TOKEN) return json({ ok: false, error: "no_contact", elapsed_ms: Date.now() - t0 }, 200);
    const computed = targetPos(String(b.action ?? ""), String(b.intent ?? ""), String(b.products ?? ""));
    const cur = await currentPos(contactId);
    const target = Math.max(cur, computed, 0);
    // Al CREAR (cur === -1, aún no existe opp) trae el contacto para: (a) DECIDIR EL DUEÑO de la opp
    // y (b) usar su NOMBRE real. Regla de dueño: si el contacto YA lo tiene un vendedor conocido
    // (Edgar/Alfredo — p.ej. lo tomó a mano, o transición antes de mover el workflow), la opp lo
    // hereda. Si no (dueño = "Ferre24 Bot", vacío, u otro), se hace el split 50/50 determinístico.
    // Solo en creación → nunca pisa reasignación/nombre de una opp existente.
    let assignedTo: string | undefined, contactName = "";
    if (cur === -1) {
      let existingOwner = "";
      try {
        const cr = await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, { headers: H });
        if (cr.ok) {
          const c = (await cr.json())?.contact ?? {};
          existingOwner = c.assignedTo || "";
          contactName = (c.contactName || [c.firstName, c.lastName].filter(Boolean).join(" ") || "").trim();
        }
      } catch (_e) { /* best-effort */ }
      assignedTo = SELLERS.includes(existingOwner) ? existingOwner : pickSeller(contactId);
      // Dueño del CONTACTO = Ferre24 Bot (salvo que un vendedor humano ya lo tenga tomado). Best-effort.
      if (!SELLERS.includes(existingOwner)) {
        try {
          await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}`, {
            method: "PUT", headers: H, body: JSON.stringify({ assignedTo: BOT_USER }),
          });
        } catch (_e) { /* best-effort */ }
      }
    }
    const name = (String(b.name ?? "").trim() || contactName || "Lead WhatsApp").slice(0, 100);
    const up = await fetch("https://services.leadconnectorhq.com/opportunities/upsert", {
      method: "POST", headers: H,
      body: JSON.stringify({ pipelineId: PIPELINE, locationId: LOC, contactId, name, status: "open", pipelineStageId: STAGES[target].id, ...(assignedTo ? { assignedTo } : {}) }),
    });
    let resp: any = null; try { resp = await up.json(); } catch { /* */ }
    console.log(`[opp-track] contact=${contactId} cur=${cur} computed=${computed} target=${STAGES[target].key} owner=${assignedTo ?? "-"} ok=${up.ok}`);
    return json({ ok: up.ok, stage: STAGES[target].key, curPos: cur, computed, target, owner: assignedTo, err: up.ok ? undefined : JSON.stringify(resp).slice(0, 250), elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) { return json({ ok: false, error: String(e).slice(0, 300), elapsed_ms: Date.now() - t0 }, 200); }
});
