#!/usr/bin/env python3
"""
build_search_page.py - write a clickable search page for every pill label.

Reads site/pill-docs.yaml and writes site/pill-docs-search.html. Each label
gets one link:

    https://cloud.ibm.com/docs/search?q=<label>

The appears list is shown so you can see where that label is used. A docs
value already in the YAML is shown as pinned; this script does not change
the YAML or the tech page.

Usage:
    python3 scripts/build_search_page.py
"""

import html
import re
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "site" / "pill-docs.yaml"
PAGE = ROOT / "site" / "pill-docs-search.html"
SEARCH = "https://cloud.ibm.com/docs/search?q="


def parse_scalar(raw: str) -> str:
    """Read a double-quoted, single-quoted, or plain YAML scalar."""
    text = raw.strip()
    if not text:
        return ""
    if text[0] == '"':
        out = []
        i = 1
        while i < len(text):
            if text[i] == "\\":
                out.append(text[i + 1] if i + 1 < len(text) else "")
                i += 2
                continue
            if text[i] == '"':
                return "".join(out)
            out.append(text[i])
            i += 1
        raise SystemExit(f"unclosed double quote: {raw!r}")
    if text[0] == "'":
        body = []
        i = 1
        while i < len(text):
            if text[i] == "'":
                if i + 1 < len(text) and text[i + 1] == "'":
                    body.append("'")
                    i += 2
                    continue
                return "".join(body)
            body.append(text[i])
            i += 1
        raise SystemExit(f"unclosed single quote: {raw!r}")
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    return text


def load_rows(text: str) -> list[dict]:
    """One row per YAML pill: label, docs, appears. File order is label order."""
    rows: list[dict] = []
    current: dict | None = None

    def finish() -> None:
        nonlocal current
        if current is None:
            return
        if not current.get("label"):
            raise SystemExit("a pill-docs row is missing label")
        rows.append(current)
        current = None

    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "pills:":
            continue
        item = re.match(r"^  - (\w+):\s*(.*)$", line)
        key = re.match(r"^    (\w+):\s*(.*)$", line)
        appear = re.match(r"^      - (.*)$", line)
        if item:
            finish()
            current = {"label": "", "docs": "", "appears": []}
            name, raw = item.group(1), item.group(2)
            if name == "appears":
                continue
            current[name] = parse_scalar(raw)
            continue
        if current is None:
            raise SystemExit(f"could not read {SPEC.name}:{lineno}: {line}")
        if key:
            name, raw = key.group(1), key.group(2)
            if name == "appears":
                continue
            current[name] = parse_scalar(raw)
            continue
        if appear:
            current["appears"].append(parse_scalar(appear.group(1)))
            continue
        raise SystemExit(f"could not read {SPEC.name}:{lineno}: {line}")
    finish()
    if not rows:
        raise SystemExit(f"no pill rows in {SPEC.name}")
    return rows


def search_url(label: str) -> str:
    return SEARCH + quote_plus(label)


def render(rows: list[dict]) -> str:
    pinned = sum(1 for row in rows if row["docs"])
    items = []
    for row in rows:
        label = row["label"]
        url = search_url(label)
        where = html.escape("; ".join(row["appears"]))
        docs = row["docs"]
        pinned_html = ""
        if docs:
            pinned_html = (
                f'<a class="pinned" href="{html.escape(docs, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">Pinned docs</a>'
            )
        items.append(
            f'<li data-pinned="{"yes" if docs else "no"}" '
            f'data-text="{html.escape(label + " " + " ".join(row["appears"]), quote=True)}">'
            f'<a class="search" href="{html.escape(url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'
            f'<p class="where">{where}</p>'
            f"{pinned_html}"
            f"</li>"
        )
    body = "\n".join(items)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pill docs search</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
:root {{
  color-scheme: light;
  --bg: #ffffff;
  --layer: #f4f4f4;
  --line: #c6c6c6;
  --text: #161616;
  --text-2: #525252;
  --link: #0f62fe;
  --pinned: #0e6027;
  --font: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 16px;
  line-height: 1.45;
}}
main {{
  max-width: 880px;
  margin: 0 auto;
  padding: 32px 16px 64px;
}}
.eyebrow {{
  margin: 0;
  color: var(--link);
  font-size: 0.75rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}}
h1 {{ font-size: 1.75rem; font-weight: 600; margin: 8px 0; }}
.lead {{ margin: 0 0 20px; color: var(--text-2); max-width: 62ch; }}
.tools {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  align-items: center;
  position: sticky;
  top: 0;
  background: var(--bg);
  padding: 8px 0 12px;
  border-bottom: 1px solid var(--line);
}}
input[type="search"] {{
  flex: 1 1 220px;
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid var(--line);
  background: var(--layer);
  color: var(--text);
  font: inherit;
}}
.tools label {{ display: flex; gap: 8px; align-items: center; }}
#count {{ margin: 0; color: var(--text-2); font-size: 0.875rem; }}
ol {{ list-style: none; margin: 0; padding: 0; }}
li {{
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 2fr) auto;
  gap: 8px 16px;
  align-items: baseline;
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}}
li[hidden] {{ display: none; }}
.search {{
  color: var(--link);
  font-weight: 600;
  text-decoration: none;
}}
.search:hover {{ text-decoration: underline; }}
.where {{ margin: 0; color: var(--text-2); font-size: 0.875rem; }}
.pinned {{
  color: var(--pinned);
  font-size: 0.875rem;
  font-weight: 600;
  white-space: nowrap;
}}
@media (max-width: 700px) {{
  li {{ grid-template-columns: 1fr; gap: 4px; }}
  .search {{ min-height: 44px; display: inline-flex; align-items: center; }}
}}
</style>
</head>
<body>
<main>
  <p class="eyebrow">IBM Cloud docs</p>
  <h1>Search links for each pill</h1>
  <p class="lead">{len(rows)} labels, one search each. The query is the label. Open a result, copy the specific docs URL into <code>site/pill-docs.yaml</code>, then run <code>mise run ingest-docs</code>. {pinned} already have a docs value.</p>
  <div class="tools">
    <input id="filter" type="search" placeholder="Filter by label or pillar" autocomplete="off">
    <label><input id="hide-pinned" type="checkbox" checked> Hide pinned</label>
    <p id="count"></p>
  </div>
  <ol id="rows">
{body}
  </ol>
</main>
<script>
const filter = document.getElementById("filter");
const hidePinned = document.getElementById("hide-pinned");
const count = document.getElementById("count");
const rows = [...document.querySelectorAll("#rows li")];
function apply() {{
  const q = filter.value.trim().toLowerCase();
  let shown = 0;
  for (const row of rows) {{
    const pinned = row.dataset.pinned === "yes";
    const match = !q || row.dataset.text.toLowerCase().includes(q);
    const hide = !match || (hidePinned.checked && pinned);
    row.hidden = hide;
    if (!hide) shown += 1;
  }}
  count.textContent = shown + " shown";
}}
filter.addEventListener("input", apply);
hidePinned.addEventListener("change", apply);
apply();
</script>
</body>
</html>
"""


def main() -> None:
    rows = load_rows(SPEC.read_text(encoding="utf-8"))
    PAGE.write_text(render(rows), encoding="utf-8")
    pinned = sum(1 for row in rows if row["docs"])
    print(f"wrote {PAGE.relative_to(ROOT)} ({len(rows)} labels, {pinned} already pinned)")


if __name__ == "__main__":
    main()
