#!/usr/bin/env python3
"""从 concept-quotes-full/ 重建 concepts.json，只保留已处理的概念"""

import json, os, re
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parents[1])
FULL_DIR = os.path.join(BASE_DIR, 'concept-quotes-full')
OLD_FILE = os.path.join(BASE_DIR, 'wiki/concepts.json')
NEW_FILE = os.path.join(BASE_DIR, 'wiki/concepts.json.bak')

# 概念名 → ID 映射
CONCEPT_IDS = {
    'Beliefs': 'concept-002',
    'Ego': 'concept-006',
    'Consciousness': 'concept-004',
}

# 概念中文映射
CONCEPT_ZH = {
    'Beliefs': '信念',
    'Ego': '自我',
    'Consciousness': '意识',
}

# 加载旧数据（提取 definition 和 explanation）
old_definitions = {}
old_explanations = {}
old_categories = {}
with open(OLD_FILE, 'r', encoding='utf-8') as f:
    old_data = json.load(f)
    for c in old_data['concepts']:
        en = c.get('name_en', '')
        old_definitions[en] = c.get('definition', [])
        old_explanations[en] = c.get('explanation', '')
        old_categories[en] = c.get('category', '')

new_concepts = []

for concept_en, concept_id in CONCEPT_IDS.items():
    safe_name = concept_en.replace('/', '_').replace(' ', '_')
    full_file = os.path.join(FULL_DIR, f'{safe_name}.json')
    if not os.path.exists(full_file):
        print(f"  跳过: {concept_en}（文件不存在）")
        continue
    
    with open(full_file, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    
    # 转换 excerpts 格式: {text_en, text_zh, ...} → {text, translation, ...}
    quotes = []
    for idx, ex in enumerate(full_data['excerpts'], 1):
        quotes.append({
            'id': f'q-{concept_id}-{idx:04d}',
            'text': ex['text_en'],
            'translation': ex['text_zh'],
            'source': ex['source'],
            'score': ex.get('score', 0),
            'match_count': ex.get('match_count', 0),
        })
    
    concept = {
        'id': concept_id,
        'name_zh': CONCEPT_ZH[concept_en],
        'name_en': concept_en,
        'category': old_categories.get(concept_en, ''),
        'definition': old_definitions.get(concept_en, []),
        'definition_ai': '',
        'definition_en': '',
        'definition_source': '',
        'explanation': old_explanations.get(concept_en, ''),
        'quotes': quotes,
        'related_concepts': [],
        'sub_concepts': [],
    }
    
    new_concepts.append(concept)
    print(f"  {concept_en} ({concept_id}): {len(quotes)} 条摘录")

# 保留旧的 topics 结构
old_topics = old_data.get('topics', {'topics': []})

new_data = {
    'concepts': new_concepts,
    'topics': old_topics,
    'metadata': {
        'version': '2.0',
        'updated': '2026-06-03',
        'total_concepts': len(new_concepts),
        'source': 'concept-quotes-full/',
    }
}

# 备份旧文件
import shutil
shutil.copy2(OLD_FILE, NEW_FILE)
print(f"  已备份旧数据: {NEW_FILE}")

# 写入新文件
with open(OLD_FILE, 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print(f"\n完成! concepts.json 已重建:")
print(f"  概念数: {len(new_concepts)}")
for c in new_concepts:
    print(f"    {c['name_en']} ({c['name_zh']}): {len(c['quotes'])} 条摘录")
print(f"\n总大小: {os.path.getsize(OLD_FILE)} bytes")
