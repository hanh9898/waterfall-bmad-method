#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Reconcile a D-03 Glossary against the ubiquitous language of the project (B11-2 / B11-3).

A glossary that lives apart from the code+design drifts into generic dictionary
prose. This check grounds it in the *real* domain vocabulary:

  - MISSING_FROM_GLOSSARY (B11-3) — an Odoo model declared in D-19 (physical
    ``_name``) or defined in code that the glossary never reflects anywhere.
    The DDD ubiquitous-language gap: the system speaks a name the glossary omits.
  - ORPHAN_TERM (B11-2) — a glossary term whose text appears in NONE of the
    source/design/code corpus: defined, but used nowhere. A candidate to drop or
    a sign the term is paraphrased elsewhere — surfaced for human review.

ADVISORY, not a hard inter-doc gate: cross-document consistency as a *blocking*
gate is the readiness gate's job (P-1, see semantic-review-rubric "Decision-scope
by location"). This script informs glossary *completeness* during creation; the
LLM still judges which prose terms are domain terms (that judgment is not
deterministic and stays in Stage 2). Structural set-comparison only.

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
        model_drift,
        parse_table,
        verdict,
    )
except Exception as exc:  # noqa: BLE001 — any import failure must be a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

TERMS_LABELS = ("Terms", "Thuật ngữ")

_CODE_GLOB = "*.py"
# Transient/derived code that is not a persistent data model — excluded so a
# wizard/test/controller never reads as a domain model the glossary must define.
_NON_MODEL_PARTS = {"wizard", "wizards", "test", "tests", "controllers", "migrations"}


def _iter_code_files(code_dir: str):
    base = Path(code_dir)
    for p in sorted(base.rglob(_CODE_GLOB)):
        # Exclude on the path RELATIVE to code_dir, never the absolute path — else a
        # project checked out under e.g. C:\...\tests\... would silently drop every
        # model and report a false-green B11-3 pass.
        rel = p.relative_to(base)
        if {part.lower() for part in rel.parts} & _NON_MODEL_PARTS:
            continue
        yield p


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def glossary_terms(content: str) -> list[str]:
    """Domain-term values (col 0) from the Terms table.

    Abbreviations are excluded from the orphan check: an abbreviation is, by
    definition, the short form OF a term — its "usage" is the expansion, so it
    legitimately may not appear verbatim in narrow source corpora and would only
    add noise. The MISSING check still scans the WHOLE glossary text (abbreviation
    definitions included), so a model token spelled out in an abbreviation entry
    still counts as reflected."""
    return [row[0].strip() for row in parse_table(content, *TERMS_LABELS)
            if row and row[0].strip()]


def code_model_names(code_dir: str) -> set[str]:
    """Every Odoo ``_name`` declared in persistent-model code under ``code_dir``.

    Reuses the shared ``model_drift`` extractor: with an empty design, ``code_only``
    is exactly the set of code ``_name``s (none can be "present" in nothing) — so
    code-name extraction stays in the single shared source of truth, not a fork."""
    code_text = "\n".join(_read(str(p)) for p in _iter_code_files(code_dir))
    return set(model_drift("", code_text)["code_only"])


def find_missing_from_glossary(glossary_text: str, design_text: str,
                               code_names: set[str]) -> list[str]:
    """Domain model tokens (D-19 physical ``_name`` + code ``_name``) absent from the
    glossary text (B11-3). Dotted/underscored-tolerant, whole-identifier — delegated
    to ``model_drift``: design tokens (+ code names as extra) not present in the
    glossary corpus is precisely its ``design_only``. (``model_drift`` also computes
    a ``code_only`` over the glossary prose; it is intentionally discarded here.)"""
    return model_drift(design_text, glossary_text, extra_tokens=code_names)["design_only"]


