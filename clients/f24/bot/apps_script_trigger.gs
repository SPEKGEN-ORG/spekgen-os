/**
 * F24 - Gatillo instantaneo de sincronizacion (v2 - disparo directo)
 * ------------------------------------------------------------
 * Ligado al Sheet "INVENTARIO F24" (1WCRbnSMwdYMVCwPHjpGpqe4fSdGoQyAt91RDFZT2f3U).
 *
 * En cada edicion relevante (hoja CAPTURA PROMOS, o STOCK Y PROMOS col E/F/Q)
 * dispara el workflow_dispatch de "f24_promos_sync.yml" en SPEKGEN-ORG/spekgen-os
 * para sincronizar Shopify/landing/bot al momento, con throttle de 20s.
 *
 * Requiere un trigger INSTALABLE onEdit (NO el simple) + la propiedad GH_PAT.
 * Match de hojas por SUBSTRING ASCII (robusto a emojis/encoding del nombre).
 */

// ===================== CONFIG =====================
var GH_OWNER = 'SPEKGEN-ORG';
var GH_REPO = 'spekgen-os';
var GH_WORKFLOW_FILE = 'f24_promos_sync.yml';
var GH_REF = 'main';
var THROTTLE_MS = 20000; // coalescer rafagas de ediciones en un solo dispatch

// ===================== TRIGGER =====================
function onEditTrigger(e) {
  try {
    if (!e || !e.range) return;
    var sheetName = e.range.getSheet().getName();

    var relevant = false;
    if (sheetName.indexOf('CAPTURA') !== -1) {
      relevant = true; // cualquier edicion en CAPTURA PROMOS dispara
    } else if (sheetName.indexOf('STOCK Y PROMOS') !== -1) {
      var col = e.range.getColumn();
      if (col === 5 || col === 6 || col === 17) relevant = true; // E precio, F stock, Q descuento
    }
    if (!relevant) return;

    var props = PropertiesService.getScriptProperties();
    var now = Date.now();
    var last = parseInt(props.getProperty('lastDispatch') || '0', 10);
    if (now - last < THROTTLE_MS) return;
    props.setProperty('lastDispatch', String(now));

    fireDispatch();
  } catch (err) {
    Logger.log('onEditTrigger error: ' + err);
  }
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
