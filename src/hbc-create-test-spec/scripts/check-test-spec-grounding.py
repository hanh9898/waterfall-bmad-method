#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Reconcile a D-27 Test Specification against the real schema + code (T3.3).

ADVISORY, not a hard inter-doc gate: the blocking cross-document gate is the
readiness gate (`hbc-check-implementation-readiness` [IR]) and the Phase-2 gate.
The structural validator (`validate-test-spec.py`) checks ids/sections/fields and
the facet metric (`check-facet-coverage.py`) checks per-facet TC coverage; this
script adds the three grounding-to-reality checks neither covers, each tied to a
[TS] DoD box:

  - MODEL_DRIFT (B3-7) — when code exists, reconcile the entities the test cases
    talk about against the REAL models. Reuses the shared `model_drift`:
    `design_only` = a model the D-19 design declares (physical `_name`) but code
    never defines — any TC that asserts behavior on it is testing a phantom
    (the RCA drift: design moved to Request+Snapshot, code stayed on the old model);
    `code_only` = a persistent model in code D-19 never declares. Every divergence
    is logged so the author reconciles the TCs against real behavior and warns on
    wrong assumptions. STRUCTURAL set-comparison only — whether a TC's *assertion*
    matches real behavior is the LLM reconcile judgment (Stage 3a).
  - TESTDATA_UNGROUNDED (B3-2) — a "Test Data" Input value that names a model field
    / entity token (dotted `model.field`) absent from BOTH D-19 and code is an
    invented fixture value, surfaced so test data is grounded in the real schema.
    Presence-only: whether a grounded value is *realistic* stays LLM judgment.
  - SANITY_MISSING (B3-1) — a "sensitive" TC that must FAIL on a business branch
    (severity Critical, or a branch keyword like idempotent/overwrite/snapshot/
    rollback/race) but whose steps carry no anti-false-green sanity step (a step
    that proves the fixture activates the branch — e.g. asserts the snapshot value
    differs from the generate-lines default). Surfaced, never auto-failed — whether
    a given TC truly needs a sanity step is judgment.

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
        iter_tc_blocks,
        model_drift,
        tc_field,
        verdict,
    )
