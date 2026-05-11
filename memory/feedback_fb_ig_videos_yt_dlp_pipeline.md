# Feedback — Videos de FB/IG en mockups: bajar con yt-dlp, NO usar iframes

**Fecha:** 2026-05-04
**Detectado en:** IES Travel mockup v2

## Problema

Embeber reels de Facebook/Instagram con `<iframe src="https://www.facebook.com/plugins/video.php?...">`:

- Se ven como **widgets de ad**: padding negro grande, logo FB visible, "Compartir" button, branding ajeno
- Aspect ratio interno 9:16 fijo del iframe NO llena el contenedor de la card → cuadro negro alrededor
- Lazy load de FB lento (2-4s para inicializar)
- Bloqueable por adblockers / ITP / cookies del usuario
- No autoplay confiable
- Estética inconsistente con el resto del site premium

## Solución

**Pipeline: yt-dlp → ffmpeg → `<video>` HTML5 nativo**

### Setup (una vez)

```bash
pip3 install --user yt-dlp
# yt-dlp instalado en ~/Library/Python/3.9/bin/yt-dlp
# brew install ffmpeg (ya disponible en /opt/homebrew/bin/ffmpeg)
```

### Workflow por reel

```bash
# 1. Descargar
yt-dlp -f "best[ext=mp4]" -o "video1.%(ext)s" "https://www.facebook.com/reel/{REEL_ID}/"

# 2. Comprimir web-optimized (720p, crf 28, faststart, 96kbps audio)
ffmpeg -y -loglevel error -i "video1.mp4" \
  -vcodec libx264 -crf 28 -preset fast \
  -vf "scale=-2:720" \
  -acodec aac -b:a 96k \
  -movflags +faststart \
  "video1_web.mp4"
```

### Resultados típicos

| Original | Web-optimized | Reducción |
|---|---|---|
| 21.2 MB (lobos marinos) | 5.8 MB | 73% |
| 11.7 MB (intro) | 3.5 MB | 70% |
| 4.5 MB (fauna) | 1.8 MB | 60% |
| 3.0 MB (tours) | 1.5 MB | 50% |
| 5.3 MB (camping) | 1.3 MB | 75% |

5 reels = ~14 MB total en lugar de ~46 MB.

### HTML para mockup

```html
<video class="tour-video" autoplay muted loop playsinline preload="metadata" poster="cover.jpg">
  <source src="photos/video2_lobos_web.mp4" type="video/mp4">
</video>
```

CSS:
```css
.tour-video {
  width: 100%; height: 100%;
  object-fit: cover;
  border-radius: inherit;
}
```

### iOS autoplay safety net (Shopify deploy crítico)

```js
document.querySelectorAll('video').forEach(v => {
  v.muted = true; v.playsInline = true;
  v.play().catch(()=>{});
});
// Re-play on tab visibility (iOS pause-on-tab fix)
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    document.querySelectorAll('video').forEach(v => v.play().catch(()=>{}));
  }
});
// First-touch fallback
['touchstart','click','scroll'].forEach(ev => {
  window.addEventListener(ev, () => {
    document.querySelectorAll('video').forEach(v => { if (v.paused) v.play().catch(()=>{}); });
  }, { once: true, passive: true });
});
```

## Soporte en `_publish_prospect.py`

El MIME_MAP NO incluye `mp4` pero el fallback funciona:

- `MIME_MAP.get(ext, "application/octet-stream")` → `application/octet-stream` para mp4
- `ctype = "FILE"` (porque no es `image/...`) → Shopify lo acepta como FILE
- Upload via staged upload + fileCreate funciona igual que para imágenes

Subidas exitosas confirmadas: 5 mp4s × ~3MB = ~15MB total en deploy IES Travel.

**TODO opcional:** agregar `"mp4": "video/mp4", "webm": "video/webm"` al MIME_MAP en línea 245 del script para ser explícito.

## Cuándo NO usar este pipeline

- Si el cliente ya tiene un canal de YouTube/Vimeo público y prefiere mantener tracking → usar embed iframe oficial
- Si los videos cambian frecuentemente y necesitas que el site refleje la última versión sin re-deploy → embed iframe (pero es lento)

## Referencias

- Memoria del flow: este archivo
- Skill: `/publish-prospect`
- yt-dlp docs: https://github.com/yt-dlp/yt-dlp
