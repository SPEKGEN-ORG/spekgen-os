---
name: No crear prompts antes de research + estilo
description: NUNCA generar Gemini prompts hasta tener product research validada, brief corregido y estilo visual definido
type: feedback
---

No crear prompts de Gemini hasta que se cumplan estos 3 pasos en orden:
1. /product-research ejecutado y datos validados
2. Brief actualizado con info correcta
3. Estilo visual seleccionado/definido

**Why:** Los prompts dependen de datos correctos del producto y del estilo visual. Crearlos antes es trabajo desechable que quema tokens innecesarios. En sesion 2026-04-03 se crearon 5 archivos de prompts (HC-006 a HC-010) que resultaron prematuros.

**How to apply:** El flujo de produccion de posts es: Calendar → Product Research → Brief → Estilo → Prompts → Generacion. Nunca saltar pasos. Los briefs SI se pueden crear temprano (con la info del calendario), pero los prompts NO.
