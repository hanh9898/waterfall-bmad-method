---
name: hbc-implement
description: "Implement code via TDD cycle per task. Use when user says 'implement', 'triển khai', 'coding', or agent menu [IM]."
---

# Implement

## Overview

Implement code via TDD cycle (RED → GREEN → REFACTOR) per task from the task breakdown. For each task, write failing tests first (from D-27 specs), then implementation code, then refactor to meet D-12 coding standards.

Per-task workflow: Load → RED (write test) → GREEN (implement) → REFACTOR → Update status. Supports batch mode (all tasks) and headless mode. The most interactive workflow — Dev agent pairs with the user throughout.

**Args:** `task <TASK-xxx>` (single task), `all` (batch remaining), `coverage` (check only). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: batch-implement all TODO tasks sequentially per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

Load `task-breakdown.md` from `{workflow.task_breakdown_path}`. Show task status summary: X TODO, Y IN_PROGRESS, Z DONE. If no task specified, suggest the next TODO task.

## Per-Task TDD Cycle

### Step 1: Load Context

Load the task's `design_ref` (D-19 entity or D-21 endpoint), `test_refs` (TC-xxx cases from D-27), and D-12 coding standards. Read `project-context.md` for framework-specific patterns.

### Step 2: RED — Write Failing Tests

Based on D-27 test cases for this task:
- Write test file(s) following D-12 test organization conventions.
- Tests must be specific and match D-27 expected results.
- Run the tests — they should FAIL (RED). If they pass, the test is wrong or the functionality already exists.

Present test code to user for review before proceeding.

### Step 3: GREEN — Implement

Write minimal implementation code to pass all tests from Step 2:
- Follow D-12 naming and formatting conventions.
- Use framework-specific patterns from `project-context.md`.
- Run tests after implementation — they should now PASS (GREEN).
- If tests still fail, iterate on implementation until green.

### Step 4: REFACTOR

With green tests as safety net:
- Clean up implementation: extract helpers, improve naming, remove duplication.
- Apply D-12 coding standards strictly.
- Run tests again — must stay GREEN after refactoring.

### Step 5: Update and Check

- Update task status to DONE in `task-breakdown.md` (a task is only DONE if it has an assigned test in `test_refs`).
- Update the traceability matrix `code_ref` for the REQ this task implements (so the matrix stays living, not back-filled at Phase 4).
- Check test coverage: `{workflow.coverage_command}`.
- If coverage below `{workflow.coverage_threshold}`: suggest additional tests.
- Return to agent menu or proceed to next task.

### Closeout: reconcile implementation reality (D2)

Before considering Phase 3 complete (and at the Phase 3 gate, item P3-02b), run:

```
python3 {skill-root}/scripts/validate-implementation.py --tasks <task-breakdown> --matrix <matrix> --project-root <root>
```

Must be clean — no `DONE_TASK_NO_TEST`, `MISSING_CODE_FILE`, or `REQ_NOT_IMPLEMENTED`. This catches tasks closed with no test, a `code_ref` pointing at a file that doesn't exist, or a REQ designed + tested but never implemented.

## Batch Mode

When `all` arg: iterate through remaining TODO tasks in dependency order. Pause between tasks for user checkpoint (skip pause in headless mode).

## Coverage Check

When `coverage` arg: run coverage command and report results without implementing.
