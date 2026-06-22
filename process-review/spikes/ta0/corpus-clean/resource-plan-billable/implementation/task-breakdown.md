---
title: "resource-plan-billable Task Breakdown (v2.3 clean)"
feature: resource-plan-billable
total_tasks: 6
completed: 6
sources:
  - D-02 v2.3 (request + snapshot model)
  - D-19 v2.3 (entities: resource.plan, resource.plan.request, resource.plan.request.line, resource.plan.line)
---

## Task List

| task_id | description | design_ref | test_refs | status |
|---------|-------------|------------|-----------|--------|
| TASK-001 | Model `resource.plan` header + `active_request_id` (REQ-RESOURCE-PLAN-BILLABLE-001) | resource.plan | TC-001 | done |
| TASK-002 | Model `resource.plan.line` (REQ-RESOURCE-PLAN-BILLABLE-002) | resource.plan.line | TC-002 | done |
| TASK-040 | Model `resource.plan.request` + snapshot_hash; Submit creates request (REQ-RESOURCE-PLAN-BILLABLE-040) | resource.plan.request | TC-040 | done |
| TASK-041 | Approve L2 → set active_request_id + Đồng bộ from snapshot (REQ-RESOURCE-PLAN-BILLABLE-041) | resource.plan.request.action_approve_l2 | TC-041 | done |
| TASK-014 | Đồng bộ from request snapshot; find-or-create period (REQ-RESOURCE-PLAN-BILLABLE-014) | _sync_from_snapshot | TC-014 | done |
| TASK-042 | Summary reflects active_request_id snapshot (REQ-RESOURCE-PLAN-BILLABLE-042) | resource.plan.summary | TC-042 | done |
