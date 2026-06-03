#!/usr/bin/env python3
"""
概念摘录批量预处理脚本 - 两阶段流程

阶段一：全书匹配 → 自然去重 → 全部翻译 → concept-quotes-full/{概念}.json (完整库)
阶段二：从完整库精选 top N → concept-quotes/{概念}.json (精选库)

试点概念：Beliefs, Ego, Consciousness
"""

import json
import os
import re
import sys
import glob
import time
from openai import OpenAI

# ============================
# API 配置
# ============================
API_KEY = 'sk-5b523bc2e0674033b240ea536041cf60'
BASE_URL = 'https://api.deepseek.com'
MODEL = 'deepseek-chat'

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ============================
# 概念匹配规则
# ============================
CONCEPT_RULES = {
    "Action": [r'\baction[s]?\b'],
    "Beliefs": [r'\bbelief[s]?\b'],
    "Camouflage / Camouflage system": [r'\bcamouflage\b', r'\bcamouflages\b'],
    "Consciousness": [r'\bconsciousness\b'],
    "Dream universe": [r'\bdream\s+universe\b', r'\bdream-world\b', r'\bdream\b.*\buniverse\b'],
    "Ego": [r'\bego\b', r'\begos\b'],
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
    "will": [r'\bwill\b'],
    "dissociate/trance": [r'\bdissociat', r'\btrance\b'],
    "Direct perception": [r'\bdirect\s+perception\b', r'\bdirect\s+perceive\b'],
    "Conceptual Sense": [r'\bconceptual\s+sens(?:e|es)\b'],
    "Mental image": [r'\bmental\s+image[s]?\b', r'\bmental\s+imagery\b'],
    "Natural aggression": [r'\bnatural\s+aggression\b', r'\bnatural\s+aggressive\b'],
    "Tissue capsule": [r'\btissue\s+capsule[s]?\b'],
    "gestalt": [r'\bgestalt[s]?\b'],
}

BASE_DIR = '/Users/sunpeng/cola/outputs/千问-赛斯测试'
PROCESSED_DIR = os.path.join(BASE_DIR, '02-processed')
FULL_DIR = os.path.join(BASE_DIR, 'concept-quotes-full')   # 完整库（去重后全部）
SELECTED_DIR = os.path.join(BASE_DIR, 'concept-quotes')     # 精选库（top N）
os.makedirs(FULL_DIR, exist_ok=True)
os.makedirs(SELECTED_DIR, exist_ok=True)

MAX_SELECTED = 200
DEDUP_SIMILARITY = 0.85


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
    definition_patterns = [
        rf'{re.escape(c)}\s+(?:is|are|was|means|refers\s+to|can\s+be\s+defined\s+as)',
        rf'[Tt]he\s+{re.escape(c)}\s+(?:is|are|was|means)',
        rf'(?:called|known\s+as|termed)\s+{re.escape(c)}',
        rf'{re.escape(c)}\s*,\s*(?:which|that)\s+(?:is|are|was)',
    ]
    for dp in definition_patterns:
        if re.search(dp, t, re.IGNORECASE):
            def_score += 10
            break
    
    if any(w in t for w in ['essentially', 'basically', 'fundamentally', 'in other words', 'that is to say']):
        def_score += 5
    
    unique_score = min(len(t) / 50, 15)
    
    return density_score + info_score + def_score + unique_score


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
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=3000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  API 错误 (尝试 {attempt+1}/{max_retries}): {e}")
            time.sleep(5)
    return ""


def batch_translate_quotes(quotes, concept_name):
    results = []
    batch_size = 3
    
    for i in range(0, len(quotes), batch_size):
        batch = quotes[i:i+batch_size]
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
        output.append({
            "id": f"_{idx+1:04d}",
            "text_en": ex['text'],
            "text_zh": translations[idx] if idx < len(translations) else "",
            "source": ex['source_str'],
            "book": ex['book'],
            "score": round(ex['score'], 1),
            "match_count": ex['match_count'],
        })
    return output


