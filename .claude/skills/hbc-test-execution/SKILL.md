---
name: hbc-test-execution
description: "Execute test suites and generate execution report. Use when user says 'test execution', 'テスト実行', 'chạy test', 'run tests', or agent menu [TE]."
---

# Test Execution

## Overview

Execute test suites (unit, integration, E2E), collect results, map them to D-27 test case IDs, classify failures, and generate an execution report. The bridge between implementation (Phase 3) and acceptance (Phase 4) — fresh eyes on test results, not the developer who wrote them.

Five-stage workflow: Prerequisites → Execute → Collect → Triage → Report. Supports headless mode. Requires Python 3.10+ for validation scripts.

**Args:** `all` (default — run full suite), `unit` / `integration` / `e2e` (specific category), `report` (generate from existing results). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

## Stage 1: Prerequisites

Verify test environment readiness:
- **Test runner** available (detect from `project-context.md` or `{workflow.test_command}`).
- **D-27** exists — load test case inventory for result mapping.
- **Phase 3 gate** passed — tests should run against implementation-complete code.
- **Code** is at a known state (clean git working tree recommended).

If D-27 not found, warn but allow execution (results won't map to TC-xxx IDs).

## Stage 2: Execute

Run test suites using project's test runner:

```
{workflow.test_command}
```

If `test_command` is empty, auto-detect from `project-context.md`:
- Python: `pytest --tb=short -v`
- Node: `npm test` or `npx jest --verbose`
- Other: ask user for command

Capture stdout/stderr and exit code. For E2E tests, use `{workflow.e2e_command}` separately.

## Stage 3: Collect

Parse test output into structured results:
- Total tests, passed, failed, skipped, errors.
- Coverage percentage (from `{workflow.coverage_command}` if configured).
- Map failed tests to D-27 TC-xxx IDs where possible (match by test name or file convention).

Present raw summary to user for verification.

## Stage 4: Triage

Classify each failure:

| Classification | Meaning | Action |
|---------------|---------|--------|
| `code_bug` | Implementation error | Return to Dev (Phase 3) |
| `test_bug` | Test itself is wrong | Return to QA (Phase 2) |
| `missing_coverage` | No test for requirement | Return to QA (Phase 2) |
| `environment` | Infra/config issue | Fix environment, re-run |
| `spec_issue` | Requirement unclear/wrong | Escalate to BA (Phase 1) |

For each failed test, suggest classification. User confirms or overrides.

## Stage 5: Report

Write to `{workflow.output_dir}/test-execution-report.md`:

```markdown
---
title: "{project_name} Test Execution Report"
executed_at: ""
total: 0
passed: 0
failed: 0
skipped: 0
coverage_pct: 0
status: "PASS | FAIL | PARTIAL"
---

## Test Execution Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Skipped | {skipped} |
| Coverage | {coverage_pct}% |

## Failed Tests Detail

| test_id | test_case_ref | error | classification |
|---------|---------------|-------|----------------|

## Defect Triage

| defect_id | type | action | assigned_to |
|-----------|------|--------|-------------|
```

Run validation:

```
python3 {workflow.validation_script} "{workflow.output_dir}/test-execution-report.md"
```

Finalize. Suggest next: _"Execution complete. {passed}/{total} passed ({coverage_pct}% coverage). Next: `hbc-acceptance-check` [AC]."_
