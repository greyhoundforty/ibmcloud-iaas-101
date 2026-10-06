#!/usr/bin/env python3
"""
scan_pills.py - add new tech-page pills to site/pill-docs.yaml.

Reads the pills in site/iaas-101-tech-focus.html. One YAML row per label.
A label that is not in the sheet yet is inserted, in label order, with
docs: "" and an appears list (pillar · card). An existing row keeps its docs
URL. New places that label shows up are appended to appears. Rows already in
the YAML are not deleted.

Usage:
    python3 scripts/scan_pills.py
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_search_page import load_rows  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "iaas-101-tech-focus.html"
SPEC = ROOT / "site" / "pill-docs.yaml"

# Eval the PILLARS array. process.argv[1] is the HTML path (node -e keeps it).
EXTRACT = r"""
const fs = require("fs");
const html = fs.readFileSync(process.argv[1], "utf8");
const start = html.indexOf("const PILLARS = ");
const end = html.indexOf("\n];", start);
if (start < 0 || end < 0) {
  console.error("could not find const PILLARS");
  process.exit(1);
}
const PILLARS = new Function(html.slice(start, end + 3) + "\nreturn PILLARS;")();
const found = [];
for (const pillar of PILLARS) {
  for (const line of pillar.lines || []) {
    for (const item of line.items || []) {
      for (const pill of item.pills || []) {
        found.push({ label: pill.label, where: pillar.title + " · " + item.name });
      }
    }
  }
}
process.stdout.write(JSON.stringify(found));
"""


def page_pills(path: Path) -> dict[str, list[str]]:
    """Label -> unique pillar · card list, in the order they appear on the page."""
    result = subprocess.run(
        ["node", "-e", EXTRACT, str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or "node failed while reading pills")
    grouped: dict[str, list[str]] = {}
    for pill in json.loads(result.stdout):
        label = pill["label"]
        if not label:
            print("skipped a pill with an empty label")
            continue
        places = grouped.setdefault(label, [])
        if pill["where"] not in places:
            places.append(pill["where"])
    return grouped


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(header: str, rows: list[dict]) -> str:
    lines = [header.rstrip(), "pills:"]
    for row in rows:
        lines.append(f"  - label: {yaml_quote(row['label'])}")
        lines.append(f"    docs: {yaml_quote(row['docs'])}")
        lines.append("    appears:")
        for where in row["appears"]:
            lines.append(f"      - {yaml_quote(where)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def insert_index(rows: list[dict], label: str) -> int:
    key = label.casefold()
    for i, row in enumerate(rows):
        if key < row["label"].casefold():
            return i
    return len(rows)


def main() -> int:
    if not PAGE.is_file():
        print(f"missing {PAGE}")
        return 1
    text = SPEC.read_text(encoding="utf-8") if SPEC.is_file() else ""
    if "\npills:" in text:
        header, _, _ = text.partition("\npills:")
    elif text.startswith("pills:"):
        header = ""
    else:
        header = (
            "# Pill docs for site/iaas-101-tech-focus.html.\n"
            "# One row per label. The docs URL is copied onto every pill with that label.\n"
            '# Leave docs as "" or set an https:// URL. appears is pillar · card, for reference only.'
        )
    existing = load_rows(text) if text.strip() else []
    seen = [row["label"] for row in existing]
    if len(set(seen)) != len(seen):
        print("duplicate labels in the yaml; fix those before scanning")
        return 1
    rows = []
    by_label = {}
    for row in existing:
        copied = {"label": row["label"], "docs": row["docs"], "appears": list(row["appears"])}
        rows.append(copied)
        by_label[copied["label"]] = copied

    on_page = page_pills(PAGE)
    added: list[str] = []
    grew: list[str] = []

    for label in sorted(on_page, key=str.casefold):
        places = on_page[label]
        current = by_label.get(label)
        if current is None:
            row = {"label": label, "docs": "", "appears": places}
            rows.insert(insert_index(rows, label), row)
            by_label[label] = row
            added.append(label)
            continue
        fresh = [place for place in places if place not in current["appears"]]
        if fresh:
            current["appears"] = [*current["appears"], *fresh]
            grew.append(label)

    missing = sorted(set(by_label) - set(on_page), key=str.casefold)
    for label in missing:
        print(f"yaml label not on a pill: {label}")
    for label in added:
        print(f"added: {label}")
        for place in on_page[label]:
            print(f"  {place}")
    for label in grew:
        print(f"appears: {label}")
        for place in on_page[label]:
            if place not in existing_appears(existing, label):
                print(f"  + {place}")

    if not added and not grew:
        print(f"no new pills ({len(on_page)} labels already in {SPEC.name})")
        return 0

    SPEC.write_text(render(header, rows), encoding="utf-8")
    try:
        shown = SPEC.relative_to(ROOT)
    except ValueError:
        shown = SPEC
    print(f"wrote {shown} ({len(added)} added, {len(grew)} appears updated)")
    return 0


def existing_appears(rows: list[dict], label: str) -> list[str]:
    for row in rows:
        if row["label"] == label:
            return row["appears"]
    return []


if __name__ == "__main__":
    sys.exit(main())
