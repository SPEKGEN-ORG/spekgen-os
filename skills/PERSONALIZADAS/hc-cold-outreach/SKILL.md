---
name: hc-cold-outreach
version: v001
description: "Ejecuta el sistema de cold outreach email de Healthy Chuchos. Envia secuencias automatizadas B2B (5 steps) y D2C (3 steps con 4 variantes de signal) desde healthychuchos@gmail.com con throttling (max 25/dia, delay aleatorio 45-120s, horario 9AM-6PM MX). Monitorea replies via IMAP y marca status=replied automaticamente. ACTIVAR cuando Gibran diga: 'envia cold outreach HC', 'corre el batch diario', 'manda el primer envio', 'enviar emails HC', 'batch de outreach', 'test email HC', 'monitorea replies HC', 'revisa replies', 'enviar a [email] step [N]', 'dry run outreach', o cualquier variante de correr o revisar el sistema de outreach. Deliverables: envios enviados desde Gmail SMTP, log en HC_OUTREACH_SEND_LOG.xlsx, notificaciones de replies a gibran.alonzo0506@gmail.com."
---

# HC Cold Outreach — Sistema de envío automatizado

## Qué hace este skill

Ejecuta el cold email outreach de Healthy Chuchos de punta a punta:
1. **Envío** — lee prospects de `HC_PROSPECTS_MASTER.xlsx`, selecciona quién debe recibir qué step hoy, personaliza el template, envía via Gmail SMTP con throttling
2. **Sequence automática** — B2B 5 steps (días 0/3/6/9/12), D2C 3 steps (días 0/5/10) con 4 variantes D2C por signal (articular/digestivo/calma/genérico)
3. **Reply monitoring** — poll IMAP cada 15 min, detecta replies, marca `status=replied` en master list, notifica a Gibran por email
4. **Logging** — cada envío queda registrado en `HC_OUTREACH_SEND_LOG.xlsx` con timestamp, track, step, subject, status

## Reglas de throttling (hardcoded)

| Parámetro | Valor | Razón |
|---|---|---|
| Max envíos/día | 25 | Límite conservador Gmail cuenta nueva (puede ramp hasta 500/día después de 2 semanas warm) |
| Delay entre envíos | 45-120s random | Simular comportamiento humano |
| Horario permitido | 9:00-18:00 MX | Fuera de esto, `--batch` aborta |
| Warmup inicial | Día 1: 5, Día 2: 10, Día 3: 15, Día 4+: 25 | Proteger deliverability |

**Reputation Gmail:** con App Password + SPF/DKIM/DMARC correctos en healthychuchos.com, la reputación inicial es neutral. Clave: <3% bounce rate, <0.5% spam reports.

## Cuándo usar

- **Diario lunes a viernes 10 AM MX:** correr `--batch` para disparar envíos nuevos + follow-ups
- **Cada 15 min:** `outreach_reply_monitor.py --loop` corre en background detectando replies
- **Ad-hoc:** `--test --to X` para testear templates antes de un batch real
- **Reparar:** `--send-one --email X --step N` para re-enviar a un prospect específico que falló

## Comandos disponibles

### A) Correr batch diario (envíos reales)

```bash
cd "HC - HEALTHY CHUCHOS/HC - 17. OUTREACH"

# Ver qué enviaría sin enviar
python3 outreach_sender.py --batch --dry-run

# Enviar batch real (respeta horario 9-18 MX)
python3 outreach_sender.py --batch
```

El sender:
1. Lee B2B_MASTER + D2C_MASTER
2. Filtra por status (solo `new` o `sent` con días suficientes desde E1)
3. Ordena: nuevos primero (step 1), luego follow-ups
4. Envía hasta 25 con delay aleatorio
5. Actualiza `status=sent`, `current_step`, `first_sent_date`, `last_sent_date`
6. Loguea cada envío en `HC_OUTREACH_SEND_LOG.xlsx`

### B) Enviar email de prueba

```bash
python3 outreach_sender.py --test --to gibran@ejemplo.com
```

Manda un email sample para verificar que SMTP funciona, DNS está OK, y el template se ve bien.

### C) Enviar a un prospect específico (reparar)

```bash
python3 outreach_sender.py --send-one --email compras@petshop.com --step 2
```

Útil cuando:
- Un prospect no recibió el E1 por bug
- Quieres saltar el warmup y mandar step manual
- Estás testeando un template nuevo con una audiencia real

### D) Monitorear replies

```bash
# Correr una vez (última 24h)
python3 outreach_reply_monitor.py

# Últimos N días
python3 outreach_reply_monitor.py --since 7

# Daemon (loop cada 15 min)
python3 outreach_reply_monitor.py --loop
```

El monitor:
1. Conecta IMAP a healthychuchos@gmail.com
2. Busca mensajes nuevos con `In-Reply-To` o `References` (replies reales)
3. Filtra: no propios, no auto-replies, no bounces
4. Busca el sender en B2B/D2C_MASTER — si matchea, marca `status=replied` + agrega snippet a `reply_notes`
5. Envía notificación HTML a gibran.alonzo0506@gmail.com con contexto completo del prospect
6. Loguea en `HC_REPLIES_LOG.xlsx`

## Templates disponibles

### B2B (5 steps, genéricos)

