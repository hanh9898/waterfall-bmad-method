# TDD Evidence — TASK-002 (gồm scaffold TASK-001)

Model `resource.plan` (header) — REQ-RESOURCE-PLAN-BILLABLE-002 (1 plan/dự án, UNIQUE project_id), persistence, state mặc định `draft`.
Test: `project_invoice/tests/test_resource_plan.py::TestResourcePlanHeader` (3 test, phase post_install — Odoo 11 dùng `@common.at_install(False)/post_install(True)`, KHÔNG có `@tagged`).

## RED — 2026-06-19

Môi trường: docker-compose (`odoo11` + `db` postgres12), DB `odoo_test` (restore từ dump `hblab` + `-u` 11 module đã đổi để khớp schema nhánh develop). Web server đã dừng; chạy bằng container một-lần (`compose run --rm`, không bind cổng).

Lệnh:
```
docker compose run --rm --no-deps odoo11 odoo-bin --db_host db --db_port 5432 \
  --db_user odoo --db_password odoo -d odoo_test \
  --addons-path=/mnt/extra-addons,/opt/odoo/odoo/addons \
  -u project_invoice --test-enable --log-level=test --stop-after-init
```

Kết quả (FAIL — model `resource.plan` chưa tồn tại):
```
ERROR odoo.addons.project_invoice.tests.test_resource_plan: ERROR: test_create_plan_for_project (...TestResourcePlanHeader)
ERROR odoo.addons.project_invoice.tests.test_resource_plan: ERROR: test_plan_persists_after_reload (...TestResourcePlanHeader)
ERROR odoo.addons.project_invoice.tests.test_resource_plan: ERROR: test_second_plan_same_project_rejected (...TestResourcePlanHeader)
    return self.env['resource.plan'].create({...})
    return self.models[model_name]
  KeyError: 'resource.plan'
INFO  odoo.addons.project_invoice.tests.test_resource_plan: Ran 3 tests in 3.133s
ERROR odoo.addons.project_invoice.tests.test_resource_plan: FAILED
      (errors=3)
```
→ RED hợp lệ: 3/3 FAIL vì `resource.plan` chưa khai báo. Tiến sang GREEN.

## GREEN — 2026-06-19

Code (scaffold TASK-001 + model TASK-002):
- `project_invoice/models/resource_plan.py` — model `resource.plan` (field header theo D-19: project_id required + index, date_from/to, state 5 trạng thái default `draft`, dept_manager_id/im_id/submitted/approved_l1/l2/reject_reason) + `_sql_constraints` `uq_resource_plan_project` unique(project_id).
- `project_invoice/models/__init__.py` — wiring `from . import resource_plan`.

Cùng lệnh trên → PASS:
```
INFO  odoo.addons.project_invoice.tests.test_resource_plan: test_create_plan_for_project (...)
INFO  odoo.addons.project_invoice.tests.test_resource_plan: test_plan_persists_after_reload (...)
INFO  odoo.addons.project_invoice.tests.test_resource_plan: test_second_plan_same_project_rejected (...)
INFO  odoo.addons.project_invoice.tests.test_resource_plan: Ran 3 tests in 2.625s
INFO  odoo.addons.project_invoice.tests.test_resource_plan: OK
```
exit=0 → GREEN. REFACTOR: không cần (code tối giản, đúng D-12).

Ghi chú môi trường: 4 test cũ của project_invoice là phase **at_install** — phase này không kích hoạt trên DB restore foreign (nhiều ghost-module thiếu source); test mới đặt **post_install** nên chạy được. Regression suite cũ cần DB cài từ nhánh để verify đầy đủ (đưa vào closeout Phase 3).

