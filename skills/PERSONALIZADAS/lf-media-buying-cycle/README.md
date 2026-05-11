# /lf-media-buying-cycle

> Skill de operación 100% autónoma de Meta Ads para LO FITNESS.
> Para producción de creativos: usar `/factory-batch`. Esta skill es para AUDITAR / DECIDIR / EJECUTAR / REPORTAR.

## Estado

`v0.2` — 2026-05-06 — Todos los 9 workflows documentados. Pendiente: GH Actions cron Japan-proof.

## Estructura

```
lf-media-buying-cycle/
├── SKILL.md              # Frontmatter + cuándo invocar + dispatch a workflows
├── README.md             # Este archivo
├── workflows/
│   ├── 01_weekly_audit.md      # ✅ Lunes audit
│   ├── 02_voc_mining.md        # ✅ Martes VoC
│   ├── 03_brief_batch.md       # ✅ Miércoles brief
│   ├── 04_qa_pre_upload.md     # ✅ Jueves QA
│   ├── 05_friday_upload.md     # ✅ Viernes upload+activate
│   ├── 06_pull_72h.md          # ✅ 72h post-batch
│   ├── 07_pull_7d.md           # ✅ 7d post-batch (Layer 2)
│   ├── 08_send_report.md       # ✅ cada 3d email
│   └── 09_monthly_plan.md      # ✅ primer lunes del mes
└── scripts/
    └── pull_meta_metrics.py    # ✅ Meta Marketing API metrics pull
```

## Roadmap inmediato

1. **2026-05-09 jue** — Primera ejecución real de workflow 06 (pull 72h sobre batch W1). Validar script + procedimiento.
2. **2026-05-12 lun** — Primera ejecución real de workflow 01 (weekly audit) + workflow 07 (pull 7d sobre W1).
3. **2026-05-13 mar** — Primer workflow 02 (VoC mining) + 03 (brief week 2 LF-066).
4. **2026-05-15-16 jue-vie** — Primera vuelta completa del ciclo Mon→Fri.
5. **Próxima sesión dedicada** — GH Actions cron Japan-proof (workflows 06, 07, 08, 01 automatizados).

## Cómo evolucionar

Workflows se refinan **al primer uso real**. Cada workflow tiene un "edge cases" que se va engordando con casos reales. Si un workflow predice mal lo que pasa en la realidad, su `.md` se actualiza con el aprendizaje.

## Scripts pendientes (futuros)

- `audit_account.py` — wrapper de workflow 01 que produce `LOGS/LF/AUDITS/audit_YYYY-MM-DD.md` automático
- `commit_decision.py` — append D-NNN a DECISIONS_LOG con formato fijo (templated)
- `send_report.py` — wrapper de workflow 08 que renderea HTML + envía Gmail SMTP
- `activate_cascade.py` — wrapper de workflow 05 que upload + activate cascade end-to-end
- `pull_voc.py` — wrapper de workflow 02 que pulls GHL + Meta comments + sintetiza PDAs

(Cada script es un wrapper del procedure `.md` correspondiente. El `.md` es el ground truth; el script automatiza pasos repetitivos.)

## Dependencias

- LF .env con `META_ACCESS_TOKEN`
- Brain docs en `SPK - MEDIA BUYING OPS/`
- LOGS/LF/ con CALIBRATION, DECISIONS_LOG, BATCH_LOG, AUTONOMY_RULEBOOK, MONTH_PLAN_MAY26
- Python deps: `requests`, `python-dotenv`
