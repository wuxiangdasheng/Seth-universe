#!/usr/bin/env python3
"""Rebuild wiki/concepts.json from concept-quotes-full/.

The script is incremental: it only replaces quote data for concepts that have
source quote files, while preserving hand-edited fields from concepts.json.
"""

import json
import os
import shutil
import sys
from datetime import datetime

try:
    from concept_utils import BASE_DIR, load_concept_table, safe_concept_name
except ImportError:
    from scripts.concept_utils import BASE_DIR, load_concept_table, safe_concept_name


FULL_DIR = BASE_DIR / 'concept-quotes-full'
BACKUP_DIR = BASE_DIR / 'backup'
CONCEPTS_FILE = BASE_DIR / 'wiki' / 'concepts.json'

PRESERVED_DEFAULTS = {
    'category': '',
    'definition': [],
    'definition_ai': '',
    'definition_en': '',
    'definition_source': '',
    'explanation': '',
    'related_concepts': [],
    'sub_concepts': [],
}


def auto_backup(filepath, backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'{filepath.stem}.{timestamp}.json'
    shutil.copy2(filepath, backup_path)
    existing = sorted(f for f in os.listdir(backup_dir) if f.startswith(filepath.stem))
    for old_file in existing[:-10]:
        os.remove(backup_dir / old_file)
    print(f'  已自动备份: {backup_path}')
    return backup_path


def load_existing_data():
    if not CONCEPTS_FILE.exists():
        return {'concepts': [], 'topics': {'topics': []}, 'metadata': {}}
    with open(CONCEPTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_quote_file(concept_en):
    full_file = FULL_DIR / f'{safe_concept_name(concept_en)}.json'
    if not full_file.exists():
        return None
    with open(full_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_quotes(full_data, concept_id):
    quotes = []
    for idx, ex in enumerate(full_data.get('excerpts', []), 1):
        quote = {
            'id': f'q-{concept_id}-{idx:04d}',
            'text': ex.get('text_en', ''),
            'translation': ex.get('text_zh', ''),
            'source': ex.get('source', ''),
            'book': ex.get('book', ''),
            'source_file': ex.get('source_file', ''),
            'source_raw': ex.get('source_raw', {}),
            'score': ex.get('score', 0),
            'match_count': ex.get('match_count', 0),
            'prefix_match': ex.get('prefix_match', False),
            'semantic_reason': ex.get('semantic_reason', ''),
            'quote_role': ex.get('quote_role', ''),
            'semantic_score': ex.get('semantic_score', 0),
            'reading_order': ex.get('reading_order', 90),
            'related_concepts': ex.get('related_concepts', []),
        }
        if ex.get('type'):
            quote['type'] = ex['type']
        quotes.append(quote)
    return quotes


def merge_concept(old_concept, table_info, full_data):
    concept = dict(PRESERVED_DEFAULTS)
    concept.update(old_concept or {})
    concept['id'] = table_info['id']
    concept['name_zh'] = table_info['zh']
    concept['name_en'] = table_info['en']

    if full_data is not None:
        concept['quotes'] = build_quotes(full_data, table_info['id'])
        concept['quotes_count'] = len(concept['quotes'])
    else:
        concept['quotes'] = concept.get('quotes', [])
        concept['quotes_count'] = len(concept.get('quotes', []))
    return concept


def main():
    target_concept = sys.argv[1] if len(sys.argv) > 1 else None
    concept_table = load_concept_table()
    old_data = load_existing_data()
    old_concepts = old_data.get('concepts', [])
    old_by_en = {c.get('name_en', ''): c for c in old_concepts}

    if target_concept and target_concept not in concept_table:
        print(f"错误: 核心概念表中未找到概念 '{target_concept}'")
        return 1

    auto_backup(CONCEPTS_FILE, BACKUP_DIR)

    targets = [target_concept] if target_concept else list(concept_table.keys())
    target_set = set(targets)
    rebuilt_by_en = {}

    for concept_en in targets:
        table_info = concept_table[concept_en]
        full_data = load_quote_file(concept_en)
        old_concept = old_by_en.get(concept_en, {})

        if full_data is None and not old_concept:
            print(f'  跳过: {concept_en}（无摘录文件且 concepts.json 中不存在）')
            continue

        concept = merge_concept(old_concept, table_info, full_data)
        rebuilt_by_en[concept_en] = concept
        source_note = '已更新摘录' if full_data is not None else '保留旧摘录'
        print(f"  {concept_en} ({table_info['id']}): {len(concept.get('quotes', []))} 条摘录，{source_note}")

    new_concepts = []
    for old in old_concepts:
        en = old.get('name_en', '')
        if en in rebuilt_by_en:
            new_concepts.append(rebuilt_by_en.pop(en))
        elif en not in target_set:
            new_concepts.append(old)

    for concept_en in concept_table:
        if concept_en in rebuilt_by_en:
            new_concepts.append(rebuilt_by_en.pop(concept_en))

    for concept in rebuilt_by_en.values():
        new_concepts.append(concept)

    new_data = {
        'concepts': new_concepts,
        'topics': old_data.get('topics', {'topics': []}),
        'metadata': {
            **old_data.get('metadata', {}),
            'version': old_data.get('metadata', {}).get('version', '2.0'),
            'updated': datetime.now().strftime('%Y-%m-%d'),
            'total_concepts': len(new_concepts),
            'source': 'concept-quotes-full/',
        },
    }

    with open(CONCEPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print('\n完成! concepts.json 已重建:')
    print(f'  概念数: {len(new_concepts)}')
    for c in new_concepts:
        print(f"    {c.get('name_en')} ({c.get('name_zh')}): {len(c.get('quotes', []))} 条摘录")
    print(f'\n总大小: {os.path.getsize(CONCEPTS_FILE)} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
