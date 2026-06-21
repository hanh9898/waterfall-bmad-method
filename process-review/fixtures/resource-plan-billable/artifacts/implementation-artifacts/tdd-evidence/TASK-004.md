# TDD Evidence — TASK-004 `resource.plan.line.month`

REQ-009 (effort_mm ≥ 0), UNIQUE(line, month); TC-070 (trùng plan,employee,month bị chặn qua tổ hợp 2 UNIQUE).
Test: `tests/test_resource_plan_line_month.py::TestResourcePlanLineMonth` (4 test, post_install).

## RED — 2026-06-19
```
ERROR ...test_resource_plan_line_month: test_create_month_ok ... KeyError: 'resource.plan.line'
Ran 4 tests ... FAILED (errors=4)
```

## GREEN — 2026-06-19
Code: `models/resource_plan_line_month.py` (`ResourcePlanLineMonth`: line_id cascade, month_date required, effort_mm; `_sql_constraints uq_resource_plan_line_month`; `@api.constrains('effort_mm')` → ValidationError nếu < 0). Wiring `models/__init__.py`.
```
...test_resource_plan_line_month: Ran 4 tests in 4.237s
...test_resource_plan_line_month: OK
```
REFACTOR: không cần.
