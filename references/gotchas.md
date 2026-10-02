# 实测坑位

## 一、wiki 仓库必须先由人创建首页

- GitHub **没有**写 wiki 页面的 REST 接口，写页面只能走 git：`git clone https://github.com/<org>/<repo>.wiki.git`。
- 但 wiki 仓库在**第一个页面被创建之前并不存在**，此时克隆返回：
  ```
  fatal: repository 'https://github.com/<org>/<repo>.wiki.git/' not found
  ```
- 解法：先让人在 `https://github.com/<org>/<repo>/wiki/_new` 建一个标题为 `Home` 的页面（内容随意，脚本随后会覆盖）。
- 仓库设置里的 `has_wiki` 必须为真；用 `gh api -X PATCH repos/<org>/<repo> -f has_wiki=true` 兜底。
- 脚本策略：交互模式下轮询重试克隆（默认 10 次 × 15 秒），`--auto` 下失败即退出码 2 并打印指引。
- **直接 `git push` 到空 wiki 同样无效**（2026-10-02 实测）：对从未初始化的 wiki 执行 `git push -u origin master` 返回 `remote: Repository not found`。即 API 与 git 两条路都走不通，首个页面只能由人在网页端创建。

## 二、分支名

- wiki 仓库默认分支是 **`master`**，主仓库通常是 `main`。克隆后先 `git branch --show-current` 确认，推送时显式写 `git push origin HEAD:master`。
- 本机 `init.defaultBranch=main` 时，在 wiki 目录里 `git init` 出来的空仓库会叫 `main`，容易推错。

## 三、链接形式不能混用

- `_Sidebar.md`：写**页名**（`- [Home](Home)`），GitHub 自动补成 wiki 链接；
- 正文与 `Home.md`：写**绝对 URL**（`https://github.com/<org>/<repo>/wiki/<Page>`）。
- 反过来用会出问题：正文里写相对页名，在「页面源码」视图或外部镜像下会跳到主仓库路径；侧栏里写绝对 URL 则在某些主题下重复前缀。

## 四、gh 建库

- 组织仓库：`gh repo create <org>/<name> --public --clone`。省略 `--license` 才不会生成模板 LICENSE（我们要自定义的「保留所有权利」）。
- `--clone` 对空仓库会提示「cloned empty repository」，属正常。
- 空仓库首次推送需要一次提交，先写 `LICENSE` 与 `README.md` 再 `git push -u origin main`。
- 描述 ≤ 100 字符；topics 用 `gh api -X PUT repos/<org>/<name>/topics -f names[]=...` 设置（默认不设）。

## 五、链接核验

- 绝对 URL 里的页名与磁盘文件名必须逐字符一致（含大小写）；GitHub wiki 对大小写**不敏感**但对外链镜像敏感，按严格匹配处理。
- 外链核验用 HEAD 请求；部分站点对 HEAD 返回 405，需回退 GET（只读前若干字节）。
- 批量核验要加间隔并做指数退避，否则触发 429。

## 六、可见性、归档与 wiki 开关的耦合

- **归档仓库是只读的**：`PATCH archived=true` 后，改可见性与 `has_wiki` 均返回 `403 Repository was archived so is read-only`。要改这两项，必须先 `archived=false` 再改，最后视需要重新归档。
- **public → private 会把 wiki 关掉**（2026-10-02 实测）：`PATCH private=true` 之后 `has_wiki` 由 `true` 变 `false`。
- **关掉的 wiki 用 API / CLI 拉不回来**：`PATCH -f has_wiki=true`（含 JSON body 形式）、`gh repo edit --enable-wiki` 都返回成功但 `has_wiki` 仍为 `false`；归档状态下则直接 403。
- 恢复方式：进入 `https://github.com/<org>/<repo>/settings` → **Features** → 勾选 **Wiki**，由人在网页端操作。
- 结论：发布流程里 **visibility 一旦变更就要回头检查 `has_wiki`**，并在建库时就把可见性一次定好，避免转换触发开关丢失。

## 七、其他

- 页面里不要写 `[[_TOC_]]` 之外的高级 Gollum 语法（如 `[[include:...]]`），GitHub 未启用。
- wiki 页面**不渲染** LaTeX 数学公式；需要公式就用代码块或图片。
- `images/` 目录随 wiki 走，不随主仓库走；体积大时考虑外链并注明失效风险。
