---
name: Service accounts no tienen Drive quota
description: SAs sin Workspace no pueden create files en Drive (403 storageQuotaExceeded). Pueden read/write cells en sheets ya creados. Para crear archivos nuevos vía API → user OAuth o domain delegation
type: feedback
originSessionId: d8d67927-4170-4520-8588-26528a98b57d
---
Service accounts (como `spekgen-sync@spekgen-sheets.iam.gserviceaccount.com`) NO tienen Drive storage propia cuando no son parte de Google Workspace con domain delegation. Resultado: `drive.files().create()` falla con `403 storageQuotaExceeded`.

**Why:** Google asigna quota a usuarios humanos y a dominios Workspace. SAs standalone son identidades sin "casa" — pueden actuar pero no almacenar.

**How to apply:**
- SAs SÍ pueden: leer celdas, escribir celdas, batch update, formato, dropdowns en sheets que YA existen y donde el SA tiene permiso de editor.
- SAs NO pueden: crear sheets nuevos, subir archivos a Drive, convertir xlsx→Sheets via Drive create+convert.
- **Workflow recomendado para nuevos sheets vía API:**
  1. User crea sheet vacío en Drive web (10 segundos)
  2. User comparte el sheet con el email del SA como editor
  3. User pasa el `spreadsheet_id` al script
  4. SA llena/actualiza vía Sheets API
- **Alternativa si quieres todo programático:** OAuth con credenciales de usuario (refresh token) — el archivo se crea en el Drive del usuario con su quota. Setup: 15 min con `google-auth-oauthlib`.
- **Para xlsx que vive en Drive sincronizado:** Google Sheets abre xlsx nativo desde hace años con fórmulas, dropdowns y estilos respetados. No siempre necesitas convertir — abrirlo "con Google Sheets" desde Drive web ya basta para edición colaborativa.

**Caso encontrado:** 2026-05-06, intento de subir SPEKGEN_AGENCIA_FINANZAS.xlsx con conversión a Sheets nativo via SA. Decisión: dejar como xlsx — funciona idéntico para el caso de uso (compartir con Pedro, edición colaborativa).

**Cross-cliente:** aplica a cualquier futuro intento de crear gsheets desde script (cross-client-intel reports, dashboards nuevos, etc.). Siempre asume "user crea, SA llena".
