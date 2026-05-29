---
skill: hbc-create-test-plan
reviewed_at: "2026-05-28"
verdict: NEEDS_WORK
---

# Quality Review: hbc-create-test-plan

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 111 |
| Path findings | 1 (hardcoded scan script path) |
| Script findings | 1 (scan script referenced but does not exist) |
| Verdict | **NEEDS_WORK** |

## Checklist
- [x] Description format — correct 2-sentence format with quoted trigger phrases
- [x] Conventions block (4 canonical lines) — all 4 present
- [x] customize.toml required fields — activation_steps_prepend, activation_steps_append, persistent_facts all present
- [~] Path references ({workflow.*} not hardcoded) — validation_script uses {workflow.*}; scan script on line 36 is hardcoded AND the file does not exist
- [x] Size within guidance — 111 lines, within 80-130 range
- [x] Outcome-based instructions — stages describe goals, soft-gates present
- [x] Intelligence placement correct — validation in script, judgment in LLM
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented — section present with contract reference
- [ ] Lint clean — phantom scan script reference is a functional gap

## Findings

1. **HIGH: Scan script does not exist.** SKILL.md line 36 references `scripts/scan-test-plan-sources.py` but this file is not present in `src/hbc-create-test-plan/scripts/`. Only `validate-test-plan.py` exists. Stage 1a will fail at runtime when the LLM tries to execute this script. The SKILL.md has no fallback clause for a missing scan script (unlike the validation step which has "If the script is unavailable, fall back to LLM-only validation").

2. **MEDIUM: No scan_script key in customize.toml.** Even once the scan script is created, the path should be liftable to customize.toml as `scan_script` (matching the glossary pattern) so teams can override it.

3. **NOTE: Validation script has tests.** `scripts/tests/test-validate-test-plan.py` exists and covers the validation script. Only the scan script is missing entirely.

## Recommendations

1. **Create `scripts/scan-test-plan-sources.py`** to match the contract described in Stage 1a: accept `--project-root` and `--output-dir`, return JSON with `state`, `existing_d26`, `d02_path`, `d06_path`, `framework`, `project_context_path`.
2. Add `scan_script = "scripts/scan-test-plan-sources.py"` to customize.toml and update SKILL.md line 36 to `{workflow.scan_script}`.
3. Add a fallback clause to Stage 1a: "If scan script is unavailable, fall back to LLM-driven project scan."
4. Write unit tests for the new scan script.
