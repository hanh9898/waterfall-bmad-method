#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Verify that the traceability matrix's code/test refs are REAL — and the model
is not drifted — before Phase 4 trusts a green test run (B16-1, B16-3).

A test-execution report can read "87/87 passed" while the matrix points at code
that was renamed/deleted and the design has moved on. "Passed" against the WRONG
model is the cardinal Phase-4 false-green. This engine does NOT trust the matrix
strings: it verifies the referenced files actually EXIST on disk and reconciles the
design (D-19) model tokens against the code that ran.

Checks (deterministic structure-only; meaning stays with the LLM/human layer):
  - B16-1 ref existence: every non-empty ``code_ref`` / ``test_ref`` path token in
    the matrix resolves to a real file under ``--code-dir`` (``missing_code_ref`` /
    ``missing_test_ref``). A matrix string is NOT proof a referenced artifact exists.
  - B16-1 matrix completeness: REQ defined in D-02 but with no matrix row
    (``missing_from_matrix``, shared primitive) — the "39/39 green but 040/041/042
    never added" seam.
  - B16-1 model-drift clean: D-19 design model tokens vs the code that ran
    (``model_drift``, shared) — "tests passed against the OLD model" (the RCA drift).
  - B16-3 D-27 stale: D-27 (or D-26) citing a STALE D-02 version
    (``stale_citations``, shared ``version_coherence``) — Phase 4 ran a spec the
    upstream already superseded.

Exit codes: 0 clean, 1 problems found, 2 unreadable required input / arg error.
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
        doc_version,
        missing_from_matrix,
        model_drift,
        parse_matrix,
        verdict,
        version_coherence,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

DEFAULT_CODE_GLOB = "models/**/*.py"

# A file-path-looking token inside a matrix ref cell: at least one "/" and a file
# extension. Restricting to path-shaped tokens (not free prose like "model/menu")
# keeps the existence check high-signal — a design note in the cell is not a path.
_PATH_TOKEN_RE = re.compile(r"[\w./-]+\.[A-Za-z0-9]{1,6}")
# Module-prefix the matrix writes that is NOT part of the on-disk feature code root
# (the matrix records repo-relative paths like "project_invoice/models/x.py", but
# --code-dir already points AT that module). Stripped before resolving on disk.
_STRIP_PREFIXES = ("project_invoice/",)


