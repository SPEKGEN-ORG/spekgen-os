# Ferre24 — Secuencia de Re-engagement WhatsApp

> **STATUS 2026-06-16 (activación):** Plantillas **APROBADAS** por Meta. IDs reales (Meta template id,
> obtenidos del backend GHL `phone-system/whatsapp/location/{loc}/template`):
> - `plantilla_meta_f24_reengagement_d3`  → **857068617015027** (categoría Utility, es_MX, POSITIONAL {{1}})
> - `plantilla_meta_f24_reengagement_d8`  → **1656192009844928** (Marketing)
> - `plantilla_meta_f24_reengagement_d18` → **2782252138818935** (Marketing)
>
> **HALLAZGO CRÍTICO (probado 16-jun):** la **API pública de GHL NO puede enviar estas plantillas**.
> `POST services.leadconnectorhq.com/conversations/messages` acepta el campo `templateId` PERO resuelve
> contra otro store → el ID de Meta da `Template ... not found`; `templateName` se ignora. Estas plantillas
> viven en `phone-system/whatsapp` que solo alcanza el UI/Workflow de GHL (token de sesión, no la API key).
> → **El envío DEBE salir de un Workflow de GHL.** Arquitectura elegida (B-lite): Make = cerebro (timing,
> goteo ~15/día, ladder una-etapa-a-la-vez d3→+5d→d8→+10d→d18, dormidos incl. no-chat, reactivación),
> y cuando un contacto toca etapa N, Make solo pone tag `f24-send-d3|d8|d18`. En GHL: workflow relay
> "tag → Send WhatsApp Template → quita el tag". El builder GHL no es automatizable por navegador de
> forma confiable (accesibilidad desincronizada) → el relay se arma a mano (guía corta) o en sesión estable.
>
> **STATUS 2026-06-15:** Las 3 plantillas Meta YA fueron creadas en GHL por Gibran, **pendientes
> de aprobación Meta**. Nombres EXACTOS registrados (lowercase, sin comillas):
> - `plantilla_meta_f24_reengagement_d3` (T1 · Día 3) — imagen: collage "TRABAJO DE VERDAD" (UMBRELLA-D)
> - `plantilla_meta_f24_reengagement_d8` (T2 · Día 8) — imagen: "+30 EQUIPOS" (UMBRELLA-A iconográfico)
> - `plantilla_meta_f24_reengagement_d18` (T3 · Día 18) — imagen: Ferre Bot "AQUÍ SIGO, A TUS ÓRDENES"
>
> **Cambio de secuencia:** Gibran **eliminó la Etapa 1 (15 min)**. La fase libre ahora arranca en
> la Etapa 2 (2h). Ajustar el blueprint en consecuencia.
> **Pendiente al aprobarse:** cablear nombres en `build_f24_followup_blueprint.py` (dispatch módulo 4)
> + reimport Make 5278490 → luego enviar a contactos dormidos.
> **Flag compliance:** si Meta rechaza d3/d8, lo más probable es **botones mixtos** (quick reply + URL
> en la misma plantilla, no permitido). Fix: dejar un solo tipo de botón por plantilla.
> Fuente de prompts de imagen: `../IMAGENES_TEMPLATES/_PROMPTS_WA_TEMPLATES_F24.md`. Vista maestra:
> `../F24_SECUENCIA_REENGAGEMENT.xlsx`.

Secuencia completa de 6 etapas. Las etapas 1-3 son texto libre (dentro de la ventana de 24h
de Meta). Las etapas 4-6 son plantillas pre-aprobadas (categoría Marketing — obligatorio).

## Reglas de compliance (verificadas con research 2026-06)

- **Categoría plantillas:** siempre **Marketing**. Nunca Utility para re-engagement (Meta reclasifica
  masivamente y sin aviso desde abril 2025 — riesgo de cuenta).
- **Máximo 3 plantillas** (etapas 4-6) en la secuencia. Más mensajes sin respuesta = opt-out masivo.
- **No abrir con descuento** en los primeros mensajes — content-first mantiene 94-97% retención.
- Desde oct 2025: calidad baja de plantilla ya **no baja el tier de envíos**, solo bloquea upgrades.
- **Rotación (etapas 1-3):** `nudge_roll = floor(random() * 3)` en SetVariables → variante 0, 1 o 2.
  Se computa una sola vez por ejecución para garantizar consistencia.

