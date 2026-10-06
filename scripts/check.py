#!/usr/bin/env python3
"""
check.py - quick sanity checks for an explorer page before you publish it.

What it checks:
  1. The page's inline <script> parses (uses `node --check`).
  2. Every `icon: "i-something"` used in the content has a matching
     <symbol id="i-something"> in the page's icon sprite.
  3. No pill or item is missing a label/name (catches half-finished edits).
  4. Every `docs` value is either "" or an https URL.

Usage:
    python3 scripts/check.py site/iaas-101-tech-focus.html
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    # --- 1. Read the page we were asked to check ---------------------------
    if len(sys.argv) != 2:
        print("usage: check.py <page.html>")
        return 2
    page = Path(sys.argv[1])
    html = page.read_text(encoding="utf-8")
    problems = []  # we collect every problem, then report them all at once

    # --- 2. Pull out the inline script and let Node parse it ---------------
    # The page has exactly one <script>...</script> block with all the logic.
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not scripts:
        problems.append("no inline <script> found")
    else:
        # node --check needs a file, so write the script to a temp file
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tmp:
            tmp.write(scripts[0])
        result = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        Path(tmp.name).unlink()  # clean up the temp file
        if result.returncode != 0:
            problems.append("script does not parse:\n" + result.stderr.strip())

    # --- 3. Every icon referenced must exist in the sprite ------------------
    used = set(re.findall(r'icon: "(i-[a-z0-9-]+)"', html))       # icons the content asks for
    defined = set(re.findall(r'<symbol id="(i-[a-z0-9-]+)"', html))  # icons the sprite provides
    for missing in sorted(used - defined):
        problems.append(f'icon "{missing}" is used but has no <symbol> (run: mise run icon -- <carbon-name> {missing})')

    # --- 4. Pills need a label, items need a name ---------------------------
    # A pill looks like { label: "...", icon: "..." }. An empty label is a bug.
    if re.search(r'label:\s*""', html):
        problems.append("a pill has an empty label")
    if re.search(r'name:\s*""', html):
        problems.append("an item has an empty name")

    # --- 5. docs is optional: "" is fine, anything else must be https ------
    for url in re.findall(r'docs:\s*"([^"]*)"', html):
        if url and not url.startswith("https://"):
            problems.append(f'docs value must be an https URL or "": {url!r}')

    # --- 6. Report ----------------------------------------------------------
    if problems:
        print(f"✗ {page}:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"✓ {page}: script parses, {len(used)} icons used / {len(defined)} defined, no empty labels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
