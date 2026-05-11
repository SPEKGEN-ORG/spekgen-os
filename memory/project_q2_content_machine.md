---
name: SPEKGEN Q2 Content Machine Strategy
description: Q2 2026 shift from paid-ads-first to organic-content-first. 180 pieces/month across 5 brands. Hormozi-inspired. Best performers graduate to paid.
type: project
---

## Strategy
SPEKGEN Q2 shifts from paid-ads-first to **organic-content-first**. Each brand produces high-volume organic posts. Best performers graduate to paid ads monthly.

**Why:** Hormozi framework — content volume is king (35K pieces → 3B impressions), content IS the targeting, brand = deliberate pairing through outcomes. Organic acts as sandbox → best performers → paid.

**How to apply:** Every content decision should prioritize volume and avatar targeting over polish. 70% value, 15% entertainment, 10% promo, 5% community.

## Volume Targets
- **SPEKGEN** (@gibran.alonzo.ecom personal brand): 60 pieces/month
- **LO FITNESS, HC, GREENRAY, METAGREEN**: 30 pieces/month each
- **Total**: 180 pieces/month

## Key Decisions (2026-03-26)
- SPEKGEN content goes through Gibran's personal brand @gibran.alonzo.ecom (NOT a business account)
- 4 clients use business accounts normally
- Carousels are the #1 priority format (visual-first with Gemini images)
- Carousel styles: reference-based (16 IG accounts = 16 styles), NOT 3 rigid templates
- Only LF and HC have Meta infrastructure for auto-promote; GR, MG, SP need setup

## Architecture
Content Hub (Next.js + Supabase) is the central nervous system. Skills (carousel-generator, single-post-generator, reel-scripter) are production tools feeding into it.

## Infrastructure Created
1. SPEKGEN added as 5th client in Content Hub (`sp` / `SPEKGEN`)
2. carousel-generator upgraded to v2.0 (16 reference styles, Gemini on every slide)
3. style-registry.json with 16 reference accounts
4. content-planner scaled to 30-60 pieces/month with Hormozi SPCL integration
5. single-post-generator skill (quote cards, tips, stats)
6. reel-scripter skill (video production briefs)
7. hormozi_spcl.json for SPEKGEN brand strategy
