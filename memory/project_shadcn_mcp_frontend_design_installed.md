---
name: shadcn-ui-mcp-server + Anthropic frontend-design skill installed
description: Both installed and verified working 2026-04-29. shadcn MCP exposes 10 tools for component/block on-demand. frontend-design skill auto-activates for UI work, anti-AI-slop philosophy.
type: project
originSessionId: 57841043-f116-44ae-a90e-75d6ba3b1741
---
**Installed 2026-04-29.** Both verified loading correctly via Prompt 1 validation after 3rd restart.

## shadcn-ui-mcp-server

**Repo**: https://github.com/jpisnice/shadcn-ui-mcp-server (v2.0.0, Jan 2026, 2.8k stars)

**Config** in `~/.claude.json` mcpServers:
```json
"shadcn": {
  "type": "stdio",
  "command": "/Users/gibranalonzo/.nvm/versions/node/v20.20.1/bin/node",
  "args": [
    "/Users/gibranalonzo/.nvm/versions/node/v20.20.1/lib/node_modules/@jpisnice/shadcn-ui-mcp-server/build/index.js",
    "--framework", "react"
  ]
}
```

**Tools exposed** (all `mcp__shadcn__*`):
- `apply_theme`
- `get_block`
- `get_component`
- `get_component_demo`
- `get_component_metadata`
- `get_directory_structure`
- `get_theme`
- `list_blocks`
- `list_components`
- `list_themes`

**Rate limit**: 60 req/hour without GitHub PAT (default). To upgrade to 5000 req/hour, add `--github-api-key YOUR_PAT` to args.

**How to use**: when building/refactoring mockup templates, jalar bloques shadcn on-demand (form blocks, dashboards, calendars, etc.). Adapt to HTML/Tailwind — no React build required since output is static HTML.

## Anthropic frontend-design skill

**Source**: github.com/anthropics/skills/skills/frontend-design (4.4 KB SKILL.md)
**Path**: `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/GLOBALES/frontend-design/SKILL.md`
**Symlink**: `~/.claude/skills/frontend-design/` → SPEKGEN globales (via sync-skills hook)
**Invocable name**: `frontend-design` (también vía `Skill` tool con `skill: "frontend-design"`)

**Activates when**: user asks to build web components, pages, artifacts, posters, applications (websites, landing pages, dashboards, React components, HTML/CSS layouts, styling/beautifying any UI).

**Core philosophy**: anti-AI-slop. Forces:
1. Pick BOLD aesthetic direction BEFORE coding (brutalist warm, retro-pet playful, editorial-magazine, organic-natural, luxury-minimal, post-modern collage, etc.)
2. Justify direction in 2-3 lines
3. Apply with precision in typography/color/motion/composition
4. REJECT generic AI aesthetics: no Inter default, no purple gradients, no rounded-xl genérico, no centered-everything

## Install gotchas (lessons learned during install)

1. **Field `"type": "stdio"` required** — without it Claude Code skips silently, zero logs. Documented in `feedback_claude_mcp_type_field_required.md`
2. **nvm-managed node not in Claude Code launcher PATH** — `npx` can't be found. Fix: pre-install package global + use absolute node binary + absolute JS file path (bypasses npx entirely)
3. **Restart required** — Claude Code does NOT pick up `mcpServers` changes mid-session. Must Cmd+Q and re-open

## How to test

In a fresh session, ask:
- "Lista las tools mcp__shadcn__*" → should return 10
- "Llama mcp__shadcn__list_components con limit:5" → should return component list
- "Skill list" or describe UI work → frontend-design should appear

## Related work

- First test of stack: PROMPTS_yerena_v2.md (in `_design_intel/`) — validation prompt + build prompt for `index_v2.html`
- Combination: frontend-design skill picks aesthetic direction → shadcn MCP provides production-grade components → yerena BRIEF + Bond Vet DNA from `reports/07_medspa_aesthetic_clinics_DNA.md` provides content/UX patterns

## Pendings

- [ ] Generate GitHub PAT con `public_repo` scope para subir rate limit shadcn MCP de 60→5000 req/hr
- [ ] Test build de yerena v2 con la nueva stack para benchmark vs el actual
- [ ] Install Blender MCP cuando aterrice tier-1 prospect $30k+ (no urgente — Spline cubre 80% del caso)
