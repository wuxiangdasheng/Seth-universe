#!/usr/bin/env python3
"""Semantic classification of concept quotes into 7 reading roles."""

import json
import os
import re
import sys
import time
from pathlib import Path
from openai import OpenAI

API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
BASE_URL = 'https://api.deepseek.com'
MODEL = 'deepseek-chat'

BASE_DIR = Path(__file__).resolve().parents[1]
FULL_DIR = BASE_DIR / 'concept-quotes-full'

ROLE_ORDER = {
    'definition': 10,
    'description': 20,
    'mechanism': 30,
    'example': 40,
    'practice': 50,
    'warning': 60,
    'uncategorized': 90,
}

ROLE_DESCRIPTIONS = {
    'definition': '直接回答"这个概念是什么"，有定义性语气（is/are/means/refers to等）',
    'description': '对定义的补充说明、性质描述、延展解释、原则阐述',
    'mechanism': '说明概念如何运行、如何产生影响、如何导致结果（因果链、作用方式）',
    'example': '为了帮助理解而举出的例子、情境、比喻、案例',
    'practice': '给读者的应用方法、练习、生活中的操作建议',
    'warning': '指出误区、错误理解、限制、危险、注意事项',
    'uncategorized': '无法明确判断、只是提到概念、关系弱',
}


def classify_batch(batch, concept_en, concept_zh):
    """Classify a batch of 5 quotes using LLM."""
    items = []
    for i, ex in enumerate(batch):
        items.append(
            f"[{i+1}]\n{ex.get('text_en', '')[:800]}"
        )

    quote_list = "\n\n".join(items)

    system_prompt = f"""你是一位精通赛斯资料（Seth Material）的哲学研究者。
你的任务是对关于「{concept_en}（{concept_zh}）」的摘录进行语义分类。

请把每条摘录归入以下 7 类之一：
- definition：直接回答"这个概念是什么"。定义性语气。
- description：对定义的补充说明、性质描述、延展解释、原则阐述。
- mechanism：说明概念如何运行、如何产生影响、因果链、作用方式。
- example：为了帮助理解而举出的例子、情境、比喻、案例。
- practice：给读者的应用方法、练习、操作建议。
- warning：指出误区、错误理解、限制、危险、注意事项。
- uncategorized：无法明确判断、只是提到概念、关系弱。

分类优先级：practice > example > definition > mechanism > warning > description > uncategorized

严格按 JSON 数组输出，不要代码块，不要解释：
[
  {{"id": "序号", "quote_role": "分类", "confidence": "high|medium|low"}}
]"""

    user_prompt = f"请对以下 {len(batch)} 条关于「{concept_en}」的摘录进行分类：\n\n{quote_list}"

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        text = response.choices[0].message.content.strip()
        # Clean markdown code blocks
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        print(f"  API 错误: {e}")
        return []


def process_file(concept_en):
    safe_name = concept_en.replace('/', '_').replace(' ', '_')
    input_file = FULL_DIR / f'{safe_name}.json'
    output_file = FULL_DIR / f'{safe_name}_classified.json'

    if not input_file.exists():
        print(f"文件不存在: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    excerpts = data.get('excerpts', [])
    concept_zh = data.get('concept_name_zh', '')
    print(f"处理: {concept_en} ({concept_zh})")
    print(f"  共 {len(excerpts)} 条摘录")
    print(f"  输出: {output_file.name}")

    results = []
    batch_size = 5

    for i in range(0, len(excerpts), batch_size):
        batch = excerpts[i:i+batch_size]
        batch_num = i // batch_size + 1
        total = (len(excerpts) + batch_size - 1) // batch_size
        print(f"  批次 {batch_num}/{total} (摘录 {i+1}-{min(i+batch_size, len(excerpts))})...", end=' ', flush=True)

        classified = classify_batch(batch, concept_en, concept_zh)
        print(f"收到 {len(classified)} 条分类", flush=True)

        # Map results back
        for j, ex in enumerate(batch):
            entry = dict(ex)
            if j < len(classified):
                c = classified[j]
                role = c.get('quote_role', 'uncategorized')
                if role not in ROLE_ORDER:
                    role = 'uncategorized'
                entry['quote_role'] = role
                entry['reading_order'] = ROLE_ORDER[role]
                entry['confidence'] = c.get('confidence', 'low')
            else:
                entry['quote_role'] = 'uncategorized'
                entry['reading_order'] = 90
                entry['confidence'] = 'low'
            results.append(entry)

        time.sleep(2)

    # Build output
    output = {
        **{k: v for k, v in data.items() if k != 'excerpts'},
        'semantic_classified': True,
        'excerpts': results,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Print distribution
    from collections import Counter
    dist = Counter(e['quote_role'] for e in results)
    print(f"\n分类分布:")
    for role, count in sorted(dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {role}: {count}")
    print(f"\n已保存: {output_file}")


def main():
    if len(sys.argv) > 1:
        concept = sys.argv[1]
    else:
        concept = 'Beliefs'

    process_file(concept)


if __name__ == '__main__':
    main()