def _read(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _read_code(code_dir: str | None, glob: str) -> str | None:
    """Concatenate persistent-model source for model-drift (mirrors readiness).

    None when no code_dir given → drift simply doesn't run. "" (not None) when the
    dir exists but matches no files — an empty corpus still lets model_drift report
    every design model as design_only instead of masquerading as "no code → green".
    """
    if not code_dir:
        return None
    root = Path(code_dir)
    if not root.exists():
        print(f"WARNING: --code-dir does not exist, model-drift skipped: {code_dir}", file=sys.stderr)
        return None
    parts: list[str] = []
    for p in sorted(root.glob(glob)):
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(parts)


def _ref_path_tokens(cell: str) -> list[str]:
    """Path-shaped tokens in a matrix ref cell (may carry several, comma/space sep)."""
    return [t for t in _PATH_TOKEN_RE.findall(cell or "")]


def _resolve_exists(token: str, code_dir: Path) -> bool:
    """A ref path token exists if it resolves under code_dir (after stripping the
    repo-module prefix the matrix records) OR matches by basename anywhere beneath
    code_dir. Basename fallback tolerates a matrix that records a path relative to a
    different root, while a bare-string match (no '/'/no ext) is excluded upstream so
    prose never counts as 'present'."""
    cleaned = token
    for pre in _STRIP_PREFIXES:
        if cleaned.startswith(pre):
            cleaned = cleaned[len(pre):]
    if (code_dir / cleaned).exists():
        return True
    # basename fallback — guard against an empty/dot basename
    name = Path(cleaned).name
    if not name or name in {".", ".."}:
        return False
    return any(code_dir.rglob(name))


def check_matrix_refs(matrix_text: str, code_dir: Path | None) -> dict:
    """B16-1: every code_ref / test_ref path token resolves to a real file.

    Returns {"missing_code_ref": {req: [tokens]}, "missing_test_ref": {...}}.
    No code_dir → returns empty (cannot verify existence without a corpus root); the
    caller surfaces a note so an un-rooted run is not read as "all refs exist".
    """
    out = {"missing_code_ref": {}, "missing_test_ref": {}}
    if code_dir is None:
        return out
    header, rows = parse_matrix(matrix_text)
    ri = header.get("req_id", 0)
    for cells in rows:
        rid = cells[ri].strip() if ri < len(cells) else "?"
        for col, key in (("code_ref", "missing_code_ref"), ("test_ref", "missing_test_ref")):
            idx = header.get(col, -1)
            if idx < 0 or idx >= len(cells):
                continue
            missing = [t for t in _ref_path_tokens(cells[idx]) if not _resolve_exists(t, code_dir)]
            if missing:
                out[key][rid] = missing
    return out


def verify(
    matrix_text: str,
    d02_text: str | None = None,
    d19_text: str | None = None,
    code_text: str | None = None,
    code_dir: Path | None = None,
    d27_text: str | None = None,
    d26_text: str | None = None,
) -> dict:
    result: dict = {"checked": []}
    problems = False
    checked_any = False  # ≥1 verification that can FAIL actually ran

    # --- B16-1: matrix ref existence (code_ref / test_ref point at real files) ---
    if code_dir is not None:
        result["checked"].append("matrix-ref-existence")
        checked_any = True
        refs = check_matrix_refs(matrix_text, code_dir)
        if refs["missing_code_ref"]:
            result["missing_code_ref"] = refs["missing_code_ref"]
            problems = True
        if refs["missing_test_ref"]:
            result["missing_test_ref"] = refs["missing_test_ref"]
            problems = True

    # --- B16-1: every D-02 REQ has a matrix row ---
    if d02_text is not None:
        result["checked"].append("matrix-completeness")
        checked_any = True
        missing = missing_from_matrix(d02_text, matrix_text)
        if missing:
            result["missing_from_matrix"] = missing
            problems = True

    # --- B16-1: model-drift clean (tests ran against the design's model) ---
    if d19_text is not None and code_text is not None:
        result["checked"].append("model-drift")
        checked_any = True
        md = model_drift(d19_text, code_text)
        if md["drift"]:
            result["model_drift"] = {"design_only": md["design_only"], "code_only": md["code_only"]}
            problems = True

    # --- B16-3: D-27 / D-26 not citing a STALE D-02 version ---
    if d02_text is not None:
        declared = doc_version(d02_text)
        if declared is not None:
            citing: dict[str, str] = {}
            if d27_text is not None:
                citing["D-27"] = d27_text
            if d26_text is not None:
                citing["D-26"] = d26_text
            if citing:
                result["checked"].append("d27-stale")
                checked_any = True
                stale = version_coherence({"D-02": declared}, citing)
                if stale:
                    result["stale_citations"] = stale
                    problems = True

    structure_ok = (not problems) and checked_any
    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=[
            "matrix code_ref/test_ref path tokens resolve to real files (if --code-dir)",
            "every D-02 REQ has a matrix row (if --d02)",
            "no model-level code↔D-19 drift (if --d19 + code)",
            "no D-27/D-26 citing a stale D-02 version (if --d02 + D-27/D-26)",
        ],
        not_checked=[
            "whether a referenced test ACTUALLY exercises its REQ (LLM/human review)",
            "whether a reported pass/fail is truthful (it's a different file)",
            "structural sanity that a fixture activates the branch under test (LLM/human review)",
            "the acceptance decision itself (hbc-acceptance-check)",
        ],
    )
    if not checked_any:
        v["note"] = ("No verifiable input given (need --code-dir and/or --d02/--d19); "
                     "nothing was reconciled — not a meaningful green.")
    v.update(result)
    v["verified"] = structure_ok
    return v


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify matrix refs are real + model not drifted (B16-1/B16-3).")
    parser.add_argument("--matrix", required=True, help="Path to the per-feature traceability matrix")
    parser.add_argument("--d02", help="Path to D-02 requirements (matrix completeness + stale-citation authority)")
    parser.add_argument("--d19", help="Path to D-19 ER diagram (model-drift design side)")
    parser.add_argument("--code-dir", dest="code_dir", help="Feature code root (ref existence + model-drift code side)")
    parser.add_argument("--code-glob", dest="code_glob", default=DEFAULT_CODE_GLOB,
                        help=f"Glob under --code-dir for persistent-model source (default: {DEFAULT_CODE_GLOB})")
    parser.add_argument("--d27", help="Path to D-27 test spec (stale-citation check)")
    parser.add_argument("--d26", help="Path to D-26 test plan (stale-citation check)")
    parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    matrix_text = _read(args.matrix)
    if matrix_text is None:
        print(json.dumps({"error": f"matrix not readable: {args.matrix}", "verified": False,
                          "reason": "matrix_unreadable"}, ensure_ascii=False))
        return 2

    code_dir = Path(args.code_dir) if args.code_dir else None
    code_text = _read_code(args.code_dir, args.code_glob)
    d19_text = _read(args.d19)
    # model-drift needs BOTH design + code; warn (don't silently green) if only one.
    if (d19_text is None) != (code_text is None):
        print("WARNING: model-drift needs BOTH --d19 and --code-dir; only one given → drift skipped.",
              file=sys.stderr)
        d19_text = None
        code_text = None

    result = verify(
        matrix_text,
        d02_text=_read(args.d02),
        d19_text=d19_text,
        code_text=code_text,
        code_dir=code_dir,
        d27_text=_read(args.d27),
        d26_text=_read(args.d26),
    )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "verified": False}, ensure_ascii=False))
            return 2
        print(f"Ref-verification report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
