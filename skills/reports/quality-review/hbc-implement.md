---
skill: hbc-implement
reviewed_at: "2026-05-28"
verdict: PASS
---

# Quality Review: hbc-implement

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 76 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS** |

## Checklist
- [x] Description format — correct 2-sentence format with quoted trigger phrases
- [x] Conventions block (4 canonical lines) — all 4 present
- [x] customize.toml required fields — activation_steps_prepend, activation_steps_append, persistent_facts all present
- [x] Path references ({workflow.*} not hardcoded) — task_breakdown_path, coverage_command, coverage_threshold all via {workflow.*}
- [~] Size within guidance — 76 lines, slightly below 80-line guidance floor but appropriate for this skill's focused scope
- [x] Outcome-based instructions — TDD cycle described as goals (RED/GREEN/REFACTOR), not micro-steps
- [x] Intelligence placement correct — no scripts needed; coverage command is delegated to project tooling via {workflow.coverage_command}; all judgment is LLM
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented — section present with contract reference
- [x] Lint clean — no path or script findings

## Findings

1. **LOW: Slightly below size floor.** At 76 lines, this is 4 lines below the 80-line guidance minimum. However, this skill is tightly scoped (TDD cycle per task) and does not benefit from padding. The brevity is a strength given its focused purpose.

2. **NOTE: No scripts directory content.** The `scripts/tests/` directory exists but is empty. This is fine -- the skill delegates all deterministic work to the project's own test/coverage tooling via `{workflow.coverage_command}` rather than shipping its own scripts. This is the correct design for an implementation skill.

3. **NOTE: coverage_command auto-detection.** The customize.toml comment says "auto-detected from project-context.md if empty" but SKILL.md does not document this auto-detection behavior. Minor gap.

## Recommendations

1. Add one sentence to the On Activation section noting that an empty `coverage_command` triggers auto-detection from `project-context.md`. This makes the behavior explicit for customizers reading SKILL.md.
