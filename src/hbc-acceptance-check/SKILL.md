---
name: hbc-acceptance-check
description: "Final acceptance evaluation with ACCEPTED/REJECTED/DEFERRED/PENDING decisions. Use when user says 'acceptance', '受入確認', 'nghiệm thu', or agent menu [AC]."
---

# Acceptance Check

## Overview

Final acceptance evaluation — review all lifecycle artifacts, test execution results, and traceability for sign-off. Produces a formal acceptance report with one of four decisions: ACCEPTED, REJECTED, DEFERRED, or PENDING. The `acceptance_owner` (from config) makes the decision; this workflow presents evidence.

Four-stage workflow: Prerequisites → Review → Decide → Report. Supports headless mode. Requires Python 3.10+ for validation scripts.

**Args:** `review` (default — full acceptance review), `status` (check current decision without re-review). Optional: `--headless` / `-H`.

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

Load all evidence for the acceptance review:
- **Test execution report** from `{workflow.input_test_report}`.
- **Traceability matrix** from `{workflow.input_traceability}`.
- **Gate reports** from `{workflow.input_gates}/phase-*-gate.md`.
- **D-02 Requirements** from `{workflow.input_requirements}/D-02-*.md` (requirement count).

If test execution report missing, block with warning. Other artifacts are recommended but not blocking.

## Stage 2: Review

Walk through acceptance criteria checklist:

| Criterion | Check Method |
|-----------|-------------|
| All requirements traced | Traceability matrix — every REQ has design_ref, code_ref, test_ref |
| All tests passed | Test execution report — 0 failed |
| Coverage meets threshold | Test execution report — coverage_pct ≥ `{workflow.coverage_threshold}` |
| Phase 1 gate passed | Gate report exists with PASSED status |
| Phase 2 gate passed | Gate report exists with PASSED status |
| Phase 3 gate passed | Gate report exists with PASSED status |
| No open critical defects | Test execution report — no unresolved critical defects |

For each criterion, produce: status (PASS/FAIL/SKIP), evidence (file path + relevant metric).

Present review summary to user (or `acceptance_owner` if different from user).

## Stage 3: Decide

Record the acceptance decision:

| Decision | Meaning |
|----------|---------|
| `ACCEPTED` | All criteria met — project deliverable complete |
| `REJECTED` | Blocking issues found — return to specific phase for fixes |
| `DEFERRED` | Acceptable with known issues — document and proceed with caveats |
| `PENDING` | Insufficient information — need more data before deciding |

If `REJECTED`: specify which phase to return to based on defect type (Phase 1 for spec issues, Phase 2 for test gaps, Phase 3 for code bugs).

The `acceptance_owner` (from `{workflow.acceptance_owner}` config) decides. In interactive mode, present evidence and ask for decision. In headless mode, auto-decide based on criteria (all PASS → ACCEPTED, any FAIL → REJECTED).

## Stage 4: Report

Write to `{workflow.output_dir}/acceptance-report.md`:

```markdown
---
title: "{project_name} Acceptance Report"
decided_at: ""
decided_by: "{acceptance_owner}"
decision: "ACCEPTED | REJECTED | DEFERRED | PENDING"
---

## Acceptance Criteria Checklist

| Criterion | Status | Evidence |
|-----------|--------|----------|

## Traceability Summary

| Metric | Value |
|--------|-------|
| Total Requirements | {total_reqs} |
| Designed | {designed} |
| Implemented | {implemented} |
| Tested | {tested} |
| Trace Coverage | {coverage_pct}% |

## Decision

**Status:** {decision}
**Decided by:** {acceptance_owner}
**Reason:** {reason}

## Action Items (if REJECTED or DEFERRED)

| Item | Phase | Description | Priority |
|------|-------|-------------|----------|
```

Run validation:

```
python3 {workflow.validation_script} "{workflow.output_dir}/acceptance-report.md"
```

Finalize. If ACCEPTED: _"Project accepted. Run Phase 4 gate [PG] to finalize."_ If REJECTED: _"Rejected — {n} blocking issues. Return to Phase {x} for fixes."_
