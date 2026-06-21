# TDD Evidence — TASK-011 Đồng bộ core (plan → invoice period/member)

REQ-014 (find-or-create period), REQ-015 (amount=MM×price), REQ-016 (replace tháng chưa-chốt), REQ-022 (snapshot generate_lines + overlay), REQ-026 (ghi đè sửa tay). Test: `tests/test_resource_plan_sync.py` (6 test). TC-017/018/019/026/041/062/063/064.

## RED — 2026-06-19
```
ERROR ...sync: self.plan.action_sync_from_plan() -> AttributeError 'resource.plan' has no 'action_sync_from_plan'
Ran 6 tests ... FAILED
```

## GREEN — 2026-06-19
Code `resource_plan.py`: `action_sync_from_plan` (IM/admin-only, chỉ khi approved_l2, `SELECT ... FOR UPDATE` serialize, mỗi tháng find-or-create period, bỏ qua state ∈ {approved,sent,paid,locked}, unlink member chưa-chốt, `period.action_generate_lines()` dựng skeleton, `_overlay_period` overlay effort_mm/rate_id/effort_ratio), `_plan_months`, `_overlay_period`. amount auto = effort_mm×rate.price (compute sẵn của member). Cho phép admin (group_system) approve/sync để test.
```
...test_resource_plan_sync: Ran 6 tests — OK
```
REFACTOR: không cần.
