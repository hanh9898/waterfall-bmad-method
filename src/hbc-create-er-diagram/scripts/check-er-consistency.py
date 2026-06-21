#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Reconcile a D-19 Database Design (ER) against its requirements + the real code (T3.2).

ADVISORY, not a hard inter-doc gate: the blocking cross-document gate is the
readiness gate (`hbc-check-implementation-readiness` [IR]) and the Phase-2 gate.
Mermaid *rendering* is a separate validator (`validate-mermaid-er.py` /
`npm run check:mermaid`); coarse entity↔PRD coverage is `check-entity-coverage.py`.
This script adds the four structure checks those do not cover, each tied to an
[ERD] DoD box:

  - ENTITY_REQ (B2-2) — every entity/relationship should trace to ≥1 REQ. A
    Mermaid block that references NO REQ id is surfaced (the entity↔REQ
    traceability the DoD requires). And a REQ defined in --sources (D-02 + D-06)
    referenced NOWHERE in D-19 is an uncovered-REQ facet (B2-5 conceptual tier
    reconciles against REQ *and* D-06, not just the PRD). Identity = the shared
    trailing-number REQ scheme so canonical (REQ-FEAT-040) and bare (REQ-040) ids
    reconcile.
  - SCHEMA_DRIFT (B2-7) — ground the design against the REAL DB models. Reuses the
    shared `model_drift`: `design_only` = a model the D-19 declares (physical
    `_name`) but code never defines (the RCA drift — design moved on, code didn't);
    `code_only` = a persistent model in code the design never mentions. EVERY
    divergence is logged (the DoD's "log mọi lệch"). STRUCTURAL set-comparison only
    — whether a divergence is intended (planned-not-built vs stale-design) is the
    grounding judgment, Stage 2b.
  - CHURN (B2-9) — revision-history row count (order-robust: matches both
    `version | date` and `date | version`). `high_churn` (> threshold) is the cue
    to freeze the model (maturity=exploratory / run [DSC]) instead of bumping the
    version every edit. Uses a LOCAL order-robust revision-row regex, NOT the shared
    `churn_assessment` (that one assumes version-first rows; D-19's HBLab template
    is date-first, so a date-first table would falsely read as zero churn).
  - ONDELETE (B2-3) — surface FK lines that declare an ondelete behavior vs those
    that do not, so an unrationalized CASCADE/RESTRICT/SET NULL is visible. The
    DoD wants ondelete ASKED + rationale RECORDED; whether the chosen behavior is
    *correct* and whether the prose carries a rationale is judgment (Stage 3 / 4b)
    — this only counts the structural signal.

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
        REQ_ID_RE,
        churn_assessment,
        model_drift,
        req_num_map,
        verdict,
    )
except Exception as exc:  # noqa: BLE001 — any import failure is a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
_DIAGRAM_TYPE_RE = re.compile(r"^\s*(erDiagram)\b", re.MULTILINE)
DEFAULT_CHURN_THRESHOLD = 4

# A markdown table cell / prose fragment declaring an FK relationship. Used only to
# count "FK lines" vs "FK lines that also name an ondelete behavior" — a structural
# cue for B2-3 (unrationalized ondelete), never a correctness check.
_FK_LINE_RE = re.compile(r"\bFK\b", re.IGNORECASE)
# ON DELETE behaviors, tolerant of the SQL `ON DELETE CASCADE` and the Odoo
# `ondelete='cascade'` spellings (and the underscore/space variants).
_ONDELETE_RE = re.compile(
    r"\b(?:on[\s_]*delete|ondelete)\b\s*[:=]?\s*['\"]?\s*"
    r"(cascade|restrict|set[\s_]*null|set[\s_]*default|no[\s_]*action)",
    re.IGNORECASE,
)
# Transient/derived code that is not a persistent data model — excluded so a
# wizard/test/controller never reads as a model the design must declare.
_NON_MODEL_PARTS = {"wizard", "wizards", "test", "tests", "controllers", "migrations"}


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _blocks(text: str) -> list[str]:
    return [m.group(1) for m in MERMAID_BLOCK_RE.finditer(text)]


def _er_blocks(text: str) -> list[tuple[int, str]]:
    """(index, block-body) for every Mermaid block that is an erDiagram."""
    return [(i, b) for i, b in enumerate(_blocks(text)) if _DIAGRAM_TYPE_RE.search(b)]


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


def phantom_entity_blocks(text: str) -> list[int]:
    """erDiagram blocks that reference NO requirement id — drawn but REQ-unbacked (B2-2)."""
    return [i for i, b in _er_blocks(text) if not REQ_ID_RE.search(b)]


def uncovered_reqs(d19_text: str, source_text: str) -> list[str]:
    """REQ ids defined in --sources (D-02 + D-06) but referenced NOWHERE in D-19 (B2-2/B2-5).

    Identity = trailing number (shared req_num_map). Multi-feature corpora make the
    trailing-number identity collide, so the caller is told (via `multi_feature`) when
    >1 feature slug appears and the count should not be trusted.
    """
    src_map, _ = req_num_map(source_text)
    d19_nums = set(req_num_map(d19_text)[0])
    return [src_map[n] for n in sorted(src_map) if n not in d19_nums]


def ondelete_signal(text: str) -> dict:
    """Count FK lines vs FK lines that also name an ondelete behavior (B2-3 cue).

    Scans the table-definition prose ONLY — Mermaid blocks are stripped first, since
    the ondelete behavior is recorded in the table rows, not the diagram (an `int x
    FK` attribute line inside an erDiagram never carries an ondelete and would just
    inflate the without-ondelete count). Structural only — whether a declared
    behavior is correct, or whether a rationale accompanies it, is judgment.
    """
    prose = MERMAID_BLOCK_RE.sub("", text)
    fk_lines = 0
    fk_with_ondelete = 0
    for line in prose.splitlines():
        if _FK_LINE_RE.search(line):
            fk_lines += 1
            if _ONDELETE_RE.search(line):
                fk_with_ondelete += 1
    return {"fk_lines": fk_lines, "fk_with_ondelete": fk_with_ondelete,
            "fk_without_ondelete": fk_lines - fk_with_ondelete}


def check(d19_path: str, sources: list[str] | None = None,
          code_dir: str | None = None,
          churn_threshold: int = DEFAULT_CHURN_THRESHOLD) -> dict:
    text = _read(d19_path)
    er_blocks = _er_blocks(text)

    issues: list[dict] = []
    checked: list[str] = []

    # --- ENTITY_REQ (B2-2): phantom entity blocks (no REQ) ---
    checked.append("every ER block references ≥1 requirement id (entity↔REQ traceability) (B2-2)")
    phantoms = phantom_entity_blocks(text)
    for idx in phantoms:
        issues.append({
            "type": "PHANTOM_ENTITY_BLOCK",
            "message": f"erDiagram block {idx} references no REQ id — its entities trace to no "
                       "requirement (cite the REQ each entity realizes, or record why it is structural-only)",
            "block": idx,
            "auto_fixable": False,
        })

    # --- ENTITY_REQ facet gap (B2-2/B2-5): REQ in sources but not in D-19 ---
    source_corpus = "\n".join(_read(s) for s in (sources or []))
    grounded_reqs = bool(source_corpus.strip())
    _, src_slugs = req_num_map(source_corpus) if grounded_reqs else ({}, set())
    multi_feature = len(src_slugs) > 1
    uncovered: list[str] = []
    if grounded_reqs:
        checked.append("every D-02/D-06 requirement appears somewhere in D-19 (REQ↔entity facet coverage) (B2-2/B2-5)")
        uncovered = uncovered_reqs(text, source_corpus)
        for rid in uncovered:
            issues.append({
                "type": "UNCOVERED_REQ",
                "message": f"requirement '{rid}' is defined in the source (D-02/D-06) but referenced nowhere "
                           "in D-19 (uncovered facet — model it, or record why it needs no schema)",
                "req": rid,
                "auto_fixable": False,
            })

    # --- SCHEMA_DRIFT (B2-7): model_drift design vs real code; log EVERY divergence ---
    drift = {"design_only": [], "code_only": [], "drift": False}
    if code_dir:
        code_text = "\n".join(_read(str(p)) for p in _iter_code_files(code_dir))
        drift = model_drift(text, code_text)
        checked.append("D-19 physical model names grounded against the real code models (log every divergence) (B2-7)")
        for tok in drift["design_only"]:
            issues.append({
                "type": "SCHEMA_DRIFT_DESIGN_ONLY",
                "message": f"model '{tok}' is declared in D-19 but no matching model exists in code "
                           "(planned-not-yet-built, or stale design — resolve and record in the grounding log)",
                "token": tok,
                "auto_fixable": False,
            })
        for tok in drift["code_only"]:
            issues.append({
                "type": "SCHEMA_DRIFT_CODE_ONLY",
                "message": f"model '{tok}' exists in code but D-19 never declares it "
                           "(undocumented model — add it to the design, or record why it is out of scope)",
                "token": tok,
                "auto_fixable": False,
            })

    # --- ONDELETE (B2-3): structural cue only, never an issue ---
    ondelete = ondelete_signal(text)
    checked.append("FK lines surfaced with/without an ondelete behavior (B2-3 cue; rationale is judgment)")

    # --- CHURN (B2-9): advisory, never an issue ---
    churn = churn_assessment(text, churn_threshold)
    checked.append("revision-history churn surfaced (B2-9 cue; high churn ⇒ freeze the model)")

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether each ondelete behavior is CORRECT and carries a rationale (B2-3 — Stage 3 ASK + 4b)",
            "whether a SCHEMA_DRIFT divergence is intended (planned) or stale (grounding judgment, Stage 2b)",
            "whether indexes are appropriate PROPOSALS (B2-4 — judgment, Stage 3)",
            "Mermaid render validity (validate-mermaid-er.py) and coarse entity↔PRD coverage (check-entity-coverage.py)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "er_block_count": len(er_blocks),
        "grounded_reqs": grounded_reqs,
        "grounded_code": bool(code_dir),
        "multi_feature_sources": multi_feature,
        "source_feature_slugs": sorted(src_slugs),
        "phantom_entity_blocks": phantoms,
        "uncovered_reqs": uncovered,
        "schema_drift": drift,
        "ondelete": ondelete,
        "churn": churn,
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-19 entities against requirements + real code models (B2-2/B2-3/B2-5/B2-7/B2-9)."
    )
    ap.add_argument("d19", help="Path to the D-19 database-design (ER) document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--sources", help="Comma-separated source docs (D-02 + D-06) for the REQ-coverage corpus")
    ap.add_argument("--code-dir", help="Code dir whose Odoo _name models D-19 must be grounded against (B2-7)")
    ap.add_argument("--churn-threshold", type=int, default=DEFAULT_CHURN_THRESHOLD,
                    help=f"Revision-row count above which churn is flagged (default {DEFAULT_CHURN_THRESHOLD})")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    d19 = Path(_resolve(args.d19))
    if not d19.exists():
        print(json.dumps({
            "error": f"D-19 not found: {d19}",
            "suggestion": "Run 'hbc-create-er-diagram' first to generate D-19.",
        }, ensure_ascii=False))
        return 2

    code_dir = _resolve(args.code_dir) if args.code_dir else None
    # A supplied-but-missing --code-dir would rglob to nothing and read as a clean
    # ungrounded pass — make it a loud arg error instead of a silent false-green.
    if code_dir is not None and not Path(code_dir).is_dir():
        print(json.dumps({"error": f"--code-dir is not a directory: {code_dir}", "valid": False}, ensure_ascii=False))
        return 2

    sources = [_resolve(s.strip()) for s in args.sources.split(",") if s.strip()] if args.sources else None
    if sources:
        missing = [s for s in sources if not Path(s).exists()]
        if missing:
            # A supplied-but-missing source would read as an empty corpus and silently
            # report every REQ as covered (false-green) — make it a loud arg error.
            print(json.dumps({"error": f"--sources not found: {missing}", "valid": False}, ensure_ascii=False))
            return 2

    try:
        result = check(str(d19), sources, code_dir, args.churn_threshold)
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
