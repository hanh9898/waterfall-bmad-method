# TDD Evidence — TASK-016 Views/UI

REQ-001 (menu/action), REQ-031 (form hiển thị Department/lines). Test: `tests/test_resource_plan_views.py` (3 test). TC-001/034/050/051 (frozen-pane TC-033 = JS widget, ngoài unit-test).

## RED — 2026-06-19
```
ERROR ...views: ValueError External ID not found: project_invoice.view_resource_plan_form (XML chưa load)
Ran 3 tests ... FAILED (errors=3)
```

## GREEN — 2026-06-19
Code `views/resource_plan_views.xml`: tree (decoration lệch), form (statusbar 2 cấp, nút Submit/Approve L1/L2/Reject/Đồng bộ/Pre-fill theo states, group project/dates/managers, notebook line_ids tree employee/department/role/effort/rate/currency), action `action_resource_plan`, menu `menu_resource_plan` dưới `menu_project_invoice_root`. Đăng ký manifest.
```
...test_resource_plan_views: Ran 3 tests — OK   (15 suite resource_plan OK; XML load sạch)
```
REFACTOR: không cần.
