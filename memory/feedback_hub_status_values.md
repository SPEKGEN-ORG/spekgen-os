---
name: Content Hub v2 status values (exact strings)
description: Los status values del portal v2 son strings específicos en inglés — schema no tiene enum, fácil equivocarse
type: feedback
---

El portal del Content Hub v2 (spekgen-hub, `components/portal/portal-client.tsx`) filtra posts por status con estos valores EXACTOS:

- `review` — aparece en tab "Pendientes de revisión"
- `approved` — aparece en "Aprobados"
- `scheduled` — también aparece en "Aprobados" (ya agendado para publicar)
- `published` — aparece en "Publicados"
- `draft` — no visible en portal cliente (default del schema)

**Why:** El schema SQL (`v2_posts.status`) es un `text` libre con `default 'draft'` — no hay enum ni CHECK constraint, así que Supabase acepta cualquier string (ej: "revision", "revisión", "pending") sin error, pero el portal no los renderiza en ningún tab porque los filtros son `===` estrictos.

**How to apply:**
- Al crear un post nuevo para revisión del cliente, SIEMPRE usar `status: "review"` (inglés, sin acento, sin "n" al final).
- Al aprobar: `approved`. Al publicar: `published`.
- Cost: sesión HC-012 2026-04-10 puse `"revision"` y el portal lo mostró como "0 pendientes"; Gibran tuvo que señalarlo.
