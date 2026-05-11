---
name: reel-scripter
description: >
  Genera briefs completos de producción para Instagram Reels. Script con hook,
  cuerpo, CTA, texto en pantalla, storyboard visual, y sugerencia de audio.
  No genera video — produce todo lo necesario para filmarlo.
  Activate for: "genera un reel", "script de reel", "brief de reel",
  "reel sobre", "reel para [CLIENTE]", "guion de reel",
  "reel script", "video brief", "contenido de video".
---

# Reel Scripter Skill — v1.0

## Overview

Generates complete production briefs for Instagram Reels. Cannot generate video, but produces everything needed to film and edit: script, storyboard, text overlays, and audio suggestions.

Output is a structured markdown brief that can be:
- Used by Gibran to film
- Sent to a videographer/UGC creator
- Stored in Content Hub as `formato: 'Reel'`, `status: 'Brief'`

**5 Client Configs:** Reuses client context files

---

## Paths

```
SKILL_DIR    = SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/reel-scripter
CLIENTS_BASE = /Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL
```

---

## Phase 1: Collect Inputs

1. **Client** — Which brand?
   - SPEKGEN = @gibran.alonzo.ecom (Gibran on camera, first-person)
   - Clients = brand-appropriate UGC or product-focused
2. **Topic** — What is the reel about?
3. **Duration** — Target length: 15s / 30s / 60s / 90s. Default: 30s
4. **Style** — Talking head / Screen recording / Product demo / B-roll montage / Trending format
5. **SPCL Pillar** — S (Status), P (Power), C (Credibility), L (Likeness)
6. **Funnel** — TOFU / MOFU / BOFU

---

## Phase 2: Write Script

### Script Structure (30s default)

| Beat | Time | Element | Purpose |
|------|------|---------|---------|
| 1 | 0-3s | **HOOK** | Stop the scroll. Pattern interrupt. Bold claim or question. |
| 2 | 3-8s | **CONTEXT** | Set up the problem or topic. Why should they care? |
| 3 | 8-22s | **VALUE** | The meat. Framework, tip, proof, or story. |
| 4 | 22-27s | **CTA** | What to do next. Follow, save, comment, link in bio. |
| 5 | 27-30s | **LOGO STING** | Brand logo flash. 1-2 seconds. |

### Adjust by Duration

- **15s**: Hook (0-2s) → Value (2-12s) → CTA (12-15s)
- **60s**: Hook (0-3s) → Context (3-10s) → Value with 3 points (10-50s) → CTA (50-58s) → Logo (58-60s)
- **90s**: Hook (0-3s) → Story/Problem (3-15s) → Framework (15-70s) → Proof (70-80s) → CTA (80-88s) → Logo (88-90s)

### Hook Types (rotate these)

1. **Bold Claim**: "Tu marca pierde $X cada mes por verse barata"
2. **Question**: "¿Sabes por qué tus anuncios no venden?"
3. **Contrarian**: "Deja de gastar en branding — haz esto primero"
4. **POV**: "POV: Tu cliente ideal te descubre en Instagram"
5. **Story**: "Hace 6 meses un cliente me dijo que no podía pagar $X..."
6. **Pattern Interrupt**: Start mid-action, unexpected visual, or sound effect

---

## Phase 3: Write Storyboard

For each beat, describe:

```
BEAT {N} — {TIME}
📷 SHOT: {Camera angle, framing, location}
👤 ACTION: {What the person is doing}
🗣️ VOICEOVER: "{Exact words spoken}"
📝 ON-SCREEN TEXT: "{Text overlay — max 5 words per line}"
🎵 AUDIO: {Music mood, sound effect, or trending audio suggestion}
```

### Shot Types to Rotate

- **Talking head**: Face to camera, well-lit, clean background
- **Screen recording**: Desktop/phone showing tool, process, or result
- **B-roll**: Product close-ups, workspace, lifestyle footage
- **Text on screen**: Kinetic typography, no person needed
- **Split screen**: Before/after, comparison

---

## Phase 4: Output Brief

Generate a complete markdown brief:

```markdown
# REEL BRIEF — {Client} — {Topic}

## Metadata
- **Cliente:** {client_name}
- **Handle:** {handle}
- **Duración:** {duration}s
- **Estilo:** {style}
- **Pilar SPCL:** {pillar}
- **Funnel:** {funnel}
- **Fecha planeada:** {date or TBD}

## Hook (0-3s)
🗣️ "{hook_text}"
📝 ON-SCREEN: "{on_screen_hook}"
📷 {shot_description}

## Context (3-8s)
🗣️ "{context_text}"
📝 ON-SCREEN: "{on_screen_context}"
📷 {shot_description}

## Value (8-22s)
🗣️ "{value_text}"
📝 ON-SCREEN:
  - "{point_1}"
  - "{point_2}"
  - "{point_3}"
📷 {shot_description}

## CTA (22-27s)
🗣️ "{cta_text}"
📝 ON-SCREEN: "{cta_overlay}"
📷 {shot_description}

## Logo Sting (27-30s)
📷 Brand logo animation or static logo card
🎵 {brand_sound or subtle whoosh}

---

## Production Notes
- **Location:** {where to film}
- **Wardrobe:** {what to wear}
- **Props:** {what's needed}
- **Music:** {genre/mood/specific track suggestion}
- **Editing style:** {cuts pace, transitions, effects}

## Caption
{Full Instagram caption with hashtags}

## Content Hub Fields
- formato: Reel
- pilar: {EDU/SPR/PRD/LFS/ENT/TND}
- funnel: {TOFU/MOFU/BOFU}
- hook: "{hook_text}"
- cta: "{cta_text}"
- status: Brief
```

---

## Phase 5: Delivery

1. Show the brief to Gibran for review
2. If approved, the brief is ready for:
   - Gibran to film (SPEKGEN personal brand content)
   - UGC creator to film (client content)
   - Editor to assemble from existing footage
3. Store in Content Hub with `status: 'Brief'`

---

## Important Rules

1. **HOOK IS EVERYTHING** — The first 1-3 seconds determine if people watch. Spend 50% of creative energy here.
2. **On-screen text on EVERY beat** — Many watch without sound. Text must carry the message alone.
3. **Max 5 words per text overlay line** — Readable at scroll speed.
4. **Match client tone** — SPEKGEN = Gibran's personal voice. Clients = brand-appropriate.
5. **Hormozi principle**: Content = targeting. Make it FOR the avatar, not for vanity metrics.
6. **Trending audio**: When possible, suggest currently trending audio. Mark with ⚠️ if the trend has a short shelf life.
7. **SPEKGEN reels**: Gibran is always on camera. First-person. Show his face, his setup, his process.
