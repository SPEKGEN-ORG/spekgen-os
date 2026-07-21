-- 003_excluir_pruebas.sql — saca los contactos de PRUEBA de la cola de QA.
--
-- El smoke test de CI le escribe al bot con un contacto "ZZ Smoke CI-…". Como
-- el bot lo atiende, f24-opp-track le anota last_inbound_at igual que a un
-- cliente real, y el contacto acababa apareciendo en la cola de QA del vendedor
-- como un pendiente que no existe. Cada corrida de CI generaba uno nuevo.
--
-- Los humanos de prueba (Sergio, Gibran, Pedro, Edgar…) se manejan aparte: hoy
-- caen del lado del backlog por el corte de arranque, pero si alguno vuelve a
-- escribir después del arranque va a entrar a la cola. Cuando estorbe, la
-- solución es la misma que aquí: excluirlos por id.

drop view if exists public.f24_qa_due;

create view public.f24_qa_due as
with cfg as (select timestamptz '2026-07-20 00:00:00-06' as go_live)   -- GO_LIVE (hora MX)
select
  cs.contact_id,
  cs.rep_name,
  cs.contact_name,
  cs.phone,
  cs.last_inbound_at,
  cs.last_inbound_at + interval '24 hours' as due_at,
  q.last_qa_at,
  (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at) as needs_qa,
  (cs.last_inbound_at < (select go_live from cfg))            as es_backlog,
  (cs.last_inbound_at >= (select go_live from cfg)
     and now() > cs.last_inbound_at + interval '24 hours'
     and (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at)) as vencido,
  (cs.last_inbound_at >= (select go_live from cfg)
     and now() <= cs.last_inbound_at + interval '24 hours'
     and (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at)) as por_vencer,
  (q.ever_qa is not null) as ever_qa
from public.f24_conversation_state cs
left join lateral (
  select max(a.created_at) as last_qa_at, min(a.created_at) as ever_qa
  from public.f24_rep_activity a
  where a.contact_id = cs.contact_id and a.kind = 'qa'
) q on true
where cs.opp_open
  and cs.last_inbound_at is not null
  -- fuera los contactos sintéticos del smoke test de CI
  and coalesce(cs.contact_name, '') !~* '^zz\s*smoke'
  and coalesce(cs.contact_name, '') !~* 'smoke.?test';
