#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Reconcile a task breakdown against its inputs (B4-7 / B4-2).

A task breakdown drifts in two characteristic ways the structural validator
(validate-task-breakdown.py) cannot see — both are the exact RCA failure mode
(`resource-plan-billable`: a STALE breakdown silently missing REQ-040/041/042):

  - REQ_WITHOUT_TASK (B4-7) — a requirement defined in D-02 with NO task that
    references it. Every REQ must map to >=1 task; a missed REQ becomes a missed
    vertical slice. Identity is the requirement's trailing number so the canonical
    id (REQ-FEAT-040) and the bare prose form (REQ-040) reconcile, and the common
    slash-shorthand `REQ-005/006/007` is expanded so each number counts as cited.
  - INPUT_INSUFFICIENT (B4-2) — the breakdown's declared input set is missing a
    dimension a complete breakdown needs to be grounded: the D-02 requirements,
    the D-06 business-flow paths, per-REQ acceptance criteria, and the code-reality
    classification (NEW / CHANGE / already-exists). Surfaced so the human can halt
    and gather the input BEFORE generating tasks, rather than generate blind.

ADVISORY, not a hard inter-doc gate: the blocking REQ<->task<->design reconcile is
the readiness gate (hbc-check-implementation-readiness [IR], B13-2). This informs
the breakdown's *coverage + input grounding* during creation. STRUCTURE-only —
whether a slice is genuinely vertical / INVEST-sound, and whether a task is correct,
stay with the LLM/semantic layer.

Machine two-way 100%-rule coverage (TA.5 / IMP-05)
==================================================
`two_way_coverage` answers the 100%-rule BY MACHINE, BOTH directions, computed as a
VIEW over the TA.1 build-graph (`hbc_buildgraph`) rather than a re-parse of a hand
table -- D-02 and the task-breakdown become nodes, and coverage is derived from the
living graph's node text, so it cannot drift from what the graph sees:

  - REQ->task  -- every REQ defined in the D-02 node has >=1 task (reuse
    `reqs_without_task`); a missed REQ is a missed vertical slice (the case's
    REQ-040/041/042 failure).
  - task->REQ  -- every task maps to >=1 LIVE REQ. An ORPHAN task cites REQ
    number(s) NONE of which still exist in D-02 (a stale/dangling reference to a
    REQ that was renumbered or removed). Identity is the trailing number, so the
    canonical (REQ-FEAT-040) and bare (REQ-040) forms reconcile and a bare cite is
    NOT a false orphan. A task that cites NO REQ at all (legitimate for infra/
    scaffold slices) is reported separately as `tasks_without_req` and does NOT, on
    its own, fail the two-way rule -- only dangling references do.

`two_way_complete` is true iff `reqs_without_task` AND `orphan_tasks` are both
empty. ADVISORY here too -- the blocking enforcement remains [IR]/the phase gate.

Exit: 0 clean, 1 findings, 2 arg/io error.
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
        churn_assessment,
        req_num_map,
        verdict,
    )
    # TA.1 build-graph kernel (read-only import) — the two-way rule is a VIEW over it.
    from hbc_buildgraph import BuildGraph, Node  # noqa: E402
except Exception as exc:  # noqa: BLE001 — any import failure is a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# A REQ reference, optionally followed by the slash-shorthand the RCA breakdown
# uses to pack several requirements into one cell, e.g. `REQ-005/006/007/010` or
# `REQ-RESOURCE-PLAN-BILLABLE-014/015/016`. group(1) = the first trailing number,
# group(2) = the `/NNN/NNN…` tail. STRUCTURE-only — this only normalizes the id
# format, it does not interpret meaning.
_REQ_SHORTHAND_RE = re.compile(r"REQ(?:-[A-Za-z][A-Za-z0-9]*)*-(\d{3,})((?:/\d{3,})+)")

# Input-set dimensions a complete breakdown declares (B4-2). Each maps to a set of
# case-insensitive marker substrings; English canonical + configured-language (VI).
# NO hardcoded Japanese. Presence-only: the script asserts the dimension is named,
# not that it is correct (that is LLM judgment).
_INPUT_DIMENSIONS = {
    "requirements_d02": ("D-02", "requirement", "yêu cầu", "REQ-"),
    "business_flow_d06": ("D-06", "business flow", "luồng nghiệp vụ", "path-", "flow"),
    "acceptance_criteria": ("acceptance", "AC ", "AC-", "tiêu chí chấp nhận", "nghiệm thu"),
    "code_reality": (
        "NEW", "CHANGE", "already-exists", "already exists", "đã có",
        "code-reality", "code reality", "brownfield", "tạo mới", "sửa",
    ),
}


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def cited_req_nums(text: str) -> set[int]:
    """Every requirement trailing-number referenced in ``text`` (B4-7 coverage side).

    Combines the shared ``req_num_map`` (which captures whole REQ ids) with an
    expansion of the slash-shorthand so `REQ-005/006/007` contributes 5, 6 and 7.
    Without expansion the shorthand would mask covered REQs as missing — the exact
    false-positive that would make a stale-but-shorthand-rich breakdown look broken
    when it is merely densely written.
    """
    nums = set(req_num_map(text or "")[0])
    for m in _REQ_SHORTHAND_RE.finditer(text or ""):
        nums.add(int(m.group(1)))
        for tail in re.findall(r"\d{3,}", m.group(2)):
            nums.add(int(tail))
    return nums


