#!/usr/bin/env python3
"""
generate_dashboard.py — Genera dashboard.html del batch para human-runner Web UI Gemini.

Diseñado para que CUALQUIERA (Gibran, team member nuevo, etc.) pueda producir las
imágenes sin training previo. Incluye onboarding section embedded.

Uso:
    python3 generate_dashboard.py {BATCH_DIR}
    python3 generate_dashboard.py {BATCH_DIR} --port 8766

Output:
    {batch_dir}/dashboard.html

El dashboard se sirve con `serve_dashboard.py` en :8766.
"""
import argparse
import json
import sys
from pathlib import Path
from html import escape as html_escape


def build_dashboard(batch_dir: Path) -> str:
    batch = json.loads((batch_dir / "batch.json").read_text(encoding="utf-8"))
    batch_id = batch.get("batch_id", batch_dir.name)
    client = batch.get("client", "?")
    n_ads = len(batch.get("entries", []))
    n_completed = sum(1 for e in batch.get("entries", []) if e.get("final_image_path"))
    n_dropped = sum(1 for e in batch.get("entries", []) if e.get("status") == "DROPPED")
    n_pending = n_ads - n_completed - n_dropped

    # Build per-ad cards
    cards_html = ""
    for i, entry in enumerate(batch.get("entries", []), 1):
        code = entry.get("ad_code", "?")
        bucket = entry.get("format", "?")
        product = entry.get("product", "")
        hook = entry.get("hook_text_on_image", "")
        prompt = entry.get("gemini_prompt", "")
        copy = entry.get("ad_copy", {})
        attachments = entry.get("extra_attachments", [])
        status = entry.get("status", "DRAFT")
        final_path = entry.get("final_image_path")

        # Status badge
        if status == "DROPPED":
            status_badge = '<span class="badge badge-dropped">⊘ DROPPED</span>'
        elif final_path:
            status_badge = '<span class="badge badge-completed">✓ COMPLETED</span>'
        else:
            status_badge = '<span class="badge badge-pending">○ PENDING</span>'

        # Attachments thumbnails
        attach_html = ""
        for a in attachments:
            ap = batch_dir / a
            if ap.exists():
                rel = ap.relative_to(batch_dir).as_posix()
                attach_html += f'<div class="attach"><img src="{rel}" alt="{a}"/><div class="attach-name">{Path(a).name}</div></div>'

        # Final image preview if exists
        final_html = ""
        if final_path:
            fp = batch_dir / final_path
            if fp.exists():
                rel = fp.relative_to(batch_dir).as_posix()
                final_html = f'<div class="final-preview"><h4>FINAL aprobada</h4><img src="{rel}" alt="final"/></div>'

        cards_html += f'''
        <div class="ad-card" data-status="{status}">
          <div class="ad-header">
            <span class="ad-num">{i:02d}</span>
            <span class="ad-code">{html_escape(code)}</span>
            <span class="badge badge-bucket">{html_escape(bucket)}</span>
            {status_badge}
          </div>
          <div class="ad-body">
            <div class="left">
              <h4>📋 Concepto</h4>
              <p><strong>Producto:</strong> {html_escape(product)}</p>
              <p><strong>Hook on image:</strong> "{html_escape(hook)}"</p>
              <h4>📎 Attachments para arrastrar a Gemini</h4>
              <div class="attachments">{attach_html or '<em>(sin attachments)</em>'}</div>
              <h4>📝 Copy del ad (lo escribe Claude en Meta)</h4>
              <div class="copy-block">
                <p><strong>Headline:</strong> {html_escape(copy.get("headline", ""))}</p>
                <p><strong>Description:</strong> {html_escape(copy.get("description", ""))}</p>
                <p><strong>CTA:</strong> {html_escape(copy.get("cta_type", ""))}</p>
              </div>
              {final_html}
            </div>
            <div class="right">
              <div class="prompt-block">
                <h4>🎨 Prompt SCALIST <button class="copy-btn" data-target="prompt-{i}">📋 COPIAR</button></h4>
                <pre id="prompt-{i}">{html_escape(prompt)}</pre>
              </div>
            </div>
          </div>
        </div>
        '''

    instructions = '''
    <div class="onboarding">
      <h2>📖 Cómo producir este batch (workflow Web UI Gemini)</h2>
      <ol>
        <li><strong>Abre <a href="https://gemini.google.com" target="_blank">gemini.google.com</a></strong> con cualquiera de las 5 cuentas Google One PRO disponibles. Asegurate que el modelo seleccionado sea <code>Gemini 3 Pro Image</code>.</li>
        <li><strong>Por cada ad de abajo:</strong>
          <ol type="a">
            <li>Click <strong>📋 COPIAR</strong> del prompt → pega en Gemini.</li>
            <li>Drag las imágenes de la sección <strong>📎 Attachments</strong> al input de Gemini (mismo turno que el prompt).</li>
            <li>Envía. Espera la imagen.</li>
            <li><strong>Iterá si no quedó perfecta:</strong> "Cambia X manteniendo todo lo demás" — máximo 3-4 turnos. Si después de 5 iters no convence, mensaje a Claude para reformular el prompt.</li>
            <li>Score visual mental (texture / lighting / anatomy / typography / cohesion = X/10). Brain pide promedio ≥8 (≥9 si tiene cara humana realista).</li>
            <li><strong>Quita la watermark</strong> de Gemini (esquina inferior derecha) en cualquier editor (Photoshop, Canva, Photopea).</li>
            <li>Guarda como <code>FINAL/{ad_code}.png</code> en este folder. Ejemplo: <code>FINAL/LF-066_FITMAX_2PACK_OFFER_PURO.png</code>.</li>
            <li>Mensaje a Claude: <code>"LF-066 listo iter 3 score 8.5"</code> (con score) o solo <code>"LF-066 listo"</code>. Claude appendeará el bloque B en BATCH_LOG.</li>
          </ol>
        </li>
        <li>Cuando todos los ads estén con FINAL completo, mensaje a Claude: <strong>"batch listo, sube a Meta"</strong>. Claude maneja el resto (validación pricing, upload Meta API, activación cascade, recap PDF).</li>
      </ol>

      <h3>🚨 Reglas duras (NO romper)</h3>
      <ul>
        <li><strong>Identity Lock:</strong> si el prompt menciona <em>"Lupita_identity.webp"</em> o reference de persona, el attachment ES obligatorio. Si Gemini cambia la cara, abandona la chain y reinicia.</li>
        <li><strong>Texto en imagen:</strong> Gemini a veces pone texto en inglés o decora con sparkles/símbolos. Si pasa, regenera (no es aceptable).</li>
        <li><strong>Watermark:</strong> SIEMPRE quitar antes de mover a FINAL/.</li>
        <li><strong>Naming:</strong> el archivo en FINAL/ debe llamarse <code>{ad_code}.png</code> exacto (sin <code>v1</code>, sin <code>final</code>, sin nada extra). El sistema busca por ese nombre.</li>
      </ul>

      <h3>❓ FAQ rápido</h3>
      <ul>
        <li><strong>¿Y si Gemini me da error de quota?</strong> Cambia a otra cuenta Google One PRO (tienes 5).</li>
        <li><strong>¿Y si 5+ iters y no me gusta?</strong> No te frustres. Mensaje a Claude — quizás el prompt necesita reescribirse (como pasó con LF-063 v1→v2).</li>
        <li><strong>¿Y si decido no producir un ad?</strong> Mensaje a Claude: <code>"LF-XXX no me gustó, drop"</code>. Se marca DROPPED y se sale del batch.</li>
      </ul>
    </div>
    '''

    css = '''
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, 'Inter', sans-serif; background: linear-gradient(180deg, #0E0B1F 0%, #1A1438 100%); color: #E8E4F5; min-height: 100vh; padding: 24px; line-height: 1.55; }
    .container { max-width: 1280px; margin: 0 auto; }
    .header { padding: 24px 28px; background: rgba(107, 79, 187, 0.12); border: 1px solid rgba(107, 79, 187, 0.35); border-radius: 16px; margin-bottom: 24px; }
    .header h1 { font-size: 26px; font-weight: 800; background: linear-gradient(90deg, #B8A2F5 0%, #E8E4F5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header .meta { margin-top: 6px; font-size: 13px; color: #9E94C7; }
    .header .stats { display: flex; gap: 14px; margin-top: 14px; flex-wrap: wrap; }
    .header .stat { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 7px 12px; border-radius: 8px; font-size: 12px; }
    .header .stat strong { color: #B8A2F5; }
    .onboarding { background: rgba(20, 50, 80, 0.18); border-left: 3px solid #4FA8E8; border-radius: 8px; padding: 22px; margin-bottom: 24px; font-size: 13.5px; }
    .onboarding h2 { font-size: 18px; color: #C9DEEC; margin-bottom: 12px; }
    .onboarding h3 { font-size: 14px; color: #C9DEEC; margin: 16px 0 6px; text-transform: uppercase; letter-spacing: 0.6px; }
    .onboarding ol, .onboarding ul { margin-left: 22px; }
    .onboarding li { margin-bottom: 4px; }
    .onboarding code { background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 3px; font-size: 12px; font-family: 'SF Mono', Monaco, monospace; }
    .onboarding a { color: #B8A2F5; text-decoration: none; border-bottom: 1px dotted; }
    .ad-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; overflow: hidden; margin-bottom: 22px; }
    .ad-card[data-status="DROPPED"] { opacity: 0.5; }
    .ad-card[data-status="READY_FOR_UPLOAD"], .ad-card[data-status="UPLOADED_PAUSED"], .ad-card[data-status="ACTIVE"] { border-color: rgba(20, 90, 60, 0.5); }
    .ad-header { padding: 16px 22px; background: rgba(0,0,0,0.18); display: flex; gap: 12px; align-items: center; flex-wrap: wrap; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .ad-num { font-family: 'SF Mono', Monaco, monospace; color: #6B4FBB; font-weight: 800; font-size: 18px; min-width: 28px; }
    .ad-code { font-family: 'SF Mono', Monaco, monospace; font-weight: 700; color: #E8E4F5; }
    .badge { padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }
    .badge-bucket { background: rgba(107, 79, 187, 0.3); color: #D6C8FF; }
    .badge-completed { background: rgba(20, 90, 60, 0.4); color: #A7D9BD; margin-left: auto; }
    .badge-pending { background: rgba(180, 130, 50, 0.4); color: #E8C580; margin-left: auto; }
    .badge-dropped { background: rgba(180, 60, 60, 0.4); color: #E8A0A0; margin-left: auto; }
    .ad-body { display: grid; grid-template-columns: 1fr 1.2fr; gap: 24px; padding: 20px 22px; }
    @media (max-width: 980px) { .ad-body { grid-template-columns: 1fr; } }
    .left h4, .right h4 { color: #9E94C7; font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px; margin: 14px 0 6px; }
    .left h4:first-child { margin-top: 0; }
    .left p { color: #C8C0E5; font-size: 13px; margin-bottom: 4px; }
    .copy-block p { font-size: 12px; padding-left: 8px; border-left: 2px solid rgba(255,255,255,0.1); }
    .attachments { display: flex; gap: 8px; flex-wrap: wrap; }
    .attach { width: 80px; }
    .attach img { width: 80px; height: 80px; object-fit: cover; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); }
    .attach-name { font-size: 9px; color: #9E94C7; text-align: center; margin-top: 2px; word-break: break-all; }
    .final-preview { margin-top: 16px; }
    .final-preview img { max-width: 200px; border: 2px solid #0E5A3A; border-radius: 6px; }
    .prompt-block { position: relative; }
    .copy-btn { position: absolute; top: 0; right: 0; background: #6B4FBB; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; letter-spacing: 0.5px; }
    .copy-btn:hover { background: #8167D9; }
    .copy-btn.copied { background: #0E5A3A; }
    pre { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06); padding: 14px; border-radius: 8px; font-family: 'SF Mono', Monaco, monospace; font-size: 11.5px; color: #C8C0E5; white-space: pre-wrap; word-break: break-word; max-height: 380px; overflow-y: auto; margin-top: 8px; }
    '''

    js = '''
    document.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-target');
        const text = document.getElementById(id).innerText;
        navigator.clipboard.writeText(text).then(() => {
          btn.classList.add('copied');
          btn.textContent = '✓ COPIADO';
          setTimeout(() => { btn.classList.remove('copied'); btn.textContent = '📋 COPIAR'; }, 1800);
        });
      });
    });
    '''

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{batch_id} · Web UI Producer</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{batch_id} · Web UI Producer</h1>
    <div class="meta">Cliente: <strong>{client}</strong> · {n_ads} ads · Modelo: Gemini 3 Pro Image (Web UI)</div>
    <div class="stats">
      <span class="stat">Total: <strong>{n_ads}</strong></span>
      <span class="stat" style="color:#A7D9BD">Completados: <strong>{n_completed}</strong></span>
      <span class="stat" style="color:#E8C580">Pendientes: <strong>{n_pending}</strong></span>
      <span class="stat" style="color:#E8A0A0">Dropped: <strong>{n_dropped}</strong></span>
    </div>
  </div>
  {instructions}
  {cards_html}
</div>
<script>{js}</script>
</body>
</html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    args = ap.parse_args()
    batch_dir = Path(args.batch_dir).expanduser().resolve()
    if not (batch_dir / "batch.json").exists():
        sys.exit(f"❌ No batch.json en {batch_dir}")
    html = build_dashboard(batch_dir)
    out = batch_dir / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard generado: {out}")
    print(f"   Sirvelo con: python3 scripts/serve_dashboard.py {batch_dir}")


if __name__ == "__main__":
    main()
