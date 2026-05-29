---
skill: hbc-create-api-spec
reviewed_at: "2026-05-28"
verdict: PASS
---

# Quality Review: hbc-create-api-spec

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 110 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines)
- [x] customize.toml required fields
- [x] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance (110 lines, single-purpose)
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented
- [x] Lint clean

## Findings

No issues found. This is a clean, well-structured skill.

### Strengths
- Description format correct: `"Generate D-21 API Specification with endpoint definitions. Use when user says 'API spec', 'API仕様書', 'đặc tả API', or agent menu [API]."`
- Conventions block has all 4 canonical lines (lines 18-21).
- customize.toml has all 3 required fields plus additional workflow-specific config (`template_path`, `output_dir`, `validation_script`, `api_style`, `auth_strategy`).
- All path references use `{workflow.*}` placeholders (e.g., `{workflow.template_path}`, `{workflow.output_dir}`, `{workflow.validation_script}`).
- Good intelligence placement: scripts handle deterministic validation (endpoint field checks, ID uniqueness, cross-reference), LLM handles judgment (RESTful naming, security completeness, missing CRUD).
- Headless mode documented with reference to `references/headless-contract.md`.
- 110 lines -- right in the sweet spot for single-purpose skills.
- API necessity gate (Stage 1b) is a smart addition for optional skills.

## Recommendations

None.
