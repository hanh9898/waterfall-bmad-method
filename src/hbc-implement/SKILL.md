---
name: hbc-implement
description: "Implement code via TDD cycle per task. Use when user says 'implement', 'triển khai', 'coding', or agent menu [IM]."
---

# Implement

## Overview

Implement code via TDD cycle (RED → GREEN → REFACTOR) per task from the task breakdown. For each task, write failing tests first (from D-27 specs), then implementation code, then refactor to meet D-12 coding standards.

Per-task workflow: Load → RED (write test) → GREEN (implement) → REFACTOR → Update status. Supports batch mode (all tasks) and headless mode. The most interactive workflow — Dev agent pairs with the user throughout.

**Args:** `task <TASK-xxx>` (single task), `all` (batch remaining), `coverage` (check only); **`feature=<slug>`** (required in headless; interactive uses the active feature in the session). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: batch-implement all TODO tasks sequentially per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

**Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask. Required in headless (missing → `blocked` `feature_required`). All paths (`{workflow.task_breakdown_path}`, `{workflow.tdd_evidence_dir}`) are namespaced by `{feature}`.

Load `task-breakdown.md` from `{workflow.task_breakdown_path}`. Show task status summary: X TODO, Y IN_PROGRESS, Z DONE. If no task specified, suggest the next TODO task.

## Per-Task TDD Cycle

### Step 1: Load Context

Load the task's `design_ref` (D-19 entity or D-21 endpoint), `test_refs` (TC-xxx cases from D-27), and D-12 coding standards. Read `project-context.md` for framework-specific patterns.

### Step 2: RED — Write Failing Tests

Based on D-27 test cases for this task:
- Write test file(s) following D-12 test organization conventions.
- Tests must be specific and match D-27 expected results.
- Run the tests — they should FAIL (RED). If they pass, the test is wrong or the functionality already exists.
- **Save RED-evidence (process enforcement):** record the FAIL test run into `{workflow.tdd_evidence_dir}/<TASK-xxx>.md` (the command run + output containing a `FAIL` line). **HALT — do NOT move to GREEN / write code until RED-evidence exists for this task.** *(Note: RED-evidence is **self-attested** — a soft enforcement at the process level: the Phase 3 gate only checks that the evidence **exists / has been recorded**, NOT a tamper-proof cryptographic proof. This is intentional — soft TDD.)*

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
python3 {skill-root}/scripts/validate-implementation.py --tasks <task-breakdown> --matrix <matrix> --tdd-evidence-dir {workflow.tdd_evidence_dir} --project-root <root>
```

Must be clean — no `DONE_TASK_NO_TEST`, `NO_RED_EVIDENCE`, `RED_EVIDENCE_NO_FAIL`, `MISSING_CODE_FILE`, or `REQ_NOT_IMPLEMENTED`. This catches tasks closed with no test, a `code_ref` pointing at a file that doesn't exist, or a REQ designed + tested but never implemented.

## Batch Mode

When `all` arg: iterate through remaining TODO tasks in dependency order. Pause between tasks for user checkpoint (skip pause in headless mode).

## Coverage Check

When `coverage` arg: run coverage command and report results without implementing.

## Sync Handoff (hbc-traceability impact integration)

Applies when re-implementing due to an upstream change. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop. (hbc-traceability impact invokes this skill as the `code` cascade node per BR-08.)
- **Hybrid trigger (default):** after a successful implementation change, suggest: _"Code updated. Run `hbc-traceability impact` to sync the traceability matrix?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly. Default is false.
