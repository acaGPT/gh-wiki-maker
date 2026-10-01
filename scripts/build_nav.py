#!/usr/bin/env python3
"""build_nav.py —— 生成 GitHub wiki 的 _Sidebar.md、Home.md 与可选 _Footer.md。

用途：
    依页面元信息表生成侧栏（相对页名链接）与首页（中英双段、绝对 URL 互链），
    沿用 acaGPT/Jurisprudence 的范式。

使用方法：
    python3 build_nav.py --pages <构建目录> --org acaGPT --repo <RepoName> \
        --site-zh "《法理学》课程 Wiki" --site-en "Jurisprudence Course Wiki" \
        --copyright iLINGBIN [--meta pages.meta.tsv] [--footer] [--auto]

参数：
    --pages      归一化后的页面目录（必填）
    --org        GitHub 组织或用户名（默认 acaGPT）
    --repo       仓库名（必填）
    --site-zh    首页中文站点名（必填）
    --site-en    首页英文站点名（必填）
    --copyright  版权主体（默认 iLINGBIN）
    --year       版权年份（默认当前年）
    --meta       页面元信息表（默认 <pages>.meta.tsv）
    --intro-zh   首页中文说明段
    --intro-en   首页英文说明段
    --footer     同时生成 _Footer.md
    --auto       非交互执行

返回：
    0 成功；1 存在必须人工处理的问题；2 参数错误。
"""

import argparse
import sys
from datetime import date
from pathlib import Path

TSV_FIELDS = ("slug", "zh_title", "en_title", "zh_summary", "en_summary", "source")


def fail(msg):
    print(f"[错误] {msg}", file=sys.stderr)


def warn(msg):
    print(f"[警告] {msg}")


def info(msg):
    print(f"[信息] {msg}")


def load_meta(path):
    rows = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = (line.split("\t") + [""] * len(TSV_FIELDS))[: len(TSV_FIELDS)]
        rows.append(dict(zip(TSV_FIELDS, [c.strip() for c in cells])))
    return rows


def main():
    ap = argparse.ArgumentParser(description="生成 wiki 侧栏与首页")
    ap.add_argument("--pages", required=True, help="归一化后的页面目录")
    ap.add_argument("--org", default="acaGPT")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--site-zh", required=True)
    ap.add_argument("--site-en", required=True)
    ap.add_argument("--copyright", default="iLINGBIN")
    ap.add_argument("--year", default=None)
    ap.add_argument("--meta", default=None)
    ap.add_argument("--intro-zh", default=None)
    ap.add_argument("--intro-en", default=None)
    ap.add_argument("--footer", action="store_true")
    ap.add_argument("--auto", action="store_true")
    args = ap.parse_args()

    pages_dir = Path(args.pages).expanduser().resolve()
    if not pages_dir.is_dir():
        fail(f"页面目录不存在：{pages_dir}")
        return 2

    meta_path = Path(args.meta).expanduser().resolve() if args.meta else pages_dir.parent / f"{pages_dir.name}.meta.tsv"
    if not meta_path.is_file():
        fail(f"元信息表不存在：{meta_path}（请先运行 normalize_pages.py）")
        return 2

    rows = load_meta(meta_path)
    if not rows:
        fail("元信息表为空")
        return 1

    year = args.year or str(date.today().year)
    base = f"https://github.com/{args.org}/{args.repo}/wiki"
    clone_url = f"https://github.com/{args.org}/{args.repo}.wiki.git"

    on_disk = sorted(p.stem for p in pages_dir.glob("*.md") if not p.name.startswith("_"))
    extra = [s for s in on_disk if s not in {r["slug"] for r in rows}]
    for s in extra:
        warn(f"磁盘上存在未登记的页面：{s}（将追加到侧栏末尾）")
        rows.append(
            {
                "slug": s,
                "zh_title": s.replace("-", " "),
                "en_title": s.replace("-", " "),
                "zh_summary": "",
                "en_summary": "",
                "source": f"{s}.md",
            }
        )

    sidebar = ["- [Home](Home)"]
    for r in rows:
        label = r["en_title"] or r["slug"].replace("-", " ")
        sidebar.append(f"- [{label}]({r['slug']})")
    (pages_dir / "_Sidebar.md").write_text("\n".join(sidebar) + "\n", encoding="utf-8")
    info(f"已生成 _Sidebar.md（{len(rows)} 项）")

    intro_zh = args.intro_zh or f"本 Wiki 发布{args.site_zh}的内容，由 {args.copyright} 创建和维护。"
    intro_en = args.intro_en or (
        f"This wiki publishes the content of {args.site_en}, created and maintained by {args.copyright}."
    )

    zh_lines = [f"# {args.site_zh}", "", intro_zh, "", "## 页面导航", ""]
    en_lines = ["## Pages", ""]
    for r in rows:
        url = f"{base}/{r['slug']}"
        label = r["en_title"] or r["slug"].replace("-", " ")
        zh_body = r["zh_summary"] or r["zh_title"] or r["slug"]
        if r["zh_title"] and r["zh_title"] != r["en_title"]:
            zh_entry = f"- [{label}]({url}) —— [{r['zh_title']}]({url})：{zh_body}"
        else:
            zh_entry = f"- [{label}]({url}) —— {zh_body}"
        zh_lines.append(zh_entry)
        en_body = r["en_summary"] or r["en_title"] or r["slug"]
        en_lines.append(f"- [{label}]({url}) — {en_body}")

    zh_lines += [
        "",
        "## 说明",
        "",
        f"- 本地编辑方式：`git clone {clone_url}`，改 `.md` 页面后推送到默认分支 `master`。",
        "- 版权：本站内容依「保留所有权利」原则处理：未获书面许可，不得以复制、改写、汇编、翻译、上传网络、制作衍生讲义、商业性使用等方式利用；课堂内为教学目的之讲授、投影、复印属许可范围内之使用，公开出版、网络公开发布、商业培训或二次改编须先行取得书面同意。",
        f"- © {year} {args.copyright}. 保留所有权利。",
        "",
        "---",
        "",
        f"# {args.site_en}",
        "",
        intro_en,
        "",
    ]
    en_lines += [
        "",
        "## Licence",
        "",
        f"- Local editing: `git clone {clone_url}`, edit the `.md` pages and push to the default branch `master`.",
        "- Licence: site content is handled under an all-rights-reserved policy: without prior written permission it may not be reproduced, adapted, compiled, translated, uploaded online, made into derivative teaching materials or used commercially; lecturing, projection and photocopying for teaching purposes within the classroom are permitted, while publication, online disclosure, commercial training or secondary adaptation require prior written consent.",
        f"- © {year} {args.copyright}. All Rights Reserved.",
        "",
    ]

    (pages_dir / "Home.md").write_text("\n".join(zh_lines + en_lines).rstrip() + "\n", encoding="utf-8")
    info("已生成 Home.md（中英双段）")

    if args.footer:
        footer = [
            f"© {year} {args.copyright} · 保留所有权利（All Rights Reserved）",
            "",
            f"[Home](Home) · 本页由 [gh-wiki-maker](https://github.com/{args.org}/{args.repo}) 维护",
        ]
        (pages_dir / "_Footer.md").write_text("\n".join(footer) + "\n", encoding="utf-8")
        info("已生成 _Footer.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
