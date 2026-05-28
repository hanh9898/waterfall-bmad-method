---
skill: hbc-acceptance-check
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-acceptance-check

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 119 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines)
- [x] customize.toml required fields
- [~] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented
- [x] Lint clean

## Findings

### MEDIUM: Input paths hardcoded thay vi dung workflow config

Lines 34-37 hardcode input paths:
```
{project-root}/_hbc_output/test/test-execution-report.md
{project-root}/_hbc_output/traceability/matrix.md
{project-root}/_hbc_output/gates/phase-*-gate.md
{project-root}/_hbc_output/plan/D-02-*.md
```

Cac path nay la input tu cac skill khac. Neu team override output dir cua skill khac, acceptance-check se khong tim thay artifact. Nen extract thanh `{workflow.input_test_report}`, `{workflow.input_traceability}`, etc. trong customize.toml.

### LOW: headless-contract.md nam trong references/ nhung cung nam trong scripts/

`references/headless-contract.md` ton tai dung cho. SKILL.md reference dung: `references/headless-contract.md`.

## Recommendations

1. Extract 4 input paths (lines 34-37) thanh workflow config keys trong customize.toml de team co the override khi output structure thay doi.
2. Khong co van de nao khac — skill nay clean, co headless mode tot, validation script dung cho.
