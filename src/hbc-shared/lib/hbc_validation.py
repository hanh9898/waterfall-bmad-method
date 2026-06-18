#!/usr/bin/env python3
"""Shared validation primitives for HBC validators (Wave 0 / C-1).

Single source of truth for table parsing, column extraction, language-aware
section detection (English canonical + configured document language — NO
hardcoded Japanese), and the honest verdict object (S-3).

Validators import this via a sys.path bootstrap computed relative to skill-root:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
    from hbc_validation import parse_table, extract_column, find_section, verdict

Design boundary: this module only describes STRUCTURE. Semantic / completeness
judgement is out of scope here — that is the LLM review layer (Wave 2). The
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


# --- Test-case (TC) block parsing — shared by D-27 readiness + facet engines ---
_FENCE_LINE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
_TC_HEADING_RE = re.compile(r"^#{3,6}[ \t]+TC-", re.MULTILINE | re.IGNORECASE)


def strip_code_fences(text: str) -> str:
    """Remove fenced code blocks so markup inside them (e.g. an example ``### TC-``
    heading) is never read as real document structure.

    A line-state scan (not a regex) so it pairs fences correctly regardless of
    info-string, indentation, or fence char (``` or ~~~). An UNCLOSED fence drops
    to end-of-input — fail-safe: fenced/garbled example content never leaks out to
    be miscounted as a real TC.
    """
    out: list[str] = []
    fence: str | None = None  # the opening fence char (` or ~) while inside a block
    for line in text.splitlines(keepends=True):
        m = _FENCE_LINE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)[0]
            else:
                out.append(line)
        elif m and m.group(1)[0] == fence:
            fence = None  # matching close — drop the closing line too
    return "".join(out)


def iter_tc_blocks(text: str) -> list[str]:
    """Each test-case detail block body, split on a ``### … TC-`` heading at levels
    3–6 (so ``#### TC-`` is not silently missed; case-insensitive), with fenced
    code stripped first. Returns the bodies AFTER each TC heading; text before the
    first heading is dropped.
    """
    return _TC_HEADING_RE.split(strip_code_fences(text))[1:]


def tc_ids(text: str) -> set[str]:
    """TC ids DECLARED as ``### … TC-NNN`` headings (levels 3-6, fence-stripped) —
    the authoritative test-case set of a D-27, mirroring iter_tc_blocks detection.
    Use to reconcile specified TCs against what a downstream report actually ran."""
    return {
        f"TC-{m}"
        for m in re.findall(r"^#{3,6}[ \t]+TC-(\d{3,})", strip_code_fences(text),
                            re.MULTILINE | re.IGNORECASE)
    }


def tc_field(block: str, label: str) -> str | None:
    """Value of a ``**Label:**`` field inside a TC block, captured up to the next
    ``**…:**`` field, blank line, or end — so a value wrapped onto the next line is
    still read. ``None`` if the field is absent, ``""`` if present but empty.

    The gap after the label is matched with ``[ \\t]*`` (NOT ``\\s*``): a bare
    ``**Label:**`` at end of line must NOT consume the newline and swallow the next
    field's line (which would, e.g., let an empty REQ ID field absorb a later
    ``**Trace:** REQ-555`` and falsely bind it). HTML comments stripped first.
    """
    cleaned = re.sub(r"<!--.*?-->", "", block, flags=re.DOTALL)
    m = re.search(
        rf"\*\*{re.escape(label)}:\*\*[ \t]*(.*?)(?=\n\s*\*\*|\n\s*\n|\Z)",
        cleaned, re.DOTALL,
    )
    return m.group(1).strip() if m else None


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
    in_data = False  # True after a separator; reset by any non-pipe (prose/blank) line
    for line in section_body(content, m).splitlines():
        s = line.strip()
        if not s.startswith("|"):
            # A prose/blank line ends the current table block. The next pipe line
            # starts a fresh block, so its header row is skipped again — this lets
            # a section with MULTIPLE sub-tables (e.g. `### 4.1`/`### 4.2`, each with
            # its own table) contribute ALL their data rows without leaking any
            # sub-table's header row in as data.
            in_data = False
            continue
        # strip one bounding pipe each side so rows with or without a trailing
        # pipe both split correctly (GFM allows omitting the trailing pipe).
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            in_data = True  # separator → subsequent rows in this block are data
            continue
        if not in_data:
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
