---
name: content-planner
description: >
  Genera parrilla mensual de contenido orgánico para cualquier cliente SPEKGEN.
  Usa pilares, productos, winners previos, ángulos creativos del Content Hub,
  y el framework Hormozi SPCL por cliente. Produce un plan de 30 piezas/mes
  (clientes) o 60 piezas/mes (SPEKGEN @gibran.alonzo.ecom).
  Activate for: "genera la parrilla", "plan de contenido", "parrilla del mes",
  "content plan de [CLIENTE]", "qué publicamos este mes", "planea el contenido",
  "parrilla de spekgen", "contenido de gibran",
  or any request to plan organic content for a client.
---

## Base Paths

```
CLIENTS_BASE   = mnt/CLIENTS
CONTENT_HUB    = {CLIENTS_BASE}/SPK - SPEKGEN AGENCY/SPK - 09. LOGS/02. CONTENT HUB/SPEKGEN_CONTENT_HUB_v1.0.xlsx
AD_LOG         = {CLIENTS_BASE}/SPK - SPEKGEN AGENCY/SPK - 09. LOGS/00. ADS LOG/SPEKGEN_CLIENTS_AD_LOG_v2.0.xlsx
```

---

## Workflow — Steps In Order

### STEP 1 — Identify Client & Month

1. Ask Gibran which client (LO FITNESS, GREENRAY, HEALTHY CHUCHOS, METAGREEN, SPEKGEN)
   - **SPEKGEN** = @gibran.alonzo.ecom personal brand. 60 piezas/mes. Tone: first-person Gibran.
   - All other clients = business accounts. 30 piezas/mes.
2. Ask target month (default: next month)
3. Read the client's `_CLIENT_CONTEXT.md` for products, pilares, and current state
4. Read the client's `hormozi_spcl.json` (if exists) from `{CLIENT}/11. STRATEGY/` for SPCL framework

### STEP 2 — Read Content Hub State

1. Open `SPEKGEN_CONTENT_HUB_v1.0.xlsx`
2. Go to the client's CONTENT sheet (📱 [CLIENTE] CONTENT)
3. Read `🎯 PILARES & ESTRATEGIA` for the client's pilar distribution
4. Read `🏆 WINNERS PIPELINE` for validated concepts to replicate
5. Read `📦 ASSET INVENTORY` for available assets

### STEP 3 — Read AD LOG for Paid Insights

1. Open AD LOG, go to client's ADS sheet
2. Identify top-performing ads (by ROAS, CTR)
3. Note products, angles, and hooks that work in paid → candidates for organic adaptation

### STEP 4 — Generate Monthly Grid

**Distribution per month — Standard (30/month, all clients except SPEKGEN):**

| Formato | Cantidad | Frecuencia |
|---------|----------|------------|
| Carrusel | 8 | 2/semana |
| Reel | 12 | 3/semana |
| Post Estático | 4 | 1/semana |
| Story | 4 | 1/semana |
| Caption-only | 2 | 2/mes |

**Distribution per month — SPEKGEN (60/month, @gibran.alonzo.ecom):**

| Formato | Cantidad | Frecuencia |
|---------|----------|------------|
| Carrusel | 16 | 4/semana |
| Reel | 24 | 6/semana |
| Post Estático | 8 | 2/semana |
| Story | 8 | 2/semana |
| Caption-only | 4 | 1/semana |

**Hormozi SPCL Content Ratio (if `hormozi_spcl.json` exists):**
- 70% Value-first (EDU, tips, frameworks, how-tos)
- 15% Entertainment (behind-scenes, personality, day-in-life)
- 10% Promotion (product/service showcases, offers, CTAs)
- 5% Community (polls, Q&A, user spotlights, challenges)

Tag each piece with its SPCL pillar: `S` (Status), `P` (Power), `C` (Credibility), `L` (Likeness)

**Pilar distribution:** Follow percentages from `🎯 PILARES & ESTRATEGIA`

**Product rotation rules:**
- No more than 3 pieces of the same product per month (clients)
- SPEKGEN: rotate across service categories (branding, ads, AI tools, content, web)
- At least 1 piece per product/service category
- Winners get priority for replication in alternate format

**Angle rotation:** Cycle through TAXONOMÍA angles (EdClarity, SymRit, IdentAsp, etc.)

**SPEKGEN-specific content pillars:**
- AI tools & tutorials (how Gibran uses AI daily)
- Brand building education (Hormozi-inspired frameworks)
- Client case studies & results (anonymized or with permission)
- Behind-the-scenes agency life
- Industry hot takes & trends

### STEP 5 — Fill Content Hub

For each planned piece, write to the client's CONTENT sheet:

| Column | Value |
|--------|-------|
| A: ID | Auto-increment from last ID (e.g., LF-ORG-049) |
| B: Atom ID | ATOM-[CLIENT]-XXX |
| C: Serie | Group name if applicable |
| D: Episodio | Number within serie |
| E: Fecha Planeada | Target publish date |
| H: Formato | Carrusel / Reel / Story / Estático |
| I: Pilar | EDU / SPR / PRD / LFS / ENT / TND |
| J: Funnel | TOFU / MOFU / BOFU |
| K: Producto(s) | Product name(s) |
| L: Ángulo | From TAXONOMÍA |
| S: Status | 💡 Idea |

### STEP 6 — Present to Gibran

Show a summary table:

```
PARRILLA [CLIENTE] — [MES] 2026

Semana 1: [fecha]
  📸 Carrusel — [Pilar] — [Producto] — [Ángulo] — [Hook idea]
  🎬 Reel — [Pilar] — [Producto] — [Ángulo] — [Hook idea]
  🎬 Reel — [Pilar] — [Producto] — [Ángulo] — [Hook idea]

Semana 2: ...
```

**Ask Gibran to approve or adjust before saving.**

### STEP 7 — Cross-Channel Intelligence

If there are paid winners in AD LOG that haven't been adapted to organic:
- Flag them as "Paid → Organic" candidates
- Suggest organic format and angle

If there are organic winners (SMART SCORE ≥ 7) that haven't been scaled to paid:
- Flag them as "Organic → Paid" candidates
- Suggest entering the ad production pipeline

---

## Output

- Updated Content Hub Excel with all planned pieces
- Summary markdown for Gibran's review
- Cross-channel recommendations

---

## Rules

1. NEVER modify the AD LOG — it's read-only for this skill
2. Always check for duplicate content IDs before creating new ones
3. Respect pilar percentages (±5% tolerance)
4. Every piece MUST have a product/service assigned — no "general brand" posts (SPEKGEN: assign a service category)
5. Save the Excel after every update with `wb.save()`
