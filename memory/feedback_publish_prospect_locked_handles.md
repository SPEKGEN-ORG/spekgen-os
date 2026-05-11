# Publish Prospect — Locked Handles + FB Video Embeds

**Origen**: 2026-04-28 sesión Mariscos Los Laureles. Ambos features ya implementados.

## Locked Handles (preserva URL canónico)

### El problema

`_publish_prospect.py` versionaba el handle con hash del body (`{slug}mockup-v{hash}`) en cada republish para bypass de Shopify page_cache poisoning. Cada edit cambiaba el handle. Mal cuando el cliente ya tiene el link compartido en WhatsApp/email.

### La solución

Sistema de "lock file" per-prospect: `.spekgen_locked_handles.json` en la carpeta del prospecto:

```json
{
  "mockup": "mariscosloslauremockup-va49f2e",
  "propuesta": "mariscosloslaurepropuesta-v84c5ec"
}
```

Comportamiento del script:
- **Primera publicación**: genera handle versionado y lo guarda en lock file
- **Siguientes publicaciones**: lee lock file, hace upsert IN-PLACE en ese handle, URL nunca cambia
- **Forzar nuevo handle**: borrar el `.spekgen_locked_handles.json` del prospecto

Aplica para TODOS los prospectos automáticamente. Mariscos Los Laureles ya está lockeado.

## FB Video Embeds (autoplay reliable)

### El problema

FB iframe plugin con `autoplay=true` en URL es poco confiable:
- Funciona a veces en desktop
- Falla en iOS Safari (Low Power Mode strict)
- Múltiples iframes compitiendo se throttlean entre sí
- Sin control via JS

### La solución

**Descargar FB videos como MP4 con yt-dlp + embed nativo HTML5:**

```bash
python3 -m yt_dlp -o "fb_{name}.%(ext)s" --recode-video mp4 "https://www.facebook.com/reel/XXXX/"
```

Si HTTP 500: probar formato sd con `-f sd`:
```bash
python3 -m yt_dlp -f sd -o "fb_{name}.%(ext)s" --recode-video mp4 "URL"
```

Embed:
```html
<video src="assets/fb_xxx.mp4" autoplay muted loop playsinline preload="auto"></video>
```

**100% reliable cross-browser**, autoplay garantizado.

### Tap-to-unmute pattern

Add overlay button + JS:
```javascript
window.toggleMute = function(el) {
  var v = el.querySelector('video'); if (!v) return;
  document.querySelectorAll('.phone-frame video').forEach(function(other) {
    if (other !== v) other.muted = true;  // mute siblings
  });
  v.muted = !v.muted;
  if (!v.muted) v.play().catch(function(){});
};
```

### Performance: pause off-screen

Intersection Observer pausa videos fuera del viewport (ahorra batería + datos):
```javascript
var io = new IntersectionObserver(function(entries) {
  entries.forEach(function(entry) {
    var v = entry.target;
    if (entry.isIntersecting) v.play().catch(function(){});
    else v.pause();
  });
}, { threshold: 0.25 });
document.querySelectorAll('.phone-frame video').forEach(function(v) { io.observe(v); });
```

## Trigger para leer este file

- Task que mencione FB video embed, autoplay, iframe, phone-frame
- Republicar mockup donde el handle no debe cambiar
- "el link ya no funciona después de republicar"
- Edit de `_publish_prospect.py`
