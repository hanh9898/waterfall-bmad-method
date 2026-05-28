---
skill: hbc-setup
reviewed_at: "2026-05-28"
verdict: PASS_WITH_NOTES
---

# Quality Review: hbc-setup

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 76 |
| Path findings | 1 (bare _bmad ref) |
| Script findings | 4 (no unit tests for 3 Python scripts; no tests/ directory) |
| Verdict | **PASS_WITH_NOTES** |

## Checklist
- [~] Description format — `"Sets up HBLAB BMad Custom module in a project. Use when the user requests to 'install hbc module', 'configure HBLAB BMad Custom', or 'setup hbc'."` Format is correct but the summary portion is 9 words (guideline is 5-8). Minor.
- [ ] Conventions block (4 canonical lines) — Missing entirely. The skill uses `{project-root}` extensively but never defines the conventions block. As a setup/infrastructure skill this is less critical (it references `{project-root}` in context that's self-evident), but the block is a canonical requirement.
- [ ] customize.toml required fields — **No customize.toml exists.** This is a module setup skill that bootstraps the config system itself, so it cannot depend on the customization mechanism it creates. Missing by design, but should be documented as intentional.
- [x] Path references — All `_bmad` references are properly `{project-root}/_bmad/...`. The 1 bare ref is `_bmad/` in a comment context (line 37 default value `{project-root}/_bmad-output`), which is actually correct.
- [x] Size within guidance — 76 lines, well within single-purpose budget.
- [x] Outcome-based instructions — Good. "Collect Configuration" section describes what to collect, not a rigid step-by-step dialog script.
- [x] Intelligence placement correct — Scripts handle merge/cleanup deterministically; LLM handles user interaction and value collection.
- [x] Core test passes — Setup requires explicit instructions for config file structure, anti-zombie pattern, and legacy migration. All necessary.
- [~] Headless mode documented — Mentioned in passing (line 29: "If the user provides arguments (e.g. `accept all defaults`, `--headless`)") but not a formal section. Adequate for this skill type.
- [~] Lint clean — Script findings are real: 3 Python scripts with no unit tests.

## Findings

1. **MEDIUM: No conventions block.** Missing the 4 canonical lines. Even though this is an infrastructure skill, the conventions block is standard and helps LLMs resolve paths correctly. The skill uses `{project-root}` throughout, so the convention is implied but not declared.

2. **MEDIUM: No customize.toml by design.** This skill bootstraps the customization system, so it cannot use it. This is architecturally correct but should be explicitly documented (e.g., a comment in the skill directory or a note in SKILL.md explaining why).

3. **MEDIUM: No unit tests for Python scripts.** `cleanup-legacy.py`, `merge-config.py`, `merge-help-csv.py` have no test coverage. These scripts handle destructive operations (deleting legacy files, merging configs) and are prime candidates for unit testing.

4. **LOW: Description slightly over 8-word summary.** "Sets up HBLAB BMad Custom module in a project" is 9 words. Trivial.

## Recommendations

1. Add a conventions block (even a 2-line version noting `{project-root}` resolution).
2. Add a brief note in SKILL.md explaining why customize.toml is absent: _"This skill bootstraps the customization system and intentionally has no customize.toml."_
3. Create `scripts/tests/` directory with unit tests for the 3 Python scripts, especially for the anti-zombie merge logic and legacy cleanup verification.
