#!/usr/bin/env python3
"""
为概念生成元数据（explanation + definition）

输入：concept-quotes-full/{概念}.json（完整摘录库）
输出：更新 wiki/concepts.json 中对应概念的 explanation 和 definition 字段

功能：
  - explanation：AI 基于摘录生成的中文总结（300 字以内）
  - definition：从摘录中提取的定义性原文（最多 5 条），中英文对照

用法：
  python3 generate_concept_metadata.py              # 处理所有缺少数据的概念
  python3 generate_concept_metadata.py "Beliefs"    # 只处理指定概念
"""

import json
import os
import re
import sys
import time
import shutil
from datetime import datetime
from openai import OpenAI
try:
    from concept_utils import BASE_DIR, safe_concept_name
except ImportError:
    from scripts.concept_utils import BASE_DIR, safe_concept_name

# ============================
# API 配置
# ============================
API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
BASE_URL = 'https://api.deepseek.com'
MODEL = 'deepseek-chat'

client = None

BASE_DIR = str(BASE_DIR)
FULL_DIR = os.path.join(BASE_DIR, 'concept-quotes-full')
CONCEPTS_FILE = os.path.join(BASE_DIR, 'wiki', 'concepts.json')
BACKUP_DIR = os.path.join(BASE_DIR, 'backup')

MAX_EXPLANATION_CHARS = 300
MAX_DEFINITIONS = 5


def call_llm(prompt, system_prompt, max_retries=2):
    global client
    if not API_KEY:
        raise RuntimeError('缺少 DEEPSEEK_API_KEY 环境变量，无法调用 DeepSeek。')
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
                temperature=0.4,
                max_tokens=1500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  API 错误 (尝试 {attempt+1}/{max_retries}): {e}")
            time.sleep(5)
    return ""


def generate_explanation(concept_en, concept_zh, excerpts):
    """基于摘录生成 300 字以内的中文 explanation"""
    # 抽取前 300 条最有代表性的摘录（按 score 排序，取前 300）
    sample = excerpts[:300]
    texts = [e.get('text_en', '') for e in sample if e.get('text_en')]

    if not texts:
        print("  无可用摘录，跳过")
        return None

    # 如果摘录总长度太长，截断到合理范围
    combined = "\n".join(texts)
    if len(combined) > 8000:
        combined = combined[:8000]

    system_prompt = f"""你是一位精通赛斯资料（Seth Material）的哲学研究者。

请根据提供的英文摘录，用中文概括总结「{concept_en}（{concept_zh}）」这个概念的核心含义。

要求：
1. 严格控制在 300 字以内
2. 用通俗易懂的现代中文写作
3. 准确传达赛斯对这个概念的核心观点
4. 不要使用客套话（如"根据资料"、"总的来说"等）
5. 直接开始解释概念本身
6. 保持哲学深度但语言平实

只输出 explanation 正文，不要标题、不要解释。"""

    prompt = f"""以下是赛斯书中关于「{concept_en}」的相关摘录，请据此生成中文总结：

{combined}"""

    result = call_llm(prompt, system_prompt)

    if result:
        # 清理可能的客套话
        result = re.sub(r'^(根据提供的资料|根据以上摘录|总结来说|总而言之|总的来说|综上所述)，?\s*', '', result)
        result = result.strip()
        # 截断到 300 字
        if len(result) > MAX_EXPLANATION_CHARS:
            result = result[:MAX_EXPLANATION_CHARS].rstrip()
            # 在句子边界截断
            last_period = max(result.rfind('。'), result.rfind('，'), result.rfind('；'))
            if last_period > 100:
                result = result[:last_period + 1]
            else:
                result += '...'

    return result


