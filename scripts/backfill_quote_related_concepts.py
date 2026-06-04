#!/usr/bin/env python3
"""Backfill per-quote related concepts in existing quote libraries."""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from batch_collect_quotes import FULL_DIR, SELECTED_DIR, related_concepts_for_text
except ImportError:
    from scripts.batch_collect_quotes import FULL_DIR, SELECTED_DIR, related_concepts_for_text
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
    backup_path = BACKUP_DIR / f'{path.stem}.related.{datetime.now().strftime("%Y%m%d_%H%M%S")}{path.suffix}'
    shutil.copy2(path, backup_path)
    return backup_path


def build_related_index(excerpts):
    index = {}
    for ex in excerpts:
        text = ex.get('text_en', '')
        if text:
            index[text] = ex.get('related_concepts', [])
    return index


def update_full(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    concept_en = data.get('concept_name_en', '')
    changed = 0
    for ex in data.get('excerpts', []):
        related = related_concepts_for_text(ex.get('text_en', ''), concept_en)
        if ex.get('related_concepts') != related:
            ex['related_concepts'] = related
            changed += 1
    if changed:
        auto_backup(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return data, changed


def update_selected(path, related_index):
    path = Path(path)
    if not path.exists():
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    changed = 0
    for ex in data.get('excerpts', []):
        related = related_index.get(ex.get('text_en', ''), ex.get('related_concepts', []))
        if ex.get('related_concepts') != related:
            ex['related_concepts'] = related
            changed += 1
    if changed:
        auto_backup(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return changed


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
        full_data, full_changed = update_full(path)
        selected_changed = update_selected(Path(SELECTED_DIR) / path.name, build_related_index(full_data.get('excerpts', [])))
        related_total = sum(1 for ex in full_data.get('excerpts', []) if ex.get('related_concepts'))
        print(f'{path.name}: full changed {full_changed}, selected changed {selected_changed}, with tags {related_total}/{len(full_data.get("excerpts", []))}')


if __name__ == '__main__':
    main()