except Exception as exc:  # noqa: BLE001 — any import failure is a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# Transient/derived code that is not a persistent data model — excluded so a
# wizard/test/controller never reads as a model the design must declare (mirrors
# the ER consistency check so the two grounding scripts agree on what "the models"
# are).
_NON_MODEL_PARTS = {"wizard", "wizards", "test", "tests", "controllers", "migrations"}
# A dotted identifier that looks like an Odoo model / model.field token in a Test
# Data Input cell (e.g. `resource.plan.request` or `project_member.effort_ratio`).
# At least two dotted/underscored segments so a bare word ("draft", "HuanTV") is
# never treated as a schema token.
_DOTTED_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+\b")
# Branch keywords (English + configured VI; NO hardcoded Japanese) that mark a TC as
# a "sensitive" branch that must demonstrably FAIL when the branch is not active —
# the anti-false-green class (T2.9). Matched case-insensitively in the TC body.
_BRANCH_HINTS = (
    "idempotent", "overwrite", "snapshot", "rollback", "race", "concurrent",
    "tamper", "lock", "terminal", "guard", "immutable", "all-or-nothing",
    "ghi đè", "bất biến", "khóa", "đồng thời", "rollback", "nguyên tử",
)
# Tokens that signal a TC step is an anti-false-green sanity check — it proves the
# fixture activates the branch (e.g. value ≠ default, "xanh giả", differs-from-default).
# Kept HIGH-SIGNAL: a loose token like a bare "khác"/"≠" would let almost any TC mask
# a real missing sanity step (the masking failure mode), so only explicit anti-false-
# green phrasings count. English canonical + configured VI; NO hardcoded Japanese.
_SANITY_HINTS = (
    "sanity", "anti-false-green", "false-green", "xanh giả", "phi-mặc-định",
    "≠ default", "≠ mặc định", "khác mặc định", "khác default", "differs-from-default",
    "differ from default", "non-default", "không phải mặc định", "phi mặc định",
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _iter_code_files(code_dir: str):
    base = Path(code_dir)
    for p in sorted(base.rglob("*.py")):
        # Exclude on the path RELATIVE to code_dir, never the absolute path — else a
        # project checked out under e.g. C:\...\tests\... would silently drop every
        # model and report a false-green grounding pass.
        rel = p.relative_to(base)
        if {part.lower() for part in rel.parts} & _NON_MODEL_PARTS:
            continue
        yield p


def testdata_tokens(d27_text: str) -> set[str]:
    """Dotted model/field tokens that appear in any TC's Test Data Input cell.

    Restricted to the **Test Data** block of each TC (the fixture values), not the
    whole TC body, so prose like "verify hash" never reads as a fixture token. A
    Test-Data table row's FIRST cell is the Input name; we scan the whole row text
    for dotted tokens (the value column often names `model.field`)."""
    tokens: set[str] = set()
    for block in iter_tc_blocks(d27_text):
        # Slice the Test Data subsection out of the block: from the **Test Data:**
        # marker to the next **Bold:** field or end.
        m = re.search(r"\*\*Test Data:?\*\*(.*?)(?=\n\s*\*\*[A-Z]|\Z)", block, re.DOTALL)
        if not m:
            continue
        for line in m.group(1).splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            tokens.update(_DOTTED_TOKEN_RE.findall(s.lower()))
    return tokens


def ungrounded_testdata(d27_text: str, grounding_corpus: str) -> list[str]:
    """Test-Data dotted tokens present in NEITHER D-19 nor code (B3-2).

    A fixture value that names a `model.field` no schema source knows about is an
    invented value. Returns the sorted tokens. With no grounding corpus supplied the
    check is skipped (the caller records `grounded_schema: false`)."""
    if not grounding_corpus.strip():
        return []
    hay = grounding_corpus.lower()
    out: list[str] = []
    for tok in sorted(testdata_tokens(d27_text)):
        # whole-token, dotted/underscored tolerant (a design may write `project.member`
        # where code writes `project_member`).
        forms = {tok, tok.replace(".", "_"), tok.replace("_", ".")}
        if not any(re.search(r"(?<![\w.])" + re.escape(f) + r"(?![\w.])", hay) for f in forms):
            out.append(tok)
    return out


def sanity_gaps(d27_text: str) -> list[dict]:
    """Sensitive TCs with no anti-false-green sanity step (B3-1).

    A TC is "sensitive" when it must demonstrably FAIL on a business branch: it is
    **Critical** severity, OR it names a branch keyword (idempotent/overwrite/
    snapshot/rollback/race…) AND is **High** severity. (A Medium/Low TC that merely
    mentions a branch word in passing is excluded — keeping the signal HIGH so the
    advisory list stays actionable rather than flagging half the document.) A
    sensitive TC needs a sanity step proving the fixture actually activates the
    branch; without one a green run is not evidence. Returns ``[{req, reason}]``.
    """
    gaps: list[dict] = []
    for block in iter_tc_blocks(d27_text):
        body = block.lower()
        sev = (tc_field(block, "Severity") or "").lower()
        is_critical = "critical" in sev
        is_high = "high" in sev
        branch = next((h for h in _BRANCH_HINTS if h in body), None)
        # Critical → always sensitive; a branch keyword only counts at High+ severity.
        sensitive = is_critical or (branch and (is_high or is_critical))
        if not sensitive:
            continue
        has_sanity = any(h in body for h in _SANITY_HINTS)
        if has_sanity:
            continue
        req = tc_field(block, "REQ ID") or "?"
        reason = "Critical severity" if is_critical else f"branch '{branch}'"
        gaps.append({"req": req.strip(), "reason": reason})
    return gaps


def check(d27_path: str, d19_path: str | None = None,
          code_dir: str | None = None) -> dict:
    text = _read(d27_path)
    d19_text = _read(d19_path) if d19_path else ""
    code_text = ""
    if code_dir:
        code_text = "\n".join(_read(str(p)) for p in _iter_code_files(code_dir))

    issues: list[dict] = []
    checked: list[str] = []

    # --- MODEL_DRIFT (B3-7): reconcile TC entities vs real code, when code exists ---
    drift = {"design_only": [], "code_only": [], "drift": False}
    if d19_path and code_dir:
        drift = model_drift(d19_text, code_text)
        checked.append("D-19 model names the TCs exercise are grounded against the real code models (B3-7)")
        for tok in drift["design_only"]:
            issues.append({
                "type": "MODEL_DRIFT_DESIGN_ONLY",
                "message": f"model '{tok}' is declared in D-19 but no matching model exists in code — "
                           "any TC asserting behavior on it tests a phantom; reconcile the TC against "
                           "real behavior (planned-not-built, or stale design) (B3-7)",
                "token": tok,
                "auto_fixable": False,
            })
        for tok in drift["code_only"]:
            issues.append({
                "type": "MODEL_DRIFT_CODE_ONLY",
                "message": f"model '{tok}' exists in code but D-19 never declares it — a TC may be "
                           "missing for it, or the assumption about the schema is wrong (B3-7)",
                "token": tok,
                "auto_fixable": False,
            })

    # --- TESTDATA_UNGROUNDED (B3-2): fixture tokens vs D-19 + code schema ---
    grounding_corpus = "\n".join([d19_text, code_text])
    grounded_schema = bool(grounding_corpus.strip())
    ungrounded: list[str] = []
    if grounded_schema:
        checked.append("Test-Data model/field tokens grounded in D-19 or code schema (B3-2)")
        ungrounded = ungrounded_testdata(text, grounding_corpus)
        for tok in ungrounded:
            issues.append({
                "type": "TESTDATA_UNGROUNDED",
                "message": f"Test-Data token '{tok}' names a model/field absent from D-19 and code — "
                           "ground the fixture value in the real schema or correct it (B3-2)",
                "token": tok,
                "auto_fixable": False,
            })

    # --- SANITY_MISSING (B3-1): sensitive TC with no anti-false-green sanity step ---
    checked.append("sensitive TCs (Critical / branch) carry an anti-false-green sanity cue (B3-1)")
    gaps = sanity_gaps(text)
    for g in gaps:
        issues.append({
            "type": "SANITY_MISSING",
            "message": f"sensitive TC for {g['req']} ({g['reason']}) has no sanity step proving the "
                       "fixture activates the branch — a green run would not be evidence (B3-1)",
            "req": g["req"],
            "auto_fixable": False,
        })

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether a TC's ASSERTION matches real code behavior (B3-7 — LLM reconcile, Stage 3a)",
            "whether each TC maps to the RIGHT technique↔source (B3-5 — semantic review, Stage 4b)",
            "whether critical-path severity is USER-confirmed (B3-6 — domain decision, ASK)",
            "whether facet + edge in/out-scope was confirmed per-REQ before generation (B3-4, ASK-before-generate)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "grounded_code": bool(code_dir),
        "grounded_schema": grounded_schema,
        "model_drift": drift,
        "ungrounded_testdata": ungrounded,
        "sanity_gaps": gaps,
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-27 test spec against real schema + code (B3-1/B3-2/B3-7)."
    )
    ap.add_argument("d27", help="Path to the D-27 test specification document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--d19", help="Path to D-19 database design (physical model names for grounding)")
    ap.add_argument("--code-dir", help="Code dir whose Odoo _name models D-27 TCs are reconciled against (B3-7)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    d27 = Path(_resolve(args.d27))
    if not d27.exists():
        print(json.dumps({
            "error": f"D-27 not found: {d27}",
            "suggestion": "Run 'hbc-create-test-spec' first to generate D-27.",
        }, ensure_ascii=False))
        return 2

    d19 = _resolve(args.d19) if args.d19 else None
    # A supplied-but-missing --d19 must be a loud arg error, not a silent empty corpus
    # that would false-green the grounding.
    if d19 is not None and not Path(d19).is_file():
        print(json.dumps({"error": f"--d19 not found: {d19}", "valid": False}, ensure_ascii=False))
        return 2

    code_dir = _resolve(args.code_dir) if args.code_dir else None
    if code_dir is not None and not Path(code_dir).is_dir():
        print(json.dumps({"error": f"--code-dir is not a directory: {code_dir}", "valid": False}, ensure_ascii=False))
        return 2

    try:
        result = check(str(d27), d19, code_dir)
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "valid": False}, ensure_ascii=False))
            return 2
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
