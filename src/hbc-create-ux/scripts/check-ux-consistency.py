#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Advisory consistency check for a D-14 UX / Screen Design document.

D-14 is the spec-of-record for the user-facing surface. This check surfaces the
gaps that make a UX spec a "mockup island" — present but disconnected from the
requirements, the design tokens, the code, and the tests. It is **ADVISORY**:
every finding is reported for human triage and is never auto-fixed; the *blocking*
inter-document gate is `hbc-check-implementation-readiness` [IR] / the Phase gate
[PG], and the living traceability matrix is owned by `hbc-traceability` [TR]
(forward-ref — this script does not own the matrix engine).

What it surfaces (structural set-comparison only — no meaning judgment):

  - REQ_NO_SCREEN  (UX-4) — a REQ referenced anywhere in D-14 that no screen serves.
  - SCREEN_NO_REQ  (UX-4) — a screen row that names no REQ.
  - SCREEN_NO_COMPONENT (UX-4) — a screen with no component mapped to it.
  - SCREEN_NO_TEST (UX-4 / UX-7) — a screen with no E2E/UI test ref (outside-in ATDD
    names the test before code; a screen with no test is an untestable surface).
  - COMPONENT_NO_TOKEN (UX-3 / UX-6) — a component whose Visual-tokens cell carries no
    {path.to.token} reference (visuals must come from the single design-token source,
    not be inlined or omitted).
  - MOCKUP_MISSING (UX-2) — Claude Design is in use (uses_claude_design / --uses-claude-design)
    but a screen has no committed Mockup Ref → design-sync cannot anchor it.
  - TOKEN_SOURCE_MISSING (UX-6) — Claude Design is in use but no single design_token_source
    is declared in frontmatter.
  - COMPONENT_NOT_IN_CODE (UX-3) — when --code-dir is supplied, a component whose Code Ref
    names a symbol absent from the code (the component-map ↔ code reconcile; ground-truth
    is the code, per the catalog). Reconcile only runs when a code dir is supplied.

Whether a screen-set semantically covers the feature, whether a test truly exercises
the screen, and whether a mockup matches the spec stay with the LLM/readiness layers.

Exit: 0 no advisories, 1 advisories found, 2 arg/io error.
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
        verdict,
    )