---

## FASE LIBRE (etapas 1-3 — texto directo, sin aprobación Meta)

_Las 3 etapas tienen 3 variantes cada una. El bot rota aleatoriamente entre ellas para no
sentirse repetitivo si el mismo cliente abre otra conversación._

### Etapa 1 — 15 min sin actividad
_Angle: "Estoy aquí, sin presión". Sin imagen._

**Variante A:**
```
¡Aquí sigo! 🔧 ¿Quieres que te ayude a elegir el equipo correcto o te paso precios? Solo dime.
```
**Variante B:**
```
¿Estás buscando algo en específico? Dime qué necesitas y te doy opciones y precio de volada. 🔧
```
**Variante C:**
```
Sigo aquí si tienes dudas — nada más dime qué necesitas y te oriento. ¿Le seguimos? 🛠️
```

---

### Etapa 2 — 2 horas sin actividad
_Angle: "¿Te quedó alguna duda?". Sin imagen._

**Variante A:**
```
¿Te quedó alguna duda sobre specs, meses sin intereses o tiempos de entrega? Puedo asesorarte sin compromiso — solo pregunta.
```
**Variante B:**
```
¿Sigues por ahí? A veces la decisión no es fácil cuando hay varias opciones. Si quieres te ayudo a comparar o te paso el precio exacto del equipo que viste.
```
**Variante C:**
```
Por si te lo preguntas: tenemos meses sin intereses en varios equipos. Si el precio es lo que te frena, puedo mostrarte cómo queda con el plan que más te convenga. ¿Le buscamos?
```

---

### Etapa 3 — ~22.5 horas sin actividad (último antes de cerrar ventana)
_Angle: "Quedamos a medias". Sin referencia a fin de día ni al horario. Puede incluir imagen si se desea._

**Variante A:**
```
Hola, vi que quedamos a media conversación. ¿Sigues buscando equipo? Dime qué necesitas y le seguimos. 🔧
```
**Variante B:**
```
¿Sigues por ahí? Quedamos a medias con tu cotización — si tienes dudas o quieres retomar, aquí ando.
```
**Variante C:**
```
Hola, veo que nos quedamos sin cerrar tu consulta. ¿Aún necesitas equipo o maquinaria? Con gusto te ayudo a cotizar. 🛠️
```

---

## PLANTILLAS POST-24H (etapas 4-6 — requieren aprobación Meta)

Registrar en **GHL → Settings → WhatsApp → Templates**:
- **Categoría:** Marketing
- **Idioma:** Spanish (MX) — `es_MX`
- **Variable `{{1}}`** = nombre del cliente → mapear a `{{contact.first_name}}` con fallback "qué tal"
- **Header:** Image (ver briefs de imagen abajo)
- **1 sola plantilla por etapa** (sin rotación — cada plantilla requiere aprobación Meta individual)

---

### T1 · Día 3 (etapa 4) — `f24_reengagement_d3` ✓ CONFIRMADA

_Angle: "Quedó pendiente" — directo, sin drama, bajo compromiso._
_Imagen: lifestyle — contratista/taller usando herramienta, cálida, no catálogo._

**Copy final:**
```
Hola {{1}} 👋

Quedó pendiente tu consulta con Ferre24. Si necesitas equipo para tu trabajo, puedo asesorarte y pasarte precio de inmediato.

¿Retomamos?
```

**Botones:**
- [Sí, retomemos] → Quick reply: "Hola, quiero retomar"
- [Ver catálogo] → URL: ferre24.com.mx/collections/all

---

### T2 · Día 8 (etapa 5) — `f24_reengagement_d8`

_Angle: Valor — entregar info útil antes de pedir. Atacar las 3 objeciones más comunes
(precio/MSI, garantía, logística)._
_Imagen: infográfico branded — 3 bullets: "12 MSI", "Garantía incluida", "Entrega GDL/Mich"._

