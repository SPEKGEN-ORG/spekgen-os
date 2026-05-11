# HC Operations Hub — single entry point Desktop

**LIVE desde 2026-05-01.** Patrón análogo a SPEKGEN Tracker.app pero para HC.

## Path

`HC - HEALTHY CHUCHOS/HC - 99. OPS HUB/`

```
├── index.html              ← main hub con 5 secciones
├── HC Operations.app       ← .app bundle macOS (también copiado a ~/Desktop/)
├── tools.json              ← config canonical
├── update_hub.py           ← regenerador del index.html
├── refresh_stats.py        ← live stats wrapper
├── README.md               ← uso, agregar tools, troubleshooting
├── snapshots/              ← log de generaciones
└── assets/
    ├── hc-logo.png         ← copiado de HC - 01. BRAND MEDIA/00. LOGOS/logohc-12.png
    └── icons/              ← Lucide / emojis por sección
```

## Stack

- HTML estático con Tailwind CDN + Lucide Icons + Chart.js
- Paleta HC: navy `#1A1464`, naranja `#E8852E`, cream `#F5F0DD`, teal `#2A9D8F`
- Live stats del Abandoned Cart Dashboard en hero (jala del último snapshot JSON)

## Secciones y tools (15 registrados al día 1)

- **📧 Marketing Automation:** Abandoned Cart Dashboard (local-html)
- **📊 Analytics:** GA4, Microsoft Clarity, Meta Ads Dashboard sheet (external)
- **🛒 E-commerce:** Shopify Admin, Content Hub portal cliente, healthychuchos.com (external)
- **🤖 Backend:** GHL HC workspace, Make scenarios HC, Supabase HC project, Resend (external)
- **📝 Local Files:** _CLIENT_CONTEXT.md, _KNOWLEDGE_BASE.md, Carpeta HC, Abandoned Cart folder

## Tipos de tool en tools.json

- `external` → URL en navegador (target=_blank)
- `local-html` → file:// HTML local (path relativo desde HUB folder)
- `local-file` → abre archivo con app default del sistema
- `folder` → abre carpeta en Finder

## Para agregar tool nuevo

1. Editar `tools.json` con nueva entry en sección apropiada
2. Correr `python3 update_hub.py`
3. Index.html regenerado con nueva card

## Patrón replicable

A LF/GR/MG cuando crezcan los tools locales. Misma estructura, diferente paleta + tools registry.

## Comando para abrir

```bash
open "/Users/gibranalonzo/Library/CloudStorage/GoogleDrive-gibran.alonzo0506@gmail.com/My Drive 2/01. CLIENTS OFFICIAL/HC - HEALTHY CHUCHOS/HC - 99. OPS HUB/HC Operations.app"
```

O desde Desktop: double-click en `HC Operations.app`.

## Gatekeeper warning primera vez

Click derecho → Open → Open Anyway. Después double-click normal.
