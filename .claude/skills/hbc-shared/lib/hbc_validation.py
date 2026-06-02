#!/usr/bin/env python3
"""Shared validation primitives for HBC validators (Đợt 0 / C-1).

Single source of truth for table parsing, column extraction, language-aware
section detection (English canonical + configured document language — NO
hardcoded Japanese), and the honest verdict object (S-3).

Validators import this via a sys.path bootstrap computed relative to skill-root:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
    from hbc_validation import parse_table, extract_column, find_section, verdict

Design boundary: this module only describes STRUCTURE. Semantic / "đủ-nghĩa"
judgement is out of scope here — that is the LLM review layer (Đợt 2). The
`verdict` helper makes that boundary explicit in the output shape.
"""
from __future__ import annotations

import re

# Semantic-review states for the honest verdict (S-3).
SEMANTIC_NA = "n/a"          # structural-only validator, no semantic gate here
SEMANTIC_PENDING = "pending"  # semantic review owed but not yet done → not passed
SEMANTIC_PASSED = "passed"    # LLM/human semantic review completed


def find_section(content: str, *labels: str) -> re.Match | None:
    """Return the first level-1/level-2 markdown heading matching ANY of ``labels``.

    Labels are tried in order; matching is case-insensitive substring within a
    top-level (``#`` or ``##``) heading line — deeper subsections (``###`` …) are
    intentionally NOT matched, so a label that also appears in a subsection title
    (e.g. "Phạm vi" inside "### 1.1 Phạm vi và mục tiêu") does not shadow the real
    section. Pass the English canonical label plus the configured-language label,
    e.g. ``find_section(text, "Scope", "Phạm vi")``. No language is hardcoded.
    Empty/None labels are skipped. Returns ``None`` if no label matches.
    """
    for label in labels:
        if not label:
            continue
        m = re.compile(
            rf"^#{{1,2}}\s.*{re.escape(label)}.*$", re.IGNORECASE | re.MULTILINE
        ).search(content)
        if m:
            return m
    return None


def _heading_level(heading_line: str) -> int:
    """Number of leading '#' characters in a heading line."""
    stripped = heading_line.lstrip()
    return len(stripped) - len(stripped.lstrip("#"))


def section_body(content: str, match: re.Match) -> str:
    """Return the text from the end of heading ``match`` up to the next heading of
    equal-or-higher level (or end of document).

    Cutting at equal-or-higher level (not a fixed ``##``) means a section's own
    deeper subsections stay inside its body, while the next sibling/parent heading
    correctly terminates it.
    """
    level = _heading_level(match.group(0)) or 2
    start = match.end()
    nxt = re.search(rf"\n#{{1,{level}}}\s", content[start:])
    return content[start:start + nxt.start()] if nxt else content[start:]


def parse_table(content: str, *labels: str) -> list[list[str]]:
    """Locate the section identified by ``labels`` and return its markdown
    table's DATA rows (header and separator excluded) as lists of cell strings.

    Returns ``[]`` when the section or a table is absent. Only rows after the
    ``|---|`` separator are treated as data — this is what lets callers trust
    table cells instead of scanning prose (S-4).
    """
    m = find_section(content, *labels)
    if not m:
        return []
    rows: list[list[str]] = []
    seen_separator = False
    started = False
    for line in section_body(content, m).splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if started:
                break  # first table block ended — don't bleed into a later table
            continue
        started = True
        # strip one bounding pipe each side so rows with or without a trailing
        # pipe both split correctly (GFM allows omitting the trailing pipe).
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            seen_separator = True
            continue
        if not seen_separator:
            # header row before the separator
            continue
        rows.append(cells)
    return rows


def extract_column(rows: list[list[str]], index: int) -> list[str]:
    """Return cell values at ``index`` across ``rows``, skipping rows too short."""
    return [r[index] for r in rows if index < len(r)]


def section_has_content(text: str) -> bool:
    """True if ``text`` has real content beyond scaffolding.

    Scaffolding = blank lines, table separators, and standalone table headers
    (a header row immediately followed by a separator, with no data rows) and
    HTML comment lines. Shared by every validator's section non-emptiness check.
    """
    non_blank = [ln.strip() for ln in text.splitlines() if ln.strip()]

    skip: set[int] = set()
    for i, line in enumerate(non_blank):
        if i + 1 < len(non_blank):
            nxt = non_blank[i + 1]
            is_separator = nxt.startswith("|") and set(nxt) <= {"|", "-", " ", ":"}
            is_header = line.startswith("|") and not set(line) <= {"|", "-", " ", ":"}
            if is_header and is_separator:
                skip.add(i)
                skip.add(i + 1)

    for i, line in enumerate(non_blank):
        if i in skip:
            continue
        if set(line) <= {"|", "-", " ", ":"}:
            continue
        if line.startswith("<!--") and line.endswith("-->"):
            continue
        return True

    return False


def check_required_sections(content: str, sections, empty_check: bool = True) -> list[dict]:
    """Standard SECTION_MISSING / SECTION_EMPTY issues for required sections.

    ``sections`` is an iterable of ``(canonical, *acceptable_labels)`` tuples —
    canonical is the English name reported in issues; any label (canonical or a
    configured-language alias) satisfies the presence check. No language is
    hardcoded. This is the shared replacement for each validator's bespoke
    ``check_sections`` (S-1 + C-1).

    ``empty_check`` — when False, only presence is checked (no SECTION_EMPTY),
    matching validators that historically did presence-only.
    """
    issues: list[dict] = []
    for entry in sections:
        canonical = entry[0]
        labels = entry[1:]
        match = find_section(content, canonical, *labels)
        if not match:
            alt = f" / {' / '.join(labels)}" if labels else ""
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{canonical}'{alt} not found",
                "section": canonical,
                "auto_fixable": False,
            })
            continue
        if not empty_check:
            continue
        body = section_body(content, match)
        stripped = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
        if not section_has_content(stripped):
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{canonical}' exists but has no content",
                "section": canonical,
                "auto_fixable": False,
            })
    return issues


def verdict(
    structure_ok: bool,
    *,
    semantic_review: str = SEMANTIC_NA,
    checked: list[str] | None = None,
    not_checked: list[str] | None = None,
) -> dict:
    """Build the honest verdict object (S-3).

    A validator may only assert STRUCTURE. ``passed`` is true only when the
    structure is OK *and* the semantic review is not still ``pending`` — so a
    consumer can never read a green structural check as "document is correct".
    """
    return {
        "structure_ok": bool(structure_ok),
        "semantic_review": semantic_review,
        "checked": list(checked or []),
        "not_checked": list(not_checked or []),
        "passed": bool(structure_ok) and semantic_review != SEMANTIC_PENDING,
    }
