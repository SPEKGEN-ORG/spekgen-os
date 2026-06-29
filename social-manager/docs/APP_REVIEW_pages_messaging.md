# App Review — `pages_messaging` (DMs de Messenger)

Necesario SOLO para auto-responder **DMs de Facebook Messenger** en HC y LF.
**No** afecta a comentarios ni a DMs de Instagram (esos ya funcionan). **F24 ya tiene el scope.**

## Apps a las que hay que pedírselo

| App | App ID | Cubre | Estado |
|---|---|---|---|
| SPEKGEN Agency API | `1465486404956665` | HC, GR, MG, Gibran | falta `pages_messaging` |
| SpekGen Marketing API | `1683612316139834` | LF | falta `pages_messaging` |

Repetir el proceso en **cada** app (dos solicitudes independientes).

## Pre-requisitos (verificar antes de solicitar)

1. **App en modo Live** (toggle arriba en el dashboard de la app; no "In development").
2. **Business verification** del negocio dueño de la app — Business Settings → Security Center.
   Probablemente ya está hecho (las apps ya corren ads); confirmar que diga "Verified".
3. **App Settings → Basic**: Privacy Policy URL, ícono de app, categoría, y "Data Use Checkup" al día.
4. **Agregar el producto Messenger**: Dashboard → Add Product → **Messenger** → Set up.
5. **Webhook de Messenger** configurado (callback URL = webhook de Make de Fase 3 + verify token),
   suscrito a los campos `messages` y `messaging_postbacks`.

## Cómo solicitarlo

Dashboard de la app → **App Review → Permissions and Features** → buscar `pages_messaging`
→ **Request Advanced Access**. Llenar:

### Texto de caso de uso (pégalo, en inglés — el reviewer lo pide en inglés)
> Our app powers a customer-service assistant for the Facebook Pages we manage as a
> marketing agency. When a customer sends a Direct Message to a Page on Messenger, our
> system receives it via webhook and replies with helpful information (product availability,
> pricing, store links) within the standard 24-hour messaging window. A human agent can take
> over at any time. We only message users who messaged the Page first. We do not send
> promotional broadcasts.

### Screencast (obligatorio — el reviewer DEBE ver el permiso en acción)
1. Entrar como usuario normal y abrir el chat de Messenger de la Página de prueba.
2. Enviar un mensaje ("¿Cuánto cuesta X?").
3. Mostrar que el sistema recibe el mensaje y responde automáticamente.
4. Mostrar a un humano tomando la conversación (handoff).

Subir el video a la solicitud + confirmar que la Privacy Policy URL esté puesta.

## Notas / gotchas

- Si rechazan, casi siempre es por: screencast que no muestra claramente el permiso, o privacy
  policy faltante. Tener ambos listos.
- **Human Agent** (ventana de 7 días para que un humano responda fuera de las 24h) es un
  feature de Advanced Access **separado**. Pedirlo solo si lo vamos a usar.
- Timeline típico: pocos días a ~2 semanas.
- Mientras tanto: en modo development el bot SÍ puede responder DMs de Messenger a cuentas con
  rol en la app (admins/testers) — sirve para probar el flujo end-to-end antes de la aprobación.

## Qué NO espera esto

DMs de **Instagram** (`instagram_manage_messages`, ya concedido) y **todos los comentarios**
(IG + FB) ya están desbloqueados. Solo el auto-reply de Messenger DM de HC/LF depende de esta review.
