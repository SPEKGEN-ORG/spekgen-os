---
name: Japan Sprint — Key Decisions
description: Decisions made April 1 for the 30-day autonomy sprint before Japan trip. Make.com upgrade, Meta API scheduling, GR checkout works.
type: project
---

Decisiones acumuladas para el sprint de autonomia pre-Japon:

### Decisiones 2026-04-02

8. **Cloud Environment** → Pieza central para Japón. Migrar a `claude-code-default` (incluido en Max Plan). Prueba completa semana 2-7 abril.
9. **WiFi en Japón** → Gibran SÍ tendrá WiFi mínimo. Arquitectura cambia de "zero touch" a "minimal touch via cloud". Sesiones cortas desde móvil para aprobar/ajustar.
10. **Make.com reposicionado** → Rol de "pegamento" entre servicios, no pieza central. Para conexiones simples sin código. Stack principal: Claude Code Cloud + Meta API + GHL.
11. **SSH/servidor propio** → Descartado. Cloud environment ya incluido en plan, sin costo adicional, menos mantenimiento.

### Decisiones 2026-04-01

1. **Make.com** → Upgrade a Core ($10 USD/mes). Para automaciones que Meta no cubre (ad rotation, monitoring, crons)
2. **Publicacion posts** → Meta API scheduling via app de developers (ya tiene permisos). NO depender de Make para esto
3. **GR checkout** → FUNCIONA. Confirmado. Desbloquea produccion de ads
4. **MG sales closer** → Alguien mas lo hara. No depende de Gibran
5. **@gibran.alonzo.ecom** → Pre-agendar todo. No pausar
6. **Comunicacion clientes** → NO notificar viaje. El sistema debe funcionar transparentemente

7. **Meta App ownership** → RESUELTO. Creamos nueva app "SPEKGEN Agency API" (1465486404956665) en Agencia BM. Token SPEKGENAUTOADS regenerado con 16 permisos, sin caducidad. Verificado: pages, ad accounts, IG accounts. .env de HC y GR actualizados. App anterior (SpekGen Marketing API) deprecada.

**Why:** Gibran vuela a Japon ~30 abril, sin WiFi 21 dias. Todo debe estar autonomo.

**How to apply:**
- Meta API scheduling es la via principal para publicacion (no Make)
- Make.com para: ad rotation, monitoring, content hub crons
- GR ya puede recibir ads — producir contenido de alto margen (Orgon Protein, Colageno, Creatine)
- No crear dependencias de Gibran para MG sales
- Sprint plan completo en: `SPK - SPEKGEN AGENCY/SPK - 00. COMMAND CENTER/JAPAN_AUTONOMY_SPRINT.md`
