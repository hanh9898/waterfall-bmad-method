# TDD Evidence — TASK-017 Đồng bộ wizard

REQ-017 (blocking confirm trước khi ghi đè, chỉ khi đã có lines). Test: `tests/test_resource_plan_sync_wizard.py` (3 test). TC-020 (blocking confirm), TC-035 (a11y dialog = view-level).

## RED — 2026-06-19
```
ERROR ...sync_wizard: KeyError: 'resource.plan.sync.wizard'
Ran 3 tests ... FAILED
```

## GREEN — 2026-06-19
Code:
- `wizard/resource_plan_sync_wizard.py` (`resource.plan.sync.wizard` TransientModel): `preview` (create/overwrite/skip mỗi tháng), `needs_confirm` (True khi có tháng overwrite lines đã có), `action_confirm` → `action_sync_from_plan`.
- `wizard/resource_plan_sync_wizard_views.xml`: form dialog (cảnh báo khi needs_confirm, preview, nút Đồng bộ/Hủy — focus-trap/Esc mặc định Odoo dialog cho TC-035).
```
...test_resource_plan_sync_wizard: Ran 3 tests — OK
```
REFACTOR: không cần.
