# Shopify custom-liquid section: límite ~50KB en el campo custom_liquid

El setting `custom_liquid` de una section type `custom-liquid` tiene límite de tamaño (~50KB). Payloads más grandes dan 422 "unknown" del Admin API (`PUT /themes/{id}/assets.json` → 422 sin body descriptivo).

## Workaround

Meter el HTML grande en un **snippet** (`snippets/<nombre>.liquid` — sin límite) y que el `custom_liquid` del section solo contenga `{% render '<nombre>' %}`.

```python
# 1. Push snippet (sin límite)
sc.put('/themes/{id}/assets.json', {
    'asset': {'key': 'snippets/spekgen-home.liquid', 'value': body_html_grande}
})

# 2. Push template que lo renderiza
template = {
    'sections': {
        'home': {
            'type': 'custom-liquid',
            'settings': {'custom_liquid': "{% render 'spekgen-home' %}"}
        }
    },
    'order': ['home']
}
sc.put('/themes/{id}/assets.json', {
    'asset': {'key': 'templates/index.json', 'value': json.dumps(template)}
})
```

## Override del root `/` en Shopify

Shopify NO permite `UrlRedirect` con path `/` (422). El único camino para que `/` sirva contenido custom es **override del template del home** (`templates/index.json`) del tema activo. Si el contenido es >50KB, usar el workaround de snippet arriba.

## Cache del root

Después de push del template del root, el `page_cache:IndexController` puede servir contenido stale durante 1-3 minutos. El etag cambia inmediatamente (indicando que origen conoce el cambio), pero la cache interna de Shopify tarda. Validar con `?bust=<random>` si urge ver el render fresco.

## Descubierto

2026-04-22 publicando spekgen.com (WEBSITE/index.html = 52KB → fallaba como custom_liquid, OK como snippet).
Ref: `SPK - SPEKGEN AGENCY/WEBSITE/_publish_website.py` — implementación completa reutilizable.
