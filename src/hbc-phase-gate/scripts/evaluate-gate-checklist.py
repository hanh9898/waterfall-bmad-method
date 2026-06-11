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
from pathlib import Path


def _is_entry_gate(item: dict) -> bool:
    """True for an item that asserts a PRIOR phase gate PASSED — a required CONTENT
    check over a gate report. Such items are never downgraded by lenient mode (B2):
    a phase must not proceed on top of a failed predecessor gate."""
    return bool(
        item.get("type") == "CONTENT"
        and item.get("required")
        and "gates/phase-" in item.get("artifact_pattern", "").replace("\\", "/")
    )


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
    """Substitute variables in artifact pattern."""
    result = pattern
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value)
    if not Path(result).is_absolute():
        result = str(Path(project_root) / result)
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
                found = re.findall(criteria, content)
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
    parser.add_argument("--verbose", action="store_true", help="Verbose diagnostics")
    args = parser.parse_args()

    variables = {}
    for v in args.var:
        key, _, value = v.partition("=")
        variables[key] = value

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
    pending_llm = sum(1 for r in results if r["status"] == "PENDING_LLM")
    gate_mode = variables.get("gate_mode", "strict")

    if entry_gate_failed > 0:
        overall_status = "FAILED"  # prior-gate failure blocks regardless of mode
    elif pending_llm > 0:
        overall_status = "PENDING_LLM"
    elif required_failed > 0:
        overall_status = "FAILED" if gate_mode == "strict" else "WARNING"
    else:
        overall_status = "PASSED"

    summary = {
        "total": len(results),
        "evaluated": sum(1 for r in results if r["status"] != "PENDING_LLM"),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
        "skipped": sum(1 for r in results if r["status"] == "SKIP"),
        "pending_llm": pending_llm,
        "required_failed": required_failed,
        "entry_gate_failed": entry_gate_failed,
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

    sys.exit(1 if summary["required_failed"] > 0 else 0)


if __name__ == "__main__":
    main()
