# Traceability Matrix — opms

**Last Updated:** 2026-06-19

| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|-------|-------|-------|-------|-------|-------|-------|-------|
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-001 |  | resource_plan (model/menu) | project_invoice/views/resource_plan_views.xml | TC-001 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-002 |  | resource_plan (project_id UK) | project_invoice/models/resource_plan.py | TC-002, TC-003 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-003 |  | resource_plan (date_from/date_to) | project_invoice/models/resource_plan.py | TC-004, TC-005 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-004 |  | resource_plan_line | project_invoice/models/resource_plan_line.py | TC-006 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-005 |  | resource_plan_line.employee_id → hr_employee | project_invoice/models/resource_plan_line.py | TC-007 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-006 |  | resource_plan_line (department_id, project_role_id) | project_invoice/models/resource_plan_line.py | TC-008 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-007 |  | resource_plan_line.effort_ratio ↔ project_member | project_invoice/models/resource_plan.py | TC-009 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-008 |  | resource_plan_line.rate_id → ntq_project_billable_rate | project_invoice/models/resource_plan_line.py | TC-010 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-009 |  | resource_plan_line_month (effort_mm, CHECK≥0) | project_invoice/models/resource_plan_line_month.py | TC-011, TC-012, TC-034 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-010 |  | resource_plan_line ← project_member | project_invoice/models/resource_plan.py | TC-013 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-011 |  | resource_plan_line.member_id → project_member | project_invoice/models/resource_plan_line.py | TC-014 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-012 |  | resource_plan_line.member_id → project_member | project_invoice/models/resource_plan_line.py | TC-015 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-013 |  | project_member.end_at (via member_id) | project_invoice/models/resource_plan_line.py | TC-016 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-014 |  | project_invoice_period, project_invoice_member (generates) | project_invoice/models/resource_plan.py | TC-017, TC-032 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-015 |  | project_invoice_member.amount | project_invoice/models/resource_plan.py | TC-018 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-016 |  | project_invoice_period / project_invoice_member (replace) | project_invoice/models/resource_plan.py | TC-019 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-017 |  | project_invoice_member | project_invoice/wizard/resource_plan_sync_wizard.py | TC-020, TC-035 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-018 |  | project_invoice_period.state | project_invoice/models/resource_plan.py | TC-021, TC-022 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-019 |  | project_invoice_period.state | project_invoice/models/resource_plan_line_month.py | TC-023, TC-033 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-020 |  | resource_plan (ir.model.access + record rule row-level) | project_invoice/security/ir.model.access.csv | TC-024, TC-036, TC-037 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-021 |  | resource_plan / resource_plan_line (constraints) | project_invoice/models/resource_plan.py | TC-025 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-022 |  | project_invoice_member (snapshot fields) | project_invoice/models/resource_plan.py | TC-026 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-023 |  | resource_plan_line.member_id (một chiều) | project_invoice/models/resource_plan_line.py | TC-027 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-024 |  | resource_plan.state (draft/submitted/approved + reject) | project_invoice/models/resource_plan.py | TC-028, TC-029, TC-030, TC-031, TC-038, TC-039 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-025 |  | resource_plan_line.member_id → project_member (quyền user) | project_invoice/models/resource_plan_line.py | TC-040 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-026 |  | project_invoice_period / project_invoice_member (overwrite) | project_invoice/models/resource_plan.py | TC-041 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-027 |  | resource_plan (optimistic concurrency token write_date) | project_invoice/models/resource_plan.py | TC-042, TC-043 |  | 2026-06-12 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-028 |  | resource_plan_summary (model stored + ACL + pivot, tách currency) | project_invoice/models/resource_plan_summary.py | TC-046, TC-048 |  | 2026-06-19 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-029 |  | resource_plan_summary stored + refresh qua hook khi sửa plan | project_invoice/models/resource_plan_summary.py | TC-047, TC-048 |  | 2026-06-19 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-030 |  | resource_plan_line.currency_id = rate_id.price_currency_id | project_invoice/models/resource_plan_line.py | TC-049 |  | 2026-06-19 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-031 |  | D-19 §3 narrative (HB / OB Delivery BU) | project_invoice/views/resource_plan_views.xml | TC-050 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-032 |  | resource_plan date_from/to + resource_plan_line_month.month_date (cửa sổ 8 tháng) | project_invoice/models/resource_plan.py | TC-051 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-033 |  | predicate committed + Access Control | project_invoice/models/resource_plan_line_month.py | TC-052, TC-059 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-034 |  | resource_plan_line.migrated + UNIQUE(plan,employee,month) | project_invoice/models/resource_plan.py __init__.py | TC-053, TC-054 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-035 |  | resource_plan_line_month (thêm rows tháng) | project_invoice/models/resource_plan.py | TC-055 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-036 |  | D-19 §3.5 Access Control (invoice edit/delete = IM+QA) | project_invoice/security/ir.model.access.csv | TC-056 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-037 |  | "Đồng bộ" + predicate committed (bỏ qua tháng đã-chốt) | project_invoice/models/resource_plan.py | TC-057, TC-059 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-038 |  | period draft → duyệt bởi QA/IM (luồng period) | project_invoice/models/invoice_period.py | TC-058 |  | 2026-06-18 |
| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-039 |  | chỉ báo lệch plan↔period (grid + summary) | project_invoice/models/resource_plan.py | TC-061 |  | 2026-06-19 |