| Step | Día | Asunto | Archivo |
|---|---|---|---|
| E1 | 0 | margen en suplementos caninos | `outreach_templates/b2b/step_1.html` |
| E2 | 3 | bacillus coagulans | `step_2.html` |
| E3 | 6 | tabla mayoreo + demo | `step_3.html` |
| E4 | 9 | última vez | `step_4.html` |
| E5 | 12 | seguimiento whatsapp | `step_5.html` |

### D2C (3 steps × 4 variantes por signal)

| Step | Día | Variantes | Archivos |
|---|---|---|---|
| E1 | 0 | articular, digestivo, calma, genérico | `step_1_articular.html`, `step_1_digestivo.html`, `step_1_calma.html`, `step_1.html` |
| E2 | 5 | story (único) | `step_2.html` |
| E3 | 10 | soft opt-in final (único) | `step_3.html` |

**Personalización:** merge tags `{{first_name}}`, `{{company}}`, `{{city}}`, `{{signal}}`, `{{dog_breed}}` se reemplazan automáticamente desde las columnas del xlsx.

## Antes de correr `--batch` por primera vez

Checklist pre-envío:

- [ ] `healthychuchos.com` DNS: SPF, DKIM, DMARC publicados (verificar con `dig`)
- [ ] Gmail App Password en `.env` como `HC_GMAIL_APP_PASSWORD`
- [ ] `HC_PROSPECTS_MASTER.xlsx` tiene al menos 5 prospects con email válido y `status=new`
- [ ] Templates existen en `outreach_templates/b2b/` y `outreach_templates/d2c/`
- [ ] Subject lines existen en `subjects.json` para cada track
- [ ] Hora actual está entre 9:00-18:00 MX
- [ ] `--dry-run` pasa sin errores

## Post-envío — QA (diario)

Después de cada `--batch`, abrir:

```bash
open "HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/00. DATABASE/HC_OUTREACH_SEND_LOG.xlsx"
```

Revisar:
- Status de cada envío: `sent` vs `failed`
- Errores comunes: SMTP timeout, recipient rejected, quota exceeded
- Bounces: si aparecen en reply monitor (Mailer-Daemon), marcar el prospect como `status=bounced`

Métricas target (primera semana):
- Delivery rate: ≥95%
- Reply rate B2B E1: ≥3%
- Reply rate D2C E1: ≥1%
- Unsubscribe rate: ≤2%

## Archivos clave

| Archivo | Ubicación | Propósito |
|---|---|---|
| `outreach_sender.py` | `HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/` | Sender principal |
| `outreach_reply_monitor.py` | Mismo | Reply monitor IMAP |
| `hc_gmaps_scraper.py` | Mismo | Scraper B2B (skill `/hc-lead-scraper`) |
| `outreach_templates/` | Mismo | Templates HTML + subjects |
| `HC_PROSPECTS_MASTER.xlsx` | `00. DATABASE/` | Master list prospects |
| `HC_OUTREACH_SEND_LOG.xlsx` | `00. DATABASE/` | Log de envíos |
| `HC_REPLIES_LOG.xlsx` | `00. DATABASE/` | Log de replies detectados |

## Credenciales

En `HC - HEALTHY CHUCHOS/.env`:

```
HC_GMAIL_USER=healthychuchos@gmail.com
HC_GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

**Nunca mostrar el App Password en outputs.** El sender lo lee automáticamente.

## Automatización sugerida (launchd macOS)

Para correr el batch diariamente sin intervención:

```xml
<!-- ~/Library/LaunchAgents/com.spekgen.hc-outreach-batch.plist -->
<dict>
  <key>Label</key><string>com.spekgen.hc-outreach-batch</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/ruta/absoluta/HC - HEALTHY CHUCHOS/HC - 17. OUTREACH/outreach_sender.py</string>
    <string>--batch</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>10</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
</dict>
```

Y el reply monitor cada 15 min:

```xml
<key>StartInterval</key><integer>900</integer>
```

## Troubleshooting

| Síntoma | Diagnóstico | Fix |
|---|---|---|
| SMTP auth failed | App Password revocado o MFA roto | Regenerar App Password en Google Account |
| "Fuera de horario" | Corriendo antes 9 AM o después 6 PM MX | Esperar o usar `--dry-run` para preview |
| "No hay prospects" | Todos en `sent` sin día suficiente, o todos `replied/bounced` | Scrapear más con `/hc-lead-scraper` |
| Bounce rate alto (>5%) | DNS mal, emails viejos en master, cuenta Gmail marked | Revisar dig SPF/DMARC, correr email validator, pausar 48h |
| Reply monitor no detecta | IMAP auth OK pero no matchea subjects | Revisar `outreach_markers` en monitor, ajustar si subjects cambiaron |

## Relación con otros skills

- **`/hc-lead-scraper`** → alimenta `HC_PROSPECTS_MASTER.xlsx` con nuevos B2B
- Este skill → envía a esos prospects
- **`/hc-meta-ads-analyzer`** → reporta ad performance (complementa el outreach)

## Roadmap

- [ ] Agregar soporte WhatsApp blaster (WA_MASTER + GHL API)
- [ ] A/B test automático de subject lines en E1
- [ ] Warmup automation (rampa gradual día 1-14)
- [ ] Dashboard HTML con metrics consolidadas (opens/clicks via pixel tracking opcional)
- [ ] Integración con Shopify Customers → auto-exclude compradores existentes
