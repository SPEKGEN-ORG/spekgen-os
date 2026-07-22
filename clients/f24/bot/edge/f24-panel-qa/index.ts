// f24-panel-qa — Edge Function (Deno). Lo que LEEN los paneles: cola de QA del
// rep y marcador de cumplimiento para Sergio.
//
// Dos modos:
//   GET ?rep=Edgar                        → panel del vendedor
//   GET ?scope=manager&period=hoy|7d|30d  → panel de Sergio
//
// Solo lectura. Los datos salen de f24_qa_due (vista con el corte de arranque) y
// de f24_rep_activity. Cero operaciones de Make.
//
// NUNCA devuelve datos de GHL ni nombres/teléfonos de contactos que el panel no
// tenga ya: solo agregados e ids que el rep ya recibió del endpoint de Make.
const SB_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SB_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const ALLOWED_ORIGIN = "https://ferre24.com.mx";
const VERSION = 1;

const SB_H = { apikey: SB_KEY, Authorization: `Bearer ${SB_KEY}`, Accept: "application/json" };
const CORS = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "content-type",
  Vary: "Origin",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...CORS },
  });
}

async function sb(path: string): Promise<any[]> {
  const r = await fetch(`${SB_URL}/rest/v1/${path}`, { headers: SB_H });
  if (!r.ok) throw new Error(`supabase ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return await r.json();
}

const PERIODS: Record<string, number> = { hoy: 0, "7d": 7, "30d": 30 };

function sinceIso(period: string): string {
  const d = new Date();
  if (period === "hoy") {
    // "Hoy" en hora de México (UTC-6), no UTC: si no, a las 6pm MX ya cambió el día.
    const mx = new Date(d.getTime() - 6 * 3_600_000);
    mx.setUTCHours(0, 0, 0, 0);
    return new Date(mx.getTime() + 6 * 3_600_000).toISOString();
  }
  return new Date(d.getTime() - (PERIODS[period] ?? 7) * 86_400_000).toISOString();
}

// Minutos desde la última corrida del sync. Es lo que distingue "no debe nada"
// de "el sync lleva 3 días muerto". Sin esto, un tablero en ceros miente.
async function freshMin(): Promise<number | null> {
  const r = await sb("f24_conversation_state?select=updated_at&order=updated_at.desc&limit=1");
  if (!r.length || !r[0].updated_at) return null;
  return Math.round((Date.now() - new Date(r[0].updated_at).getTime()) / 60_000);
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method !== "GET") return json({ ok: false, error: "method_not_allowed" }, 405);

  const t0 = Date.now();
  const u = new URL(req.url);
  const scope = u.searchParams.get("scope") ?? "";
  const rep = (u.searchParams.get("rep") ?? "").trim();
  const period = u.searchParams.get("period") ?? "7d";

  try {
    const fresh = await freshMin();

    // ── modo SERGIO ────────────────────────────────────────────────────────
    if (scope === "manager") {
      const since = sinceIso(period);
      const due = await sb("f24_qa_due?select=rep_name,needs_qa,vencido,por_vencer,es_backlog,ever_qa");
      const acts = await sb(
        `f24_rep_activity?select=rep_name,kind,outcome,call_type,sla_status&created_at=gte.${since}`,
      );

      const names = new Set<string>();
      for (const d of due) if (d.rep_name) names.add(d.rep_name);
      for (const a of acts) if (a.rep_name) names.add(a.rep_name);

      const reps = [...names].sort().map((name) => {
        const d = due.filter((x) => x.rep_name === name);
        const a = acts.filter((x) => x.rep_name === name);
        const qa = a.filter((x) => x.kind === "qa");
        const calls = a.filter((x) => x.kind === "call");
        const aTiempo = qa.filter((x) => x.sla_status === "a_tiempo").length;
        const tarde = qa.filter((x) => x.sla_status === "tarde").length;
        const conSla = aTiempo + tarde;
        // Cobertura = del stock abierto, cuántos han tenido QA alguna vez.
        // Es OTRA cosa que el cumplimiento del SLA: un rep puede ir al 100% del
        // proceso nuevo y seguir con un hoyo histórico enorme.
        const backlog = d.filter((x) => x.es_backlog).length;
        const backlogSinQa = d.filter((x) => x.es_backlog && !x.ever_qa).length;
        const outcomes: Record<string, number> = {};
        for (const c of calls) if (c.outcome) outcomes[c.outcome] = (outcomes[c.outcome] ?? 0) + 1;
        return {
          rep: name,
          qa_hechos: qa.length,
          qa_a_tiempo: aTiempo,
          qa_tarde: tarde,
          sla_pct: conSla ? Math.round((aTiempo / conSla) * 100) : null,
          qa_vencidos_ahora: d.filter((x) => x.vencido).length,
          qa_por_vencer_ahora: d.filter((x) => x.por_vencer).length,
          backlog,
          backlog_sin_qa: backlogSinQa,
          cobertura_pct: backlog ? Math.round(((backlog - backlogSinQa) / backlog) * 100) : null,
          llamadas: calls.length,
          llamadas_proactivas: calls.filter((x) => x.call_type === "proactiva").length,
          llamadas_solicitadas: calls.filter((x) => x.call_type === "solicitada").length,
          outcomes,
        };
      });

      return json({
        ok: true, period, reps,
        sin_asignar: due.filter((x) => !x.rep_name).length,
        state_fresh_min: fresh, elapsed_ms: Date.now() - t0,
      });
    }

    // ── modo REP ───────────────────────────────────────────────────────────
    if (!rep) return json({ ok: false, error: "falta rep o scope=manager" }, 200);

    const due = await sb(
      `f24_qa_due?select=contact_id,last_inbound_at,due_at,needs_qa,vencido,por_vencer,es_backlog,ever_qa,last_qa_at&rep_name=eq.${encodeURIComponent(rep)}`,
    );
    const since7 = new Date(Date.now() - 7 * 86_400_000).toISOString();
    const acts = await sb(
      `f24_rep_activity?select=contact_id,kind,outcome,created_at&rep_name=eq.${encodeURIComponent(rep)}&created_at=gte.${since7}`,
    );
    // "¿alguna vez llamó?" SIN ventana de tiempo — para el candado de "perdida".
    // El de 7 días (acts) es para el conteo del día; un lead perdible está 18+
    // días frío, así que su llamada casi siempre cae fuera de esa ventana.
    const everCalledRows = await sb(
      `f24_rep_activity?select=contact_id&kind=eq.call&rep_name=eq.${encodeURIComponent(rep)}`,
    );
    const everCalled: Record<string, boolean> = {};
    for (const r of everCalledRows) everCalled[r.contact_id] = true;

    // Mapa contacto → estado, para que el panel pinte el badge en cada tarjeta.
    const byContact: Record<string, unknown> = {};
    for (const d of due) {
      byContact[d.contact_id] = {
        vencido: d.vencido, por_vencer: d.por_vencer, backlog: d.es_backlog,
        needs_qa: d.needs_qa, ever_qa: d.ever_qa,
        due_at: d.due_at, last_inbound_at: d.last_inbound_at, last_qa_at: d.last_qa_at,
      };
    }
    const callByContact: Record<string, unknown> = {};
    for (const a of acts) {
      if (a.kind !== "call") continue;
      const p = callByContact[a.contact_id] as any;
      if (!p || a.created_at > p.at) callByContact[a.contact_id] = { at: a.created_at, outcome: a.outcome };
    }
    const hoy = sinceIso("hoy");
    return json({
      ok: true, rep,
      resumen: {
        vencidos: due.filter((d) => d.vencido).length,
        por_vencer: due.filter((d) => d.por_vencer).length,
        backlog_sin_qa: due.filter((d) => d.es_backlog && !d.ever_qa).length,
        qa_hoy: acts.filter((a) => a.kind === "qa" && a.created_at >= hoy).length,
        llamadas_hoy: acts.filter((a) => a.kind === "call" && a.created_at >= hoy).length,
      },
      contacts: byContact,
      calls: callByContact,
      ever_called: everCalled,
      state_fresh_min: fresh, elapsed_ms: Date.now() - t0,
    });
  } catch (e) {
    console.log(`[f24-panel-qa] ERROR ${String(e).slice(0, 300)}`);
    return json({ ok: false, error: String(e).slice(0, 300), elapsed_ms: Date.now() - t0 }, 200);
  }
});
