#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Reconcile a D-16 Behavioral Design against its requirements + the real code (T3.12 E-2 / T3.13d / grounding).

ADVISORY, not a hard inter-doc gate: the blocking cross-document gate is the
readiness gate (`hbc-check-implementation-readiness` [IR]) and the Phase-2 gate.
Structural element validity (well-formed ids, uniqueness, sections) is the sibling
`validate-behavioral-design.py`. This script adds the four checks those do not
cover, each tied to a [BD] DoD box:

  - ELEMENT_REQ (E-2) — every behavioural-element section must trace to ≥1 REQ. A
    requirement subsection that contains ST-/DR-/INV-/SEQ- elements but names NO
    REQ id is surfaced (the element↔REQ traceability E-2 requires). And a REQ
    defined in --sources (D-02 + D-06) referenced NOWHERE in D-16 is an uncovered
    behavioural facet (model it as a transition/rule/invariant/sequence, or record
    why it has no behaviour). Identity = the shared trailing-number REQ scheme so
    canonical (REQ-FEAT-040) and bare (REQ-040) ids reconcile.
  - BDD (T3.13d) — a Behavioral Design with elements but no Given/When/Then scenario
    has no acceptance-facing expression for ATDD downstream. Surfaces the absence
    (structural presence only — whether the Given/When/Then is *meaningful* is the
    LLM review layer).
  - BEHAVIOR_DRIFT (grounding; D-16 ground_truth = code, reconcile_seam =
    behavioral-vs-code) — ground the behaviour against the REAL code models. Reuses
    the shared `model_drift`. For a D-16 the high-signal direction is `code_only` =
    a persistent model in code the behaviour design never names (likely undocumented
    behaviour); `design_only` reads the same D-19-style "Physical name: `model`"
    lines `model_drift` keys on, so it only fires when a D-16 carries such a line for
    a model code lacks (a prose-only D-16 yields no design_only — by design, to stay
    high-signal rather than flag every incidental dotted token in prose).
    Set-comparison only — whether a divergence is intended is the grounding judgment.
  - CHURN (T2.11) — revision-history row count. `high_churn` (> threshold) is the
    cue to freeze the behaviour model (maturity=exploratory / run [DSC]) instead of
    bumping the version on every edit. The D-16 template is version-first, so the
    shared `churn_assessment` matches directly.

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

DEFAULT_CHURN_THRESHOLD = 4

# An element id DEFINED in the first cell of a table row (matches the sibling
# validator). A behavioural-element section is an H2/H3 whose body defines ≥1 element.
_ELEMENT_DEF_RE = re.compile(r"(?m)^\|\s*(?:ST|DR|INV|SEQ)-\d+\s*\|")
# A markdown heading line (## / ### …). Used to slice the doc into sections so a
# section's REQ coverage is judged against the elements IT defines.
_HEADING_RE = re.compile(r"(?m)^(#{2,6})\s+(.*)$")
# Given/When/Then markers — English canonical + the configured document language
# (Vietnamese: Giả sử / Khi / Thì), mirroring how section detection takes an English
# label PLUS the localized one (NO hardcoded Japanese). Structural presence only.
_GWT_RE = re.compile(r"(?im)\b(given|when|then|gi[ảa]\s*s[ửu]|khi|th[ìi])\b")
# A full triad in order, in EITHER language. English (given→when→then) OR Vietnamese
# (giả sử→khi→thì). `.*?` is non-greedy but unbounded across the whole doc, so the
# triad may span a Scenario block. A lone localized keyword (e.g. "khi") alone never
# satisfies it — all three ordered markers of one language are required.
_GWT_TRIAD_RE = re.compile(
    r"(?is)(?:\bgiven\b.*?\bwhen\b.*?\bthen\b"
    r"|gi[ảa]\s*s[ửu].*?\bkhi\b.*?\bth[ìi]\b)"
)
# Transient/derived code that is not a persistent data model — excluded so a
# wizard/test/controller never reads as a model the design must declare.
_NON_MODEL_PARTS = {"wizard", "wizards", "test", "tests", "controllers", "migrations"}


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


