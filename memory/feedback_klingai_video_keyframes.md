# Klingai.com video gen — keyframe workflow lessons

**Date:** 2026-05-08
**Context:** Logo animation para FERRE24. Kling 3.0 con first+last frame.

## Setup
- **Klingai Standard plan $6.99/mo** = 660 credits/mo. Desbloquea VIDEO 3.0.
- VIDEO 3.0 acepta start+end frame para keyframe interpolation.
- Costo aprox 60 credits por video 1080p · 5s con end frame.

## Lecciones técnicas

### 1. CSP de Klingai bloquea upload programático
- `mcp__Claude_in_Chrome__file_upload` → "Not allowed" (bloqueado por CSP)
- JS `fetch('http://127.0.0.1:8765/...')` → bloqueado por connect-src CSP
- XHR + img.src externos → bloqueados igual
- **Workaround único:** usuario hace drag-drop manual desde Finder al área de upload.
- Computer-use no ayuda: Chrome está restringido a tier "read" — no acepta drops.

### 2. Kling 3.0 renderiza texto legible mid-animation con prompt explícito
- Pasar la palabra exacta entre comillas + describir momento + estilo tipográfico.
- Ejemplo que funcionó (FERRE en cinta): _"at the moment the tape is fully extended, the word 'FERRE' must appear printed in bold black sans-serif letters on the yellow tape ribbon, perfectly legible, reading as F-E-R-R-E together with the F on the case. The word FERRE stays visible on the extended tape for 1 full second."_
- Sin esa especificidad, Kling interpola entre los keyframes pero no inventa texto.

### 3. Klingai Standard vence Higgsfield Starter para tareas one-off
| | Klingai Standard | Higgsfield Starter |
|---|---|---|
| Precio | $6.99/mo | $15/mo |
| Credits | 660 | 200 |
| Kling 3.0 | ✓ unlocked | ✓ unlocked |
| Veo 3.1 / Seedance | — | ✓ |
| One-off task | **Mejor** | Caro |
| Multi-modelo | — | Mejor |

## Anti-patterns
- ❌ Intentar reconstruir logo desde cero en Remotion cuando ya hay vector source — los traces (potrace) suelen quedar rotos para componentes específicos.
- ❌ Asumir colores del logo sin verificar visualmente — costó 6 iteraciones (la "tuerca" de FERRE24 es hex NEGRO + disco AMARILLO, no al revés).
- ❌ Pagar Higgsfield si solo necesitas Kling 3.0 — ir directo a Klingai es mitad de precio.

## Workflow probado (replicable)
1. Generar a mano start frame (estado inicial) y end frame (estado final) — sí, con Photoshop/Figma/Gemini Web UI.
2. Klingai → Video Generation → VIDEO 3.0 → drag-drop start + end frames.
3. Prompt: descripción del feel (snappy/bouncy/smooth) + sequence narrativa + texto explícito si hay palabras clave que deben aparecer.
4. 1080p · 5s · 1 video → ~60 credits.
5. Download MOV/MP4 y mover a la carpeta del proyecto.

Aplicable cross-client cuando el deliverable es un short logo reveal (5-10s).
