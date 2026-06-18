<!-- {project_name}: filled by LLM from project context at generation time, not a workflow config variable. -->
---
document_id: D-02
feature: "{feature}"
title: "{project_name} — Requirements Specification — feature: {feature}"
version: "1.0"
project_kind: "greenfield"   # set to "brownfield" when grounded against an existing system (enables --brownfield checks)
# na_deliverables — OPTIONAL: deliverables not-applicable to THIS feature; the phase
# gate waives them (reports NA, not FAIL). ONLY D-19 (no data-model change) / D-21 (no
# API) — D-02/D-03/D-06 always apply. Give a one-line rationale.
#   na_deliverables: ["D-19"]   # rationale: this feature changes no data model
status: draft
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — Requirements Specification

## 1. Project Overview

### 1.1 Purpose

<!-- Project purpose and background -->

### 1.2 Stakeholders

| Name | Role | Responsibility |
|------|------|---------------|

### 1.3 Timeline Constraints

<!-- Key dates, deadlines, dependencies -->

## 2. Scope

### 2.1 In Scope

<!-- Explicit list of what IS included -->

### 2.2 Out of Scope

<!-- Explicit list of what is NOT included — as important as in-scope -->

## 3. User Roles

| Role | Description | Key Requirements |
|------|-------------|-----------------|

## 4. Functional Requirements

<!--
  REQ ID: `REQ-<FEAT>-NNN` (e.g. REQ-{feature}-001), sequential within this feature.
  Requirements shared across features: define them in the shared D-02 as `REQ-SHARED-NNN`,
  then reference (do not redefine) here in the Acceptance/User Role column.
  Write the Requirement column in EARS — English keywords, content in {document_output_language}:
    "WHEN <condition> THE SYSTEM SHALL <behavior>"
    "THE SYSTEM SHALL <behavior>" (ubiquitous)
    "WHILE <state> ... / IF <unexpected> THEN THE SYSTEM SHALL ..."
-->

| REQ ID | Category | Requirement (EARS) | Priority | User Role | Acceptance Criteria |
|--------|----------|--------------------|----------|-----------|-------------------|

<!--
  BROWNFIELD ONLY (project has existing code → Phase 0 produced project-context.md):
  reconcile every requirement against the EXISTING system. Use the EXTENDED table
  below (adds Change Type + Existing System Ref) INSTEAD of the one above, and add a
  Change Spec block per CHANGE/REMOVE requirement. Greenfield: ignore this block.

  | REQ ID | Category | Requirement (EARS) | Change Type | Existing System Ref | Priority | User Role | Acceptance Criteria |
  |--------|----------|--------------------|-------------|---------------------|----------|-----------|-------------------|

  - Change Type: NEW | CHANGE | REMOVE
  - Existing System Ref: the existing feature/flow/entity it touches
    (e.g. flow:checkout, entity:Invoice, feature:resource-plan) — NOT a code path.
  - NEW requirements need no Change Spec; CHANGE/REMOVE require one:

  #### Change Spec — REQ-<FEAT>-NNN
  - AS-IS (current behavior): …
  - TO-BE (target behavior — WHAT changes; the Acceptance Criteria column is HOW to verify it): …
  - Invariants (must stay unchanged): …
  - Out-of-scope (NOT changing this release): …
-->

## 5. Non-Functional Requirements

### 5.1 Performance

| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|

### 5.2 Security

| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|

### 5.3 Availability

| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|

### 5.4 Usability

| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|

## 6. Constraints and Assumptions

### 6.1 Technical Constraints

<!-- Technology stack, infrastructure limits, integration requirements -->

### 6.2 Business Constraints

<!-- Budget, timeline, regulatory, organizational constraints -->

### 6.3 Assumptions

<!-- What is assumed true for this specification -->

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
