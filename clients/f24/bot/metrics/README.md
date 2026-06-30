# F24 Follow-up Metrics

Monitor de desempeño de los follow-ups de re-engagement de Ferre24. Mide, por **etapa** y
**variante** de mensaje, el `seen rate` (visto azul de WhatsApp), el `reply rate` (% que respondió
dentro de 7 días) y los contactos reactivados. Es la base del **A/B test** de plantillas.

## Correr local

```bash
cd clients/f24/bot
python3 metrics/f24_followup_metrics.py --days 30 \
  --env-file "/ruta/F24- FERRE24/.env"   # toma GHL_API_KEY de ahí
```

Output: `metrics/out/followup_metrics_<fecha>.{json,html}` (gitignored). El HTML es un dashboard
oscuro listo para abrir o mandar por correo.

## En la nube

`.github/workflows/f24_followup_metrics.yml` corre cada 3 días (9am CDMX) con el secret
`F24_GHL_API_KEY`, manda el reporte HTML por correo a Gibran y lo sube como artifact. Dispara manual
con `workflow_dispatch` (input opcional `days`).

## Cómo clasifica

`SIGNATURES` mapea substrings estables del copy de cada follow-up → (etapa, variante). Incluye el copy
**viejo** y el **nuevo** (post v2.6) para no perder histórico y poder comparar variantes en el A/B.
Cuando se agregue una variante nueva de plantilla, registrar su firma ahí.

## Etapas

- `etapa2` (2h), `etapa3` (~22.5h) → nudges de **fase libre** (texto, editables en
  `scenario_builders/build_f24_followup_blueprint.py`).
- `d3`, `d8`, `d18` → **plantillas Meta** aprobadas (copy registrado en Meta; cambiarlo = re-aprobación).
