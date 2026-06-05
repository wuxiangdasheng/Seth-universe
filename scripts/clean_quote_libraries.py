#!/usr/bin/env python3
"""Clean existing full quote libraries without calling external APIs."""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    from batch_collect_quotes import (
        FULL_DIR,
        compile_rule,
        is_biographical_note,
        semantic_relevance_reason,
    )
except ImportError:
    from scripts.batch_collect_quotes import (
        FULL_DIR,
        compile_rule,
        is_biographical_note,
        semantic_relevance_reason,
    )
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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f'{path.stem}.clean.{timestamp}{path.suffix}'
    shutil.copy2(path, backup_path)
    return backup_path


def translated_count(excerpts):
    return sum(1 for ex in excerpts if ex.get('text_zh'))


def clean_one(full_path):
    full_path = Path(full_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    excerpts = data.get('excerpts', [])
    concept_en = data.get('concept_name_en', '') or full_path.stem.replace('_', ' ')
    compiled_rule = compile_rule(concept_en)
    kept = []
    removed_bio = 0
    removed_semantic = 0
    for ex in excerpts:
        text = ex.get('text_en', '')
        if is_biographical_note(text):
            removed_bio += 1
            continue
        semantic_reason = semantic_relevance_reason(text, concept_en, compiled_rule)
        if not semantic_reason:
            removed_semantic += 1
            continue
        ex['semantic_reason'] = semantic_reason
        kept.append(ex)
    removed = len(excerpts) - len(kept)
    if removed == 0:
        return {'file': str(full_path), 'before': len(excerpts), 'after': len(kept), 'removed': 0}

    auto_backup(full_path)
    data['excerpts'] = kept
    data['total_after_dedup'] = len(kept)
    data['total_translated'] = translated_count(kept)
    data['cleaned_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['cleaning_rule'] = 'drop_biographical_note_and_require_semantic_relevance'
    data['removed_biographical_note'] = removed_bio
    data['removed_semantic_irrelevant'] = removed_semantic
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        'file': str(full_path),
        'before': len(excerpts),
        'after': len(kept),
        'removed': removed,
        'removed_bio': removed_bio,
        'removed_semantic': removed_semantic,
    }


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
        result = clean_one(path)
        print(
            f"{Path(result['file']).name}: {result['before']} -> {result['after']}，"
            f"移除 {result['removed']} "
            f"(bio {result.get('removed_bio', 0)}, semantic {result.get('removed_semantic', 0)})"
        )


if __name__ == '__main__':
    main()
