---
name: Cloud Environment Migration Plan
description: Plan de migración a Claude Code Cloud Environment para autonomía en Japón. Prueba semana 2-7 abril 2026.
type: project
---

## Decisión (2026-04-02)

Migrar operaciones de SPEKGEN a Claude Code Cloud Environment para que Gibran pueda operar desde cualquier dispositivo durante Japón (mayo 1-21).

**Recurso existente:** `claude-code-default` — ya disponible en Max Plan, sin costo adicional.

## Arquitectura Cloud para Japón

```
Cloud Environment (pieza central)
├── Workspace con archivos, scripts, skills
├── Scheduled tasks remotas (corren sin Mac)
├── Accesible via claude.ai/code desde cualquier dispositivo
│
├── Make.com (pegamento)
│   └── Conexiones simples: GHL→Sheets, Meta→alertas email
│
├── Meta API (directo)
│   └── Scheduling de posts, upload de ads, lectura de métricas
│
├── GHL (autónomo)
│   └── Automations de CRM para MG, bot WhatsApp LF
│
└── Google Apps Script (autónomo)
    └── Inventory sync LF + GR (cada 4h)
```

## Plan de Prueba — Semana del 2-7 abril 2026

| Paso | Tarea | Status |
|---|---|---|
| 1 | Conectar al cloud environment desde Claude Code | DONE (2026-04-02) |
| 2 | Verificar qué archivos/workspace tiene acceso | DONE — clona repo GitHub, /home/user/Spekgen-ops/ |
| 3 | Probar internet/network | DONE — Network: Full. HTTP/HTTPS/APIs todas PASS |
| 4 | Probar commit + push a GitHub | DONE — Commit + push funciona |
| 5 | Probar scheduled task remota (que corra sin Mac) | PENDIENTE |
| 6 | Probar acceso desde teléfono via claude.ai/code | PENDIENTE |
| 7 | Documentar resultado y decisión final | EN PROGRESO |

### Resultados Test 1 (2026-04-02)
- Linux 6.18.5 x86_64, root access
- Python 3.11.15, Node v22.22.2, git 2.43.0
- Network: NECESITA "Full" (default "Trusted" bloquea salida). Ya configurado.
- Commit + push: funciona (pushea a branches, no directo a main)
- GitHub repo: g-bran/Spekgen-ops conectado y funcional
- GitHub username: g-bran

## Qué cambia vs Local

| Aspecto | Local (actual) | Cloud Environment |
|---|---|---|
| Archivos | En Google Drive (Mac) | En contenedor cloud |
| Scheduled tasks | Requiere Mac encendida + Claude abierto | Corren en cloud sin Mac |
| Acceso | Solo desde Mac con Claude Code | Desde cualquier dispositivo con internet |
| MCPs | Todos los configurados localmente | Hay que verificar cuáles funcionan en cloud |
| Google Drive | Acceso directo via filesystem | Necesita alternativa (API o sync) |

## Connectors Configurados (2026-04-02)

TODOS los servicios que usamos localmente ya tienen connector en cloud:

| Connector | Status | Herramientas |
|---|---|---|
| Google Drive | Connected | Acceso a archivos de Drive |
| GitHub | Connected | Repos, PRs, issues |
| ClickUp | Connected | 23 tools (read-only) |
| Gmail | Connected | 6 read + 1 write (crear borradores) |
| Google Calendar | Connected | 5 read + 4 write |
| Make | Connected | 65 tools (read-only) |
| Canva | Connected | 4 interactive + 14 read |
| GHL | Custom connector disponible (no conectado aún) |

## Limitaciones Descubiertas (2026-04-02 a 04-03)

1. **Connectors de claude.ai NO funcionan en Claude Code cloud.** CONFIRMADO DEFINITIVAMENTE en browser Y desktop app. Los connectors (Drive, ClickUp, Gmail, etc.) configurados en claude.ai/settings/connectors solo sirven para el chat regular de claude.ai, NO para claude.ai/code. Cloud Code solo tiene: filesystem del repo + internet (curl/APIs) + GitHub MCP + code tools + web tools + agents. Bug reportado: GitHub #35899.
2. **Modelo:** Browser cloud = Sonnet 4.6. Desktop app + cloud = Opus 4.6. Para trabajo interactivo complejo, desktop app + cloud es viable.
3. **Skills locales:** Los skills creados localmente (.claude/commands/) no están en cloud. Habría que migrarlos al repo GitHub.
4. **Para acceder a Google Drive desde cloud:** Usar Google Drive API via curl con OAuth token, o sincronizar archivos clave al repo GitHub.
5. **Para acceder a ClickUp/Gmail/etc desde cloud:** Usar las APIs directamente via curl/Python con tokens en environment variables.

## Estrategia Revisada (2026-04-03)

Dado que connectors NO funcionan en cloud, la estrategia se divide en dos:

```
LOCAL (Mac + Claude Code desktop)    CLOUD (claude-code-default)
├── Trabajo interactivo diario       ├── Scheduled tasks autónomas
├── Todos los MCPs/connectors        ├── Scripts Python con API tokens
├── Opus 4.6                         ├── Meta API, Gmail SMTP, etc.
├── Google Drive filesystem          ├── GitHub repo como filesystem
└── Sesiones de producción           └── Corre sin Mac encendida
```

**Para Japón:**
- Cloud = ejecutor autónomo (scheduled tasks, scripts que corren solos)
- Teléfono + claude.ai/code = intervenciones manuales rápidas (revisar, aprobar, ajustar)
- NO depender de connectors — todo via API directa con tokens en env vars

**Why:** Gibran vuela a Japón ~30 abril. WiFi mínimo disponible. Cloud environment permite scheduled tasks sin Mac + sesiones cortas de revisión desde móvil.

**How to apply:** Trabajo diario sigue en local (mejor experiencia). Cloud solo para: (1) scheduled tasks que deben correr sin Mac, (2) acceso de emergencia desde teléfono. SMTP bloqueado en cloud — emails via Make.com webhook → Gmail.

## Primer Task Migrado: SkyDropx Notifier (2026-04-03)

- **Script:** `scripts/skydropx_notifier.py` en repo `g-bran/Spekgen-ops`
- **Scheduled task:** "notifier de SkyDropx-CLOUD" — hourly at :59
- **Pipeline:** Cloud Script (SkyDropx API) → Make.com webhook → Gmail
- **Webhook:** `https://hook.us2.make.com/fj7xmmf8wbpdk5jwa9v5f43nxsqpt3in`
- **Make scenario:** ID 4622703, folder LO FITNESS
- **Estado persistente:** notified_shipments.json en el repo
- **Hallazgos clave:**
  1. SMTP (puerto 465) bloqueado en cloud — Make.com como email proxy funciona perfecto
  2. RemoteTrigger API da `Unable to resolve organization UUID` — pero la UI de Scheduled Tasks SI funciona para crear cloud tasks
  3. Scheduled tasks en la UI permiten agregar connectors (Canva, ClickUp, Gmail, Calendar, Make)
  4. Patron replicable: cualquier script que necesite enviar email en cloud → Make webhook
