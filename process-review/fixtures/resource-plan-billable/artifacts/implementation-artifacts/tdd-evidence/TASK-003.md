# TDD Evidence — TASK-003 `resource.plan.line`

REQ-004 (bắt buộc employee/rate), REQ-006 (dept/role), UNIQUE(plan,employee,role), currency theo rate.price_currency_id.
Test: `tests/test_resource_plan_line.py::TestResourcePlanLine` (5 test, post_install). Base: `tests/common_resource_plan.py`.

## RED — 2026-06-19
Lệnh: `docker compose run --rm --no-deps odoo11 odoo-bin ... -d odoo_test -u project_invoice --test-enable --stop-after-init`
```
ERROR ...test_resource_plan_line: test_create_line_ok ... KeyError: 'resource.plan.line'
ERROR ...test_resource_plan_line: test_unique_plan_employee_role ... KeyError: 'resource.plan.line'
Ran 5 tests ... FAILED (errors=3)
```

## GREEN — 2026-06-19
Code: `models/resource_plan_line.py` (`ResourcePlanLine`: plan_id cascade, employee_id/rate_id required, department_id/project_role_id, effort_ratio, currency_id related `rate_id.price_currency_id` store, member_id, migrated, month_ids; `_sql_constraints uq_resource_plan_line`; `_onchange_employee_id` → department). `resource_plan.py` thêm `line_ids`. Wiring `models/__init__.py`.
```
...test_resource_plan_line: Ran 5 tests in 5.342s
...test_resource_plan_line: OK
```
REFACTOR: không cần.