def reqs_without_task(d02_text: str, tasks_text: str) -> list[str]:
    """REQ ids in D-02 with no reference anywhere in the breakdown (B4-7).

    Forward direction (a REQ missing a task). The reverse (orphan tasks) and the full
    two-way 100%-rule live in ``two_way_coverage`` (TA.5), which reuses this.
    """
    nums, _ = req_num_map(d02_text or "")
    covered = cited_req_nums(tasks_text)
    return [nums[n] for n in sorted(nums) if n not in covered]


# A task row in the breakdown table. Task ids are TASK-NNN / T-NNN style; the row's
# REQ citations are extracted with the same shorthand-aware logic as the whole-doc
# scan, so a task citing `REQ-005/006/007` contributes 5, 6 and 7 to that task.
_TASK_ID_RE = re.compile(r"\b(T(?:ASK)?-\d{1,})\b", re.IGNORECASE)


def task_req_citations(tasks_text: str) -> dict[str, set[int]]:
    """Map each task id -> the set of REQ trailing-numbers cited IN THAT task's row.

    Only markdown table rows are considered (a row is a ``|``-delimited line whose
    first non-empty cell holds a task id). A row with no task id is skipped, so prose
    paragraphs and the header/separator do not manufacture phantom tasks. Per-row
    citation reuse of ``cited_req_nums`` keeps the slash-shorthand expansion identical
    to the whole-doc side — no second, divergent parser.
    """
    out: dict[str, set[int]] = {}
    for line in (tasks_text or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            continue  # separator row
        # the task id is the first cell that looks like one (id column position is
        # not assumed — some breakdowns lead with a feature/seq cell)
        tid = next((m.group(1) for c in cells for m in [_TASK_ID_RE.match(c)] if m), None)
        if tid is None:
            continue
        out.setdefault(tid, set()).update(cited_req_nums(s))
    return out


def two_way_coverage(d02_text: str, tasks_text: str) -> dict:
    """The machine 100%-rule, BOTH directions, as a VIEW over the TA.1 build-graph.

    D-02 and the task-breakdown are added as graph nodes; the coverage is then
    derived from the living graph's node text (``g.get('D-02').text`` /
    ``g.get('task-breakdown').text``) — not from a hand-maintained matrix table — so
    the check is a view over the graph, consistent with ``matrix_view``/``missing_edges``.

    Returns ``{reqs_without_task, orphan_tasks, tasks_without_req, two_way_complete}``:
      * reqs_without_task  — REQ->task gap (forward; ``reqs_without_task``).
      * orphan_tasks       — task->REQ gap: tasks whose cited REQ numbers are ALL
                             dangling (none exists in D-02). Each entry is
                             ``{task_id, dangling: [bare ids]}``.
      * tasks_without_req  — tasks citing zero REQ (advisory; infra/scaffold may
                             legitimately cite none) — does not fail the rule.
      * two_way_complete   — both reqs_without_task AND orphan_tasks empty.
    """
    g = BuildGraph()
    g.add(Node(id="D-02", kind="doc", text=d02_text or ""))
    g.add(Node(id="task-breakdown", kind="task-breakdown", text=tasks_text or ""))
    d02 = g.get("D-02")
    tb = g.get("task-breakdown")

    req_nums, _ = req_num_map(d02.text)
    live_nums = set(req_nums)  # the authoritative REQ universe from the D-02 node

    # forward direction reuses the local shorthand-aware reqs_without_task, so a dense
    # `REQ-005/006/007` cell isn't false-flagged (the shared primitive doesn't expand it)
    forward = reqs_without_task(d02.text, tb.text)

    orphans: list[dict] = []
    tasks_without_req: list[str] = []
    citations = task_req_citations(tb.text)
    for tid in sorted(citations):
        cited = citations[tid]
        if not cited:
            tasks_without_req.append(tid)
            continue
        if not (cited & live_nums):
            # every REQ this task cites is dangling — a stale/orphan reference
            orphans.append({
                "task_id": tid,
                "dangling": [f"REQ-{n:03d}" for n in sorted(cited)],
            })

    return {
        "reqs_without_task": forward,
        "orphan_tasks": orphans,
        "tasks_without_req": tasks_without_req,
        "two_way_complete": not forward and not orphans,
    }


def input_gaps(tasks_text: str) -> list[str]:
    """Input-set dimensions the breakdown declares NO marker for (B4-2).

    Scans the whole breakdown (frontmatter `sources:` + body) for each dimension's
    markers. A dimension with zero markers is surfaced so the author can confirm the
    input was actually consulted before generating — 'suspect inputs insufficient'.
    Returns the missing dimension keys (e.g. ['acceptance_criteria','code_reality']).
    """
    low = (tasks_text or "").lower()
    missing: list[str] = []
    for dim, markers in _INPUT_DIMENSIONS.items():
        if not any(mk.lower() in low for mk in markers):
            missing.append(dim)
    return missing


def check(
    tasks_path: str,
    d02_path: str | None = None,
) -> dict:
    content = _read(tasks_path)

    missing_reqs: list[str] = []
    grounded = bool(d02_path)
    coverage: dict | None = None
    if d02_path:
        d02_text = _read(d02_path)
        coverage = two_way_coverage(d02_text, content)
        missing_reqs = coverage["reqs_without_task"]

    gaps = input_gaps(content)

    issues: list[dict] = []
    for rid in missing_reqs:
        issues.append({
            "type": "REQ_WITHOUT_TASK",
            "message": f"{rid} is defined in D-02 but no task references it — every REQ needs >=1 task/slice (B4-7)",
            "req_id": rid,
            "auto_fixable": False,
        })
    for orphan in coverage["orphan_tasks"] if coverage else []:
        issues.append({
            "type": "ORPHAN_TASK",
            "message": (
                f"{orphan['task_id']} cites only dangling REQ(s) {orphan['dangling']} "
                f"— none exists in the current D-02 (stale/renumbered ref) (TA.5 task->REQ)"
            ),
            "task_id": orphan["task_id"],
            "auto_fixable": False,
        })
    for dim in gaps:
        issues.append({
            "type": "INPUT_INSUFFICIENT",
            "message": f"input dimension '{dim}' is not declared in the breakdown — confirm it was consulted before generating tasks (B4-2)",
            "dimension": dim,
            "auto_fixable": False,
        })

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=[
            "two-way 100%-rule via the build-graph: every D-02 REQ has >=1 task (B4-7) "
            "AND every task maps to >=1 live REQ — no orphan/dangling task (TA.5)"
            if grounded
            else "REQ<->task two-way coverage SKIPPED (no --d02 supplied)",
            "the input set declares D-02 / D-06 / acceptance-criteria / code-reality (B4-2)",
        ],
        not_checked=[
            "whether each task is a genuine VERTICAL slice (INVEST/SPIDR — LLM/semantic)",
            "whether a task citing zero REQ (tasks_without_req — infra/scaffold) is legitimately REQ-free (LLM/semantic)",
            "whether the path/REQ-facet/entity->slice mapping was reviewed with the user before generation (B4-6, ASK-before-generate)",
            "whether the declared inputs are actually current vs upstream (B4-3 STALE re-derive — forward-ref T2.4)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "grounded": grounded,
        "reqs_without_task": missing_reqs,
        # TA.5 machine two-way 100%-rule (view over the build-graph). Null when no
        # --d02 was supplied (the REQ universe is unknown, so the rule can't be run).
        "two_way_coverage": coverage,
        "input_gaps": gaps,
        "churn": churn_assessment(content),
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile task-breakdown coverage: every REQ has >=1 task (B4-7), input set declared (B4-2)."
    )
    ap.add_argument("document", help="Path to task-breakdown.md")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--d02", help="Path to D-02 requirements (REQ->task coverage check)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    doc = Path(_resolve(args.document))
    if not doc.exists():
        print(json.dumps({
            "error": f"Task breakdown not found: {doc}",
            "suggestion": "Run 'hbc-task-breakdown' first to generate it.",
        }, ensure_ascii=False))
        return 2

    # A supplied --d02 that is missing is a loud arg error, not a silent skip — a
    # silently-dropped D-02 would turn the coverage check into a false green.
    d02: str | None = None
    if args.d02:
        d02 = _resolve(args.d02)
        if not Path(d02).is_file():
            print(json.dumps({"error": f"--d02 file not found: {d02}", "valid": False}, ensure_ascii=False))
            return 2

    try:
        result = check(str(doc), d02)
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "valid": False}, ensure_ascii=False))
            return 2
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
