#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""HBC inter-document readiness check (P-1).

Reconciles the authoritative requirement set (D-02 functional requirements table)
against the downstream design/test documents that must cover it — closing the
"seam" no single-document validator can see. Deterministic structural
reconciliation only; semantic adequacy stays with the LLM review layer.

Checks, for every REQ id DEFINED in D-02's functional requirements table:
  - referenced by ≥1 test case in D-27   (uncovered_by_test)
  - referenced in the test plan D-26      (uncovered_by_plan)      [if --d26 given]
  - present in the traceability matrix     (missing_from_matrix)    [if --matrix given]
And flags REQ ids referenced downstream but NOT defined in D-02 (orphans).

Returns the shared honest verdict (structure_ok / semantic_review / checked /
not_checked / passed) plus per-document reconciliation sets.

Exit codes: 0 ready, 1 gaps found, 2 D-02 missing/unreadable or arg error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- shared lib bootstrap (C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import SEMANTIC_NA, find_section, parse_table, verdict  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

REQ_ID_RE = re.compile(r"REQ-\d{3,}")
FUNCTIONAL_LABELS = ("Functional Requirements", "Yêu cầu chức năng")


def d02_defined_reqs(text: str) -> set[str]:
    """REQ ids DEFINED in D-02 — functional table ID column only (mirrors S-4).

    If the functional section is present, its table is authoritative even when
    empty; only when the section is absent do we fall back to a whole-file scan.
    """
    if find_section(text, *FUNCTIONAL_LABELS):
        ids: set[str] = set()
        for cells in parse_table(text, *FUNCTIONAL_LABELS):
            for cell in cells:
                m = REQ_ID_RE.match(cell.strip())
                if m:
                    ids.add(m.group(0))
                    break
        return ids
    return set(REQ_ID_RE.findall(text))


def referenced_reqs(text: str) -> set[str]:
    """Every REQ id referenced anywhere in a downstream document."""
    return set(REQ_ID_RE.findall(text))


def _read(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_readiness(
    d02_text: str,
    d27_text: str | None = None,
    d26_text: str | None = None,
    d21_text: str | None = None,
    matrix_text: str | None = None,
) -> dict:
    defined = d02_defined_reqs(d02_text)

    result: dict = {
        "d02_req_count": len(defined),
        "checked_documents": [],
    }
    all_orphans: set[str] = set()
    gaps = False

    def reconcile(label: str, text: str | None, key_uncovered: str):
        nonlocal gaps
        if text is None:
            return
        result["checked_documents"].append(label)
        refs = referenced_reqs(text)
        uncovered = sorted(defined - refs)
        orphans = refs - defined
        all_orphans.update(orphans)
        result[key_uncovered] = uncovered
        if uncovered:
            gaps = True

    reconcile("D-27", d27_text, "uncovered_by_test")
    reconcile("D-26", d26_text, "uncovered_by_plan")
    reconcile("D-21", d21_text, "uncovered_by_api")

    if matrix_text is not None:
        result["checked_documents"].append("matrix")
        matrix_refs = referenced_reqs(matrix_text)
        missing = sorted(defined - matrix_refs)
        all_orphans.update(matrix_refs - defined)
        result["missing_from_matrix"] = missing
        if missing:
            gaps = True

    result["orphan_reqs_downstream"] = sorted(all_orphans)
    if all_orphans:
        gaps = True

    structure_ok = not gaps
    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=[
            "D-02 REQ ids referenced by downstream docs",
            "no orphan REQ referenced but undefined",
            "matrix ↔ D-02 sync (if matrix given)",
        ],
        not_checked=[
            "facet-level coverage (read/write·api/admin) — see facet rubric / M-1",
            "semantic adequacy of each REQ's coverage (LLM review)",
        ],
    )
    v.update(result)
    v["ready"] = structure_ok
    return v


def main() -> int:
    parser = argparse.ArgumentParser(description="HBC inter-document readiness check (P-1).")
    parser.add_argument("--d02", required=True, help="Path to D-02 requirements")
    parser.add_argument("--d27", help="Path to D-27 test spec")
    parser.add_argument("--d26", help="Path to D-26 test plan")
    parser.add_argument("--d21", help="Path to D-21 API spec")
    parser.add_argument("--matrix", help="Path to traceability matrix")
    parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    d02_text = _read(args.d02)
    if d02_text is None:
        print(json.dumps({"error": f"D-02 not readable: {args.d02}", "ready": False}, ensure_ascii=False))
        return 2

    result = check_readiness(
        d02_text,
        d27_text=_read(args.d27),
        d26_text=_read(args.d26),
        d21_text=_read(args.d21),
        matrix_text=_read(args.matrix),
    )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Readiness report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