def process_concept(concept_name, zh_name, all_paragraphs):
    print(f"\n{'='*60}")
    print(f"处理: {concept_name} ({zh_name})")
    print(f"{'='*60}")
    
    patterns = CONCEPT_RULES.get(concept_name, [rf'\b{re.escape(concept_name)}\b'])
    
    # === 阶段一：匹配 → 去重 → 翻译 → 保存完整库 ===
    print("\n[阶段一] 全书匹配 + 自然去重...")
    candidates = []
    seen = set()
    
    for p in all_paragraphs:
        text = p.get('text', '').strip()
        if not text or not is_good_excerpt(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        
        match_count = count_matches(text, patterns)
        if match_count == 0:
            continue
        
        source = format_source(p.get('source', {}))
        if not source:
            continue
        
        score = score_excerpt(text, concept_name, patterns, match_count)
        candidates.append({
            'text': text,
            'source': p.get('source', {}),
            'source_str': source,
            'book': p.get('_book', ''),
            'match_count': match_count,
            'score': score,
        })
    
    print(f"  初始匹配: {len(candidates)} 条")
    
    print(f"  自然去重中...")
    deduped = deduplicate_excerpts(candidates)
    print(f"  去重后: {len(deduped)} 条（自然结果，无人工截断）")
    
    unique_sessions = set()
    for ex in deduped:
        s = extract_session_number(ex.get('source', {}))
        if s:
            unique_sessions.add(s)
    print(f"  Session覆盖: {len(unique_sessions)} 个")
    
    # 全部翻译
    print(f"\n[阶段一] 批量翻译全部 {len(deduped)} 条摘录...")
    translations_full = batch_translate_quotes(deduped, concept_name)
    translated_count = len([t for t in translations_full if t])
    print(f"  翻译完成 {translated_count} / {len(deduped)} 条")
    
    # 保存完整库
    safe_name = concept_name.replace('/', '_').replace(' ', '_')
    full_output = {
        "concept_name_en": concept_name,
        "concept_name_zh": zh_name,
        "total_matched_initial": len(candidates),
        "total_after_dedup": len(deduped),
        "total_translated": translated_count,
        "excerpts": build_excerpt_list(deduped, translations_full),
    }
    
    full_file = os.path.join(FULL_DIR, f"{safe_name}.json")
    with open(full_file, 'w', encoding='utf-8') as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)
    
    print(f"\n[阶段一] 完整库已保存: {full_file}")
    print(f"  文件大小: {os.path.getsize(full_file)} bytes")
    print(f"  摘录数: {len(full_output['excerpts'])}")
    
    # === 阶段二：从完整库精选 top N → 保存精选库 ===
    print(f"\n[阶段二] 从完整库精选 top {MAX_SELECTED}...")
    deduped.sort(key=lambda x: -x['score'])
    selected = deduped[:MAX_SELECTED]
    selected_translations = translations_full[:MAX_SELECTED]
    
    scores = [ex['score'] for ex in selected]
    matches = [ex['match_count'] for ex in selected]
    print(f"  精选 {len(selected)} 条")
    print(f"  评分范围: {min(scores):.1f} ~ {max(scores):.1f} (平均 {sum(scores)/len(selected):.1f})")
    print(f"  匹配次数: {min(matches)} ~ {max(matches)} (平均 {sum(matches)/len(selected):.1f})")
    
    selected_output = {
        "concept_name_en": concept_name,
        "concept_name_zh": zh_name,
        "source": f"从 {len(deduped)} 条去重摘录中精选 top {MAX_SELECTED}",
        "excerpts": build_excerpt_list(selected, selected_translations),
    }
    
    selected_file = os.path.join(SELECTED_DIR, f"{safe_name}.json")
    with open(selected_file, 'w', encoding='utf-8') as f:
        json.dump(selected_output, f, ensure_ascii=False, indent=2)
    
    print(f"[阶段二] 精选库已保存: {selected_file}")
    print(f"  文件大小: {os.path.getsize(selected_file)} bytes")
    
    return {
        'concept': concept_name,
        'matched': len(candidates),
        'deduped': len(deduped),
        'translated': translated_count,
        'selected': len(selected),
    }


def main():
    # 从命令行参数获取概念名，默认跑试点概念
    if len(sys.argv) > 1:
        pilot_concepts = [sys.argv[1]]
    else:
        pilot_concepts = ["Beliefs", "Ego", "Consciousness", "dissociate/trance"]
    
    concept_map_file = os.path.join(PROCESSED_DIR, 'concept-wiki', '核心概念表.md')
    concepts_map = {}
    with open(concept_map_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('|') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    try:
                        idx = int(parts[0])
                        en_name = parts[1]
                        zh_name = parts[2]
                        concepts_map[en_name] = {'zh': zh_name, 'idx': idx}
                    except ValueError:
                        continue
    
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
    print(f"{'概念':<25} | {'初始匹配':>6} | {'去重后':>6} | {'已翻译':>6} | {'精选':>6}")
    print("-" * 60)
    for r in results:
        print(f"{r['concept']:<25} | {r['matched']:>6} | {r['deduped']:>6} | {r['translated']:>6} | {r['selected']:>6}")


if __name__ == '__main__':
    main()
