---
name: Content Machine System Architecture
description: Q2 2026 content machine technical architecture — what was built, key files, system flow, deployment notes
type: project
---

## Architecture Overview

The Content Machine is a federated system with Content Hub as the central nervous system:

```
Content Hub (Vercel + Supabase)
├── Orchestrator cron (daily 7AM CST) → calls 14+ agents sequentially
├── Auto-Publisher cron (hourly) → publishes scheduled content
├── content_items table (8-stage workflow × 5 brands)
├── client_strategies table (Hormozi SPCL per brand)
├── funnel_sequences table (multi-post conversion journeys)
├── trend_insights table (scraped competitor data)
├── Dashboard (Content Machine, Calendar, Inspiration, per-client views)
└── Production Skills Bridge (Claude Code local → Content Hub API)
```

## Key Database Changes (migration 007)
- `client_strategies` — Hormozi SPCL, format distribution, posting times per client
- `funnel_sequences` — Multi-post TOFU→MOFU→BOFU journeys
- `content_items` new columns: `spcl_pillar`, `content_ratio_type`, `best_posting_time`, `production_brief`, `style_id`, `funnel_sequence_id`

## Content Pipeline Intelligence
- `content-generator.ts` v2.0 loads `client_strategies` from Supabase
- Generates posts with SPCL tags (S/P/C/L), funnel (TOFU/MOFU/BOFU), format distribution, style_ids, posting times
- Topic de-duplication: queries last 2 weeks to avoid repetition
- SPEKGEN gets 15 posts/week, other clients get 7-8

## Auto-Publishing
- `auto-publisher` cron runs hourly on Vercel Pro
- Publishes items with status='Programado' when date_planned + best_posting_time matches current window (±30 min)
- Falls back in daily orchestrator for items missed by hourly cron

## Scraping & Trends
- `apify-client.ts` now has SPEKGEN niche accounts (8 IG + 2 TikTok)
- `trend-analyzer.ts` runs after trend-scout on Sundays, extracts hook patterns and format distribution
- Analysis stored in trend_insights with content_type='analysis'
- Content generator reads recent trends to inform next week's plan

## Production Bridge
- `production-trigger` agent generates structured briefs for items in 'Produccion' status
- `batch-producer` skill (Claude Code local) fetches briefs from Content Hub API
- Invokes carousel-generator, single-post-generator, reel-scripter per format
- Uploads PNGs via `/api/upload-production` endpoint
- Updates status to 'Revision'

**Why:** Gibran's 4-6 hour weekly commitment = review plan + batch produce + QA/approve.

**How to apply:** When making changes to content pipeline, always consider the SPCL framework and format distribution rules.
