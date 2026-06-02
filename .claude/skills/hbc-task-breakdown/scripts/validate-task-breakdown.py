#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a task breakdown document.

Checks task IDs, dependency ordering, entity coverage against D-19,
and test case assignment against D-27.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# --- shared lib bootstrap (Đợt 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import SEMANTIC_NA, verdict  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

TASK_ID_RE = re.compile(r"TASK-(\d{3,})")
TC_ID_RE = re.compile(r"TC-(\d{3,})")
ENTITY_RE = re.compile(r"```mermaid.*?erDiagram(.*?)```", re.DOTALL)
ENTITY_NAME_RE = re.compile(r"^\s*(\w+)\s*\{", re.MULTILINE)

TASK_ROW_RE = re.compile(
    r"\|\s*(TASK-\d{3,})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|"
)


def check_task_ids(content: str) -> list[dict]:
    issues: list[dict] = []
    rows = TASK_ROW_RE.findall(content)

    if not rows:
        issues.append({
            "type": "NO_TASKS",
            "message": "No TASK-xxx rows found in task table",
            "auto_fixable": False,
        })
        return issues

    ids = []
    for row in rows:
        task_id = row[0]
        num = int(re.search(r"\d+", task_id).group())
        ids.append(num)

    seen: set[int] = set()
    for num in ids:
        if num in seen:
            issues.append({
                "type": "TASK_ID_DUPLICATE",
                "message": f"TASK-{num:03d} is duplicated",
                "auto_fixable": True,
            })
        seen.add(num)

    return issues


def check_dependencies(content: str) -> list[dict]:
    issues: list[dict] = []
    rows = TASK_ROW_RE.findall(content)

    task_order = {}
    for idx, row in enumerate(rows):
        task_id = row[0]
        task_order[task_id] = idx

    for row in rows:
        task_id = row[0]
        deps_str = row[6].strip()
        if not deps_str or deps_str == "-":
            continue

        dep_ids = [d.strip() for d in deps_str.split(",") if d.strip()]
        for dep in dep_ids:
            if dep not in task_order:
                issues.append({
                    "type": "UNKNOWN_DEPENDENCY",
                    "message": f"{task_id} depends on unknown {dep}",
                    "auto_fixable": False,
                })
            elif task_order[dep] >= task_order[task_id]:
                issues.append({
                    "type": "DEPENDENCY_ORDER",
                    "message": f"{task_id} depends on {dep} which appears later in the list",
                    "auto_fixable": True,
                })

    return issues


def check_entity_coverage(content: str, d19_path: str | None) -> list[dict]:
    issues: list[dict] = []
    if not d19_path:
        return issues

    try:
        d19_content = Path(d19_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues

    er_match = ENTITY_RE.search(d19_content)
    if not er_match:
        return issues

    entities = set(ENTITY_NAME_RE.findall(er_match.group(1)))
    if not entities:
        return issues

    # S-4: only the design_ref column of the task table counts as coverage —
    # an entity merely mentioned in prose/description is not "covered".
    design_refs = " ".join(row[2] for row in TASK_ROW_RE.findall(content)).lower()
    uncovered = [e for e in entities if e.lower() not in design_refs]

    for entity in uncovered:
        issues.append({
            "type": "ENTITY_NOT_COVERED",
            "message": f"D-19 entity '{entity}' has no corresponding task",
            "entity": entity,
            "auto_fixable": False,
        })

    return issues


def check_test_assignment(content: str, d27_path: str | None) -> list[dict]:
    issues: list[dict] = []
    if not d27_path:
        return issues

    try:
        d27_content = Path(d27_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues

    d27_tc_ids = set(TC_ID_RE.findall(d27_content))
    task_tc_ids = set(TC_ID_RE.findall(content))

    unassigned = d27_tc_ids - task_tc_ids
    for tc_num in sorted(unassigned):
        issues.append({
            "type": "TC_UNASSIGNED",
            "message": f"TC-{tc_num} from D-27 is not assigned to any task",
            "tc_id": f"TC-{tc_num}",
            "auto_fixable": False,
        })

    return issues


def validate(
    doc_path: str,
    d19_path: str | None = None,
    d27_path: str | None = None,
) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_task_ids(content))
    all_issues.extend(check_dependencies(content))
    all_issues.extend(check_entity_coverage(content, d19_path))
    all_issues.extend(check_test_assignment(content, d27_path))

    rows = TASK_ROW_RE.findall(content)

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=[
            "task id uniqueness",
            "dependency ordering / unknown deps",
            "D-19 entity coverage (design_ref column)",
            "D-27 test-case assignment",
        ],
        not_checked=[
            "task granularity / correctness (LLM review)",
            "REQ→task completeness (readiness gate)",
            "task type completeness incl UI/admin/service (LLM review)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "total_tasks": len(rows),
        "issues": all_issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate task breakdown.")
    parser.add_argument("document", help="Path to task-breakdown.md")
    parser.add_argument("--d19", help="Path to D-19 (entity coverage check)")
    parser.add_argument("--d27", help="Path to D-27 (test assignment check)")
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({"error": f"Not found: {args.document}"}))
        sys.exit(1)

    result = validate(str(doc_path), args.d19, args.d27)
    text = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
