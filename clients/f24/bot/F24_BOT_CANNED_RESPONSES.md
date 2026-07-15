# Ferre24 Bot — Respuestas con Info Fija

Cada bloque es una "canned knowledge" que el bot usa cuando el cliente pide ESA info específica.
El bot NO debe inventar datos (bancarios, garantías, tiempos). Manda el texto tal cual.
Las URLs de PDF/ficha de producto van como elemento SEPARADO al final del array "messages".

**EXCEPCIÓN — GUÍAS DE PAGO BRANDED (formalidad):** cuando el cliente pregunta por un MÉTODO de
pago ESPECÍFICO (transferencia/SPEI, OXXO, tarjeta/MSI), adjunta su guía visual branded en
"attachments" (es una imagen PNG en el CDN de Shopify → WhatsApp la muestra como tarjeta, no como
link). UNA guía, la del método que preguntó — nunca varias. Esto da la formalidad de una empresa
seria (tarjeta con CLABE, banco, pasos) sin que el bot dicte datos sueltos. Para la pregunta
GENÉRICA "¿cómo pago / formas de pago?" NO adjuntes imagen (son varios métodos → satura): manda el
texto + el link de la página. En todo lo demás, "attachments" va como [] vacío.

> PENDIENTES DE DATOS REALES (de Sergio, antes de go-live):
> - Datos bancarios de Ferre24 para transferencia (CLABE + banco + titular). Mientras no existan,
>   `pago_transferencia` ESCALA a humano — el bot NO inventa CLABE.
> - Política exacta de envío gratis / umbral + tiempos por zona.
> - Garantías por familia de producto.

---

## pago_metodos

**Disparadores:** cómo pagar, formas de pago, métodos de pago (pregunta GENÉRICA, sin nombrar un método)

**Cuándo usar:** el cliente pregunta en general "¿cómo pago?" sin nombrar un método. Aquí NO
adjuntas imagen (son varios métodos → satura): mandas el texto + el link de la página. Si el cliente
aterriza en un método específico (OXXO / transferencia / tarjeta-MSI) → usa el bloque de ese método,
que SÍ adjunta su guía branded (`pago_oxxo`, `pago_transferencia`, `pago_tarjeta_msi`).

**Respuesta (texto):**
Aceptamos 💳: tarjeta de crédito/débito (con meses sin intereses en equipos que aplican), OXXO y transferencia. Aquí te explico cómo pagar paso a paso: https://ferre24.com.mx/pages/como-pagar. Cuando cierres tu pedido te mando un link de pago seguro. ¿Te armo el pedido?

**JSON esperado:**
{"action":"respond","messages":["Aceptamos 💳 tarjeta de credito/debito (con meses sin intereses en equipos que aplican), OXXO y transferencia.","Aqui te explico como pagar paso a paso 👉 https://ferre24.com.mx/pages/como-pagar","Cuando cierres tu pedido te mando un link de pago seguro. Te armo el pedido?"],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

---

## pago_transferencia

**Disparadores:** transferencia, CLABE, cuenta, depósito, a qué cuenta deposito

**Cuándo usar:** Cliente quiere pagar por transferencia. Sigue el FLUJO DE CIERRE (sección CIERRE
del system prompt): NO dictes tú la CLABE ni el total — recolecta nombre + código postal + dirección
de envío, luego emite create_order con payment_method="transferencia". El SISTEMA manda la CLABE +
el total real. Cuando el cliente mande comprobante → "¡Recibido! Un asesor confirma y libera tu
pedido" + action=escalate.

**Respuesta (texto, mientras recolectas datos):** adjunta la guía SPEI branded (trae la CLABE,
beneficiario y banco reales, y ella misma indica "transfiere el monto exacto del total de tu pedido"
→ NO provoca pago prematuro). Aun así recolectas nombre + CP + dirección y cierras con create_order
(payment_method="transferencia") para que el sistema mande el TOTAL exacto.
Claro, con transferencia 💳. Aquí tienes los datos de la cuenta (aparecen en la guía). Para armar tu pedido y darte el total exacto necesito: 1) tu nombre, 2) tu código postal, 3) tu dirección de envío (calle y número, colonia, CP, ciudad y estado). En cuanto me los pases te genero el pedido con el total.

**JSON esperado (mientras faltan datos — con guía branded adjunta):**
{"action":"respond","messages":["Claro, con transferencia 💳. Aqui tienes los datos de la cuenta (aparecen en la guia).","Para armar tu pedido y darte el total exacto necesito: 1) tu nombre, 2) tu codigo postal, 3) tu direccion de envio (calle y numero, colonia, CP, ciudad y estado). En cuanto me los pases te genero el pedido con el total."],"products_mentioned":[],"intent":"ready_to_buy","order":null,"attachments":["https://cdn.shopify.com/s/files/1/0725/1519/0872/files/GUIA_TRANSFERENCIA_SPEI_353fc071-c655-4ddd-8373-017fc0e55288.png"]}