def generate_definition(concept_en, excerpts):
    """从摘录中提取最具定义性的句子（最多 5 条），中英文对照"""
    # 过滤出有定义特征的句子
    definition_candidates = []
    for e in excerpts:
        text = e.get('text_en', '')
        if not text:
            continue
        # 定义性模式：is/are/means/refers to 等
        if re.search(rf'\b{re.escape(concept_en)}\s+(?:is|are|was|means|refers\s+to)', text, re.IGNORECASE):
            definition_candidates.append(e)
        elif re.search(rf'(?:called|known\s+as|termed)\s+{re.escape(concept_en)}', text, re.IGNORECASE):
            definition_candidates.append(e)
        elif re.search(rf'\b{re.escape(concept_en)}\s*,\s*(?:which|that)\s+(?:is|are|was)', text, re.IGNORECASE):
            definition_candidates.append(e)

    # 如果定义性句子不够，补充高分摘录
    if len(definition_candidates) < MAX_DEFINITIONS:
        for e in excerpts[:50]:
            if e not in definition_candidates:
                text = e.get('text_en', '')
                if text and len(text) > 30 and len(text) < 500:
                    definition_candidates.append(e)
            if len(definition_candidates) >= MAX_DEFINITIONS * 3:
                break

    # 取前 5 条，用 AI 提取定义并翻译
    candidates = definition_candidates[:10]
    quote_list = "\n".join([f"[{i+1}] {e['text_en']}" for i, e in enumerate(candidates)])

    system_prompt = f"""你是一位精通赛斯资料（Seth Material）的哲学研究者。

请从以下摘录中，提取关于「{concept_en}」最具定义性的句子（最多 {MAX_DEFINITIONS} 条）。

要求：
1. 必须是赛斯原话的直接定义，不是 AI 自己的总结
2. 选择最具代表性、最核心的定义句
3. 每条定义需附英文原文、中文翻译、来源
4. 中文翻译要准确，符合赛斯资料的常用译法
5. 不要客套话，直接输出

严格按以下 JSON 格式输出（不要代码块，不要多余文字）：
[
  {{
    "en": "英文定义原文",
    "zh": "中文翻译",
    "source": "Session XXX"
  }}
]"""

    prompt = f"""以下是关于「{concept_en}」的相关摘录：

{quote_list}

请从中提取最具定义性的句子（最多 {MAX_DEFINITIONS} 条），输出 JSON 数组。"""

    result = call_llm(prompt, system_prompt)

    if result:
        # 清理可能的代码块标记
        result = re.sub(r'^```json\s*', '', result)
        result = re.sub(r'\s*```$', '', result)
        result = result.strip()

        try:
            definitions = json.loads(result)
            if isinstance(definitions, list) and len(definitions) > 0:
                # 清理每条数据
                cleaned = []
                for d in definitions:
                    if isinstance(d, dict):
                        cleaned.append({
                            'en': d.get('en', '').strip(),
                            'zh': d.get('zh', '').strip(),
                            'source': d.get('source', '').strip()
                        })
                if cleaned:
                    return cleaned
        except json.JSONDecodeError:
            print(f"  JSON 解析失败: {result[:100]}")

    return None


def load_concepts():
    with open(CONCEPTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_concepts(data):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'concepts.metadata.{timestamp}.json')
    shutil.copy2(CONCEPTS_FILE, backup_path)
    existing = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith('concepts.metadata.'))
    for old_file in existing[:-10]:
        os.remove(os.path.join(BACKUP_DIR, old_file))
    with open(CONCEPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    target_concept = sys.argv[1] if len(sys.argv) > 1 else None

    concepts_data = load_concepts()
    concepts = concepts_data.get('concepts', [])

    # 找出需要处理的概念（任一字段缺失都要处理）
    to_process = []
    for c in concepts:
        if target_concept and c.get('name_en') != target_concept:
            continue
        expl = c.get('explanation', '').strip()
        defs = c.get('definition', [])
        # definition 为空字符串、空列表、或测试数据都需要重新生成
        need_def = (
            not defs or
            (isinstance(defs, str) and not defs.strip()) or
            (isinstance(defs, list) and len(defs) == 0) or
            (isinstance(defs, list) and any(d.get('en') == 'test' for d in defs if isinstance(d, dict)))
        )
        if not expl or need_def:
            to_process.append(c)

    if not to_process:
        if target_concept:
            print(f"概念「{target_concept}」数据完整，无需处理")
        else:
            print("所有概念数据完整，无需处理")
        return

    print(f"需要处理 {len(to_process)} 个概念\n")

    for c in to_process:
        concept_en = c.get('name_en', '')
        concept_zh = c.get('name_zh', '')
        safe_name = safe_concept_name(concept_en)
        full_file = os.path.join(FULL_DIR, f"{safe_name}.json")

        print(f"\n{'='*50}")
        print(f"处理: {concept_en} ({concept_zh})")
        print(f"{'='*50}")

        if not os.path.exists(full_file):
            print(f"  跳过：未找到 {full_file}")
            continue

        with open(full_file, 'r', encoding='utf-8') as f:
            full_data = json.load(f)

        excerpts = full_data.get('excerpts', [])
        if not excerpts:
            print(f"  跳过：无摘录数据")
            continue

        # 生成 explanation（如果缺失）
        expl = c.get('explanation', '').strip()
        if not expl:
            explanation = generate_explanation(concept_en, concept_zh, excerpts)
            if explanation:
                c['explanation'] = explanation
                print(f"  ✓ explanation 已生成 ({len(explanation)} 字)")
            else:
                print(f"  ✗ explanation 生成失败")

        # 生成 definition（如果缺失或无效）
        defs = c.get('definition', [])
        need_def = (
            not defs or
            (isinstance(defs, str) and not defs.strip()) or
            (isinstance(defs, list) and len(defs) == 0) or
            (isinstance(defs, list) and any(d.get('en') == 'test' for d in defs if isinstance(d, dict)))
        )
        if need_def:
            definitions = generate_definition(concept_en, excerpts)
            if definitions:
                c['definition'] = definitions
                print(f"  ✓ definition 已生成 ({len(definitions)} 条)")
            else:
                print(f"  ✗ definition 生成失败")

        # 每次处理完一个概念后立即保存
        save_concepts(concepts_data)
        print(f"  ✓ 已保存到 {CONCEPTS_FILE}")

        time.sleep(2)

    print(f"\n{'='*50}")
    print("处理完成")


if __name__ == '__main__':
    main()
