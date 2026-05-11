---
name: yt-insights skill v1.1
description: Skill global /yt-insights — procesa video de YouTube → transcript + insights.pdf + content_briefs.pdf + _RECAP.pdf 1-página. Vault en SPK - 18. YT VAULT/. Build 2026-05-10/11.
type: project
originSessionId: 56b2c3bd-f8bb-4b88-b82a-63c7676c8e94
---
# Skill `/yt-insights` v1.1 — pipeline YouTube → knowledge + content briefs

**Path:** `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/yt-insights/`
**Symlink:** `~/.claude/skills/yt-insights/`
**Vault:** `SPK - SPEKGEN AGENCY/SPK - 18. YT VAULT/`
**Obsidian:** `_OBSIDIAN/04 - YT INSIGHTS/`
**Activación:** "procesa este video <URL>", "/yt-insights <URL>", "saca contenido de este video", o pegando URL de YouTube.

## Arquitectura — 2 fases

**Fase 1 — `extract` (mecánica):**
```bash
/usr/bin/python3 scripts/run.py extract <URL> [--mode fail|overwrite|version]
```
- yt-dlp jala auto-subs + info JSON (chapters si existen formales)
- VTT → transcript.srt + transcript.txt, borra raw.vtt
- metadata.json con chapters, duration, channel, views
- Crea carpeta `videos/{YYYY-MM-DD}_{slug}/`
- **Idempotencia:** si folder existe, exit 3 con `FOLDER_EXISTS:` → Claude pregunta a Gibran (sobrescribir / -v2 / cancelar)
- Edge case: sin auto-subs → exit 2 con `NEED_MANUAL_TRANSCRIPT` → Gibran pega transcript en chat

**Fase 2 — análisis cognitivo (Claude):**
Claude lee `transcript.srt`, escribe `insights.md` + `content_briefs.md` en la carpeta. Templates de referencia (no Jinja-fill) en `templates/{insights,content_briefs}.md.j2`.

**Fase 3 — `finalize` (mecánica):**
```bash
/usr/bin/python3 scripts/run.py finalize <slug>
```
- Renderiza `insights.pdf`, `content_briefs.pdf`, `_RECAP.pdf` con Playwright headless chromium + CSS oscuro SPEKGEN (purple #8B5CF6 + bg #0F0F14)
- `_RECAP.pdf` es 1-pager A4 real: TL;DR + lista de 6 ideas (3 carruseles + 3 reels) con justificación 1-línea
- Upsert a `MASTER_INDEX.xlsx` por slug (no duplica)
- Crea nota Obsidian con frontmatter + tags + backlinks `[[X]]` auto-detectados (HEALTHY CHUCHOS, GREENRAY, LO FITNESS, METAGREEN, GAE, SPEKGEN, Claude Code, Make, Shopify, GHL, factory-batch, publish-prospect, kill-prospect)
- `open -R` del RECAP en Finder

## Stack — $0 costos externos

- yt-dlp (brew, gratis, mantenido)
- ffmpeg 8.1 (brew)
- Python 3.9 system + openpyxl + jinja2 + playwright (todos ya instalados)
- Chromium headless (Playwright auto-managed)

## Reglas de contenido GAE (críticas, ver feedback_gae_content_voice.md)

`content_briefs.md` debe seguir tono "amigo compartiendo tips", NUNCA guru/superior. Mínimo 3 carruseles + 3 reels (menú, no idea pulida única). Hook desde dolor concreto del viewer. NUNCA mencionar # clientes/empleados/"agencia 99.99% AI" en posts públicos.

## Lecciones del build (2026-05-10/11)

1. **Screenshots del video se quitaron en v1.1** — Gibran dijo "no veo que sean tan útiles". Eliminaron complejidad (download 480p + ffmpeg seek) sin perder valor real.
2. **PDF >>> markdown** para consumo de Gibran — no lee .md. CSS oscuro purple SPEKGEN match al feed GAE.
3. **Master index upsert por slug** — naive append creaba duplicados al re-correr finalize. Fix: buscar fila por slug en col 1, update si existe.
4. **`raw.en.vtt` cleanup automático** — ocupaba 200KB innecesarios después de procesarlo.
5. **Idempotencia explícita** — exit codes (2=no subs, 3=folder exists, 0=ok) + mensajes parseables (`FOLDER_EXISTS:`, `NEED_MANUAL_TRANSCRIPT`) permiten que Claude decida interactivo con Gibran.

## Roadmap (no bloqueante)

- Multi-source: `--source pdf|audio|web` (cuando aparezca primer caso non-YT)
- Pre-flight check de deps (yt-dlp/ffmpeg/playwright)
- Test del fallback manual transcript en un video real sin auto-subs
- Optimización PDF size (insights.pdf ~500KB para 10KB MD — aceptable pero monitorear)

## Primer uso real

Video procesado 2026-05-10: "32 Tricks to Level Up Claude Code" de Nate Herk (https://www.youtube.com/watch?v=jqoFP9QapXI). 32 tricks identificados, 3 carruseles + 3 reels generados para GAE. Top idea: "3 comandos que uso todos los días para ahorrar tokens en Claude Code" (`/context` + `/compact` + `/clear`).
