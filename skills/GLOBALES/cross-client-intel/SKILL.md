---
name: cross-client-intel
description: >
  Analisis cross-client de Meta Ads para GREENRAY, HEALTHY CHUCHOS y LO FITNESS.
  Jala insights ultimos 14 dias de las 3 cuentas via Marketing API v21.0, normaliza
  por baseline de cada cuenta, detecta winners replicables cross-client, losers a
  pausar (validados contra regla CPA-por-producto = precio - $150), y genera un
  reporte HTML + PDF con tema dark purple SPEKGEN que se abre en Preview y se
  revela en Finder. Tambien se ejecuta automaticamente cada 3 dias en GitHub
  Actions (cron "0 15 */3 * *" = 9 AM MX) y envia el PDF por email a
  gibran.alonzo0506@gmail.com via Gmail SMTP.
  Activar para: "corre el cross-client intel", "analiza los 3 clientes",
  "genera el reporte cross-client", "cross-client insights", "que me dice la red",
  "reporte semanal de ads", "lecciones entre clientes".
trigger_phrases:
  - "corre el cross-client intel"
  - "analiza los 3 clientes"
  - "genera el reporte cross-client"
  - "cross-client insights"
  - "que me dice la red"
  - "reporte semanal de ads"
  - "lecciones entre clientes"
---

# cross-client-intel

Skill global para **inteligencia cross-client de Meta Ads**. Mira GR + HC + LF
en una sola vista, extrae patrones, detecta leaks, y recomienda replicaciones.

## Por que existe

SPEKGEN tiene 3 cuentas de Meta Ads, cada una con su propio monitor individual.
Lo que faltaba era la vista de conjunto: que formato gana en un cliente pero nadie
lo ha probado en otro, cual ad esta quemando capital sin retorno, cuales son los
patrones emergentes de la red.

Corriendo este skill cada 3 dias (cron auto o manual), Gibran recibe un PDF con:

1. Snapshot por cuenta (spend, compras, ROAS)
2. Ads a PAUSAR con confianza (CPA real excede precio - 150)
3. Winners cross-client (ROAS >= 2, spend >= 50) listos a replicar
4. Plan de replicacion bidireccional (LF -> HC, LF -> GR, GR -> HC, etc.)
5. Senales a vigilar en el siguiente pull

## Comandos

### `run`
Corre el analisis completo ahora mismo y produce el reporte del dia.

```bash
python3 "SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/cross-client-intel/scripts/run.py"
```

Flujo:
1. Corre `cross_client_pull.py --days 14` (ya existe)
2. Renderiza HTML con plantilla + data fresca
3. Convierte HTML -> PNG (Playwright full_page screenshot, 2x scale) -> JPEG 85% -> PDF via img2pdf
4. Guarda ambos archivos en `_cross_client_intel/CROSS_CLIENT_INSIGHTS_{FECHA}.{html,pdf}`
5. `open` del PDF + `open -R` para revelar en Finder

### `pause`
Pausa los ads marcados como `PAUSAR` en el ultimo reporte. **No se ejecuta solo**
como parte de `run` — es un paso manual con confirmacion. Lee el archivo de
plan generado por `run` (`pause_plan_{FECHA}.json`).

```bash
python3 "SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/cross-client-intel/scripts/pause.py"
```

Pide confirmacion `y/n` antes de disparar los PAUSE a Meta API y escribe log
`pause_log_{FECHA}.json`.

## Como actuar sobre el reporte

### 1. Revisar ads a PAUSAR (seccion 2 del PDF)
Cada ad listado cumple: `CPA_real > (precio_producto - 150)` o `spend > 100 MXN
con 0 compras en 14 dias`. Si estas de acuerdo:
```
python3 scripts/pause.py
```
Confirmar con `y`. Los ads pasan a `PAUSED` status en Meta.

