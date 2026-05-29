---
skill: hbc-traceability
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-traceability

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 107 |
| Path findings | 14 (10 from .analysis/ artifacts, 3 from .decision-log.md, 1 prompt file at root) |
| Script findings | 0 |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [x] Description format — `"Living traceability matrix for HBC waterfall lifecycle. Use when user says 'traceability', 'ma tran', 'truy vet', or agent menu [TR]."` Correct format, trigger phrases quoted.
- [x] Conventions block (4 canonical lines) — All 4 present at lines 18-22. Also includes a 5th convention line for capability report language, which is a reasonable extension.
- [x] customize.toml required fields — `activation_steps_prepend`, `activation_steps_append`, `persistent_facts` all present.
- [x] Path references — SKILL.md uses `{project-root}/_hbc_output/...` consistently. Script invocations use `{project-root}` and `{workflow.*}`. No hardcoded absolute paths in the prompt itself.
- [x] Size within guidance — 107 lines for a 4-capability skill (init, update, report, audit). Efficient use of space.
- [x] Outcome-based instructions — Init and Report are procedural (appropriate -- they're deterministic). Update is outcome-driven with phase-specific column population. Audit classifies gap severity by phase context. Good balance.
- [x] Intelligence placement correct — `extract-trace-ids.py` and `trace-report.py` handle deterministic extraction and counting. LLM handles design-to-requirement mapping (Phase 2) and code-to-requirement mapping (Phase 3) -- genuine judgment tasks.
- [x] Core test passes — The Update section's phase-specific mapping instructions are necessary. LLM would not know the column-to-phase mapping or the interrupted-update recovery pattern without them.
- [x] Headless mode documented — Lines 26-31, clear JSON contract with `status`, `capability`, `matrix_path`, `decision_log`.
- [~] Lint clean — See findings below.

## Findings

1. **LOW: .decision-log.md at skill root.** Build artifact from workflow builder. Should be in `references/` or removed before distribution. Contains useful build-time rationale but is not part of the skill's runtime.

2. **LOW: .analysis/ folder present.** Contains build process analysis reports. Accounts for 10 of the 14 path findings. Should be excluded from distribution.

3. **INFO: Hardcoded `_hbc_output` paths in SKILL.md.** Lines 48, 59, 63, 67, 69 reference `{project-root}/_hbc_output/...` directly in script invocations and prose. These are correct (they use `{project-root}` prefix), but some could be further abstracted via `{workflow.*}` variables in customize.toml. Currently, only `matrix_path` is in customize.toml; paths like `_hbc_output/plan/D-02-*` and `_hbc_output/design/D-27-*` are inline. This is acceptable since those are cross-skill conventions (not configurable per-team), but worth noting.

## Recommendations

1. Move `.decision-log.md` into `references/` directory.
2. Add `.analysis/` to `.gitignore` or strip from distribution builds.
3. Consider adding `plan_output_dir` and `design_output_dir` to customize.toml for teams with non-standard output layouts. Low priority -- current inline paths follow the module convention.
