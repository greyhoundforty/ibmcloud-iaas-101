#!/usr/bin/env python3
"""
preview.py - wrap the explorer pages so they render correctly in a local browser.

Why this exists:
  The files in site/ are written for the claude.ai Artifact publisher, which adds
  the <!doctype html><html><head>...<body> skeleton for you at publish time.
  Opened directly in a browser, a file with no doctype renders in "quirks mode"
  and the layout can drift. This script adds the same skeleton and writes the
  results to build/, which `mise run serve` then serves on http://localhost:8000.

Usage:
    python3 scripts/preview.py            # wraps every site/*.html into build/
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (one level above scripts/)
SITE = ROOT / "site"
BUILD = ROOT / "build"

# The skeleton the Artifact publisher adds. viewport-fit=cover matches what the
# live page gets, so phone-width previews behave the same way.
HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>body{margin:0}[hidden]{display:none!important}</style>
"""


def wrap(page_html: str) -> str:
    # Everything up to and including </style> belongs in <head> (title, fonts, CSS);
    # the rest (icon sprite, <main>, <script>) belongs in <body>.
    split_at = page_html.index("</style>") + len("</style>")
    head_part, body_part = page_html[:split_at], page_html[split_at:]
    return f"{HEAD}{head_part}\n</head>\n<body>\n{body_part}\n</body>\n</html>\n"


# Local worksheets, not explorer fragments. They are complete HTML documents.
SKIP = {"pill-docs-search.html"}


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    pages = [src for src in sorted(SITE.glob("*.html")) if src.name not in SKIP]
    for src in pages:
        out = BUILD / src.name
        out.write_text(wrap(src.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
    # A tiny index so http://localhost:8000 lists the pages
    links = "".join(f'<li><a href="{p.name}">{p.name}</a></li>' for p in pages)
    (BUILD / "index.html").write_text(f"<!doctype html><ul>{links}</ul>", encoding="utf-8")


if __name__ == "__main__":
    main()
