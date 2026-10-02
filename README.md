# gh-wiki-maker

将本地 Markdown 内容发布为 GitHub Wiki 的用户级技能，页面范式沿用 `acaGPT/Jurisprudence`：纯 Markdown、ASCII 连字符文件名、`_Sidebar.md` 侧栏导航、根目录「保留所有权利」LICENSE、首页中英双段、页内互链一律绝对 URL。

## 功能

- 在指定组织（默认 `acaGPT`）创建**公开**仓库，写入自定义「保留所有权利」`LICENSE` 与指向 wiki 的 `README.md`；
- 归一化页面：文件名规范化、相对链接与 `[[页面名]]` 改写为绝对 URL、静态体检；
- 生成 `_Sidebar.md`（相对页名）、`Home.md`（中英双段）、可选 `_Footer.md`；
- 提示人工创建 Wiki 首页（GitHub 无写 wiki 的 API，此步不可自动化），随后克隆 `<repo>.wiki.git` 批量推送页面至 `master`；
- 发布核验：侧栏覆盖、绝对 URL 指向、图片存在、首页双段结构，可选逐条 HTTP 核验。

## 目录结构

```
SKILL.md                     技能入口：范式、命名规则、五阶段流程
references/paradigm.md       acaGPT/Jurisprudence 范式逐项拆解
references/naming.md         仓库与页面命名规则
references/wiki-features.md  常见 wiki 功能清单与取舍
references/gotchas.md        实测坑位（含 2026-10-02 验证结论）
assets/                      LICENSE / README / 文本模板
scripts/normalize_pages.py   页面归一化
scripts/build_nav.py         侧栏、首页、页脚生成
scripts/check_pages.py       静态校验与外链核验
scripts/new_wiki.py          建库推送主控
```

## 使用方法

四个脚本均只依赖 Python 3 标准库与 `gh`、`git`，全部支持 `--auto` 非交互执行：

```bash
S=~/.workbuddy/skills/gh-wiki-maker/scripts

python3 $S/normalize_pages.py --source ./source --out ./build \
  --org acaGPT --repo <RepoName> --map ./source/pages.tsv

python3 $S/build_nav.py --pages ./build --org acaGPT --repo <RepoName> \
  --site-zh "《站点名》" --site-en "Site Name" --copyright iLINGBIN --footer

python3 $S/new_wiki.py --name <RepoName> --source ./build \
  --description "……" --copyright iLINGBIN --check-links

python3 $S/check_pages.py --pages ./build --org acaGPT --repo <RepoName> --check-links
```

页面清单 `pages.tsv` 的列定义与自动推导规则见 `SKILL.md`「阶段 1」。

## 关键约束

1. **Wiki 首页必须由人在网页端创建**：API 与 `git push` 均无法初始化空的 wiki 仓库（已实测）；
2. wiki 仓库默认分支是 `master`，主仓库是 `main`；
3. 侧栏用相对页名、正文用绝对 URL，两者不得混用；
4. 仓库名依 `references/naming.md` 裁定：英文核心词、PascalCase、≤24 字符、去容器词。

## 版本

- v1.0.1（2026-10-02）：补注端到端样本 `acaGPT/GHWikiMaker` 已归档为只读，wiki 首页人工创建步骤未实际完成，样本仅作流程留档。
- v1.0.0（2026-10-02）：首版。四脚本、四份参考文档、文本模板；端到端样本 `acaGPT/GHWikiMaker`。
