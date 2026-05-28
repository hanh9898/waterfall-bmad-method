---
skill: hbc-agent-qa
reviewed_at: "2026-05-28"
verdict: PASS
---

# Quality Review: hbc-agent-qa

## Summary
| Metric | Value |
|--------|-------|
| SKILL.md lines | 101 |
| Path findings | 0 |
| Script findings | 0 |
| Verdict | **PASS** |

## Checklist
- [x] Description format
- [x] Conventions block (4 canonical lines)
- [x] customize.toml required fields
- [x] Path references ({workflow.*} not hardcoded)
- [x] Size within guidance
- [x] Outcome-based instructions
- [x] Intelligence placement correct
- [x] Core test passes (no unnecessary instructions)
- [x] Headless mode documented
- [x] Lint clean

## Findings

Khong co finding nao. Chi tiet:

- Description format chuan: "Phase 2 Test Design coordinator..." + trigger phrases `'QA'`, `'quality assurance'`, `'kiem thu'`, `'thiet ke test'`.
- Conventions block day du 4 dong.
- customize.toml co day du 3 required fields.
- Moi path ref dung `{project-root}`, `{skill-root}`, `{skill-name}`, `{agent.*}`.
- 101 dong — trong guidance range.
- Headless mode documented voi JSON contract.
- Scan script (`scripts/scan-test-design-state.py`) co fallback.
- Phase 1 gate check truoc khi scan — dependency ordering dung.
- Context capsule: pass D-26 test strategy summary khi dispatch D-27, pass D-02 REQ count khi available.
- Gate shared voi architect — documented ro rang (line 93).
- Staleness flagging co (line 83).

## Recommendations

Khong co recommendation. Skill nay follow dung pattern cua cac agent khac va day du cac feature can thiet.
