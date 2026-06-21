# TDD Evidence — TASK-015 Luồng period sau Đồng bộ (REQ-038)

REQ-038: period(draft) sau Đồng bộ đi qua QA → review/submitted → Admin/IM approved. Test: `tests/test_resource_plan_period_flow.py` (3 test). TC-058.

**Verification-only** — workflow period đã có đầy đủ trong develop (`action_send_to_dm_review` cho QA, `action_submit`, `action_admin_approve`→`_try_set_approved`, `delivery_manager_user_id`). Không thêm production code.

## RED — 2026-06-19
Lần chạy đầu FAILED: `UserError: Missing manager user. Please configure Department Manager or Delivery Team Manager` — flow yêu cầu project có manager (đúng thiết kế). Đã cấu hình `dept_delivery.manager_id` trong test setUp.
```
ERROR ...period_flow: test_full_period_flow_to_approved ... Missing manager user
Ran 3 tests ... FAILED (errors=1)
```

## GREEN — 2026-06-19
Sau khi cấu hình delivery manager: QA `action_send_to_dm_review` → review; `action_submit` → submitted; `action_admin_approve` → approved.
```
...test_resource_plan_period_flow: Ran 3 tests — OK   (14 suite resource_plan OK)
```
REFACTOR: không cần.
