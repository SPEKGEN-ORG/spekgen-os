---
name: Horizon Theme — Width Constraint via CSS Grid (NOT max-width)
description: Horizon's page-width-narrow constrains content via grid-template-columns + CSS variables, not max-width. Override the vars, not max-width.
type: feedback
originSessionId: 57841043-f116-44ae-a90e-75d6ba3b1741
---
**Discovered 2026-04-29 publishing yerena to spekgen.com/yerenamockup.**

When publishing prospect mockups via `_publish_prospect.py` to spekgen.com (Shopify Horizon theme), content sections appeared narrower than expected even though `chrome_hider_css` set `max-width: none !important` everywhere.

## Root cause

Horizon's `body.page-width-narrow` does NOT use `max-width` to constrain content. It uses **CSS Grid with computed CSS variables**:

```css
body.page-width-narrow, .page-width-content {
  --page-margin: 40px;
  --page-content-width: var(--narrow-page-width);
  --page-width: calc(var(--page-content-width) + (var(--page-margin) * 2));
}
.section {
  --full-page-grid-central-column-width: min(
    var(--page-width) - var(--page-margin) * 2,
    calc(100% - var(--page-margin) * 2)
  );
  display: grid;
  grid-template-columns:
    var(--full-page-grid-margin)
    var(--full-page-grid-central-column-width)
    var(--full-page-grid-margin);
}
```

Content placed in `.section` lives inside the central grid column whose width is computed from `--narrow-page-width` (which Horizon admin sets, e.g. ~1100px). `max-width: none !important` does nothing because the constraint is `grid-template-columns`, not `max-width`.

## Fix (now in `_publish_prospect.py` chrome_hider, 2026-04-29)

Override the CSS variables on `:root, html, body, .page-width-narrow, .section, main, #MainContent`:

```css
--narrow-page-width: 100% !important;
--normal-page-width: 100% !important;
--wide-page-width: 100% !important;
--page-content-width: 100% !important;
--page-width: 100% !important;
--page-margin: 0px !important;
--full-page-grid-central-column-width: 100% !important;
--full-page-grid-margin: 0px !important;
--util-page-margin-offset: 0px !important;
--full-page-margin-inline-offset: 0px !important;
```

PLUS force `.section` to single-column:

```css
main > .shopify-section .section,
.shopify-section > .section {
  display: block !important;
  grid-template-columns: 100% !important;
  padding-inline: 0 !important;
}
```

## Adjacent fixes done in same session

1. **Auto page-title heading** — Horizon renders `page.title` as `<h1>` inside `.text-block.text-block--XXX__heading`. Hide via `[class*="__heading"]` + `:has(>h1)` + nuke `section-background` padding/min-height to remove residual dark bar.
2. **Logo detection** — script previously only matched files literally named `logo.*`. Patched to match `*logo*` regex (catches `yerena-logo.jpg`, `brand_logo.svg`, etc.).

## How to apply

Next time publishing a prospect mockup and the content looks narrower than localhost: this fix is already in `_publish_prospect.py` as of 2026-04-29 v07e7b3 / v30cf35 yerena handles. If a future Horizon update adds new width vars, append them to the chrome_hider section.

## Cache bust note

Shopify `page_cache` may serve stale HTML even when `pageUpdate` API succeeds. The script bypasses this by versioning handles per content hash, BUT it locks handles by default. To force a definitive cache bust, delete `{prospect-dir}/.spekgen_locked_handles.json` before re-running. The script will mint a new handle, update redirect, delete old version.