**Copy:**
```
Hola {{1}} 👋

Por si no lo viste cuando platicamos: en Ferre24 tienes hasta 12 meses sin intereses en equipo selecto, garantía de marca incluida, y entrega rápida a Guadalajara y Michoacán.

¿Hay algo concreto en lo que te pueda ayudar a decidir?
```

**Botones:**
- [Quiero asesoría] → Quick reply: "Sí, quiero que me asesoren"
- [Ver promociones] → URL: ferre24.com.mx (o landing MSI cuando esté lista)

---

### T3 · Día 18 (etapa 6) — `f24_reengagement_d18` ✓ CONFIRMADA

_Angle: Puerta abierta — "ha pasado un tiempo". Sin breakup, sin "último mensaje",
sin urgencia. La puerta queda abierta, el cliente escribe cuando esté listo._
_Imagen: minimalista — logo Ferre24 + "Aquí cuando lo necesites". Fondo oscuro. Sin producto._

**Copy final:**
```
Hola, ha pasado un tiempo desde tu última consulta con Ferre24.

Seguimos disponibles para ayudarte a encontrar el equipo que necesitas, con garantía de marca y entrega express.

Escríbenos cuando estés listo 🔧
```

**Botones:**
- [Escribir ahora] → Quick reply: "Hola, quiero información"

_(Después del T3 sin respuesta: tag `reengagement_exhausted` en GHL. No más mensajes por 30 días.)_

---

## Briefs de imagen para las plantillas

### Imagen T1 (f24_reengagement_d3)
- **Tipo:** Foto lifestyle (puede ser stock de alta calidad)
- **Escena:** Contratista o técnico usando herramienta o maquinaria en obra/taller, iluminación cálida
- **Mood:** Real, no estudio, profesional pero accesible
- **Proporción:** 1:1 o 16:9 (WhatsApp comprime — preferir JPG < 2MB)
- **Branding:** Logo Ferre24 pequeño en esquina inferior derecha (opcional)
- **Prompt Gemini (base):**
  ```
  Editorial lifestyle photo. Mexican male contractor in his 40s using a powerful chainsaw or
  water pump in an outdoor workshop setting. Golden afternoon light. Work clothes, safety goggles.
  Tool in foreground, sharp focus. Background slightly blurred. Professional but authentic,
  not stock-photo generic. Warm orange and brown tones. Horizontal format.
  ```

### Imagen T2 (f24_reengagement_d8)
- **Tipo:** Infográfico branded (generar en Canva o con factory-batch)
- **Contenido:** 3 secciones con íconos + texto:
  - 📅 "Hasta 12 MSI en equipo selecto"
  - 🛡️ "Garantía de marca incluida"
  - 🚚 "Entrega rápida GDL y Michoacán"
- **Paleta:** colores Ferre24 (carbón #2A2A2A + naranja de marca)
- **Fondo:** oscuro, texto claro, legible en móvil
- **Logo** Ferre24 en la parte inferior
- **Proporción:** 1:1 (funciona mejor en WhatsApp)

### Imagen T3 (f24_reengagement_d18)
- **Tipo:** Minimalista — solo tipografía + logo
- **Contenido:** Logo Ferre24 centrado + frase en tipografía limpia:
  _"Aquí cuando lo necesites."_
- **Fondo:** carbón oscuro (#1A1A1A) o azul marino profundo
- **Sin producto, sin texto adicional**
- **Proporción:** 1:1
- **Nota:** Este mensaje es de cierre suave — la imagen debe sentirse serena, no urgente

---

## Pasos para activar las plantillas (checklist)

- [ ] Crear las 3 plantillas en GHL Settings → WhatsApp → Templates
- [ ] Subir las imágenes correspondientes como header (Image)
- [ ] Esperar aprobación Meta (minutos a ~24h; si se rechaza, ajustar copy)
- [ ] Pasar los nombres/IDs exactos aprobados para cablearlos en el blueprint
- [ ] En `build_f24_followup_blueprint.py`: actualizar `FOLLOWUP_MAX_STAGE = 6`
- [ ] Agregar lógica de template dispatch en módulo 4 (ver TODO en el script)
- [ ] Rebuild + reimport en Make (scenario 5278490)
