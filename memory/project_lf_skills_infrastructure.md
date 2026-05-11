---
name: LF Skills Infrastructure (2026-05-06)
description: Dos skills nuevas para operación 100% autónoma media buying LF — /lf-media-buying-cycle v0.2 + /factory-batch v3 refactor
type: project
originSessionId: 55420f07-94ea-4818-a2df-5056f11e2f2e
---
## Skills creadas/refactoreadas 2026-05-06

### `/lf-media-buying-cycle` v0.2 (NUEVA — operation-only, LF-first)

Path: `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/PERSONALIZADAS/lf-media-buying-cycle/`

Estructura:
```
SKILL.md       ← Frontmatter + cuándo invocar + dispatch
README.md      ← Estado + roadmap
workflows/     ← 9 procedimientos documentados
  01_weekly_audit.md     (Lunes — audit cuenta + decisiones)
  02_voc_mining.md       (Martes — PDAs frescos GHL+comments)
  03_brief_batch.md      (Miércoles — brief 6-8 ads)
  04_qa_pre_upload.md    (Jueves — QA visual + COFEPRIS)
  05_friday_upload.md    (Viernes — upload Meta + cascade)
  06_pull_72h.md         (3d post-batch — Layer 1)
  07_pull_7d.md          (7d post-batch — Layer 2 graduate/iterate/kill)
  08_send_report.md      (cada 3d — email Japan-proof Gibran)
  09_monthly_plan.md     (primer lunes mes — 30 ads mapeados)
scripts/
  pull_meta_metrics.py   ← Meta API metrics + verdict Layer 1
```

Cada workflow `.md` documenta: trigger, pre-flight reads obligatorios, procedimiento step-by-step, edge cases, output esperado.

**Activación:** invocable como `/lf-media-buying-cycle` después del próximo SessionStart (hook symlinkea a ~/.claude/skills/).

### `/factory-batch` v3 (REFACTOR — production-only)

Path: `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/factory-batch/`

Cambios v2→v3 en CHANGELOG.md:
- 100% Web UI (drop API → `_archive/generate_images.py.v2`)
- Drop cost tracker (sin API = sin costo)
- Pricing pre-flight obligatorio integrado a `validate_batch.py --pricing-check`
- `generate_batch_log.py` NUEVO — genera BATCH_LOG.md programáticamente
- `generate_dashboard.py` NUEVO — dashboard.html con onboarding embedded para human-runner
- `build_recap_pdf.py` consolidado — HTML+Playwright matrix style canónico
- `_buckets/LF.json` — per-client bucket taxonomy + adset/campaign IDs + pricing mechanic + calibración
- `init_batch.py` auto-llama `generate_dashboard.py` al final
- Workflow simplificado de 8 fases v2 → 5 fases v3

## Reparto de responsabilidades

| Skill | Scope | Quien usa |
|---|---|---|
| `/factory-batch` v3 | Producción de creativos (init batch + generación Web UI + finalize selección + recap) | Claude operator + Gibran/team-member para Web UI |
| `/lf-media-buying-cycle` v0.2 | Operación cuenta (audit + decisiones + upload + monitoring + reporting) | Claude operator only |

NO overlap. `/factory-batch` termina en "batch ready para upload"; `/lf-media-buying-cycle` workflow 05 toma el handoff.

## Pendiente sesión dedicada

GH Actions cron Japan-proof (~2h):
- Crear/usar repo Spekgen-ops
- 4 workflow YAML (lf-monday-audit, lf-thursday-72h, lf-monday-7d, lf-3day-report)
- Python wrappers que invoquen los workflows del skill
- Email config Gmail SMTP + secrets
- Test runs

Sin esto, los workflows 06/07/08 se corren manualmente (sigue funcionando, solo no es Japan-proof).
