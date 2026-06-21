---
name: hbc-test-execution
description: "Execute test suites and generate execution report. Use when user says 'test execution', 'chạy test', 'run tests', or agent menu [TE]."
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

> **Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask (headless: required, if missing → blocked `feature_required`). Substitute `{feature}` in every workflow path.

## Stage 1: Prerequisites

**Phase-entry gate (enforced, overridable).** This skill opens Phase 4. First verify the **Phase 3 gate PASSED** — run `hbc-phase-gate` for phase 3 headless (`-H`) and read `overall_status`. If not `PASSED`, **HALT** and report the failing items; proceed only on an explicit user override (record it in the execution report). In headless mode a non-PASSED Phase 3 gate returns `blocked`. Tests must run against implementation-complete, gated code — not a half-finished Phase 3.

Then verify test environment readiness:
- **Test runner** available (detect from `project-context.md` or `{workflow.test_command}`).
- **D-27** exists — load test case inventory for result mapping.
- **Code** is at a known state (clean git working tree recommended).

**D-27 presence (D-27 gate).** D-27 is the test-case inventory results map to. If it is not found:
- **Interactive** — warn but allow execution (results won't map to TC-xxx IDs); record the warning in the report. The user accepts the lost TC mapping.
- **Headless** — return `blocked` (reason `no_test_spec`). Do NOT silently run a headless suite with no D-27: with no inventory to reconcile against, a "passed" result would silently hide unrun TCs (the D1 reconciliation in Stage 5 has nothing to check). Headless callers must supply D-27 or accept the block.

**Verify the suite runs against the RIGHT artifacts (B16-1, B16-3).** A green run is worthless if it ran against renamed/missing code, an incomplete matrix, or a stale spec — "87/87 passed" against the OLD model is the cardinal Phase-4 false-green. Before trusting results, run the ref-verifier — it does NOT trust matrix strings; it checks the referenced files exist on disk and reconciles design↔code↔spec-version via the shared primitives (`model_drift`, `missing_from_matrix`, `version_coherence`):

```
python3 {workflow.verify_refs_script} --matrix <matrix> --d02 <D-02> \
  [--d19 <D-19> --code-dir <feature code root>] [--d27 <D-27>] [--d26 <D-26>]
```

Surfaces `missing_code_ref`/`missing_test_ref` (a matrix ref pointing at a file that does not exist — B16-1), `missing_from_matrix` (a D-02 REQ with no row — B16-1), `model_drift` (tests ran against a model the design abandoned — B16-1), `stale_citations` (D-27/D-26 citing a superseded D-02 version — B16-3). Any non-empty set means the run is verifying the wrong thing: record it prominently in the report and treat the suite as **not trustworthy as-is** — do not present a clean PASS over a drifted/incomplete substrate. This is an existing-gate fix, not new ceremony.

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

**Anti-false-green sanity (B16-2).** A passing test is not automatically meaningful. When reporting, flag a *suspicious pass* — a test whose fixture may not actually activate the branch it claims to cover (e.g. asserts only on a no-op path, or the model under test drifted per the B16-1 check so the assertion targets the wrong code). You cannot prove a fixture exercises a branch with structure alone (that is an LLM/human judgement, listed in the verifier's `not_checked`), so do not silently upgrade "green" to "verified" — surface the candidates so acceptance ([AC]) can weigh them. Coverage % is necessary-but-not-sufficient.

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

Run validation — pass `--d27` so executed TCs are reconciled against the specified set (D1):

```
python3 {workflow.validation_script} "{workflow.output_dir}/test-execution-report.md" --threshold {workflow.coverage_threshold} --d27 "<D-27 path>"
```

A `TC_UNEXECUTED` issue means a test specified in D-27 has no result here — "all passed" must not hide a test that was never run. `TC_PHANTOM_RESULT` means a result references a TC not in D-27. Resolve both before finalizing.

Also fold the B16-1/B16-3 ref-verification result (from Stage 1) into the report — `missing_code_ref`, `missing_test_ref`, `missing_from_matrix`, `model_drift`, `stale_citations`. A clean coverage number over a drifted/incomplete substrate must NOT read as a trustworthy PASS.

Finalize. Suggest next: _"Execution complete. {passed}/{total} passed ({coverage_pct}% coverage). Next: `hbc-acceptance-check` [AC]."_

## Autonomy (A5)

Separate **mechanical** from **domain** decisions. Mechanical — detecting the test runner, mapping results to TC ids, formatting the report, running the verifier and reconciliation engines, classifying an obvious `environment` failure — decide and proceed. Surfacing a drifted/missing-ref/stale-spec finding is mechanical too: report it, never soft-pedal a real drift into a clean PASS.

Domain — whether a *suspicious pass* truly exercises its branch, or whether a surfaced gap (a missing ref, an unrun TC) is an acceptable deliberate deferral versus a real omission. **ASK; never fabricate that a green is "fine".** TE only *executes and reports*; the accept judgement is [AC]'s.

Headless resolves this two ways:
- `--strict` — stop at the first finding that needs a human call (suspicious pass, possible deferral) and return `blocked` with the question; do not assume.
- `--assumptions-allowed` (default in CI) — treat every surfaced finding as real (the safe, non-green default), log that no deferral was confirmed, and return the honest `FAIL`/`PARTIAL` status rather than blocking the first turn. CI never gets a false green.

## Churn / semantic-review (T2.11 / T2.12) — N/A

A test-execution report is an **execution record**, not a versioned D-xx deliverable. It is regenerated each run, not edited over time, so there is no revision-history churn to assess (T2.11 N/A) and no document-semantics to gate via `semanticReview` frontmatter (T2.12 N/A). The meaning layer here is the anti-false-green sanity (B16-2) + the ref/drift/stale reconciliation (B16-1/B16-3), reported for [AC] to weigh — not a churn/semantic-review record.
