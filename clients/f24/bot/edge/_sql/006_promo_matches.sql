-- 006_promo_matches.sql — LOG de candidatos a reactivación por promo.
--
-- NO envía nada. Cada ~15 días entran promos nuevas; este log cruza los SKU en
-- promo contra el producto de interés de los leads fríos y guarda quién se
-- beneficiaría, para que Pedro lo revise y decida si vale un blast.
--
-- Clave de deduplicado: (promo_sku, contact_id, vigencia). Dentro del MISMO
-- ciclo de promo un lead+SKU se registra una vez; cuando entra una promo nueva
-- (otra vigencia) se vuelve a registrar (es otra oportunidad).

create table if not exists public.f24_promo_matches (
  id             bigint generated always as identity primary key,
  run_at         timestamptz not null default now(),

  promo_sku      text        not null,
  producto       text,
  regular_price  numeric(12,2),
  promo_price    numeric(12,2),
  pct_desc       text,
  vigencia       text,                     -- fin de la promo (define el ciclo)

  contact_id     text        not null,
  rep_name       text,
  contact_name   text,
  phone          text,
  cold_days      int,                      -- días sin respuesta del cliente
  lead_breadth   int,                      -- # de SKUs que le interesan (browser vs focalizado)

  notified       boolean     not null default false,  -- futuro: el blast marca true
  notified_at    timestamptz,

  unique (promo_sku, contact_id, vigencia)
);

create index if not exists f24_pm_run   on public.f24_promo_matches (run_at desc);
create index if not exists f24_pm_notif on public.f24_promo_matches (notified) where not notified;

alter table public.f24_promo_matches enable row level security;  -- solo service_role
