# 赛斯宇宙 Wiki 项目 — AI 生成规则

## 项目概述

本项目从赛斯书（Seth Material）英文原文中提取哲学概念，经过匹配、去重、翻译、精选、AI 总结等流程，生成前端可展示的结构化数据。

## 目录结构

```
/Users/sunpeng/cola/outputs/千问-赛斯测试/
├── 02-processed/                    # 原始处理数据（全书 JSON 段落）
├── concept-quotes-full/             # 完整摘录库（去重后全部翻译）
│   ├── Beliefs.json
│   ├── Ego.json
│   ├── Consciousness.json
│   └── ...
├── concept-quotes/                  # 精选摘录库（top 200）
│   ├── Beliefs.json
│   └── ...
├── wiki/
│   ├── concepts.json                # 主数据文件（前端/后端共用）
│   ├── concepts-lite.json           # 轻量列表（前端快速加载）
│   ├── index.html                   # 前端页面
│   ├── admin.html                   # 后台管理页面
│   └── server.py                    # HTTP 服务器 + CRUD API
└── scripts/
    ├── batch_collect_quotes.py      # 摘录匹配/去重/翻译/精选（两阶段流程）
    ├── generate_explanations.py     # AI 生成 explanation 中文总结
    ├── rebuild_concepts_from_quotes.py  # 从摘录重建 concepts.json
    └── rebuild_lite.py              # 生成 concepts-lite.json
```

## 数据流：从新书概念到前端展示的完整链路

### 第 1 步：添加概念到核心概念表

在 `02-processed/concept-wiki/核心概念表.md` 中添加一行：

```
| 序号 | 概念英文名 | 概念中文名 |
```

### 第 2 步：添加匹配规则

在 `scripts/batch_collect_quotes.py` 的 `CONCEPT_RULES` 字典中添加正则匹配规则：

```python
"概念英文名": [r'\b正则1\b', r'\b正则2\b'],
```

### 第 3 步：运行摘录收集脚本（两阶段流程）

```bash
python3 scripts/batch_collect_quotes.py "概念英文名"
```

脚本自动执行以下流程：

#### 阶段一：全书匹配 → 自然去重 → 全部翻译 → 保存完整库

1. **全文匹配**：扫描 `02-processed/*.json` 中的所有段落（约 5-6 万段）
   - 使用正则规则匹配概念关键词
   - 计算每条摘录的相关度评分（密度 + 信息量 + 定义性 + 独特性）
   - 只保留有 Session 来源的段落

2. **自然去重**：n-gram Jaccard 相似度去重
   - n=6 字符级 n-gram
   - Jaccard 相似度 > 0.85 视为重复
   - **无人工上限**，匹配多少留多少
   - 按评分降序排列

3. **批量翻译**：调用 DeepSeek API 逐批翻译全部摘录（每批 3 条）
   - 输入：英文原文
   - 输出：中文翻译

4. **保存完整库**：`concept-quotes-full/{概念名}.json`
   ```json
   {
     "concept_name_en": "Beliefs",
     "concept_name_zh": "信念",
     "total_matched_initial": 1319,
     "total_after_dedup": 1314,
     "total_translated": 1314,
     "excerpts": [
       {
         "id": "_0001",
         "text_en": "英文原文",
         "text_zh": "中文翻译",
         "source": "Session XXX",
         "book": "Seth Speaks",
         "score": 45.2,
         "match_count": 3
       }
     ]
   }
   ```

#### 阶段二：从完整库精选 top 200 → 保存精选库

1. 按评分降序，取 top 200
2. 保存到 `concept-quotes/{概念名}.json`

### 第 4 步：生成 explanation（AI 中文总结）

```bash
python3 scripts/generate_explanations.py "概念英文名"
```

脚本逻辑：
1. 从 `concept-quotes-full/{概念}.json` 读取前 300 条高评分摘录
2. 发送给 DeepSeek API，生成 300 字以内的中文 explanation
3. 自动清理客套话（"根据资料"、"总的来说"等）
4. 直接更新 `wiki/concepts.json` 中对应概念的 `explanation` 字段

### 第 5 步：重建 concepts.json

```bash
python3 scripts/rebuild_concepts_from_quotes.py
```

脚本逻辑：
1. 读取 `concept-quotes-full/` 目录下所有概念文件
2. 将摘录数据写入 `wiki/concepts.json` 中对应概念
3. 统一数据格式：`{text_en, text_zh}` → `{text, translation, source}`
4. 更新 `quotes_count` 统计字段

### 第 6 步：重建轻量列表

```bash
python3 scripts/rebuild_lite.py
```

脚本逻辑：
1. 从 `wiki/concepts.json` 提取概念基本信息
2. 生成 `wiki/concepts-lite.json`（供前端快速加载列表）

### 第 7 步：前端展示

访问 `http://localhost:8081/index.html`

## concepts.json 数据结构

```json
{
  "concepts": [
    {
      "id": "concept-001",
      "name_zh": "信念",
      "name_en": "Beliefs",
      "category": "信念",
      "explanation": "信念是你创造自己现实的核心机制...",
      "definition": [
        {
          "zh": "信念是你关于现实的假设...",
          "en": "A belief is your assumption about reality...",
          "source": "Session 123"
        }
      ],
      "quotes": [
        {
          "text": "英文原文",
          "translation": "中文翻译",
          "source": "Session XXX"
        }
      ],
      "quotes_count": 1314,
      "sub_concepts": [],
      "sub_concepts_count": 0,
      "related_concepts": [],
      "related_count": 0
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `explanation` | string | AI 生成的中文总结（300 字以内） |
| `definition` | array | 从书中提取的原始定义（最多 5 条），中英文对照 |
| `quotes` | array | 与该概念相关的摘录列表 |
| `quotes[].text` | string | 英文原文 |
| `quotes[].translation` | string | 中文翻译 |
| `quotes[].source` | string | 来源，格式为 "Session XXX" |

## API 接口

### GET /api/concepts
返回概念列表（轻量）

### GET /api/concepts/{id}
返回单个概念完整数据（含摘录）

### DELETE /api/concepts/{cid}/quotes/{qidx}
删除指定概念的第 N 条摘录

### POST /api/concepts
创建新概念

### PUT /api/concepts/{id}
更新概念

### DELETE /api/concepts/{id}
删除整个概念

## 前端规范

- 全站最小字号 14px，正文 16px
- 金色主题 `#b4a064`
- 星空背景 + 噪声纹理
- 摘录卡片：中文在上（quote-zh），英文在下（quote-en），来源在底部
- 定义区块：每条定义独立展示，序号 + 中文 + 英文 + 来源
- 摘录卡片有删除按钮（悬停显示），调用 DELETE API 删除数据

## 后台管理规范

- 三栏布局：左侧菜单、中间概念列表、右侧编辑面板
- 菜单项与前端一致，名称后加 "管理"
- '核心概念管理' 为默认页面

## 注意事项

1. **全链路一致性**：修改数据后必须同步更新 `concepts.json` 和 `concepts-lite.json`，并重启 server.py（数据在启动时加载到内存）
2. **去重不设上限**：自然去重，匹配多少留多少
3. **翻译批量进行**：每批 3 条，避免 API 超时
4. **explanation 清理**：去除客套话，直接输出概念解释
5. **摘录删除**：前端删除会同步更新 concepts.json，但不会删除 concept-quotes-full/ 中的源文件
