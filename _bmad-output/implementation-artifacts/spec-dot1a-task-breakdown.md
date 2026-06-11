---
title: 'Đợt 1A — task-breakdown: S-4 entity-coverage + verdict + E-2 warning'
type: 'refactor'
created: '2026-06-02'
status: 'done'
baseline_commit: '492fedd'
context:
  - '{project-root}/_bmad-output/hbc-refactor-plan.md'
---

<frozen-after-approval>

## Intent

**Problem:** `validate-task-breakdown.py` kiểm entity coverage bằng substring trên TOÀN tài liệu (`entity.lower() in content_lower`) → entity chỉ được nhắc trong prose vẫn tính "covered" (false-positive S-4). Output là bool `valid` không trung thực (S-3). SKILL.md sinh infra task im lặng khi thiếu project-context.md (E-2).

**Approach:** Đếm coverage chỉ trên cột `design_ref` của bảng task (S-4); output thêm phán quyết trung thực qua lib `hbc_validation.verdict` (S-3, additive — giữ key cũ); thêm cảnh báo E-2 vào SKILL.md Stage 2.

## Boundaries & Constraints

**Always:** import lib qua bootstrap `parents[2]/"hbc-shared"/"lib"` + try/except → JSON error nếu thiếu. Behavior-preserving trừ S-4 (entity coverage theo design_ref) + output additive.
**Never:** đổi/loại key cũ (`valid`/`issues`/`total_tasks`); wiring LLM review (semantic_review="n/a"); đụng skill ngoài task-breakdown.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected | Error |
|---|---|---|---|
| entity trong design_ref | design_ref="User entity" | covered | N/A |
| entity chỉ trong prose | mô tả nhắc "Payment", design_ref không | ENTITY_NOT_COVERED | N/A |
| thiếu lib | hbc-shared absent | JSON error, exit 2 | guarded |

</frozen-after-approval>

## Code Map
- `.claude/skills/hbc-task-breakdown/scripts/validate-task-breakdown.py` — bootstrap; check_entity_coverage→design_ref column; verdict output.
- `.claude/skills/hbc-task-breakdown/scripts/tests/test-validate-task-breakdown.py` — thêm test prose-not-counted + verdict fields.
- `.claude/skills/hbc-task-breakdown/SKILL.md` — Stage 2: cảnh báo khi thiếu project-context.md (E-2).

## Tasks & Acceptance
**Execution:**
- [x] test: thêm `test_entity_in_prose_not_counted` (đỏ trước) + assert verdict fields
- [x] validator: bootstrap lib + check_entity_coverage dùng cột design_ref + verdict additive
- [x] SKILL.md: thêm câu cảnh báo E-2

**Acceptance Criteria:**
- Given D-19 có entity "Payment" và task chỉ nhắc Payment ở mô tả (không ở design_ref), when validate, then ENTITY_NOT_COVERED cho Payment.
- Given doc hợp lệ, when validate, then output có `valid` (cũ) lẫn `structure_ok/semantic_review/passed` (mới); `passed` true.
- Given mọi test, when pytest, then xanh.

## Verification
**Commands:**
- `python3 -m pytest .claude/skills/hbc-task-breakdown/scripts/tests -q` -- expected: all pass