### 2. Replicar winners (seccion 4 del PDF)
Por cada "accion sugerida" (ej. "LF -> HC: crear UGC_PERSONA tutor perro para
ArtriDog"), invocar skills existentes:
- Para crear ads nuevos: `/spekgen-meta-ads-upload` con brief en el formato
  canonico `[CLIENT]-AD-[NNN]_[FORMATO]_[PRODUCTO]_[VARIANTE]`
- Para generar creatives: `/spekgen-image-creator` o `/carousel-generator`

### 3. Monitorear senales (seccion 5 del PDF)
El reporte lista "preguntas abiertas" que el siguiente pull debe responder
(ej. "LUPITA sostiene ROAS al escalar?"). Al correr `run` en 3 dias, cruzar
manualmente las respuestas contra estas preguntas.

## Automatizacion (GitHub Actions)

Workflow: `.github/workflows/cross-client-intel.yml` en repo `Spekgen-ops`.

Cron: `0 15 */3 * *` (cada 3 dias a las 15:00 UTC = 9:00 AM Mexico).

Proceso automatico:
1. Checkout del repo
2. Setup Python 3.11
3. Install deps: `playwright`, `img2pdf`, `pillow`
4. `playwright install chromium`
5. Corre el pull + render + PDF
6. Envia email a `gibran.alonzo0506@gmail.com` con el PDF adjunto via Gmail SMTP
7. Sube el PDF como artifact de GH Actions (retencion 30 dias)

### Secrets necesarios en el repo GH (Settings -> Secrets -> Actions)

| Secret | Para que sirve | Estado |
|---|---|---|
| `META_TOKEN_GR` | Token GR (o usar `META_TOKEN` global si es unificado) | usar existente `META_TOKEN` |
| `META_TOKEN_HC` | Token HC | usar existente `META_TOKEN` |
| `META_TOKEN_LF` | Token LF | agregar (diferente del token unificado) |
| `META_AD_ACCOUNT_GR` | Ad account id GR | ya existe como `GR_AD_ACCOUNT` |
| `META_AD_ACCOUNT_HC` | Ad account id HC | ya existe como `HC_AD_ACCOUNT` (verificar) |
| `META_AD_ACCOUNT_LF` | Ad account id LF | agregar |
| `SPEKGEN_GMAIL_SENDER` | spekgen.ai@gmail.com | ya existe |
| `SPEKGEN_GMAIL_APP_PASSWORD` | App password Gmail | ya existe |
| `REPORT_RECIPIENT` | gibran.alonzo0506@gmail.com | agregar (o hardcoded en workflow) |

> **Nota:** El token META puede ser el mismo unificado para GR+HC+Gibran Ecom.
> LF usa un token distinto (ver `LF - LO FITNESS/.env`). El workflow
> acepta ambos esquemas.

## Estructura de archivos

```
cross-client-intel/
  SKILL.md              <- este archivo
  scripts/
    run.py              <- orquesta pull + render + PDF + open
    pause.py            <- pausa los ads del plan ultimo (requiere confirm)
    render_report.py    <- genera HTML+PDF desde json del pull
    detect_actions.py   <- detecta winners/losers aplicando reglas CPA
    templates/
      report.html.tmpl  <- template HTML (dark purple SPEKGEN)
```

## Reglas de deteccion (detect_actions.py)

### Ads a PAUSAR (listos para confirmar con `pause`)
- `spend > 100 MXN AND purchases == 0` en 14 dias
- `CPA_real > (precio_producto - 150 MXN)` cuando hay purchases
- Adicional: `kill_ad_hard` flag si ya paso spend = 4x del CPA_max sin compra

### Precios por producto (para calcular CPA_max = precio - 150)

| Cliente | Producto | Precio MXN | CPA max |
|---|---|---|---|
| LF | METAFIT | 498 | 348 |
| LF | OMEGA3 | 390 | 240 |
| LF | CITMG / CITPT | 310 | 160 |
| LF | KIT / 2PACK | 899 | 749 |
| HC | ARTRIDOG | 350 | 200 |
| HC | DOGRELAX | 350 | 200 |
| HC | GASTRODOG | 350 | 200 |
| HC | OMEGADOG | 380 | 230 |
| GR | ARTRIX / GXAMIN | 410 | 260 |
| GR | HORMO | 650 | 500 |
| GR | COLAGENO | 390 | 240 |
| GR | BELLSAN | 320 | 170 |
| GR | PROTOCOLO | 1200 | 1050 |

> Precios de referencia — validar contra PDP actual de cada cliente si hay duda.
> Defaults si producto no se detecta: `CPA_max = 200 MXN`.

### Winners a replicar
- `spend >= 50 MXN` Y
- `ROAS >= 2.0` Y
- `purchases >= 1` en 14 dias
- Ordenados por `ROAS desc`

### Plan de replicacion bidireccional
Para cada formato que sea winner en un cliente (ej. `UGC_PERSONA` en LF):
- Sugerir replicar a los otros 2 clientes donde ese formato tenga spend < 30 MXN
  o ads_count < 2
- Formato del sugerido: `[CLIENT]-AD-NNN_[FORMATO]_[PRODUCTO]_VAR01/02/03`

## Historico

- **2026-04-17** — Primer reporte manual (Gibran + Claude). 5 ads pausados,
  $4,044 MXN quemados. Winners detectados: LUPITA_ICONBAR, OFFER_2PACK, COLAGENO
  fitness. Gap critico: LF sin monitor automatizado.
- **2026-04-17** — Skill creado + workflow para automatizacion cada 3 dias.
