-- 005_products_interest.sql — guarda el PRODUCTO DE INTERÉS (SKU) por lead.
--
-- Hoy el bot extrae products_mentioned en cada turno y lo TIRA (solo lo usa para
-- decidir la etapa). Sin eso no se puede reactivar un lead frío cuando su
-- producto entra en promoción. Aquí lo acumulamos por contacto.
--
-- El SKU ya llega a f24-opp-track (campo `products`); solo faltaba guardarlo.
-- Se usa un array + una RPC de UNIÓN atómica para no pisar lo que ya había
-- (cada turno trae los SKUs de ESE mensaje; se acumulan sin duplicar).

alter table public.f24_conversation_state
  add column if not exists products_interest       text[] not null default '{}',
  add column if not exists products_interest_at     timestamptz;

-- Unión atómica: agrega SKUs nuevos al array del contacto sin duplicar y sin
-- read-modify-write desde la edge function (evita carreras entre turnos).
create or replace function public.f24_add_products(p_contact text, p_skus text[])
returns void
language sql
as $$
  update public.f24_conversation_state
     set products_interest = (
           select array(
             select distinct trim(e)
             from unnest(coalesce(products_interest, '{}') || p_skus) as e
             where trim(e) <> ''
           )
         ),
         products_interest_at = now()
   where contact_id = p_contact;
$$;

-- Índice GIN para "¿qué leads tienen el SKU X?" (la consulta del blast de promos).
create index if not exists f24_cs_products
  on public.f24_conversation_state using gin (products_interest);
