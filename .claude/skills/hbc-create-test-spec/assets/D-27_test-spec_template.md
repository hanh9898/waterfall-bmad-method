---
document_id: D-27
title: "{project_name} — Đặc tả kiểm thử"
version: "1.0"
status: draft
tc_count: 0
coverage: 0
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — Đặc tả kiểm thử (Test Specification)

## 1. Tổng quan (Overview)

### 1.1 Mục đích (Purpose)

<!-- Purpose and scope of this test specification -->

### 1.2 Tài liệu tham chiếu (Reference Documents)

| Document | ID | Description |
|----------|----|-------------|

### 1.3 Quy ước mã test case (Test Case ID Format)

Format: `TC-xxx` (sequential from TC-001). Each TC links to one or more REQ-xxx IDs.

## 2. Danh sách test case (Test Case Summary)

| TC ID | Category | REQ ID | Description | Severity | Status |
|-------|----------|--------|-------------|----------|--------|

## 3. Chi tiết test case (Detailed Test Cases)

<!-- Repeat this block for each test case -->

### TC-xxx: {test_case_name}

**REQ ID:** REQ-xxx
**Facets:** read | write | api | admin | ui | batch  (comma-separated facets this TC exercises — see semantic-review-rubric.md; enables automated facet coverage M-1)
**Category:** Functional | Non-Functional | Security | Performance | Integration
**Severity:** Critical | High | Medium | Low
**Preconditions:**

- <!-- List preconditions -->

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|

**Postconditions:**

<!-- Expected state after test execution -->

## 4. Ma trận bao phủ (Coverage Matrix)

<!-- `Facets` lists the facets REQUIRED for each REQ (read/write · api/admin · lifecycle).
     check-facet-coverage.py (M-1) verifies every required facet has a covering TC. -->

| REQ ID | Requirement Summary | Test Cases | Facets | Coverage |
|--------|-------------------|------------|--------|----------|

## 5. Yêu cầu dữ liệu kiểm thử (Test Data Requirements)

<!-- Shared test data specifications, data generation strategy -->

## Lịch sử sửa đổi (Revision History)

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
