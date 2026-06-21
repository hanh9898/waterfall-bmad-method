# TDD Evidence — TASK-013 Committed predicate + chặn sửa + hiển thị + lệch

REQ-018/033 (predicate + chặn sửa tháng đã-chốt), REQ-019 (hiển thị trạng thái tháng), REQ-039 (chỉ báo lệch). Test: `tests/test_resource_plan_committed.py` (5 test). TC-022/023/052/059/061 (TC-033 frozen-pane = view TASK-016).

## RED — 2026-06-19
```
ERROR ...committed: AttributeError month_has_committed_invoice / has_divergence / committed_reason
FAIL  ...committed: UserError not raised (edit committed month)
Ran 5 tests ... FAILED
```

## GREEN — 2026-06-19
Code:
- `resource_plan.py`: `_committed_reason`/`month_has_committed_invoice` (enum state đã-chốt), `has_divergence` computed (plan ≠ approved_l2 nhưng có period đã-chốt → lệch).
- `resource_plan_line_month.py`: `committed_reason` computed (hiển thị trạng thái tháng), `_check_month_editable` chặn create/write/unlink ô thuộc tháng đã-chốt (UserError).
- Sửa test TASK-011 `test_committed_period_skipped` (không còn sửa tháng committed — nay bị chặn đúng thiết kế).
```
...test_resource_plan_committed: Ran 5 tests — OK   (12 suite resource_plan OK)
```
REFACTOR: không cần.
