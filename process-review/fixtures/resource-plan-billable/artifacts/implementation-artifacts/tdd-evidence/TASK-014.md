# TDD Evidence — TASK-014 Migration lần đầu

REQ-034: nạp invoice member → resource plan (post_init_hook), idempotent, bỏ qua dirty data. Test: `tests/test_resource_plan_migration.py` (5 test). TC-053/054/067/068/069 (TC-066 tz→TASK-009 window).

## RED — 2026-06-19
```
ERROR ...migration: AttributeError 'resource.plan' has no '_migrate_from_invoices'
Ran 5 tests ... FAILED
```

## GREEN — 2026-06-19
Code:
- `resource_plan.py`: `_migrate_from_invoices(projects=None)` — group invoice member theo project, tạo plan(draft) + line(migrated=True) + month; idempotent (key project/employee/role/month qua search-exists); bỏ qua employee non-approved + member thiếu rate; dedup (nguồn đã có UNIQUE(period,employee)). Chạy `rp_migrating` context để bỏ alloc-sync + edit-block.
- `__init__.py` + `__manifest__.py`: `post_init_hook` gọi migration khi cài mới.
```
...test_resource_plan_migration: Ran 5 tests — OK   (13 suite resource_plan OK)
```
REFACTOR: không cần.
