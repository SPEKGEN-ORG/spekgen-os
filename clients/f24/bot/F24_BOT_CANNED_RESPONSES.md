# Ferre24 Bot — Respuestas con Info Fija

Cada bloque es una "canned knowledge" que el bot usa cuando el cliente pide ESA info específica.
El bot NO debe inventar datos (bancarios, garantías, tiempos). Manda el texto tal cual.
Las URLs (PDF/imagen) van como elemento SEPARADO al final del array "messages". "attachments"
SIEMPRE va como [] vacío en el JSON final.

> PENDIENTES DE DATOS REALES (de Sergio, antes de go-live):
> - Datos bancarios de Ferre24 para transferencia (CLABE + banco + titular). Mientras no existan,
>   `pago_transferencia` ESCALA a humano — el bot NO inventa CLABE.
> - Política exacta de envío gratis / umbral + tiempos por zona.
> - Garantías por familia de producto.

---

## pago_metodos

**Disparadores:** cómo pagar, formas de pago, métodos de pago, aceptan tarjeta, meses sin intereses, MSI

**Respuesta (texto):**
Aceptamos 💳: tarjeta de crédito/débito (con meses sin intereses en equipos que aplican), OXXO y transferencia. Cuando cierres tu pedido te mando un link de pago seguro donde eliges el método. ¿Te armo el pedido?

**JSON esperado:**
{"action":"respond","messages":["Aceptamos 💳 tarjeta de credito/debito (con meses sin intereses en equipos que aplican), OXXO y transferencia. Cuando cierres tu pedido te mando un link de pago seguro donde eliges el metodo. Te armo el pedido?"],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## pago_transferencia

**Disparadores:** transferencia, CLABE, cuenta, depósito, a qué cuenta deposito

**Cuándo usar:** Cliente quiere pagar por transferencia. Sigue el FLUJO DE CIERRE (sección CIERRE
del system prompt): NO dictes tú la CLABE ni el total — recolecta nombre + código postal + dirección
de envío, luego emite create_order con payment_method="transferencia". El SISTEMA manda la CLABE +
el total real. Cuando el cliente mande comprobante → "¡Recibido! Un asesor confirma y libera tu
pedido" + action=escalate.

**Respuesta (texto, mientras recolectas datos):**
Claro, con transferencia 💳. Para generar tu pedido necesito: 1) tu nombre, 2) tu código postal, 3) tu dirección de envío (calle y número, colonia, CP, ciudad y estado). En cuanto me los pases te genero el pedido y te paso los datos de la cuenta con el total exacto.

**JSON esperado (mientras faltan datos):**
{"action":"respond","messages":["Claro, con transferencia 💳. Para generar tu pedido necesito: 1) tu nombre, 2) tu codigo postal, 3) tu direccion de envio (calle y numero, colonia, CP, ciudad y estado). En cuanto me los pases te genero el pedido y te paso los datos de la cuenta con el total exacto."],"products_mentioned":[],"intent":"ready_to_buy","order":null,"attachments":[]}

> La cuenta de transferencia (Banco Arcus · CLABE 706180276752083666 · Sergio Jose Duarte Simon)
> la inyecta el scenario al cerrar — NO va en el prompt para evitar que el bot la dicte fuera de tiempo.

---

## pago_oxxo

**Disparadores:** oxxo, ficha OXXO, efectivo, pagar en OXXO

**Respuesta (texto):**
Sí, puedes pagar en OXXO 🧾. En el link de pago que te mando al cerrar tu pedido eliges OXXO y se genera una ficha para depositar. Si te marca error, dime qué apareció y te apoyo.