> La CLABE también la inyecta el scenario al cerrar (con el total real). La guía branded se adjunta
> ANTES como formalidad; su propio texto obliga a transferir el total del pedido, no un monto suelto.

---

## pago_oxxo

**Disparadores:** oxxo, ficha OXXO, efectivo, pagar en OXXO

**Respuesta (texto — con guía OXXO branded adjunta):**
Sí, puedes pagar en OXXO 🧾. Te dejo la guía con el paso a paso. En el link de pago que te mando al cerrar tu pedido eliges OXXO y se genera una ficha para depositar. Si te marca error, dime qué apareció y te apoyo.

**JSON esperado:**
{"action":"respond","messages":["Si, puedes pagar en OXXO 🧾. Te dejo la guia con el paso a paso.","En el link de pago que te mando al cerrar tu pedido eliges OXXO y se genera una ficha para depositar. Si te marca error, dime que aparecio y te apoyo."],"products_mentioned":[],"intent":"asking","order":null,"attachments":["https://cdn.shopify.com/s/files/1/0725/1519/0872/files/GUIA_OXXO_e71e0369-19de-4f37-9996-593955672abe.png"]}

---

## pago_tarjeta_msi

**Disparadores:** con tarjeta, aceptan tarjeta, meses sin intereses, MSI, a cuántos meses, diferir, ¿hay meses?

**Cuándo usar:** el cliente pregunta específicamente por pago con TARJETA o por los MESES SIN
INTERESES. Adjunta la guía branded de tarjeta+MSI. Regla de oro: MSI SOLO con tarjeta de CRÉDITO;
hasta 6 en el pago normal; **9 y 12 solo en SKUs de la lista de promos** (ahí cierras con
payment_method="msi_promo" y el sistema genera el link MercadoPago con hasta 12 MSI — ver PRICING).

**Respuesta (texto — con guía tarjeta/MSI branded adjunta):**
Sí, aceptamos tarjeta de crédito y débito 💳. Con tarjeta de crédito manejas meses sin intereses (hasta 6 en la mayoría de equipos; 9 y 12 en los que están en promo). Te dejo la guía. ¿Te armo el pedido y te paso el link de pago?

**JSON esperado:**
{"action":"respond","messages":["Si, aceptamos tarjeta de credito y debito 💳. Con tarjeta de credito manejas meses sin intereses (hasta 6 en la mayoria de equipos; 9 y 12 en los que estan en promo).","Te dejo la guia. Te armo el pedido y te paso el link de pago?"],"products_mentioned":[],"intent":"asking","order":null,"attachments":["https://cdn.shopify.com/s/files/1/0725/1519/0872/files/GUIA_TARJETA_CREDITO_MSI_50eea5d8-9373-4b39-8923-310d59a89e6a.png"]}

---

## envio_info

**Disparadores:** envío, cuánto tarda, cuándo llega, tiempo de entrega, costo de envío, paquetería, mandan a [ciudad]

**Respuesta (texto):**
🚚 Enviamos a todo México. En GDL y la zona de Michoacán (Tinguindín, Zamora, Los Reyes) la entrega es rápida, normalmente 24-48 horas; al resto del país llega por paquetería. Dime tu ciudad y te confirmo el tiempo estimado.

**REGLA DE COSTO DE ENVÍO (CRÍTICA — SE COTIZA REAL, YA NO SE INVENTA NI SE ESCALA):** el sistema
saca la tarifa REAL por CP directo con la paquetería. NUNCA inventes ni "estimes" un monto (ni cites
la vieja referencia del ~10%). Cuando el cliente pregunte el COSTO del envío: si NO tienes su código
postal, pídeselo (action='respond'). En cuanto tengas el CP y haya un producto en contexto, emite
action='quote_shipping' con el CP en "codigo_postal" y el SKU en "products_mentioned"; tus "messages"
son solo un puente corto SIN monto y el sistema manda la tarifa real. El tiempo de entrega por zona
(24-48h GDL/Michoacán, resto por paquetería) sí lo confirmas tú directo.

**JSON esperado (tiempo de entrega / zona):**
{"action":"respond","messages":["🚚 Enviamos a todo Mexico. En GDL y la zona de Michoacan (Tinguindin, Zamora, Los Reyes) la entrega es rapida, normalmente 24-48 horas; al resto del pais llega por paqueteria. Dime tu ciudad y te confirmo el tiempo estimado."],"products_mentioned":[],"intent":"asking","order":null,"attachments":[]}

