# TDD Evidence — TASK-018 Summary pivot + NFR audit

REQ-028 (pivot summary + menu, tách currency), NFR-004 (audit Đồng bộ), NFR perf. Test: `tests/test_resource_plan_summary_views.py` (3 test). TC-046/048/060/081.

## RED — 2026-06-19
```
ERROR ...summary_views: ValueError External ID not found: project_invoice.action_resource_plan_summary
Ran 3 tests ... FAILED
```

## GREEN — 2026-06-19
Code:
- `views/resource_plan_summary_views.xml`: pivot (row Department/Employee/Currency, col month, measure amount+mm — tách currency TC-048), tree, action `pivot,tree`, menu `menu_resource_plan_summary`.
- `resource_plan.py`: field `last_sync_by`/`last_sync_at` + ghi audit trong `action_sync_from_plan` (NFR-004 TC-081).
- TC-060 perf: smoke test Đồng bộ nhiều dòng × nhiều tháng không lỗi.
```
...test_resource_plan_summary_views: Ran 3 tests — OK   (17/17 suite resource_plan OK)
```
REFACTOR: không cần.
