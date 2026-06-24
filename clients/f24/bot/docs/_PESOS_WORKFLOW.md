# F24 — Manejo de pesos por producto (para envíos)

El motor de guía (`f24-generate-guide`) necesita el peso de cada producto para cotizar y
generar la guía correcta. Shopify trae pesos a veces mal importados (ej. navajas en "5kg").
Este es el flujo para tenerlos correctos, sin maratón de datos.

## Fuente de verdad: el Sheet INVENTARIO F24

- Hoja `📦 STOCK Y PROMOS`, columna **R "Peso real (kg)"**.
- Estado del seed inicial (15-jun-2026):
  - **102** SKUs pre-llenados (pesos plausibles, tomados de Shopify).
  - **117** SKUs **en blanco** = los pesos sospechosos/basura → **el equipo los corrige aquí**.
  - 50 SKUs sin match en Shopify (aún sin PDP).

## Cómo el equipo lo mantiene

1. En la hoja, llenar/corregir la columna **R "Peso real (kg)"** del SKU (en kilos, ej. `0.2`, `25`, `85`).
2. Prioridad: **solo los SKUs que se venden** (no hace falta los 219 de golpe). Conforme caen pedidos, corregir el peso del que se vendió.
3. Correr el sync para empujar a Shopify:

   ```
   cd "F24- FERRE24/F24 - 08. WHATSAPP/bot_multimodal"
   /usr/bin/python3 sync_f24_weights.py            # preview (dry-run)
   /usr/bin/python3 sync_f24_weights.py --apply     # aplica a Shopify
   ```

   Solo toca los SKUs con peso lleno y distinto del de Shopify. Las filas vacías se ignoran.

## Red de seguridad (ya activa, aunque no se llene nada)

El motor de guía NO confía ciegamente en Shopify:
- Si un peso es absurdo para su categoría (navaja en 5kg), lo **descarta solo** y usa el peso
  típico del perfil de categoría.
- Las **dimensiones** las pone el motor por perfil de categoría (Shopify no guarda dimensiones).
- Pedidos > 70 kg se marcan `needs_review` (flete pesado) para que Sergio los revise.

O sea: aunque no se corrija nada, ningún pedido sale con peso disparatado. La columna R solo
**afina** la exactitud del costo de los productos que importan.

## Pendiente opcional (automatización)

Hoy el sync se corre on-demand. Se puede enganchar al cron diario que ya corre el sync de
promos (GH Actions) para que se empuje solo. Bajo esfuerzo; pedírselo a Claude cuando se quiera.
