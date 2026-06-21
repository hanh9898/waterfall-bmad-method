---
title: "opms · resource-plan-billable Task Breakdown"
feature: resource-plan-billable
total_tasks: 18
completed: 18
coverage_pct: 100
max_hours_per_task: 4
updated: "2026-06-19"
sources:
  - D-02 v1.8 (39 REQ)
  - D-19 v1.3 (entities: resource_plan, resource_plan_line, resource_plan_line_month, resource_plan_summary)
  - D-27 v1.5 (82 TC)
  - D-12 opms coding standards · project-context.md
notes:
  - "Phase 2 gate PASSED (entry gate ✓); project-context.md present → Infrastructure tasks included."
  - "D-21 absent (no API) → no API tasks. Module = extension of existing `project_invoice` (Odoo 11)."
  - "Implement via hbc-implement TDD (RED→GREEN→REFACTOR) per task; fill matrix code_ref as each completes."
---

## Task List

| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Infra: scaffold extend `project_invoice` — `__manifest__.py` (version 11.0.x, `data` order, `post_init_hook` stub), `models/__init__.py`, security file stubs | module/project_invoice | TC-002 | 1 | done | - |
| TASK-002 | Model `resource.plan` (header): state 2-cấp Selection (draft/submitted/approved_l1/approved_l2/rejected), `project_id` UNIQUE (1/project), `dept_manager_id`/`im_id`/approve audit, `write_date` lock token | resource_plan ← project_project | TC-002, TC-003, TC-071 | 2 | done | TASK-001 |
| TASK-003 | Model `resource.plan.line`: employee/department/role(auto)/effort_ratio/rate_id/`currency_id=rate.price_currency_id`/member_id/migrated; UNIQUE(plan, employee, role) | resource_plan_line → hr_department / ntq_project_billable_rate / ntq_project_role_skills | TC-006, TC-008 | 3 | done | TASK-002 |
| TASK-004 | Model `resource.plan.line.month`: `month_date` first-of-month, `effort_mm` CHECK ≥0, UNIQUE(line, month) | resource_plan_line_month | TC-010, TC-011, TC-070 | 4 | done | TASK-003 |
| TASK-005 | Model + build `resource.plan.summary` (stored): bulk-SQL `generate_*`, refresh ORM hook on line create/write/unlink + re-entrancy guard, preserve locked, pivot-ready | resource_plan_summary | TC-046, TC-047 | 5 | done | TASK-003, TASK-004 |
| TASK-006 | Security 3-lớp: ACL csv (4 model), record rules (Delivery via `delivery_team_id.manager_id.user_id`, Dept row-level, IM all), groups; siết quyền module invoice IM+QA (REQ-020/036) | security/ACL+record_rule | TC-024, TC-036, TC-037, TC-056 | 6 | done | TASK-002, TASK-003, TASK-004, TASK-005 |
| TASK-007 | Pre-fill từ allocation (`project.member`) + employee approved domain + dept/role auto-fill read-only (REQ-005/006/007/010) | resource_plan_line ← project_member / hr_employee | TC-007, TC-009, TC-012, TC-013, TC-082 | 7 | done | TASK-003, TASK-006 |
| TASK-008 | Đồng bộ một chiều plan→allocation: thêm→create `project.member`, sửa→effort_ratio, xóa→set end_at; chạy dưới quyền user (no-sudo) + re-entrancy guard (REQ-011/012/013/023/025) | resource_plan_line.member_id → project_member | TC-014, TC-015, TC-016, TC-027, TC-040, TC-072, TC-073 | 8 | done | TASK-007 |
| TASK-009 | Lưới nhập + cột tiền tệ (`rate.price`/`price_currency_id`) + cửa sổ 8 tháng (current−2..+5) + thêm tháng trên form (REQ-003/004/008/009/030/032/035) | resource_plan date_from/to + line_month | TC-004, TC-005, TC-049, TC-055, TC-065, TC-066 | 9 | done | TASK-004, TASK-006 |
| TASK-010 | Vòng đời plan 2 cấp: action submit/approve_l1/approve_l2/reject + self-approve; optimistic lock **touch parent `write_date`** khi sửa line/month (REQ-024/027) | resource_plan.state | TC-028, TC-029, TC-030, TC-031, TC-038, TC-039, TC-042, TC-043, TC-078, TC-079, TC-080 | 10 | done | TASK-002, TASK-006 |
| TASK-011 | Đồng bộ core `action_sync_from_plan`: IM-only sau Approved L2, find-or-create period (`uniq_project_month`), **unlink member chưa-chốt** + reuse `action_generate_lines` + overlay effort_mm/rate_id/effort_ratio, amount=MM×price, serialize (REQ-014/015/016/022) | project_invoice_period / project_invoice_member | TC-017, TC-018, TC-019, TC-026, TC-041, TC-062, TC-063, TC-064 | 11 | done | TASK-008, TASK-010 |
| TASK-012 | Đồng bộ guards: chặn plan invalid (REQ-021), blocking confirm ghi đè (REQ-017), bỏ qua tháng đã-chốt "đã có"/"đã khóa" (REQ-018/037), re-sync downstream khi period `submitted` (REQ-026) | committed predicate + đồng bộ | TC-021, TC-025, TC-032, TC-044, TC-045, TC-057, TC-074, TC-075, TC-076, TC-077 | 12 | done | TASK-011 |
| TASK-013 | Predicate `month_has_committed_invoice` + chặn sửa plan tháng đã-chốt (REQ-033) + hiển thị trạng thái tháng (REQ-019) + chỉ báo lệch plan↔period (REQ-039) | predicate + grid/summary indicator | TC-022, TC-023, TC-033, TC-052, TC-059, TC-061 | 13 | done | TASK-005, TASK-011 |
| TASK-014 | Migration lần đầu (`post_init_hook`): nạp project invoice → resource plan, idempotent key (project, employee, month, rate), plan state draft, tháng đã-chốt read-only, report đối chiếu số dòng + amount (REQ-034) | resource_plan_line.migrated | TC-053, TC-054, TC-067, TC-068, TC-069 | 14 | done | TASK-009, TASK-011 |
| TASK-015 | Luồng period sau Đồng bộ (REQ-038): QA đẩy → submitted; DM/Admin/IM duyệt cuối → approved (`action_approve_delivery`→`_try_set_approved`, cần `delivery_manager_user_id`) | period draft → QA/IM | TC-058 | 15 | done | TASK-006, TASK-011 |
| TASK-016 | Views/UI: menu (REQ-001), tree (list), form + PlanGrid widget, statusbar 2-cấp, nút theo role/state, hiển thị Department (HB)/OB Delivery (BU) (REQ-031); a11y | views + D-19 §3 narrative | TC-001, TC-034, TC-050, TC-051 | 16 | done | TASK-009, TASK-010 |
| TASK-017 | Đồng bộ wizard (TransientModel + view): preview theo tháng (Tạo mới/Ghi đè/Bỏ qua), blocking confirm (REQ-017) | wizard | TC-020, TC-035 | 17 | done | TASK-012, TASK-016 |
| TASK-018 | Resource Plan Summary pivot view + menu (REQ-028) + NFR perf/audit (NFR-001/002/004/008): pivot model stored, default filter, đa-currency tách; audit Đồng bộ | resource_plan_summary (pivot) | TC-046, TC-048, TC-060, TC-081 | 18 | done | TASK-005, TASK-015 |

