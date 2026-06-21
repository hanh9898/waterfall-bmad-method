#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Evaluate FILE, CONTENT, and METRIC checklist items deterministically.

Parses a phase gate checklist markdown table, evaluates each non-QUALITY item,
and returns structured JSON. QUALITY items are passed through unevaluated for
LLM judgment.
"""

import argparse
import glob
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# --- shared lib bootstrap (C-1) --- for MATRIX completeness (A9): the gate
# computes coverage numbers BY SCRIPT (B6-2) using the same primitives the
# create/readiness skills use, so "X/Y REQ covered" is never an LLM claim.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import matrix_coverage_gaps, missing_from_matrix, req_num_map
    _HAVE_SHARED = True
except ModuleNotFoundError:
    _HAVE_SHARED = False


def _is_entry_gate(item: dict) -> bool:
    """True for an item that asserts a PRIOR phase gate PASSED — a required CONTENT
    check over a gate report. Such items are never downgraded by lenient mode (B2):
    a phase must not proceed on top of a failed predecessor gate."""
    return bool(
        item.get("type") == "CONTENT"
        and item.get("required")
        and "gates/phase-" in item.get("artifact_pattern", "").replace("\\", "/")
    )


def _is_correctness_item(item: dict) -> bool:
    """True for a CORRECTNESS item — one whose FAIL means the artifacts are
    factually wrong / inconsistent, not merely thin (B6-3 extend · B6-4 · T2.7).

    Correctness items are non-negotiable: lenient mode never downgrades them to
    WARNING, and an `--na` waiver may never silence them (a waiver may skip an
    inapplicable deliverable, never a correctness check). Covers:
      - entry-gate (a prior phase gate must have PASSED), and
      - MATRIX completeness (every REQ traced — the RCA "39/39 green" false pass).
    Model-drift checks surface through MATRIX/QUALITY items that carry a
    `correctness` marker in their criteria cell (`[correctness]`).
    """
    if _is_entry_gate(item):
        return True
    if item.get("type") == "MATRIX" and item.get("required"):
        return True
    # Opt-in tag for QUALITY/CONTENT correctness items (e.g. MODEL_DRIFT clean):
    # author writes `[correctness]` in the description OR the criteria cell.
    tagged = "[correctness]" in (item.get("criteria") or "").lower() \
        or "[correctness]" in (item.get("description") or "").lower()
    return bool(item.get("required") and tagged)


def parse_checklist(checklist_path: str) -> list[dict]:
    """Parse markdown table rows into checklist items."""
    items = []
    text = Path(checklist_path).read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    in_table = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 6:
            continue
        if set(cells[0]) <= {"-", " "}:
            in_table = True
            continue
        if not in_table:
            if cells[0].lower() == "item_id":
                in_table = True
            continue

        items.append({
            "item_id": cells[0],
            "description": cells[1],
            "type": cells[2].upper(),
            "required": cells[3].lower() in ("yes", "true"),
            "artifact_pattern": cells[4],
            "criteria": cells[5] if len(cells) > 5 else "",
            "skill_to_create": cells[6].strip() if len(cells) > 6 and cells[6].strip() else "",
        })
    return items


def resolve_pattern(pattern: str, project_root: str, variables: dict) -> str:
    """Substitute variables in an artifact pattern, returning a forward-slash path.

    Cross-platform: `glob` accepts `/` on both Windows and POSIX, so normalising
    to forward slashes keeps behaviour (and test expectations) identical on each.
    `Path.is_absolute()` is platform-dependent — a POSIX `/abs` path is NOT
    absolute on Windows — so absoluteness is detected explicitly: a leading `/`
    or a drive-letter prefix (`C:`) both count.
    """
    result = pattern
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value)
    result = result.replace("\\", "/")
    is_absolute = result.startswith("/") or (len(result) >= 2 and result[1] == ":")
    if not is_absolute:
        result = project_root.replace("\\", "/").rstrip("/") + "/" + result
    return result


def _expand_matches(resolved: str) -> list[str]:
    """Glob a pattern, expanding any directory match to the markdown files inside.

    C-4 dir-aware resolution: a pattern like `.../D-06-*` that matches a workspace
    FOLDER resolves to the `.md` document(s) within it, not the directory itself —
    so FILE checks find a real file and CONTENT checks read the document instead of
    failing on a directory (the source of the confusing "1 file(s)" message).
    """
    out: list[str] = []
    for m in glob.glob(resolved, recursive=True):
        p = Path(m)
        if p.is_dir():
            out.extend(str(f) for f in sorted(p.rglob("*.md")))
        else:
            out.append(m)
    return out


def evaluate_file(pattern: str, project_root: str, variables: dict) -> dict:
    """Check if files matching glob pattern exist."""
    resolved = resolve_pattern(pattern, project_root, variables)
    matches = _expand_matches(resolved)
    if matches:
        return {
            "status": "PASS",
            "evidence": f"Found: {', '.join(Path(m).name for m in matches[:5])}",
            "matched_files": matches[:10],
        }
    keyword = Path(resolved).name.replace("*", "").replace("-", "").strip()
    near = []
    if keyword:
        near = glob.glob(str(Path(project_root) / "**" / f"*{keyword}*"), recursive=True)[:5]
    return {
        "status": "FAIL",
        "evidence": f"No files matching {resolved}",
        "matched_files": [],
        "near_matches": [str(Path(p).relative_to(project_root)) for p in near],
    }


def evaluate_content(
    pattern: str, criteria: str, project_root: str, variables: dict
) -> dict:
    """Check if file content matches regex criteria."""
    resolved = resolve_pattern(pattern, project_root, variables)
    # Handle comma-separated patterns (multiple artifacts)
    patterns = [p.strip() for p in resolved.split(",")]
    all_matches = []
    files_checked = []

    for pat in patterns:
        pat_resolved = pat if Path(pat).is_absolute() else str(Path(project_root) / pat)
        for fpath in _expand_matches(pat_resolved):
            files_checked.append(fpath)
            try:
                content = Path(fpath).read_text(encoding="utf-8")
                try:
                    found = re.findall(criteria, content)
                except re.error:
                    # criteria came from a gate-checklist cell and is not a
                    # valid regex (e.g. an escaped markdown pipe like
                    # "P2-03 \|..."). Degrade to a literal substring search so
                    # one malformed criterion can't crash the whole evaluator.
                    found = [criteria] if criteria in content else []
                if found:
                    for m in found[:3]:
                        for line_num, line in enumerate(content.splitlines(), 1):
                            if m in line:
                                all_matches.append(
                                    {"match": m, "file": Path(fpath).name, "line": line_num}
                                )
                                break
            except (OSError, UnicodeDecodeError):
                continue

    if not files_checked:
        return {
            "status": "FAIL",
            "evidence": f"No files found for pattern: {resolved}",
            "match_count": 0,
            "sample_matches": [],
        }

    return {
        "status": "PASS" if all_matches else "FAIL",
        "evidence": f"{len(all_matches)} matches in {len(files_checked)} file(s)"
        if all_matches
        else f"Pattern '{criteria}' not found in {len(files_checked)} file(s)",
        "match_count": len(all_matches),
        "sample_matches": all_matches[:5],
    }


def evaluate_metric(
    pattern: str, criteria: str, project_root: str, variables: dict
) -> dict:
    """Extract numeric value and compare against threshold in criteria."""
    resolved = resolve_pattern(pattern, project_root, variables)

    # Substitute variables in criteria
    resolved_criteria = criteria
    for key, value in variables.items():
        resolved_criteria = resolved_criteria.replace(f"{{{key}}}", str(value))

    matches = glob.glob(resolved, recursive=True)
    if not matches:
        return {
            "status": "FAIL",
            "evidence": f"No files matching {resolved}",
            "actual_value": None,
            "threshold": resolved_criteria,
        }

    # Try to extract a percentage or number from the file
    for fpath in matches:
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            numbers = re.findall(r"(\d+(?:\.\d+)?)\s*%", content)
            if numbers:
                # Find threshold in criteria
                threshold_match = re.search(r">=?\s*(\d+(?:\.\d+)?)", resolved_criteria)
                if threshold_match:
                    threshold = float(threshold_match.group(1))
                    actual = float(numbers[0])
                    return {
                        "status": "PASS" if actual >= threshold else "FAIL",
                        "evidence": f"Found {actual}% (threshold: {threshold}%)",
                        "actual_value": actual,
                        "threshold": threshold,
                    }
        except (OSError, UnicodeDecodeError, ValueError):
            continue

    return {
        "status": "SKIP",
        "evidence": f"Could not extract metric from files. Criteria: {resolved_criteria}",
        "actual_value": None,
        "threshold": resolved_criteria,
    }


def _semantic_review_status(text: str) -> str | None:
    """Extract frontmatter ``semanticReview.status`` (block or inline YAML).

    Returns the lowercased status (``pending``/``passed``/...) or None if absent.
    """
    # Trailing newline optional (F3): a file whose final line is `status: passed`
    # with no terminating newline must still parse. Status class allows hyphens.
    block = re.search(r"semanticReview:\s*\n((?:[ \t]+\S.*\n?)+)", text)
    if block:
        sm = re.search(r"status:\s*['\"]?([A-Za-z_-]+)", block.group(1))
        if sm:
            return sm.group(1).lower()
    inline = re.search(r"semanticReview:\s*\{[^}]*status:\s*['\"]?([A-Za-z_-]+)", text)
    return inline.group(1).lower() if inline else None


def evaluate_review(pattern: str, project_root: str, variables: dict) -> dict:
    """REVIEW item (#5): pass only when the target doc's frontmatter
    ``semanticReview.status`` is ``passed`` — the deterministic teeth that make
    the LLM semantic-review layer non-skippable. Missing/``pending`` → FAIL.
    """
    resolved = resolve_pattern(pattern, project_root, variables)
    files = _expand_matches(resolved)
    if not files:
        return {"status": "FAIL", "evidence": f"No files matching {resolved}", "review_status": {}}
    statuses: dict[str, str | None] = {}
    for fpath in files:
        try:
            statuses[Path(fpath).name] = _semantic_review_status(
                Path(fpath).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeDecodeError):
            statuses[Path(fpath).name] = None
    not_passed = {n: s for n, s in statuses.items() if s != "passed"}
    if not_passed:
        return {
            "status": "FAIL",
            "evidence": f"semanticReview not passed (need 'passed'): {not_passed}",
            "review_status": statuses,
        }
    return {
        "status": "PASS",
        "evidence": f"semanticReview passed in {len(statuses)} file(s)",
        "review_status": statuses,
    }


def evaluate_matrix(
    pattern: str, criteria: str, project_root: str, variables: dict
) -> dict:
    """MATRIX completeness (A9 · B6-2 · T1.5): every REQ defined in D-02 has a
    matrix row, and that row has a non-empty design_ref/code_ref/test_ref.

    Numbers are computed BY SCRIPT via the shared primitives — never LLM-claimed.
    The `artifact_pattern` is the per-feature traceability matrix; the criteria
    cell names the D-02 source (`d02=<glob>`) and, optionally, which columns must
    be non-empty (`cols=design_ref,test_ref`; default all three). This is a
    CORRECTNESS check — it caught the RCA "39/39 green but REQ-040/041/042 never
    in the matrix" false pass. FAIL when any REQ is missing or has a blank ref.
    """
    if not _HAVE_SHARED:
        return {
            "status": "CONTESTED",
            "evidence": "Cannot compute matrix completeness: shared lib hbc_validation "
            "not importable. Treated as CONTESTED (not PASS) — a gate must never "
            "pass when its evidence cannot be computed.",
            "missing_from_matrix": [], "coverage_gaps": {},
        }
    resolved = resolve_pattern(pattern, project_root, variables)
    matrix_files = _expand_matches(resolved)
    # Parse `d02=<glob>` and optional `cols=a,b` out of the criteria cell.
    d02_glob = ""
    cols = ("design_ref", "code_ref", "test_ref")
    dm = re.search(r"d02\s*=\s*([^\s;|]+)", criteria)
    if dm:
        d02_glob = dm.group(1)
    # `cols=a,b,c` — only comma-joined identifiers (no spaces). Anchored to stop at
    # the first non-[word/comma] char so trailing prose ("cols=a,b — every REQ…")
    # is NOT swallowed as bogus column names (which would mark a phantom column gap
    # on every row and FAIL the whole matrix for the wrong reason).
    cm = re.search(r"cols\s*=\s*([A-Za-z0-9_]+(?:,[A-Za-z0-9_]+)*)", criteria)
    if cm:
        cols = tuple(c.strip() for c in cm.group(1).split(",") if c.strip())
    d02_files = _expand_matches(resolve_pattern(d02_glob, project_root, variables)) if d02_glob else []

    if not matrix_files:
        return {"status": "FAIL", "evidence": f"No traceability matrix at {resolved}",
                "missing_from_matrix": [], "coverage_gaps": {}}
    if not d02_files:
        # Ambiguous: cannot establish the REQ universe → CONTESTED, not a silent pass (B6-6).
        return {"status": "CONTESTED",
                "evidence": f"No D-02 source resolvable (criteria d02={d02_glob!r}); "
                "cannot establish the REQ set to check coverage against.",
                "missing_from_matrix": [], "coverage_gaps": {}}
    try:
        matrix_text = "\n".join(Path(m).read_text(encoding="utf-8") for m in matrix_files)
        d02_text = "\n".join(Path(d).read_text(encoding="utf-8") for d in d02_files)
    except (OSError, UnicodeDecodeError) as exc:
        return {"status": "CONTESTED", "evidence": f"Cannot read matrix/D-02: {exc}",
                "missing_from_matrix": [], "coverage_gaps": {}}

    # Multi-feature matrix would collide trailing-number identity → don't trust count.
    d02_nums, d02_slugs = req_num_map(d02_text)
    total = len(d02_nums)
    if total == 0:
        # No REQ ids parsed from the D-02 source → the REQ universe is unknown.
        # An empty/unparseable D-02 must NOT pass as "0 missing" (silent false-green).
        return {"status": "CONTESTED",
                "evidence": "D-02 source resolved but no REQ ids parsed — cannot "
                "establish the REQ set; treated as CONTESTED, not a pass.",
                "missing_from_matrix": [], "coverage_gaps": {}}
    missing = missing_from_matrix(d02_text, matrix_text)
    gaps = matrix_coverage_gaps(matrix_text, columns=cols)
    traced = total - len(missing)
    ok = not missing and not gaps
    parts = [f"{traced}/{total} D-02 REQs have a matrix row"]
    if missing:
        parts.append(f"MISSING rows: {', '.join(missing[:8])}" + (" …" if len(missing) > 8 else ""))
    if gaps:
        parts.append(f"{len(gaps)} row(s) with a blank {'/'.join(cols)}: "
                     + ", ".join(list(gaps)[:8]))
    if len(d02_slugs) > 1:
        parts.append(f"WARNING multi-feature matrix ({sorted(d02_slugs)}) — count may be unreliable")
    return {
        "status": "PASS" if ok else "FAIL",
        "evidence": "; ".join(parts),
        "missing_from_matrix": missing,
        "coverage_gaps": gaps,
        "traced": traced,
        "total": total,
    }


_DELIVERABLE_RE = re.compile(r"D-\d+")


def _item_deliverable(item: dict) -> str | None:
    """The D-NN deliverable a checklist item targets, parsed from its
    artifact_pattern (e.g. '.../D-19*' -> 'D-19'). Used to honor per-feature N/A
    waivers; None if the pattern names no deliverable."""
    m = _DELIVERABLE_RE.search(item.get("artifact_pattern") or "")
    return m.group(0) if m else None


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate FILE, CONTENT, METRIC, and REVIEW gate checklist items."
    )
    parser.add_argument("checklist", help="Path to phase gate checklist markdown file")
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Variable substitution as key=value (repeatable)",
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "--na",
        default="",
        help="Comma-separated deliverables N/A for this feature (e.g. D-19,D-21). "
             "Their checklist items report NA (waived, not FAIL). Resolve from D-02 "
             "frontmatter `na_deliverables`. Only applicable-if deliverables (D-19/D-21) "
             "should be waived — D-02/D-03/D-06 apply to every feature.",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose diagnostics")
    args = parser.parse_args()

    variables = {}
    for v in args.var:
        key, _, value = v.partition("=")
        variables[key] = value

    na_deliverables = {d.strip().upper() for d in args.na.split(",") if d.strip()}

    if args.verbose:
        print(f"Checklist: {args.checklist}", file=sys.stderr)
        print(f"Project root: {args.project_root}", file=sys.stderr)
        print(f"Variables: {variables}", file=sys.stderr)

    items = parse_checklist(args.checklist)
    if args.verbose:
        print(f"Parsed {len(items)} checklist items", file=sys.stderr)

    results = []
    for item in items:
        result = {
            "item_id": item["item_id"],
            "description": item["description"],
            "type": item["type"],
            "required": item["required"],
        }

        # Per-feature N/A waiver (DF-STRUCT): a deliverable declared N/A for this
        # feature passes as NA (not FAIL), so a feature that genuinely has no data
        # model / API isn't blocked by D-19/D-21. The judgment of WHAT is N/A + the
        # rationale lives in D-02 frontmatter `na_deliverables`; the gate only honors it.
        #
        # B6-4 (T2.7): a waiver may NOT silence a CORRECTNESS item. If a waived
        # deliverable's item is also a correctness check (entry-gate / matrix /
        # tagged), the waiver is REJECTED — the item is still evaluated and the
        # rejection recorded. A waiver skips inapplicable work; it never makes a
        # factually-broken artifact "pass".
        deliverable = _item_deliverable(item)
        if deliverable and deliverable.upper() in na_deliverables:
            if _is_correctness_item(item):
                result["waiver_rejected"] = (
                    f"--na {deliverable} ignored: this is a correctness item and may "
                    "not be waived (B6-4). Still evaluated below."
                )
            else:
                result["status"] = "NA"
                result["evidence"] = f"Waived: {deliverable} declared not-applicable for this feature (--na)."
                results.append(result)
                continue

        if item["type"] == "FILE":
            eval_result = evaluate_file(
                item["artifact_pattern"], args.project_root, variables
            )
            result.update(eval_result)
            if eval_result["status"] == "FAIL" and item.get("skill_to_create"):
                result["skill_to_create"] = item["skill_to_create"]
        elif item["type"] == "CONTENT":
            eval_result = evaluate_content(
                item["artifact_pattern"],
                item["criteria"],
                args.project_root,
                variables,
            )
            result.update(eval_result)
        elif item["type"] == "METRIC":
            eval_result = evaluate_metric(
                item["artifact_pattern"],
                item["criteria"],
                args.project_root,
                variables,
            )
            result.update(eval_result)
            # B6-6 ambiguous→CONTESTED: a REQUIRED metric whose number can't be
            # extracted must NOT silently SKIP into a pass — escalate to CONTESTED
            # so the gate cannot go green on un-evaluated correctness evidence.
            if eval_result["status"] == "SKIP" and item["required"]:
                result["status"] = "CONTESTED"
                result["evidence"] = (
                    "Required metric could not be extracted — ambiguous, treated as "
                    "CONTESTED (not a pass). " + eval_result.get("evidence", "")
                )
        elif item["type"] == "MATRIX":
            eval_result = evaluate_matrix(
                item["artifact_pattern"],
                item["criteria"],
                args.project_root,
                variables,
            )
            result.update(eval_result)
        elif item["type"] == "QUALITY":
            result["status"] = "PENDING_LLM"
            result["evidence"] = "Requires LLM judgment"
            result["criteria"] = item["criteria"]
            result["artifact_pattern"] = item["artifact_pattern"]
        elif item["type"] == "REVIEW":
            eval_result = evaluate_review(
                item["artifact_pattern"], args.project_root, variables
            )
            result.update(eval_result)
            # On a REVIEW FAIL, surface the owning doc-authoring skill so the
            # reviewer knows where to record the missing semantic-review status
            # (parity with the FILE branch).
            if eval_result["status"] == "FAIL" and item.get("skill_to_create"):
                result["skill_to_create"] = item["skill_to_create"]
        else:
            result["status"] = "SKIP"
            result["evidence"] = f"Unknown type: {item['type']}"

        results.append(result)

    required_failed = sum(
        1 for r in results if r["status"] == "FAIL" and r["required"]
    )
    # Entry-gate items assert a PRIOR phase gate PASSED — they are non-negotiable
    # and must NOT be downgraded to WARNING by lenient mode (B2). Identified
    # structurally: a required CONTENT check whose artifact is a gate report.
    entry_gate_failed = sum(
        1 for item, r in zip(items, results)
        if r["status"] == "FAIL" and r["required"] and _is_entry_gate(item)
    )
    # B6-3 extend (T2.7): a correctness item (entry-gate + matrix-completeness +
    # tagged model items) that definitively FAILs is never downgraded by lenient
    # mode — lenient relaxes thoroughness, never factual correctness.
    correctness_failed = sum(
        1 for item, r in zip(items, results)
        if r["status"] == "FAIL" and r["required"] and _is_correctness_item(item)
    )
    # B6-6: a required item the evaluator could not resolve (CONTESTED — ambiguous
    # evidence, or two lenses disagreeing) is NOT a pass. It blocks (a human must
    # adjudicate) and is never downgraded. A CONTESTED correctness item counts here,
    # not as a definitive FAIL — "can't compute" ≠ "proven broken".
    contested = sum(1 for r in results if r["status"] == "CONTESTED" and r["required"])
    pending_llm = sum(1 for r in results if r["status"] == "PENDING_LLM")
    gate_mode = variables.get("gate_mode", "strict")

    if correctness_failed > 0:
        overall_status = "FAILED"  # prior-gate / matrix / model correctness blocks regardless of mode
    elif pending_llm > 0:
        overall_status = "PENDING_LLM"
    elif contested > 0:
        # An unresolved CONTESTED required item is not a pass — neither strict nor
        # lenient may go green on un-adjudicated evidence.
        overall_status = "CONTESTED"
    elif required_failed > 0:
        overall_status = "FAILED" if gate_mode == "strict" else "WARNING"
    else:
        overall_status = "PASSED"

    summary = {
        "total": len(results),
        "evaluated": sum(1 for r in results if r["status"] not in ("PENDING_LLM", "CONTESTED")),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
        "skipped": sum(1 for r in results if r["status"] == "SKIP"),
        "contested": contested,
        "pending_llm": pending_llm,
        "required_failed": required_failed,
        "entry_gate_failed": entry_gate_failed,
        "correctness_failed": correctness_failed,
        "gate_mode": gate_mode,
        "overall_status": overall_status,
    }

    output = {"summary": summary, "results": results}

    text = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(text)

    # Non-zero when any required item failed OR any required item is CONTESTED — so
    # CI never reads "exit 0" as a clean gate on un-adjudicated/ambiguous evidence.
    sys.exit(1 if (summary["required_failed"] > 0
                   or summary["correctness_failed"] > 0
                   or summary["contested"] > 0) else 0)


if __name__ == "__main__":
    # B6-6 (T1.6, gate-robust): an evaluator CRASH must become BLOCKED, never a
    # silent PASS. Any unhandled exception is caught here, emitted as a BLOCKED
    # JSON the caller can recognize, and exits non-zero — a crashed gate never
    # produces exit 0 (which a CI step would read as "passed").
    try:
        main()
    except SystemExit:
        raise  # main()'s own intentional exit codes pass through unchanged
    except BaseException as exc:  # noqa: BLE001 — last-resort: must not become a pass
        import traceback
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "evaluator_crashed",
            "evidence": f"{type(exc).__name__}: {exc}",
            "summary": {"overall_status": "BLOCKED"},
        }, ensure_ascii=False))
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)
