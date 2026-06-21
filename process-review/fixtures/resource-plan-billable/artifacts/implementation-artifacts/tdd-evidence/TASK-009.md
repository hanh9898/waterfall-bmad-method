# TDD Evidence — TASK-009 Cửa sổ 8 tháng / currency / thêm tháng

REQ-003 (cửa sổ 8 tháng, from>to), REQ-030 (currency theo rate), REQ-035 (thêm tháng). Test: `tests/test_resource_plan_window.py` (6 test). TC-054→TASK-014, TC-064→TASK-011 (misassigned).

## RED — 2026-06-19
```
ERROR ...window: AttributeError _month_window / action_add_month
FAIL  ...window: ValidationError not raised (from>to)
Ran 6 tests ... FAILED
```

## GREEN — 2026-06-19
Code `resource_plan.py`: `_month_window(ref)` (current-2..+5, dùng relativedelta, vắt năm OK), default `date_from/date_to` từ window, `@api.constrains('date_from','date_to')` (from>to → ValidationError), `action_add_month(month_date)` (tạo ô mỗi line + mở rộng date_to, plan duy nhất). currency_id đã có ở TASK-003.
```
...test_resource_plan_window: Ran 6 tests — OK   (8 suite resource_plan OK)
```
REFACTOR: không cần.