except Exception as exc:  # noqa: BLE001 — import failure must be a structured error, not a traceback
    print(json.dumps({
        "error": f"Shared lib 'hbc_validation' could not be loaded: {exc}",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

SCREENS_LABELS = ("Screens", "Màn hình")
COMPONENTS_LABELS = ("Components", "Thành phần")
TRACE_LABELS = ("Traceability", "Truy vết")

REQ_RE = re.compile(r"\bREQ-(?:[A-Z0-9]+-)+\d{3,}\b")
SCR_RE = re.compile(r"\bSCR-\d+\b")
CMP_RE = re.compile(r"\bCMP-\d+\b")
TOKEN_RE = re.compile(r"\{[a-zA-Z][\w.-]*\}")  # {path.to.token}
# A blank/placeholder cell: empty, an em/en dash, "n/a", or "tbd".
_BLANK_RE = re.compile(r"^\s*(|[-–—]+|n/?a|tbd|todo)\s*$", re.IGNORECASE)
# Frontmatter scalar lines we read (no YAML dep — structural).
# Strip surrounding quotes so a YAML-valid `uses_claude_design: "true"` is not
# silently read as a non-boolean (which would disable the Claude-Design checks — a
# false-green).
_USES_CD_RE = re.compile(r'(?m)^\s*uses_claude_design\s*:\s*["\']?(\w+)["\']?')
_TOKEN_SRC_RE = re.compile(r'(?m)^\s*design_token_source\s*:\s*["\']?([^"\'\n]*)["\']?\s*$')


def _blank(cell: str) -> bool:
    return bool(_BLANK_RE.match(cell or ""))


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _frontmatter_uses_claude_design(content: str) -> bool:
    m = _USES_CD_RE.search(content)
    return bool(m and m.group(1).strip().lower() in {"true", "yes", "1"})


def _frontmatter_token_source(content: str) -> str:
    m = _TOKEN_SRC_RE.search(content)
    return m.group(1).strip() if m else ""


def _screen_rows(content: str) -> list[list[str]]:
    return parse_table(content, *SCREENS_LABELS)


def _component_rows(content: str) -> list[list[str]]:
    return parse_table(content, *COMPONENTS_LABELS)


def _trace_rows(content: str) -> list[list[str]]:
    return parse_table(content, *TRACE_LABELS)


def _col(row: list[str], idx: int) -> str:
    return row[idx] if idx < len(row) else ""


def check(doc_path: str, code_dir: str | None = None,
          uses_claude_design: bool | None = None) -> dict:
    content = _read(doc_path)

    uses_cd = (uses_claude_design if uses_claude_design is not None
               else _frontmatter_uses_claude_design(content))
    token_source = _frontmatter_token_source(content)

    screen_rows = _screen_rows(content)
    comp_rows = _component_rows(content)
    trace_rows = _trace_rows(content)

    # --- screen → {id, req, mockup} (Screens table: ID | Screen | REQ | D-06 | Mockup) ---
    screens: dict[str, dict] = {}
    for r in screen_rows:
        ids = SCR_RE.findall(_col(r, 0))
        if not ids:
            continue
        sid = ids[0]
        screens[sid] = {
            "req": set(REQ_RE.findall(_col(r, 2))),
            "mockup": _col(r, 4),
        }

    # --- component → {id, screen, tokens, code_ref, req} (ID|Comp|Screen|Tokens|Code|REQ) ---
    components: dict[str, dict] = {}
    screen_has_component: set[str] = set()
    for r in comp_rows:
        ids = CMP_RE.findall(_col(r, 0))
        if not ids:
            continue
        cid = ids[0]
        for s in SCR_RE.findall(_col(r, 2)):
            screen_has_component.add(s)
        components[cid] = {
            "screens": set(SCR_RE.findall(_col(r, 2))),
            "tokens": TOKEN_RE.findall(_col(r, 3)),
            "code_ref": _col(r, 4),
        }

    # --- traceability table: REQ | Screen | Component(s) | Test Ref ---
    screen_has_test: set[str] = set()
    req_in_trace: set[str] = set()
    for r in trace_rows:
        for s in SCR_RE.findall(_col(r, 1)):
            if not _blank(_col(r, 3)):
                screen_has_test.add(s)
        req_in_trace |= set(REQ_RE.findall(_col(r, 0)))

    # All REQ ids referenced anywhere in the doc (the UI-facing requirement set as
    # D-14 itself states it — we do not invent a REQ the doc never mentions).
    all_reqs = set(REQ_RE.findall(content))
    reqs_with_screen: set[str] = set()
    for sid, s in screens.items():
        reqs_with_screen |= s["req"]

    advisories: list[dict] = []

    def add(kind: str, msg: str, **extra):
        advisories.append({"type": kind, "message": msg, "auto_fixable": False, **extra})

    # UX-4: every referenced REQ is served by a screen.
    for req in sorted(all_reqs - reqs_with_screen):
        add("REQ_NO_SCREEN", f"{req} is referenced but no screen serves it (REQ→screen gap)", req=req)

    for sid in sorted(screens):
        if not screens[sid]["req"]:
            add("SCREEN_NO_REQ", f"screen {sid} names no REQ (untraceable screen)", screen=sid)
        if sid not in screen_has_component:
            add("SCREEN_NO_COMPONENT", f"screen {sid} has no component mapped to it", screen=sid)
        if sid not in screen_has_test:
            add("SCREEN_NO_TEST",
                f"screen {sid} has no E2E/UI test ref (outside-in ATDD names the test first)", screen=sid)
        if uses_cd and _blank(screens[sid]["mockup"]):
            add("MOCKUP_MISSING",
                f"screen {sid} has no committed Mockup Ref but Claude Design is in use (design-sync gap)",
                screen=sid)

    # UX-3 / UX-6: each component sources visuals from a token.
    for cid in sorted(components):
        if not components[cid]["tokens"]:
            add("COMPONENT_NO_TOKEN",
                f"component {cid} references no {{path.to.token}} — visuals must come from the design-token source",
                component=cid)

    # UX-6: single token source declared when Claude Design is used.
    if uses_cd and not token_source:
        add("TOKEN_SOURCE_MISSING",
            "Claude Design is in use but no single design_token_source is declared in frontmatter (UX-6)")

    # UX-3: component-map ↔ code reconcile (only when a code dir is supplied).
    code_reconciled = False
    if code_dir:
        code_text = _gather_code(code_dir)
        code_reconciled = True
        for cid in sorted(components):
            ref = components[cid]["code_ref"]
            if _blank(ref):
                continue  # not yet implemented — not a gap, just unmapped
            symbol = ref.strip().strip("`")
            if not _symbol_in_code(symbol, code_text):
                add("COMPONENT_NOT_IN_CODE",
                    f"component {cid} maps to code symbol '{symbol}' not found under the code dir",
                    component=cid, code_ref=symbol)

    checked = [
        "every referenced REQ is served by a screen (UX-4)",
        "every screen names a REQ, has a component, has a test ref (UX-4 / UX-7)",
        "every component references a design token (UX-3 / UX-6)",
    ]
    if uses_cd:
        checked.append("every screen has a committed mockup + a single token source (UX-2 / UX-6)")
    if code_reconciled:
        checked.append("each component Code Ref resolves to a real code symbol (UX-3 component-map ↔ code)")

    structure_ok = not advisories
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether the screen set semantically covers the feature (LLM / readiness)",
            "whether a test truly exercises its screen (Phase 4 [TE]/[AC])",
            "whether a mockup visually matches the spec (visual-regression, consumer tool)",
        ],
    )
    result.update({
        # ADVISORY: `valid` mirrors structure but the skill never blocks on it
        # (blocking gate is [IR]/[PG]). Findings are surfaced for triage.
        "valid": structure_ok,
        "advisory": True,
        "uses_claude_design": uses_cd,
        "design_token_source": token_source,
        "screen_count": len(screens),
        "component_count": len(components),
        "code_reconciled": code_reconciled,
        "advisory_count": len(advisories),
        "advisories": advisories,
    })
    return result


def _gather_code(code_dir: str) -> str:
    base = Path(code_dir)
    parts: list[str] = []
    for ext in ("*.py", "*.js", "*.ts", "*.tsx", "*.jsx", "*.vue", "*.xml"):
        for p in base.rglob(ext):
            try:
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    return "\n".join(parts)


def _symbol_in_code(symbol: str, code_text: str) -> bool:
    """Whole-identifier presence of a component symbol in the code corpus. Lenient —
    a substring of a longer identifier does NOT count (avoids 'Table' matching
    'DataTable'), but the symbol need only appear, not be defined a particular way."""
    if not symbol:
        return False
    return re.search(rf"(?<![\w.]){re.escape(symbol)}(?![\w])", code_text) is not None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Advisory consistency check for D-14 UX / Screen Design (UX-2/3/4/6/7)."
    )
    ap.add_argument("document", help="Path to the D-14 document")
    ap.add_argument("--project-root", default=".", help="Project root; relative path args resolve against it")
    ap.add_argument("--code-dir", help="Code dir to reconcile component Code Refs against (UX-3). Omit to skip.")
    ap.add_argument("--uses-claude-design", action="store_true",
                    help="Force Claude-Design checks on (else read from frontmatter uses_claude_design).")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    root = Path(args.project_root)

    def _resolve(path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else root / p)

    doc = Path(_resolve(args.document))
    if not doc.exists():
        print(json.dumps({
            "error": f"Document not found: {doc}",
            "suggestion": "Run 'hbc-create-ux' first to generate D-14.",
        }, ensure_ascii=False))
        return 2

    code_dir = _resolve(args.code_dir) if args.code_dir else None
    # A supplied-but-missing --code-dir would rglob to nothing and read as a clean
    # "no code gaps" pass — make it a loud arg error, not a silent false-green.
    if code_dir is not None and not Path(code_dir).is_dir():
        print(json.dumps({"error": f"--code-dir is not a directory: {code_dir}", "valid": False}, ensure_ascii=False))
        return 2

    uses_cd = True if args.uses_claude_design else None
    try:
        result = check(str(doc), code_dir, uses_cd)
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
