import json
from pathlib import Path

WIKI_DIR = Path(__file__).resolve().parents[1] / 'wiki'

with open(WIKI_DIR / 'concepts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

lite = []
for c in data['concepts']:
    lc = {
        'id': c.get('id'),
        'name_zh': c.get('name_zh'),
        'name_en': c.get('name_en'),
        'category': c.get('category', ''),
        'definition': c.get('definition', ''),
        'definition_en': c.get('definition_en', ''),
        'definition_source': c.get('definition_source', ''),
        'definition_ai': c.get('definition_ai', ''),
        'explanation': c.get('explanation', ''),
        'quotes_count': len(c.get('quotes', [])),
        'sub_concepts': [],
        'related_concepts': c.get('related_concepts', [])
    }
    for sc in c.get('sub_concepts', []):
        lc['sub_concepts'].append({
            'id': sc.get('id'),
            'name_zh': sc.get('name_zh'),
            'name_en': sc.get('name_en'),
            'definition': sc.get('definition', ''),
            'definition_source': sc.get('definition_source', ''),
            'explanation': sc.get('explanation', ''),
            'quotes_count': len(sc.get('quotes', []))
        })
    lite.append(lc)

with open(WIKI_DIR / 'concepts-lite.json', 'w', encoding='utf-8') as f:
    json.dump(lite, f, ensure_ascii=False)

import os
size = os.path.getsize(WIKI_DIR / 'concepts-lite.json')
print('OK, size:', size, 'bytes')
sample = lite[0]
print('Sample:', sample['name_zh'], '-> source:', repr(sample.get('definition_source', 'MISSING')))
