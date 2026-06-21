# TDD Evidence — TASK-010 Vòng đời 2 cấp + optimistic lock

REQ-024 (Submit→L1→L2, Reject, self-approve), REQ-027 (optimistic-lock token). Test: `tests/test_resource_plan_lifecycle.py` (8 test).

## RED — 2026-06-19
```
ERROR ...lifecycle: AttributeError action_submit / revision
Ran 8 tests ... FAILED
```

## GREEN — 2026-06-19
Code `resource_plan.py`: `action_submit/approve_l1/approve_l2/reject` (permission qua has_group: L1=Dept Mgr, L2=IM; self-approve cho phép vì IM⊇Dept), field `revision` + `_touch()` (sudo, bump khi line/month CUD). `resource_plan_line.py`/`_month.py`: gọi `_touch()` trong create/write/unlink. TC-078 (out-of-scope) đã chặn qua record rule Delivery.
```
...test_resource_plan_lifecycle: Ran 8 tests — OK   (9 suite resource_plan OK)
```
REFACTOR: không cần.
