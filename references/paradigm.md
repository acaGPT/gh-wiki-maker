# acaGPT/Jurisprudence 范式拆解

来源：克隆 `https://github.com/acaGPT/Jurisprudence.wiki.git`（默认分支 `master`）后逐文件比对得出。

## 一、仓库与 wiki 的关系

| 项 | 主仓库 | wiki 仓库 |
| --- | --- | --- |
| 地址 | `github.com/acaGPT/Jurisprudence` | `github.com/acaGPT/Jurisprudence.wiki.git` |
| 默认分支 | `main` | `master` |
| 主要文件 | `LICENSE`、`README.md` | `Home.md`、`_Sidebar.md`、`LICENSE`、`*.md`、`images/` |
| 提交方式 | 常规 git | 常规 git（另可在网页端直接编辑） |

主仓库极简，只承担「入口 + 版权」两项职责；内容全部落在 wiki。

## 二、文件命名

```
Home.md
_Sidebar.md
LICENSE
Course-Syllabus.md
PI.2.-What-is-Jurisprudence.md
PII.3.-Classical-Natural-Law.md
PVI.1.a.-Legal-Formalism-vs-Legal-Realism.md
Glossary.md
Portrait-Credits.md
images/…
tools/…
```

规则：

- 只含 `[A-Za-z0-9.-]`；单词间用 `-`；层级编号用 `.` 结尾（`PI.2.-`、`PVI.1.a.-`）；
- 页名即 URL 片段，一经验证即成永久标识，**改名等于断链**，故首次入库前需确认；
- 中文标题不进文件名，只出现在页内 H1 与首页导航。

## 三、`_Sidebar.md`（相对页名）

```markdown
- [Home](Home)
- [Course Syllabus](Course-Syllabus)
- [PI.2. What is Jurisprudence](PI.2.-What-is-Jurisprudence)
```

- 标签用**英文页名**；顺序即阅读顺序；`Home` 置首，附录类（署名、词表）置末；
- 链接写**页名**，不写 URL、不带 `.md`。

## 四、`Home.md`（绝对 URL + 中英双段）

结构：

1. `# 中文站点名` + 一句中文说明；
2. `## 页面导航` —— 每行 `- [英文页名](绝对URL) —— 中文一句话摘要`；
3. `## 说明` —— 本地编辑方式、外链核验状态、版权声明；
4. `---`；
5. `# English Site Name` + 一句英文说明；
6. `## Pages` —— 每行 `- [英文页名](绝对URL) — English one-line summary`；
7. 版权英文段。

绝对 URL 形如：

```
https://github.com/acaGPT/Jurisprudence/wiki/PI.3.-Classical-Natural-Law
```

同一行内可以再嵌一次指向本页的链接（中文标题处），形成「英文页名 + 中文标题」双链，这是该范式的显著特征。

## 五、正文页

- H1 为中英对照：`# 法理学 — 课程大纲（Jurisprudence — Syllabus）`；
- 表格表头双语：`| 项目（Item） | 内容（Detail） |`；
- 段落级双语：中文段落后紧跟对应英文段落（不是逐句夹注）；
- 大段落前可用 `>` 引用块写「材料说明」，同样中英各一段；
- 延伸阅读区块配肖像时用 `<img src="images/xxx.jpg" width="60" align="left">` 之类行内 HTML，并在 `Portrait-Credits.md` 记明来源与授权。

## 六、`LICENSE`（自定义，非 SPDX）

```
Copyright (c) 2026 iLINGBIN

保留所有权利（All Rights Reserved）

本仓库及课程 Wiki（大纲、讲稿、词表、图示、页面代码）整体依「保留所有权利」原则处理：未获书面许可，不得以复制、改写、汇编、翻译、上传网络、制作衍生讲义、商业性使用等方式利用。课堂内为教学目的之讲授、投影、复印，属许可范围内之使用；公开出版、网络公开发布、商业培训或二次改编须先行取得书面同意。
```

要点：

- GitHub 的 license 模板列表里**没有**「All Rights Reserved」，必须用自定义文本；
- 中文正文在前、`All Rights Reserved` 括注在后，便于中文读者直接理解；
- 明确写出「课堂讲授、投影、复印」属许可范围，否则对教学材料过于苛刻。
