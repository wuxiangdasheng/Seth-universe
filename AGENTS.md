# AGENTS.md — 赛斯宇宙 Wiki

## 项目概述

从赛斯书（Seth Material）英文原文中提取哲学概念，经过匹配、去重、翻译、精选、AI 总结等流程，生成前端可展示的结构化数据。

## 目录结构

```
千问-赛斯测试/
├── 02-processed/              # 原始处理数据（全书 JSON 段落，54278 段）
├── concept-quotes-full/       # 完整摘录库（去重后全部翻译）
├── concept-quotes/            # 精选摘录库（top 200）
├── wiki/
│   ├── concepts.json          # 主数据文件（前端/后端共用）
│   ├── concepts-lite.json     # 轻量列表（前端快速加载）
│   ├── index.html             # 前端主页
│   ├── admin.html             # 后台管理页面
│   ├── admin-backup.html      # 备份管理页面
│   ├── admin-menu.js          # 后端菜单配置
│   ├── global-menu.js         # 全局菜单（前端侧栏）
│   ├── server.py              # HTTP 服务器 + CRUD API
│   ├── quotes.json            # 全局语录库
│   ├── topics.json            # 专题数据
│   ├── relations.json         # 概念/语录/专题关系
│   └── bookmark.json          # 书签数据
├── scripts/
│   ├── add_concept.py                 # 一键概念录入总控脚本
│   ├── concept_utils.py               # 概念表/ID/文件名共享工具
│   ├── batch_collect_quotes.py        # 摘录匹配/去重/翻译/精选
│   ├── clean_quote_libraries.py       # 清洗现有摘录库并重建精选库
│   ├── generate_concept_metadata.py   # AI 生成 explanation/definition
│   ├── rebuild_concepts_from_quotes.py # 从摘录重建 concepts.json
│   ├── rebuild_lite.py                # 生成 concepts-lite.json
│   └── backup/                        # 脚本自动备份目录
├── reports/                   # 每个概念的质量报告
└── backup/                    # 数据备份包、代码备份包、恢复前备份
```

## 原始数据格式

`02-processed/*.json` — 每本书一个文件，包含 `all_content` 数组：

```json
{
  "all_content": [
    {
      "type": "seth",       // "seth" 口述 | "jane_note" Jane笔记
      "text": "英文段落内容",
      "style": "Normal",
      "source": { "session_number": "511", "chapter_title": "..." }
    }
  ]
}
```

## 概念录入全流程

### 0. 配置 API Key

DeepSeek API Key 不写入代码和文档，通过环境变量提供：

```bash
export DEEPSEEK_API_KEY="sk-..."
```

### 推荐：一键录入

```bash
cd /Users/sunpeng/cola/outputs/千问-赛斯测试
python3 scripts/add_concept.py "概念英文名"
```

总控脚本会按正确顺序执行：
1. `batch_collect_quotes.py`：摘录匹配、去重、翻译、精选、质量报告
2. `rebuild_concepts_from_quotes.py`：把摘录写入 `wiki/concepts.json`
3. `generate_concept_metadata.py`：生成 `explanation` / `definition`
4. `rebuild_lite.py`：重建 `wiki/concepts-lite.json`

可选参数：
```bash
python3 scripts/add_concept.py "ConceptName" --skip-collect     # 跳过摘录收集
python3 scripts/add_concept.py "ConceptName" --skip-metadata    # 跳过 AI 元数据
python3 scripts/add_concept.py "ConceptName" --prefix-required  # 只保留前 360 字符命中的摘录
```

### 1. 添加概念到核心概念表

在 `02-processed/concept-wiki/核心概念表.md` 中添加：
```
| 序号 | 概念英文名 | 概念中文名 |
```

### 2. 添加匹配规则

在 `scripts/batch_collect_quotes.py` 的 `CONCEPT_RULES` 中添加：
```python
"概念英文名": [r'\b正则1\b', r'\b正则2\b'],
```

也支持更细的规则结构：

