// f24-pay — Supabase Edge Function (Deno)
//
// Link de pago ENVUELTO para tracking de clic. El bot manda este link en vez del invoice_url
// crudo. Al hacer clic:
//   1. Taggea el contacto en GHL con "pago-clic" + nota fechada (señal de conversión/fuga).
//   2. Redirige (302) al invoice_url real del draft order (lo obtiene de Shopify).
//
// URL: https://wjlwpfaogjpeqgyxxnwa.supabase.co/functions/v1/f24-pay?o=<draft_id>&c=<contact_id>
// verify_jwt=false (lo abre el cliente desde WhatsApp, sin auth).

const SHOPIFY_SHOP = Deno.env.get("SHOPIFY_SHOP") ?? "0mtky1-q6.myshopify.com";
const SHOPIFY_CLIENT_ID = Deno.env.get("SHOPIFY_CLIENT_ID") ?? "";
const SHOPIFY_CLIENT_SECRET = Deno.env.get("SHOPIFY_CLIENT_SECRET") ?? "";
const SHOPIFY_API_VERSION = Deno.env.get("SHOPIFY_API_VERSION") ?? "2024-10";
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";

// ── Link preview (Open Graph) para WhatsApp / redes ──────────────────────────
const OG_IMAGE = "https://cdn.shopify.com/s/files/1/0725/1519/0872/files/f24_og_whatsapp_v2.jpg?v=1780532789";
const OG_TITLE = "Ferre24 — Ferretería en movimiento";
const OG_DESC = "Generadores, bombas, hidrolavadoras y más. Equipo profesional para trabajo pesado con envío a todo México. Precios reales, sin letras chiquitas.";

// Detecta scrapers de link-preview (WhatsApp/Meta/Twitter/etc.) — NO son el cliente haciendo clic
function isCrawler(ua: string): boolean {
  return /facebookexternalhit|facebookcatalog|Facebot|WhatsApp|Twitterbot|TelegramBot|Slackbot|LinkedInBot|Discordbot|Pinterest|redditbot|Googlebot|bingbot|Applebot|bot\b|crawler|spider|preview/i.test(ua);
}

function ogHtml(target: string): string {
  return `<!doctype html><html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ferre24">
<meta property="og:url" content="https://ferre24.com.mx">
<meta property="og:title" content="${OG_TITLE}">
<meta property="og:description" content="${OG_DESC}">
<meta property="og:image" content="${OG_IMAGE}">
<meta property="og:image:secure_url" content="${OG_IMAGE}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Ferre24 — Herramientas sin igual">
<link rel="image_src" href="${OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${OG_TITLE}">
<meta name="twitter:description" content="${OG_DESC}">
<meta name="twitter:image" content="${OG_IMAGE}">
<title>${OG_TITLE}</title>
</head><body style="font-family:system-ui;background:#0e0e0f;color:#fff;text-align:center;padding:60px">
<a style="color:#FFD400" href="${target}">Continuar a tu link de pago seguro</a>
</body></html>`;
}

async function getShopifyToken(): Promise<string> {
  const r = await fetch(`https://${SHOPIFY_SHOP}/admin/oauth/access_token`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: SHOPIFY_CLIENT_ID, client_secret: SHOPIFY_CLIENT_SECRET, grant_type: "client_credentials" }),
  });
  return (await r.json()).access_token;
}

async function tagClick(contactId: string): Promise<void> {
  if (!GHL_TOKEN || !contactId) return;
  const h = { Authorization: `Bearer ${GHL_TOKEN}`, Version: "2021-07-28", "Content-Type": "application/json" };
  try {
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/tags`, {
      method: "POST", headers: h, body: JSON.stringify({ tags: ["pago-clic"] }),
    });
    await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, {
      method: "POST", headers: h,
      body: JSON.stringify({ body: `🔗 Hizo clic en el link de pago — ${new Date().toISOString()}` }),
    });
  } catch (_e) { /* best-effort */ }
}

Deno.serve(async (req: Request) => {
  const url = new URL(req.url);
  const draftId = url.searchParams.get("o") ?? "";
  const contactId = url.searchParams.get("c") ?? "";
  const ua = req.headers.get("user-agent") ?? "";

  // Si es un scraper de link-preview (WhatsApp/Meta), servir SOLO el OG HTML:
  // no taggear (no es un clic real), no resolver invoice. Esto arregla el preview
  // del link del bot Y evita el falso "pago-clic" del pre-scrape de WhatsApp.
  if (isCrawler(ua)) {
    return new Response(ogHtml("https://ferre24.com.mx"), {
      status: 200,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  }

  // Registrar el clic (no bloquea el redirect si falla)
  await tagClick(contactId);

  // Resolver el invoice_url real del draft
  let invoiceUrl = "https://ferre24.com.mx";
  try {
    if (draftId) {
      const token = await getShopifyToken();
      const r = await fetch(`https://${SHOPIFY_SHOP}/admin/api/${SHOPIFY_API_VERSION}/draft_orders/${draftId}.json`, {
        headers: { "X-Shopify-Access-Token": token, "Content-Type": "application/json" },
      });
      if (r.ok) {
        const d = await r.json();
        invoiceUrl = d.draft_order?.invoice_url || invoiceUrl;
      }
    }
  } catch (_e) { /* fall back a home */ }

  return new Response(null, { status: 302, headers: { Location: invoiceUrl } });
});
