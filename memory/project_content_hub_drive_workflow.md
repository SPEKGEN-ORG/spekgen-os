---
name: Content Hub v2 Architecture
description: New Content Hub (spekgen-hub) — Next.js 16 + Supabase + Vercel. Replaced bloated v1. Supabase Storage for media, Drive only for documents.
type: project
---

## Content Hub v2 (2026-04-03)

**Why:** v1 was 25K LOC, 49 API routes, 20+ tables, 15 broken autonomous agents. Rebuilt from scratch as lightweight ~2K LOC hub.

**How to apply:** Use v2 URLs and architecture for all Content Hub work. v1 is deprecated.

## URLs
- **Dashboard:** https://spekgen-hub.vercel.app/dashboard/{client}
- **Portal HC:** https://spekgen-hub.vercel.app/portal/3b22f35e-975e-4e50-b913-85ea5baa3925
- **Login:** gibran.alonzo0506@gmail.com / Spekgen2026!
- **Repo:** https://github.com/g-bran/spekgen-hub
- **Local:** ~/Developer/spekgen-hub/

## Stack
- Next.js 16 (App Router) + TypeScript strict
- Supabase (project: wjlwpfaogjpeqgyxxnwa) — same as v1
- Tailwind CSS + shadcn/ui (dark mode default, Geist fonts)
- Vercel (free tier, auto-deploy from GitHub)

## Database Schema (v2_ prefix, coexists with v1)
- v2_clients, v2_posts, v2_post_media, v2_approvals, v2_profiles, v2_meta_ads_sync, v2_documents, v2_image_proposals
- RLS enabled on all tables
- Post status flow: draft → review → approved → scheduled → published
- v2_posts: rating (smallint 1-5), time_planned (time)
- v2_image_proposals: post_id, media_id, original_url, proposed_url, description, status (pending/accepted/rejected)
- Content pillars: S (Status), P (Power), C (Credibility), L (Likeness)
- Funnel: TOFU, MOFU, BOFU (uppercase)
- Format values: carrusel, reel, static, story, video

## Media Strategy
- **Post images:** Supabase Storage bucket `post-media` (public). Upload via /api/upload
- **Client documents:** Google Drive (tab "Documentos" in portal). Drive folder IDs in v2_clients.drive_docs_folder_id
- **v1 used Drive for everything** — v2 only uses Drive for documents

## Portal (7 tabs, conditional)
1. Pipeline — posts in `review` status, approve/reject buttons
2. Aprobados — approved/scheduled/published posts with progress bar
3. Calendario — monthly calendar with color-coded status pills
4. Rendimiento — published posts count, reach, engagement placeholders
5. Rechazados* — only shows if rejected posts exist
6. Anuncios* — only shows if meta_ads_sync data exists
7. Documentos* — only shows if documents exist

## Auth
- Admin: Supabase session auth (email/password)
- Portal: token-based (v2_clients.portal_token in URL)

## Key Files
- `lib/types.ts` — all TypeScript interfaces
- `lib/constants.ts` — client configs, status/pillar/format labels
- `lib/notifications.ts` — email notifications (nodemailer/Gmail SMTP)
- `app/api/posts/route.ts` — CRUD
- `app/api/approve/route.ts` — approval flow + auto-publish trigger
- `app/api/upload/route.ts` — media upload to Supabase Storage
- `app/api/auto-publish/route.ts` — publish to IG+FB, supports approved+scheduled
- `app/api/revise-image/route.ts` — AI image revision (Claude+Gemini, base64)
- `app/api/proposal-action/route.ts` — accept/reject image proposals
- `app/api/portal/update-post/route.ts` — client copy edits
- `app/portal/[token]/page.tsx` — portal server component
- `app/dashboard/[client]/page.tsx` — dashboard server component

## Portal Features (updated 2026-04-07)
- Caption editable inline
- AI Image Revision with slide selector + before/after proposals (max 2 attempts)
- Star rating (1-5, mandatory on approval)
- Publication time visible on each post
- "Publicar ahora" button (triggers auto-publish immediately)
- Email notifications to Gibran on all client actions
