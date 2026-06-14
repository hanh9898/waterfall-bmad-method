#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""HBC inter-document readiness check (P-1).

Reconciles the authoritative requirement set (D-02 functional requirements table)
against the downstream design/test documents that must cover it — closing the
"seam" no single-document validator can see. Deterministic structural
reconciliation only; semantic adequacy stays with the LLM review layer.

Checks, for every REQ id DEFINED in D-02's functional requirements table, whether
it is covered downstream:
  - D-27 test spec: BOUND TO A `### TC-` BLOCK   (uncovered_by_test)   gates ready
        (TC-scoped, not a bare mention — closes the paste-the-appendix loophole;
         whether that test case is ADEQUATE stays with the LLM review layer)
  - the test plan D-26: mentioned                 (uncovered_by_plan)   gates ready [if --d26]
  - the traceability matrix: present              (missing_from_matrix) gates ready [if --matrix]
  - the API spec D-21: mentioned                  (uncovered_by_api)    INFORMATIONAL [if --d21]
And flags REQ ids referenced downstream but NOT defined in D-02 (orphans).

D-21 is informational, not gating: a UI-only / batch-only REQ legitimately has no
API surface, so an uncovered D-21 facet must not by itself fail readiness (it is
owned at D-26/D-27 per the facet rubric).

Returns the shared honest verdict (structure_ok / semantic_review / checked /
not_checked / passed) plus per-document reconciliation sets.

Exit codes: 0 ready, 1 gaps found, 2 D-02 missing/unreadable/no functional section
or arg error.
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

# --- shared lib bootstrap (C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        find_section,
        iter_tc_blocks,
        parse_table,
        tc_field,
        verdict,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

REQ_ID_RE = re.compile(r"REQ-\d{3,}")
FUNCTIONAL_LABELS = ("Functional Requirements", "Yêu cầu chức năng")


class FunctionalSectionMissing(ValueError):
    """D-02 has no functional requirements section → no authoritative REQ set."""


def d02_defined_reqs(text: str) -> set[str]:
    """REQ ids DEFINED in D-02 — functional table ID column only (mirrors S-4).

    The functional requirements section is REQUIRED; its table is authoritative
    even when empty. If the section is ABSENT we raise rather than fall back to a
    whole-file scan — a free-form scan would wrongly promote prose/assumption
    REQ-ids to "defined" and silently invert downstream coverage (D4).
    """
    if not find_section(text, *FUNCTIONAL_LABELS):
        raise FunctionalSectionMissing(
            "D-02 has no functional requirements section "
            f"({' / '.join(FUNCTIONAL_LABELS)}); cannot determine the authoritative REQ set."
        )
    ids: set[str] = set()
    for cells in parse_table(text, *FUNCTIONAL_LABELS):
        for cell in cells:
            m = REQ_ID_RE.match(cell.strip())
            if m:
                ids.add(m.group(0))
                break
    return ids


def referenced_reqs(text: str) -> set[str]:
    """Every REQ id referenced anywhere in a downstream document (mention-level).

    Used for D-26 (test plan) and D-21 (API spec), which have no test-case
    structure to bind a REQ to.
    """
    return set(REQ_ID_RE.findall(text))


def test_covered_reqs(text: str) -> set[str]:
    """REQ ids actually BOUND TO A TEST CASE in D-27 — from each `### TC-` block's
    `**REQ ID:**` field (the M-1 convention), not a bare mention anywhere in the
    document. This is what makes "covered by test" mean a test case exists, closing
    the paste-the-requirements-appendix loophole (#3). A TC may name several REQ
    ids (comma-separated, even wrapped onto the next line). Fenced code, `#### TC-`
    headings, and HTML comments are all handled by the shared TC helpers.
    """
    covered: set[str] = set()
    for block in iter_tc_blocks(text):
        field = tc_field(block, "REQ ID")
        if field:
            covered.update(REQ_ID_RE.findall(field))
    return covered


