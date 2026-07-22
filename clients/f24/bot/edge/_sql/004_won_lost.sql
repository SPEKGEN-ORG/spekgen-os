-- 004_won_lost.sql — botones Ganada / Perdida desde el panel del rep.
--
-- El vendedor ya puede registrar QA y llamadas; faltaba CERRAR la oportunidad.
-- won: cerró la venta (Shopify → el valor lo pone el webhook; Efectivo/Transfer
--      → el rep teclea el VALOR DE VENTA, mismo campo que usa comisiones).
-- lost: el lead se murió, con candados (llamada + 18 días) verificados server-side.
--
-- Reusa f24_rep_activity (mismo doble-write Supabase + nota GHL). Se agregan 3
-- columnas y se amplía el CHECK de kind.

alter table public.f24_rep_activity
  add column if not exists close_method text
    check (close_method is null or close_method in ('shopify','cash')),
  add column if not exists lost_reason  text,
  add column if not exists sale_value   numeric(12,2);

-- Ampliar kind. El CHECK inline viejo (f24_rep_activity_kind_check) solo permite
-- qa|call; hay que TIRARLO, no basta con agregar otro (se AND-earían y won/lost
-- seguiría fallando el viejo).
alter table public.f24_rep_activity drop constraint if exists f24_rep_activity_kind_check;
alter table public.f24_rep_activity
  add constraint f24_rep_activity_kind_check
  check (kind in ('qa','call','won','lost'));

-- won requiere método de cierre; won+cash requiere valor > 0; lost requiere motivo.
alter table public.f24_rep_activity drop constraint if exists won_needs_method;
alter table public.f24_rep_activity
  add constraint won_needs_method
  check (kind <> 'won' or close_method is not null);

alter table public.f24_rep_activity drop constraint if exists won_cash_needs_value;
alter table public.f24_rep_activity
  add constraint won_cash_needs_value
  check (kind <> 'won' or close_method <> 'cash' or (sale_value is not null and sale_value > 0));

alter table public.f24_rep_activity drop constraint if exists lost_needs_reason;
alter table public.f24_rep_activity
  add constraint lost_needs_reason
  check (kind <> 'lost' or lost_reason is not null);