```python
"概念英文名": {
    "include": [r'\b正则1\b'],
    "exclude": [r'\b排除词\b'],
    "context": [r'\b上下文词\b'],
},
```

`context` 是正向语义门槛的一部分：摘录除了命中 `include`，还必须命中定义句、机制/教学语气，或命中该概念的 `context` 上下文词。这样可减少“只是提到概念词，但没有解释概念”的段落。

### 3. 运行摘录收集（两阶段，可单独调试）

```bash
cd /Users/sunpeng/cola/outputs/千问-赛斯测试
python3 scripts/batch_collect_quotes.py "概念英文名"
```

**匹配规则：**
- 只摘录 `type == 'seth'` 的段落（Jane 笔记跳过）
- 完整库也会硬过滤 `biographical_note` / 记录性噪声：Jane/Rob 记录、break/end/stage direction、出版说明、dictation/trance time 统计、标题/附录说明等不入库
- 完整库还会应用正向语义门槛：定义性、机制性、教学性或概念专属上下文命中至少其一，否则不入库
- 默认允许全段命中；前 360 个字符内命中会额外加权
- 如需严格限制前缀命中，设置 `SETH_REQUIRE_PREFIX_MATCH=1` 或使用 `add_concept.py --prefix-required`
- 评分 = 密度(40) + 信息量(25) + 定义性(20) + 独特性(15) + 前缀命中奖励(8)
- n-gram Jaccard 去重（n=6, 阈值 0.85）
- DeepSeek API 批量翻译（每批 3 条）
- 已翻译摘录会从旧 `concept-quotes-full/{概念}.json` 复用，避免重复翻译

输出：
- `concept-quotes-full/{概念}.json` — 完整库
- `concept-quotes/{概念}.json` — 精选 top 200
- `reports/{概念}.md` — 质量报告（匹配数、去重数、语义门槛排除数、翻译率、Session 覆盖、Top 样例、低分样例）

摘录字段会包含 `related_concepts`：如果该段落同时命中核心概念表中的其他概念，会记录为：

```json
{
  "related_concepts": [
    {"id": "concept-004", "name_zh": "意识", "name_en": "Consciousness", "match_count": 2}
  ]
}
```

说明：`related_concepts` 默认排除当前概念本身；`will` 因为常作为英文助动词出现，不作为自动关联标签。

### 3.1 清洗现有摘录库（不调用 API）

当过滤规则调整后，可直接清洗已有库：

```bash
python3 scripts/clean_quote_libraries.py                # 清洗全部已有概念
python3 scripts/clean_quote_libraries.py "ConceptName"  # 只清洗一个概念
python3 scripts/rebuild_concepts_from_quotes.py
python3 scripts/rebuild_lite.py
```

该脚本会从 `concept-quotes-full/` 删除 Jane/Rob 记录、break、出版说明等段落，并用清洗后的完整库重建 `concept-quotes/` 精选库。

### 4. 重建 concepts.json

```bash
python3 scripts/rebuild_concepts_from_quotes.py "概念英文名"
```

将摘录数据从 `concept-quotes-full/` 写入 `wiki/concepts.json`。

说明：
- 概念 ID 和中文名自动读取 `核心概念表.md`
- 增量合并，不覆盖已有的人工编辑字段
- 默认只替换该概念的 `quotes` / `quotes_count`

### 5. 生成元数据（explanation + definition）

```bash
python3 scripts/generate_concept_metadata.py "概念英文名"
```

AI 基于高评分摘录生成：
- `explanation`：300 字以内中文总结
- `definition`：最多 5 条，每条含中英文和来源

### 6. 重建轻量列表

```bash
python3 scripts/rebuild_lite.py
```

生成 `wiki/concepts-lite.json`，供前端快速加载概念列表。

### 7. 重启服务器

```bash
lsof -ti:8081 | xargs kill -9
cd wiki && python3 server.py
```

**重要：** server.py 启动时加载数据到内存，修改文件后必须重启。

## concepts.json 数据结构

