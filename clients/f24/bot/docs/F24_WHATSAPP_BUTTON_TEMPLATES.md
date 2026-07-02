# Ferre24 — Plantillas WhatsApp con botones Quick Reply

> Patrón replicado del validado en SSICMA (2026-07-01): plantilla business-initiated con **3 botones
> Quick Reply** (máximo que WhatsApp muestra tappables; >3 se colapsa en lista = fricción). Un tap
> **reabre la ventana de 24h** → a partir de ahí el bot atiende y cierra **gratis, sin plantillas**.

## Por qué botones (backed by data)
1. Botones interactivos suben el response rate vs texto plano.
2. Un tap abre la ventana de 24h → todo el follow-up del bot queda gratis.
3. Los 3 botones mapean a **intención por etapa de compra** y a **sistemas reales de F24** (nada de
   "ver redes" = fuga).
4. Self-serve / cotización instantánea = la conversión más alta y descarga al humano.

## Regla de compliance (CRÍTICA)
- **Un solo tipo de botón por plantilla.** 3 Quick Reply. NUNCA mezclar Quick Reply + URL en la
  misma plantilla (Meta la rechaza — era el bug latente de las d3/d8 actuales).
- Categoría: **Marketing** para re-engagement (d3/d8/d18); **Utility** para primer contacto
  transaccional. es_MX. `{{1}}` = `{{contact.first_name}}` con fallback "qué tal" (ya trae nombre
  real gracias a `save_name`).
- Botón texto ≤ 25 caracteres.

## Los 3 botones (mismos en todas las plantillas F24)

| Botón (label) | Payload que envía el tap | Ruta en el bot |
|---|---|---|
| `💰 Quiero cotizar` | **Quiero cotizar** | Bot pide producto + CP → cotiza → cierra con link de pago (self-serve, conversión más alta) |
| `📞 Que me llamen` | **Quiero que me llamen** | R32 callback: el bot pregunta el horario → escala "LLAMADA SOLICITADA" → email a Sergio/Edgar |
| `🔧 Sí, retomemos` | **Hola, quiero retomar** | Reabre ventana 24h; el bot retoma con el contexto del equipo que vio |

En el **body** siempre cerrar con: *"…o escríbeme tu duda 👇"* → el bot lee texto libre y cubre todo
lo demás. **F24 no necesita workflow de ruteo por botón**: el payload es texto que el bot interpreta
y rutea solo (a diferencia de SSICMA, que sí arma workflow por botón).

---

## Plantilla 1 — Primer contacto (lead nuevo · Utility)
_Nombre GHL sugerido: `f24_primer_contacto_botones`_

**Body:**
```
Hola {{1}} 👋 Aquí Ferre24. Manejamos generadores, motobombas, motosierras, compresores y más
para campo, obra y taller — con meses sin intereses y envío a todo México.

¿Cómo te ayudo? Elige abajo o escríbeme tu duda 👇
```
**Botones:** `💰 Quiero cotizar` · `📞 Que me llamen` · `🔧 Ver equipo`
_(Header imagen opcional: collage de equipo en uso.)_

---

## Plantilla 2 — Re-engagement Día 3 (Marketing) — reemplaza `f24_reengagement_d3`
**Body:**
```
Hola {{1}} 👋 Quedaste viendo equipo con nosotros en Ferre24 y quería saber si sigues
buscándolo. Te paso precio y opciones sin compromiso.

¿Le seguimos? Elige abajo o escríbeme tu duda 👇
```
**Botones:** `💰 Quiero cotizar` · `📞 Que me llamen` · `🔧 Sí, retomemos`
_(Header imagen: contratista/taller usando herramienta — cálida.)_

---

## Plantilla 3 — Re-engagement Día 8 (Marketing) — reemplaza `f24_reengagement_d8`
_El d8 actual (2.1% reply) es el peor: era puro folleto. Aquí, humano + botones._

**Body:**
```
Hola {{1}} 👋 No quiero dejarte con la duda: ¿al final encontraste el equipo que buscabas, o
te echo una mano para elegirlo? Aquí seguimos con precio real y meses sin intereses.

Dime abajo o escríbeme 👇
```
**Botones:** `💰 Quiero cotizar` · `📞 Que me llamen` · `🔧 Tengo una duda`
_(Header imagen: 3 íconos "12 MSI · Garantía · Envío" o producto en uso.)_

---

## Plantilla 4 — Re-engagement Día 18 (Marketing) — reemplaza `f24_reengagement_d18`
**Body:**
```
Hola {{1}}, pasó un rato desde que platicamos en Ferre24. Si todavía traes pendiente lo del
equipo, aquí sigo para ayudarte a cerrarlo cuando gustes.

¿Lo vemos? Elige abajo o escríbeme 👇
```
**Botones:** `💰 Quiero cotizar` · `📞 Que me llamen` · `🔧 Retomar`
_(Header imagen: minimalista, logo Ferre24 + "Aquí cuando lo necesites".)_

---

## Cómo se registran (acción de UI — la API no alcanza estas plantillas)
1. GHL → Settings → WhatsApp → Templates → New. Las plantillas viven en `phone-system/whatsapp`
   (solo UI/Workflow, no la API pública — ver [[project_f24_reengagement_live]]).
2. Categoría (Marketing / Utility), idioma es_MX, body con `{{1}}`, header Image (opcional), y los
   **3 botones Quick Reply** con los payloads exactos de la tabla.
3. Enviar a aprobación de Meta (minutos–24h). Si rechaza: casi siempre es botón mixto — verificar que
   los 3 sean Quick Reply.
4. El **relay de GHL** (tag `f24-send-dN` → Send WhatsApp Template) y el cron de Make 5278490 no
   cambian: solo apuntan a las nuevas plantillas por nombre.

## Ruteo de los taps (bot-native, sin workflow extra)
- `Quiero cotizar` → el bot ya sabe cotizar (pide producto + CP, arma create_order).
- `Quiero que me llamen` → **R32 callback** (prompt v2.7): el bot pregunta horario → escala
  "LLAMADA SOLICITADA". NO cae en R31 (handoff ciego).
- `Hola, quiero retomar` → el bot retoma con contexto (ya era el payload del d3 viejo).

## Pendiente al registrar
Agregar las firmas de las nuevas plantillas a `metrics/f24_followup_metrics.py` (`SIGNATURES`) para
que el monitor trackee el A/B (control texto plano vs retador con botones) por reply rate.
