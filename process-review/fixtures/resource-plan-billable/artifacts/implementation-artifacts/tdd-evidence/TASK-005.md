# TDD Evidence — TASK-005 `resource.plan.summary`

REQ-028 (summary stored phản ánh plan), REQ-029 (refresh qua hook). Test: `tests/test_resource_plan_summary.py` (3 test, post_install).

## RED — 2026-06-19
```
ERROR ...test_resource_plan_summary ... KeyError: 'resource.plan.summary'
Ran 3 tests ... FAILED (errors=3)
```

## GREEN — 2026-06-19
Code:
- `models/resource_plan_summary.py` (`ResourcePlanSummary`: plan_id/project_id/department_id/employee_id/role_id/month_date/mm/price/amount Monetary/currency_id/state; `_rebuild_for_plans` xóa+tạo từ line×month, sudo).
- `resource_plan.py` `_refresh_summary()` (guard `rp_no_summary`, sudo).
- `resource_plan_line.py` + `resource_plan_line_month.py`: override create/write/unlink → refresh summary của plan.
```
...test_resource_plan_summary: Ran 3 tests in 3.153s — OK
(toàn bộ resource_plan: 3+5+4+3 = 15 test OK)
```
REFACTOR: rebuild bằng ORM (đúng đắn); tối ưu bulk-SQL + pivot view để TASK-018.
