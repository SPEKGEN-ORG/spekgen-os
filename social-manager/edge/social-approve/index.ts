// social-approve — endpoint del botón "Aprobar y publicar" del digest.
// NO toca tokens de Meta. Solo: verifica firma HMAC y cambia el estado en social_inbox.
// GET  -> página de confirmación (sin efecto; seguro ante escáneres de correo).
// POST -> ejecuta el cambio de estado (approved | discarded).
// Un worker aparte (social_publish.py) publica lo 'approved' en Meta.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SB_URL = Deno.env.get("SUPABASE_URL")!;
const SB_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

async function sb(method: string, path: string, body?: unknown, prefer?: string) {
  const headers: Record<string, string> = {
    apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}`, "Content-Type": "application/json",
  };
  if (prefer) headers["Prefer"] = prefer;
  const res = await fetch(`${SB_URL}/rest/v1/${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  const txt = await res.text();
  return txt ? JSON.parse(txt) : [];
}

let _secret = "";
async function approveSecret(): Promise<string> {
  if (_secret) return _secret;
  const rows = await sb("GET", "social_secrets?key=eq.approve_secret&select=value");
  _secret = rows[0]?.value ?? "";
  return _secret;
}

async function verify(id: string, action: string, sig: string): Promise<boolean> {
  const secret = await approveSecret();
  if (!secret || !sig) return false;
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${id}:${action}`));
  const expected = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  // comparación de tiempo constante
  if (expected.length !== sig.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ sig.charCodeAt(i);
  return diff === 0;
}

function page(title: string, body: string, color = "#2ecc71"): Response {
  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${title}</title><style>
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e8e8ec;
display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px}
.card{background:#171a21;border:1px solid #232733;border-radius:14px;padding:28px;max-width:460px;width:100%}
h1{font-size:18px;margin:0 0 12px;color:${color}}
.q{font-size:14px;color:#c9d0db;margin:0 0 8px}
.draft{background:#10241a;border-left:3px solid ${color};padding:10px 12px;border-radius:6px;
font-size:14px;color:#dff;margin:12px 0;white-space:pre-wrap}
button{background:${color};color:#062;border:0;border-radius:8px;padding:11px 20px;
font-size:14px;font-weight:600;cursor:pointer;width:100%}
.muted{color:#8b92a0;font-size:12px;margin-top:14px}
</style></head><body><div class="card">${body}</div></body></html>`;
  const headers = new Headers();
  headers.set("content-type", "text/html; charset=utf-8");
  return new Response(html, { status: 200, headers });
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const id = url.searchParams.get("id") ?? "";
  const action = url.searchParams.get("action") ?? "";
  const sig = url.searchParams.get("sig") ?? "";

  if (!["approve", "discard"].includes(action) || !id) {
    return page("Error", `<h1 style="color:#ff8a8a">Link inválido</h1>`, "#ff8a8a");
  }
  if (!(await verify(id, action, sig))) {
    return page("Error", `<h1 style="color:#ff8a8a">Firma inválida o vencida</h1>`, "#ff8a8a");
  }

  const rows = await sb("GET",
    `social_inbox?external_id=eq.${encodeURIComponent(id)}&select=client,channel,author,body,draft,status`);
  const row = rows[0];
  if (!row) return page("Error", `<h1 style="color:#ff8a8a">No encontrado</h1>`, "#ff8a8a");

  // GET -> confirmación (sin efecto)
  if (req.method === "GET") {
    if (action === "discard") {
      return page("Descartar",
        `<h1 style="color:#8b92a0">Descartar comentario</h1>
         <p class="q"><b>${row.client}</b> · ${row.author ?? "cliente"}: "${row.body ?? ""}"</p>
         <form method="POST"><button style="background:#2a2f3a;color:#cbd2e0">Sí, descartar</button></form>
         <p class="muted">No se publicará nada. Solo se saca de la bandeja.</p>`, "#8b92a0");
    }
    if (row.status !== "drafted" || !row.draft) {
      return page("Sin borrador",
        `<h1 style="color:#8b92a0">Este comentario ya fue procesado (${row.status})</h1>`, "#8b92a0");
    }
    return page("Aprobar respuesta",
      `<h1>Publicar esta respuesta</h1>
       <p class="q"><b>${row.client}</b> · ${row.author ?? "cliente"} comentó: "${row.body ?? ""}"</p>
       <div class="draft">${row.draft}</div>
       <form method="POST"><button>Confirmar y publicar</button></form>
       <p class="muted">Se publicará en Meta en los próximos minutos.</p>`);
  }

  // POST -> ejecuta
  if (req.method === "POST") {
    if (action === "discard") {
      await sb("PATCH", `social_inbox?external_id=eq.${encodeURIComponent(id)}`,
        { status: "discarded", acted_by: "discard", acted_at: new Date().toISOString() },
        "return=minimal");
      return page("Descartado", `<h1 style="color:#8b92a0">Listo, descartado.</h1>`, "#8b92a0");
    }
    if (row.status !== "drafted" || !row.draft) {
      return page("Ya procesado",
        `<h1 style="color:#8b92a0">Este comentario ya estaba en estado: ${row.status}</h1>`, "#8b92a0");
    }
    await sb("PATCH", `social_inbox?external_id=eq.${encodeURIComponent(id)}`,
      { status: "approved", acted_by: "approve", acted_at: new Date().toISOString() },
      "return=minimal");
    return page("Aprobado",
      `<h1>✓ Aprobado</h1><p class="q">Se publicará en Meta en los próximos minutos.</p>`);
  }

  return new Response("Method not allowed", { status: 405 });
});
