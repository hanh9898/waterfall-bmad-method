---
skill: hbc-test-execution
reviewed_at: "2026-05-28"
verdict: PASS
---

# Quality Review: hbc-test-execution

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 122 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS** |

## Checklist
- [x] Description format — `"Execute test suites and generate execution report. Use when user says 'test execution', 'tesuto jikko', 'chay test', 'run tests', or agent menu [TE]."` Correct format, trigger phrases quoted, multi-language.
- [x] Conventions block (4 canonical lines) — All 4 present at lines 18-21.
- [x] customize.toml required fields — `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` all present. Also includes `test_command`, `e2e_command`, `coverage_command`, `coverage_threshold` -- good customization surface.
- [x] Path references — All paths use `{workflow.*}` or `{project-root}`. No hardcoded paths.
- [x] Size within guidance — 122 lines for a 5-stage workflow with triage classification. Within multi-branch budget.
- [x] Outcome-based instructions — Stage 4 (Triage) uses a classification table rather than a decision tree. LLM applies judgment to classify, user confirms. Clean design.
- [x] Intelligence placement correct — Validation script handles deterministic checks. LLM handles failure classification (judgment) and test-to-TC mapping (requires understanding).
- [x] Core test passes — The failure classification taxonomy (code_bug, test_bug, missing_coverage, environment, spec_issue) is genuinely needed -- LLM would not produce this consistent taxonomy without it.
- [x] Headless mode documented — Line 25, references `references/headless-contract.md`.
- [x] Lint clean — Zero findings.

## Findings

No issues found.

## Recommendations

None. Clean skill with a well-designed customize.toml that exposes the right knobs (test commands, coverage threshold) without over-configuring.