**JSON esperado (cliente pide el COSTO y AÚN no tienes su CP → pídelo):**
{"action":"respond","messages":["Con gusto te cotizo el envio 🚚. ¿Cual es tu codigo postal? Con eso te saco la tarifa exacta al instante."],"products_mentioned":["GPH1000W"],"intent":"asking","codigo_postal":"","order":null,"attachments":[]}

**JSON esperado (ya tienes CP + producto → cotización real, puente SIN monto):**
{"action":"quote_shipping","messages":["Dejame checar el envio a tu CP 📦"],"products_mentioned":["GPH1000W"],"intent":"asking","codigo_postal":"06700","order":null,"attachments":[]}

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

---

## pago_contraentrega_tyc

> ⚠️ **BORRADOR — PENDIENTE DE APROBACIÓN DE SERGIO.** Estos Términos y Condiciones NO están
> validados por Ferre24. El umbral exacto de monto, la política de verificación de INE, quién
> entrega/cobra y la cobertura fina por zona los define Sergio antes de ponerlo LIVE. Mientras no
> apruebe, este canned NO debe usarse en producción — el bot solo lo plantea como opción sujeta a
> confirmación de un asesor y SIEMPRE termina en handoff humano (nunca cierra el COD solo).

**Disparadores:** pago contraentrega, pagar al recibir, pagar cuando llegue, contra entrega, COD,
pagar en efectivo al recibir, ¿me cobran al entregar?

**Cuándo usar:** SOLO después de calificar al cliente (ver bloque PAGO CONTRAENTREGA (COD) del system
prompt): CP en Guanajuato (36-38) / Jalisco (44-49) / Michoacán (58-61), pedido grande (~$10k+) de
productos EN PROMO, pago de CONTADO (no MSI), y el cliente pidió las condiciones. Si NO califica, NO
mandes este bloque. El cliente debe ACEPTAR estos términos explícitamente antes de que captures sus
datos y escales.

**Respuesta (texto — BORRADOR de T&C, sujeto a confirmación de asesor):**
Con gusto. Pago contraentrega significa que pagas en EFECTIVO al recibir tu equipo 🚚. Aplica bajo estas
condiciones (te las confirma un asesor al cerrar): 1) Solo entregamos contraentrega en Guanajuato, Jalisco
y Michoacán. 2) Solo para pedidos de contado de $10,000 o más en productos que están en promoción. 3) No
aplica a meses sin intereses (el COD es de contado). 4) Al entregar te pedimos una identificación oficial
(INE) y un comprobante de domicilio para validar la entrega. 5) La mercancía se entrega y se cobra en el
momento; un asesor confirma la fecha y coordina el envío. ¿Estás de acuerdo con estas condiciones? Si sí,
te pido tu nombre y dirección completa para pasarlo con el asesor que lo agenda.

**Acción adicional:** action=respond mientras el cliente decide/acepta. Una vez que ACEPTA y ya diste
nombre + dirección + CP → action=escalate con el lead_summary de COD (ver system prompt). El COD NUNCA
cierra con create_order — siempre termina en handoff a Sergio/Edgar.

**JSON esperado (presentando los T&C, cliente aún no acepta):**
{"action":"respond","messages":["Con gusto. Pago contraentrega significa que pagas en EFECTIVO al recibir tu equipo 🚚. Aplica bajo estas condiciones (te las confirma un asesor al cerrar):","1) Solo entregamos contraentrega en Guanajuato, Jalisco y Michoacan. 2) Solo para pedidos de contado de $10,000 o mas en productos en promocion. 3) No aplica a meses sin intereses (el COD es de contado).","4) Al entregar te pedimos identificacion oficial (INE) y comprobante de domicilio para validar la entrega. 5) La mercancia se entrega y se cobra en el momento; un asesor confirma la fecha y coordina el envio.","Estas de acuerdo con estas condiciones? Si si, te pido tu nombre y direccion completa para pasarlo con el asesor que lo agenda."],"products_mentioned":["GP9500TB"],"intent":"ready_to_buy","codigo_postal":"45100","order":null,"attachments":[]}

**JSON esperado (cliente ACEPTÓ + ya dio nombre y dirección → escalate con lead_summary COD):**
{"action":"escalate","messages":["¡Listo! Ya con eso te paso con un asesor para que valide tu identificacion, confirme el total y agende la entrega contraentrega 🛠️. Te contacta en breve por aqui."],"products_mentioned":["GP9500TB"],"intent":"b2b_lead","codigo_postal":"45100","lead_summary":"PAGO CONTRAENTREGA · Estado: Jalisco · Producto(s) promo: GP9500TB · Cantidad: 1 · CP: 45100 · Cliente: Juan Perez · Direccion: Av. Vallarta 100, Col. Centro, Guadalajara, Jalisco · Contado · FALTA VERIFICAR: INE + comprobante de domicilio (el asesor recolecta y confirma umbral $ y entrega)","order":null,"attachments":[]}
