#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""HBC inter-document readiness check (P-1) — the seam gate (B.13).

Reconciles the authoritative requirement set (D-02 functional requirements table)
against the downstream design/test/implementation documents that must cover it —
closing the "seam" no single-document validator can see. This gate was BROKEN in
the RCA case (it let a half-failed feature through); the overhaul makes it catch
the half-failure it missed. Deterministic structural reconciliation only; semantic
adequacy stays with the LLM review layer.

Checks, for every REQ id DEFINED in D-02's functional requirements table:
  - D-27 test spec: BOUND TO A `### TC-` BLOCK   (uncovered_by_test)    gates ready
        (TC-scoped, not a bare mention — closes the paste-the-appendix loophole #3 /
         B13-5; whether that test case is ADEQUATE stays with the LLM review layer)
  - the test plan D-26: mentioned                 (uncovered_by_plan)    gates ready [if --d26]
  - the traceability matrix: has a ROW            (missing_from_matrix)  gates ready [if --matrix] (B13-1)
        + per-REQ trace columns NON-EMPTY         (matrix_coverage_gaps) gates ready          (B13-1)
  - the task-breakdown: has ≥1 task               (reqs_without_task)    gates ready [if --task-breakdown] (B13-2)
  - the API spec D-21: mentioned                  (uncovered_by_api)     INFORMATIONAL [if --d21]
And flags:
  - REQ ids referenced downstream but NOT defined in D-02 (orphan_reqs_downstream)
  - tasks referencing a REQ undefined in D-02       (orphan_tasks)        gates ready    (B13-2)
  - downstream docs / task-breakdown citing a STALE D-02 version (stale_citations) gates ready (B13-2/B13-4)
  - model-level code↔design drift                   (model_drift)         gates ready [if --d19 + --code-dir] (B13-3)
  - matrix test_ref ↔ D-27 TC-binding drift         (test_ref_drift)      gates ready

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
        doc_version,
        find_section,
        iter_tc_blocks,
        matrix_coverage_gaps,
        missing_from_matrix,
        model_drift,
        parse_matrix,
        parse_table,
        req_num_map,
        reqs_without_task,
        tc_field,
        test_ref_drift,
        verdict,
        version_coherence,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# Namespace-aware (v2): matches both legacy `REQ-001` and per-feature
# `REQ-<FEAT>-NNN` (e.g. REQ-AUTH-001) + shared `REQ-SHARED-NNN`. Mirrors the
# id grammar used by validate-requirements.py and trace-report.py. A bare
# `REQ-\d{3,}` here silently matched ZERO feature-namespaced ids → every gap
# reported green (the false-green seam bug).
REQ_ID_RE = re.compile(r"REQ-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}")
FUNCTIONAL_LABELS = ("Functional Requirements", "Yêu cầu chức năng")

