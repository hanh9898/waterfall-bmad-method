---
skill: hbc-task-breakdown
reviewed_at: "2026-05-28"
verdict: PASS
---

# Quality Review: hbc-task-breakdown

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 99 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS** |

## Checklist
- [x] Description format — `"Break down design artifacts into granular TDD tasks. Use when user says 'task breakdown', 'tasuku bunkai', 'phan chia task', or agent menu [TB]."` Correct format, trigger phrases quoted, multi-language triggers.
- [x] Conventions block (4 canonical lines) — All 4 present at lines 18-21.
- [x] customize.toml required fields — `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` all present.
- [x] Path references — All paths use `{workflow.*}` or `{project-root}` properly. No hardcoded paths.
- [x] Size within guidance — 99 lines for a 5-stage workflow. Clean and well-scoped.
- [x] Outcome-based instructions — Stages describe what to produce, not how to think. Analysis section (Stage 2) defines categories and required fields without over-prescribing.
- [x] Intelligence placement correct — Validation script handles deterministic checks (coverage, circular deps, uniqueness). LLM handles decomposition judgment and dependency ordering.
- [x] Core test passes — Task decomposition is a judgment task that genuinely needs the design_ref/test_refs/dependencies structure spelled out.
- [x] Headless mode documented — Line 25, references `references/headless-contract.md`. Concise.
- [x] Lint clean — Zero findings.

## Findings

No issues found. This is a clean, well-structured skill.

## Recommendations

None. This skill can serve as a reference example for the quality standard.
