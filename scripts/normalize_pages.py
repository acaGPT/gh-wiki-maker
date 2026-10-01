#!/usr/bin/env python3
"""normalize_pages.py —— 把本地 Markdown 归一化为 GitHub wiki 页面。

用途：
    1. 依 pages.tsv（或文件名推导）确定 ASCII 连字符页面名；
    2. 复制并重命名源文件到构建目录；
    3. 把页内指向其他页面的相对链接改写为绝对 URL；
    4. 体检：非 ASCII 文件名、空文件、缺一级标题、裸 script/style 标签。

使用方法：
    python3 normalize_pages.py --source <源目录> --out <构建目录> \
        --org acaGPT --repo <RepoName> [--map pages.tsv] [--meta pages.meta.tsv] [--auto]

参数：
    --source     源 Markdown 目录（必填）
    --out        构建输出目录（必填，自动创建）
    --org        GitHub 组织或用户名（默认 acaGPT）
    --repo       仓库名（必填，用于拼绝对 URL）
    --map        页面清单 pages.tsv；缺省时自动推导
    --meta       输出元信息表路径（默认 <out>.meta.tsv）
    --auto       非交互：缺少英文标题或摘要时只告警不中断

返回：
    0 成功；1 校验失败（存在必须人工处理的问题）；2 参数错误。
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

SLUG_OK = re.compile(r"^[A-Za-z0-9.-]+$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

TSV_FIELDS = ("slug", "zh_title", "en_title", "zh_summary", "en_summary", "source")


def fail(msg):
    print(f"[错误] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[警告] {msg}")


def info(msg):
    print(f"[信息] {msg}")


def slugify(stem):
    """把文件名主干转成合法 wiki 页面名；无法转换时返回空字符串。"""
    out = []
    prev_dash = False
    for ch in stem:
        if ch.isascii() and (ch.isalnum() or ch in ".-"):
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug


def load_map(path):
    """读取 pages.tsv，返回 [{slug, zh_title, en_title, zh_summary, en_summary, source}]。"""
    rows = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines:
        return rows
    header = [h.strip().lower() for h in lines[0].split("\t")]
    if header[0] != "slug":
        fail("pages.tsv 首行必须是表头，且首列为 slug")
        sys.exit(2)
    for line in lines[1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = (line.split("\t") + [""] * len(TSV_FIELDS))[: len(TSV_FIELDS)]
        rows.append(dict(zip(TSV_FIELDS, [c.strip() for c in cells])))
    return rows


def first_heading(text):
    m = H1_RE.search(text)
    return m.group(1).strip() if m else ""


def split_bilingual(h1):
    """从形如「中文（English）」的一级标题中拆出中英文标题。"""
    m = re.match(r"^(.*?)[（(]\s*([A-Za-z].*?)\s*[)）]\s*$", h1)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return h1, ""


def derive_rows(source_dir):
    """无 pages.tsv 时按文件名与一级标题自动推导页面清单。"""
    rows = []
    for path in sorted(source_dir.glob("*.md")):
        if path.name.startswith("_") or path.name.lower() in ("home.md", "license.md"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        h1 = first_heading(text)
        if not h1:
            h1 = path.stem
        zh, en = split_bilingual(h1)
        slug = slugify(path.stem)
        rows.append(
            {
                "slug": slug,
                "zh_title": zh,
                "en_title": en,
                "zh_summary": "",
                "en_summary": "",
                "source": path.name,
            }
        )
    return rows


def abs_url(org, repo, slug):
    return f"https://github.com/{org}/{repo}/wiki/{slug}"


def rewrite_links(text, org, repo, slugs):
    """相对页内链接与 [[页面名]] 一律改为绝对 URL；返回 (新文本, 改动数, 未解析集合)。"""
    changed = 0
    unresolved = set()

    def replace_md(m):
        nonlocal changed
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        if target.lower().endswith(IMAGE_EXT):
            return m.group(0)
        base = target[:-3] if target.lower().endswith(".md") else target
        base = base.rstrip("/")
        if base in slugs:
            changed += 1
            return f"[{label}]({abs_url(org, repo, base)})"
        unresolved.add(target)
        return m.group(0)

    text = LINK_RE.sub(replace_md, text)

    def replace_wiki(m):
        nonlocal changed
        name, label = m.group(1).strip(), (m.group(2) or "").strip()
        slug = name[:-3] if name.lower().endswith(".md") else name
        slug = slug.replace(" ", "-")
        if slug in slugs:
            changed += 1
            return f"[{label or name}]({abs_url(org, repo, slug)})"
        unresolved.add(name)
        return m.group(0)

    text = WIKILINK_RE.sub(replace_wiki, text)
    return text, changed, unresolved


def lint(slug, text):
    problems = []
    if not text.strip():
        problems.append("空文件")
    if not H1_RE.search(text):
        problems.append("缺少一级标题（#）")
    if re.search(r"<\s*(script|style)\b", text, re.I):
        problems.append("含 script/style 标签，wiki 会剥离")
    return problems


def main():
    ap = argparse.ArgumentParser(description="归一化本地 Markdown 为 GitHub wiki 页面")
    ap.add_argument("--source", required=True, help="源 Markdown 目录")
    ap.add_argument("--out", required=True, help="构建输出目录")
    ap.add_argument("--org", default="acaGPT", help="GitHub 组织或用户名")
    ap.add_argument("--repo", required=True, help="仓库名")
    ap.add_argument("--map", default=None, help="页面清单 pages.tsv")
    ap.add_argument("--meta", default=None, help="输出元信息表路径")
    ap.add_argument("--auto", action="store_true", help="非交互执行")
    args = ap.parse_args()

    source_dir = Path(args.source).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    if not source_dir.is_dir():
        fail(f"源目录不存在：{source_dir}")
        return 2
    if out_dir.exists() and not out_dir.is_dir():
        fail(f"输出路径已存在且不是目录：{out_dir}")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.map:
        map_path = Path(args.map).expanduser().resolve()
        if not map_path.is_file():
            fail(f"页面清单不存在：{map_path}")
            return 2
        rows = load_map(map_path)
        derived = False
    else:
        rows = derive_rows(source_dir)
        derived = True
    if not rows:
        fail("没有可处理的页面")
        return 1

    slugs = []
    errors = []
    for row in rows:
        slug = row["slug"] or slugify(Path(row["source"] or row["slug"]).stem)
        if not slug or not SLUG_OK.match(slug) or slug.startswith("_"):
            errors.append(f"页面名不合法（需 ASCII 字母/数字/连字符/点，且不以 _ 开头）：{row['source'] or slug}")
            continue
        row["slug"] = slug
        slugs.append(slug)
    if errors:
        for e in errors:
            fail(e)
        return 1

    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    if dupes:
        fail(f"页面名重复：{', '.join(dupes)}")
        return 1

    slug_set = set(slugs)
    meta_rows = []
    total_links = 0
    unresolved_all = set()

    for row in rows:
        src_name = row["source"] or f"{row['slug']}.md"
        src_path = source_dir / src_name
        if not src_path.is_file():
            alt = source_dir / f"{row['slug']}.md"
            if alt.is_file():
                src_path = alt
            else:
                fail(f"源文件不存在：{src_path}")
                return 1
        text = src_path.read_text(encoding="utf-8", errors="replace")
        problems = lint(row["slug"], text)
        for p in problems:
            warn(f"{row['slug']}：{p}")
        new_text, changed, unresolved = rewrite_links(text, args.org, args.repo, slug_set)
        total_links += changed
        unresolved_all |= unresolved
        if not row["zh_title"]:
            row["zh_title"] = first_heading(text) or row["slug"]
        if not row["en_title"]:
            row["en_title"] = row["slug"].replace("-", " ")
        if not row["en_title"] or not row["zh_title"]:
            msg = f"{row['slug']} 缺少英文标题"
            if args.auto:
                warn(msg)
            else:
                fail(msg)
                return 1
        (out_dir / f"{row['slug']}.md").write_text(new_text, encoding="utf-8")
        meta_rows.append(row)

    images = source_dir / "images"
    if images.is_dir():
        shutil.copytree(images, out_dir / "images", dirs_exist_ok=True)
        info(f"已复制图片目录：{images} → {out_dir / 'images'}")

    meta_path = Path(args.meta).expanduser().resolve() if args.meta else out_dir.parent / f"{out_dir.name}.meta.tsv"
    with meta_path.open("w", encoding="utf-8") as fh:
        fh.write("\t".join(TSV_FIELDS) + "\n")
        for r in meta_rows:
            fh.write("\t".join(r.get(k, "") for k in TSV_FIELDS) + "\n")

    info(f"页面 {len(meta_rows)} 个 → {out_dir}")
    info(f"改写站内链接 {total_links} 处 → 绝对 URL")
    info(f"元信息表：{meta_path}")
    if derived:
        warn("未使用 pages.tsv，标题与摘要为自动推导；发布前请补齐 pages.tsv 中的英文标题与双语摘要。")
    if unresolved_all:
        warn(f"以下链接未匹配到页面名，保持原样：{', '.join(sorted(unresolved_all))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
