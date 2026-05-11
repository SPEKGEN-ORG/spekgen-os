---
name: Drive crash después de borrado masivo de archivos
description: Cuando se borran miles de archivos en paths sincronizados con Drive, Drive Desktop puede saturarse al 100% CPU y bloquear lecturas vía file://
type: feedback
originSessionId: 99bf4022-b3d3-4cd0-8c8a-7e3e9230f758
---
Cuando ejecutes operaciones de borrado masivo dentro de `~/Library/CloudStorage/GoogleDrive-.../` (ej. `find ... -name node_modules -exec rm -rf {} +`, o eliminar carpetas grandes con miles de subarchivos), Google Drive Desktop puede subir a 100% CPU procesando los cambios contra la nube y trabarse — quedan inaccesibles los archivos vía `file://` URLs y las apps cuyo .app bundle vive en Drive (rebotan en el dock sin abrir).

**Why:** Drive sincroniza cada delete con la nube y procesa los miles de eventos en serie. Mientras procesa, el FileProvider que sirve los archivos al sistema deja de responder. No es por borrar los archivos importantes — los archivos están intactos. Es saturación del proceso Drive.

**How to apply:**
- **Antes de borrados masivos en Drive:** advertir al usuario que Drive puede ralentizarse 5-30 min después
- **Si Drive sube al 80%+ CPU y archivos no responden:** `pkill -9 -f "Google Drive"` + `pkill -9 -f "DFSFileProviderExtension"` + `open -a "Google Drive"`. CPU baja inmediato, FileProvider remonta en ~30s, archivos vuelven a responder
- **Síntomas a reconocer:** Chrome dice `ERR_FAILED` al abrir `file:///Users/.../GoogleDrive-.../...`, apps en dock rebotan sin abrir si su bundle vive en Drive, `cp` desde paths de Drive cuelga
- **NO confundir con archivos borrados** — siempre verificar primero con `ls -la` que los archivos sigan ahí (suelen estar intactos, solo bloqueados)
- Riesgo del kill: bajo. Drive persiste pending uploads a disco antes de procesar; al relanzar retoma sin perder data
- Evitar a futuro: agregar `node_modules`, `__pycache__`, `.venv` al `.gitignore` global y no permitir que vivan dentro de carpetas sincronizadas con Drive