def _sections(text: str) -> list[tuple[str, int, str, str]]:
    """(heading-text, level, body, ancestor-text) for every H2..H6 section.

    ``body`` runs up to the next heading of ANY level. ``ancestor-text`` is the
    concatenation of every enclosing heading's text (smaller level number), so a
    child section (e.g. `### State Transitions`) inherits the REQ id declared on its
    parent (`## REQ-FEAT-024: …`) — the template's normal shape. Without this an
    element table under a REQ-named H2 would falsely read as untraced.
    """
    out: list[tuple[str, int, str, str]] = []
    headings = list(_HEADING_RE.finditer(text))
    stack: list[tuple[int, str]] = []  # (level, heading-text) of open ancestors
    for i, m in enumerate(headings):
        level = len(m.group(1))
        heading = m.group(2).strip()
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        # Pop ancestors at the same or deeper level — they are siblings/closed.
        while stack and stack[-1][0] >= level:
            stack.pop()
        ancestor_text = "\n".join(h for _, h in stack)
        out.append((heading, level, text[start:end], ancestor_text))
        stack.append((level, heading))
    return out


def untraced_element_sections(text: str) -> list[str]:
    """Headings whose body DEFINES ≥1 behavioural element but neither the heading,
    its body, NOR any ancestor heading names a REQ id (E-2).

    A behaviour that traces to no requirement is exactly the gap E-2 closes. The REQ
    may be named in the heading, the element rows, or the enclosing REQ section
    (all count), so the template's "REQ on the H2, elements in H3 children" shape is
    correctly read as traced.
    """
    out: list[str] = []
    for heading, _level, body, ancestor in _sections(text):
        if _ELEMENT_DEF_RE.search(body) and not REQ_ID_RE.search(
            heading + "\n" + body + "\n" + ancestor
        ):
            out.append(heading)
    return out


def uncovered_reqs(d16_text: str, source_text: str) -> list[str]:
    """REQ ids defined in --sources (D-02 + D-06) but referenced NOWHERE in D-16.

    Identity = trailing number (shared req_num_map). The caller is told (via
    `multi_feature`) when >1 feature slug appears and the count should not be trusted.
    NOTE: not every REQ has a behavioural facet — this is ADVISORY (the applicability
    catalog decides which REQs trigger D-16); surfaced for the author to confirm or
    record as no-behaviour, never auto-failed.
    """
    src_map, _ = req_num_map(source_text)
    d16_nums = set(req_num_map(d16_text)[0])
    return [src_map[n] for n in sorted(src_map) if n not in d16_nums]


def bdd_signal(text: str) -> dict:
    """Count Given/When/Then markers + whether a full Given→When→Then triad appears (T3.13d)."""
    markers = len(_GWT_RE.findall(text))
    triad = bool(_GWT_TRIAD_RE.search(text))
    return {"markers": markers, "has_triad": triad}


def has_elements(text: str) -> bool:
    return bool(_ELEMENT_DEF_RE.search(text))