## Dependency graph (foundation → dependent)

```
TASK-001 (scaffold)
 └─ TASK-002 resource.plan ──┬─ TASK-003 line ──┬─ TASK-004 line_month ──┐
                         │              ├─ TASK-005 summary ─────┤
                         │              └─ TASK-007 prefill ─ TASK-008 alloc-sync ─┐
                         ├─ TASK-006 security (needs TASK-002..TASK-005)               │
                         └─ TASK-010 lifecycle (TASK-002,TASK-006)                     │
 TASK-004,TASK-006 ─ TASK-009 grid/currency/window ───────────────────────────────────┤
 TASK-008 + TASK-010 ─ TASK-011 Đồng bộ core ─┬─ TASK-012 guards                           │
                                  ├─ TASK-013 committed/divergence (TASK-005)      │
                                  ├─ TASK-014 migration (TASK-009)                 │
                                  └─ TASK-015 period flow (TASK-006)               │
 TASK-009,TASK-010 ─ TASK-016 Views ─ TASK-017 wizard (TASK-012)                              │
 TASK-005,TASK-015 ─ TASK-018 Summary pivot + NFR                                     │
```

## Coverage

- **Entities (D-19):** resource_plan (TASK-002) · resource_plan_line (TASK-003) · resource_plan_line_month (TASK-004) · resource_plan_summary (TASK-005) — all covered.
- **Test cases:** TC-001…TC-082 (82) each assigned to ≥1 task (TC-046/048 shared model TASK-005 ↔ pivot TASK-018).
- **Infra:** TASK-001 (project-context present). **No API** (D-21 absent). **Migration:** TASK-014.
