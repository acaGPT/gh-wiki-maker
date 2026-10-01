---
name: gh-wiki-maker
description: 把本地 Markdown 内容发布为 GitHub Wiki —— 在指定组织创建公开仓库、按 acaGPT/Jurisprudence 范式归一化页面（ASCII 连字符文件名、_Sidebar.md 侧栏导航、中英双语首页、绝对 URL 互链）、写入「保留所有权利」LICENSE，并提示用户先手工创建 Wiki 首页后再批量推送页面。含建库命名规则、首页初始化不可自动化的坑、链接与渲染核验。不用于单页 README、不用于站点生成器（MkDocs/Docusaurus）场景。
agent_created: true
---

# 将本地内容发布为 GitHub Wiki

## 何时使用

- 「把这些讲义 / 笔记 / 大纲发布成 GitHub Wiki」——本地已有一批 Markdown，需要一个可浏览、可检索、可版本回溯的知识站；
- 需要**沿用 `acaGPT/Jurisprudence` 的既有范式**（同一课程系列的外观与链接规则必须一致）；
- 需要中英双语首页与侧栏导航的长文档集合。

不适用：只写一份 README 或单页文档（直接提交到主仓库即可）；需要主题、搜索、静态生成的正式文档站（改用 MkDocs / Docusaurus）；需要 CI 预览的多人协作文档（改用 GitHub Pages + Actions）。

## 范式（硬规则，来自 acaGPT/Jurisprudence 实测）

| 维度 | 规则 |
| --- | --- |
| 页面文件 | 纯 Markdown，`.md`；文件名**只含 ASCII 字母、数字、连字符**，如 `PII.3.-Classical-Natural-Law.md`；点号用于章节层级，连字符连接单词 |
| 侧栏 | `_Sidebar.md`，每行 `- [英文标题](页面名)`，用**相对页名**链接（GitHub 会自动解析），顺序即导航顺序，`Home` 置首 |
| 首页 | `Home.md`：**中文章节在前、英文章节在后**，两段之间以 `---` 分隔；正文互链一律**绝对 URL**：`https://github.com/<org>/<repo>/wiki/<Page>` |
| 许可 | wiki 根目录与主仓库根目录**各放一份** `LICENSE`，内容为自定义「保留所有权利（All Rights Reserved）」文本，非 SPDX 模板 |
| 互指 | 页内互相引用用绝对 URL；`_Sidebar.md` 用相对页名；两者不得混用 |
| 分支 | wiki 仓库默认分支是 **`master`**（主仓库是 `main`），推送前先确认 |
| 图片 | 放 wiki 内 `images/` 目录，页内以相对路径 `images/xxx.jpg` 引用，并配 `Portrait-Credits.md` 之类的署名页 |

## 仓库命名规则

由本技能统一裁定，不需每次征询：

1. 英文名词短语，**概括主旨**，优先**单个词**（`Jurisprudence`）；
2. 多词一律 **PascalCase 连写**（`NaturalLawTheory`），仅当连写产生歧义时才用连字符（`Legal-Formalism`）；
3. 去掉容器词：`Course` / `Wiki` / `Notes` / `Materials` / `Docs` / `2026`；
4. 字符集 `[A-Za-z0-9-]`，长度 ≤ 24，不用缩写与下划线；
5. 建库前用 `gh api repos/<org>/<name>` 检查占用（404 即可用），重名则追加核心限定词，不追加数字后缀。

## 流程

### 阶段 0 · 采集参数（不要猜）

用 `AskUserQuestion` 确认四件事（或由 `--auto` 传入）：

1. **组织与可见性** —— 默认 `acaGPT` + 公开（主仓库 `main`，公开）；
2. **站点主旨与仓库名** —— 由主旨推导仓库名并按上节规则校验；
3. **版权主体与年份** —— 默认 `iLINGBIN`，年份取当前年；
4. **内容源目录与页面清单** —— 见下。

### 阶段 1 · 页面清单（`pages.tsv`）