def check(d16_path: str, sources: list[str] | None = None,
          code_dir: str | None = None,
          churn_threshold: int = DEFAULT_CHURN_THRESHOLD) -> dict:
    text = _read(d16_path)
    elements_present = has_elements(text)

    issues: list[dict] = []
    checked: list[str] = []

    # --- ELEMENT_REQ (E-2): element sections that trace to no REQ ---
    checked.append("every behavioural-element section traces to ≥1 requirement id (element↔REQ, E-2)")
    untraced = untraced_element_sections(text)
    for heading in untraced:
        issues.append({
            "type": "UNTRACED_ELEMENT_SECTION",
            "message": f"section '{heading}' defines behavioural elements but names no REQ id "
                       "(cite the REQ each element realizes — E-2 element↔REQ traceability)",
            "section": heading,
            "auto_fixable": False,
        })

    # --- ELEMENT_REQ facet gap (E-2): REQ in sources but not in D-16 ---
    source_corpus = "\n".join(_read(s) for s in (sources or []))
    grounded_reqs = bool(source_corpus.strip())
    _, src_slugs = req_num_map(source_corpus) if grounded_reqs else ({}, set())
    multi_feature = len(src_slugs) > 1
    uncovered: list[str] = []
    if grounded_reqs:
        checked.append("every D-02/D-06 requirement appears somewhere in D-16 (REQ↔behaviour facet coverage, E-2)")
        uncovered = uncovered_reqs(text, source_corpus)
        for rid in uncovered:
            issues.append({
                "type": "UNCOVERED_REQ",
                "message": f"requirement '{rid}' is defined in the source (D-02/D-06) but referenced nowhere "
                           "in D-16 (uncovered behaviour — express its transition/rule/invariant/sequence, "
                           "or record why it is pure-CRUD / has no behaviour)",
                "req": rid,
                "auto_fixable": False,
            })

    # --- BDD (T3.13d): Given/When/Then presence when there ARE behavioural elements ---
    bdd = bdd_signal(text)
    checked.append("Behavioral Design carries ≥1 Given/When/Then scenario for ATDD downstream (T3.13d)")
    if elements_present and not bdd["has_triad"]:
        issues.append({
            "type": "NO_BDD_SCENARIO",
            "message": "behavioural elements exist but no Given/When/Then scenario found — add a BDD "
                       "scenario per behaviour so D-27/acceptance can derive ATDD cases (T3.13d)",
            "auto_fixable": False,
        })

    # --- BEHAVIOR_DRIFT (grounding; behavioral-vs-code seam): model_drift design vs real code ---
    drift = {"design_only": [], "code_only": [], "drift": False}
    if code_dir:
        code_text = "\n".join(_read(str(p)) for p in _iter_code_files(code_dir))
        drift = model_drift(text, code_text)
        checked.append("D-16 model names grounded against the real code models (behavioral-vs-code seam)")
        for tok in drift["design_only"]:
            issues.append({
                "type": "BEHAVIOR_DRIFT_DESIGN_ONLY",
                "message": f"model '{tok}' is named in D-16 but no matching model exists in code "
                           "(planned-not-yet-built, or stale behaviour design — resolve and record in the grounding log)",
                "token": tok,
                "auto_fixable": False,
            })
        for tok in drift["code_only"]:
            issues.append({
                "type": "BEHAVIOR_DRIFT_CODE_ONLY",
                "message": f"model '{tok}' exists in code but D-16 never names it "
                           "(behaviour may be undocumented — model it, or record why it is out of scope)",
                "token": tok,
                "auto_fixable": False,
            })

    # --- CHURN (T2.11): advisory, never an issue ---
    churn = churn_assessment(text, churn_threshold)
    checked.append("revision-history churn surfaced (T2.11 cue; high churn ⇒ freeze the behaviour model)")

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether transitions cover illegal paths / decision tables are complete (LLM review, Stage 4)",
            "whether a BEHAVIOR_DRIFT divergence is intended (planned) or stale (grounding judgment, Stage 2b)",
            "whether a Given/When/Then scenario is MEANINGFUL (LLM review, Stage 4)",
            "whether referenced entities/fields exist in D-19 (readiness gate / LLM review)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "elements_present": elements_present,
        "grounded_reqs": grounded_reqs,
        "grounded_code": bool(code_dir),
        "multi_feature_sources": multi_feature,
        "source_feature_slugs": sorted(src_slugs),
        "untraced_element_sections": untraced,
        "uncovered_reqs": uncovered,
        "bdd": bdd,
        "behavior_drift": drift,
        "churn": churn,
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-16 behaviour against requirements + real code (E-2 / T3.13d / grounding)."
    )
    ap.add_argument("d16", help="Path to the D-16 behavioral-design document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--sources", help="Comma-separated source docs (D-02 + D-06) for the REQ-coverage corpus")
    ap.add_argument("--code-dir", help="Code dir whose Odoo _name models D-16 must be grounded against")
    ap.add_argument("--churn-threshold", type=int, default=DEFAULT_CHURN_THRESHOLD,
                    help=f"Revision-row count above which churn is flagged (default {DEFAULT_CHURN_THRESHOLD})")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    d16 = Path(_resolve(args.d16))
    if not d16.exists():
        print(json.dumps({
            "error": f"D-16 not found: {d16}",
            "suggestion": "Run 'hbc-create-behavioral-design' first to generate D-16.",
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
        result = check(str(d16), sources, code_dir, args.churn_threshold)
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
