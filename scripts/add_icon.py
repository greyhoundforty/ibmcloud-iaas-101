#!/usr/bin/env python3
"""
add_icon.py - copy an official Carbon icon into a page's icon sprite.

The pages don't load icons from the network. Each icon lives once in a hidden
<svg> "sprite" near the top of the page as a <symbol id="i-...">, and pills point
at it with `icon: "i-..."`. This script finds the Carbon SVG, turns it into a
<symbol>, and inserts it just before the i-chevron symbol (the last one).

Usage:
    python3 scripts/add_icon.py <carbon-name> <symbol-id> [page]

    python3 scripts/add_icon.py ibm-cloud--direct-link-2--dedicated i-dl-dedicated
    python3 scripts/add_icon.py --search load-balancer        # list matching names

Carbon names are the file names in @carbon/icons/svg/32 (no .svg), e.g.
"floating-ip", "ibm-cloud--transit-gateway". Browse them at
https://carbondesignsystem.com/elements/icons/library/
"""

import re
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "carbon"             # where the npm package gets unpacked
ICON_DIR = CACHE / "package" / "svg" / "32"     # the 32px icon set
DEFAULT_PAGE = ROOT / "site" / "iaas-101-tech-focus.html"


def ensure_carbon() -> None:
    """Download @carbon/icons once (via `npm pack`) and unpack it into .cache/."""
    if ICON_DIR.exists():
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    print("fetching @carbon/icons (one time)...")
    # npm pack downloads the published tarball without installing anything
    name = subprocess.run(
        ["npm", "pack", "@carbon/icons", "--silent"],
        cwd=CACHE, capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()[-1]
    with tarfile.open(CACHE / name) as tar:
        tar.extractall(CACHE, filter="data")  # "data" filter blocks unsafe paths in the archive


def search(term: str) -> None:
    """Print every Carbon icon name that contains `term`."""
    for svg in sorted(ICON_DIR.glob(f"*{term}*.svg")):
        print(svg.stem)


def add(carbon_name: str, symbol_id: str, page: Path) -> None:
    svg_file = ICON_DIR / f"{carbon_name}.svg"
    if not svg_file.exists():
        sys.exit(f"no Carbon icon named '{carbon_name}' (try --search)")

    html = page.read_text(encoding="utf-8")
    if f'<symbol id="{symbol_id}"' in html:
        sys.exit(f"{symbol_id} already exists in {page.name}; reuse it")

    # Keep only what's inside <svg ...>...</svg>, minus any <title>
    inner = re.search(r"<svg[^>]*>(.*)</svg>", svg_file.read_text(), re.S).group(1)
    inner = re.sub(r"<title>.*?</title>", "", inner)
    symbol = f'  <symbol id="{symbol_id}" viewBox="0 0 32 32">{inner}</symbol>\n'

    # Insert right before the chevron symbol so the sprite stays in one place
    anchor = '  <symbol id="i-chevron"'
    if anchor not in html:
        sys.exit("couldn't find the i-chevron symbol to insert before")
    page.write_text(html.replace(anchor, symbol + anchor, 1), encoding="utf-8")
    print(f'added {symbol_id} ({carbon_name}) to {page.name}; use it with icon: "{symbol_id}"')


def main() -> None:
    args = sys.argv[1:]
    ensure_carbon()
    if len(args) == 2 and args[0] == "--search":
        search(args[1])
    elif len(args) in (2, 3):
        page = Path(args[2]) if len(args) == 3 else DEFAULT_PAGE
        add(args[0], args[1], page)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