wiki 的文件名必须是 ASCII，而标题通常是中文，**这一层映射必须由人确认，不能自动音译**。源目录根下放 `pages.tsv`，制表符分隔，首行为表头：

```
slug	zh_title	en_title	zh_summary	en_summary	source
Course-Syllabus	课程大纲	Course Syllabus	中英双语完整大纲……	The complete bilingual syllabus……	syllabus.md
```

- `source` 省略时按 `slug` 在同目录找同名 `.md`；
- 无 `pages.tsv` 时脚本自动推导：slug 取文件名，标题取首个 `#` 标题，摘要留空（首页只列标题）——**随后必须人工补齐英文标题与双语摘要**，否则首页会退化。

### 阶段 2 · 归一化

```bash
python3 scripts/normalize_pages.py --source <源目录> --out <构建目录> \
  --org acaGPT --repo <RepoName> [--map pages.tsv] [--auto]
```

做四件事：文件名规范化并复制；页内相对链接改写为绝对 URL；`[[页面名]]` 转为绝对 URL；体检（非 ASCII 文件名、空文件、缺 H1、裸 `<script>`/`<style>`）。

### 阶段 3 · 生成导航与首页

```bash
python3 scripts/build_nav.py --pages <构建目录> --org acaGPT --repo <RepoName> \
  --site-zh "《法理学》课程 Wiki" --site-en "Jurisprudence Course Wiki" \
  --copyright iLINGBIN [--map pages.tsv] [--auto]
```

产出 `_Sidebar.md`（相对页名）与 `Home.md`（中英双段、绝对 URL）。

### 阶段 4 · 建库与推送

```bash
python3 scripts/new_wiki.py --org acaGPT --name <RepoName> \
  --source <构建目录> --description "……" --copyright iLINGBIN \
  [--workdir <工作目录>] [--auto] [--check-links]
```

主控流程：校验仓库名 → `gh repo create --public --clone` → 写 `LICENSE` / `README.md` 并推送到 `main` → 打开 `https://github.com/<org>/<repo>/wiki/_new` 并**提示用户手工创建首页** → 克隆 `<repo>.wiki.git` → 复制页面、`_Sidebar.md`、`LICENSE`、`images/` → 提交并推送到 `master` → 核验。

**首页必须先由人在网页端创建。** GitHub 的 wiki 仓库在首次创建页面前并不存在，直接克隆 `*.wiki.git` 会返回 404；这是唯一无法自动化的一步。交互模式下脚本会等待并重试，`--auto` 下检测到不可克隆即退出码 2 并打印指引。

### 阶段 5 · 校验

```bash
python3 scripts/check_pages.py --pages <wiki 克隆目录> --org acaGPT --repo <RepoName> [--check-links]
```

静态项：文件名字符集合法、`_Sidebar.md` 覆盖全部页面、绝对 URL 指向存在的页面、图片文件存在、首页含中英两段。
`--check-links` 逐条发 HEAD 请求核验 HTTP 200（外链慢，需要对端容忍，默认关闭）。

## 坑位

详见 `references/gotchas.md`。三条必记：

1. **wiki 首页不能自动创建** —— GitHub API 不提供写 wiki 页面的接口，只能走 git；而 wiki 仓库在首个页面被创建后才存在。
2. **wiki 默认分支是 `master`**，不是 `main`；新仓库的 `init.defaultBranch` 若为 `main`，推送时会推到空分支。
3. **侧栏与首页的链接形式相反** —— 侧栏用相对页名、首页用绝对 URL，混用会在某些入口下失效。

## 可选的常见 wiki 功能

`_Footer.md` 页脚、`[[_TOC_]]` 页内目录、锚点跳转、术语表页、变更日志页、`images/` + 署名页、页面内嵌 HTML/Mermaid、双向链接的人工索引、页面历史与修订对比、整站 `git clone` 离线备份。取舍与写法见 `references/wiki-features.md`。