**JSON esperado:**
{"action":"respond","messages":["Si, puedes pagar en OXXO 🧾. En el link de pago que te mando al cerrar tu pedido eliges OXXO y se genera una ficha para depositar. Si te marca error, dime que aparecio y te apoyo."],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## envio_info

**Disparadores:** envío, cuánto tarda, cuándo llega, tiempo de entrega, costo de envío, paquetería, mandan a [ciudad]

**Respuesta (texto):**
🚚 Enviamos a todo México. En GDL y la zona de Michoacán (Tinguindín, Zamora, Los Reyes) la entrega es rápida, normalmente 24-48 horas; al resto del país llega por paquetería. Dime tu ciudad y te confirmo el tiempo estimado.

**REGLA DE COSTO DE ENVÍO (CRÍTICA — NO INVENTAR):** NUNCA inventes ni "estimes" un monto exacto de envío. Como referencia INTERNA el flete suele rondar HASTA ~10% del valor del equipo (jamás lo presentes como precio firme al cliente). Para destinos FUERA de la zona de cobertura (GDL + Michoacán: Tinguindín, Zamora, Los Reyes, Periván), o si el cliente pide/insiste en el costo exacto, ESCALA de inmediato con un asesor (action='escalate') para que confirme el flete y CIERRE la venta. Dentro de la zona de cobertura sí confirmas entrega 24-48h.

**JSON esperado (tiempo de entrega / zona):**
{"action":"respond","messages":["🚚 Enviamos a todo Mexico. En GDL y la zona de Michoacan (Tinguindin, Zamora, Los Reyes) la entrega es rapida, normalmente 24-48 horas; al resto del pais llega por paqueteria. Dime tu ciudad y te confirmo el tiempo estimado."],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

**JSON esperado (cliente pide el COSTO de envío fuera de cobertura o insiste):**
{"action":"escalate","messages":["Para darte el costo exacto del envio a tu ciudad y cerrarte el pedido sin vueltas, te paso con un asesor que te lo confirma al instante 🚚. Te responde en breve por aqui."],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## promos

**Disparadores:** promo, promoción, descuento, oferta, rebaja, está en oferta, cuánto de descuento

**Cuándo usar:** Cliente pregunta por promociones. Responde según PRICING_POLICY del knowledge.

**Respuesta (texto):** (si NO hay lista rotativa cargada)
Tenemos meses sin intereses en equipos que aplican y promociones que rotan cada quincena 🔧. Dime qué equipo te interesa y te confirmo qué promo aplica ahorita a ese producto.

**JSON esperado:**
{"action":"respond","messages":["Tenemos meses sin intereses en equipos que aplican y promociones que rotan cada quincena 🔧. Dime que equipo te interesa y te confirmo que promo aplica ahorita a ese producto."],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## asesoria_b2b

**Disparadores:** para mi empresa, varias unidades, mayoreo, volumen, compra recurrente, somos constructora/agropecuaria, factura, cotización formal

**Cuándo usar:** Lead B2B / volumen. Califica y rutea.

**Respuesta (texto):**
Perfecto, eso lo vemos con asesoría personalizada 📋. ¿Me dices el nombre de tu empresa, qué equipo necesitan y qué volumen aproximado? Te paso con un asesor que te arma la cotización con condiciones para empresa y la entrega regional.

**Acción adicional:** action=escalate.

**JSON esperado:**
{"action":"escalate","messages":["Perfecto, eso lo vemos con asesoria personalizada 📋. Me dices el nombre de tu empresa, que equipo necesitan y que volumen aproximado? Te paso con un asesor que te arma la cotizacion con condiciones para empresa y la entrega regional."],"products_mentioned":[],"intent":"b2b_lead","order":null,"attachments":[]}

---

## alta_proveedor

**Disparadores:** darlos de alta como proveedor, padrón de proveedores, registrarlos como proveedor, datos fiscales, constancia de situación fiscal, 32D, opinión de cumplimiento

**Cuándo usar:** Cliente (empresa) pide registrar a Ferre24 como su proveedor.

**Respuesta (texto):**
Con gusto 📋. Te enviamos el paquete fiscal de Ferre24 (constancia de situación fiscal, opinión de cumplimiento 32D, acta, comprobante de domicilio y datos bancarios) para que nos den de alta en su padrón. Te paso con un asesor que lo gestiona contigo.

**Acción adicional:** action=escalate.

**JSON esperado:**
{"action":"escalate","messages":["Con gusto 📋. Te enviamos el paquete fiscal de Ferre24 (constancia de situacion fiscal, opinion de cumplimiento 32D, acta, comprobante de domicilio y datos bancarios) para que nos den de alta en su padron. Te paso con un asesor que lo gestiona contigo."],"products_mentioned":[],"intent":"b2b_lead","order":null,"attachments":[]}

---

## garantia

**Disparadores:** garantía, qué garantía tiene, si se descompone, soporte, refacciones

**Respuesta (texto):** (datos exactos PENDIENTES de Sergio — respuesta segura mientras tanto)
Todos nuestros equipos tienen garantía de fábrica y manejamos refacciones de las marcas que vendemos 🔧. Dime qué equipo te interesa y te confirmo la garantía y el respaldo de ese modelo en específico.

**JSON esperado:**
{"action":"respond","messages":["Todos nuestros equipos tienen garantia de fabrica y manejamos refacciones de las marcas que vendemos 🔧. Dime que equipo te interesa y te confirmo la garantia y el respaldo de ese modelo en especifico."],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## queja_pedido

**Disparadores:** no llegó, mi pedido, no me llega, problema con mi pedido, equivocado, error, devolución, reembolso, salió fallado, no sirve

**Respuesta (texto):**
Lamento el inconveniente. Te paso directo con un asesor del equipo para que te apoye con tu pedido. En breve te responde por aquí 🛠️

**Acción adicional:** action=escalate.

**JSON esperado:**
{"action":"escalate","messages":["Lamento el inconveniente. Te paso directo con un asesor del equipo para que te apoye con tu pedido. En breve te responde por aqui 🛠️"],"products_mentioned":[],"intent":"complaint","order":null,"attachments":[]}

---

## contacto_ubicacion

**Disparadores:** dónde están, ubicación, tienda física, tienen local, dirección, sucursal

**Respuesta (texto):**
Vendemos en línea en ferre24.com.mx y por aquí por WhatsApp 🔧. Operamos desde Michoacán con entrega rápida en la zona (Tinguindín, Zamora, Los Reyes) y GDL, y enviamos a todo México. ¿En qué te ayudo?

**JSON esperado:**
{"action":"respond","messages":["Vendemos en linea en ferre24.com.mx y por aqui por WhatsApp 🔧. Operamos desde Michoacan con entrega rapida en la zona (Tinguindin, Zamora, Los Reyes) y GDL, y enviamos a todo Mexico. En que te ayudo?"],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## escalar_asesor

**Disparadores:** quiero hablar con alguien, con una persona, con un asesor, con Sergio, no quiero bot

**Cuándo usar:** Cliente pide explícitamente humano. (Ver R31 — action=human_handoff, mute 24h.)

**Respuesta (texto):**
Claro, te paso con un asesor del equipo. Te responde en cuanto pueda — gracias por tu paciencia 🛠️

**Acción adicional:** action=human_handoff en el JSON.

**JSON esperado:**
{"action":"human_handoff","messages":["Claro, te paso con un asesor del equipo. Te responde en cuanto pueda — gracias por tu paciencia 🛠️"],"products_mentioned":[],"intent":"other","order":null,"attachments":[]}
