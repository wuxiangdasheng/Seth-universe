# 公共前台部署说明

本项目公开部署只发布 `public-site/`，不发布后台和源数据。

## EdgeOne Pages 配置

在 EdgeOne Pages 新建项目并连接 GitHub 仓库后，使用：

```text
Repository: wuxiangdasheng/Seth-universe
Production branch: main
Framework preset: None / 静态站点
Build command: 留空
Build output directory: public-site
Root directory: 留空
```

腾讯云迁移文档要求把 Cloudflare Pages 的 `_headers` 配置迁移为 EdgeOne Pages 的 `edgeone.json`。构建脚本会同时生成：

- `public-site/_headers`
- `public-site/edgeone.json`

所以这个公开目录可以同时适配 Cloudflare Pages 和 EdgeOne Pages。

## Cloudflare Pages 配置

在 Cloudflare Pages 新建项目并连接 GitHub 仓库后，使用：

```text
Framework preset: None
Production branch: main
Build command: 留空
Build output directory: public-site
Root directory: 留空
```

不要把输出目录设为 `wiki/` 或项目根目录。

## 为什么构建命令留空

`wiki/concepts.json`、`wiki/concepts-lite.json`、`wiki/concept-graph.json` 是本地内容数据，不进入 Git 代码版本。Cloudflare 线上构建环境拿不到这些源数据，所以不要在 Cloudflare 上运行：

```bash
python3 scripts/build_public_site.py
```

正确做法是在本地先生成公开目录，再提交 `public-site/`。

## 每次更新内容后的发布流程

```bash
# 1. 本地后台编辑内容后，先在后台备份内容数据
# http://localhost:8081/admin-backup.html

# 2. 重新生成公开站点目录
python3 scripts/build_public_site.py

# 3. 检查公开目录
python3 -m http.server 8092 --directory public-site
# 打开 http://localhost:8092/index.html 检查

# 4. 提交公开目录
git add public-site
git commit -m "Update public site data"

# 5. 推送到 GitHub
git push
```

推送后 Pages 平台会自动发布 `public-site/`。

## 公开目录不得包含

- `wiki/admin.html`
- `wiki/admin-backup.html`
- `wiki/server.py`
- `backup/`
- `02-processed/`
- `concept-quotes-full/`
- `concept-quotes/`
- `scripts/`
- 本地书签和后台编辑状态
