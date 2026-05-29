---
skill: hbc-create-coding-standards
reviewed_at: "2026-05-28"
verdict: PASS
---

# Quality Review: hbc-create-coding-standards

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 105 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines)
- [x] customize.toml required fields
- [x] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance (105 lines, single-purpose)
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented
- [x] Lint clean

## Findings

No issues found. This is a clean, well-structured skill.

### Strengths
- Description format correct: `"Generate D-12 Coding Standards adapted to project framework. Use when user says 'coding standards', 'コーディング規約', 'chuẩn code', or agent menu [CS]."`
- Conventions block has all 4 canonical lines (lines 18-21).
- customize.toml has all 3 required fields plus `template_path`, `output_dir`, `validation_script`, `framework`, `comment_language`.
- All path references use `{workflow.*}` placeholders.
- Good intelligence placement: script validates required sections, detects contradictions, checks framework presence; LLM judges whether conventions are actionable, examples match stated conventions, framework-specific patterns are accurate.
- Framework-specific adaptation examples (Stage 2, lines 68-72) add real value -- Odoo, Django, Next.js/React patterns are concrete, not generic.
- Team preference elicitation (Stage 1c) is well-designed: pre-populates framework defaults and presents as confirmations, not open questions.
- 105 lines -- well within single-purpose guidance.

## Recommendations

None.
