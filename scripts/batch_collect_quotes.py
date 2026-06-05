#!/usr/bin/env python3
"""
概念摘录批量预处理脚本

全书匹配 → 自然去重 → 全部翻译 → concept-quotes-full/{概念}.json

试点概念：Beliefs, Ego, Consciousness
"""

import json
import os
import re
import sys
import glob
import time
import shutil
from datetime import datetime
from openai import OpenAI
try:
    from concept_utils import BASE_DIR, PROCESSED_DIR, load_concept_table, safe_concept_name, definition_patterns_for
except ImportError:
    from scripts.concept_utils import BASE_DIR, PROCESSED_DIR, load_concept_table, safe_concept_name, definition_patterns_for

# ============================
# API 配置
# ============================
API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
BASE_URL = 'https://api.deepseek.com'
MODEL = 'deepseek-chat'

client = None

# ============================
# 路径配置
# ============================
BASE_DIR = str(BASE_DIR)
PROCESSED_DIR = str(PROCESSED_DIR)
FULL_DIR = os.path.join(BASE_DIR, 'concept-quotes-full')   # 最终摘录库（机器 + 人工维护）
REPORT_DIR = os.path.join(BASE_DIR, 'reports')
os.makedirs(FULL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

DEDUP_SIMILARITY = 0.85
REQUIRE_PREFIX_MATCH = os.environ.get('SETH_REQUIRE_PREFIX_MATCH', '0') == '1'
RELATED_CONCEPT_STOPLIST = {'will'}
QUOTE_ROLE_ORDER = {
    'definition': 10,
    'description': 20,
    'mechanism': 30,
    'example': 40,
    'practice': 50,
    'warning': 60,
    'uncategorized': 90,
}

BIOGRAPHICAL_NOTE_PATTERNS = [
    # Session bookkeeping / break notes.
    (r'^\s*[\(（]\s*(?:break|end)\s+at\b', 'break_or_end_note'),
    (r'^\s*[\(（]\s*(?:pause|long pause|one of many pauses)\b', 'stage_direction'),
    (r'^\s*[\(（].{0,120}\b(?:break|end)\s+at\b', 'break_or_end_note'),

    # Jane's trance/dissociation state as observer notes rather than Seth teaching.
    (r'\bJane\b.{0,120}\b(?:trance|dissociated|dissociation|came out|eyes|voice|delivery|speaking)\b', 'jane_session_note'),
    (r'\b(?:trance|dissociated|dissociation|came out)\b.{0,120}\bJane\b', 'jane_session_note'),
    (r'\bJane\b', 'jane_session_note'),
    (r'\bRuburt\b.{0,120}\bas Jane\b.{0,120}\btrance\b', 'jane_session_note'),

    # Rob / editor / publication framing.
    (r'\bRob(?:\'s)?\b', 'rob_note'),
    (r'\bI averaged\b.{0,120}\bsessions?\b', 'production_note'),
    (r'\b(?:dictation|break times?|trance time)\b.{0,120}\b(?:sessions?|volumes?|book)\b', 'production_note'),
    (r'\b(?:we could have presented|this book should cover|in this book|for the record|I\'m summarizing|opening notes|closing notes)\b', 'publication_note'),
    (r'^\s*(?:appendix|chapter|session)\s+\d+\b', 'heading_note'),
]

SEMANTIC_TEACHING_PATTERNS = [
    r'\b(?:you|one)\s+(?:must|should|can|will|may)\s+(?:understand|realize|remember|recognize|learn|discover|consider)\b',
    r'\b(?:it is|it becomes|this is|this means|this does not mean)\b',
    r'\b(?:in other words|that is to say|basically|essentially|fundamentally)\b',
]

SEMANTIC_MECHANISM_PATTERNS = [
    r'\b(?:forms?|creates?|affects?|organizes?|operates?|functions?|directs?|focuses?|perceives?|expresses?|manifests?|materializes?)\b',
    r'\b(?:results?\s+in|leads?\s+to|is\s+responsible\s+for|is\s+connected\s+with|is\s+related\s+to)\b',
    r'\b(?:relationship|connection|process|mechanism|method|effect|cause|source|nature)\b',
]

QUOTE_ROLE_PATTERNS = [
    ('definition', [
        r'\b(?:is|are|means|refers\s+to|can\s+be\s+defined\s+as)\b',
        r'\b(?:called|known\s+as|termed)\b',
    ]),
    ('practice', [
        r'\b(?:try|practice|exercise|method|technique|write down|examine|ask yourself|suggestion[s]?)\b',
        r'\b(?:you should|you must|you can|you may)\b',
    ]),
    ('description', [
        r'\b(?:distinction|difference|different from|not the same|rather than|instead of|unlike|separate from)\b',
    ]),
    ('warning', [
        r'\b(?:danger|risk|mistake|misunderstand|confusion|limitation|problem|difficulty|fear|block)\b',
    ]),
    ('example', [
        r'\b(?:for example|for instance|as an example|such as|case in point|suppose|say,)\b',
    ]),
    ('mechanism', [
        r'\b(?:forms?|creates?|affects?|organizes?|operates?|functions?|directs?|focuses?|perceives?|expresses?|manifests?|materializes?)\b',
        r'\b(?:results?\s+in|leads?\s+to|is\s+responsible\s+for|is\s+connected\s+with|is\s+related\s+to)\b',
    ]),
    ('description', [
        r'\b(?:all|always|never|basically|essentially|fundamentally|the nature of|inherent|primary|basic)\b',
    ]),
]

# ============================
# 自动备份函数
# ============================
BACKUP_DIR = os.path.join(BASE_DIR, 'scripts', 'backup')
os.makedirs(BACKUP_DIR, exist_ok=True)

def auto_backup(filepath, backup_dir=BACKUP_DIR, max_backups=10):
    """带时间戳的自动备份，只保留最近 N 个备份"""
    if not os.path.exists(filepath):
        return None
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    basename = os.path.splitext(os.path.basename(filepath))[0]
    ext = os.path.splitext(os.path.basename(filepath))[1]
    backup_path = os.path.join(backup_dir, f'{basename}.{timestamp}{ext}')
    shutil.copy2(filepath, backup_path)
    # 清理旧备份
    existing = sorted([f for f in os.listdir(backup_dir) if f.startswith(basename) and f.endswith(ext)])
    for old_file in existing[:-max_backups]:
        os.remove(os.path.join(backup_dir, old_file))
    print(f"  已自动备份: {backup_path}")
    return backup_path

# ============================
# 概念匹配规则
# ============================
CONCEPT_RULES = {
    "Action": [r'\baction[s]?\b'],
    "Beliefs": {
        "include": [r'\bbelief[s]?\b'],
        "context": [
            r'\b(?:reality|experience|physical|body|health|emotion[s]?|feeling[s]?|thought[s]?)\b',
            r'\b(?:materializ|manifest|create|change|beneficial|limiting|conscious|invisible)\b',
        ],
    },
    "Camouflage / Camouflage system": [r'\bcamouflage\b', r'\bcamouflages\b'],
    "Consciousness": {
        "include": [r'\bconsciousness\b'],
        "context": [
            r'\b(?:awareness|self|focus|attention|body|physical|reality|dream|identity)\b',
            r'\b(?:inner|molecular|cellular|forms?|creates?|perceives?|operates?|state)\b',
        ],
    },
    "Dream universe": [r'\bdream\s+universe\b', r'\bdream-world\b', r'\bdream\b.*\buniverse\b'],
    "Ego": {
        "include": [r'\bego\b', r'\begos\b'],
        "context": [
            r'\b(?:self|personality|identity|conscious|subconscious|inner|outer|action)\b',
            r'\b(?:controls?|focus|directive|stability|adjust|protect|specialized)\b',
        ],
    },
    "Outer ego": [r'\bouter\s+ego\b'],
    "Inner ego": [r'\binner\s+ego\b'],
    "Electromagnetic reality": [r'\belectromagnetic\b.*\breality\b', r'\bEM\b.*\breality\b'],
    "Emotions / Feelings": [r'\bemotion[s]?\b', r'\bfeeling[s]?\b'],
    "Entity": [r'\bentit(?:y|ies)\b'],
    "Whole Self": [r'\bwhole\s+self\b', r'\bwhole\s+self\s+of\s+self\b'],
    "Expectation": [r'\bexpectation[s]?\b'],
    "Framework 1": [r'\b[Ff]ramework\s+1\b', r'\b[Ff]ramework\s+one\b'],
    "Framework 2": [r'\b[Ff]ramework\s+2\b', r'\b[Ff]ramework\s+two\b'],
    "framework": [r'\bframework[s]?\b'],
    "hypnosis": [r'\bhypnosis\b', r'\bhypnotic\b', r'\bhypnotize\b'],
    "Identity": [r'\bidentit(?:y|ies)\b'],
    "Imagination": [r'\bimagination\b', r'\bimagin(?:e|ing|es|ed)\b'],
    "Inner self": [r'\binner\s+self\b', r'\binner\s+selves\b'],
    "Inner Senses": [r'\binner\s+sens(?:e|es)\b'],
    "Physical senses": [r'\bphysical\s+sens(?:e|es)\b'],
    "Psychological Time": [r'\bpsychological\s+time\b'],
    "Reincarnation": [r'\breincarnation[s]?\b'],
    "Spacious Present": [r'\bspacious\s+present\b', r'\b[Ss]pacious\s+[Pp]resent\b'],
    "Subconscious": [r'\bsubconscious\b', r'\bsubconsciously\b'],
    "The point of power is in the present": [r'\bpoint\s+of\s+power\b'],
    "Thoughts": [r'\bthought[s]?\b'],
    "Idea constructions": [r'\bidea\s+construction[s]?\b', r'\bidea[s]?\s+construct'],
    "Vitality": [r'\bvitality\b'],
    "awareness": [r'\bawareness\b', r'\baware\b'],
    "intent": [r'\bintent[s]?\b', r'\bintentions?\b'],
    "mind": [r'\bmind[s]?\b'],
    "personality": [r'\bpersonalit(?:y|ies)\b'],
    "present": [r'\bpresent\b'],
    "physical reality": [r'\bphysical\s+reality\b', r'\bphysical\s+realities\b'],
    "reality": [r'\breality\b', r'\brealit(?:y|ies)\b'],
    "self": [r'\bself\b', r'\bselves\b'],
    "soul": [r'\bsoul[s]?\b'],
    "unconscious": [r'\bunconscious\b', r'\bunconsciously\b'],
    "will": {
        "include": [
            r'\bfree\s+will\b',
            r'\bwill[-\s]?power\b',
            r'\b(?:conscious|personal|inner|creative|directed)\s+will\b',
            r'\b(?:exercise|exercising|use|using|focus|focusing|direct|directing)\s+(?:your\s+|the\s+|one\'s\s+|his\s+|her\s+|their\s+|its\s+|our\s+|own\s+)will\b',
            r'\b(?:act|acts|action)\s+of\s+will\b',
            r'\bwill\s+to\s+(?:live|create|choose|act|be|become|survive|change)\b',
            r'\b(?:desire|intent|intention|choice|purpose)\s+and\s+will\b',
            r'\bwill\s+and\s+(?:desire|intent|intention|choice|purpose)\b',
            r'\bwilled\b',
            r'\bwillingness\b',
        ],
        "context": [
            r'\b(?:desire|intent|intention|choice|purpose|decision|action|creative|conscious|focus|power)\b',
            r'\b(?:directs?|chooses?|creates?|acts?|focuses?|changes?|decides?)\b',
        ],
    },
    "dissociate/trance": {
        "include": [r'\bdissociat', r'\btrance\b'],
        "context": [
            r'\b(?:consciousness|awareness|focus|attention|state|hypnot|suggestion)\b',
            r'\b(?:conscious mind|ordinary consciousness|deep trance|medium trance|dissociation)\b',
        ],
    },
    "Direct perception": [r'\bdirect\s+perception\b', r'\bdirect\s+perceive\b'],
    "Conceptual Sense": [r'\bconceptual\s+sens(?:e|es)\b'],
    "Mental image": [r'\bmental\s+image[s]?\b', r'\bmental\s+imagery\b'],
    "Natural aggression": [r'\bnatural\s+aggression\b', r'\bnatural\s+aggressive\b'],
    "Tissue capsule": [r'\btissue\s+capsule[s]?\b'],
    "gestalt": [r'\bgestalt[s]?\b'],
}



def load_all_paragraphs():
    all_paragraphs = []
    json_files = sorted(glob.glob(os.path.join(PROCESSED_DIR, '*.json')))
    for fpath in json_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            continue
        for p in data.get('all_content', []):
            p['_book'] = data.get('book_title', '')
            p['_source_file'] = os.path.basename(fpath)
            all_paragraphs.append(p)
    print(f"  加载 {len(all_paragraphs)} 个段落，来自 {len(json_files)} 个文件")
    return all_paragraphs


def match_concept(text, patterns):
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def count_matches(text, patterns):
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


def concept_match_patterns(concept_name):
    rule = CONCEPT_RULES.get(concept_name, [rf'\b{re.escape(concept_name)}\b'])
    if isinstance(rule, dict):
        return rule.get('include', [])
    return rule


def related_concepts_for_text(text, current_concept='', max_related=8):
    related = []
    concept_table = load_concept_table()
    for concept_en, info in concept_table.items():
        if concept_en == current_concept:
            continue
        if concept_en in RELATED_CONCEPT_STOPLIST:
            continue
        patterns = concept_match_patterns(concept_en)
        match_count = count_matches(text, patterns)
        if match_count <= 0:
            continue
        related.append({
            'id': info['id'],
            'name_zh': info['zh'],
            'name_en': info['en'],
            'match_count': match_count,
        })
    related.sort(key=lambda item: (-item['match_count'], item['id']))
    return related[:max_related]


def format_source(source_dict):
    if not source_dict or source_dict.get('type') == 'unknown':
        return ""
    session = source_dict.get('session_number', '')
    if session:
        return f"Session {session}"
    return ""


def is_good_excerpt(text):
    if len(text.strip()) < 30:
        return False
    if re.match(r'^(Cover|Contents|Index|Chapter\s+\d+|Session\s+\d+)$', text.strip(), re.IGNORECASE):
        return False
    return True


def biographical_note_reason(text):
    normalized = re.sub(r'\s+', ' ', text or '').strip()
    for pattern, reason in BIOGRAPHICAL_NOTE_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return reason
    return ''


def is_biographical_note(text):
    return bool(biographical_note_reason(text))


def extract_session_number(source_dict):
    if not source_dict:
        return None
    session = source_dict.get('session_number', '')
    if session:
        try:
            return int(session)
        except (ValueError, TypeError):
            return None
    return None


def text_fingerprint(text, n=6):
    t = text.lower().strip()
    return frozenset(t[i:i+n] for i in range(max(0, len(t) - n + 1)))


def jaccard_similarity(set1, set2):
    if not set1 and not set2:
        return 1.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0.0


def score_excerpt(text, concept_name, patterns, match_count):
    t = text.lower()
    c = concept_name.lower()
    
    density_score = min(match_count * 10, 40)
    
    cleaned = re.sub(r'\((?:\d+:\d+|Pause\.?|Jane.*?)\)', '', t)
    effective_len = len(cleaned.strip())
    info_score = min(effective_len / 20, 25)
    
    def_score = 0
    for dp in definition_patterns_for(concept_name):
        if re.search(dp, t, re.IGNORECASE):
            def_score += 10
            break
    
    if any(w in t for w in ['essentially', 'basically', 'fundamentally', 'in other words', 'that is to say']):
        def_score += 5
    
    unique_score = min(len(t) / 50, 15)
    
    return density_score + info_score + def_score + unique_score


def compile_rule(concept_name):
    rule = CONCEPT_RULES.get(concept_name, [rf'\b{re.escape(concept_name)}\b'])
    if isinstance(rule, dict):
        return {
            'include': rule.get('include', []),
            'exclude': rule.get('exclude', []),
            'context': rule.get('context', []),
        }
    return {'include': rule, 'exclude': [], 'context': []}


def passes_rule(text, compiled_rule):
    for pattern in compiled_rule['exclude']:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    return True


def semantic_relevance_reason(text, concept_name, compiled_rule):
    normalized = re.sub(r'\s+', ' ', text or '').strip()
    lowered = normalized.lower()

    for pattern in definition_patterns_for(concept_name):
        if re.search(pattern, lowered, re.IGNORECASE):
            return 'definition'

    for pattern in compiled_rule.get('context', []):
        if re.search(pattern, normalized, re.IGNORECASE):
            return 'concept_context'

    for pattern in SEMANTIC_TEACHING_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return 'teaching_language'

    for pattern in SEMANTIC_MECHANISM_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return 'mechanism_language'

    return ''


def is_semantically_relevant(text, concept_name, compiled_rule):
    return bool(semantic_relevance_reason(text, concept_name, compiled_rule))


def classify_quote(text, concept_name, semantic_reason='', score=0):
    normalized = re.sub(r'\s+', ' ', text or '').strip()
    lowered = normalized.lower()
    role = 'uncategorized'

    if semantic_reason == 'definition':
        role = 'definition'
    else:
        for candidate_role, patterns in QUOTE_ROLE_PATTERNS:
            if candidate_role == 'definition':
                continue
            if any(re.search(pattern, lowered, re.IGNORECASE) for pattern in patterns):
                role = candidate_role
                break
        if role == 'uncategorized' and semantic_reason == 'mechanism_language':
            role = 'mechanism'
        elif role == 'uncategorized' and semantic_reason == 'teaching_language':
            role = 'description'
        elif role == 'uncategorized' and semantic_reason == 'concept_context':
            role = 'description'

    if role == 'definition':
        semantic_score = 5
    elif role in ('description', 'mechanism'):
        semantic_score = 4
    elif role in ('practice', 'example'):
        semantic_score = 3
    elif role == 'warning':
        semantic_score = 3
    else:
        semantic_score = 2 if score >= 50 else 1

    return {
        'quote_role': role,
        'semantic_score': semantic_score,
        'reading_order': QUOTE_ROLE_ORDER.get(role, 90),
    }


def has_prefix_match(text, patterns):
    first_360 = text[:360]
    return any(re.search(pattern, first_360, re.IGNORECASE) for pattern in patterns)


def load_translation_cache(full_file):
    cache = {}
    if not os.path.exists(full_file):
        return cache
    with open(full_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for ex in data.get('excerpts', []):
        text = ex.get('text_en', '')
        translation = ex.get('text_zh', '')
        if text and translation:
            cache[text] = translation
    return cache


def deduplicate_excerpts(excerpts, similarity_threshold=DEDUP_SIMILARITY):
    """自然去重，不人为设上限"""
    if not excerpts:
        return []
    
    excerpts.sort(key=lambda x: -x['score'])
    
    result = []
    result_fps = []
    
    for ex in excerpts:
        fp = text_fingerprint(ex['text'])
        is_dup = False
        
        for kept_fp in result_fps:
            sim = jaccard_similarity(fp, kept_fp)
            if sim > similarity_threshold:
                is_dup = True
                break
        
        if not is_dup:
            result.append(ex)
            result_fps.append(fp)
    
    return result


def call_llm(prompt, system_prompt, max_retries=2):
    global client
    if not API_KEY:
        raise RuntimeError('缺少 DEEPSEEK_API_KEY 环境变量，无法调用 DeepSeek 翻译。')
    if client is None:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=int(os.environ.get('SETH_TRANSLATE_MAX_TOKENS', '6000')),
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  API 错误 (尝试 {attempt+1}/{max_retries}): {e}")
            time.sleep(5)
    return ""


def batch_translate_quotes(quotes, concept_name, translation_cache=None):
    results = []
    batch_size = max(1, int(os.environ.get('SETH_TRANSLATE_BATCH_SIZE', '6')))
    translation_cache = translation_cache or {}
    
    for i in range(0, len(quotes), batch_size):
        batch = quotes[i:i+batch_size]
        cached = [translation_cache.get(q['text'], '') for q in batch]
        if all(cached):
            results.extend(cached)
            print(f"  翻译批次 {i // batch_size + 1}: 使用缓存 {len(cached)} 条")
            continue

        batch_num = i // batch_size + 1
        total_batches = (len(quotes) + batch_size - 1) // batch_size
        print(f"  翻译批次 {batch_num}/{total_batches} (摘录 {i+1}-{i+len(batch)})...")
        
        quote_list = "\n".join([f"[{j+1}] {q['text']}" for j, q in enumerate(batch)])
        
        system_prompt = f"""你是一位专业的翻译家，精通英文到中文的文学翻译。

请逐条翻译以下英文为中文。
严格按以下格式输出，每条翻译占一行，以方括号序号开头：
[1] 第一条翻译
[2] 第二条翻译
...
[{len(batch)}] 最后一条翻译

不要任何解释，只输出翻译结果。哲学/灵性术语使用赛斯资料的常用译法。"""
        
        prompt = f"请翻译以下关于 '{concept_name}' 的英文摘录：\n\n{quote_list}"
        
        response = call_llm(prompt, system_prompt)
        
        if response:
            translated = re.findall(r'\[\d+\]\s*(.+)', response)
            
            if len(translated) == 0:
                lines = response.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    cleaned = re.sub(r'^\d+[\.\、\s\-\)]\s*', '', line).strip()
                    if cleaned and len(cleaned) > 5:
                        translated.append(cleaned)
            
            if len(translated) == len(batch):
                results.extend(translated)
                print(f"    ✓ {len(translated)} 条翻译成功")
            elif len(translated) > len(batch):
                results.extend(translated[:len(batch)])
                print(f"    ✓ {len(batch)} 条翻译成功（丢弃多余 {len(translated) - len(batch)} 条）")
            elif len(translated) > 0:
                results.extend(translated)
                for _ in range(len(batch) - len(translated)):
                    results.append("")
                print(f"    ⚠ {len(translated)}/{len(batch)} 条翻译成功")
            else:
                for _ in range(len(batch)):
                    results.append("")
                print(f"    ✗ 解析失败")
        else:
            for _ in range(len(batch)):
                results.append("")
            print(f"    ✗ API 调用失败")
        
        time.sleep(1.5)
    
    return results[:len(quotes)]


def build_excerpt_list(excerpts, translations):
    output = []
    for idx, ex in enumerate(excerpts):
        entry = {
            "id": f"_{idx+1:04d}",
            "text_en": ex['text'],
            "text_zh": translations[idx] if idx < len(translations) else "",
            "source": ex['source_str'],
            "book": ex['book'],
            "source_file": ex.get('source_file', ''),
            "source_raw": ex.get('source', {}),
            "score": round(ex['score'], 1),
            "match_count": ex['match_count'],
            "prefix_match": ex.get('prefix_match', False),
            "semantic_reason": ex.get('semantic_reason', ''),
            "quote_role": ex.get('quote_role', ''),
            "semantic_score": ex.get('semantic_score', 0),
            "reading_order": ex.get('reading_order', 90),
            "related_concepts": ex.get('related_concepts', []),
        }
        if ex.get('type'):
            entry['type'] = ex['type']
        output.append(entry)
    return output


def compact_text(text, max_len=220):
    text = re.sub(r'\s+', ' ', text or '').strip()
    return text if len(text) <= max_len else text[:max_len].rstrip() + '...'


def write_quality_report(concept_name, zh_name, candidates, deduped, translated_count, rejected_counts=None):
    rejected_counts = rejected_counts or {}
    safe_name = safe_concept_name(concept_name)
    report_file = os.path.join(REPORT_DIR, f'{safe_name}.md')
    sessions = {
        extract_session_number(ex.get('source', {}))
        for ex in deduped
        if extract_session_number(ex.get('source', {}))
    }
    prefix_count = sum(1 for ex in deduped if ex.get('prefix_match'))
    scores = [ex.get('score', 0) for ex in deduped]
    match_counts = [ex.get('match_count', 0) for ex in deduped]
    low_samples = sorted(deduped, key=lambda ex: ex.get('score', 0))[:10]

    lines = [
        f'# {concept_name} / {zh_name} 质量报告',
        '',
        f'- 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'- 原始召回: {rejected_counts.get("raw_matched", len(candidates))}',
        f'- 入库候选: {len(candidates)}',
        f'- 剔除 biographical_note / noise: {rejected_counts.get("biographical_note", 0)}',
        f'- 规则排除: {rejected_counts.get("rule_excluded", 0)}',
        f'- 语义门槛排除: {rejected_counts.get("semantic_excluded", 0)}',
        f'- 前缀排除: {rejected_counts.get("prefix_excluded", 0)}',
        f'- 去重后: {len(deduped)}',
        f'- 翻译成功: {translated_count} / {len(deduped)}',
        f'- Session 覆盖: {len(sessions)}',
        f'- 前 360 字符命中: {prefix_count} / {len(deduped)}',
    ]
    if scores:
        lines.extend([
            f'- 评分范围: {min(scores):.1f} ~ {max(scores):.1f}',
            f'- 平均评分: {sum(scores) / len(scores):.1f}',
        ])
    if match_counts:
        lines.append(f'- 平均匹配次数: {sum(match_counts) / len(match_counts):.1f}')

    top_samples = sorted(deduped, key=lambda ex: ex.get('score', 0), reverse=True)[:20]
    lines.extend(['', '## Top 20 样例', ''])
    for idx, ex in enumerate(top_samples, 1):
        lines.extend([
            f'### {idx}. {ex.get("source_str", "")} / score {ex.get("score", 0):.1f}',
            '',
            compact_text(ex.get('text', '')),
            '',
        ])

    lines.extend(['', '## 低分样例', ''])
    for idx, ex in enumerate(low_samples, 1):
        lines.extend([
            f'### {idx}. {ex.get("source_str", "")} / score {ex.get("score", 0):.1f}',
            '',
            compact_text(ex.get('text', '')),
            '',
        ])

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return report_file


def process_concept(concept_name, zh_name, all_paragraphs):
    print(f"\n{'='*60}")
    print(f"处理: {concept_name} ({zh_name})")
    print(f"{'='*60}")
    
    safe_name = safe_concept_name(concept_name)
    full_file = os.path.join(FULL_DIR, f"{safe_name}.json")
    translation_cache = load_translation_cache(full_file)
    
    # 如果文件已存在，先备份
    if os.path.exists(full_file):
        auto_backup(full_file)
    
    compiled_rule = compile_rule(concept_name)
    patterns = compiled_rule['include']
    
    # === 阶段一：匹配 → 去重 → 翻译 → 保存完整库 ===
    print("\n[阶段一] 全书匹配 + 自然去重...")
    candidates = []
    seen = set()
    rejected_counts = {
        'raw_matched': 0,
        'biographical_note': 0,
        'rule_excluded': 0,
        'semantic_excluded': 0,
        'prefix_excluded': 0,
    }
    
    for p in all_paragraphs:
        # 只摘录 Seth 口述的内容
        if p.get('type') != 'seth':
            continue
        
        text = p.get('text', '').strip()
        if not text or not is_good_excerpt(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        
        match_count = count_matches(text, patterns)
        if match_count == 0:
            continue
        rejected_counts['raw_matched'] += 1

        prefix_match = has_prefix_match(text, patterns)
        if REQUIRE_PREFIX_MATCH and not prefix_match:
            rejected_counts['prefix_excluded'] += 1
            continue
        if not passes_rule(text, compiled_rule):
            rejected_counts['rule_excluded'] += 1
            continue
        if is_biographical_note(text):
            rejected_counts['biographical_note'] += 1
            continue
        semantic_reason = semantic_relevance_reason(text, concept_name, compiled_rule)
        if not semantic_reason:
            rejected_counts['semantic_excluded'] += 1
            continue
        
        source = format_source(p.get('source', {}))
        if not source:
            continue
        
        score = score_excerpt(text, concept_name, patterns, match_count)
        if prefix_match:
            score += 8
        classification = classify_quote(text, concept_name, semantic_reason, score)
        candidates.append({
            'text': text,
            'source': p.get('source', {}),
            'source_str': source,
            'book': p.get('_book', ''),
            'source_file': p.get('_source_file', ''),
            'match_count': match_count,
            'score': score,
            'prefix_match': prefix_match,
            'semantic_reason': semantic_reason,
            **classification,
            'related_concepts': related_concepts_for_text(text, concept_name),
            'type': p.get('type', ''),
        })
    
    print(f"  初始匹配: {len(candidates)} 条")
    print(f"  原始召回: {rejected_counts['raw_matched']} 条")
    print(f"  剔除 biographical_note / noise: {rejected_counts['biographical_note']} 条")
    print(f"  语义门槛排除: {rejected_counts['semantic_excluded']} 条")
    
    print(f"  自然去重中...")
    deduped = deduplicate_excerpts(candidates)
    print(f"  去重后: {len(deduped)} 条（自然结果，无人工截断）")
    if not deduped:
        write_quality_report(concept_name, zh_name, candidates, deduped, 0, rejected_counts)
        print("  无可用摘录，跳过翻译与保存")
        return {
            'concept': concept_name,
            'matched': len(candidates),
            'deduped': 0,
            'translated': 0,
        }
    
    unique_sessions = set()
    for ex in deduped:
        s = extract_session_number(ex.get('source', {}))
        if s:
            unique_sessions.add(s)
    print(f"  Session覆盖: {len(unique_sessions)} 个")
    
    # 全部翻译
    print(f"\n[阶段一] 批量翻译全部 {len(deduped)} 条摘录...")
    translations_full = batch_translate_quotes(deduped, concept_name, translation_cache)
    translated_count = len([t for t in translations_full if t])
    print(f"  翻译完成 {translated_count} / {len(deduped)} 条")
    
    # 保存完整库
    full_output = {
        "concept_name_en": concept_name,
        "concept_name_zh": zh_name,
        "total_matched_initial": len(candidates),
        "total_after_dedup": len(deduped),
        "total_translated": translated_count,
        "excerpts": build_excerpt_list(deduped, translations_full),
    }
    
    with open(full_file, 'w', encoding='utf-8') as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[阶段一] 最终摘录库已保存: {full_file}")
    print(f"  文件大小: {os.path.getsize(full_file)} bytes")
    print(f"  摘录数: {len(full_output['excerpts'])}")

    report_file = write_quality_report(
        concept_name,
        zh_name,
        candidates,
        deduped,
        translated_count,
        rejected_counts,
    )
    print(f"  质量报告: {report_file}")
    
    # Git 提示
    print(f"\n提示: 运行 'cd {BASE_DIR} && git add -A && git commit -m \"add {concept_name}\"' 保存版本")
    
    return {
        'concept': concept_name,
        'matched': len(candidates),
        'deduped': len(deduped),
        'translated': translated_count,
    }


def main():
    # 从命令行参数获取概念名，默认跑试点概念
    if len(sys.argv) > 1:
        pilot_concepts = [sys.argv[1]]
    else:
        pilot_concepts = ["Beliefs", "Ego", "Consciousness", "dissociate/trance"]
    
    concepts_map = load_concept_table()
    
    print("加载全书段落...")
    all_paragraphs = load_all_paragraphs()
    
    results = []
    for concept_name in pilot_concepts:
        if concept_name not in concepts_map:
            print(f"错误: 未找到概念 '{concept_name}'")
            continue
        
        info = concepts_map[concept_name]
        zh_name = info['zh']
        
        result = process_concept(concept_name, zh_name, all_paragraphs)
        if result:
            results.append(result)
    
    # 总结
    print(f"\n{'='*60}")
    print("试点概念处理完成总结")
    print(f"{'='*60}")
    print(f"{'概念':<25} | {'初始匹配':>6} | {'去重后':>6} | {'已翻译':>6}")
    print("-" * 60)
    for r in results:
        print(f"{r['concept']:<25} | {r['matched']:>6} | {r['deduped']:>6} | {r['translated']:>6}")


if __name__ == '__main__':
    main()
