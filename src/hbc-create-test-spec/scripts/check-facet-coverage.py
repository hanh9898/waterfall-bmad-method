#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Automated facet-aware coverage metric for D-27 (M-1).

The plain "≥1 TC per REQ" metric reports 100% even when a multi-facet REQ has a
whole facet untested (the seam). This script counts coverage PER FACET.

Conventions (both optional — absent = no facet requirements, backward compatible):
  - Required facets per REQ: a `Facets` column in the D-02 functional requirements
    table (--d02) AND/OR in the D-27 Coverage Matrix table — the two are UNIONED,
    so neither source shadows the other (D1).
  - Covered facets: each D-27 test-case detail block carries
    `**REQ ID:** REQ-xxx` and `**Facets:** <comma-list>`. A TC may name several
    REQ ids; its facets count for each (D3).

For every REQ that DECLARES required facets, reports the facets no TC covers.
Returns the shared honest verdict. Exit: 0 all facets covered, 1 gaps, 2 arg/io error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        find_section,
        iter_tc_blocks,
        section_body,
        tc_field,
        verdict,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# Namespace-aware (v2): matches REQ-<FEAT>-NNN / REQ-SHARED-NNN + legacy REQ-NNN.
REQ_ID_RE = re.compile(r"REQ-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _strip_comments(s: str) -> str:
    """Remove HTML comments so a `<!-- reviewer note -->` can't leak into a parsed
    header, facet token, or REQ id. Shared by both the required and covered sides."""
    return _COMMENT_RE.sub("", s)


def _split_facets(s: str) -> set[str]:
    # Split on comma/semicolon/slash AND pipe — the D-27 template once shipped a
    # pipe-separated placeholder, so accepting '|' avoids one garbage token (P2).
    return {f.strip().lower() for f in re.split(r"[,;/|]", s) if f.strip()}


# Unfilled-placeholder facet markers. A TC (or matrix row) left as "TODO" must
# fail LOUDLY — otherwise a "TODO" on BOTH the required and covered side cancels
# out and the REQ reports full facet coverage. "n/a" is intentionally NOT here
# (it can be a deliberate "no facets apply" marker).
_PLACEHOLDER_FACETS = {"todo", "tbd", "tba", "xxx", "???", "..."}


def _is_placeholder_facets(raw: str) -> bool:
    """True when a Facets value is purely an unfilled placeholder, not real tokens."""
    toks = _split_facets(raw)
    return bool(toks) and toks <= _PLACEHOLDER_FACETS


def table_with_header(content: str, *labels: str) -> tuple[list[str], list[list[str]]]:
    """First markdown table under a section → (header cells, data rows).

    Unlike lib.parse_table this keeps the header so callers can locate columns by
    name. Returns ([], []) if no section/table.
    """
    m = find_section(content, *labels)
    if not m:
        return [], []
    # Strip HTML comments before parsing so a `<!-- reviewer note -->` inside a
    # matrix cell cannot leak into a header name or a facet token (P2, required side).
    body = _strip_comments(section_body(content, m))
    header: list[str] = []
    rows: list[list[str]] = []
    seen_sep = False
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if header or rows:
                break
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            seen_sep = True
            continue
        if not seen_sep and not header:
            header = cells
            continue
        if seen_sep:
            rows.append(cells)
    return header, rows


def _col_score(hl: str, needle: str) -> int:
    """How well a (lowercased) header cell matches a needle. Higher = stronger.

    4 exact · 3 prefix-as-token (``"req id"`` for ``"req"``, but NOT
    ``"requirement"``) · 2 word-boundary anywhere (``"notes about req."``) ·
    1 plain substring (``"facets"`` for ``"facet"``) · 0 no match.
    """
    if hl == needle:
        return 4
    if hl.startswith(needle) and (len(hl) == len(needle) or not hl[len(needle)].isalpha()):
        return 3
    if re.search(rf"\b{re.escape(needle)}\b", hl):
        return 2
    if needle in hl:
        return 1
    return 0


def _col_index(header: list[str], *needles: str, exclude: int | None = None) -> int | None:
    """Index of the column header that BEST matches any needle.

    Scores every cell and picks the global maximum (ties → first), so a noisy
    column like ``"Notes about req."`` cannot pre-empt the real ``"REQ ID"``
    column the way a first-match scan would (P4). ``exclude`` skips a column
    already claimed by another role, so the same index can't satisfy two needles
    (e.g. a single ``"REQ Facets"`` header).
    """
    best_i, best_score = None, 0
    for i, h in enumerate(header):
        if i == exclude:
            continue
        hl = h.lower()
        score = max((_col_score(hl, n) for n in needles), default=0)
        if score > best_score:
            best_i, best_score = i, score
    return best_i


def _req_col(header: list[str], rows: list[list[str]], exclude: int | None) -> int | None:
    """Resolve the REQ-id column. Like ``_col_index(header, "req")`` but, when the
    top score is a weak/tied match, breaks the tie by DATA: prefer the candidate
    column whose cells actually contain ``REQ-xxx`` ids — so a noisy ``"Acceptance
    Requirement"`` column can't silently win over the real id column at score 1.
    """
    scored = [
        (i, _col_score(h.lower(), "req"))
        for i, h in enumerate(header)
        if i != exclude
    ]
    top = max((s for _, s in scored), default=0)
    if top == 0:
        return None
    cands = [i for i, s in scored if s == top]
    if len(cands) == 1:
        return cands[0]
    # Tie-break on TOTAL REQ-id hits (not rows containing one), so a single-row tie
    # still prefers the column with more actual REQ ids (#8).
    cands.sort(key=lambda i: (-sum(len(REQ_ID_RE.findall(r[i])) for r in rows if i < len(r)), i))
    return cands[0]


def required_facets(d27_text: str, d02_text: str | None) -> dict[str, set[str]]:
    """REQ → required facets, UNIONED across a `Facets` column in the D-02
    functional table AND the D-27 Coverage Matrix (D1).

    Both sources contribute — declaring facets for one REQ in D-02 no longer
    shadows the rest of the D-27 matrix. A row's REQ cell may name more than one
    REQ id; each gets the row's facets (D3).
    """
    sources = []
    if d02_text:
        sources.append(table_with_header(d02_text, "Functional Requirements", "Yêu cầu chức năng"))
    sources.append(table_with_header(d27_text, "Coverage Matrix", "Ma trận bao phủ"))
    req_facets: dict[str, set[str]] = {}
    for header, rows in sources:
        if not header:
            continue
        # Resolve the (unambiguous) facet column first, then the req column
        # excluding it — distinct indices, with a data-aware tie-break for req.
        ci_fac = _col_index(header, "facet")
        ci_req = _req_col(header, rows, exclude=ci_fac)
        if ci_req is None or ci_fac is None:
            continue
        for r in rows:
            if ci_req >= len(r) or ci_fac >= len(r):
                continue
            facets = _split_facets(r[ci_fac])
            if not facets:
                continue
            for req in REQ_ID_RE.findall(r[ci_req]):
                req_facets.setdefault(req, set()).update(facets)
    return req_facets


def covered_facets(d27_text: str) -> dict[str, set[str]]:
    """REQ → facets covered, from each TC detail block's REQ ID + Facets tags.

    A TC block may name multiple REQ ids; the block's facets are credited to each
    (D3). The shared TC helpers handle fenced code, `#### TC-` headings, HTML
    comments, and values wrapped onto the next line.
    """
    covered: dict[str, set[str]] = {}
    for block in iter_tc_blocks(d27_text):
        req_field = tc_field(block, "REQ ID")
        fac_field = tc_field(block, "Facets")
        if req_field and fac_field:
            facets = _split_facets(fac_field)
            for req in REQ_ID_RE.findall(req_field):
                covered.setdefault(req, set()).update(facets)
    return covered


def malformed_tc_count(d27_text: str) -> int:
    """TC blocks declaring exactly ONE of REQ ID / Facets — surfaced so a half-
    tagged TC (its facets or its binding silently dropped) is visible, not lost (#6)."""
    n = 0
    for block in iter_tc_blocks(d27_text):
        if bool(tc_field(block, "REQ ID")) != bool(tc_field(block, "Facets")):
            n += 1
    return n


def placeholder_facets(d27_text: str, d02_text: str | None = None) -> list[dict]:
    """REQ/TC entries whose Facets value is an unfilled placeholder (TODO/TBD/…).

    These must fail loudly: a "TODO" required facet and a "TODO" covered facet
    would otherwise cancel and report full coverage (the template warns that a TC
    left as "TODO" must fail the M-1 check).
    """
    found: list[dict] = []
    for block in iter_tc_blocks(d27_text):
        fac = tc_field(block, "Facets")
        if fac and _is_placeholder_facets(fac):
            req = (tc_field(block, "REQ ID") or "?").strip()
            found.append({"source": "TC Facets", "req": req, "value": fac.strip()})

    sources = []
    if d02_text:
        sources.append(table_with_header(d02_text, "Functional Requirements", "Yêu cầu chức năng"))
    sources.append(table_with_header(d27_text, "Coverage Matrix", "Ma trận bao phủ"))
    for header, rows in sources:
        if not header:
            continue
        ci_fac = _col_index(header, "facet")
        ci_req = _req_col(header, rows, exclude=ci_fac)
        if ci_fac is None:
            continue
        for r in rows:
            if ci_fac < len(r) and _is_placeholder_facets(r[ci_fac]):
                req = (r[ci_req].strip() if (ci_req is not None and ci_req < len(r)) else "?")
                found.append({"source": "Coverage Matrix", "req": req, "value": r[ci_fac].strip()})
    return found


def check(d27_text: str, d02_text: str | None = None) -> dict:
    required = required_facets(d27_text, d02_text)
    covered = covered_facets(d27_text)

    uncovered: dict[str, list[str]] = {}
    for req, facets in required.items():
        missing = sorted(facets - covered.get(req, set()))
        if missing:
            uncovered[req] = missing

    placeholders = placeholder_facets(d27_text, d02_text)
    structure_ok = not uncovered and not placeholders
    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=["per-facet TC coverage for REQs that declare required facets"],
        not_checked=["whether the declared facet set is COMPLETE (LLM review per rubric)"],
    )
    v.update({
        "reqs_with_declared_facets": len(required),
        "uncovered_facets": uncovered,
        "facet_covered": structure_ok,
    })
    if placeholders:
        # Loud failure (not a silent cancel): facets left as TODO/TBD/…
        v["placeholder_facets"] = placeholders
    # Transparency (#2): a green with zero declared facets measured NOTHING. We do
    # not flip the verdict — single-facet REQs legitimately declare none — but the
    # P2-08 reviewer must see that the metric was vacuous and confirm completeness.
    if not required and not placeholders:
        v["note"] = ("No REQ declares required facets; facet_covered is vacuous "
                     "(nothing measured). Confirm via LLM review whether facets should be declared.")
    malformed = malformed_tc_count(d27_text)
    if malformed:
        v["malformed_tc"] = malformed  # transparency (#6): half-tagged TC blocks
    return v


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated facet-aware coverage (M-1).")
    parser.add_argument("--d27", required=True, help="Path to D-27 test spec")
    parser.add_argument("--d02", help="Path to D-02 (additional source of required facets, UNIONED with D-27)")
    parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    try:
        d27_text = Path(args.d27).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(json.dumps({"error": f"D-27 not readable: {args.d27}", "facet_covered": False}, ensure_ascii=False))
        return 2
    d02_text = None
    if args.d02:
        try:
            d02_text = Path(args.d02).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Warn rather than silently dropping the preferred facet source (P3).
            print(f"WARNING: --d02 provided but not readable, ignoring: {args.d02}", file=sys.stderr)
            d02_text = None

    result = check(d27_text, d02_text)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "facet_covered": False}, ensure_ascii=False))
            return 2
        print(f"Facet coverage report written to {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0 if result["facet_covered"] else 1


if __name__ == "__main__":
    sys.exit(main())
