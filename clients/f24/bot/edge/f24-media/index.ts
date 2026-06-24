// f24-media — Supabase Edge Function (Deno)
//
// Capa multimodal del bot WhatsApp de Ferre24. Recibe la URL del media que GHL re-hospeda
// en su CDN (link.spekgen.com/conversations-assets/...), lo descarga, y:
//   - mode "transcribe":   nota de voz → Gemini → texto literal (se inyecta al text path del bot).
//   - mode "vision_match": foto de pieza → Gemini Vision identifica + matchea contra el catálogo
//                          F24 → descriptor + 2-3 candidatos (sku/title/price del catálogo).
//   - mode "auto":         detecta audio vs imagen por Content-Type/extensión y rutea solo.
//
// El bot (Make scenario 5258612) llama esta función, recibe el resultado, y lo mete en `user_msg`
// (Módulo 28) para que el cerebro Haiku lo trate como si el cliente lo hubiera escrito.
//
// Diseño calcado de f24-process-order: Deno.serve, router por `mode`, SIEMPRE HTTP 200 (para que
// Make no auto-pause; el bot decide por result.ok / transcript / candidates).
//
// Secrets (Supabase → Edge Functions secrets):
//   GEMINI_API_KEY   (opcional)  — si no está como secret, Make manda la key en el body (`gemini_key`).
//   GHL_TOKEN        (ya existe)  — PIT F24, fallback de auth si el CDN de GHL lo exige.
//   GEMINI_MODEL     (opcional)   — default "gemini-2.5-flash" (multimodal: audio + visión).

import { CATALOG_TSV } from "./catalog_compact.ts";

// Catálogo bundleado como TSV pipe-delimitado (sku|short_title|category|marca|price) — se parsea
// a objetos al cold-start. Va dentro del código de la función (no público) → no expone pricing.
interface CatItem { sku: string; t: string; c: string; m: string; p: string; }
const CATALOG: CatItem[] = CATALOG_TSV.trim().split("\n").map((line) => {
  const [sku, t, c, m, p] = line.split("|");
  return { sku, t, c, m, p };
});

const GEMINI_KEY = Deno.env.get("GEMINI_API_KEY") ?? "";
const GHL_TOKEN = Deno.env.get("GHL_TOKEN") ?? "";
const GEMINI_MODEL = Deno.env.get("GEMINI_MODEL") ?? "gemini-2.5-flash";

const AUDIO_EXT = /\.(ogg|oga|opus|mp3|m4a|amr|aac|wav|flac)(\?|$)/i;
const IMAGE_EXT = /\.(jpe?g|png|webp|gif|heic|heif|bmp)(\?|$)/i;

// ── helpers ──
function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// Quita comillas dobles y saltos de línea — el descriptor se inyecta en el JSON-con-prefill que
// Make arma hacia Anthropic; un `"` o `\n` sin escapar rompería ese JSON.
function sanitize(s: string): string {
  return String(s ?? "").replace(/["\r\n]+/g, " ").replace(/\s+/g, " ").trim();
}

// Uint8Array → base64 (en chunks para no reventar el call stack con archivos medianos).
function toBase64(bytes: Uint8Array): string {
  let bin = "";
  const CH = 0x8000;
  for (let i = 0; i < bytes.length; i += CH) {
    bin += String.fromCharCode(...bytes.subarray(i, i + CH));
  }
  return btoa(bin);
}

function mimeFromUrl(url: string): string | null {
  if (AUDIO_EXT.test(url)) {
    const ext = url.toLowerCase().match(AUDIO_EXT)![1];
    if (ext === "oga" || ext === "opus") return "audio/ogg";
    if (ext === "m4a") return "audio/mp4";
    return `audio/${ext === "mp3" ? "mpeg" : ext}`;
  }
  if (IMAGE_EXT.test(url)) {
    const ext = url.toLowerCase().match(IMAGE_EXT)![1];
    if (ext === "jpg") return "image/jpeg";
    return `image/${ext}`;
  }
  return null;
}

type Media = { bytes: Uint8Array; mime: string; kind: "audio" | "image" | "unknown" };

// Descarga el media del CDN de GHL. Intenta sin auth primero (URLs firmadas suelen ser públicas);
// si el CDN responde 401/403, reintenta con el PIT de GHL como Bearer.
async function fetchMedia(url: string): Promise<Media> {
  let resp = await fetch(url);
  if ((resp.status === 401 || resp.status === 403) && GHL_TOKEN) {
    resp = await fetch(url, { headers: { Authorization: `Bearer ${GHL_TOKEN}` } });
  }
  if (!resp.ok) throw new Error(`media_fetch_${resp.status}`);
  const ctype = (resp.headers.get("content-type") ?? "").split(";")[0].trim().toLowerCase();
  const bytes = new Uint8Array(await resp.arrayBuffer());
  // mime: preferir Content-Type del CDN; si es genérico/ausente, inferir de la extensión de la URL.
  let mime = ctype && ctype !== "application/octet-stream" && ctype !== "binary/octet-stream"
    ? ctype
    : (mimeFromUrl(url) ?? "application/octet-stream");
  let kind: Media["kind"] = mime.startsWith("audio/")
    ? "audio"
    : mime.startsWith("image/")
    ? "image"
    : "unknown";
  // Si el Content-Type fue genérico pero la URL delata el tipo, confiar en la extensión.
  if (kind === "unknown") {
    if (AUDIO_EXT.test(url)) { kind = "audio"; mime = mimeFromUrl(url) ?? "audio/ogg"; }
    else if (IMAGE_EXT.test(url)) { kind = "image"; mime = mimeFromUrl(url) ?? "image/jpeg"; }
  }
  return { bytes, mime, kind };
}

// ── Gemini ──
// La key se resuelve: secret GEMINI_API_KEY (si está) > `gemini_key` del body (lo manda Make desde
// su .env, mismo patrón que ANTHROPIC_API_KEY). Así no depende del dashboard de Supabase.
async function geminiGenerate(
  parts: unknown[],
  apiKey: string,
  opts: { jsonOut?: boolean; temperature?: number } = {},
): Promise<string> {
  const key = GEMINI_KEY || apiKey;
  if (!key) throw new Error("no_gemini_key");
  const url =
    `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${key}`;
  const generationConfig: Record<string, unknown> = { temperature: opts.temperature ?? 0.1 };
  if (opts.jsonOut) generationConfig.responseMimeType = "application/json";
  const payload = JSON.stringify({ contents: [{ parts }], generationConfig });
  // Retry en 429/503 (Gemini se sobrecarga por spikes) — backoff corto, no bloquea al cliente.
  let last = "gemini_error";
  for (let attempt = 0; attempt < 3; attempt++) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
    });
    if ((resp.status === 429 || resp.status === 503) && attempt < 2) {
      last = `gemini_${resp.status}`;
      await new Promise((r) => setTimeout(r, 700 * (attempt + 1)));
      continue;
    }
    const data = await resp.json();
    if (!resp.ok) throw new Error(`gemini_${resp.status}: ${JSON.stringify(data).slice(0, 300)}`);
    const text = data?.candidates?.[0]?.content?.parts?.map((p: any) => p?.text ?? "").join("") ?? "";
    return String(text).trim();
  }
  throw new Error(`${last}_after_retries`);
}

