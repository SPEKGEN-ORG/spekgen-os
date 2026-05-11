---
name: Obsidian Vault Setup
description: SPEKGEN Obsidian vault — estado actual, plugins, modelo de uso, trigger de cierre
type: project
originSessionId: 8d248559-d5d8-46cf-8ced-c85706017595
---
# Obsidian Vault (actualizado 2026-04-18)

Vault root: `/01. CLIENTS OFFICIAL/`. Lee los .md existentes directamente, no duplica nada.

## Plugins instalados y activos

- **Dataview** — queries DQL en dashboards. Inline prefix `=`. Sintaxis correcta: `date(today)`, NO `dv.date()` (eso es JS, no DQL)
- **Templater** — templates con `tp.date.now()`. Folder template: `02 - DAILY NOTES` → `Daily Note.md`. `trigger_on_file_creation: true`
- **Calendar** — ícono en sidebar derecho, abre daily note del día

## Modelo de uso (CRÍTICO)

**Claude escribe, Gibran lee.** Gibran no llena nada manualmente.

- Al cierre de sesión, Claude escribe en la daily note del día
- Obsidian muestra el Tasks Board con todos los `- [ ]` agregados por Claude
- Gibran abre Obsidian para monitorear qué hizo Claude, qué quedó pendiente, qué cliente está stale

## Trigger de cierre de sesión

Palabra: **"platano"** (con o sin tilde) → Claude ejecuta protocolo completo de cierre inmediatamente.

## Protocolo de cierre (paso 5 — Obsidian)

Path daily note: `_OBSIDIAN/02 - DAILY NOTES/YYYY-MM-DD.md`
- Si no existe, crear con estructura base (sin sintaxis Templater)
- Actualizar "Clientes trabajados hoy"
- Agregar entrada en "Sesiones" con: qué se hizo, decisiones, pendientes `- [ ]`
- Los `- [ ]` aparecen automáticamente en Tasks Board

## Estructura del vault

```
_OBSIDIAN/
├── 00 - DASHBOARDS/
│   ├── Home.md              ← entry point, fechas dinámicas con Dataview DQL
│   ├── Clients.md
│   ├── Clients Status.md    ← muestra cuándo se modificó cada _CLIENT_CONTEXT
│   ├── Japan Sprint.md      ← countdown dinámico
│   ├── Daily Notes Index.md ← lista Dataview de todas las daily notes
│   ├── Tasks Board.md       ← agrega todos los - [ ] de daily notes
│   └── Recent Activity.md   ← últimos 25 archivos modificados
├── 01 - TEMPLATES/
│   └── Daily Note.md        ← template con Templater syntax
├── 02 - DAILY NOTES/        ← YYYY-MM-DD.md por día (Claude los crea)
└── 03 - INBOX/
```

## Shortcuts clave (para decirle a Gibran)

- `Cmd + O` — abrir cualquier archivo
- `Cmd + Shift + F` — buscar en todo el vault
- `Cmd + E` — toggle editar/preview
- `Cmd + P` — command palette

## Sync

Google Drive for Desktop. NO Obsidian Sync.
