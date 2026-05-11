---
name: kill-prospect
description: Da de baja un prospecto sin respuesta. Borra las páginas Shopify (mockup + propuesta + redirects + versiones viejas), actualiza el pipeline xlsx (Status → "No interesado" + nota fechada), archiva la carpeta del prospecto, y lo registra en _kill_log.md. Soporta gracia (`--in 24h`) que encola la baja para ejecutarse después. Activar cuando Gibran diga "kill prospect X", "da de baja a X", "borra el link de X", "archiva al prospecto X", "Y ya no contestó, baja", o cualquier variante de cerrar a un prospecto frío. Acepta resolver por ID (LP-090), nombre del negocio (mariscos), slug (mariscoslosloure), o teléfono.
---

# /kill-prospect

Cierra un prospecto frío y limpia su huella pública.

## Cuándo usar

- Prospecto no responde tras 2-3 follow-ups
- Gibran quiere bajar el link público para no tenerlo expuesto indefinidamente
- Limpieza periódica del pipeline (status "Interesado" estancado)

## Uso

**Inmediato:**
```bash
cd "SPK - SPEKGEN AGENCY/PROSPECTOS/mockup_factory"
python3 _kill_prospect.py kill --query "LP-090" --reason "Sin respuesta tras 3 follow-ups"
```

**Con gracia (encolar para 24h después):**
```bash
python3 _kill_prospect.py kill --query "mariscos" --in 24h
```

**Procesar la cola (ejecuta los kills cuyo `execute_at` ya pasó):**
```bash
python3 _kill_prospect.py process-pending
```

**Dry run (no hace nada, solo muestra qué haría):**
```bash
python3 _kill_prospect.py kill --query "LP-090" --dry-run
```

**Listar la cola pendiente:**
```bash
python3 _kill_prospect.py list-pending
```

## Flags

| Flag | Default | Descripción |
|---|---|---|
| `--query` | requerido | ID exacto (LP-090), nombre, slug o teléfono. Si matchea múltiples, error con la lista |
| `--reason` | "Sin respuesta tras follow-ups" | Razón que se loguea en xlsx + log |
| `--in` | inmediato | `24h`, `2d`, `30m` — encola para ejecutar después |
| `--dry-run` | false | No ejecuta, solo muestra |

## Qué hace

1. **Resuelve el prospecto** en `SPEKGEN_PROSPECTOS.xlsx` (matchea contra ID/nombre/slug/teléfono/URL)
2. **Borra del Shopify:**
   - Todas las pages cuyo handle empiece con `{slug}mockup-v` o `{slug}propuesta-v` (versiones nuevas)
   - Pages legacy con handle exacto `{slug}mockup` / `{slug}propuesta`
   - URL redirects `/{slug}mockup` y `/{slug}propuesta`
3. **Actualiza pipeline xlsx:**
   - Status → `No interesado`
   - Nota append: `[DD/MM] BAJA: {reason}`
4. **Archiva carpetas:**
   - `mockup_factory/generated/{slug}/` → `mockup_factory/generated/_KILLED/{slug}_{timestamp}/`
   - `_prospectos/{NOMBRE}/` → `_ARCHIVED/{NOMBRE}/` (si existe)
5. **Append a `_kill_log.md`** con fecha, ID, slug, razón, y lo que se borró

## Modo gracia (`--in`) — Japan-proof

La cola vive en `Spekgen-ops/state/pending_kills.json` (cloud source of truth). Cuando corres `kill --in 24h`, el script local:

1. Encola en el repo (no en Drive)
2. Hace `git add + commit + push` automático (best-effort — si falla, te avisa)
3. La **GH Action `Kill Prospect Processor`** corre cada día a las **8:05 AM hora La Paz** (14:05 UTC) y procesa los kills vencidos
4. Manda email resumen a Gibran si procesó algo

**Esto significa que aunque estés en Japón sin WiFi, los kills se ejecutan a tiempo.**

**Comandos manuales que puedes seguir corriendo:**
- `process-pending` — fuerza procesado local (también borra Shopify; útil si la GH Action falló)
- `list-pending` — lista la cola (lee del repo si está disponible)

**Trigger manual del workflow:**
```bash
gh workflow run kill-prospect-processor.yml --repo g-bran/Spekgen-ops
```

## Secrets requeridos en GH (ya configurados)

Reusa los del Content Hub + cross-client-intel. NO necesitas crear nada nuevo:

| Secret | Origen |
|---|---|
| `SHOPIFY_SHOP` | Content Hub |
| `SHOPIFY_CLIENT_ID` | Content Hub |
| `SHOPIFY_CLIENT_SECRET` | Content Hub |
| `SPEKGEN_GMAIL_SENDER` | cross-client-intel |
| `SPEKGEN_GMAIL_APP_PASSWORD` | cross-client-intel |
| `REPORT_RECIPIENT` | cross-client-intel |

## Diferencia local vs cloud

- **Local script** (`_kill_prospect.py`): borra Shopify + actualiza xlsx + archiva carpetas + log.
- **Cloud processor** (GH Action): solo borra Shopify y manda email.

El xlsx y las carpetas locales se actualizan **cuando regresas a la compu y corres `process-pending`** (idempotente — si la GH Action ya borró Shopify, el script local solo actualiza xlsx + archiva). En Japón los links están abajo aunque tu xlsx local quede desactualizado por 21 días — no rompe nada.

## Output

```
🎯 Dando de baja: LP-090 — Mariscos Los Laureles
   URL: spekgen.com/mariscosloslauremockup
   Slug: mariscosloslaure
   Razón: Sin respuesta tras 3 follow-ups

[1/4] Shopify: borrando pages + redirects...
    🗑  deleted page handle=mariscoslosloremockup-v82363c
    🗑  deleted page handle=mariscoslosloure propuesta-vc24a04
    🗑  deleted redirect /mariscosloslauremockup
    🗑  deleted redirect /mariscoslosloure propuesta
    Total: 2 pages + 2 redirects

[2/4] Pipeline xlsx: actualizando status...
    ✓ LP-090: Interesado → No interesado

[3/4] Archivando carpetas...
    ✓ mockup_factory/generated/mariscosloslaure → _KILLED/mariscosloslaure_20260506_134500
    (no hay carpeta en _prospectos/, skip)

[4/4] Log append...
    ✓ _kill_log.md

✅ DONE — LP-090 dado de baja.
```

## Restaurar (si se equivoca)

No hay deshacer automático. Para recuperar:
1. La carpeta sigue en `mockup_factory/generated/_KILLED/{slug}_{timestamp}/` — moverla de regreso
2. Re-publicar con `/publish-prospect` (regenera pages + redirects)
3. Cambiar status manualmente en xlsx

Por eso el skill **no borra archivos del filesystem** — solo los archiva.

## Ruta del script

`SPK - SPEKGEN AGENCY/PROSPECTOS/mockup_factory/_kill_prospect.py`

Depende de: `SPK - SPEKGEN AGENCY/_CONTENT_HUB_SHOPIFY/shopify_client.py` y openpyxl.