```json
{
  "id": "concept-001",
  "name_zh": "信念",
  "name_en": "Beliefs",
  "category": "信念",
  "explanation": "AI 中文总结",
  "definition": [{"zh": "...", "en": "...", "source": "Session 123"}],
  "definition_en": "",
  "definition_ai": "",
  "quotes": [
    {
      "id": "q-concept-001-0001",
      "text": "英文原文",
      "translation": "中文翻译",
      "source": "Session XXX",
      "book": "书名",
      "source_file": "原始 JSON 文件",
      "source_raw": {"session_number": "123", "chapter_title": "..."},
      "type": "seth",
      "score": 45.2,
      "match_count": 3,
      "prefix_match": true,
      "semantic_reason": "concept_context",
      "quote_role": "mechanism",
      "semantic_score": 4,
      "reading_order": 30,
      "related_concepts": [{"id": "concept-004", "name_zh": "意识", "name_en": "Consciousness", "match_count": 2}]
    }
  ],
  "quotes_count": 1314,
  "sub_concepts": [],
  "related_concepts": []
}
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/concepts` | 概念列表（轻量） |
| GET | `/api/concepts/{id}` | 单个概念完整数据 |
| POST | `/api/concepts` | 创建概念 |
| PUT | `/api/concepts/{id}` | 更新概念 |
| PATCH | `/api/concepts/{cid}/quotes/{qidx}/metadata` | 即时更新摘录元数据：`quote_role` / `semantic_score` / `reading_order` |
| DELETE | `/api/concepts/{id}` | 删除概念 |
| DELETE | `/api/concepts/{cid}/quotes/{qidx}` | 删除摘录 |
| GET | `/api/quotes` | 全局语录（分页/搜索） |
| GET | `/api/topics` | 专题列表 |
| GET | `/api/topics/{id}` | 单个专题 |
| POST | `/api/bookmark` | 保存书签 |
| GET | `/api/bookmark` | 读取书签 |
| GET | `/api/backups` | 备份列表 |
| POST | `/api/backups/manual` | 创建内容数据备份包 |
| POST | `/api/backups/restore` | 恢复备份 |
| POST | `/api/backups/delete` | 删除备份 |

## 前端规范

- 金色主题 `#b4a064`，星空背景 + 噪声纹理
- 最小字号 14px，正文 16px，副标题 14px
- 摘录卡片：中文翻译在上，英文原文在下，来源在底部
- 定义区块：序号 + 中文 + 英文 + 来源，每条独立展示
- 摘录卡片悬停显示删除按钮
- 三栏布局后台：左侧菜单、中间列表、右侧编辑面板
- 后台概念编辑页采用即时保存：修改概念字段、定义、摘录翻译、英文原文、摘录元数据后自动写入后端；右上角不再使用“保存”按钮
- 摘录元数据编辑项使用中文 UI：摘录角色、语义评分、阅读顺序
- `quote_role` 可选值：未设置、定义、原则、机制、区别、方法、例子、提醒、背景
- 删除摘录必须有居中的确认弹窗，避免误删

## 技术规范

- 前端/后端共用 CSS 变量、颜色系统、字体、滚动条样式
- `concepts-lite.json` 和前端使用一致的复数字段名：`quotes_count`, `sub_concepts_count`, `related_count`
- HTTP 服务器使用 `BaseHTTPRequestHandler` + `ThreadingMixIn`（最多 4 并发）
- API 响应支持 gzip 压缩
- 菜单：后端 `admin-menu.js`，前端 `global-menu.js`
- 后端 API 响应应设置 no-cache，避免后台更新后前台看到旧数据
- 前台概念详情页进入概念时应重新请求 `/api/concepts/{id}`，不要长期复用旧的摘录缓存

## 安全机制

- 关键脚本执行前自动备份（保留最近 10 个版本）
- `rebuild_concepts_from_quotes.py` 增量合并，不覆盖人工编辑字段
- DeepSeek API Key 使用 `DEEPSEEK_API_KEY` 环境变量，不写入代码
- `reports/{概念}.md` 用于人工验收召回质量
- Git 版本管理

