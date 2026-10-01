#!/usr/bin/env python3
"""check_pages.py —— GitHub wiki 页面静态校验与可选外链核验。

用途：
    发布前或发布后检查页面是否符合 acaGPT/Jurisprudence 范式，避免断链、非法文件名、
    侧栏漏项、图片缺失与首页结构不完整。

使用方法：
    python3 check_pages.py --pages <wiki 目录> --org acaGPT --repo <RepoName> [--check-links] [--auto]

参数：
    --pages       wiki 目录（本地克隆或构建目录，必填）
    --org         GitHub 组织或用户名（默认 acaGPT）
    --repo        仓库名（必填）
    --check-links 逐条核验站内绝对 URL 与外链的 HTTP 状态（慢，默认关闭）
    --auto        非交互执行

返回：
    0 无错误（可能有警告）；1 存在错误；2 参数错误。
"""

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

NAME_OK = re.compile(r"^_?[A-Za-z0-9.-]+\.md$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SIDEBAR_RE = re.compile(r"^-\s+\[([^\]]+)\]\(([^)\s]+)\)", re.M)
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"|!\[[^\]]*\]\(([^)\s]+)\)')
CJK_RE = re.compile(r"[一-鿿]")
UA = "gh-wiki-maker-linkcheck/1.0"


def fail(msg):
    print(f"[错误] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[警告] {msg}")


def info(msg):
    print(f"[信息] {msg}")


def http_status(url, timeout=20):
    """返回 HTTP 状态码；HEAD 被拒（405/403）时回退 GET。"""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 405) and method == "HEAD":
                continue
            return exc.code
        except Exception:
            if method == "HEAD":
                continue
            return -1
    return -1


def main():
    ap = argparse.ArgumentParser(description="校验 wiki 页面")
    ap.add_argument("--pages", required=True)
    ap.add_argument("--org", default="acaGPT")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--check-links", action="store_true")
    ap.add_argument("--auto", action="store_true")
    args = ap.parse_args()

    pages_dir = Path(args.pages).expanduser().resolve()
    if not pages_dir.is_dir():
        fail(f"目录不存在：{pages_dir}")
        return 2

    errors, warnings = [], []
    files = sorted(pages_dir.glob("*.md"))
    if not files:
        fail("目录中没有 .md 页面")
        return 1

    slugs = set()
    reserved = {"_Sidebar.md", "_Footer.md"}
    for path in files:
        if not NAME_OK.match(path.name):
            errors.append(f"文件名不合法（仅 ASCII 字母/数字/连字符/点）：{path.name}")
            continue
        if path.name in reserved:
            continue
        slugs.add(path.stem)

    if "Home.md" not in {p.name for p in files}:
        errors.append("缺少首页 Home.md")
    sidebar_path = pages_dir / "_Sidebar.md"
    if not sidebar_path.is_file():
        errors.append("缺少侧栏 _Sidebar.md")
        sidebar_targets = []
    else:
        sidebar_text = sidebar_path.read_text(encoding="utf-8", errors="replace")
        sidebar_targets = [m.group(2) for m in SIDEBAR_RE.finditer(sidebar_text)]
        for t in sidebar_targets:
            if t.startswith(("http://", "https://")):
                warnings.append(f"侧栏应使用相对页名，发现绝对 URL：{t}")
            elif t not in slugs:
                errors.append(f"侧栏指向不存在的页面：{t}")
        missing = sorted(slugs - set(sidebar_targets) - {"Home"})
        for m in missing:
            warnings.append(f"页面未在侧栏登记：{m}")
        if sidebar_targets and sidebar_targets[0] != "Home":
            warnings.append("侧栏首项应为 Home")

    base = f"https://github.com/{args.org}/{args.repo}/wiki"
    wiki_links, external_links = set(), set()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in LINK_RE.finditer(text):
            target = m.group(2)
            if target.startswith(base + "/"):
                wiki_links.add(target[len(base) + 1 :])
            elif target.startswith(("http://", "https://")):
                external_links.add(target)
            elif target.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")):
                if not (pages_dir / target).exists():
                    errors.append(f"{path.name}：图片缺失 {target}")
        for m in IMG_RE.finditer(text):
            rel = m.group(1) or m.group(2) or ""
            if rel.startswith(("http://", "https://")):
                continue
            if rel and not (pages_dir / rel).exists():
                errors.append(f"{path.name}：图片缺失 {rel}")

    for slug in sorted(wiki_links):
        if slug not in slugs:
            errors.append(f"绝对 URL 指向不存在的页面：{slug}")

    home_path = pages_dir / "Home.md"
    if home_path.is_file():
        home_text = home_path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"^---\s*$", home_text, re.M):
            warnings.append("Home.md 缺少中英分段分隔符 ---")
        parts = re.split(r"^---\s*$", home_text, flags=re.M)
        if len(parts) < 2:
            warnings.append("Home.md 未检出中英双段")
        else:
            if not CJK_RE.search(parts[0]):
                warnings.append("Home.md 中文段未检出中文内容")
            if CJK_RE.search(parts[-1]) and not re.search(r"^\s*#\s+\w", parts[-1], re.M):
                warnings.append("Home.md 英文段混入中文标题")
    if not (pages_dir / "LICENSE").exists():
        warnings.append("wiki 根目录缺少 LICENSE")

    if args.check_links:
        info(f"开始核验链接（站内 {len(wiki_links)} 条，外链 {len(external_links)} 条）")
        bad = []
        for slug in sorted(wiki_links):
            code = http_status(f"{base}/{slug}")
            if code != 200:
                bad.append((f"{base}/{slug}", code))
            time.sleep(0.3)
        for url in sorted(external_links):
            code = http_status(url)
            if code not in (200, 0):
                bad.append((url, code))
            time.sleep(0.5)
        for url, code in bad:
            errors.append(f"链接不可访问（{code}）：{url}")
        info(f"链接核验完成，异常 {len(bad)} 条")

    for w in warnings:
        warn(w)
    for e in errors:
        fail(e)
    info(f"页面 {len(files)} 个；错误 {len(errors)} 项，警告 {len(warnings)} 项")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
