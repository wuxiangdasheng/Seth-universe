#!/usr/bin/env python3
"""Run the full concept ingestion pipeline in the correct order."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    from concept_utils import BASE_DIR, load_concept_table
except ImportError:
    from scripts.concept_utils import BASE_DIR, load_concept_table


SCRIPT_DIR = Path(__file__).resolve().parent


def run_step(label, command, env):
    print(f'\n{"=" * 60}', flush=True)
    print(label, flush=True)
    print(f'命令: {" ".join(command)}', flush=True)
    print(f'{"=" * 60}', flush=True)
    result = subprocess.run(command, cwd=BASE_DIR, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description='录入或刷新一个赛斯概念')
    parser.add_argument('concept', help='概念英文名，必须存在于核心概念表')
    parser.add_argument('--skip-collect', action='store_true', help='跳过摘录收集与翻译')
    parser.add_argument('--skip-metadata', action='store_true', help='跳过 explanation/definition 生成')
    parser.add_argument('--prefix-required', action='store_true', help='只保留前 360 字符命中的摘录')
    args = parser.parse_args()

    concepts = load_concept_table()
    if args.concept not in concepts:
        print(f"错误: 核心概念表中未找到概念 '{args.concept}'")
        return 1

    env = os.environ.copy()
    if args.prefix_required:
        env['SETH_REQUIRE_PREFIX_MATCH'] = '1'

    if not args.skip_collect and not env.get('DEEPSEEK_API_KEY'):
        print('错误: 缺少 DEEPSEEK_API_KEY 环境变量，无法翻译摘录。')
        return 1
    if not args.skip_metadata and not env.get('DEEPSEEK_API_KEY'):
        print('错误: 缺少 DEEPSEEK_API_KEY 环境变量，无法生成元数据。')
        return 1

    python = sys.executable or 'python3'

    if not args.skip_collect:
        run_step('1. 收集摘录、去重、翻译、生成质量报告', [python, str(SCRIPT_DIR / 'batch_collect_quotes.py'), args.concept], env)

    run_step('2. 重建 wiki/concepts.json', [python, str(SCRIPT_DIR / 'rebuild_concepts_from_quotes.py'), args.concept], env)

    if not args.skip_metadata:
        run_step('3. 生成 explanation / definition', [python, str(SCRIPT_DIR / 'generate_concept_metadata.py'), args.concept], env)

    run_step('4. 重建 wiki/concepts-lite.json', [python, str(SCRIPT_DIR / 'rebuild_lite.py')], env)

    print('\n处理完成。server.py 启动时会加载内存数据，如服务器正在运行，请重启 8081。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
