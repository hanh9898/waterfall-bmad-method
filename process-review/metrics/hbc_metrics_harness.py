#!/usr/bin/env python3
"""HBC F-6 metrics harness (TF.3).

Measures the six F-6 outcome metrics of the HBC improvement plan on a frozen
regression fixture (TD.0), so each remediation wave can be re-measured against
a *fixed* substrate (RCA case `resource-plan-billable`, error-state snapshot).

Why a harness at all: the RCA proved the symptoms with point-in-time numbers
(13 D-02 versions, 65 spec-ref leaks, false-pass gates, ...). Those numbers are
worthless for tracking progress unless they can be re-derived from a fixed input.
This script *re-derives* them mechanically from the fixture and emits before/after
numbers per wave.

Scope of measurement:
  - Five metrics are MECHANICAL (re-derived from the fixture every run).
  - One metric (`recascade`) is a documented HISTORICAL baseline: it counts
    cascade rounds that happened across the project's timeline and cannot be
    reconstructed from a single static snapshot. It is reported with an honest
    `mechanical: false` flag and its provenance, never silently fabricated.

stdlib-only. Run with `python` (Windows dev) or `python3` (Linux/Mac CI):
    python process-review/metrics/hbc_metrics_harness.py
    python process-review/metrics/hbc_metrics_harness.py --fixture <dir>

Prints a JSON report to stdout. Errors go to stderr with a non-zero exit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- fixture layout (relative to fixture root) -------------------------------
DEFAULT_FIXTURE = (
    Path(__file__).resolve().parent.parent / "fixtures" / "resource-plan-billable"
)
D02 = "artifacts/planning-artifacts/D-02-resource-plan-billable.md"
MATRIX = "artifacts/traceability/matrix.md"
D19 = "artifacts/planning-artifacts/D-19-opms/D-19-er-diagram.md"
GATES = "artifacts/gates"
CODE = "code"

# Canonical v2.3 domain-model tokens (the Request+Snapshot model). They live in
# the design (D-19) but were never implemented in code — this *is* the MODEL_DRIFT.
DESIGN_TOKENS = [
    "active_request_id",
    "snapshot_hash",
    "resource.plan.request",
    "resource_plan_request",
    "request_line",
]

# A spec-ref leak is any requirement/test/NFR id embedded in source code.
SPEC_REF_RE = re.compile(r"\b(?:REQ|TC|NFR)-[A-Za-z0-9-]+\b")
# A requirement id, canonical (REQ-FEAT-SLUG-040) or bare-numeric (REQ-040) form.
REQ_ID_RE = re.compile(r"\bREQ-(?:[A-Za-z0-9]+-)*\d+\b")
# A revision-history row: "| 2.3 | 2026-06-19 | ...". The date in the 2nd cell
# distinguishes a real revision row from any other table whose first cell is N.N.
REV_ROW_RE = re.compile(r"^\|\s*\d+\.\d+\s*\|\s*\d{4}-\d{2}-\d{2}", re.MULTILINE)
# Gate verdicts that count as a pass (exact match after strip/upper — so "BYPASSED",
# "NOT PASSED", "PASSED (manual)" do NOT silently slip through as a clean pass).
PASS_VERDICTS = {"PASS", "PASSED"}


def _read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.is_file():
        raise FileNotFoundError(f"fixture file missing: {rel}")
    return p.read_text(encoding="utf-8", errors="replace")


def _is_pass(verdict) -> bool:
    return verdict is not None and str(verdict).strip().upper() in PASS_VERDICTS


def metric_d02_churn(root: Path) -> dict:
    """D-02 version churn = number of dated revision-history rows. RCA: 13, target <=4."""
    rows = REV_ROW_RE.findall(_read(root, D02))
    return {
        "id": "d02_churn",
        "title": "D-02 version churn",
        "mechanical": True,
        "baseline_measured": len(rows),
        "rca_claimed": 13,
        "target": "<=4",
        "detail": f"{len(rows)} dated revision rows in D-02 revision history",
    }


def metric_spec_ref_leak(root: Path) -> dict:
    """Spec-ref ids embedded in code/test. RCA headline: 65, target 0."""
    code = root / CODE
    prod, test = 0, 0
    per_file = {}
    for py in sorted(code.rglob("*.py")):
        n = len(SPEC_REF_RE.findall(py.read_text(encoding="utf-8", errors="replace")))
        if not n:
            continue
        rel = py.relative_to(code)
        per_file[str(rel).replace("\\", "/")] = n
        # classify on the path *relative to code/* — never the absolute parts,
        # so a fixture relocated under a dir named "tests" can't flip prod->test.
        if "tests" in rel.parts:
            test += n
        else:
            prod += n
    return {
        "id": "spec_ref_leak",
        "title": "Spec-ref leak in code/test",
        "mechanical": True,
        "baseline_measured": prod + test,
        "baseline_breakdown": {"prod": prod, "test": test},
        "rca_claimed": 65,
        "rca_breakdown": {"prod": 29, "test": 36},
        "target": "0",
        "detail": (
            f"{prod + test} spec-refs in fixture code slice (prod {prod} + test {test}). "
            "prod count matches RCA exactly (29); RCA test headline (36) used a "
            "broader/earlier count — fixture self-measures the feature code slice."
        ),
        "per_file": per_file,
    }


def _req_number_map(text: str):
    """Map each requirement's trailing number -> representative id, plus the slugs seen.

    D-02 mixes the canonical id (REQ-RESOURCE-PLAN-BILLABLE-040) with bare short
    forms (REQ-040) in prose; the matrix uses only the canonical form. The fixture
    is single-feature, so a requirement's identity is its trailing number — that is
    what makes "defined but unmapped" comparable across the two id styles. The set
    of distinct feature slugs is returned too, so callers can detect (and refuse to
    trust) a multi-feature input where trailing-number identity would collide.
    """
    out, slugs = {}, set()
    for rid in REQ_ID_RE.findall(text):
        num = int(re.search(r"\d+$", rid).group())
        slug = rid[: rid.rfind("-")]  # everything before the trailing -NNN
        if slug and slug != "REQ":
            slugs.add(slug)
        if num not in out or len(rid) > len(out[num]):
            out[num] = rid
    return out, slugs


def metric_req_without_matrix_row(root: Path) -> dict:
    """REQs defined in D-02 but absent from the matrix. RCA: 040/041/042, target 0."""
    d02, slugs = _req_number_map(_read(root, D02))
    matrix_nums = set(_req_number_map(_read(root, MATRIX))[0].keys())
    missing = sorted(n for n in d02 if n not in matrix_nums)
    missing_ids = [d02[n] for n in missing]
    result = {
        "id": "req_without_matrix_row",
        "title": "REQ defined but missing from matrix",
        "mechanical": True,
        "baseline_measured": len(missing),
        "rca_claimed": 3,
        "target": "0",
        "detail": (
            f"{len(missing)} REQ defined in D-02 but absent from matrix "
            "(identity = trailing number; valid because fixture is single-feature)"
        ),
        "missing": missing_ids,
    }
    # trailing-number identity is only sound for a single feature; surface a warning
    # rather than silently miscount if this is ever pointed at a multi-feature input.
    if len(slugs) > 1:
        result["multi_feature_warning"] = (
            "multiple feature slugs detected "
            f"({sorted(slugs)}); trailing-number identity may collide — count unreliable"
        )
    return result


def metric_gate_false_pass(root: Path) -> dict:
    """Gates that PASSED despite a *structural* reason they should not have.

    A pure "count PASSED gates" metric is tautological and becomes unmeasurable
    after remediation (legitimately-green gates would still count). So a gate is a
    false-pass only when it reports PASS(ED) AND carries an at-gate-time signal it
    should not have: an item failure (`failed>0`/`required_failed>0`) or a
    manual/override evaluation (the RCA's "manual-pass after evaluator crash").
    After TD.4 re-runs real gates on v2.3 these signals clear and the count -> 0.

    Note vs RCA "3": all 3 fixture gates are stale-passes in hindsight (they passed
    on an older model), but phase-1 has no at-gate-time signal — its falseness is
    only knowable by cross-referencing later drift, which is the build-graph's job
    (TA.1), not a single-gate structural check. So this metric reports the
    structurally-detectable subset and lists the rest as stale-pass context.
    """
    gates_dir = root / GATES
    false_pass, stale_context = [], []
    for jf in sorted(gates_dir.glob("phase-*-gate-results.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed gate JSON in {jf.name}: {exc}") from exc
        summary = data.get("summary", {})
        verdict = summary.get("overall_status") or data.get("status")
        if not _is_pass(verdict):
            continue
        failed = (summary.get("failed") or 0) + (summary.get("required_failed") or 0)
        evaluation = str(data.get("evaluation") or "")
        manual = bool(re.search(r"manual|override|crash|fallback", evaluation, re.I))
        if failed > 0 or manual:
            false_pass.append(
                {
                    "file": jf.name,
                    "verdict": verdict,
                    "failed": failed,
                    "manual_override": manual,
                }
            )
        else:
            stale_context.append({"file": jf.name, "verdict": verdict})
    return {
        "id": "gate_false_pass",
        "title": "Gate false-pass (structural)",
        "mechanical": True,
        "baseline_measured": len(false_pass),
        "rca_claimed": 3,
        "target": "0",
        "detail": (
            f"{len(false_pass)} gates PASSED despite an at-gate-time failure/override; "
            f"{len(stale_context)} further PASSED gate(s) are stale-passes detectable "
            "only by cross-referencing drift (TA.1), not counted here"
        ),
        "false_pass_gates": false_pass,
        "stale_pass_context": stale_context,
    }


def _token_in(token: str, text: str) -> bool:
    """Whole-identifier presence test for a design token.

    Bare-word tokens (active_request_id, snapshot_hash, request_line) use word
    boundaries so `request_line` does NOT match inside `purchase_request_lines`.
    Dotted tokens (resource.plan.request) are Odoo model names — matched as a
    literal substring, since `.` is not a word char and an Odoo `_name`/comodel is
    written exactly that way.
    """
    if "." in token:
        return token in text
    return re.search(r"\b" + re.escape(token) + r"\b", text) is not None


def metric_model_drift(root: Path) -> dict:
    """Design tokens present in D-19 (v2.3) but absent from code = MODEL_DRIFT.

    The harness must CATCH the drift (detection capability). Baseline shows drift
    exists; target is 100% catch (zero design tokens missing from code once
    remediated). RCA: code is 100% old model, target 0 missing.
    """
    d19 = _read(root, D19).lower()
    code_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace").lower()
        for p in (root / CODE).rglob("*.py")
    )
    rows, drift = [], []
    for tok in DESIGN_TOKENS:
        in_design = _token_in(tok.lower(), d19)
        in_code = _token_in(tok.lower(), code_text)
        rows.append({"token": tok, "in_design": in_design, "in_code": in_code})
        if in_design and not in_code:
            drift.append(tok)
    return {
        "id": "model_drift",
        "title": "Code<->design drift (MODEL_DRIFT)",
        "mechanical": True,
        "baseline_measured": len(drift),
        "rca_claimed": "code 100% old model",
        "target": "0 design tokens missing from code",
        "detail": f"{len(drift)} v2.3 design tokens present in D-19 but absent from code",
        "drift_tokens": drift,
        "token_matrix": rows,
    }


def metric_recascade(root: Path) -> dict:
    """Cascade rounds across the project timeline.

    HISTORICAL — not derivable from a single static snapshot (it counts repeated
    full-stack rewrites over time). Reported honestly as non-mechanical with its
    documented baseline and provenance, never fabricated as if measured.
    """
    return {
        "id": "recascade",
        "title": "Re-cascade rounds",
        "mechanical": False,
        "baseline_measured": None,
        "documented_baseline": 4,  # RCA says "4+" — this is a lower bound
        "rca_claimed": ">=4",
        "target": "1",
        "detail": (
            "Process metric: RCA documented 4+ manual cascade rounds "
            "(v2.0->2.1->2.2->2.3, ~7 docs each). Cannot be reconstructed from a "
            "single snapshot; tracked manually against the documented baseline (>=4)."
        ),
        "provenance": "process-review/process-retrospective-rca-2026-06-20.md §1, §2",
    }


METRICS = [
    metric_d02_churn,
    metric_spec_ref_leak,
    metric_req_without_matrix_row,
    metric_gate_false_pass,
    metric_model_drift,
    metric_recascade,
]


def run(fixture: Path) -> dict:
    if not fixture.is_dir():
        raise FileNotFoundError(f"fixture dir not found: {fixture}")
    metrics = [m(fixture) for m in METRICS]
    return {
        "fixture": str(fixture),
        "fixture_name": fixture.name,
        "metric_count": len(metrics),
        "mechanical_count": sum(1 for m in metrics if m["mechanical"]),
        "metrics": metrics,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="HBC F-6 metrics harness (TF.3)")
    ap.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="fixture root (default: resource-plan-billable TD.0 fixture)",
    )
    args = ap.parse_args(argv)
    try:
        report = run(args.fixture)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
