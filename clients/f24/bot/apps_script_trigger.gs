/**
 * F24 - Gatillo de sincronizacion (v3 - DEBOUNCE REAL)
 * ------------------------------------------------------------
 * Ligado al Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U).
 *
 * En cada edicion relevante (hoja CAPTURA PROMOS, o STOCK Y PROMOS col E/F/Q) NO dispara
 * de inmediato: agenda un flush con DEBOUNCE real. Dispara UN SOLO workflow_dispatch de
 * "f24_promos_sync.yml" recien 90s DESPUES de la ULTIMA edicion. Asi, editar 20 filas
 * seguidas = 1 dispatch = 1 deploy del bot (no 20 = el storm que tiro mensajes del bot).
 *
 * v2 (anterior) tenia un THROTTLE de 20s que NO agrupaba: disparaba la 1a edicion y luego
 * 1 cada 20s durante una sesion de edicion -> storm. ESTE v3 es un debounce de cola real.
 *
 * Requiere: trigger INSTALABLE onEdit -> onEditTrigger + propiedad de script GH_PAT.
 * (El flush usa un trigger time-based que el propio script crea/borra; no configurar a mano.)
 */

// ===================== CONFIG =====================
var GH_OWNER = 'SPEKGEN-ORG';
var GH_REPO = 'spekgen-os';
var GH_WORKFLOW_FILE = 'f24_promos_sync.yml';
var GH_REF = 'main';
var DEBOUNCE_MS = 90000; // dispara UNA vez, 90s despues de la ULTIMA edicion

// ===================== TRIGGER (onEdit) =====================
function onEditTrigger(e) {
  try {
    if (!e || !e.range) return;
    var sheetName = e.range.getSheet().getName();

    var relevant = false;
    if (sheetName.indexOf('CAPTURA') !== -1) {
      relevant = true; // cualquier edicion en CAPTURA PROMOS
    } else if (sheetName.indexOf('STOCK Y PROMOS') !== -1) {
      var col = e.range.getColumn();
      if (col === 5 || col === 6 || col === 17) relevant = true; // E precio, F stock, Q descuento
    }
    if (!relevant) return;

    // Debounce: marca la ultima edicion y garantiza UN solo flush pendiente.
    PropertiesService.getScriptProperties().setProperty('lastEditTs', String(Date.now()));
    ensureFlushTrigger_();
  } catch (err) {
    Logger.log('onEditTrigger error: ' + err);
  }
}

// Crea un unico trigger de flush ~DEBOUNCE_MS adelante. Si ya hay uno pendiente, no crea otro.
function ensureFlushTrigger_() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'flushDispatch') return;
  }
  ScriptApp.newTrigger('flushDispatch').timeBased().after(DEBOUNCE_MS).create();
}

// Corre DEBOUNCE_MS despues. Si siguen editando (silencio < DEBOUNCE_MS) reprograma;
// si ya hubo silencio, dispara UN SOLO dispatch.
function flushDispatch() {
  // Borra este trigger (y cualquier flush duplicado) primero.
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'flushDispatch') ScriptApp.deleteTrigger(triggers[i]);
  }
  var props = PropertiesService.getScriptProperties();
  var last = parseInt(props.getProperty('lastEditTs') || '0', 10);
  if (!last) return;

  if (Date.now() - last < DEBOUNCE_MS) {
    ensureFlushTrigger_(); // siguen editando -> espera otra ventana
    return;
  }
  props.deleteProperty('lastEditTs');
  fireDispatch();          // silencio confirmado -> UN solo dispatch
}

// ===================== DISPATCH =====================
function fireDispatch() {
  var props = PropertiesService.getScriptProperties();
  var pat = props.getProperty('GH_PAT');
  if (!pat) {
    Logger.log('fireDispatch: falta GH_PAT en las Propiedades del script. Abortando.');
    return;
  }

  var url = 'https://api.github.com/repos/' + GH_OWNER + '/' + GH_REPO +
            '/actions/workflows/' + GH_WORKFLOW_FILE + '/dispatches';

  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'Authorization': 'Bearer ' + pat,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'f24-sheet-trigger'
    },
    'payload': JSON.stringify({ 'ref': GH_REF }),
    'muteHttpExceptions': true
  };

  try {
    var resp = UrlFetchApp.fetch(url, options);
    var code = resp.getResponseCode();
    if (code === 204) {
      Logger.log('fireDispatch OK: workflow disparado (HTTP 204).');
    } else {
      Logger.log('fireDispatch ERROR: HTTP ' + code + ' - ' + resp.getContentText());
    }
  } catch (err) {
    Logger.log('fireDispatch EXCEPTION: ' + err);
  }
}
