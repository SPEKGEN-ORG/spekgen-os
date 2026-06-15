# F24 — Automatización de la Landing de Promociones

> Construido 2026-06-13. Hermano de `sync_f24_promos.py` (precios) y
> `sync_f24_inventory.py` (stock). Este resuelve la **landing** `/pages/promociones`.

## Qué se construyó

| Archivo | Qué hace |
|---|---|
| `sync_f24_landing.py` | Reconcilia la colección Shopify `promociones-vigentes` contra la pestaña `🔥 PROMO ACTIVA` del Sheet + actualiza el contador `end_iso` del template (copia del repo). Idempotente. `--apply` gateado; dry-run por defecto. |
| `theme/f24-promo-grid.liquid` | Grid **plano** refactorizado: renderiza toda la colección directo, sin los 7 grupos hardcodeados ni tags `promo-grupo-*`. Mismo diseño de tarjeta. |
| `theme/page.landing-promociones.json` | Copia versionada del template (countdown `end_iso` en 4 secciones). El script trabaja sobre esta copia; **no se sube al tema**. |

## Cómo corre

```bash
# dry-run (preview, read-only — no toca Shopify ni el template)
/usr/bin/python3 sync_f24_landing.py

# aplica: reconcilia collects de la colección + escribe el template del repo
/usr/bin/python3 sync_f24_landing.py --apply
```

En **cloud (GitHub Actions)** las credenciales Shopify llegan por env (secrets) y el SA
de Sheets por `GOOGLE_SA_PATH`, igual que los otros `sync_*`. Localmente, el script hace
best-effort de cargar el `.env` de F24 desde el árbol de Drive (función
`_bootstrap_local_env`) — no tiene efecto en cloud.

## Lo que reconcilia (la pieza clave: la baja de tarjeta)

`sync_f24_landing.py` calcula tres conjuntos sobre la colección `promociones-vigentes`:

- **AGREGAR** = SKUs vigentes (en `🔥 PROMO ACTIVA`, `hoy <= Vigencia fin`) que resuelven
  a un producto en Shopify y aún **no** están en la colección.
- **QUITAR** = productos que **sí** están en la colección pero **ya no** están vigentes.
  → Esto es lo que **da de baja la tarjeta** cuando una promo expira. Diff por
  `product_id`, borra el `collect` correspondiente.
- **SIN CAMBIO** = los que ya están bien (idempotente, no re-escribe).

SKUs que no resuelven en Shopify se **reportan y se omiten** (no truena la corrida).

El **contador** se pone a la **vigencia MÁXIMA** de las promos activas, en formato
`YYYY-MM-DDT23:59:59-06:00`, en las secciones `promobar, hero, promogrid, final`.

## Helpers portados (de `swap_promo_cycle.py`, ahora self-contained)

- `resolve_product_id_by_sku` — adaptado para recibir `sc` (módulo shopify_client) y usar
  `sc.graphql`. Filtra match exacto de SKU (case-insensitive).
- `ensure_collection` / `find_collection_by_handle` — REST `custom_collections.json`.
  En dry-run, si la colección no existe, devuelve `None` (no la crea).
- `list_collects` — devuelve `product_id -> collect_id` para hacer el diff.
- `update_template_dates` — adaptado para escribir **solo la copia del repo**
  (`theme/page.landing-promociones.json`) y **no** subir al tema.
- Parsers `parse_money` / `parse_vig` / `parse_msi_ladder` y `find_sa` / `read_promo_active`
  copiados tal cual de `sync_f24_promos.py` (mismo patrón de lectura del Sheet).

**Diferencia con el flujo viejo (`seed_promo_landing.py` + grid agrupado):** ese tageaba
cada producto con `promo-grupo-{slug}` y el liquid iteraba 7 grupos hardcodeados. El nuevo
elimina los tags y los grupos — la colección es la única fuente, el grid es plano.

## IDs y handles exactos

