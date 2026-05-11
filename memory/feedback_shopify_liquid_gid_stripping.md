---
name: Shopify Liquid strips gid:// prefix from HTML attributes
description: Full metaobject GIDs get URL-sanitized out of HTML attrs — pass numeric id and reconstruct in JS
type: feedback
---

Shopify's theme renderer strips `gid://shopify/Metaobject/` (and likely any `scheme://` prefix) from HTML attribute values at render time. A template like `data-item-id="gid://shopify/Metaobject/{{ item.system.id }}"` renders as `data-item-id="383913820417"` — only the numeric portion survives.

**Why:** Shopify's HTML sanitizer treats `//` in attribute values as a protocol-relative URL and either strips or rewrites the attribute to prevent XSS / unintended resource loading. Confirmed on the Horizon theme 2026-04-10 when building the Content Hub portal for HC.

**How to apply:**
- In snippet: `data-item-id="{{ item.system.id }}"` (just the numeric id, no prefix).
- In JS: reconstruct the full GID before any API call: `var fullId = 'gid://shopify/Metaobject/' + rawId;`
- Applies to any attribute where you'd want to pass a GID (variant, product, customer, metaobject). Always store numeric and reconstruct client-side.
- Do NOT waste time trying `| escape`, `| url_encode`, or other filters — the sanitizer runs AFTER Liquid filters.