def find_orphan_terms(terms: list[str], corpus: str) -> list[str]:
    """Glossary terms whose text appears nowhere in the corpus (B11-2). Case-insensitive
    substring (lenient — a paraphrase containing the term is not an orphan).

    The corpus is the BUSINESS sources (D-02/D-06/project-context), not code or the
    design: glossary terms are human-language (often the document language), while code
    is English identifiers and the design uses physical names — comparing a human label
    against code would flag every term as a false orphan. So orphan detection runs only
    against the prose where the same vocabulary actually lives."""
    if not corpus.strip():
        return []
    hay = corpus.lower()
    return [t for t in terms if t.lower() not in hay]


def check(glossary_path: str, sources: list[str] | None = None,
          design_path: str | None = None, code_dir: str | None = None) -> dict:
    glossary_text = _read(glossary_path)
    terms = list(dict.fromkeys(glossary_terms(glossary_text)))  # dedupe, keep order

    design_text = _read(design_path) if design_path else ""
    code_names = code_model_names(code_dir) if code_dir else set()
    # "grounded" = a B11-3 input (design/code) was SUPPLIED — independent of whether
    # any model tokens were found, so an all-excluded code dir does not masquerade as
    # "nothing supplied".
    grounded = bool(design_path or code_dir)

    issues: list[dict] = []
    missing: list[str] = []
    orphans: list[str] = []
    checked: list[str] = []

    if grounded:
        missing = find_missing_from_glossary(glossary_text, design_text, code_names)
        checked.append("D-19/code domain models reflected in glossary (ubiquitous language, B11-3)")
        for tok in missing:
            issues.append({
                "type": "MISSING_FROM_GLOSSARY",
                "message": f"domain model '{tok}' is declared in the design/code but not reflected in the glossary (ubiquitous-language gap)",
                "token": tok,
                "auto_fixable": False,
            })

    # Orphan check: business sources only (see find_orphan_terms).
    source_corpus = "\n".join(_read(s) for s in (sources or []))
    if source_corpus.strip():
        orphans = find_orphan_terms(terms, source_corpus)
        checked.append("glossary terms appear in the business sources (no orphans, B11-2)")
        for term in orphans:
            issues.append({
                "type": "ORPHAN_TERM",
                "message": f"glossary term '{term}' is used in none of the source docs — orphan candidate (verify or drop)",
                "term": term,
                "auto_fixable": False,
            })

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked or ["nothing to reconcile (no --design/--code-dir/--sources supplied)"],
        not_checked=[
            "which source-prose terms are domain terms missing from the glossary (LLM judgment, Stage 2)",
            "whether each definition is accurate / project-specific (semantic review, Stage 3b)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "term_count": len(terms),
        "grounded": grounded,
        "missing_from_glossary": missing,
        "orphan_terms": orphans,
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-03 glossary against D-19/code domain vocabulary (B11-2/B11-3)."
    )
    ap.add_argument("glossary", help="Path to the D-03 glossary document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--sources", help="Comma-separated source docs (D-02/D-06) for the orphan corpus")
    ap.add_argument("--design", help="D-19 path — its physical model names must be reflected in the glossary (B11-3)")
    ap.add_argument("--code-dir", help="Code dir whose Odoo _name models must be reflected in the glossary (B11-3)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    gloss = Path(_resolve(args.glossary))
    if not gloss.exists():
        print(json.dumps({
            "error": f"Glossary not found: {gloss}",
            "suggestion": "Run 'hbc-create-glossary' first to generate D-03.",
        }, ensure_ascii=False))
        return 2

    design = _resolve(args.design) if args.design else None
    code_dir = _resolve(args.code_dir) if args.code_dir else None
    # A supplied-but-missing --code-dir would rglob to nothing and read as a clean
    # ungrounded pass — make it a loud arg error instead of a silent false-green.
    if code_dir is not None and not Path(code_dir).is_dir():
        print(json.dumps({"error": f"--code-dir is not a directory: {code_dir}", "valid": False}, ensure_ascii=False))
        return 2

    sources = [_resolve(s.strip()) for s in args.sources.split(",") if s.strip()] if args.sources else None
    try:
        result = check(str(gloss), sources, design, code_dir)
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
