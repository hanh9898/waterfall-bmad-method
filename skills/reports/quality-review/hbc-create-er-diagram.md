---
skill: hbc-create-er-diagram
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-create-er-diagram

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 243 |
| Path findings | 2 (1 bare `_bmad` ref, 1 SKILL.md at root -- expected) |
| Script findings | 4 (missing unit test for `extract-entity-candidates.py`) |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines + extra placeholder line)
- [x] customize.toml required fields
- [~] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance (243 lines, multi-branch -- within ~250)
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented (with full blocker reason enumeration)
- [~] Lint clean

## Findings

### Minor: One bare `_bmad` reference (LOW)
Line 35: `"...then legacy `_bmad/bmm/config.yaml`."` -- missing the `{project-root}/` prefix. Should be `{project-root}/_bmad/bmm/config.yaml`. All other `_bmad` references on lines 31 and 35 are properly prefixed. This is a documentation-only issue (the LLM reading this would likely still resolve it correctly from context), but it deviates from the path-reference standard.

### Minor: Missing unit test for `extract-entity-candidates.py` (MEDIUM)
The `scripts/tests/` directory contains tests for 3 of 4 scripts:
- `test_check_entity_coverage.py` -- covers `check-entity-coverage.py`
- `test_discover_planning_artifacts.py` -- covers `discover-planning-artifacts.py`
- `test_validate_mermaid_er.py` -- covers `validate-mermaid-er.py`

Missing: `test_extract_entity_candidates.py` for `extract-entity-candidates.py`. This is the entity pre-pass script used in Stage 2 that extracts candidate entities from source documents. Its correctness matters for the discovery stage.

### Note: "Prompt file at root" finding is a false positive (INFO)
The scan flagged `SKILL.md` at root as a "prompt file at root" finding. This is the standard skill entry point, not a stray prompt file.

### Strengths
- Description format correct with Vietnamese triggers.
- All 4 canonical convention lines present (lines 16-20) plus a 5th documenting additional placeholder behavior.
- customize.toml has all required fields plus `er_diagram_template`, `decision_log_template`, `er_diagram_output_path`, `on_complete_distillate`, `on_complete`.
- Comprehensive headless mode: closed-set of blocker reasons enumerated (line 41) including `no_entities_found` which is specific to ER diagram generation.
- Good intelligence placement: `extract-entity-candidates.py`, `validate-mermaid-er.py`, `check-entity-coverage.py`, `discover-planning-artifacts.py` handle deterministic work; LLM handles normalization judgment, relationship completeness, naming consistency.
- Wrong-skill off-ramp (lines 90-91) redirects D-20/D-17/D-18 requests appropriately.
- `on_complete_distillate` config (`offer`/`always`/`never`) is a well-designed customization point.
- `stale_artifact` fresh_reason (line 61) handles an edge case not in the business-flow-diagram skill.

## Recommendations

1. **Fix bare _bmad ref** on line 35: change `_bmad/bmm/config.yaml` to `{project-root}/_bmad/bmm/config.yaml`.
2. **Add `test_extract_entity_candidates.py`** to `scripts/tests/` to complete test coverage for all 4 scripts. This script's correctness directly affects the quality of Stage 2 discovery.
