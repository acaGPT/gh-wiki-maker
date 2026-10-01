# 命名规则

## 一、仓库名

判定顺序：

1. 取主旨的**英文核心词**。能用一个词说清就不用两个词。
2. 多词用 **PascalCase 连写**，首词首字母大写，其余词首字母大写、不加分隔符。
3. 连写会造成误读时才用连字符（`Legal-Formalism` 优于 `LegalFormalism` 仅在会产生歧义时）。
4. 删除容器词：`Course` / `Wiki` / `Notes` / `Materials` / `Docs` / `Handbook` / 年份。
5. 字符集合法 `[A-Za-z0-9-]`，长度 ≤ 24；不用下划线、不用缩写。

示例：

| 主旨 | 采用 | 弃用 |
| --- | --- | --- |
| 法理学课程 | `Jurisprudence` | `Jurisprudence-Course-Wiki` |
| 近代自然法与社会契约论 | `NaturalLawTheory` | `Modern-Natural-Law-and-Social-Contract-Theory` |
| 宪法学讲义 | `ConstitutionalLaw` | `ConstLaw2026` |
| 法律形式主义与现实主义之争 | `LegalFormalism` | `Legal-Formalism-vs-Realism-Notes` |

占用处理：先 `gh api repos/<org>/<name>`，404 才可用；被占用则**追加核心限定词**（`JurisprudenceSeminars`），不加数字后缀。

## 二、页面名（wiki 文件名）

- 字符集 `[A-Za-z0-9.-]`；单词间 `-`；章节编号结尾带 `.`（`PI.2.-`）；
- 一律英文；中文标题只出现在 H1 与导航文案里；
- 避免 `&`、`(`、`)`、`'`、空格、中文标点 —— GitHub 会把它们转义成 `%xx`，链接易断；
- 页名发布后即成永久地址，改名要同步改 `_Sidebar.md`、`Home.md` 与所有绝对 URL。

## 三、辅助页

| 页名 | 用途 |
| --- | --- |
| `Home.md` | 首页，中英双语导航 |
| `_Sidebar.md` | 侧栏 |
| `_Footer.md` | 页脚（可选） |
| `Glossary.md` | 术语/译名对照表 |
| `Changelog.md` | 变更日志 |
| `Portrait-Credits.md` | 图片来源与授权 |
