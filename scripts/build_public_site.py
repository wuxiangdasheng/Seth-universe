#!/usr/bin/env python3
"""Build a static public site for Cloudflare Pages or EdgeOne Pages.

The output intentionally excludes admin pages, Python server code, backups,
raw source data, and local editing state. It contains only reader-facing pages
and public JSON data.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / 'wiki'
OUT = ROOT / 'public-site'
DATA = OUT / 'data'
CONCEPT_DATA = DATA / 'concepts'

PUBLIC_PAGES = [
    'index.html',
    'book.html',
    'dream.html',
    'ai.html',
    'system.html',
    'topics.html',
]

PUBLIC_ASSETS = [
    'global-menu.js',
    'site-chrome.css',
]


def read_text(path):
    return path.read_text(encoding='utf-8')


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def copy_file(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def patch_index_html(html):
    html = html.replace("const BOOKMARK_API = '/api/bookmark';", "const BOOKMARK_API = null;")
    html = html.replace("fetch('concepts-lite.json')", "fetch('data/concepts-lite.json')")
    html = html.replace("fetch('concept-graph.json')", "fetch('data/concept-graph.json')")
    html = html.replace(
        "xhr.open('GET', '/bookmark.json?t=' + Date.now(), true);",
        "xhr.open('GET', 'data/bookmark.json?t=' + Date.now(), true);",
    )
    html = html.replace(
        "fetch('/api/concepts/' + id + '?t=' + Date.now())",
        "fetch('data/concepts/' + encodeURIComponent(id) + '.json')",
    )
    html = html.replace(
        "请通过本地服务器访问：<br><a style=\"color:var(--gold)\" href=\"http://localhost:8081/index.html\">http://localhost:8081/index.html</a>",
        "请稍后刷新页面，或联系站点维护者检查公开数据文件。",
    )
    html = html.replace(
        """function persistBookmarkRemote(store) {
  if (!store) return;
  fetch(BOOKMARK_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(store)
  }).catch(function() {});
}""",
        """function persistBookmarkRemote(store) {
  // Public static site stores reading position only in the visitor's browser.
  return;
}""",
    )
    return html


def patch_global_menu(js):
    return js.replace("fetch('concepts-lite.json')", "fetch('data/concepts-lite.json')")


def clean_output():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)


def write_public_data():
    concepts_lite = json.loads(read_text(WIKI / 'concepts-lite.json'))
    concepts_full = json.loads(read_text(WIKI / 'concepts.json'))
    concept_graph_path = WIKI / 'concept-graph.json'
    system_faq_path = WIKI / 'system-faq.json'

    write_text(DATA / 'concepts-lite.json', json.dumps(concepts_lite, ensure_ascii=False, separators=(',', ':')))

    if concept_graph_path.exists():
        concept_graph = json.loads(read_text(concept_graph_path))
    else:
        concept_graph = {'nodes': [], 'edges': [], 'metadata': {}}
    write_text(DATA / 'concept-graph.json', json.dumps(concept_graph, ensure_ascii=False, separators=(',', ':')))

    if system_faq_path.exists():
        system_faq = json.loads(read_text(system_faq_path))
    else:
        system_faq = {'faqs': []}
    write_text(DATA / 'system-faq.json', json.dumps(system_faq, ensure_ascii=False, separators=(',', ':')))

    concepts = concepts_full.get('concepts', [])
    CONCEPT_DATA.mkdir(parents=True, exist_ok=True)
    for concept in concepts:
        cid = concept.get('id')
        if not cid:
            continue
        write_text(CONCEPT_DATA / f'{cid}.json', json.dumps(concept, ensure_ascii=False, separators=(',', ':')))

    manifest = {
        'type': 'seth-universe-public-site',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'concepts': len(concepts),
        'lite_items': len(concepts_lite if isinstance(concepts_lite, list) else concepts_lite.get('concepts', [])),
        'includes': [
            'reader-facing HTML/CSS/JS',
            'data/concepts-lite.json',
            'data/concept-graph.json',
            'data/system-faq.json',
            'data/concepts/{concept-id}.json',
        ],
        'excludes': [
            'admin pages',
            'server.py',
            'backup/',
            '02-processed/',
            'concept-quotes-full/',
            'local bookmark state',
        ],
    }
    write_text(DATA / 'manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))


def write_hosting_files():
    write_text(
        OUT / '_headers',
        """/*
  Cache-Control: public, max-age=300

/data/*
  Cache-Control: public, max-age=300
""",
    )
    write_text(
        OUT / 'edgeone.json',
        json.dumps({
            'headers': [
                {
                    'source': '/*',
                    'headers': [
                        {'key': 'Cache-Control', 'value': 'public, max-age=300'},
                    ],
                },
                {
                    'source': '/data/*',
                    'headers': [
                        {'key': 'Cache-Control', 'value': 'public, max-age=300'},
                    ],
                },
            ],
        }, ensure_ascii=False, indent=2),
    )
    write_text(
        OUT / 'README.md',
        """# Seth Universe Public Site

This folder is generated by `python3 scripts/build_public_site.py`.

Deploy this directory as the Cloudflare Pages or EdgeOne Pages output folder:

- Framework preset: None
- Build command: leave empty
- Build output directory: `public-site`

The source content files under `wiki/` are intentionally not committed to Git.
Run `python3 scripts/build_public_site.py` locally after editing content, then
commit the regenerated `public-site/` files.

For EdgeOne Pages, `edgeone.json` contains the migrated headers config.

Do not add admin pages, backups, raw source data, or server code here.
""",
    )


def main():
    clean_output()

    for page in PUBLIC_PAGES:
        src = WIKI / page
        if not src.exists():
            continue
        html = read_text(src)
        if page == 'index.html':
            html = patch_index_html(html)
        write_text(OUT / page, html)

    for asset in PUBLIC_ASSETS:
        src = WIKI / asset
        if not src.exists():
            continue
        if asset == 'global-menu.js':
            write_text(OUT / asset, patch_global_menu(read_text(src)))
        else:
            copy_file(src, OUT / asset)

    write_public_data()
    write_hosting_files()

    file_count = sum(1 for p in OUT.rglob('*') if p.is_file())
    size = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    print(f'OK: built {OUT}')
    print(f'files: {file_count}')
    print(f'size: {size} bytes')


if __name__ == '__main__':
    main()
