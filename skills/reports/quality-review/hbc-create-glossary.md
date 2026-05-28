---
skill: hbc-create-glossary
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-create-glossary

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 104 |
| Path findings | 0 (latest scan clean) |
| Script findings | 1 (low: no sys.exit in scan script) |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [x] Description format — correct 2-sentence format with quoted trigger phrases
- [x] Conventions block (4 canonical lines) — all 4 present
- [x] customize.toml required fields — activation_steps_prepend, activation_steps_append, persistent_facts all present
- [x] Path references ({workflow.*} not hardcoded) — scan_script, validation_script, template_path, glossary_output_path all use {workflow.*}
- [x] Size within guidance — 104 lines, within 80-130 single-purpose range
- [x] Outcome-based instructions — stages describe goals; Discovery is invitation-led, not procedural
- [x] Intelligence placement correct — scan/validate in Python scripts, filtering/judgment in LLM
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented — Section present with --headless flag and contract reference
- [~] Lint clean — 1 low-severity finding: scan-glossary-sources.py lacks sys.exit() for meaningful exit codes

## Findings

1. **LOW: scan-glossary-sources.py lacks sys.exit() calls.** The script may not return meaningful exit codes to the calling LLM. The SKILL.md has a fallback clause ("If scan script fails...") so this is mitigated but not ideal.

2. **NOTE: Earlier scan findings (path + script) appear resolved.** The latest scan (2026-05-28T103000) shows 0 path findings and 0 missing tests. The user's summary numbers (2 path, 2 script) likely reflect an older scan.

## Recommendations

1. Add `sys.exit(0)` on success and `sys.exit(1)` on failure to `scan-glossary-sources.py` for deterministic exit code signaling.
