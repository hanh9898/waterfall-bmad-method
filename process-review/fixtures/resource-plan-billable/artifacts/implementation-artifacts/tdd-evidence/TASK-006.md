# TDD Evidence — TASK-006 Security 3 lớp

REQ-020 (ACL 4 model + record rule Delivery/IM scope), REQ-036 (summary/invoice đọc cho QA). Test: `tests/test_resource_plan_security.py` (5 test, post_install).

## RED — 2026-06-19
```
ERROR ...security: test_im_full_access / test_qa_reads_summary ... AccessError (resource.plan / resource.plan.summary: no ACL)
Ran 5 tests ... FAILED (errors=3)
```

## GREEN — 2026-06-19
Code:
- `security/ir.model.access.csv`: +9 dòng (resource.plan/.line/.line.month rwcu cho IM + DM; summary read cho IM/DM/QA).
- `security/record_rule.xml`: rule IM "thấy tất cả" (resource.plan + line) + rule Delivery scope (`project_id.delivery_team_id.manager_id.user_id`) cho `group_project_department_manager`.
- Fix: IM implies DM → cần rule IM global (rules cùng model OR theo group) để IM không bị Delivery scope.
```
...test_resource_plan_security: Ran 5 tests — OK   (tổng 20 test resource_plan OK)
```
REFACTOR: không cần.
