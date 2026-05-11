---
name: Prospects Calendar OAuth setup
description: OAuth de Google Calendar para auto-trigger del dashboard de prospects (Interesado → mockup + cita + email). LIVE 2026-05-04.
type: project
originSessionId: ef5c9756-824a-4ed8-80f9-0c4ee19d4e4d
---
OAuth de Google Calendar configurado 2026-05-04 para el sistema de prospects. Cuando Gibran marca un lead como "Interesado" en el dashboard, dispara automáticamente: mockup v1 local + evento en Calendar + email resumen.

**Setup vivo:**
- OAuth Desktop client en proyecto Google Cloud `calm-cab-493723-k7` ("My First Project") bajo cuenta `metagreenlabs@gmail.com`
- Client name en Cloud Console: "SPEKGEN Calendar Auto"
- Client ID: `536762513958-i91ulevovlv7dg45rf1q354anmom1lt2.apps.googleusercontent.com`
- Test user autorizado: `gibran.alonzo0506@gmail.com` (donde aparecen los eventos)
- Consent app name: "SPEKGEN V2" (testing mode)
- Token cache: `PROSPECTOS/_tools/automations/.calendar_token.json`
- Client secret: `PROSPECTOS/_tools/automations/client_secret.json`
- Wrapper para re-auth via Claude-in-Chrome: `_setup_gcal_via_claude.py` (server local en port 9876)
- Dashboard server lo invoca via thread daemon en `serve_dashboard.py:84-117` cuando detecta cambio a "Interesado" + nuevos campos `meeting_fecha` y `meeting_contacto`
- Smoke test 2026-05-04: trigger completo OK (calendar + email summary), token refresca solo

**Why:** Gibran no puede operar OAuth Cloud Console solo (no sabe los pasos). Setup hecho via Claude-in-Chrome MCP en sesión 2026-05-04. Permite que el dashboard de prospects sea autónomo durante Japón (cuando él marque "Interesado", sistema hace mockup + cita sin él).

**How to apply:** Si el token expira o se borra, re-autorizar con `python3 _setup_gcal_via_claude.py` y navegar al `AUTH_URL` que printa. Si Google rota policies, puede requerir re-crear OAuth client en Cloud Console (5 clicks). Si Gibran quiere replicar para otra cuenta Google Cloud, mismo flow: Calendar API enable → consent screen testing + add gibran como test user → Desktop OAuth client → download JSON.
