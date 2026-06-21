#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Reconcile a D-12 Coding Standards document against the project's REAL code (B10-1 / B10-2).

A coding standard invented from framework defaults — rather than derived from what
the codebase already does — codifies fiction. This check grounds D-12 in the actual
source tree:

  - DEVIATION (B10-1) — a standard D-12 states (indentation, naming case, quote
    style) that the real code does NOT predominantly follow. Surfaced so the author
    either corrects the standard to match reality or records a deliberate migration.
    The standard must be DERIVED from real code, not asserted over it.
  - SPEC_REF_LEAK (B10-2) — a REQ-/TC-/NFR- id embedded in source/test files. D-12's
    "no spec ids in code" rule is the machine-checkable expression of this; the count
    here is what the Phase-3 gate (via hbc-implement spec-ref lint, T1.2) enforces.
    Reported so the standard's lint section is grounded in the real leak count.

ADVISORY, not a hard inter-doc gate: the blocking cross-document gate is the
readiness gate ([IR]) and the Phase-3 implement gate. This script informs D-12
*grounding* during creation/update. It measures STRUCTURE only (indentation chars,
identifier case, spec-id regex) — whether a deviation is acceptable is an LLM/USER
judgment, kept out of here.

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
        spec_ref_leaks,
        verdict,
    )
except Exception as exc:  # noqa: BLE001 — any import failure must be a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# Source extensions whose indentation/case we sample. Kept to the common stacks the
# detector below understands; an unknown extension contributes nothing (no false claim).
_CODE_GLOBS = ("*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.php", "*.java")
# Dirs that are not first-party source — never sample conventions from vendored/build code.
_SKIP_PARTS = {
    "node_modules", "vendor", "dist", "build", ".git", "__pycache__",
    "migrations", ".venv", "venv", "env",
}

