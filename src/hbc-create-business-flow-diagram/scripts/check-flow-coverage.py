#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Reconcile a D-06 Business Flow Diagram against its requirements and path standard (T3.11).

ADVISORY, not a hard inter-doc gate: the blocking cross-document gate is the
readiness gate (`hbc-check-implementation-readiness` [IR]) and the Phase-1 gate.
This check informs D-06 *completeness* during creation. Mermaid *rendering* is a
separate validator (`validate-mermaid.py` / `npm run check:mermaid`); FR↔PRD
coverage is `check-fr-coverage.py`. This script only adds the three structure
checks those two do not cover:

  - ALL_PATHS (B8-2) — every flow should enumerate more than the happy path.
    A sequenceDiagram/flowchart block with NO branch construct (`alt`/`opt`/
    `par`/`break` for sequence; a decision `{...}` node for flowchart;
    `stateDiagram` is exempt — its branches are transitions) is surfaced as a
    SINGLE_PATH_FLOW candidate for the user to confirm or fill. STRUCTURAL only:
    whether the alternate/exception path is *semantically correct* stays with the
    LLM/semantic layer.
  - PATH_ID (B8-6) — path identifiers follow a single stable scheme `PATH-NN`
    (two+ digits), so task-breakdown and test cases can reference a branch. A
    `PATH-N` that does not match, or a flow heading with no PATH-id at all, is
    flagged. The scheme is configurable via --path-id-pattern.
  - PHANTOM_FLOW + REQ-facet (B8-5) — a flow that references NO requirement id is
    a phantom (drawn but backed by no REQ). And a REQ present in the D-02 source
    but referenced nowhere in D-06 is an uncovered-REQ facet gap. Both reuse the
    shared trailing-number REQ identity so canonical (REQ-FEAT-040) and bare
    (REQ-040) ids reconcile. (FR/NFR-vs-PRD coverage proper is check-fr-coverage.)

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
DEFAULT_PATH_ID_PATTERN = r"PATH-\d{2,}"
# A path-token shaped like the scheme but NOT matching it (e.g. PATH-1, PATH-A) —
# used only to tell "malformed id" apart from "no id at all".
_PATH_TOKEN_RE = re.compile(r"\bPATH-[A-Za-z0-9]+\b")
# Branch constructs that prove a sequenceDiagram block draws >1 path.
_SEQ_BRANCH_RE = re.compile(r"^\s*(alt|opt|par|break|critical|else)\b", re.MULTILINE)
# A flowchart decision node: `X{ ... }` or `X{" ... "}` (diamond = a branch point).
_FLOW_DECISION_RE = re.compile(r"\{[^}]+\}")
_DIAGRAM_TYPE_RE = re.compile(
    r"^\s*(sequenceDiagram|flowchart|graph|stateDiagram(?:-v2)?)\b", re.MULTILINE
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _blocks(text: str) -> list[str]:
    return [m.group(1) for m in MERMAID_BLOCK_RE.finditer(text)]


def _diagram_type(block: str) -> str | None:
    m = _DIAGRAM_TYPE_RE.search(block)
    return m.group(1) if m else None


def _block_has_branch(block: str) -> bool:
    """True if the block draws an alternate/exception path beyond the happy line.

    sequenceDiagram → an `alt/opt/par/break/critical` construct.
    flowchart/graph → ≥1 decision diamond `{...}` (a branch point).
    stateDiagram    → exempt (its transitions ARE the branches) — treated as
                      branched so a lifecycle diagram is never a false single-path.
    """
    dtype = _diagram_type(block)
    if dtype and dtype.startswith("stateDiagram"):
        return True
    if dtype in ("flowchart", "graph"):
        return bool(_FLOW_DECISION_RE.search(block))
    # sequenceDiagram (or untyped — default to the sequence rule)
    return bool(_SEQ_BRANCH_RE.search(block))


def single_path_flows(text: str) -> list[dict]:
    """Mermaid blocks (by index) that draw only one path — no branch construct (B8-2)."""
    out: list[dict] = []
    for idx, block in enumerate(_blocks(text)):
        if not _block_has_branch(block):
            out.append({"block": idx, "diagram_type": _diagram_type(block)})
    return out


def path_id_issues(text: str, pattern: re.Pattern[str]) -> tuple[list[str], list[str]]:
    """Return (well_formed_path_ids, malformed_path_tokens) found in the document (B8-6).

    A token shaped `PATH-…` that does NOT match the scheme is malformed (e.g.
    `PATH-1` when the scheme wants `PATH-01`). Whole-document scan — path-ids are
    annotated inside Mermaid blocks (`%% PATH-01` / `Note`) and in prose tables.

    Uses ``finditer`` + ``group(0)`` (the WHOLE match), never ``findall`` — so a
    custom ``--path-id-pattern`` that happens to carry a capture group does not
    corrupt the well-formed set with only the captured fragment. Malformed
    detection only runs for ``PATH-``-shaped schemes (the malformed-token corpus is
    ``PATH-…``); a project using a different prefix gets well-formed detection but
    no false "malformed" noise from unrelated ``PATH-`` text.
    """
    well_formed = sorted({m.group(0) for m in pattern.finditer(text)})
    # Only meaningful to call a stray PATH- token "malformed" when the scheme itself
    # is PATH--shaped; otherwise the prefix is unrelated to this project's scheme.
    scheme_is_path = pattern.fullmatch("PATH-01") is not None or pattern.fullmatch("PATH-1") is not None
    if scheme_is_path:
        all_tokens = set(_PATH_TOKEN_RE.findall(text))
        malformed = sorted(t for t in all_tokens if not pattern.fullmatch(t))
    else:
        malformed = []
    return well_formed, malformed


def phantom_flows(text: str) -> list[dict]:
    """Mermaid blocks that reference NO requirement id — drawn but REQ-unbacked (B8-5).

    A flow with no REQ is either a phantom (no requirement justifies it) or an
    un-annotated flow (the REQ exists but was never cited in the diagram). Either
    way it breaks REQ↔flow traceability and is surfaced. stateDiagram lifecycle
    blocks are included — a lifecycle still traces to the REQ that owns the entity.
    """
    out: list[dict] = []
    for idx, block in enumerate(_blocks(text)):
        if not REQ_ID_RE.search(block):
            out.append({"block": idx, "diagram_type": _diagram_type(block)})
    return out


def uncovered_reqs(d06_text: str, source_text: str) -> list[str]:
    """REQ ids defined in the D-02 source but referenced NOWHERE in D-06 (B8-5 facet gap).

    Identity = trailing number (sound for a single feature; reuses the shared
    req_num_map). Returns the canonical source id form for each uncovered REQ.
    """
    src_map, _ = req_num_map(source_text)
    d06_nums = set(req_num_map(d06_text)[0])
    return [src_map[n] for n in sorted(src_map) if n not in d06_nums]


def check(d06_path: str, sources: list[str] | None = None,
          path_id_pattern: str = DEFAULT_PATH_ID_PATTERN) -> dict:
    text = _read(d06_path)
    try:
        pat = re.compile(path_id_pattern)
    except re.error as exc:
        raise ValueError(f"bad --path-id-pattern: {exc}") from exc

    blocks = _blocks(text)
    singles = single_path_flows(text)
    phantoms = phantom_flows(text)
    well_formed, malformed = path_id_issues(text, pat)

    source_corpus = "\n".join(_read(s) for s in (sources or []))
    grounded = bool(source_corpus.strip())
    uncovered = uncovered_reqs(text, source_corpus) if grounded else []

    issues: list[dict] = []
    checked: list[str] = []

    checked.append("every flow enumerates >1 path (happy + alternate/exception) (B8-2)")
    for s in singles:
        issues.append({
            "type": "SINGLE_PATH_FLOW",
            "message": f"Mermaid block {s['block']} ({s['diagram_type'] or 'untyped'}) draws only one path — "
                       "no alternate/exception branch (confirm happy-only, or add the alt/exception path)",
            "block": s["block"],
            "auto_fixable": False,
        })

    checked.append(f"path identifiers follow the '{path_id_pattern}' scheme (B8-6)")
    for tok in malformed:
        issues.append({
            "type": "MALFORMED_PATH_ID",
            "message": f"path id '{tok}' does not match the scheme '{path_id_pattern}' (e.g. PATH-01)",
            "token": tok,
            "auto_fixable": False,
        })

    checked.append("every flow references ≥1 requirement id (no phantom flow) (B8-5)")
    for p in phantoms:
        issues.append({
            "type": "PHANTOM_FLOW",
            "message": f"Mermaid block {p['block']} ({p['diagram_type'] or 'untyped'}) references no REQ id — "
                       "phantom flow (no requirement backs it) or un-annotated (cite the REQ it realizes)",
            "block": p["block"],
            "auto_fixable": False,
        })

    if grounded:
        checked.append("every D-02 requirement appears somewhere in D-06 (REQ↔flow facet coverage) (B8-5)")
        for rid in uncovered:
            issues.append({
                "type": "UNCOVERED_REQ",
                "message": f"requirement '{rid}' is defined in the source but referenced nowhere in D-06 "
                           "(uncovered facet — draw it, or record why it is not a flow)",
                "req": rid,
                "auto_fixable": False,
            })

    structure_ok = not issues
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether each alternate/exception path is the CORRECT one (semantic review, Stage 4b)",
            "whether AS-IS matches real code/behavior (grounding-to-code, Stage 2b — judgment)",
            "Mermaid render validity (validate-mermaid.py) and FR↔PRD coverage (check-fr-coverage.py)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "block_count": len(blocks),
        "grounded": grounded,
        "path_ids": well_formed,
        "single_path_flows": [s["block"] for s in singles],
        "malformed_path_ids": malformed,
        "phantom_flows": [p["block"] for p in phantoms],
        "uncovered_reqs": uncovered,
        "total_issues": len(issues),
        "issues": issues,
    })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reconcile D-06 flows against requirements + path-ID standard (B8-2/B8-5/B8-6)."
    )
    ap.add_argument("d06", help="Path to the D-06 business-flow-diagram document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--sources", help="Comma-separated source docs (D-02) for the REQ-coverage corpus")
    ap.add_argument("--path-id-pattern", default=DEFAULT_PATH_ID_PATTERN,
                    help=f"Regex for path identifiers (default: {DEFAULT_PATH_ID_PATTERN})")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    d06 = Path(_resolve(args.d06))
    if not d06.exists():
        print(json.dumps({
            "error": f"D-06 not found: {d06}",
            "suggestion": "Run 'hbc-create-business-flow-diagram' first to generate D-06.",
        }, ensure_ascii=False))
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
        result = check(str(d06), sources, args.path_id_pattern)
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "valid": False}, ensure_ascii=False))
        return 2
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
