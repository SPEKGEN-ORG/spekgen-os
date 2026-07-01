# SPEKGEN Social Manager (IG/FB)

Detecta y (próximamente) responde **DMs y comentarios sin atender** en Instagram y Facebook
para los clientes de SPEKGEN. Complementa los bots de WhatsApp existentes.

Plan completo: `~/.claude/plans/bro-quiero-que-me-shimmying-sunbeam.md`
Memoria: `project_social_manager_ig_fb`

## Estado

| Fase | Qué | Estado |
|---|---|---|
| 0 | Auditar apps/scopes Meta | ✅ Hecho |
| 1 | Barrido + cola Supabase + digest email | ✅ Hecho (piloto HC/LF/F24) |
| 2 | Cerebro Claude + borradores de comentarios + aprobación | ⏳ Pendiente |
| 3 | Auto-reply de DMs (HC/LF) + webhooks tiempo real | ⏳ Pendiente |

## Hallazgo clave

Los comentarios accionables de clientes ad-heavy **NO están en el feed orgánico** —
viven en los **anuncios (dark posts)**. El barrido itera
`act_X/ads → creative.effective_object_story_id → /{story}/comments`.
Esa es la fuente real (F24: 0 orgánico, 100% en ads).

## Arquitectura

```
social_sweep.py  ──► social_inbox (Supabase)  ──► social_digest.py (email)
  3 fuentes:                  dedupe por              agrupa por cliente,
  FB feed / IG media / ADS    external_id             solo señal (pending)
```

- **Tokens:** 1 por Business Manager. HC→agency, LF→lf, F24→f24 (cada cliente su `.env`).
- **Cola:** tabla Supabase `social_inbox` (RLS on, solo service_role). Dedupe por `external_id`,
  `ignore-duplicates` (no resucita items ya gestionados por un humano).
- **Filtro:** descarta cuentas internas (`internal_accounts` en `clients.json`) y ruido
  (comentarios solo-emoji) → `status='skipped'`. La señal real queda `status='pending'`.
- **Sin dependencias pip** — solo stdlib (urllib, smtplib).

## Uso local

```bash
python3 social_sweep.py --client F24 --dry-run   # solo lee, no escribe
python3 social_sweep.py --client all             # barre y escribe a Supabase
python3 social_digest.py --test                  # preview HTML, no envía
python3 social_digest.py                          # envía digest a digest_email
```

Local lee tokens de los `.env` del Drive automáticamente (`lib/secrets.py`).

## Cron (GH Actions)

`.github/workflows/social-sweep.yml` — barrido cada 3h, digest 9am MX.
**Secrets requeridos en el repo** (Settings → Secrets):
`AGENCY_META_TOKEN`, `LF_META_TOKEN`, `F24_META_TOKEN`,
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SPEKGEN_GMAIL_APP_PASSWORD`, `ANTHROPIC_API_KEY`.

## Scopes Meta (auditado 2026-06-27)

| Scope | Agency | LF | F24 |
|---|---|---|---|
| IG DMs / comments | ✅ | ✅ | ✅ |
| FB comments (engagement) | ✅ | ✅ | ✅ |
| `pages_messaging` (Messenger DM) | ❌ App Review | ❌ App Review | ✅ |

DMs de IG + comentarios = listos. DM de Messenger en Agency/LF requiere App Review (Fase 3).

## Reglas

- **F24 = solo borrador en todo.** Nunca auto-publica (WABA baneada, riesgo de sanción).
- Precios/links **verbatim** del knowledge del cliente (anti-alucinación).
- Ortografía ES correcta (ñ/tildes).
- Ventana 24h de mensajería para DMs.
