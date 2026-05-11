---
name: Market A proxy con reviews+rating arrastra cadenas e infraestructura
description: Filtrar leads "tier A potencial" solo por reviews>=30 + rating>=4.0 sin Apify produce ~50% falsos positivos (cadenas nacionales, mercados públicos, fraccionamientos como entidad, marinas). Necesario blacklist de tipos/keywords cuando Apify no está disponible.
type: feedback
originSessionId: 0dc2b6ce-0382-4bc0-8a23-ac81a7a62d4d
---
Cuando el enrichment Apify (followers IG/FB) no está disponible y se intenta proxy de market_tier A solo con `reviews >= 30 + rating >= 4.0` en Google Places, los resultados arrastran:

1. **Cadenas nacionales con website corporativo** que no liga a la sucursal en GMaps (Chedraui Selecto, Tienda LEY, Soriana, Walmart, Oxxo, Costco, etc.)
2. **Mercados públicos / plazas** (Mercado Francisco I. Madero) — no son negocios individuales
3. **Fraccionamientos como entidad** (FRACC X, Residencial Y) — son los desarrollos en sí, no inmobiliarias
4. **Infraestructura marítima** (La Marina del Palmar, Marina Cantamar) — son las marinas, no charters
5. **Salones de eventos** clasificados como "renta de equipo" cuando se buscan "eventos"

**Why:** las reviews altas + rating alto son proxy de "negocio establecido y querido", pero NO discriminan tipo de entidad. Cadenas y infraestructura cumplen ambos criterios. El validation gate strict v2 (memory `project_market_tier_system.md`) usa followers IG/FB justamente para evitar esto, y depende de Apify.

**How to apply:** Cuando Apify esté caput y haya que armar prospect lists con Google Places solo:
- Mantener blacklist de keywords en `name`: `chedraui|ley|soriana|walmart|oxxo|costco|home depot|mercado|fracc\s|fraccionamiento|residencial|marina (?!charter|tour)|supermercado`
- Filtrar `types` que incluyan `supermarket|department_store|public_market`
- Para real_estate: requerir keyword `inmobiliaria|bienes raíces|broker|asesor` en el nombre, no aceptar nombres de fraccionamientos
- Para yates: requerir `charter|tour|sportfishing|yacht` en el nombre, no `marina` solo
- Validar 1×1 antes de marcar `outreachReady` (memory `feedback_prospects_validation_gates.md`)

Detectado 2026-04-25 corriendo `harvest_lapaz_market_a.py` para 5 cats en La Paz BCS: 19 leads recolectados, ~9 falsos positivos.