def tc_without_req_id_count(text: str) -> int:
    """TC blocks that exist but carry no usable **REQ ID:** field — surfaced so a
    test case that can't be bound to a REQ is visible, not silently ignored (#1)."""
    return sum(1 for block in iter_tc_blocks(text) if not tc_field(block, "REQ ID"))


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
    # Surface the missing-functional-section error as data (not an exception) so
    # library callers, not just main(), get a clean result (#5). Keep the FULL
    # verdict shape so an error result is key-compatible with a normal one (M3).
    try:
        defined = d02_defined_reqs(d02_text)
    except FunctionalSectionMissing as exc:
        v = verdict(False, semantic_review=SEMANTIC_NA, checked=[], not_checked=[])
        v.update({"error": str(exc), "ready": False, "d02_req_count": 0, "checked_documents": []})
        return v

    result: dict = {
        "d02_req_count": len(defined),
        "checked_documents": [],
    }
    all_orphans: set[str] = set()
    gaps = False
    gated_any = False  # ≥1 GATING document actually reconciled (D-21 doesn't count)

    def reconcile(label: str, text: str | None, key_uncovered: str, *,
                  gate_uncovered: bool = True, ref_fn=referenced_reqs):
        nonlocal gaps, gated_any
        if text is None:
            return
        result["checked_documents"].append(label)
        if gate_uncovered:
            gated_any = True
        refs = ref_fn(text)
        uncovered = sorted(defined - refs)
        orphans = refs - defined
        all_orphans.update(orphans)
        result[key_uncovered] = uncovered
        if uncovered and gate_uncovered:
            gaps = True

    # D-27 coverage is TC-scoped (a REQ must be bound to a `### TC-` block), not a
    # bare mention (#3). D-26/D-21 stay mention-level — they have no test-case form.
    reconcile("D-27", d27_text, "uncovered_by_test", ref_fn=test_covered_reqs)
    if d27_text is not None:
        unbindable = tc_without_req_id_count(d27_text)
        if unbindable:
            result["tc_without_req_id"] = unbindable  # transparency (#1)
    reconcile("D-26", d26_text, "uncovered_by_plan")
    # D-21 is informational: a UI/batch-only REQ has no API surface, so an
    # uncovered API facet must not by itself fail readiness (D2). Orphans from
    # D-21 still count — a REQ in the API spec but undefined in D-02 is a real seam.
    reconcile("D-21", d21_text, "uncovered_by_api", gate_uncovered=False)

    if matrix_text is not None:
        result["checked_documents"].append("matrix")
        gated_any = True
        matrix_refs = referenced_reqs(matrix_text)
        missing = sorted(defined - matrix_refs)
        all_orphans.update(matrix_refs - defined)
        result["missing_from_matrix"] = missing
        if missing:
            gaps = True

    result["orphan_reqs_downstream"] = sorted(all_orphans)
    if all_orphans:
        gaps = True

    # Nothing GATING reconciled = nothing that can fail was verified: do not report
    # a meaningful green. D-21 is informational, so a --d21-only run is not ready (P6).
    structure_ok = (not gaps) and gated_any
    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=[
            "D-02 REQ ids bound to a TC block in D-27 (TC-scoped)",
            "D-02 REQ ids mentioned in the test plan D-26 (if given)",
            "no orphan REQ referenced but undefined",
            "matrix ↔ D-02 sync (if matrix given)",
        ],
        not_checked=[
            "whether each TC actually EXERCISES its REQ adequately (LLM review)",
            "D-26 is mention-level (no test-case structure to bind to)",
            "D-21 API coverage is reported but informational, not gating",
            "facet-level coverage (read/write·api/admin) — see facet rubric / M-1",
            "semantic adequacy of each REQ's coverage (LLM review)",
        ],
    )
    if not gated_any:
        v["note"] = "No gating downstream document (D-27/D-26/matrix) provided; nothing was reconciled."
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

    def read_or_warn(path: str | None, label: str) -> str | None:
        """Read a downstream doc; warn (don't silently skip) if a path was given
        but is unreadable, so a missing/corrupt doc can't masquerade as green (P3)."""
        if not path:
            return None
        text = _read(path)
        if text is None:
            print(f"WARNING: {label} provided but not readable, skipping: {path}", file=sys.stderr)
        return text

    result = check_readiness(
        d02_text,
        d27_text=read_or_warn(args.d27, "--d27"),
        d26_text=read_or_warn(args.d26, "--d26"),
        d21_text=read_or_warn(args.d21, "--d21"),
        matrix_text=read_or_warn(args.matrix, "--matrix"),
    )
    if result.get("error"):
        print(json.dumps(result, ensure_ascii=False))
        return 2

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "ready": False}, ensure_ascii=False))
            return 2
        print(f"Readiness report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
