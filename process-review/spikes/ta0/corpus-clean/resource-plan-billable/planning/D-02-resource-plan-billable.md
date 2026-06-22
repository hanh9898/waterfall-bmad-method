---
document_id: D-02
title: "Resource Plan & Billable — Requirements (v2.3 clean)"
version: "2.3"
status: approved
---

# Resource Plan & Billable — Requirements

> Clean v2.3 core: the Request+Snapshot model is the source of truth. A trimmed
> but genuine requirement set (not the full 42 — a coherent slice covering the
> approval-request lifecycle that the v2.3 U-turn introduced) used to prove the
> kernel reports zero false-positives on a consistent corpus.

## Requirements

| req_id | category | requirement | priority |
|--------|----------|-------------|----------|
| REQ-RESOURCE-PLAN-BILLABLE-001 | Model | Resource plan entity per project (`resource.plan`), one per project. | High |
| REQ-RESOURCE-PLAN-BILLABLE-002 | Model | Plan lines (`resource.plan.line`): employee, role, rate. | High |
| REQ-RESOURCE-PLAN-BILLABLE-014 | Sync | Đồng bộ runs once when a request is Approved L2; source = the request snapshot. | High |
| REQ-RESOURCE-PLAN-BILLABLE-040 | Lifecycle | Submit creates a `resource.plan.request` with a content snapshot (`snapshot_hash`); approval lifecycle lives on the request, not the plan. | High |
| REQ-RESOURCE-PLAN-BILLABLE-041 | Lifecycle | Approve L2 on a request sets `plan.active_request_id` and triggers Đồng bộ from that request's snapshot. | High |
| REQ-RESOURCE-PLAN-BILLABLE-042 | Reporting | Resource Plan Summary reflects the latest Approved-L2 snapshot (`active_request_id`), not the live plan. | High |
