#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Cross-document version-coherence check (T1.3).

Catches a downstream document citing a STALE version of an upstream one — e.g.
D-26 says "per D-02 v2.2" while D-02 is actually v2.3 (the cross-doc staleness the
RCA case showed after the v2.0 model U-turn). Each passed document declares its own
version in frontmatter; that builds the authority map, and every other document is
scanned for version citations of those doc ids.

Historical revision-history rows ("synced to D-02 v1.6") are skipped — they
describe a past state, not a live cross-reference. Detection only. Exit: 0
coherent, 1 incoherence(s) found, 2 io error.

Run with `python` (Windows dev) or `python3` (Linux/Mac CI):
    python3 {skill-root}/scripts/check-version-coherence.py D-02.md D-19.md D-26.md D-27.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- shared lib bootstrap (C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        doc_version,
        version_coherence,
        verdict,
    )
    import re  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

_DOC_ID_FROM_FM = re.compile(r"^document_id:\s*[\"']?(D-\d{2})", re.MULTILINE)


def _doc_id(text: str, fallback: str) -> str:
    """Doc id from frontmatter `document_id:`, else the first D-NN in the filename."""
    m = _DOC_ID_FROM_FM.search(text)
    if m:
        return m.group(1)
    fm = re.search(r"D-\d{2}", fallback)
    return fm.group(0) if fm else fallback


def check(named_texts: dict[str, str]) -> dict:
    """named_texts: {label_or_path: text}. Builds authority map from declared
    versions, then flags stale citations across all docs."""
    authority: dict[str, str] = {}
    doc_ids: dict[str, str] = {}
    for label, text in named_texts.items():
        did = _doc_id(text, label)
        doc_ids[label] = did
        ver = doc_version(text)
        if ver is not None:
            authority[did] = ver

    issues = version_coherence(authority, named_texts)
    structure_ok = not issues
    v = verdict(structure_ok, semantic_review=SEMANTIC_NA,
                checked=["downstream docs cite the current version of each upstream doc"],
                not_checked=["whether the cited *content* is actually in sync (readiness/LLM)"])
    v.update({
        "valid": structure_ok,
        "total_issues": len(issues),
        "authority_versions": authority,
        "issues": [{"type": "VERSION_INCOHERENCE", "auto_fixable": False,
                    "message": f"{i['source']} cites {i['doc']} v{i['cited']} but {i['doc']} is v{i['declared']}",
                    **i} for i in issues],
    })
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-document version-coherence check (T1.3).")
    ap.add_argument("docs", nargs="+", help="D-xx document paths (each declares version in frontmatter)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    named: dict[str, str] = {}
    try:
        for d in args.docs:
            named[Path(d).name] = Path(d).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    result = check(named)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write {args.output}: {exc}", "valid": False}, ensure_ascii=False))
            return 2
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
