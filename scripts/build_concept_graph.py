#!/usr/bin/env python3
"""Build a concept graph from per-quote related concepts."""

import json
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
CONCEPTS_FILE = BASE_DIR / 'wiki' / 'concepts.json'
GRAPH_FILE = BASE_DIR / 'wiki' / 'concept-graph.json'


def main():
    with open(CONCEPTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    concepts = data.get('concepts', [])
    concept_by_id = {c.get('id'): c for c in concepts}
    edge_map = {}

    for concept in concepts:
        source_id = concept.get('id')
        if not source_id:
            continue
        for quote in concept.get('quotes', []):
            quote_id = quote.get('id', '')
            for rel in quote.get('related_concepts', []):
                target_id = rel.get('id')
                if not target_id or target_id == source_id or target_id not in concept_by_id:
                    continue
                key = (source_id, target_id)
                if key not in edge_map:
                    edge_map[key] = {
                        'source': source_id,
                        'target': target_id,
                        'type': 'co_occurs',
                        'weight': 0,
                        'quote_count': 0,
                        'evidence_quote_ids': [],
                    }
                edge = edge_map[key]
                edge['weight'] += max(1, int(rel.get('match_count', 1) or 1))
                edge['quote_count'] += 1
                if quote_id and len(edge['evidence_quote_ids']) < 12:
                    edge['evidence_quote_ids'].append(quote_id)

    nodes = []
    degree = defaultdict(int)
    for edge in edge_map.values():
        degree[edge['source']] += edge['weight']
        degree[edge['target']] += edge['weight']

    for concept in concepts:
        cid = concept.get('id')
        nodes.append({
            'id': cid,
            'name_zh': concept.get('name_zh', ''),
            'name_en': concept.get('name_en', ''),
            'quotes_count': len(concept.get('quotes', [])),
            'degree': degree.get(cid, 0),
        })

    edges = sorted(edge_map.values(), key=lambda e: (-e['weight'], e['source'], e['target']))
    graph = {
        'nodes': nodes,
        'edges': edges,
        'metadata': {
            'source': 'wiki/concepts.json quotes[].related_concepts',
            'total_nodes': len(nodes),
            'total_edges': len(edges),
        },
    }
    with open(GRAPH_FILE, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f'OK: {GRAPH_FILE} nodes={len(nodes)} edges={len(edges)}')


if __name__ == '__main__':
    main()
