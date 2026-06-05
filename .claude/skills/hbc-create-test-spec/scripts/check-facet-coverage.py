#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Automated facet-aware coverage metric for D-27 (M-1).

The plain "≥1 TC per REQ" metric reports 100% even when a multi-facet REQ has a
whole facet untested (the seam). This script counts coverage PER FACET.

Conventions (both optional — absent = no facet requirements, backward compatible):
  - Required facets per REQ: a `Facets` column in the D-02 functional requirements
    table (preferred, --d02) OR in the D-27 Coverage Matrix table.
  - Covered facets: each D-27 test-case detail block carries
    `**REQ ID:** REQ-xxx` and `**Facets:** <comma-list>`.

For every REQ that DECLARES required facets, reports the facets no TC covers.
Returns the shared honest verdict. Exit: 0 all facets covered, 1 gaps, 2 arg/io error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import SEMANTIC_NA, find_section, section_body, verdict  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

REQ_ID_RE = re.compile(r"REQ-\d{3,}")


def _split_facets(s: str) -> set[str]:
    return {f.strip().lower() for f in re.split(r"[,;/]", s) if f.strip()}


def table_with_header(content: str, *labels: str) -> tuple[list[str], list[list[str]]]:
    """First markdown table under a section → (header cells, data rows).

    Unlike lib.parse_table this keeps the header so callers can locate columns by
    name. Returns ([], []) if no section/table.
    """
    m = find_section(content, *labels)
    if not m:
        return [], []
    header: list[str] = []
    rows: list[list[str]] = []
    seen_sep = False
    for line in section_body(content, m).splitlines():
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


def _col_index(header: list[str], *needles: str) -> int | None:
    for i, h in enumerate(header):
        hl = h.lower()
        if any(n in hl for n in needles):
            return i
    return None


def required_facets(d27_text: str, d02_text: str | None) -> dict[str, set[str]]:
    """REQ → required facets, from a `Facets` column in D-02 functional table
    (preferred) or the D-27 Coverage Matrix."""
    sources = []
    if d02_text:
        sources.append(table_with_header(d02_text, "Functional Requirements", "Yêu cầu chức năng"))
    sources.append(table_with_header(d27_text, "Coverage Matrix", "Ma trận bao phủ"))
    req_facets: dict[str, set[str]] = {}
    for header, rows in sources:
        if not header:
            continue
        ci_req = _col_index(header, "req")
        ci_fac = _col_index(header, "facet")
        if ci_req is None or ci_fac is None:
            continue
        for r in rows:
            if ci_req >= len(r) or ci_fac >= len(r):
                continue
            mreq = REQ_ID_RE.search(r[ci_req])
            facets = _split_facets(r[ci_fac])
            if mreq and facets:
                req_facets.setdefault(mreq.group(0), set()).update(facets)
        if req_facets:
            break  # first source that declared facets wins
    return req_facets


def covered_facets(d27_text: str) -> dict[str, set[str]]:
    """REQ → facets covered, from each TC detail block's REQ ID + Facets tags."""
    covered: dict[str, set[str]] = {}
    blocks = re.split(r"^###\s+TC-", d27_text, flags=re.MULTILINE)
    for block in blocks[1:]:
        mreq = re.search(r"\*\*REQ ID:\*\*\s*(REQ-\d{3,})", block)
        mfac = re.search(r"\*\*Facets:\*\*\s*([^\n]+)", block)
        if mreq and mfac:
            covered.setdefault(mreq.group(1), set()).update(_split_facets(mfac.group(1)))
    return covered


def check(d27_text: str, d02_text: str | None = None) -> dict:
    required = required_facets(d27_text, d02_text)
    covered = covered_facets(d27_text)

    uncovered: dict[str, list[str]] = {}
    for req, facets in required.items():
        missing = sorted(facets - covered.get(req, set()))
        if missing:
            uncovered[req] = missing

    structure_ok = not uncovered
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
    return v


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated facet-aware coverage (M-1).")
    parser.add_argument("--d27", required=True, help="Path to D-27 test spec")
    parser.add_argument("--d02", help="Path to D-02 (preferred source of required facets)")
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
            d02_text = None

    result = check(d27_text, d02_text)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Facet coverage report written to {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0 if result["facet_covered"] else 1


if __name__ == "__main__":
    sys.exit(main())
