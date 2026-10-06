#!/usr/bin/env python3
"""
ingest_docs.py - copy site/pill-docs.yaml onto tech-page pills.

One YAML row per label. That row's docs value is written onto every pill with
the same label in site/iaas-101-tech-focus.html. The appears list is only
there so a person can see where the URL is copied; this script ignores it.

An empty docs value stays "". A non-empty value must start with https://.
If any value does not, the script exits non-zero and does not change the page.

Labels in the YAML that match no pill, and pill labels with no YAML row, are
printed. They do not block a valid write.

Usage:
    python3 scripts/ingest_docs.py
"""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "site" / "iaas-101-tech-focus.html"
SPEC = ROOT / "site" / "pill-docs.yaml"

# One pill object is a single {...} with a label. Titles in this file have no braces.
PILL_RE = re.compile(
    r"\{[^{}]*?\blabel:\s*\"((?:\\.|[^\"\\])*)\"[^{}]*?\}",
    re.S,
)
DOCS_RE = re.compile(r"docs:\s*\"((?:\\.|[^\"\\])*)\"")


class DocsError(Exception):
    """A problem that must stop the run before the page is written."""


def js_unescape(value: str) -> str:
    """Decode the escapes used in the page's double-quoted JS strings."""
    out = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            out.append(value[i + 1])
            i += 2
            continue
        out.append(value[i])
        i += 1
    return "".join(out)


def js_escape(value: str) -> str:
    """Escape a docs URL for a double-quoted JS string."""
    return value.replace("\\", "\\\\").replace('"', r"\"")


def yaml_unescape(value: str) -> str:
    """Decode a double-quoted YAML scalar the way this file writes them."""
    out = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
            i += 2
            continue
        out.append(value[i])
        i += 1
    return "".join(out)


def parse_scalar(raw: str) -> str:
    """Read a docs or label scalar. Quoted or a plain https URL."""
    text = raw.strip()
    if not text:
        return ""
    if text[0] == '"':
        end = 1
        while end < len(text):
            if text[end] == "\\":
                end += 2
                continue
            if text[end] == '"':
                return yaml_unescape(text[1:end])
            end += 1
        raise DocsError(f"unclosed double quote: {raw!r}")
    if text[0] == "'":
        # YAML single quotes escape a quote by doubling it.
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
        raise DocsError(f"unclosed single quote: {raw!r}")
    # Plain scalar. A trailing " # comment" is a comment; a URL has no space before #.
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    return text


def load_docs(text: str) -> dict[str, str]:
    """Map label -> docs from pill-docs.yaml. Reject duplicate labels."""
    docs: dict[str, str] = {}
    current: dict[str, str] | None = None
    seen_order: list[str] = []

    def finish() -> None:
        nonlocal current
        if current is None:
            return
        label = current.get("label")
        if not label:
            raise DocsError("a pill-docs row is missing label")
        if label in docs:
            raise DocsError(f"duplicate yaml label: {label!r}")
        docs[label] = current.get("docs", "")
        seen_order.append(label)
        current = None

    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "pills:":
            continue
        item = re.match(r"^  - (\w+):\s*(.*)$", line)
        key = re.match(r"^    (\w+):\s*(.*)$", line)
        if item:
            finish()
            current = {}
            name, raw = item.group(1), item.group(2)
            if name == "appears":
                continue
            current[name] = parse_scalar(raw)
            continue
        if key and current is not None:
            name, raw = key.group(1), key.group(2)
            if name == "appears":
                continue
            current[name] = parse_scalar(raw)
            continue
        if line.startswith("      "):
            continue  # appears entries, ignored
        raise DocsError(f"could not read {SPEC.name}:{lineno}: {line}")

    finish()
    if not docs:
        raise DocsError(f"no pill rows in {SPEC.name}")
    return docs


def validate(docs: dict[str, str]) -> None:
    """Non-empty docs must be https. Raise before any write."""
    for label, url in docs.items():
        if url and not url.startswith("https://"):
            raise DocsError(f"docs for {label!r} must be an https URL or \"\": {url!r}")


def pill_labels(html: str) -> list[str]:
    """Every pill label, in page order, one entry per occurrence."""
    return [js_unescape(match.group(1)) for match in PILL_RE.finditer(html)]


def apply_docs(html: str, docs: dict[str, str]) -> tuple[str, int]:
    """Set docs on every pill whose label is in docs. Return html and count."""
    updated = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal updated
        label = js_unescape(match.group(1))
        if label not in docs:
            return match.group(0)
        url = docs[label]
        escaped = js_escape(url)
        obj = match.group(0)
        if DOCS_RE.search(obj):
            new = DOCS_RE.sub(f'docs: "{escaped}"', obj, count=1)
        else:
            new = obj[:-1].rstrip()
            if not new.endswith(","):
                new += ","
            new += f' docs: "{escaped}" }}'
        if new != obj:
            updated += 1
        return new

    return PILL_RE.sub(repl, html), updated


def report(docs: dict[str, str], html: str) -> list[str]:
    """Labels that do not line up. Empty when the sheet matches the page."""
    on_page = set(pill_labels(html))
    lines = []
    for label in sorted(set(docs) - on_page, key=str.casefold):
        lines.append(f"yaml label not on a pill: {label}")
    for label in sorted(on_page - set(docs), key=str.casefold):
        lines.append(f"pill with no yaml row: {label}")
    return lines


def main() -> int:
    if PAGE.name != "iaas-101-tech-focus.html":
        print("refusing to edit a page other than the tech-focus file")
        return 1
    try:
        docs = load_docs(SPEC.read_text(encoding="utf-8"))
        validate(docs)
        html = PAGE.read_text(encoding="utf-8")
        updated_html, updated = apply_docs(html, docs)
    except DocsError as exc:
        print(exc)
        return 1
    except OSError as exc:
        print(exc)
        return 1

    for line in report(docs, html):
        print(line)
    if updated_html != html:
        PAGE.write_text(updated_html, encoding="utf-8")
        print(f"updated {updated} pill(s) in {PAGE.relative_to(ROOT)}")
    else:
        print(f"html unchanged ({len(docs)} labels, {len(pill_labels(html))} pills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