## 备份与版本管理策略

### 内容数据备份

日常手动编辑概念、摘录、翻译、摘录角色、语义评分、阅读顺序后，优先使用后台 `admin-backup.html` 的备份功能。

当前后台内容备份包为 `backup/seth-data.YYYYMMDD_HHMMSS.zip`，包含：
- `manifest.json`
- `wiki/concepts.json`
- `concept-quotes-full/`
- `concept-quotes/`

恢复 zip 备份时，应同时恢复以上三部分，并在恢复后重新加载内存数据、重建 `wiki/concepts-lite.json`。旧版 `backup/concepts.*.json` 只代表主数据文件备份，可继续恢复，但不包含两个摘录目录。

### 网站代码版本

网站代码不要只依赖 zip 备份，优先用本地 Git 做版本管理。Git 用来记录每次代码修改的快照，便于查看差异、回退和交接。

建议策略：
- 内容数据：用后台备份功能创建 `seth-data.*.zip`
- 网站代码：用本地 Git 提交版本
- 关键节点：额外打一个代码 zip 包作为离线保险

代码文件通常包括：
- `wiki/*.html`
- `wiki/*.js`
- `wiki/server.py`
- `scripts/*.py`
- `AGENTS.md`

代码版本不应包含大体量或运行时数据：
- `wiki/concepts.json`
- `wiki/concepts-lite.json`
- `concept-quotes-full/`
- `concept-quotes/`
- `02-processed/`
- `reports/`
- `backup/`

如需手动创建代码 zip，可使用类似命名：

```bash
backup/site-code.YYYYMMDD_HHMMSS.zip
```

该 zip 只作为辅助备份；长期版本记录仍以 Git 为准。提交前应先查看 `git status --short`，不要回滚或覆盖用户已有改动。

## 最近后台改造记录

- `wiki/admin.html`：概念编辑页已改为即时保存；去掉右上角保存按钮；摘录翻译和英文原文平铺编辑；去掉中文翻译/英文原文标签、出处编辑、摘录展开收起、子概念及接口代码展示；摘录列表显示全部。
- `wiki/admin.html`：每个摘录新增可编辑字段 `quote_role`、`semantic_score`、`reading_order`，UI 名称为摘录角色、语义评分、阅读顺序。
- `wiki/admin.html`：摘录角色不是筛选器，而是写入后台数据的编辑项。
- `wiki/admin.html`：删除摘录恢复居中确认提示。
- `wiki/server.py`：增加 `PATCH /api/concepts/{cid}/quotes/{qidx}/metadata`，用于即时保存摘录元数据。
- `wiki/server.py`：`PUT /api/concepts/{id}` 用于保存整个概念，`_save_concepts()` 使用临时文件 + `os.replace` 原子写入。
- `wiki/server.py`：删除摘录时会同步从 `concept-quotes-full/` 和 `concept-quotes/` 删除对应来源摘录。
- `wiki/server.py`：后台手动备份已从单文件 `concepts.json` 升级为 `seth-data.*.zip` 内容数据包。
- `wiki/admin-backup.html`：备份列表显示备份类型，“全量包”代表 zip 内容数据包，“主数据”代表旧版 `concepts.*.json`。
- `wiki/index.html`：概念详情进入时重新拉取完整数据，减少后台更新后前台不刷新的问题。

## 常用命令

```bash
# 启动服务器
cd wiki && python3 server.py

# 录入新概念
export DEEPSEEK_API_KEY="sk-..."
python3 scripts/add_concept.py "ConceptName"

# 单步调试
python3 scripts/batch_collect_quotes.py "ConceptName"
python3 scripts/clean_quote_libraries.py "ConceptName"
python3 scripts/rebuild_concepts_from_quotes.py "ConceptName"
python3 scripts/generate_concept_metadata.py "ConceptName"
python3 scripts/rebuild_lite.py

# 查看端口占用
lsof -ti:8081

# 重启服务器
lsof -ti:8081 | xargs kill -9 && cd wiki && python3 server.py
```