| Cosa | Valor |
|---|---|
| Sheet INVENTARIO F24 | `1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U` · pestaña `🔥 PROMO ACTIVA` |
| Colección | handle `promociones-vigentes` · id `312670715992` (custom collection) |
| Página | handle `promociones` → `/pages/promociones` · template suffix `landing-promociones` |
| Shop | `0mtky1-q6.myshopify.com` (ferre24.com.mx) |
| Theme ID F24 | en `.env` como `SHOPIFY_THEME_ID` (no se transcribe aquí; el script lo lee de `sc.THEME_ID`). El upload del grid/template lo hace el operador con ese theme id. |
| Sección liquid (key en tema) | `sections/f24-promo-grid.liquid` |
| Template (key en tema) | `templates/page.landing-promociones.json` |

## Resultado del dry-run (2026-06-13, read-only)

```
Filas en PROMO ACTIVA: 49 | vigentes: 49 | expiradas: 0
vigentes resueltos en Shopify: 45 | ya en colección: 35
AGREGAR (10): GPDS8.5M, PK-EASY-600US, ENERWELL-G1000, ENERWELL-G2500,
              PK-EASY-100CT, PK-EASY-200US, KAS-12P-TF, KAS-10P, KASPRO-16P, LMH-1000W
QUITAR (0)   ← (todas vigentes ahora mismo; la lógica de baja está lista)
OMITIDOS (4 sin PDP): MINI60-12/1127, PK-EASY-400US, PK-EASY-600N-US, PK-EASY-800US
CONTADOR: 2026-06-14 -> 2026-06-30 (vigencia máx) en promobar, hero, promogrid, final
```

El template del repo quedó intacto (`end_iso` sigue en `2026-06-14`). No se tocó Shopify,
no se subió nada al tema, no hubo git.

## Riesgos / incertidumbres (LEER antes de subir al tema)

1. **El refactor del liquid SÍ cambia la landing en vivo al subirlo.** El grid plano
   elimina los **encabezados de grupo** ("Generadores", "Motosierras", etc.) y el conteo
   por grupo. Visualmente: pasa de secciones agrupadas a una sola grilla continua. El
   diseño de cada **tarjeta** es idéntico (imagen, precio, tachado, MSI, botones Ver/WA),
   pero la estructura de la página cambia. Confirmar con Gibran/Sergio que se quiere el
   grid plano antes de subir `f24-promo-grid.liquid` al tema.

2. **`LMH-1000W` y `GPDS8.5M` ahora entran.** El `seed_promo_landing.py` viejo los excluía
   a mano (LMH-1000W estaba DRAFT sin precio; GPDS8.5M sin imagen). El nuevo script los
   agrega si están vigentes en el Sheet **y** resuelven en Shopify. Hoy ambos resuelven →
   entrarían a la colección. Si su PDP sigue incompleta (sin imagen / DRAFT), la tarjeta
   se verá pobre. **Acción sugerida:** o se completan sus PDPs, o se les quita la vigencia
   en el Sheet, o se añade una lista de exclusión al script. No lo hardcodeé para no
   reintroducir la lógica que se pidió eliminar — decisión de Gibran.

3. **El grid usa `product.featured_image` y `compare_at_price`.** Productos sin imagen caen
   al `placeholder_svg_tag`; sin `compare_at_price` no muestran tachado ni `-%`. Es
   tolerante, pero verificar que los 45 vigentes tengan imagen + compare_at correctos
   (eso lo setea `sync_f24_promos.py` al sincronizar precios — correr ese **primero**).

4. **Orden de operaciones recomendado al ir a producción:**
   `sync_f24_promos.py --apply` (precios + compare_at + tag msi-912) → `sync_f24_landing.py --apply`
   (colección + contador) → operador sube `f24-promo-grid.liquid` y
   `page.landing-promociones.json` al tema F24 → verificar `/pages/promociones`.

5. **Reconciliación de collects sin paginación >250.** `list_collects` no pagina por Link
   header (igual que `swap_promo_cycle.py`). La colección de promos no debería pasar de 250
   ítems, pero si algún día crece, hay que paginar.

6. **El contador toma la vigencia MÁXIMA.** Si conviven promos con fechas distintas, el
   chip "Termina en" muestra la más lejana. Es lo pedido, pero ojo: una promo que vence
   antes seguirá mostrando el countdown global hasta que `sync_f24_landing.py` la saque de
   la colección (en su próxima corrida tras expirar). El cron 2×/día acota ese desfase a
   ~12 h máx.
