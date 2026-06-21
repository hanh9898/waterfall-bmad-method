# TDD Evidence — TASK-007 Pre-fill + employee approved

REQ-005 (chỉ nhân viên approved), REQ-007 (effort_ratio khớp member), REQ-010 (pre-fill từ allocation), TC-082 (@api.constrains approved). Test: `tests/test_resource_plan_prefill.py` (4 test).

## RED — 2026-06-19
```
ERROR ...prefill: AttributeError 'resource.plan' has no 'action_prefill_from_allocation'
FAIL  ...prefill: ValidationError not raised (employee draft)
Ran 4 tests ... FAILED (failures=1, errors=2)
```

## GREEN — 2026-06-19
Code:
- `resource_plan_line.py`: `employee_id` domain `process_state='approved'` + `@api.constrains('employee_id')` → ValidationError nếu chưa approved.
- `resource_plan.py`: `action_prefill_from_allocation()` tạo line từ `project.member` (employee approved, effort_ratio/role/dept theo allocation, member_id liên kết, rate_id mặc định để user chỉnh).
- base test: employee fixtures set `process_state='approved'`.
```
...test_resource_plan_prefill: OK   (6 suite resource_plan OK)
```
Quyết định: prefill đặt `rate_id` = rate đầu tiên (placeholder) vì billable.rate không link employee — TC-006 vẫn buộc rate khi lưu. REFACTOR: không cần.
