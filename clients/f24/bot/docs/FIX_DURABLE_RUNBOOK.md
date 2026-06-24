# Fix durable — Inyección determinista de link por SKU (v2.1)

**Estado:** ARMADO y validado offline. PENDIENTE de deploy + smoke test en vivo.
**Por qué no se deployó automático:** toca el bot de ventas LIVE (scenario Make 5258612) y no se
puede simular un mensaje entrante para probarlo en caliente. Regla "no construir sin verificar".

## Qué hace

Elimina de raíz la alucinación de URLs (el bug del link 404 a DAK). En lugar de que el LLM escriba
la URL del producto (y a veces la reconstruya mal mezclando hermanos), el **sistema adjunta el link
OFICIAL** resuelto por SKU desde `F24_BOT_KNOWLEDGE/catalog_links.json`, vía un `switch()` Make
(match literal, dot-safe para SKUs como GPD8.5M) en el mapper del módulo de envío. Hasta 3 SKUs de
`products_mentioned`. SKU desconocido → no agrega nada (sin línea en blanco).

El mismo flag activa la **directiva de prompt**: "NO escribas URLs de producto; pon el SKU en
products_mentioned; el sistema adjunta el link". Así no hay links duplicados. Los **precios** los
sigue citando el LLM (verbatim del catálogo) — esos no se inyectan en v2.1.

## Implementación (ya hecha)

- `build_f24_bot_blueprint.py`: flag `SYSTEM_LINK_INJECTION` (env `F24_LINK_INJECTION=1`), default OFF.
  - `build_full_prompt()` añade la directiva cuando el flag está ON.
  - `_link_switch_cases()` / `_link_inject_suffix()` generan el `switch()` desde `catalog_links.json`.
  - `ghl_send_module_from_claude()` concatena el sufijo al `message` cuando el flag está ON.
- `F24_BOT_KNOWLEDGE/catalog_links.json`: mapa SKU/ID → {url, price, compare_at, title}. 216 keys.
  Regenerar junto con el catálogo (deriva de `catalog.json`).
- Candidato archivado: `_BLUEPRINTS/f24_bot_v2.1_candidate_link-injection_2026-06-11.json`.

Verificado offline: ENERWELL-G2500 → `...enerwell-4t-6-5hp` (el correcto, NO el 404). Comparativa
2 productos → 2 links correctos. SKU inexistente → sin línea.

## Deploy

```bash
cd ".../F24 - 08. WHATSAPP/bot_multimodal"
F24_LINK_INJECTION=1 /usr/bin/python3 build_f24_bot_blueprint.py   # build con flag ON
./deploy_f24_bot.sh dev v2.1                                       # scenario 5258612
# En la salida: isinvalid debe ser False. Si es True → NO quedó válido, rollback (abajo).
```

> Nota: el build sin `F24_LINK_INJECTION` regenera el blueprint v2.0 (sin inyección). El archivo
> `catalog_links.json` debe existir (regenerarlo si se actualiza el catálogo).

## Smoke test (OBLIGATORIO tras deploy)

Desde un WhatsApp de prueba (NO el de Gibran), al número del bot **523317903630**:

1. "Hola, quiero una planta de luz para mi casa" → el bot debe pedir potencia/uso (proving question).
2. "El ENERWELL 2500" → el bot debe cotizar y **el link adjunto debe ser**
   `ferre24.com.mx/products/generador-portatil-gasolina-2500w-enerwell-4t-6-5hp` (abre, no 404).
3. Pide comparar 2 generadores → deben llegar 2 links, ambos abren.
4. Verifica que el bot **no escribió** una URL en el texto Y que el link adjunto es correcto.

✅ Si los links abren y son correctos → v2.1 confirmado.
❌ Si llega sin link, link roto, o el bot tira error → rollback.

## Rollback (instantáneo)

Redeploy del blueprint v2.0 (prompt-only, ya probado):

```bash
/usr/bin/python3 build_f24_bot_blueprint.py     # flag OFF = v2.0
./deploy_f24_bot.sh dev v2.0
```

El bot vuelve a v2.0 (que ya tiene la regla anti-alucinación "copia verbatim / no mezcles hermanos"
en el prompt — sigue siendo seguro, solo sin la garantía de sistema).

## Notas / mejoras futuras

- v2.1 inyecta LINKS. Los **precios** siguen en manos del LLM (verbatim). Si reaparece un desfase de
  precio (como GPDS8.5T en el audit), el siguiente paso es inyectar también el precio por SKU
  (mismo patrón switch) — pero cambia el flujo conversacional (el precio va en prosa). Evaluar.
- El mapper del switch pesa ~71KB (×2 módulos de envío). Si Make rechaza por tamaño (isinvalid),
  alternativa: mover la resolución a un Data Store "F24 Catalog Links" + iterator, o a una Edge
  Function `f24-resolve-links`. Más módulos, más fragilidad — por eso se prefirió el switch inline.
