# F24 — Workflow de reactivación por promo (spec para armar en GHL)

Lo que falta para que la reactivación por promo pueda MANDAR. La skill
`f24-promo-reactivation` ya arma la lista y (con `--confirm`) pone el tag; esta
WF es la que convierte ese tag en un WhatsApp. **Nada de esto manda hasta que
Pedro lo arme y lo active en GHL.**

## 0. Por qué hace falta un template aprobado (no es opcional)

Los leads a reactivar llevan 15–40 días sin escribir → están FUERA de la ventana
de 24h de WhatsApp. Meta solo deja escribir fuera de esa ventana con un
**Message Template (HSM) aprobado**. No se puede mandar texto libre. F24 ya hace
esto para los follow-ups D3/D8/D18, así que el proceso es conocido; solo falta
crear y aprobar el template de promo (aprobación de Meta: ~1–2 días).

## 1. Custom fields (YA creados, 2026-07-22)

La skill los llena por contacto al poner el tag. El template los interpola.

| Campo | ID | Ejemplo |
|---|---|---|
| Promo - Producto | `auacJ9xx8LJlEE1N4kHg` | Generador Parazzini GP3000M |
| Promo - Descuento | `XLACyGso7RK5RVL4PbPk` | 10% |
| Promo - Precio | `x3jV2aiI2JItGRucKvY3` | $4,545 |
| Promo - Vigencia | `RVi3Vg006IHgN48pHxue` | 2026-07-31 |

## 2. Template de WhatsApp a crear + mandar a aprobar (borrador)

Nombre sugerido: `f24_promo_reactivacion`. Categoría: MARKETING.

> Hola {{1}} 👋 En Ferre24 vimos que te interesó el *{{2}}*.
> ¡Buenas noticias! Ahora tiene *{{3}} de descuento* — queda en {{4}}, válido
> hasta el {{5}}. ¿Te lo apartamos? Responde por aquí y un asesor te ayuda. 🔧
>
> _Responde BAJA si no quieres volver a recibir promociones._

Variables → campos:
`{{1}}` first_name · `{{2}}` Promo - Producto · `{{3}}` Promo - Descuento ·
`{{4}}` Promo - Precio · `{{5}}` Promo - Vigencia.

La línea de BAJA es obligatoria (opt-out) y alimenta el paso 4.

## 3. Workflow de GHL

- **Trigger**: Contact Tag Added = `promo-reactivar`.
- **Filtros de seguridad** (defensa en profundidad, aunque la skill ya excluye):
  NO tiene tag `bot-pausado`, NO tiene `no-promo`, NO tiene `no-insistir`.
- **Acción 1**: enviar el template `f24_promo_reactivacion` por WhatsApp con los
  5 campos mapeados.
- **Acción 2**: quitar el tag `promo-reactivar` y poner `promo-enviado-{{date}}`
  (para no re-mandar y para medir).
- **Ventana de envío**: horario hábil MX (ej. 9am–7pm), throttle si GHL lo
  permite, para no disparar cientos de golpe.

## 4. Opt-out entrante (STOP)

Segundo WF: **Trigger** Customer Replied, **Filtro** mensaje contiene
"baja"/"no me interesa"/"no insistan" → **Acción** poner tag `no-promo` (lo
excluye de aquí en adelante, tanto en la skill como en este WF). Esta es la
lección del lead que pidió "no me insistan" — sin esto, reincidimos.

## 5. Orden para prenderlo (cuando Pedro decida)

1. Crear el template y mandarlo a aprobar con Meta.
2. Armar los dos WF (envío + opt-out), DESACTIVADOS.
3. Correr la skill en modo lista y revisar los candidatos.
4. `--tag --confirm` sobre un GRUPO CHICO de prueba (2–3 contactos internos).
5. Activar el WF, verificar que llega bien 1 mensaje de prueba.
6. Recién ahí, correr `--confirm` sobre la lista real, con OK de Pedro.

## Estado

- Captura de producto de interés + backfill + matcher + log + tagging: ✅ hecho.
- Custom fields: ✅ creados.
- Template Meta + los 2 WF de GHL: ⛔ pendiente (esto). Es lo único que falta
  para poder mandar — y es a propósito el paso que queda en manos de Pedro.
