#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Reconcile a D-26 Test Plan against its inputs and own structure (B9-1 / B9-4).

A test plan drifts in two characteristic ways the structural validator cannot see:

  - FABRICATED_SCHEDULE (B9-1) — a concrete calendar date appears in the Schedule
    section that is grounded in NOTHING: not present in any supplied source doc, and
    the plan does not flag the schedule as ASSUMPTION / ADR / pending. An invented
    timeline reads as authoritative when it is a guess. Surfaced for the human to
    ground or mark.
  - TECHNIQUE_GAP (B9-4) — an in-scope test area (a data row of the In-Scope table)
    with no stated test technique/approach and no D-27 cross-link. Every scope area
    needs a stated approach that hands off to the detailed D-27 test cases.

ADVISORY, not a hard inter-doc gate: the blocking cross-document gate is the
readiness gate (hbc-check-implementation-readiness, P-1). This informs the plan's
*grounding + completeness* during creation. STRUCTURE-only — whether a risk's
likelihood/impact is *realistic* (B9-2) and whether a technique is *appropriate*
stay with the LLM/semantic layer; this script only checks presence and grounding.

D-27 may not exist yet (it is authored after D-26) — a forward-reference to D-27
counts as a satisfied link; the file's existence is NOT required.

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
        find_section,
        parse_table,
        section_body,
        verdict,
    )
except Exception as exc:  # noqa: BLE001 — any import failure is a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

SCHEDULE_LABELS = ("Schedule", "Lịch trình")
# The In-Scope area table lives under the In-Scope SUBSECTION (### 2.1), but
# find_section only resolves level-1/2 headings — so we locate the level-2
# "Test Scope" parent, then slice its In-Scope subsection out of the body before
# parsing the table (so Out-of-Scope rows are never counted as in-scope areas).
# Labels: English canonical + configured (VI). NO hardcoded Japanese.
TESTSCOPE_LABELS = ("Test Scope", "Phạm vi kiểm thử")
# In-Scope / Out-of-Scope subsection headings (any heading level), used to slice the
# In-Scope subsection body out of the Test Scope section.
_INSCOPE_HEAD_RE = re.compile(r"^#{2,6}\s.*\b(?:In[- ]?Scope|Trong phạm vi)\b", re.IGNORECASE | re.MULTILINE)
_OUTSCOPE_HEAD_RE = re.compile(r"^#{2,6}\s.*(?:Out[- ]?of[- ]?Scope|Ngoài phạm vi)", re.IGNORECASE | re.MULTILINE)

