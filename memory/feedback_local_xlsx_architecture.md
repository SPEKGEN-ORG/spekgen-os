---
name: Architecture decision — xlsx in Google Drive as source of truth
description: All operational data lives in xlsx files in Google Drive (synced locally). No Supabase as source of truth. Vercel only for client views if needed.
type: feedback
---

Decisión arquitectónica confirmada 2026-03-30: archivos xlsx en Google Drive son la fuente de verdad operativa para toda la agencia.

**Why:** Se construyó un Content Hub en Vercel+Supabase que tiene data valiosa (HC content pipeline, ads) pero: Claude no puede accederlo entre sesiones, Gibran no puede editarlo, y cada chat nuevo no sabe que existe. Esto impide el objetivo de "agencia 100% AI".

**How to apply:**
1. xlsx en la carpeta del cliente = fuente de verdad (content calendars, ad logs, product logs, etc.)
2. Claude lee/escribe esos xlsx directamente en cada sesión
3. Google Drive sync hace que Gibran acceda desde cualquier dispositivo
4. Para automatizaciones 24/7 (sin Claude abierto) → Google Apps Script + Google Sheets
5. Para client views → Google Sheet compartido con vista elegante, o HTML simple
6. Supabase → dejar morir como fuente de verdad. Si se usa, solo como backend de views
7. Vercel → solo para client-facing views que lean de archivos base, nunca como lugar donde vive la data
8. Pendiente: migrar data de Supabase HC al xlsx local (contenido, pipeline, ads)
