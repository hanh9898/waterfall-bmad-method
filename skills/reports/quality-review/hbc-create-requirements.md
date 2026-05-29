---
skill: hbc-create-requirements
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-create-requirements

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 107 |
| Path findings | 1 (bare script path in SKILL.md) |
| Script findings | 2 (missing scan_script in toml, scanner false positive on test naming) |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [x] Description format — correct 2-sentence format with quoted trigger phrases
- [x] Conventions block (4 canonical lines) — all 4 present
- [x] customize.toml required fields — activation_steps_prepend, activation_steps_append, persistent_facts all present
- [~] Path references ({workflow.*} not hardcoded) — validation_script uses {workflow.*} correctly, but `scripts/scan-sources.py` on line 36 is hardcoded (no `scan_script` key in customize.toml)
- [x] Size within guidance — 107 lines, within 80-130 range
- [x] Outcome-based instructions — Discovery is invitation-led, soft-gates between areas
- [x] Intelligence placement correct — deterministic validation in script, judgment checks in LLM
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented — section present with contract reference
- [~] Lint clean — path scan flagged 3 bare _bmad refs but all in .analysis/ temp files (false positives); 1 real issue: missing scan_script in customize.toml

## Findings

1. **MEDIUM: Hardcoded scan script path.** SKILL.md line 36 uses `scripts/scan-sources.py` directly instead of `{workflow.scan_script}`. The glossary skill already follows the correct pattern with a `scan_script` key in customize.toml. Teams cannot swap the scanner without forking.

2. **LOW: Scanner false positive on test file.** The scripts scanner reported "No unit test found for scan-sources.py" but `scripts/tests/test_scan_sources.py` exists. The scanner expected hyphenated naming (`test-scan-sources.py`) but the actual file uses underscores. This is a scanner bug, not a skill bug.

3. **LOW: scan-sources.py lacks sys.exit() calls.** Same as glossary -- no meaningful exit codes.

4. **NOTE: .analysis/ temp files contain bare _bmad references.** The path scanner flagged 3 findings, but all are in `.analysis/2026-05-27T103000/` output files (customization-analysis.md and report-data.json), not in source files. These are false positives from scanning analysis artifacts.

## Recommendations

1. Add `scan_script = "scripts/scan-sources.py"` to customize.toml and change SKILL.md line 36 to use `{workflow.scan_script}`. This matches the glossary pattern and makes the scanner overridable.
2. Add `sys.exit(0)` / `sys.exit(1)` to scan-sources.py for deterministic exit codes.
3. Consider excluding `.analysis/` directories from future path scans to avoid false positives.