// ── mode: transcribe ──
// CRÍTICO (probado con audio real 2026-06-17): Gemini ALUCINA fácil en audios cortos/casi-silencio.
// Con un "Ah, ¿qué tal?" de 1.3s:
//   - lista de jerga en el prompt → loro-repitió la lista como si fuera el audio.
//   - temperature 0.1 → inventó "pistola de calor Dewalt DWHA2000..." (query de 15s).
//   - prompt con framing "cliente de ferretería / herramientas y marcas" → "un taladro" (4/4, determinista).
// CUALQUIER pista de dominio en el prompt sesga la invención hacia herramientas. Defensa validada:
// temperature 0 + prompt 100% NEUTRO (SIN mencionar ferretería/herramientas) + guard de audio corto +
// anti-invención. Tradeoff aceptado: una marca rara puede quedar peor escrita, pero NUNCA se fabrica un
// producto que el cliente no dijo (eso haría que el bot cotice algo equivocado).
const TRANSCRIBE_PROMPT =
  "Transcribe este audio en español, palabra por palabra, SOLO lo que realmente se escucha. " +
  "NO inventes, NO completes, NO agregues ninguna palabra que no esté en el audio. " +
  "El audio puede ser muy corto (1-2 segundos), un saludo, o casi en silencio; en ese caso transcribe " +
  "solo esas pocas palabras, o devuelve una cadena vacía si no se entiende nada. " +
  "Devuelve SOLO la transcripción, sin comillas ni notas.";

async function transcribe(media: Media, apiKey: string): Promise<{ transcript: string }> {
  // temperature 0 = determinista, mínimo riesgo de invención.
  const transcript = await geminiGenerate([
    { inline_data: { mime_type: media.mime, data: toBase64(media.bytes) } },
    { text: TRANSCRIBE_PROMPT },
  ], apiKey, { temperature: 0 });
  return { transcript: transcript.trim() };
}

// ── mode: vision_match ──
const CAT_BY_SKU = new Map<string, CatItem>(CATALOG.map((c) => [c.sku.toUpperCase(), c]));
// Lista compacta para el prompt: "SKU | título | categoría | marca modelo | $precio"
const CATALOG_BLOCK = CATALOG.map((c) => `${c.sku} | ${c.t} | ${c.c} | ${c.m} | $${c.p}`).join("\n");

