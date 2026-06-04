#!/usr/bin/env python3
"""Backfill quote_role / semantic_score / reading_order for quote libraries."""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from batch_collect_quotes import FULL_DIR, SELECTED_DIR, MAX_SELECTED, classify_quote
except ImportError:
    from scripts.batch_collect_quotes import FULL_DIR, SELECTED_DIR, MAX_SELECTED, classify_quote
try:
    from concept_utils import BASE_DIR, safe_concept_name
except ImportError:
    from scripts.concept_utils import BASE_DIR, safe_concept_name


BACKUP_DIR = Path(BASE_DIR) / 'scripts' / 'backup'


def auto_backup(path):
    path = Path(path)
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f'{path.stem}.roles.{datetime.now().strftime("%Y%m%d_%H%M%S")}{path.suffix}'
    shutil.copy2(path, backup_path)
    return backup_path


def sort_key(ex):
    return (
        int(ex.get('reading_order', 90) or 90),
        -int(ex.get('semantic_score', 0) or 0),
        -float(ex.get('score', 0) or 0),
        ex.get('source', ''),
    )


def apply_roles(data):
    concept_en = data.get('concept_name_en', '')
    changed = 0
    counts = {}
    for ex in data.get('excerpts', []):
        role_data = classify_quote(
            ex.get('text_en', ''),
            concept_en,
            ex.get('semantic_reason', ''),
            ex.get('score', 0),
        )
        for key, value in role_data.items():
            if ex.get(key) != value:
                ex[key] = value
                changed += 1
        counts[ex.get('quote_role', 'other')] = counts.get(ex.get('quote_role', 'other'), 0) + 1
    return changed, counts


def process_full(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    changed, counts = apply_roles(data)
    if changed:
        auto_backup(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return data, changed, counts


def process_selected(path, full_data):
    path = Path(path)
    selected = sorted(full_data.get('excerpts', []), key=sort_key)[:MAX_SELECTED]
    data = {
        'concept_name_en': full_data.get('concept_name_en', ''),
        'concept_name_zh': full_data.get('concept_name_zh', ''),
        'source': f"从 {len(full_data.get('excerpts', []))} 条摘录中按阅读顺序精选 top {MAX_SELECTED}",
        'sort_rule': 'reading_order asc + semantic_score desc + score desc',
        'excerpts': selected,
    }
    auto_backup(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        paths = [Path(FULL_DIR) / f'{safe_concept_name(target)}.json']
    else:
        paths = sorted(Path(FULL_DIR).glob('*.json'))

    for path in paths:
        if not path.exists():
            print(f'跳过: {path} 不存在')
            continue
        full_data, changed, counts = process_full(path)
        process_selected(Path(SELECTED_DIR) / path.name, full_data)
        print(f'{path.name}: changed {changed}, roles {counts}')


if __name__ == '__main__':
    main()
