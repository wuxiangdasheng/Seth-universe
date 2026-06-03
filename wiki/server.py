#!/usr/bin/env python3
"""赛斯宇宙 Wiki 服务器 - Threading + 内存缓存"""
import json, os, re
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'concepts.json')
LITE_FILE = os.path.join(DIR, 'concepts-lite.json')
QUOTES_FILE = os.path.join(DIR, 'quotes.json')
TOPICS_FILE = os.path.join(DIR, 'topics.json')
RELATIONS_FILE = os.path.join(DIR, 'relations.json')
BASE_DIR = os.path.dirname(DIR)
QUOTE_SOURCE_DIRS = [
    os.path.join(BASE_DIR, 'concept-quotes-full'),
    os.path.join(BASE_DIR, 'concept-quotes'),
]

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    ALL_DATA = json.load(f)
CONCEPTS = ALL_DATA.get('concepts', [])

def _load_quotes():
    with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_quotes(data):
    with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_topics():
    with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_topics(data):
    with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_relations():
    with open(RELATIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_relations(data):
    with open(RELATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _save_concepts():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(ALL_DATA, f, ensure_ascii=False, indent=2)

def _save_lite():
    lite = []
    for c in CONCEPTS:
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
            'related_concepts': c.get('related_concepts', []),
        }
        for sc in c.get('sub_concepts', []):
            lc['sub_concepts'].append({
                'id': sc.get('id'),
                'name_zh': sc.get('name_zh'),
                'name_en': sc.get('name_en'),
                'definition': sc.get('definition', ''),
                'definition_source': sc.get('definition_source', ''),
                'explanation': sc.get('explanation', ''),
                'quotes_count': len(sc.get('quotes', [])),
            })
        lite.append(lc)
    with open(LITE_FILE, 'w', encoding='utf-8') as f:
        json.dump(lite, f, ensure_ascii=False)

def _safe_quote_file_name(name):
    return (name or '').replace('/', '_').replace(' ', '_') + '.json'

def _raw_quote_id(quote_id):
    m = re.search(r'-(\d+)$', quote_id or '')
    return '_' + m.group(1) if m else ''

def _delete_source_quote(concept, quote):
    deleted = []
    raw_id = _raw_quote_id(quote.get('id', ''))
    text = quote.get('text', '')
    translation = quote.get('translation', '')
    source = quote.get('source', '')
    fname = _safe_quote_file_name(concept.get('name_en', ''))

    for source_dir in QUOTE_SOURCE_DIRS:
        fpath = os.path.join(source_dir, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        excerpts = data.get('excerpts', [])
        before = len(excerpts)
        kept = []
        removed = 0
        for ex in excerpts:
            same_id = raw_id and ex.get('id') == raw_id
            same_content = (
                ex.get('text_en') == text and
                ex.get('text_zh') == translation and
                ex.get('source') == source
            )
            if same_id or same_content:
                removed += 1
                continue
            kept.append(ex)
        if removed:
            data['excerpts'] = kept
            for key in ('total_after_dedup', 'total_translated'):
                if isinstance(data.get(key), int):
                    data[key] = max(0, data[key] - removed)
            if isinstance(data.get('source'), str):
                data['source'] = re.sub(r'从 \d+ 条', f'从 {len(kept)} 条', data['source'])
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            deleted.append({'file': fpath, 'removed': removed, 'before': before, 'after': len(kept)})
    return deleted

def _rebuild_flat():
    global FLAT, IDX
    IDX = {}
    for c in CONCEPTS:
        IDX[c['id']] = c
        _idx(c.get('sub_concepts', []))
    FLAT = [{
        'id': c['id'], 'name_zh': c['name_zh'],
        'name_en': c['name_en'], 'category': c.get('category',''),
        'quotes_count': len(c.get('quotes',[])),
        'sub_concepts_count': len(c.get('sub_concepts',[])),
    } for c in CONCEPTS]

def _find_concept_by_id(cid):
    for i, c in enumerate(CONCEPTS):
        if c['id'] == cid:
            return i, c
    return None, None

IDX = {}
def _idx(concepts):
    for c in concepts:
        IDX[c['id']] = c
        _idx(c.get('sub_concepts', []))
_idx(CONCEPTS)

FLAT = [{
    'id': c['id'], 'name_zh': c['name_zh'],
    'name_en': c['name_en'], 'category': c.get('category',''),
    'quotes_count': len(c.get('quotes',[])),
    'sub_concepts_count': len(c.get('sub_concepts',[])),
} for c in CONCEPTS]


class LimitedThreadPool(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    max_children = 4  # 最多 4 个并发线程


class H(BaseHTTPRequestHandler):
    server_version = 'SethWiki/3.2'

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        # 启用 gzip 压缩
        ae = self.headers.get('Accept-Encoding', '')
        if 'gzip' in ae:
            import gzip, io
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as f:
                f.write(body)
            compressed = buf.getvalue()
            if len(compressed) < len(body):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(compressed)))
                self.send_header('Vary', 'Accept-Encoding')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(compressed)
                return
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/concepts':
                self._json(200, {'concepts': FLAT, 'total': len(FLAT)})
                return
            if path.startswith('/api/concepts/'):
                cid = path.split('/')[-1]
                c = IDX.get(cid)
                if c:
                    self._json(200, c)
                else:
                    self._json(404, {'error': 'not found'})
                return
            if path == '/api/quotes':
                data = _load_quotes()
                qs = data.get('quotes', [])
                page = int(self._qp('page', 1))
                per = int(self._qp('per', 20))
                q = self._qp('q', '').strip()
                filtered = qs
                if q:
                    ql = q.lower()
                    filtered = [x for x in qs if q in x.get('text','') or q in x.get('translation','') or q in x.get('source','') or x['id'].lower() == ql]
                total = len(filtered)
                start = (page - 1) * per
                end = start + per
                self._json(200, {'quotes': filtered[start:end], 'total': total, 'page': page, 'per': per})
                return
            if path == '/api/topics':
                data = _load_topics()
                self._json(200, data)
                return
            if path == '/api/relations':
                data = _load_relations()
                self._json(200, data)
                return
            if path == '/api/topics/concepts':
                tid = self._qp('topic_id', '')
                rels = _load_relations()
                cids = [r['concept_id'] for r in rels.get('concept_to_topic',[]) if r['topic_id'] == tid]
                result = [IDX[cid] for cid in cids if cid in IDX]
                self._json(200, {'concepts': result})
                return
            if path == '/api/topics/quotes':
                tid = self._qp('topic_id', '')
                rels = _load_relations()
                qids = [r['quote_id'] for r in rels.get('quote_to_topic',[]) if r['topic_id'] == tid]
                quotes = _load_quotes().get('quotes', [])
                qmap = {q['id']: q for q in quotes}
                result = [qmap[qid] for qid in qids if qid in qmap]
                self._json(200, {'quotes': result})
                return
            if path.startswith('/api/topics/'):
                tid = path.split('/')[-1]
                data = _load_topics()
                topic = None
                for t in data.get('topics', []):
                    if t['id'] == tid:
                        topic = t
                        break
                if topic:
                    self._json(200, topic)
                else:
                    self._json(404, {'error': 'topic not found'})
                return
            if path == '/': path = '/index.html'
            fpath = os.path.normpath(os.path.join(DIR, path.lstrip('/')))
            if not fpath.startswith(DIR) or not os.path.isfile(fpath):
                self.send_error(404)
                return
            ct = 'text/html; charset=utf-8'
            if '.json' in path: ct = 'application/json; charset=utf-8'
            elif '.css' in path: ct = 'text/css; charset=utf-8'
            elif '.js' in path: ct = 'application/javascript; charset=utf-8'
            with open(fpath, 'rb') as f:
                body = f.read()
            ae = self.headers.get('Accept-Encoding', '')
            if 'gzip' in ae and len(body) > 512 and '.json' in path:
                import gzip, io
                buf = io.BytesIO()
                with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=6) as f:
                    f.write(body)
                compressed = buf.getvalue()
                if len(compressed) < len(body):
                    self.send_response(200)
                    self.send_header('Content-Type', ct)
                    self.send_header('Content-Encoding', 'gzip')
                    self.send_header('Content-Length', str(len(compressed)))
                    self.send_header('Vary', 'Accept-Encoding')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(compressed)
                    return
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            import traceback; traceback.print_exc()

    def _qp(self, k, d=''):
        qs = urlparse(self.path).query
        params = {}
        if qs:
            for p in qs.split('&'):
                kv = p.split('=', 1)
                if len(kv) == 2:
                    params[kv[0]] = kv[1]
        return params.get(k, d)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
            if path == '/api/concepts':
                cid = body.get('id', '')
                if not cid:
                    cid = 'concept-new-' + str(len(CONCEPTS) + 1)
                    body['id'] = cid
                if cid in IDX:
                    self._json(400, {'error': 'id already exists'})
                    return
                body.setdefault('quotes', [])
                body.setdefault('sub_concepts', [])
                body.setdefault('related_concepts', [])
                CONCEPTS.append(body)
                _save_concepts()
                _rebuild_flat()
                self._json(200, {'ok': True, 'id': cid})
                return
            if path.startswith('/api/concepts/') and path.endswith('/save-quotes'):
                cid = path.split('/')[-2]
                _, c = _find_concept_by_id(cid)
                if not c:
                    self._json(404, {'error': 'not found'})
                    return
                c['quotes'] = body.get('quotes', [])
                _save_concepts()
                _rebuild_flat()
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/concept-group':
                rels = _load_relations()
                cg = rels.get('concept_groups', [])
                cid = body.get('concept_id')
                rel = body.get('related_to')
                exists = False
                for g in cg:
                    if g['concept_id'] == cid:
                        if rel not in g['related_to']:
                            g['related_to'].append(rel)
                        exists = True
                        break
                if not exists:
                    cg.append({'concept_id': cid, 'related_to': [rel]})
                rels['concept_groups'] = cg
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/quote-to-concept':
                rels = _load_relations()
                qtoc = rels.get('quote_to_concept', [])
                qid = body.get('quote_id')
                cid = body.get('concept_id')
                for r in qtoc:
                    if r['quote_id'] == qid and r['concept_id'] == cid:
                        self._json(200, {'ok': True, 'exists': True})
                        return
                qtoc.append({'quote_id': qid, 'concept_id': cid})
                rels['quote_to_concept'] = qtoc
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/concept-to-topic':
                rels = _load_relations()
                ctot = rels.get('concept_to_topic', [])
                cid = body.get('concept_id')
                tid = body.get('topic_id')
                for r in ctot:
                    if r['concept_id'] == cid and r['topic_id'] == tid:
                        self._json(200, {'ok': True, 'exists': True})
                        return
                ctot.append({'concept_id': cid, 'topic_id': tid})
                rels['concept_to_topic'] = ctot
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/quote-to-topic':
                rels = _load_relations()
                qtot = rels.get('quote_to_topic', [])
                qid = body.get('quote_id')
                tid = body.get('topic_id')
                for r in qtot:
                    if r['quote_id'] == qid and r['topic_id'] == tid:
                        self._json(200, {'ok': True, 'exists': True})
                        return
                qtot.append({'quote_id': qid, 'topic_id': tid})
                rels['quote_to_topic'] = qtot
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/create-topic':
                data = _load_topics()
                topics = data.get('topics', [])
                tid = body.get('id')
                for t in topics:
                    if t['id'] == tid:
                        self._json(400, {'error': 'topic id exists'})
                        return
                topics.append({
                    'id': tid,
                    'name_zh': body.get('name_zh', ''),
                    'name_en': body.get('name_en', ''),
                    'description': body.get('description', '')
                })
                data['topics'] = topics
                _save_topics(data)
                self._json(200, {'ok': True})
                return
            if path == '/api/topics':
                data = _load_topics()
                topics = data.get('topics', [])
                tid = body.get('id')
                for t in topics:
                    if t['id'] == tid:
                        t['name_zh'] = body.get('name_zh', t['name_zh'])
                        t['name_en'] = body.get('name_en', t['name_en'])
                        t['description'] = body.get('description', t['description'])
                        break
                _save_topics(data)
                self._json(200, {'ok': True})
                return
            self._json(404, {'error': 'not found'})
        except Exception:
            import traceback; traceback.print_exc()
            self._json(500, {'error': 'internal error'})

    def do_DELETE(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
            if re.match(r'^/api/concepts/[^/]+/quotes/[^/]+$', path):
                parts = path.split('/')
                cid = parts[3]
                qid = parts[5]
                _, c = _find_concept_by_id(cid)
                if not c:
                    self._json(404, {'error': 'concept not found'})
                    return
                quotes = c.get('quotes', [])
                qidx = None
                for i, q in enumerate(quotes):
                    if q.get('id') == qid:
                        qidx = i
                        break
                if qidx is None:
                    self._json(404, {'error': 'quote not found'})
                    return
                removed_quote = quotes.pop(qidx)
                source_deleted = _delete_source_quote(c, removed_quote)
                _save_concepts()
                _save_lite()
                _rebuild_flat()
                self._json(200, {
                    'ok': True,
                    'deleted_quote_id': qid,
                    'remaining': len(quotes),
                    'source_deleted': source_deleted,
                })
                return
            if path.startswith('/api/concepts/'):
                cid = path.split('/')[-1]
                idx, c = _find_concept_by_id(cid)
                if not c:
                    self._json(404, {'error': 'not found'})
                    return
                CONCEPTS.pop(idx)
                if cid in IDX:
                    del IDX[cid]
                _save_concepts()
                _rebuild_flat()
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/concept-group':
                rels = _load_relations()
                cg = rels.get('concept_groups', [])
                cid = body.get('concept_id')
                rel = body.get('related_to')
                for g in cg:
                    if g['concept_id'] == cid:
                        g['related_to'] = [x for x in g['related_to'] if x != rel]
                        break
                rels['concept_groups'] = cg
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/quote-to-concept':
                rels = _load_relations()
                qtoc = rels.get('quote_to_concept', [])
                rels['quote_to_concept'] = [r for r in qtoc if not (r['quote_id'] == body.get('quote_id') and r['concept_id'] == body.get('concept_id'))]
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/concept-to-topic':
                rels = _load_relations()
                ctot = rels.get('concept_to_topic', [])
                rels['concept_to_topic'] = [r for r in ctot if not (r['concept_id'] == body.get('concept_id') and r['topic_id'] == body.get('topic_id'))]
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            if path == '/api/relations/quote-to-topic':
                rels = _load_relations()
                qtot = rels.get('quote_to_topic', [])
                rels['quote_to_topic'] = [r for r in qtot if not (r['quote_id'] == body.get('quote_id') and r['topic_id'] == body.get('topic_id'))]
                _save_relations(rels)
                self._json(200, {'ok': True})
                return
            self._json(404, {'error': 'not found'})
        except Exception:
            import traceback; traceback.print_exc()
            self._json(500, {'error': 'internal error'})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_PUT(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
            if path.startswith('/api/concepts/'):
                cid = path.split('/')[-1]
                idx, c = _find_concept_by_id(cid)
                if not c:
                    self._json(404, {'error': 'not found'})
                    return
                # Update fields
                c['name_zh'] = body.get('name_zh', c.get('name_zh', ''))
                c['name_en'] = body.get('name_en', c.get('name_en', ''))
                c['category'] = body.get('category', c.get('category', ''))
                c['definition'] = body.get('definition', c.get('definition', []))
                c['definition_en'] = body.get('definition_en', c.get('definition_en', ''))
                c['definition_source'] = body.get('definition_source', c.get('definition_source', ''))
                c['explanation'] = body.get('explanation', c.get('explanation', ''))
                if 'quotes' in body:
                    c['quotes'] = body['quotes']
                if 'sub_concepts' in body:
                    c['sub_concepts'] = body['sub_concepts']
                if 'related_concepts' in body:
                    c['related_concepts'] = body['related_concepts']
                _save_concepts()
                _rebuild_flat()
                self._json(200, {'ok': True})
                return
            self._json(404, {'error': 'not found'})
        except Exception:
            import traceback; traceback.print_exc()
            self._json(500, {'error': 'internal error'})

    def log_message(self, fmt, *args):
        pass


if __name__ == '__main__':
    port = 8081
    print(f'  赛斯宇宙 Wiki 服务器已启动  ({len(CONCEPTS)} 概念, threading)')
    print(f'  前端页面: http://localhost:{port}')
    print(f'  管理后台: http://localhost:{port}/admin.html')
    print(f'  内容管理: http://localhost:{port}/admin-content.html')
    s = LimitedThreadPool(('0.0.0.0', port), H)
    s.serve_forever()