function visionPrompt(): string {
  return [
    "Eres un experto en herramientas y equipo de ferretería. Analiza la FOTO que mandó un cliente por WhatsApp.",
    "Tu tarea: (1) describe en una frase qué se ve (tipo de producto, marca visible si la hay, specs visibles como HP/PSI/pulgadas/color);",
    "(2) elige los SKUs MÁS probables de ESTE catálogo de Ferre24 que correspondan a lo de la foto.",
    "",
    "REGLAS:",
    "- USA SOLO SKUs que aparezcan en la lista de abajo. NUNCA inventes un SKU.",
    "- Devuelve entre 0 y 3 candidatos, ordenados del más probable al menos probable.",
    "- confidence: 0.0 a 1.0 (qué tan seguro estás de que ESE SKU es lo de la foto).",
    "- Si la foto no corresponde a nada del catálogo o es ilegible, devuelve candidates vacío.",
    "",
    "Responde SOLO este JSON (sin texto extra):",
    '{"descriptor": "<frase de lo que se ve>", "candidates": [{"sku": "<SKU exacto del catálogo>", "confidence": <0-1>}]}',
    "",
    "CATÁLOGO (SKU | título | categoría | marca modelo | precio):",
    CATALOG_BLOCK,
  ].join("\n");
}

type Candidate = { sku: string; title: string; price: string; confidence: number };

async function visionMatch(media: Media, apiKey: string): Promise<{ descriptor: string; candidates: Candidate[] }> {
  const raw = await geminiGenerate(
    [
      { inline_data: { mime_type: media.mime, data: toBase64(media.bytes) } },
      { text: visionPrompt() },
    ],
    apiKey,
    { jsonOut: true },
  );
  let parsed: any = {};
  try {
    parsed = JSON.parse(raw);
  } catch {
    // por si el modelo envolvió en ```json
    const m = raw.match(/\{[\s\S]*\}/);
    parsed = m ? JSON.parse(m[0]) : {};
  }
  const descriptor = sanitize(parsed?.descriptor ?? "");
  const rawCands: any[] = Array.isArray(parsed?.candidates) ? parsed.candidates : [];
  const seen = new Set<string>();
  const candidates: Candidate[] = [];
  for (const rc of rawCands) {
    const sku = String(rc?.sku ?? "").trim().toUpperCase();
    if (!sku || seen.has(sku)) continue;
    const hit = CAT_BY_SKU.get(sku); // valida contra catálogo (anti-alucinación) + precio autoritativo
    if (!hit) continue;
    seen.add(sku);
    candidates.push({
      sku: hit.sku,
      title: hit.t,
      price: hit.p,
      confidence: Math.max(0, Math.min(1, Number(rc?.confidence ?? 0))),
    });
    if (candidates.length >= 3) break;
  }
  return { descriptor, candidates };
}

// ── server ──
Deno.serve(async (req: Request) => {
  if (req.method === "GET") {
    return json({ ok: true, service: "f24-media", version: 1, model: GEMINI_MODEL, modes: ["transcribe", "vision_match", "auto"] });
  }
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  const t0 = Date.now();
  try {
    const body = await req.json();
    console.log(`[f24-media] RAW BODY: ${JSON.stringify(body).slice(0, 400)}`);
    const url = String(body.media_url ?? body.media ?? "").trim();
    const apiKey = String(body.gemini_key ?? "").trim();
    let mode = String(body.mode ?? "auto");
    if (!url) return json({ ok: false, error: "no_media_url", mode, elapsed_ms: Date.now() - t0 }, 200);

    const media = await fetchMedia(url);
    if (mode === "auto") {
      mode = media.kind === "audio" ? "transcribe" : media.kind === "image" ? "vision_match" : "unknown";
    }

    if (mode === "transcribe") {
      const r = await transcribe(media, apiKey);
      // inject_text = lo que Make mete tal cual en user_msg (evita construir strings en IML de Make).
      return json({ ok: true, mode, transcript: r.transcript, inject_text: r.transcript, lang: "es", elapsed_ms: Date.now() - t0 }, 200);
    }
    if (mode === "vision_match") {
      const r = await visionMatch(media, apiKey);
      // inject_text armado AQUÍ (no en Make): así Make solo referencia un escalar, sin map()/length()
      // sobre campos de respuesta no declarados (que rompen la validación de blueprint).
      const inject_text = r.candidates.length > 0
        ? `[El cliente mando una FOTO. Lo que se ve: ${r.descriptor || "un producto"}. ` +
          `Posibles del catalogo (SKU): ${r.candidates.map((c) => c.sku).join(", ")}. ` +
          `IMPORTANTE: pregunta al cliente cual de estos es el correcto ANTES de cotizar; no cotices a ciegas.]`
        : "[El cliente mando una FOTO pero no se identifico el producto en el catalogo. Pidele el nombre o modelo.]";
      return json({ ok: true, mode, descriptor: r.descriptor, candidates: r.candidates, inject_text, elapsed_ms: Date.now() - t0 }, 200);
    }
    return json({ ok: false, error: `unknown_mode_${mode}`, media_kind: media.kind, elapsed_ms: Date.now() - t0 }, 200);
  } catch (e) {
    // Siempre 200: el bot maneja el caso degradado (transcript vacío / candidates vacío → pide reenviar).
    return json({ ok: false, error: String(e).slice(0, 400), elapsed_ms: Date.now() - t0 }, 200);
  }
});
