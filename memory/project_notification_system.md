---
name: SPEKGEN Notification System
description: Email notification system for client comms — spekgen_notify.py script, events, architecture, Gmail SMTP
type: project
originSessionId: c0d489c0-ebb2-4ec3-84cd-e54179eee763
---
Sistema de notificaciones por email para comunicación con clientes.

**Script:** `SPK - SPEKGEN AGENCY/SPK - 10. AUTOMATION/spekgen_notify.py`
**Log:** `SPK - SPEKGEN AGENCY/SPK - 10. AUTOMATION/notification_log.jsonl`
**Sender:** spekgen.ai@gmail.com via Gmail SMTP (App Password en LF/.env: SPEKGEN_GMAIL_APP_PASSWORD)

**Why:** Los clientes necesitan saber cuándo hay posts listos, cambios de caption, o publicaciones exitosas. Antes se hacía manual.

**How to apply:** Usar `spekgen_notify.py` cada vez que:
- Se sube un post nuevo al portal (--event post_ready)
- Se modifica un caption (--event caption_updated)
- Se publica un post (--event post_published)
- Falla una publicación (--event publish_failed → solo Gibran)
- Mensaje custom (--event custom)

**Eventos soportados:**
| Evento | Destinatario | Cuándo |
|--------|-------------|--------|
| post_ready | Cliente | Post nuevo en portal con status "review" |
| caption_updated | Cliente | Se modificó copy de un post existente |
| post_published | Cliente | Auto-publish exitoso en IG/FB |
| publish_failed | Gibran (interno) | Error en auto-publish |
| custom | Cliente | Mensaje libre |

**Clientes registrados:** HC (monsealonzougc@gmail.com → solo Monse). Enrique REMOVIDO 2026-04-14 por pedido de Gibran. Gibran (gibran.alonzo0506@gmail.com) se agrega auto como CC en post_ready/caption_updated/post_published desde 2026-04-14.

**WIRING:** `upload_post_to_hub.py` (Content Hub Shopify) dispara `spekgen_notify.py` auto al final del upload — mapeo: status=review→post_ready, status=published→post_published. Patch aplicado 2026-04-14 (antes no había notificación auto, todos los uploads previos fueron silenciosos).

**Uso:**
```bash
python3 spekgen_notify.py --event post_ready --client hc --post HC-008
python3 spekgen_notify.py --event caption_updated --client hc --post HC-007 --detail "Cambió de duo a solo DogRelax"
python3 spekgen_notify.py --event post_published --client hc --post HC-007 --ig-url URL --fb-url URL
python3 spekgen_notify.py --event publish_failed --client hc --post HC-007 --detail "IG API error code 2"
```

**Fase 2 (pendiente, pre-Japón):** Integrar al auto-publish endpoint en Vercel para que mande notificación automática después de publicar. Opciones: (1) llamar script desde Claude Cloud via Remote Trigger, (2) agregar envío SMTP directo al endpoint de Next.js.

**Decisión de arquitectura (2026-04-06):** Claude Cloud > Make para notificaciones. Razones: inteligencia contextual, sin costo de operaciones Make, centralización.

**Update 2026-04-23 — notificaciones de acciones del cliente en portal:**
- Scenario Make 4706750 (SHOPIFY — Content Hub Actions) ahora tiene Route 5 con módulo `google-email:sendAnEmail` v4 que dispara email a Gibran en cada acción del cliente (approve/reject/changes_copy/changes_visual/edit_copy). Usa connection 8183100 (spekgen.ai@gmail.com). HTML inline con action label + color dinámico + detalle + link al portal.
- GH Actions workflow `spekgen-notify.yml` (repo g-bran/Spekgen-ops) también deployed y testeado: workflow_dispatch con inputs event/client/post/detail/category/publish_date/publish_time/subject. Ejecuta spekgen_notify.py en cloud. Secret: SPEKGEN_GMAIL_APP_PASSWORD.
- Nuevos eventos agregados a spekgen_notify.py: `post_approved`, `post_rejected`, `changes_requested` (con flag --category copy|visual|general). Templates HTML con dominio spekgen.com/pages/{client}-vault.
- Pendiente: validar end-to-end con approve real. Execution 26da07f del 2026-04-23 quedó en RUNNING por bug preexistente de timeout en OAuth Shopify (módulo 3 del scenario, 40s+). Posible fix: cachear access_token en data store Make.