# An ISO calendar date (YYYY-MM-DD) — the schedule grain D-26 uses for milestones
# and the Gantt `dateFormat YYYY-MM-DD`. We only reason about whole dates, never
# bare years/months, so a Gantt duration ("6d") or an Odoo version ("Odoo 11") is
# never mistaken for a schedule commitment.
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# Markers that DECLARE a schedule as not-yet-grounded — any of these in the Schedule
# section means the dates are openly provisional, so B9-1 does not fire. Case-
# insensitive; English canonical + configured-language equivalents (NO hardcoded
# Japanese — VI is the configured label here; extend per document_output_language).
_PROVISIONAL_MARKERS = (
    "assumption", "adr", "tbd", "pending", "provisional", "tentative",
    "giả định", "dự kiến", "tạm tính", "chưa chốt", "sẽ chốt", "điều chỉnh",
)
# A reference to the detailed test-spec deliverable — satisfies the B9-4 hand-off
# link whether or not D-27 exists yet (forward-reference allowed).
_D27_REF_RE = re.compile(r"\bD-27\b|test[- ]?spec|đặc tả test", re.IGNORECASE)
# Words that signal a stated test technique/approach in a scope-area row. English
# canonical + VI; matched case-insensitively. Presence-only — the LLM judges whether
# the named technique actually fits the area (that judgment is not deterministic).
_TECHNIQUE_HINTS = (
    "unit", "integration", "e2e", "system", "regression", "performance",
    "security", "decision-table", "decision table", "boundary", "equivalence",
    "smoke", "acceptance", "manual", "spot-check", "spot check", "tdd",
    "test", "kiểm thử", "kịch bản", "phương pháp", "đối chiếu", "assert",
    "sanity", "fixture", "snapshot",
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _inscope_rows(content: str) -> list[list[str]]:
    """Data rows of the In-Scope area table (B9-4 input).

    Locate the level-2 Test Scope section, slice from the In-Scope subsection
    heading to the Out-of-Scope heading (or section end), then parse the table out
    of that slice via the shared parser (wrapped in a synthetic level-2 heading so
    the language-aware ``parse_table`` can resolve it). Falls back to the whole Test
    Scope body when there is no In-Scope subsection heading (a flat table directly
    under ## Test Scope) — but still cuts at Out-of-Scope so out-rows never leak in.
    """
    m = find_section(content, *TESTSCOPE_LABELS)
    if not m:
        return []
    body = section_body(content, m)
    head = _INSCOPE_HEAD_RE.search(body)
    start = head.end() if head else 0
    out = _OUTSCOPE_HEAD_RE.search(body, start)
    slice_text = body[start:out.start()] if out else body[start:]
    return parse_table("## In Scope\n" + slice_text, "In Scope")


def schedule_dates(content: str) -> list[str]:
    """Every ISO date inside the Schedule section (de-duplicated, source order)."""
    m = find_section(content, *SCHEDULE_LABELS)
    if not m:
        return []
    return list(dict.fromkeys(_DATE_RE.findall(section_body(content, m))))


def schedule_is_provisional(content: str) -> bool:
    """True if the Schedule section openly flags its dates as not-yet-grounded.

    When the plan itself says the timeline is an assumption / TBD / will be
    confirmed, the dates are not a fabrication — B9-1 is satisfied without each
    date needing a source. Checked only within the Schedule section so a stray
    'TBD' in an unrelated table (e.g. an Assignee column) does not mask real
    fabricated dates elsewhere."""
    m = find_section(content, *SCHEDULE_LABELS)
    if not m:
        return False
    body = section_body(content, m).lower()
    return any(marker in body for marker in _PROVISIONAL_MARKERS)


def find_fabricated_dates(content: str, source_corpus: str) -> list[str]:
    """Schedule dates grounded in NEITHER a source doc NOR a provisional marker (B9-1).

    A date that also appears verbatim in a supplied source is grounded. If the
    Schedule section flags itself provisional, NONE of its dates are fabrications.
    With no sources supplied AND no provisional marker, every concrete date is an
    ungrounded candidate — surfaced, not silently passed (an invented timeline is
    the failure mode)."""
    if schedule_is_provisional(content):
        return []
    dates = schedule_dates(content)
    if not dates:
        return []
    hay = source_corpus  # exact-date substring; dates are unambiguous tokens
    return [d for d in dates if d not in hay]


def find_technique_gaps(content: str) -> list[str]:
    """In-scope area rows that state no test technique and no D-27 hand-off (B9-4).

    The In-Scope table's first column is the scope area; a later column should name
    the test focus/approach. A row whose cells (beyond the area name) mention no
    technique hint AND no D-27/test-spec reference is a gap — the area has no stated
    approach. Returns the area names. Whole-row text (beyond col 0) is scanned, so a
    2-column 'Area | Focus' and a 3-column table both work.

    The D-27 hand-off is checked PER ROW, not globally: a single D-27 mention
    elsewhere in the plan must NOT satisfy every area's approach (that would make
    B9-4 toothless — the failure mode is precisely an area with no stated technique
    that hides behind one document-wide test-spec reference). Each area earns its
    pass by naming a technique OR linking D-27 in its own row."""
    rows = _inscope_rows(content)
    gaps: list[str] = []
    for cells in rows:
        if not cells or not cells[0].strip():
            continue
        area = cells[0].strip()
        # Evidence must be in the row's OTHER cells (col 0, the area name, is excluded
        # so an area literally called "Unit testing" is not self-satisfying).
        row_rest = " ".join(cells[1:])
        has_technique = any(h in row_rest.lower() for h in _TECHNIQUE_HINTS)
        has_link = bool(_D27_REF_RE.search(row_rest))
        if not has_technique and not has_link:
            gaps.append(area)
    return gaps


def check(plan_path: str, sources: list[str] | None = None) -> dict:
    content = _read(plan_path)
    source_corpus = "\n".join(_read(s) for s in (sources or []))
    # "grounded" = at least one source was SUPPLIED to ground dates against. Without
    # sources B9-1 can still flag concrete, non-provisional dates (they are
    # ungrounded by definition), but the result records that no corpus backed them.
    grounded = bool(sources)

    fabricated = find_fabricated_dates(content, source_corpus)
    technique_gaps = find_technique_gaps(content)

    issues: list[dict] = []
    for d in fabricated:
        issues.append({
            "type": "FABRICATED_SCHEDULE",
            "message": f"schedule date '{d}' is grounded in no supplied source and the schedule is not marked provisional (ASSUMPTION/ADR/pending) — ground it or mark it (B9-1)",
            "date": d,
            "auto_fixable": False,
        })
    for area in technique_gaps:
        issues.append({
            "type": "TECHNIQUE_GAP",
            "message": f"in-scope area '{area}' states no test technique/approach and no D-27 hand-off — each scope area needs a stated approach linked to D-27 (B9-4)",
            "area": area,
            "auto_fixable": False,
        })

    checked = [
        "schedule dates grounded in a source or marked provisional (no fabricated timeline, B9-1)",
        "each in-scope area states a test technique / links D-27 (B9-4)",
    ]
    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether each risk's likelihood/impact is realistic + USER-confirmed (B9-2, domain decision — ASK)",
            "whether the named technique actually fits the area (semantic review, Stage 4b)",
            "whether in/out-scope was confirmed with the user before generation (B9-3, ASK-before-generate)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "grounded": grounded,
        "schedule_provisional": schedule_is_provisional(content),
        "fabricated_dates": fabricated,
        "technique_gaps": technique_gaps,
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-26 test plan grounding: no fabricated schedule (B9-1), technique-per-scope-area → D-27 (B9-4)."
    )
    ap.add_argument("plan", help="Path to the D-26 test plan document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--sources", help="Comma-separated source docs whose dates ground the schedule (D-02/D-06/decision-log)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    plan = Path(_resolve(args.plan))
    if not plan.exists():
        print(json.dumps({
            "error": f"Test plan not found: {plan}",
            "suggestion": "Run 'hbc-create-test-plan' first to generate D-26.",
        }, ensure_ascii=False))
        return 2

    # Resolve + drop sources that don't exist (a missing source must not silently
    # turn a grounded date into a fabrication false-positive). A supplied source
    # that is missing is a loud arg error, not a silent skip.
    sources: list[str] | None = None
    if args.sources:
        sources = [_resolve(s.strip()) for s in args.sources.split(",") if s.strip()]
        for s in sources:
            if not Path(s).is_file():
                print(json.dumps({"error": f"--sources file not found: {s}", "valid": False}, ensure_ascii=False))
                return 2

    try:
        result = check(str(plan), sources)
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
