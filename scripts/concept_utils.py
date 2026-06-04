#!/usr/bin/env python3
"""Shared helpers for the Seth concept pipeline."""

import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / '02-processed'
CONCEPT_TABLE = PROCESSED_DIR / 'concept-wiki' / '核心概念表.md'


def safe_concept_name(name):
    return (name or '').replace('/', '_').replace(' ', '_')


def concept_id_from_index(index):
    return f'concept-{int(index):03d}'


def load_concept_table(path=CONCEPT_TABLE):
    concepts = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('|') or line.startswith('|---'):
                continue
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) < 3:
                continue
            try:
                index = int(parts[0])
            except ValueError:
                continue
            en_name = parts[1]
            zh_name = parts[2]
            concepts[en_name] = {
                'idx': index,
                'id': concept_id_from_index(index),
                'en': en_name,
                'zh': zh_name,
            }
    return concepts


def definition_patterns_for(concept_name):
    """Get definition sentence patterns for a concept (is/are/means/refers to etc)."""
    c = re.escape((concept_name or '').lower())
    return [
        rf'{c}\s+(?:is|are|was|means|refers\s+to|can\s+be\s+defined\s+as)',
        rf'the\s+{c}\s+(?:is|are|was|means)',
        rf'(?:called|known\s+as|termed)\s+{c}',
        rf'{c}\s*,\s*(?:which|that)\s+(?:is|are|was)',
    ]
