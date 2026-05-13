---
stepsCompleted: []
inputDocuments: []
format: INVEST + 3Cs
---

# {{project_name}} - INVEST User Stories

## Overview

Pure INVEST + 3C's user stories for {{project_name}}. Each story is Independent, Negotiable, Valuable, Estimable, Small (1-2 days), and Testable. Acceptance criteria describe observable user behavior only — implementation details live in Architecture.md.

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

**Story Points:** {{fibonacci_points}}

**Card:**
As a {{user_role}},
I want {{capability}},
So that {{value_benefit}}.

**Conversation:**
{{negotiation_notes_and_context}}

**Confirmation:**

- [ ] **Given** {{precondition}} **When** {{user_action}} **Then** {{observable_outcome}}
- [ ] **Given** {{precondition}} **When** {{user_action}} **Then** {{observable_outcome}}

> Implementation reference: See Architecture.md § {{relevant_section}}

<!-- End story repeat -->

## Technical Tasks

> Items that are necessary for implementation but do not deliver direct user value.
> These are NOT user stories — they belong in Definition of Done or sprint overhead.

{{technical_tasks_list}}

## Comparison Notes

> How this document differs from epics.md (implementation stories format):
> - AC describes user-observable behavior only (no code/syntax/file paths)
> - Stories sized to 1-2 days max (Fibonacci: 1, 2, 3, 5, 8)
> - Enabler/foundation work moved to Technical Tasks or DoD
> - "As a System" stories reframed as user-centric or moved to Technical Tasks
> - Dependencies minimized for parallel implementation
> - Implementation HOW deferred to Architecture.md references
