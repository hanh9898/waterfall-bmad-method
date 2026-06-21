# TDD Evidence — TASK-012 Đồng bộ guards

REQ-021 (chặn plan invalid), REQ-018/037 (bỏ qua tháng đã-chốt "đã khóa"/"đã có"), REQ-012 (effort_ratio biên), 0-MM→no member. Test: `tests/test_resource_plan_guards.py` (7 test). TC-021/025/044/057/074/075/076/077 (TC-032 atomic = savepoint/tháng; TC-045 no-confirm = wizard TASK-017).

## RED — 2026-06-19
```
ERROR ...guards: 'bool' object is not subscriptable (action_sync trả True, chưa phải dict)
FAIL  ...guards: UserError not raised / ValidationError not raised
Ran 7 tests ... FAILED (failures=1, errors=4)
```

## GREEN — 2026-06-19
Code `resource_plan.py`: `_check_sync_valid` (rỗng/thiếu rate/không MM>0 → UserError), `action_sync_from_plan` trả `{'synced':[],'skipped':[(month,lý_do)]}` ("đã khóa"/"đã có"), savepoint mỗi tháng (atomic), xóa member effort_mm≤0 (0-MM không sinh member). `resource_plan_line.py`: `@api.constrains('effort_ratio')` ≥0.
```
...test_resource_plan_guards: Ran 7 tests — OK   (11 suite resource_plan OK)
```
REFACTOR: không cần.
