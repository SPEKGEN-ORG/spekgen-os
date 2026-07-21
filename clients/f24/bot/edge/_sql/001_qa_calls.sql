-- 001_qa_calls.sql — QA obligatorio + registro de llamadas para los paneles F24.
--
-- Proyecto Supabase: wjlwpfaogjpeqgyxxnwa (compartido F24 + Healthy Chuchos).
-- Aplicar con: python clients/f24/bot/edge/apply_sql.py 001_qa_calls.sql
--
-- POR QUÉ ESTO EXISTE: el QA del bot se guardaba como NOTA de contacto en GHL, y
-- GHL no deja contar notas en bloque. Sin una tabla, Sergio no puede saber cuántas
-- revisiones debe cada rep. Todo lo nuevo vive en Supabase porque la org de Make
-- agotó sus 10,000 operaciones el 2026-07-19 y apagó todo sin avisar.

-- ─────────────────────────────────────────────────────────────────────────────
-- Log de actividad del rep: QA del bot + llamadas. Append-only, nunca se edita.
-- ─────────────────────────────────────────────────────────────────────────────
create table if not exists public.f24_rep_activity (
  id              bigint generated always as identity primary key,
  kind            text        not null check (kind in ('qa','call')),

  rep_name        text        not null,          -- 'Edgar' | 'Alfredo'
  rep_user_id     text,                          -- ghl userId
  contact_id      text        not null,
  opp_id          text,
  contact_name    text,
  phone           text,

  -- kind='qa'
  rating          text        check (rating is null or rating in ('up','down')),
  category        text,

  -- kind='call'
  call_type       text        check (call_type is null or call_type in ('proactiva','solicitada')),
  outcome         text        check (outcome is null or outcome in (
                    'no_contesto','buzon','numero_equivocado',
                    'contesto_interesado','contesto_no_interesado',
                    'pidio_cotizacion','pidio_volver_llamar',
                    'ya_compro_otro','cerro_venta')),

  comment         text,

  -- Veredicto del SLA CONGELADO al momento de escribir.
  -- Se guarda en vez de recalcularse para que el historial sea inmutable: si el
  -- rep revisó a la hora 23 esta fila dice 'a_tiempo' para siempre, aunque el
  -- cliente vuelva a escribir después y mueva last_inbound_at.
  last_inbound_at timestamptz,
  sla_due_at      timestamptz,
  sla_hours       numeric(8,2),
  sla_status      text        check (sla_status is null or sla_status in
                    ('a_tiempo','tarde','sin_referencia')),

  -- Observabilidad del dual-write (Supabase + nota en GHL)
  ghl_note_ok     boolean     not null default false,
  ghl_note_error  text,

  source          text        not null default 'panel',   -- 'panel'|'backfill'|'manual-test'
  created_at      timestamptz not null default now(),

  constraint qa_needs_rating   check (kind <> 'qa'   or rating  is not null),
  constraint call_needs_outcome check (kind <> 'call' or outcome is not null)
);

create index if not exists f24_ra_rep_kind_created
  on public.f24_rep_activity (rep_name, kind, created_at desc);
create index if not exists f24_ra_contact_kind
  on public.f24_rep_activity (contact_id, kind, created_at desc);
create index if not exists f24_ra_created
  on public.f24_rep_activity (created_at desc);

-- ─────────────────────────────────────────────────────────────────────────────
-- Estado de conversación por contacto. Lo llena conv_state_sync.py cada 30 min.
-- ─────────────────────────────────────────────────────────────────────────────
-- last_inbound_at es el dato caro: el bot SIEMPRE contesta, así que 99 de 100
-- conversaciones terminan en 'outbound' y lastMessageDirection no sirve para
-- saber cuándo habló el cliente. Hay que leer los mensajes, por eso se cachea.
create table if not exists public.f24_conversation_state (
  contact_id        text        primary key,
  conversation_id   text,
  rep_name          text,          -- atribuido por la OPORTUNIDAD, no por la conversación
  rep_user_id       text,
  contact_name      text,
  phone             text,

  last_message_at   timestamptz,
  last_message_dir  text,
  last_inbound_at   timestamptz,
  last_outbound_at  timestamptz,

  opp_open          boolean     not null default true,
  deep_scanned_at   timestamptz,
  updated_at        timestamptz not null default now()
);

create index if not exists f24_cs_rep
  on public.f24_conversation_state (rep_name) where opp_open;
create index if not exists f24_cs_inbound
  on public.f24_conversation_state (last_inbound_at desc);

-- ─────────────────────────────────────────────────────────────────────────────
-- Vista: quién debe QA ahora mismo.
-- ─────────────────────────────────────────────────────────────────────────────
-- 'vencido' = pasaron 24h desde que habló el cliente y nadie ha revisado desde
-- entonces. 'ever_qa' sirve para la métrica de COBERTURA del backlog viejo, que
-- es distinta del cumplimiento del SLA.
create or replace view public.f24_qa_due as
select
  cs.contact_id,
  cs.rep_name,
  cs.contact_name,
  cs.phone,
  cs.last_inbound_at,
  cs.last_inbound_at + interval '24 hours'          as due_at,
  q.last_qa_at,
  (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at) as needs_qa,
  (now() > cs.last_inbound_at + interval '24 hours'
     and (q.last_qa_at is null or q.last_qa_at < cs.last_inbound_at)) as vencido,
  (q.ever_qa is not null)                            as ever_qa
from public.f24_conversation_state cs
left join lateral (
  select max(a.created_at) as last_qa_at, min(a.created_at) as ever_qa
  from public.f24_rep_activity a
  where a.contact_id = cs.contact_id and a.kind = 'qa'
) q on true
where cs.opp_open and cs.last_inbound_at is not null;

-- ─────────────────────────────────────────────────────────────────────────────
-- RLS: sin policies a propósito. Solo service_role (las edge functions) entra.
-- La anon key NO debe poder leer ni escribir: estos datos alimentan una
-- evaluación de desempeño de los reps.
-- ─────────────────────────────────────────────────────────────────────────────
alter table public.f24_rep_activity       enable row level security;
alter table public.f24_conversation_state enable row level security;
