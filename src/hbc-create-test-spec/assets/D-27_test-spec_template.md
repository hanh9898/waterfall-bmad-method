---
document_id: D-27
title: "{project_name} — Test Specification"
version: "1.0"
status: draft
tc_count: 0
coverage: 0
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — Test Specification

## 1. Overview

### 1.1 Purpose

<!-- Purpose and scope of this test specification -->

### 1.2 Reference Documents

| Document | ID | Description |
|----------|----|-------------|

### 1.3 Test Case ID Format

Format: `TC-xxx` (sequential from TC-001). Each TC links to one or more REQ-xxx IDs.

## 2. Test Case Summary

| TC ID | Category | REQ ID | Description | Severity | Status |
|-------|----------|--------|-------------|----------|--------|

## 3. Detailed Test Cases

<!-- Repeat this block for each test case -->

### TC-xxx: {test_case_name}

**REQ ID:** REQ-xxx
**Facets:** TODO
<!-- Replace TODO with the comma-separated facets THIS TC exercises (choose from
     read/write · api/admin/ui/batch · lifecycle); see semantic-review-rubric.md —
     enables automated facet coverage (M-1). A TC may list several REQ IDs
     (comma-separated) above. Leaving "TODO" fails the M-1 check LOUDLY rather than
     silently claiming a facet the TC does not actually exercise. -->
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

## 4. Coverage Matrix

<!-- `Facets` lists the facets REQUIRED for each REQ (read/write · api/admin · lifecycle).
     check-facet-coverage.py (M-1) verifies every required facet has a covering TC.
     Required facets may instead (or also) be declared in a `Facets` column on the
     D-02 functional requirements table — M-1 UNIONS both sources (pass --d02). -->

| REQ ID | Requirement Summary | Test Cases | Facets | Coverage |
|--------|-------------------|------------|--------|----------|

## 5. Test Data Requirements

<!-- Shared test data specifications, data generation strategy -->

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
