---
stepsCompleted: []
inputDocuments: []
format: INVEST + 3Cs
epicCount: 0
totalPoints: 0
validationStatus: pending
---

# {{project_name}} - INVEST User Stories

Pure INVEST + 3C's user stories cho {{project_name}}. Mỗi story là Independent, Negotiable, Valuable, Estimable, Small (1-2 ngày), và Testable. Acceptance criteria chỉ mô tả hành vi user quan sát được — không chứa bất kỳ chi tiết kỹ thuật nào.

### Story Points Legend

| Points | Ý nghĩa | Thời gian |
|--------|---------|-----------|
| 1 | Trivial — thay đổi đơn giản, rõ ràng | < nửa ngày |
| 2 | Small — đơn giản, không có unknowns | nửa ngày |
| 3 | Medium — rõ ràng nhưng nhiều phần | 1 ngày |
| 5 | Large — có complexity, ở giới hạn | 1-2 ngày |
| 8 | Quá lớn — **bắt buộc split** | > 2 ngày |

## Requirements Inventory

### Functional Requirements

{{fr_list}}

### Non-Functional Requirements

{{nfr_list}}

### Additional Requirements

{{additional_requirements}}

### UX Design Requirements

{{ux_design_requirements}}

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}

<!-- Repeat for each epic (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

**Story Points:** {{fibonacci_points}} | **Parallel:** {{yes_no}}

**Card:**
As a {{user_role}},
I want {{capability}},
So that {{value_benefit}}.

**Conversation:**
{{negotiation_notes_and_context}}

**Confirmation:**

- [ ] **Given** {{precondition}} **When** {{user_action}} **Then** {{observable_outcome}}
- [ ] **Given** {{precondition}} **When** {{user_action}} **Then** {{observable_outcome}}

<!-- End story repeat -->

## Technical Tasks

> Công việc cần thiết cho implementation nhưng không mang giá trị trực tiếp cho user.
> Đây KHÔNG phải user stories — thuộc Definition of Done hoặc sprint overhead.

{{technical_tasks_list}}

## INVEST Validation Summary

| Tiêu chí | Pass | Ghi chú |
|----------|------|---------|
| Independent | {{pass_fail}} | {{notes}} |
| Negotiable | {{pass_fail}} | {{notes}} |
| Valuable | {{pass_fail}} | {{notes}} |
| Estimable | {{pass_fail}} | {{notes}} |
| Small | {{pass_fail}} | {{notes}} |
| Testable | {{pass_fail}} | {{notes}} |
