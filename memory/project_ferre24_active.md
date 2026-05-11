---
name: Ferre24 cliente activo SPEKGEN — opción C $32K + $10.5K/mes (post-merge 2026-05-07)
description: Quinto cliente activo SPEKGEN. Setup $32K (anticipo $8.5K cobrado, saldo $23.5K go-live). Retainer $10.5K/mes desde mes 2. Marca Duarte invisible al frente. Dominio ferre24.com.mx. Implementación 3-4 sem desde 7-may. P-9001 (mutado, no nuevo ID)
type: project
originSessionId: 88f8c182-ddb4-4757-af13-c37e8cabe475
---
# Ferre24 — Estado activo post-merge (2026-05-07)

> **Mutación 2026-05-07:** cliente nació como Ferreterías Duarte fork 1 (P-9001 cerrado 2026-05-06, $17K). El día siguiente Sergio pidió pasar a Ferre24 opción C ($32K). Detalle del cierre original + lecciones del merge en `project_first_win_duarte.md` y en `F24- FERRE24/_KNOWLEDGE_BASE.md`.

## Identidad

- **Marca pública:** Ferre24 (Duarte invisible al frente)
- **Razón social / sourcing:** Ferreterías Duarte (Tinguindín, Michoacán)
- **Owner / contacto:** Sergio Duarte — `332 550 0287`
- **Pipeline ID:** P-9001 (conservado, mutado de fork 1 a fork 2)
- **Folder:** `F24- FERRE24/` (root del Drive, renombrado de `FD- FERRETERIAS DUARTE/`)
- **Dominio:** ferre24.com.mx (comprado por SPEKGEN, incluido en setup)

## Deal económico

- **Setup:** $32,000 MXN one-time (opción C — E-commerce comprable + Biblioteca editorial)
- **Anticipo:** $8,500 MXN (depositado 2026-05-05 al fork 1, reasignado al setup C)
- **Saldo al go-live:** $23,500 MXN
- **Retainer:** $10,500 MXN/mes desde mes 2 (incluye rotación trimestral de los 4 catálogos editoriales)
- **Año 1 piso:** $32K + 11 × $10.5K = **$147,500 MXN**
- **Hosting:** Sergio paga directo a Shopify (~$580 MXN/mes Basic)

## Scope contratado (setup $32K)

- Plataforma Shopify Ferre24 + tema custom
- Branding nuevo Ferre24 (logo + paleta + identidad — mockup base existe pero no es definitivo)
- 200 SKUs comprables llave en mano (distribución TBD por Sergio ~lunes 12-may)
- 4 catálogos editoriales propios marca Ferre24 (categorías propuesta: Eléctrico/Plomería/Pro Construcción/Industrial)
- Flipbook viewer custom para catálogos editoriales
- Bot multimodal WhatsApp (texto + audio + imagen, auto-pause)
- Automation pedidos (carrito abandonado + Skydropx + ticket system)
- Tracking GA4 + Pixel + CAPI + Microsoft Clarity
- Catálogo PDF auto-generado (sweetener)
- Dominio ferre24.com.mx

## Retainer mensual ($10,500 desde mes 2)

- Bot WhatsApp 24/7 mantenimiento
- Hasta 20 SKUs nuevos/mes multi-proveedor
- Rotación trimestral de los 4 catálogos editoriales
- 8h cambios menores en sitio/mes
- Reporte mensual + soporte
- Bloques adicionales SKUs: $1,500 / 50 SKUs (multi-proveedor +50% vs single-source)

## Timeline

- **Implementación:** 3-4 semanas desde 2026-05-07
- **Go-live target:** ~28-may a 4-jun 2026
- Si Sergio no entrega los 3 inputs bloqueantes (distribución SKUs + categorías editoriales + recursos branding) antes de ~lunes 12-may, el timeline se mueve.

## Pendientes bloqueantes (Sergio)

- Confirmar distribución 200 SKUs (Duarte single-source vs Ferre24 multi-proveedor MC/Truper/VDE)
- Confirmar 4 categorías catálogos editoriales
- Entregar recursos branding (preferencias + feedback mockup)
- Firmar Addendum REV.B (delta +$15K setup, +$3K/mes retainer)

## Pendientes operativos (SPEKGEN)

- Generar Addendum REV.B y mandar a firma
- Definir stack del bot multimodal (Cloud API + Edge Function recomendado)
- Construir skill `/ferre24-product-pipeline` (research multi-proveedor + 3 imgs + upload)
- Decidir despublicación URLs `/duarte*mockup` en spekgen.com una vez Ferre24 esté live
- Rotar Client Secret de la app `SPEKGEN FD Admin` (se expuso en chat durante el setup)

## Infra Shopify (LIVE 2026-05-07 PM)

- **Store:** `0mtky1-q6.myshopify.com` (Plan Basic, MXN, América/Mazatlán)
- **Dominio primario:** `ferre24.com.mx` (ya conectado, verificado en `shop.json`)
- **Theme:** Horizon — id `150711664728` (role=main)
- **Custom App:** `SPEKGEN FD Admin` con 104 scopes (Admin + Storefront full). Auth Client Credentials OAuth (mismo patrón que HC + LF).
- **`.env`:** `F24- FERRE24/.env` — `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_SHOP`, `SHOPIFY_THEME_ID`, `SHOPIFY_API_VERSION=2024-10`, `SHOPIFY_PRIMARY_DOMAIN`
- **Test runner:** `F24- FERRE24/F24 - 04. WEBSITE/f24_shopify_test_connection.py` — valida 5 endpoints + reporta scopes. 5/5 OK el 2026-05-07.
- **Estado:** tienda vacía (0 productos, 1 location genérica, 1 page Contact, shop.name="My Store" placeholder). Lista para arrancar build cuando Sergio confirme branding + 200 SKUs.

## Banderas

- **Branding mutó de "tema custom Duarte ya en mockup" → "branding nuevo Ferre24 desde cero".** Recalibrar fecha de go-live si la sesión de revisión con Sergio pide cambios mayores.
- **Catálogo es multi-fuente.** Cada SKU 50% más complejo (extracción 3 PDFs proveedor + decisión + normalización). El retainer mensual incluye 20 SKUs/mes (vs 30 del fork 1) — recordárselo a Sergio en mes 2.
- **Mantenimiento "es problema para mes 2"** — pero hay que meterlo en el ticket del 50% restante como nota explícita ($10,500/mes) para evitar sorpresa cuando llegue la 1ra factura.
