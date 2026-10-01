#!/usr/bin/env python3
"""new_wiki.py —— 创建公开仓库并把归一化后的页面推送为 GitHub Wiki。

用途：
    串联「建公开仓库 → 写 LICENSE/README → 提示人工创建 Wiki 首页 → 克隆 wiki 仓库 →
    推送页面与侧栏 → 核验」全流程，沿用 acaGPT/Jurisprudence 范式。

使用方法：
    python3 new_wiki.py --name <RepoName> --source <构建目录> \
        --description "……" [--org acaGPT] [--copyright iLINGBIN] \
        [--workdir <工作目录>] [--auto] [--check-links] [--skip-repo]

参数：
    --name        仓库名（PascalCase、≤24 字符，必填）
    --source      归一化后的页面目录（必填）
    --description 仓库描述（≤100 字符，必填）
    --org         组织或用户名（默认 acaGPT）
    --copyright   版权主体（默认 iLINGBIN）
    --year        版权年份（默认当前年）
    --workdir     工作目录（默认系统临时目录下建子目录）
    --retries     等待人工创建首页的克隆重试次数（默认 10）
    --wait        每次重试间隔秒数（默认 15）
    --skip-repo   仓库已存在时跳过建库，直接进入 wiki 阶段
    --topics      仓库 topics，逗号分隔（默认不设）
    --auto        非交互：不打开浏览器、不等待人工确认
    --check-links 推送后核验页面可访问性

返回：
    0 成功；1 流程失败；2 参数或前置条件不满足；3 等待人工创建首页超时。
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
NAME_OK = re.compile(r"^[A-Za-z0-9-]{1,24}$")


def fail(msg):
    print(f"[错误] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[警告] {msg}")


def info(msg):
    print(f"[信息] {msg}")


def run(cmd, cwd=None, check=True, capture=True):
    """执行命令；返回 (返回码, 标准输出)。"""
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=capture,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"命令失败（{proc.returncode}）：{' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.returncode, (proc.stdout or "").strip()


def render(template_name, **pairs):
    text = (ASSETS / template_name).read_text(encoding="utf-8")
    for key, value in pairs.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def repo_exists(org, name):
    code, _ = run(["gh", "api", f"repos/{org}/{name}"], check=False)
    return code == 0


def clone_wiki(org, name, dest):
    url = f"https://github.com/{org}/{name}.wiki.git"
    if dest.exists():
        shutil.rmtree(dest)
    code, _ = run(["git", "clone", url, str(dest)], check=False)
    return code == 0


def main():
    ap = argparse.ArgumentParser(description="创建仓库并发布 GitHub Wiki")
    ap.add_argument("--name", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--org", default="acaGPT")
    ap.add_argument("--copyright", default="iLINGBIN")
    ap.add_argument("--year", default=None)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--retries", type=int, default=10)
    ap.add_argument("--wait", type=int, default=15)
    ap.add_argument("--skip-repo", action="store_true")
    ap.add_argument("--topics", default="")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--check-links", action="store_true")
    args = ap.parse_args()

    name = args.name.strip()
    if not NAME_OK.match(name):
        fail(f"仓库名不合法（仅字母/数字/连字符，≤24 字符）：{name}")
        return 2
    if len(args.description) > 100:
        fail(f"仓库描述超过 100 字符：{len(args.description)}")
        return 2

    source_dir = Path(args.source).expanduser().resolve()
    if not source_dir.is_dir():
        fail(f"页面目录不存在：{source_dir}")
        return 2
    if not list(source_dir.glob("*.md")):
        fail(f"页面目录中没有 .md 文件：{source_dir}")
        return 2

    workdir = Path(args.workdir).expanduser().resolve() if args.workdir else Path(tempfile.mkdtemp(prefix="gh-wiki-"))
    workdir.mkdir(parents=True, exist_ok=True)
    year = args.year or str(date.today().year)
    full = f"{args.org}/{name}"
    wiki_url = f"https://github.com/{full}/wiki"
    wiki_clone = f"https://github.com/{full}.wiki.git"
    info(f"目标仓库：{full}（公开）")

    # 阶段一：建库
    if args.skip_repo:
        info("--skip-repo：跳过建库，直接进入 wiki 阶段")
    else:
        if repo_exists(args.org, name):
            fail(f"仓库已存在：{full}（若确要复用，请加 --skip-repo）")
            return 2
        run(["gh", "repo", "create", full, "--public", "--confirm", "--clone", "--description", args.description], cwd=workdir)
        run(["gh", "api", "-X", "PATCH", f"repos/{full}", "-f", "has_wiki=true"], cwd=workdir)
        if args.topics:
            topics = [t.strip() for t in args.topics.split(",") if t.strip()]
            cmd = ["gh", "api", "-X", "PUT", f"repos/{full}/topics"]
            for t in topics:
                cmd += ["-f", "names[]=" + t]
            run(cmd, cwd=workdir)
        info(f"仓库已创建：https://github.com/{full}")

        repo_dir = workdir / name
        (repo_dir / "LICENSE").write_text(
            render("LICENSE.all-rights-reserved.md", YEAR=year, HOLDER=args.copyright), encoding="utf-8"
        )
        (repo_dir / "README.md").write_text(
            render(
                "README.template.md",
                NAME=name,
                DESC_ZH=args.description,
                DESC_EN=args.description,
                WIKI_URL=wiki_url,
                WIKI_CLONE_URL=wiki_clone,
                YEAR=year,
                HOLDER=args.copyright,
            ),
            encoding="utf-8",
        )
        run(["git", "add", "-A"], cwd=repo_dir)
        run(["git", "commit", "-m", "添加版权声明与仓库说明"], cwd=repo_dir)
        branch, _ = run(["git", "branch", "--show-current"], cwd=repo_dir)
        run(["git", "push", "-u", "origin", branch or "main"], cwd=repo_dir)
        info("主仓库 LICENSE 与 README 已推送")

    # 阶段二：等待人工创建 Wiki 首页
    new_page_url = f"{wiki_url}/_new"
    print("\n" + "=" * 60)
    print("必须人工完成一步：创建 Wiki 首页")
    print(f"  1. 打开 {new_page_url}")
    print("  2. 标题填 Home，正文随意（脚本随后会覆盖为规范首页）")
    print("  3. 保存页面后回到这里")
    print("=" * 60 + "\n")
    if not args.auto:
        run(["open", new_page_url], check=False)

    wiki_dir = workdir / f"{name}.wiki"
    for attempt in range(1, args.retries + 1):
        if clone_wiki(args.org, name, wiki_dir):
            info(f"wiki 仓库已克隆：{wiki_dir}")
            break
        if args.auto:
            fail(f"wiki 仓库尚不存在（{wiki_clone}）。请先人工创建首页后重跑本脚本。")
            return 3
        info(f"第 {attempt}/{args.retries} 次尝试未检测到 wiki 仓库，{args.wait} 秒后重试……")
        time.sleep(args.wait)
    else:
        fail("等待人工创建 Wiki 首页超时")
        return 3

    # 阶段三：写入页面并推送
    for path in source_dir.glob("*.md"):
        shutil.copy2(path, wiki_dir / path.name)
    images = source_dir / "images"
    if images.is_dir():
        shutil.copytree(images, wiki_dir / "images", dirs_exist_ok=True)
    (wiki_dir / "LICENSE").write_text(
        render("LICENSE.all-rights-reserved.md", YEAR=year, HOLDER=args.copyright), encoding="utf-8"
    )
    info(f"已写入页面 {len(list(source_dir.glob('*.md')))} 个与 LICENSE")

    branch, _ = run(["git", "branch", "--show-current"], cwd=wiki_dir)
    run(["git", "add", "-A"], cwd=wiki_dir)
    code, _ = run(["git", "diff", "--cached", "--quiet"], cwd=wiki_dir, check=False)
    if code == 0:
        warn("没有需要提交的改动")
    else:
        run(["git", "commit", "-m", "发布 wiki 页面与侧栏导航"], cwd=wiki_dir)
        run(["git", "push", "origin", f"HEAD:{branch or 'master'}"], cwd=wiki_dir)
        info(f"已推送到 wiki 分支 {branch or 'master'}")

    # 阶段四：核验
    if args.check_links:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from check_pages import http_status

        targets = ["Home"] + sorted(p.stem for p in source_dir.glob("*.md") if not p.name.startswith("_"))
        bad = []
        for slug in targets:
            code = http_status(f"{wiki_url}/{slug}")
            if code != 200:
                bad.append((slug, code))
            time.sleep(0.3)
        for slug, code in bad:
            fail(f"页面不可访问（{code}）：{wiki_url}/{slug}")
        info(f"页面核验完成，异常 {len(bad)} 个")
        if bad:
            return 1

    print("\n" + "=" * 60)
    print(f"Wiki 地址：{wiki_url}")
    print(f"页面总数：{len(list(source_dir.glob('*.md')))}")
    print(f"工作目录：{workdir}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        fail(str(exc))
        sys.exit(1)
