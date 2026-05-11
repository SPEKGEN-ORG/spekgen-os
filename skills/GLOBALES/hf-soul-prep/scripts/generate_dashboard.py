#!/usr/bin/env python3
"""
generate_dashboard.py — Sincroniza ATTACHMENTS/ desde REFERENCE/ y genera dashboard.html.

El dashboard es la UI principal del Soul prep:
- Onboarding embebido (workflow Web UI Gemini)
- 8 cards (una por prompt) con:
  · Título + subtítulo
  · Status badge (PENDING / COMPLETED / DROPPED)
  · Thumbnails de attachments del prompt (drag a Gemini)
  · Botón COPIAR el prompt SCALIST
  · Preview del PNG de OUTPUTS/ si ya descargado
  · Score field

Uso:
    python3 generate_dashboard.py {batch_dir}

Output:
    {batch_dir}/dashboard.html
    {batch_dir}/ATTACHMENTS/0N_*/   ← poblado con copias de REFERENCE/
"""
import argparse
import json
import shutil
import sys
from html import escape as html_escape
from pathlib import Path


# ----- attachment sync -----

def sync_attachments(batch_dir: Path, batch: dict) -> dict:
    """Copy REFERENCE/* into each ATTACHMENTS/0N_*/ subfolder. Update batch['prompts'][i]['attachments']."""
    ref_dir = batch_dir / "REFERENCE"
    if not ref_dir.exists():
        return batch

    ref_files = sorted([f for f in ref_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
    if not ref_files:
        return batch

    for pr in batch["prompts"]:
        att_dir = batch_dir / f"ATTACHMENTS/{pr['num']:02d}_{pr['slug']}"
        att_dir.mkdir(parents=True, exist_ok=True)

        # Copy each REFERENCE file into the prompt's attachment dir (only if missing or older)
        for src in ref_files:
            dst = att_dir / src.name
            if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                shutil.copy2(src, dst)

        # Update batch.json with full list of attachments in this dir (any extras kept by user too)
        existing = sorted([f for f in att_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
        pr["attachments"] = [f.relative_to(batch_dir).as_posix() for f in existing]

    return batch


# ----- output detection -----

def detect_outputs(batch_dir: Path, batch: dict) -> dict:
    """For each prompt, check if OUTPUTS/0N_*.png exists; flip status to completed."""
    for pr in batch["prompts"]:
        if pr["status"] == "dropped":
            continue
        out_path = batch_dir / pr["output_filename"]
        if out_path.exists():
            pr["status"] = "completed"
        elif pr["status"] == "completed":
            # File got deleted, revert
            pr["status"] = "pending"
    return batch


# ----- dashboard render -----

def is_image(filename: str) -> bool:
    return filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))


def is_pdf(filename: str) -> bool:
    return filename.lower().endswith(".pdf")


def render_attachment(rel_path: str) -> str:
    name = Path(rel_path).name
    safe_name = html_escape(name)
    safe_path = html_escape(rel_path)
    if is_image(name):
        return f'''<div class="attach"><img src="{safe_path}" alt="{safe_name}" loading="lazy"/><div class="attach-name">{safe_name}</div></div>'''
    elif is_pdf(name):
        return f'''<div class="attach attach-pdf"><div class="pdf-icon">PDF</div><div class="attach-name"><a href="{safe_path}" target="_blank">{safe_name}</a></div></div>'''
    else:
        return f'''<div class="attach"><div class="file-icon">📎</div><div class="attach-name">{safe_name}</div></div>'''


def build_dashboard_html(batch_dir: Path, batch: dict) -> str:
    n_total = len(batch["prompts"])
    n_completed = sum(1 for p in batch["prompts"] if p["status"] == "completed")
    n_dropped = sum(1 for p in batch["prompts"] if p["status"] == "dropped")
    n_pending = n_total - n_completed - n_dropped

    soul_id = batch["training"].get("soul_id") or "—"
    cost = batch["training"].get("cost_credits") or "—"

    # Build cards
    cards_html = ""
    for pr in batch["prompts"]:
        num = pr["num"]
        slug = pr["slug"]
        title = pr["title"]
        subtitle = pr.get("subtitle", "")
        prompt_text = pr["prompt"]
        status = pr["status"]
        score = pr.get("score") or ""

        # Status badge
        if status == "completed":
            status_badge = '<span class="badge badge-completed">✓ COMPLETADO</span>'
        elif status == "dropped":
            status_badge = '<span class="badge badge-dropped">⊘ DROPPED</span>'
        else:
            status_badge = '<span class="badge badge-pending">○ PENDIENTE</span>'

        # Attachments
        attachments = pr.get("attachments", [])
        attach_html = "".join(render_attachment(a) for a in attachments) or '<em class="muted">(arrastrá refs a REFERENCE/ y regenerá)</em>'
        att_dir_rel = f"ATTACHMENTS/{num:02d}_{slug}/"

        # Final preview
        final_html = ""
        out_path = batch_dir / pr["output_filename"]
        if out_path.exists():
            rel = out_path.relative_to(batch_dir).as_posix()
            final_html = f'''
            <div class="final-preview">
              <h4>✓ FINAL descargado</h4>
              <img src="{html_escape(rel)}" alt="final"/>
            </div>'''

        score_input = f'''<input type="text" class="score-input" data-prompt-num="{num}" placeholder="Score /10" value="{html_escape(str(score))}">'''

        cards_html += f'''
        <div class="card" data-status="{status}" data-num="{num}">
          <div class="card-header">
            <span class="card-num">{num:02d}</span>
            <div class="card-title-block">
              <h3 class="card-title">{html_escape(title)}</h3>
              <div class="card-subtitle">{html_escape(subtitle)}</div>
            </div>
            {status_badge}
          </div>
          <div class="card-body">
            <div class="card-left">
              <h4>📎 Attachments para arrastrar a Gemini</h4>
              <div class="attachments-grid">{attach_html}</div>
              <div class="att-folder-hint">Carpeta lista para drag-and-drop: <code>{att_dir_rel}</code></div>

              <h4>📥 Output esperado</h4>
              <div class="output-hint"><code>{html_escape(pr["output_filename"])}</code></div>
              {final_html}

              <h4>⭐ Score (rubric ≥8/10)</h4>
              {score_input}
            </div>
            <div class="card-right">
              <div class="prompt-block">
                <h4>🎨 Prompt SCALIST <button class="copy-btn" data-target="prompt-{num}">📋 COPIAR</button></h4>
                <pre id="prompt-{num}">{html_escape(prompt_text)}</pre>
              </div>
            </div>
          </div>
        </div>
        '''

    # Onboarding section
    onboarding = '''
    <details class="onboarding" open>
      <summary><strong>📖 Cómo producir este Soul (paso a paso, ~30-45 min total)</strong></summary>
      <div class="onb-body">
        <ol>
          <li><strong>Abre <a href="https://gemini.google.com" target="_blank">gemini.google.com</a></strong> y selecciona el modelo <code>Gemini 3 Pro Image / Nano Banana Pro</code>. (Requiere Google One Pro, que la agencia ya paga.)</li>
          <li><strong>Por cada card de abajo (1 a 8):</strong>
            <ol type="a">
              <li>Click <strong>📋 COPIAR</strong> del prompt → pega en Gemini.</li>
              <li>Abre la carpeta <code>ATTACHMENTS/0N_slug/</code> que indica la card y arrastra TODOS sus archivos al input de Gemini (mismo turno que el prompt).</li>
              <li>Envía. Espera la imagen.</li>
              <li>Si no quedó perfecta: en el mismo chat, "cambia X manteniendo el resto". Máximo 3-4 iteraciones por prompt.</li>
              <li>Score visual mental (texture / lighting / typography / brand-fidelity / cohesion = X/10). Mínimo aceptable: 8/10.</li>
              <li>Descarga el PNG y guárdalo en <code>OUTPUTS/</code> con el nombre exacto que indica la card (ej. <code>01_hero_3_4.png</code>).</li>
              <li>Ingresa el score en el campo de la card. Recarga la página → status flip a ✓ COMPLETADO automáticamente.</li>
            </ol>
          </li>
          <li>Cuando los 8 estén completados (o ≥6 con score ≥8): mensaje a Claude <strong>"los 8 mockups están"</strong>. Claude ejecuta upload + Soul training en Higgsfield (Fase C).</li>
        </ol>

        <h3>🚨 Reglas duras</h3>
        <ul>
          <li><strong>Identity Lock:</strong> el prefix está embebido en cada prompt. NO lo borres al copiar.</li>
          <li><strong>Aspect ratio 1:1:</strong> Soul training requiere todas las imágenes cuadradas. Si Gemini te da otra ratio, pídele "make it square 1:1".</li>
          <li><strong>Naming exacto:</strong> el archivo en <code>OUTPUTS/</code> debe llamarse exactamente como dice la card. El sistema busca por ese filename.</li>
          <li><strong>Watermark:</strong> Gemini pone una marca de agua en la esquina inferior derecha. Quítala con Photoshop / Photopea / Canva antes de mover a OUTPUTS/.</li>
          <li><strong>Mínimo 5 outputs ≥8/10:</strong> Si menos pasan, regenerá los que fallaron antes de Soul training. Soul aprende lo que recibe — basura entra, basura sale para siempre.</li>
        </ul>

        <h3>❓ FAQ</h3>
        <ul>
          <li><strong>¿Y si Gemini me da error de quota?</strong> Cambia a otra cuenta Google One Pro disponible.</li>
          <li><strong>¿Y si después de 5 iters no me gusta?</strong> Mensaje a Claude — el prompt quizás necesita reescribirse.</li>
          <li><strong>¿Y si decido no producir un slot (ej. el #8 splash es overkill)?</strong> Mensaje a Claude: <code>"drop el #8"</code>. Se marca DROPPED y se sale del set de training.</li>
        </ul>
      </div>
    </details>
    '''

    css = '''
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, "Inter", "Segoe UI", sans-serif; background: linear-gradient(180deg, #0E0B1F 0%, #1A1438 100%); color: #E8E4F5; min-height: 100vh; padding: 24px; line-height: 1.55; }
    .container { max-width: 1320px; margin: 0 auto; }
    .header { padding: 26px 30px; background: rgba(107, 79, 187, 0.12); border: 1px solid rgba(107, 79, 187, 0.35); border-radius: 18px; margin-bottom: 24px; }
    .header h1 { font-size: 28px; font-weight: 800; background: linear-gradient(90deg, #B8A2F5 0%, #E8E4F5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header .meta { margin-top: 6px; font-size: 13px; color: #9E94C7; }
    .header .stats { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
    .header .stat { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 8px 13px; border-radius: 8px; font-size: 12px; }
    .header .stat strong { color: #B8A2F5; }
    .header .training-info { margin-top: 12px; font-size: 12px; color: #9E94C7; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06); }
    .onboarding { background: rgba(20, 50, 80, 0.18); border-left: 3px solid #4FA8E8; border-radius: 8px; padding: 18px 22px; margin-bottom: 24px; font-size: 13.5px; }
    .onboarding summary { cursor: pointer; font-size: 15px; color: #C9DEEC; padding: 4px 0; user-select: none; }
    .onboarding summary:hover { color: #E8E4F5; }
    .onb-body { padding-top: 14px; }
    .onb-body h3 { font-size: 13px; color: #C9DEEC; margin: 18px 0 6px; text-transform: uppercase; letter-spacing: 0.7px; }
    .onb-body ol, .onb-body ul { margin-left: 22px; }
    .onb-body li { margin-bottom: 4px; }
    .onb-body code { background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 3px; font-size: 12px; font-family: "SF Mono", Monaco, monospace; }
    .onb-body a { color: #B8A2F5; text-decoration: none; border-bottom: 1px dotted; }
    .onb-body strong { color: #E8E4F5; }
    .card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; overflow: hidden; margin-bottom: 22px; transition: border-color 0.2s; }
    .card[data-status="dropped"] { opacity: 0.45; }
    .card[data-status="completed"] { border-color: rgba(20, 90, 60, 0.55); }
    .card-header { padding: 16px 22px; background: rgba(0,0,0,0.18); display: flex; gap: 14px; align-items: center; flex-wrap: wrap; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .card-num { font-family: "SF Mono", Monaco, monospace; color: #6B4FBB; font-weight: 800; font-size: 22px; min-width: 32px; }
    .card-title-block { flex: 1; }
    .card-title { font-size: 16px; font-weight: 700; color: #E8E4F5; }
    .card-subtitle { font-size: 11px; color: #9E94C7; margin-top: 2px; font-style: italic; }
    .badge { padding: 4px 11px; border-radius: 5px; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; white-space: nowrap; }
    .badge-completed { background: rgba(20, 90, 60, 0.4); color: #A7D9BD; }
    .badge-pending { background: rgba(180, 130, 50, 0.4); color: #E8C580; }
    .badge-dropped { background: rgba(180, 60, 60, 0.4); color: #E8A0A0; }
    .card-body { display: grid; grid-template-columns: 1fr 1.2fr; gap: 26px; padding: 22px; }
    @media (max-width: 1000px) { .card-body { grid-template-columns: 1fr; } }
    .card-left h4, .card-right h4 { color: #9E94C7; font-size: 11px; text-transform: uppercase; letter-spacing: 1.4px; margin: 16px 0 8px; }
    .card-left h4:first-child, .card-right h4:first-child { margin-top: 0; }
    .attachments-grid { display: flex; gap: 8px; flex-wrap: wrap; }
    .attach { width: 88px; }
    .attach img { width: 88px; height: 88px; object-fit: cover; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); display: block; }
    .attach-pdf .pdf-icon { width: 88px; height: 88px; background: rgba(180, 60, 60, 0.25); border: 1px solid rgba(180, 60, 60, 0.4); border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #E8A0A0; font-weight: 700; font-size: 16px; letter-spacing: 1px; }
    .attach .file-icon { width: 88px; height: 88px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 28px; }
    .attach-name { font-size: 9.5px; color: #9E94C7; text-align: center; margin-top: 4px; word-break: break-all; line-height: 1.3; }
    .attach-name a { color: #B8A2F5; text-decoration: none; }
    .att-folder-hint { font-size: 11px; color: #9E94C7; margin-top: 8px; }
    .att-folder-hint code { background: rgba(255,255,255,0.06); padding: 2px 7px; border-radius: 3px; font-family: "SF Mono", Monaco, monospace; color: #C8C0E5; }
    .output-hint code { background: rgba(255,255,255,0.06); padding: 2px 7px; border-radius: 3px; font-family: "SF Mono", Monaco, monospace; color: #C8C0E5; font-size: 12px; }
    .final-preview { margin-top: 14px; padding: 12px; background: rgba(20, 90, 60, 0.12); border: 1px solid rgba(20, 90, 60, 0.35); border-radius: 8px; }
    .final-preview h4 { color: #A7D9BD; margin: 0 0 8px; }
    .final-preview img { max-width: 220px; max-height: 220px; border-radius: 6px; border: 1px solid rgba(20, 90, 60, 0.5); }
    .score-input { background: rgba(0,0,0,0.3); color: #E8E4F5; border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 8px 12px; font-size: 13px; width: 140px; font-family: "SF Mono", Monaco, monospace; }
    .score-input:focus { outline: none; border-color: #6B4FBB; }
    .prompt-block { position: relative; }
    .copy-btn { position: absolute; top: -3px; right: 0; background: #6B4FBB; color: white; border: none; padding: 7px 16px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; letter-spacing: 0.5px; transition: background 0.15s; }
    .copy-btn:hover { background: #8167D9; }
    .copy-btn.copied { background: #0E5A3A; }
    pre { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06); padding: 16px; border-radius: 8px; font-family: "SF Mono", Monaco, monospace; font-size: 11.5px; color: #C8C0E5; white-space: pre-wrap; word-break: break-word; max-height: 480px; overflow-y: auto; margin-top: 8px; }
    .muted { color: #6E658F; font-size: 12px; }
    .footer { text-align: center; margin-top: 30px; padding: 20px; color: #6E658F; font-size: 11px; }
    '''

    js = '''
    document.querySelectorAll(".copy-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-target");
        const text = document.getElementById(id).innerText;
        navigator.clipboard.writeText(text).then(() => {
          btn.classList.add("copied");
          btn.textContent = "✓ COPIADO";
          setTimeout(() => { btn.classList.remove("copied"); btn.textContent = "📋 COPIAR"; }, 1800);
        });
      });
    });

    // Score input -> POST to local server
    document.querySelectorAll(".score-input").forEach(inp => {
      inp.addEventListener("blur", () => {
        const num = inp.getAttribute("data-prompt-num");
        const score = inp.value.trim();
        fetch("/__update_score", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ num: parseInt(num), score: score })
        }).then(r => {
          if (r.ok) {
            inp.style.borderColor = "#0E5A3A";
            setTimeout(() => { inp.style.borderColor = ""; }, 1200);
          }
        }).catch(() => {});
      });
    });
    '''

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{html_escape(batch["batch_id"])} · Soul Prep</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{html_escape(batch["batch_id"])} · Soul Prep</h1>
    <div class="meta">Cliente: <strong>{html_escape(batch["client"])}</strong> · Sujeto: <strong>{html_escape(batch["subject_name"])}</strong> ({html_escape(batch["subject_type"])}) · Modelo: <strong>{html_escape(batch["soul_model"])}</strong></div>
    <div class="stats">
      <span class="stat">Total: <strong>{n_total}</strong></span>
      <span class="stat" style="color:#A7D9BD">Completados: <strong>{n_completed}</strong></span>
      <span class="stat" style="color:#E8C580">Pendientes: <strong>{n_pending}</strong></span>
      <span class="stat" style="color:#E8A0A0">Dropped: <strong>{n_dropped}</strong></span>
    </div>
    <div class="training-info">
      <strong>Soul ID:</strong> {html_escape(str(soul_id))} · <strong>Costo training:</strong> {html_escape(str(cost))} créditos
    </div>
  </div>
  {onboarding}
  {cards_html}
  <div class="footer">
    Generado por <code>/hf-soul-prep</code> · refrescá el browser después de descargar PNGs para ver el status actualizado
  </div>
</div>
<script>{js}</script>
</body>
</html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch_dir")
    args = ap.parse_args()
    batch_dir = Path(args.batch_dir).expanduser().resolve()
    bj = batch_dir / "batch.json"
    if not bj.exists():
        sys.exit(f"❌ batch.json no encontrado en {batch_dir}")

    batch = json.loads(bj.read_text(encoding="utf-8"))

    # Sync attachments + detect outputs
    batch = sync_attachments(batch_dir, batch)
    batch = detect_outputs(batch_dir, batch)

    # Persist updated batch.json
    bj.write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")

    # Render
    html = build_dashboard_html(batch_dir, batch)
    out = batch_dir / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard generado: {out}")
    print(f"   Sirvelo con: python3 scripts/serve_dashboard.py {batch_dir}")


if __name__ == "__main__":
    main()
