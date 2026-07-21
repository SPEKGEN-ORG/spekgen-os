-- 002_go_live.sql — separa el BACKLOG viejo del cumplimiento del SLA nuevo.
--
-- Decisión de Pedro (2026-07-20): "reloj limpio". La regla de las 24h solo aplica
-- a conversaciones donde el cliente respondió DESPUÉS del arranque. Lo de antes
-- se mide aparte como COBERTURA, y nunca se pinta como "vencido".
--
-- Por qué importa: al momento del arranque había 81 conversaciones abiertas sin
-- una sola QA (Edgar 59, Alfredo 22) y NINGUNA con respuesta del cliente de menos
-- de 24h. Sin este corte, los dos reps abren su panel el día 1 con todo en rojo
-- por trabajo anterior a la regla — y un tablero que arranca acusando es un
-- tablero al que le dejan de creer.
--
-- Para mover la fecha: cambia GO_LIVE aquí abajo y vuelve a correr este archivo.

-- DROP + CREATE, no "create or replace": esta versión agrega columnas nuevas en
-- medio y Postgres no deja reordenar/renombrar columnas de una vista existente
-- ("cannot change name of view column").
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

  -- ¿nadie ha revisado desde que habló el cliente por última vez?
  (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at) as needs_qa,

  -- BACKLOG: el cliente habló antes del arranque. Cuenta para cobertura,
  -- NUNCA para el SLA.
  (cs.last_inbound_at < (select go_live from cfg))            as es_backlog,

  -- VENCIDO: solo post-arranque y con más de 24h encima.
  (cs.last_inbound_at >= (select go_live from cfg)
     and now() > cs.last_inbound_at + interval '24 hours'
     and (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at)) as vencido,

  -- PENDIENTE: post-arranque, dentro de la ventana, todavía a tiempo.
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
where cs.opp_open and cs.last_inbound_at is not null;
