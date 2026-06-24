#!/usr/bin/env python3
"""Genera f24-media/catalog_compact.ts desde F24_BOT_KNOWLEDGE/catalog.json.
Lista compacta (sku, short_title, category, marca+modelo, price) que la Edge Function
f24-media usa para el matching de visión + validacion de SKU + enriquecimiento de precio.
Regenerar cada vez que cambie el catalogo (junto con build_f24_knowledge.py)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, 'F24_BOT_KNOWLEDGE/catalog.json'), encoding='utf-8'))
items = d['products']
out = []
for it in items:
    sku = (it.get('sku') or '').strip()
    if not sku:
        continue
    marca = (it.get('marca') or '').strip()
    modelo = (it.get('modelo') or '').strip()
    out.append({
        'sku': sku,
        't': (it.get('short_title') or it.get('title') or '').strip(),
        'c': (it.get('category') or '').strip(),
        'm': (marca + (' ' + modelo if modelo else '')).strip(),
        'p': (it.get('price') or '').strip(),
    })
ts  = '// AUTO-GENERADO desde F24_BOT_KNOWLEDGE/catalog.json — NO editar a mano.\n'
ts += '// Regenerar: /usr/bin/python3 gen_catalog_compact.py\n'
ts += '// Campos: sku, t(short_title), c(category), m(marca modelo), p(price MXN).\n'
ts += 'export interface CatItem { sku: string; t: string; c: string; m: string; p: string; }\n'
ts += 'export const CATALOG: CatItem[] = ' + json.dumps(out, ensure_ascii=False) + ';\n'
open(os.path.join(HERE, 'f24-media/catalog_compact.ts'), 'w', encoding='utf-8').write(ts)
print('wrote', len(out), 'items ->', round(os.path.getsize(os.path.join(HERE,'f24-media/catalog_compact.ts'))/1024,1), 'KB')
print('categories:', len(set(o['c'] for o in out)))
print('sample:', out[0])
