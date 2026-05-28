---
skill: hbc-create-business-flow-diagram
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-create-business-flow-diagram

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 256 |
| Path findings | 953 total (904 in .analysis/, ~49 in source) |
| Script findings | 0 |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines + extra placeholder line)
- [x] customize.toml required fields
- [x] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance (256 lines, multi-branch -- within ~250 allowance)
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented (with full blocker reason enumeration)
- [~] Lint clean

## Findings

### Context: 953 path findings are a false positive (INFO)
904 of the 953 path findings originate from the `.analysis/` directory, which contains prior analysis/review artifacts -- not part of the skill's runtime source. The remaining ~49 findings in SKILL.md are all properly `{project-root}/_bmad/` prefixed references (lines 33, 35, 49), which is the correct pattern for BMad infrastructure paths. The lint scanner should exclude `.analysis/` directories from its scan scope.

### Note: 256 lines at the upper bound (LOW)
At 256 lines this is 6 lines over the ~250 guidance for multi-branch skills. The complexity is justified: 5-stage workflow with resume/update/validate-only modes, headless mode, migration vs greenfield branching, parallel-lens menus, and detailed scope-of-change gating. No obvious content to cut without losing necessary behavioral specificity.

### Strengths
- Description format correct with multilingual triggers including Vietnamese.
- All 4 canonical convention lines present (lines 18-21) plus a 5th documenting additional placeholder behavior.
- customize.toml has all required fields plus rich workflow config (`business_flow_template`, `decision_log_template`, `diagram_type`, `business_flow_output_path`, `fr_id_pattern`, `on_complete`).
- Excellent headless mode documentation: closed-set of blocker reasons enumerated inline (lines 59-67) with explicit instruction to extend both the list and the contract file together.
- Good intelligence placement: `discover-planning-artifacts.py`, `validate-mermaid.py`, `check-fr-coverage.py`, `diff-stage2-flush.py` handle deterministic work; LLM handles layout readability, delta clarity, language consistency.
- Wrong-skill off-ramp (line 130-131) prevents the skill from being misused for architecture or single-feature sequence diagrams.
- Compaction-flush discipline at every stage boundary ensures resume-state survives context drops.
- Decision log is properly templated and initialized from `{workflow.decision_log_template}`.

## Recommendations

1. Consider adding `.analysis/` to the lint scanner's exclude list to prevent false-positive path findings in future scans.
2. If trimming is desired, the "Short-circuit Stage 1e" gate (lines 131-132) and "Zero-actor branch" (lines 177-178) are necessary but could be compressed by ~5 lines each without losing meaning.