# Persistent-model source only (B13-3): drift is measured against models the design
# declares as real tables. Transient wizards/transient models are not in D-19, so a
# code_only wizard would be a false drift signal — restrict the code corpus to
# model files. A caller can widen this with --code-glob if their layout differs.
DEFAULT_CODE_GLOB = "models/**/*.py"


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
    the paste-the-requirements-appendix loophole (#3 / B13-5). A TC may name several
    REQ ids (comma-separated, even wrapped onto the next line). Fenced code,
    `#### TC-` headings, and HTML comments are all handled by the shared TC helpers.
    """
    covered: set[str] = set()
    for block in iter_tc_blocks(text):
        field = tc_field(block, "REQ ID")
        if field:
            covered.update(REQ_ID_RE.findall(field))
    return covered


def orphans_by_number(text: str, defined_nums: set[int]) -> set[str]:
    """REQ ids referenced in ``text`` whose trailing NUMBER is not among D-02's
    defined numbers — a real orphan (referenced but undefined).

    Identity is the trailing number, not the exact string, so the bare prose form
    (``REQ-040``) and the canonical form (``REQ-RESOURCE-PLAN-BILLABLE-040``) of the
    SAME requirement reconcile and are NOT counted as orphans of each other. Using
    exact-string set difference here was a false-positive (masking) bug: a downstream
    doc that writes ids in bare form would flag every requirement as an orphan.
    Mirrors the trailing-number identity in missing_from_matrix / reqs_without_task.
    """
    out: set[str] = set()
    for rid in REQ_ID_RE.findall(text):
        m = re.search(r"\d+$", rid)
        if m and int(m.group()) not in defined_nums:
            out.add(rid)
    return out


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


def _read_code(code_dir: str | None, glob: str) -> str | None:
    """Concatenate persistent-model source under ``code_dir`` (B13-3 ground truth).

    Returns None when no code_dir was given so model-drift simply doesn't run.
    Returns "" (empty, not None) when the dir exists but has no matching files — an
    empty corpus still lets model_drift report every design model as design_only
    rather than masquerading as "no code to check, therefore green".
    """
    if not code_dir:
        return None
    root = Path(code_dir)
    if not root.exists():
        print(f"WARNING: --code-dir does not exist, model-drift skipped: {code_dir}", file=sys.stderr)
        return None
    parts: list[str] = []
    for p in sorted(root.glob(glob)):
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(parts)


def check_readiness(
    d02_text: str,
    d27_text: str | None = None,
    d26_text: str | None = None,
    d21_text: str | None = None,
    matrix_text: str | None = None,
    task_text: str | None = None,
    d19_text: str | None = None,
    code_text: str | None = None,
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

    # Trailing-number identity for D-02's defined set, so orphan detection reconciles
    # the bare (REQ-040) and canonical (REQ-FEAT-040) forms of the same requirement.
    defined_nums = set(req_num_map(d02_text)[0])

    result: dict = {
        "d02_req_count": len(defined),
        "checked_documents": [],
    }
    all_orphans: set[str] = set()
    gaps = False
    gated_any = False  # ≥1 GATING document actually reconciled (D-21 doesn't count)

    def _ref_nums(refs: set[str]) -> set[int]:
        out: set[int] = set()
        for rid in refs:
            m = re.search(r"\d+$", rid)
            if m:
                out.add(int(m.group()))
        return out

    def reconcile(label: str, text: str | None, key_uncovered: str, *,
                  gate_uncovered: bool = True, ref_fn=referenced_reqs):
        nonlocal gaps, gated_any
        if text is None:
            return
        result["checked_documents"].append(label)
        if gate_uncovered:
            gated_any = True
        refs = ref_fn(text)
        # Coverage is by trailing NUMBER, not exact string, so a downstream doc that
        # writes ids in bare form (REQ-014) still covers the canonical D-02 id
        # (REQ-FEAT-014). Exact-string `defined - refs` was a false-positive bug that
        # would mark every REQ uncovered when the downstream doc used a different form.
        covered_nums = _ref_nums(refs)
        uncovered = sorted(r for r in defined
                           if (m := re.search(r"\d+$", r)) and int(m.group()) not in covered_nums)
        all_orphans.update(orphans_by_number(text, defined_nums))
        result[key_uncovered] = uncovered
        if uncovered and gate_uncovered:
            gaps = True

    # D-27 coverage is TC-scoped (a REQ must be bound to a `### TC-` block), not a
    # bare mention (#3 / B13-5). D-26/D-21 stay mention-level — no test-case form.
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

    # --- B13-1: matrix ROW present + trace columns NON-EMPTY ---
    if matrix_text is not None:
        result["checked_documents"].append("matrix")
        gated_any = True
        # Trailing-number identity (shared primitive) so canonical/bare ids reconcile.
        missing = missing_from_matrix(d02_text, matrix_text)
        all_orphans.update(orphans_by_number(matrix_text, defined_nums))
        result["missing_from_matrix"] = missing
        if missing:
            gaps = True
        # A REQ can have a ROW yet a blank design_ref/code_ref/test_ref — still
        # untraced for that axis (the "39/39 green" that hid empty cells). B13-1.
        # Gate ONLY on trace columns the matrix actually CARRIES: an absent column is
        # the matrix's schema (not a per-REQ omission), so a lean req-id-only matrix
        # is not penalized for columns it never tracked — we'd otherwise flag every
        # row as a gap. The fixture matrix carries all three, so the real
        # blank-cell case is still caught.
        header, _ = parse_matrix(matrix_text)
        present_cols = tuple(c for c in ("design_ref", "code_ref", "test_ref") if c in header)
        if present_cols:
            col_gaps = matrix_coverage_gaps(matrix_text, present_cols)
            if col_gaps:
                result["matrix_coverage_gaps"] = col_gaps
                gaps = True

    # --- B13-2: 3-way reconcile REQ ↔ TASK ↔ current design ---
    # The exact half-failure of the RCA case: a task-breakdown stuck on an older
    # D-02 (v1.8/39 REQ) reading "green" while D-02 had moved to v2.3/42 REQ, so the
    # request/snapshot/withdraw slice (REQ-040/041/042) was never tasked.
    if task_text is not None:
        result["checked_documents"].append("task-breakdown")
        gated_any = True
        # (a) REQ → TASK: every defined REQ needs ≥1 task.
        without_task = reqs_without_task(defined, task_text)
        result["reqs_without_task"] = without_task
        if without_task:
            gaps = True
        # (b) TASK → REQ: a task referencing a REQ undefined in D-02 is an orphan
        #     task (stale slice for a requirement that no longer exists). By trailing
        #     number so bare/canonical forms of the same REQ are not false orphans.
        task_orphans = sorted(orphans_by_number(task_text, defined_nums))
        result["orphan_tasks"] = task_orphans
        if task_orphans:
            gaps = True

    # --- B13-4 + B13-2(c): version-coherence at the seam ---
    # A downstream doc / task-breakdown that pins a STALE D-02 version is consuming a
    # superseded spec — "D-26 cites D-02 v2.2 while D-02 is v2.3", "task-breakdown
    # sources: D-02 v1.8". This is the TASK↔current-design staleness (B13-2) and the
    # D-26/D-27 seam staleness (B13-4), via the one shared primitive.
    declared = doc_version(d02_text)
    if declared is not None:
        citing: dict[str, str] = {}
        if d26_text is not None:
            citing["D-26"] = d26_text
        if d27_text is not None:
            citing["D-27"] = d27_text
        if task_text is not None:
            citing["task-breakdown"] = task_text
        stale = version_coherence({"D-02": declared}, citing)
        if stale:
            result["stale_citations"] = stale
            gaps = True

    # --- B13-3: model-level code ↔ design (D-19) drift ---
    # readiness must fail when the design moved (Request+Snapshot) but code stayed on
    # the old model — the central RCA drift. Only runs when BOTH the design and a
    # code corpus are given (drift is meaningless with one side absent).
    if d19_text is not None and code_text is not None:
        result["checked_documents"].append("D-19/code")
        gated_any = True
        md = model_drift(d19_text, code_text)
        if md["drift"]:
            result["model_drift"] = {"design_only": md["design_only"], "code_only": md["code_only"]}
            gaps = True

    # Matrix test_ref ↔ D-27 drift (DF-9): when both are present, the matrix's
    # test_ref must reflect D-27's current TC↔REQ binding. Catches a matrix gone
    # stale after D-27 grew (e.g. a cascade added TCs) but test_ref was never
    # back-filled — readiness must NOT close Phase 2 on a matrix that silently
    # under-reports test coverage. {req: {missing, stale}}; gates ready.
    if d27_text is not None and matrix_text is not None:
        drift = test_ref_drift(d27_text, matrix_text)
        if drift:
            result["test_ref_drift"] = drift
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
            "matrix ROW present + design/code/test_ref non-empty per REQ (if matrix given)",
            "every REQ has ≥1 task + no orphan task (3-way reconcile, if task-breakdown given)",
            "no downstream doc / task-breakdown cites a stale D-02 version",
            "no model-level code↔design (D-19) drift (if D-19 + code given)",
            "no orphan REQ referenced but undefined",
            "matrix test_ref ↔ D-27 TC binding drift (if both given)",
        ],
        not_checked=[
            "whether each TC actually EXERCISES its REQ adequately (LLM review)",
            "D-26 is mention-level (no test-case structure to bind to)",
            "D-21 API coverage is reported but informational, not gating",
            "facet-level coverage (read/write·api/admin) — see facet rubric / M-1",
            "whether an out-of-scope deferral is acceptable (domain decision — ASK)",
            "semantic adequacy of each REQ's coverage (LLM review)",
        ],
    )
    if not gated_any:
        v["note"] = ("No gating downstream document (D-27/D-26/matrix/task-breakdown/D-19) "
                     "provided; nothing was reconciled.")
    v.update(result)
    v["ready"] = structure_ok
    return v


def main() -> int:
    parser = argparse.ArgumentParser(description="HBC inter-document readiness check (P-1, B.13).")
    parser.add_argument("--d02", required=True, help="Path to D-02 requirements")
    parser.add_argument("--d27", help="Path to D-27 test spec")
    parser.add_argument("--d26", help="Path to D-26 test plan")
    parser.add_argument("--d21", help="Path to D-21 API spec (informational)")
    parser.add_argument("--matrix", help="Path to the per-feature traceability matrix")
    parser.add_argument("--task-breakdown", dest="task_breakdown",
                        help="Path to the task-breakdown (B13-2 3-way reconcile)")
    parser.add_argument("--d19", help="Path to D-19 ER diagram (B13-3 model-drift design side)")
    parser.add_argument("--code-dir", dest="code_dir",
                        help="Path to the feature code root (B13-3 model-drift code side)")
    parser.add_argument("--code-glob", dest="code_glob", default=DEFAULT_CODE_GLOB,
                        help=f"Glob under --code-dir for persistent-model source (default: {DEFAULT_CODE_GLOB})")
    parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    d02_text = _read(args.d02)
    if d02_text is None:
        print(json.dumps({"error": f"D-02 not readable: {args.d02}", "ready": False,
                          "reason": "d02_unreadable"}, ensure_ascii=False))
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

    # model-drift needs BOTH --d19 and --code-dir; warn if only one was given so a
    # half-specified pair can't quietly drop the drift check and read green (#false-green).
    code_text = _read_code(args.code_dir, args.code_glob)
    d19_text = read_or_warn(args.d19, "--d19")
    if (d19_text is None) != (code_text is None):
        print("WARNING: model-drift (B13-3) needs BOTH --d19 and --code-dir; "
              "only one given → drift check skipped.", file=sys.stderr)
        d19_text = None
        code_text = None

    result = check_readiness(
        d02_text,
        d27_text=read_or_warn(args.d27, "--d27"),
        d26_text=read_or_warn(args.d26, "--d26"),
        d21_text=read_or_warn(args.d21, "--d21"),
        matrix_text=read_or_warn(args.matrix, "--matrix"),
        task_text=read_or_warn(args.task_breakdown, "--task-breakdown"),
        d19_text=d19_text,
        code_text=code_text,
    )
    if result.get("error"):
        result.setdefault("reason", "no_functional_section")
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