# Identifier-definition patterns per language family. Group 1 = the declared name.
# Structure only: we read the *case shape* of names the code actually declares.
_DEF_PATTERNS = (
    re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\("),          # python func/method
    re.compile(r"^\s*(?:async\s+)?function\s+([A-Za-z_$]\w*)"),  # js/ts function
    re.compile(r"^\s*(?:public|private|protected)\s+function\s+([A-Za-z_$]\w*)"),  # php method
)


def _iter_code_files(code_dir: str):
    base = Path(code_dir)
    for pat in _CODE_GLOBS:
        for p in sorted(base.rglob(pat)):
            # Exclude on the path RELATIVE to code_dir, never the absolute path — else a
            # project checked out under e.g. C:\...\build\... would silently sample nothing
            # and report a false-green pass.
            rel = p.relative_to(base)
            if {part.lower() for part in rel.parts} & _SKIP_PARTS:
                continue
            yield p


def _read(path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


# --- indentation (B10-1) -------------------------------------------------------

def detect_indent_style(lines: list[str]) -> tuple[str | None, int]:
    """Predominant leading-whitespace style across indented lines.

    Returns ``(style, sample_size)`` where style is ``"tabs"``, ``"spaces"``, or
    None (too few indented lines to decide). Counts the FIRST indent char of each
    line that starts with whitespace and has non-whitespace content."""
    tab = space = 0
    for ln in lines:
        if not ln.strip():
            continue
        head = ln[: len(ln) - len(ln.lstrip(" \t"))]
        if not head:
            continue
        if head[0] == "\t":
            tab += 1
        elif head[0] == " ":
            space += 1
    sample = tab + space
    if sample < 5:  # too little signal to assert a project-wide style
        return None, sample
    return ("tabs" if tab > space else "spaces"), sample


def _case_of(name: str) -> str | None:
    """Coarse case classification of an identifier. None = ambiguous (e.g. one word)."""
    if "_" in name and name.lower() == name:
        return "snake_case"
    if name[:1].isupper() and "_" not in name:
        return "PascalCase"
    if name[:1].islower() and any(c.isupper() for c in name) and "_" not in name:
        return "camelCase"
    return None


def detect_naming_case(files_text: list[tuple[str, str]]) -> tuple[str | None, int]:
    """Predominant function/method-name case across the sampled code.

    Returns ``(case, sample_size)``; case is one of snake_case/camelCase/PascalCase
    or None when too few classifiable names exist. Leading-underscore (private)
    names are normalized before classification."""
    counts: dict[str, int] = {}
    for _, text in files_text:
        for ln in text.splitlines():
            for pat in _DEF_PATTERNS:
                m = pat.match(ln)
                if not m:
                    continue
                name = m.group(1).lstrip("_")
                c = _case_of(name)
                if c:
                    counts[c] = counts.get(c, 0) + 1
    sample = sum(counts.values())
    if sample < 5:
        return None, sample
    return max(counts, key=lambda k: counts[k]), sample


# --- stated-standard extraction (structure only) -------------------------------

def stated_indent(d12_text: str) -> str | None:
    """The indentation style D-12 STATES, if unambiguous. None when it names both
    or neither (the validator's CONTRADICTION advisory covers the 'both' case)."""
    low = d12_text.lower()
    says_tabs = bool(re.search(r"\btabs?\b", low))
    says_spaces = bool(re.search(r"\bspaces?\b", low))
    if says_tabs == says_spaces:  # both or neither → no single stated value
        return None
    return "tabs" if says_tabs else "spaces"


def stated_case(d12_text: str) -> set[str]:
    """The naming cases D-12 explicitly names (may be several; e.g. snake for funcs,
    Pascal for classes). A code case that is among these is NOT a deviation."""
    low = d12_text.lower()
    out: set[str] = set()
    if "snake_case" in low:
        out.add("snake_case")
    if "camelcase" in low:
        out.add("camelCase")
    if "pascalcase" in low:
        out.add("PascalCase")
    return out


# --- deviations ----------------------------------------------------------------

def find_deviations(d12_text: str, files_text: list[tuple[str, str]]) -> list[dict]:
    """Standards in D-12 the real code does not follow (B10-1)."""
    issues: list[dict] = []
    all_lines: list[str] = []
    for _, text in files_text:
        all_lines.extend(text.splitlines())

    code_indent, indent_n = detect_indent_style(all_lines)
    want_indent = stated_indent(d12_text)
    if want_indent and code_indent and want_indent != code_indent:
        issues.append({
            "type": "DEVIATION",
            "aspect": "indentation",
            "message": (
                f"D-12 states '{want_indent}' indentation but the code predominantly uses "
                f"'{code_indent}' ({indent_n} indented lines sampled) — derive from reality or record a migration"
            ),
            "stated": want_indent,
            "actual": code_indent,
            "auto_fixable": False,
        })

    code_case, case_n = detect_naming_case(files_text)
    want_cases = stated_case(d12_text)
    if code_case and want_cases and code_case not in want_cases:
        issues.append({
            "type": "DEVIATION",
            "aspect": "naming_case",
            "message": (
                f"code function/method names are predominantly '{code_case}' ({case_n} sampled) "
                f"but D-12 names only {sorted(want_cases)} — the standard omits the real convention"
            ),
            "stated": sorted(want_cases),
            "actual": code_case,
            "auto_fixable": False,
        })
    return issues


def check(d12_path: str, code_dir: str | None = None) -> dict:
    d12_text = _read(d12_path)

    issues: list[dict] = []
    checked: list[str] = []
    deviations: list[dict] = []
    spec_refs: list[str] = []
    grounded = bool(code_dir)
    indent_actual = case_actual = None

    if grounded:
        files_text = [(str(p), _read(p)) for p in _iter_code_files(code_dir)]
        checked.append("D-12 stated conventions match the real code (derive-from-code, B10-1)")
        deviations = find_deviations(d12_text, files_text)
        issues.extend(deviations)

        all_lines: list[str] = []
        for _, t in files_text:
            all_lines.extend(t.splitlines())
        indent_actual, _ = detect_indent_style(all_lines)
        case_actual, _ = detect_naming_case(files_text)

        # SPEC_REF_LEAK (B10-2): the machine-checkable rule D-12 must emit so the
        # Phase-3 gate can enforce 0 leaks. Reported here grounded in the real count.
        checked.append("spec-id leaks the D-12 lint rule must forbid (machine-rule→gate-P3, B10-2)")
        for fp, text in files_text:
            for ref in spec_ref_leaks(text):
                spec_refs.append(ref)
                issues.append({
                    "type": "SPEC_REF_LEAK",
                    "message": (
                        f"spec id '{ref}' is embedded in code ({Path(fp).name}) — D-12 must carry a "
                        f"machine-checkable 'no spec ids in code' lint rule; the Phase-3 gate enforces it"
                    ),
                    "ref": ref,
                    "file": Path(fp).name,
                    "auto_fixable": False,
                })

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked or ["nothing to reconcile (no --code-dir supplied)"],
        not_checked=[
            "whether a deviation is an acceptable deliberate choice (USER/LLM judgment)",
            "correctness/quality of each stated rule (semantic review, Stage 3b)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "grounded": grounded,
        "indent_actual": indent_actual,
        "naming_case_actual": case_actual,
        "deviations": deviations,
        "spec_ref_leaks": spec_refs,
        "spec_ref_leak_count": len(spec_refs),
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-12 coding standards against the real code (B10-1/B10-2)."
    )
    ap.add_argument("document", help="Path to the D-12 coding standards document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--code-dir", help="First-party source dir to derive conventions from / scan for spec-id leaks")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    doc = Path(_resolve(args.document))
    if not doc.exists():
        print(json.dumps({
            "error": f"Coding standards doc not found: {doc}",
            "suggestion": "Run 'hbc-create-coding-standards' first to generate D-12.",
        }, ensure_ascii=False))
        return 2

    code_dir = _resolve(args.code_dir) if args.code_dir else None
    # A supplied-but-missing --code-dir would rglob to nothing and read as a clean
    # ungrounded pass — make it a loud arg error instead of a silent false-green.
    if code_dir is not None and not Path(code_dir).is_dir():
        print(json.dumps({"error": f"--code-dir is not a directory: {code_dir}", "valid": False}, ensure_ascii=False))
        return 2

    try:
        result = check(str(doc), code_dir)
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
