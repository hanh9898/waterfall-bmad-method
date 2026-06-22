---
document_id: D-19
title: "Resource Plan & Billable — Database Design (v2.3 clean)"
version: "2.3"
status: approved
---

# D-19 — Database Design (Request + Snapshot model, v2.3)

## Tables

### resource.plan
- **Tên vật lý (Physical name)**: `resource.plan`
- Holds `active_request_id` (the in-force Approved-L2 request).

### resource.plan.request
- **Tên vật lý (Physical name)**: `resource.plan.request`
- Approval lifecycle (submitted / approved_l1 / approved_l2 / rejected) + `snapshot_hash`.

### resource.plan.request.line
- **Tên vật lý (Physical name)**: `resource.plan.request.line`
- Snapshot of plan lines at submit time (the `request_line` set).

### resource.plan.line
- **Tên vật lý (Physical name)**: `resource.plan.line`
