---
skill: hbc-create-test-spec
reviewed_at: "2026-05-28"
verdict: NEEDS_WORK
---

# Quality Review: hbc-create-test-spec

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 109 |
| Path findings | 1 (hardcoded scan script path) |
| Script findings | 1 (scan script referenced but does not exist) |
| Verdict | **NEEDS_WORK** |

## Checklist
- [x] Description format — correct 2-sentence format with quoted trigger phrases
- [x] Conventions block (4 canonical lines) — all 4 present
- [x] customize.toml required fields — activation_steps_prepend, activation_steps_append, persistent_facts all present
- [~] Path references ({workflow.*} not hardcoded) — validation_script uses {workflow.*}; scan script on line 36 is hardcoded AND the file does not exist
- [x] Size within guidance — 109 lines, within 80-130 range
- [x] Outcome-based instructions — stages describe goals, batched discovery with soft-gates
- [x] Intelligence placement correct — validation in script, judgment in LLM
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented — section present with contract reference
- [ ] Lint clean — phantom scan script reference is a functional gap

## Findings

1. **HIGH: Scan script does not exist.** SKILL.md line 36 references `scripts/scan-test-spec-sources.py` but this file is not present in `src/hbc-create-test-spec/scripts/`. Only `validate-test-spec.py` exists. Stage 1a will fail at runtime. No fallback clause is provided for a missing scan script.

2. **MEDIUM: No scan_script key in customize.toml.** The path should be liftable to customize.toml as `scan_script` for team overrides.

3. **NOTE: Validation script has tests.** `scripts/tests/test-validate-test-spec.py` exists. Only the scan script is missing entirely.

4. **NOTE: Large-document batching well-handled.** Stage 2 offers chunked processing for >20 REQs with per-batch compaction flush. This is a strength for the "heaviest document workflow."

## Recommendations

1. **Create `scripts/scan-test-spec-sources.py`** to match the contract described in Stage 1a: accept `--project-root` and `--output-dir`, return JSON with `state`, `existing_d27`, `d26_path`, `d02_path`, `d19_path`, `d06_path`, `req_ids`.
2. Add `scan_script = "scripts/scan-test-spec-sources.py"` to customize.toml and update SKILL.md line 36 to `{workflow.scan_script}`.
3. Add a fallback clause to Stage 1a: "If scan script is unavailable, fall back to LLM-driven project scan."
4. Write unit tests for the new scan script.
