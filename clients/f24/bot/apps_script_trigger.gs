/**
 * F24 — Gatillo instantáneo de sincronización
 * ------------------------------------------------------------
 * Ligado al Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U).
 *
 * Cuando el dueño edita el inventario/promos en VIVO, este script dispara
 * (con debounce) el workflow de GitHub Actions "f24_promos_sync.yml" del repo
 * SPEKGEN-ORG/spekgen-os, para que el bot quede sincronizado al momento sin
 * esperar al cron de 2×/día.
 *
 * Requiere un trigger INSTALABLE onEdit (NO el simple onEdit), porque el simple
 * no tiene permisos para hacer UrlFetchApp con autenticación.
 *
 * Setup completo (token, propiedades, trigger): ver APPS_SCRIPT_SETUP.md
 */

// ============================================================
// CONFIGURACIÓN
// ============================================================

// Repo destino del workflow_dispatch
var GH_OWNER = 'SPEKGEN-ORG';
var GH_REPO  = 'spekgen-os';
var GH_WORKFLOW_FILE = 'f24_promos_sync.yml';
var GH_REF = 'main'; // rama donde corre el workflow

// Hojas que vigilamos
var SHEET_CAPTURA = '✍️ CAPTURA PROMOS'; // cualquier edición dispara
var SHEET_STOCK   = '📦 STOCK Y PROMOS';  // solo dispara si se edita col E (5) o F (6)
var STOCK_COL_PRECIO = 5; // columna E = precio
var STOCK_COL_STOCK  = 6; // columna F = stock

// Debounce: coalescer ráfagas de ediciones en un solo dispatch
var DEBOUNCE_MS = 60000; // ~60 segundos
var PROP_PENDING_SINCE = 'pendingSince';

// ============================================================
// 1) onEditTrigger — entry point del trigger INSTALABLE onEdit
// ============================================================

/**
 * Se ejecuta en cada edición del Sheet (vía trigger instalable).
 * Filtra qué ediciones merecen disparar la sincronización y, si aplica,
 * arma/reinicia el debounce.
 */
function onEditTrigger(e) {
  try {
    if (!e || !e.range) {
      return; // llamada inválida, nada que hacer
    }

    var sheet = e.range.getSheet();
    var sheetName = sheet.getName();

    var debeDisparar = false;

    if (sheetName === SHEET_CAPTURA) {
      // En la hoja de captura, CUALQUIER edición cuenta
      debeDisparar = true;
    } else if (sheetName === SHEET_STOCK) {
      // En stock/promos, solo precio (col E=5) o stock (col F=6)
      var col = e.range.getColumn();
      if (col === STOCK_COL_PRECIO || col === STOCK_COL_STOCK) {
        debeDisparar = true;
      }
    }

    if (!debeDisparar) {
      return; // edición irrelevante → salir sin hacer nada
    }

    // Edición relevante → (re)armar el debounce
    scheduleDebouncedDispatch_();
  } catch (err) {
    // Nunca dejar que un error reviente la edición del usuario
    Logger.log('onEditTrigger error: ' + err);
  }
}

// ============================================================
// 2) Debounce — coalescer ediciones múltiples
// ============================================================

/**
 * Marca el momento de la última edición relevante y programa un disparo
 * único dentro de ~60s. Borra cualquier trigger time-based pendiente para
 * que ráfagas de ediciones no generen múltiples dispatches.
 */
function scheduleDebouncedDispatch_() {
  var props = PropertiesService.getScriptProperties();

  // Guardar el timestamp de "última edición pendiente"
  props.setProperty(PROP_PENDING_SINCE, String(Date.now()));

  // Borrar triggers time-based previos de fireDispatch (evita acumulación)
  deletePendingDispatchTriggers_();

  // Programar UN solo disparo dentro de DEBOUNCE_MS
  ScriptApp.newTrigger('fireDispatch')
    .timeBased()
    .after(DEBOUNCE_MS)
    .create();
}

/**
 * Elimina todos los triggers time-based pendientes que apunten a fireDispatch.
 * Los triggers onEdit (instalables) NO se tocan.
 */
function deletePendingDispatchTriggers_() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'fireDispatch') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

// ============================================================
// 3) fireDispatch — dispara el workflow_dispatch en GitHub
// ============================================================

/**
 * Se ejecuta cuando vence el debounce. Hace el POST a la API de GitHub para
 * disparar el workflow. Limpia el estado y sus propios triggers al terminar.
 */
function fireDispatch() {
  // Limpiar el/los trigger(s) que provocaron esta ejecución
  deletePendingDispatchTriggers_();

  var props = PropertiesService.getScriptProperties();
  props.deleteProperty(PROP_PENDING_SINCE);

  var pat = props.getProperty('GH_PAT');
  if (!pat) {
    Logger.log('fireDispatch: falta GH_PAT en las Propiedades del script. Abortando.');
    return;
  }

  var url = 'https://api.github.com/repos/' + GH_OWNER + '/' + GH_REPO +
            '/actions/workflows/' + GH_WORKFLOW_FILE + '/dispatches';

  var payload = {
    'ref': GH_REF
    // Nota: sin dry_run → el workflow corre en modo --apply (default 'false').
  };

  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'Authorization': 'Bearer ' + pat,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'f24-sheet-trigger'
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true // capturamos el código nosotros mismos
  };

  try {
    var resp = UrlFetchApp.fetch(url, options);
    var code = resp.getResponseCode();

    if (code === 204) {
      // 204 No Content = éxito (GitHub no devuelve body en dispatch OK)
      Logger.log('fireDispatch OK: workflow disparado (HTTP 204).');
    } else {
      // Cualquier otra cosa es error: loguear cuerpo para diagnóstico
      Logger.log('fireDispatch ERROR: HTTP ' + code + ' — ' + resp.getContentText());
    }
  } catch (err) {
    Logger.log('fireDispatch EXCEPTION: ' + err);
  }
}
