<!-- {project_name}: filled by LLM from project context at generation time. -->
---
document_id: D-14
feature: "{feature}"
title: "{project_name} — UX / Screen Design — feature: {feature}"
version: "1.0"
status: draft
uses_claude_design: false   # set true when the feature uses Claude Design (asked at Stage 1c)
maturity: standard          # standard | exploratory  (exploratory relaxes gate ceremony — T3.16)
design_token_source: ""     # the SINGLE source of visual tokens (e.g. DESIGN.md). Required when uses_claude_design (UX-6).
semanticReview:
  status: pending           # pending | passed
  openFacets: []
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — UX / Screen Design

## 1. Overview

<!-- Which UI-facing requirements this covers; whether Claude Design is used; the
     DESIGN.md token contract it references. 1–2 paragraphs.
     If the feature has no `has-ui` facet (catalog instance marks D-14 N/A),
     do NOT fabricate screens — state N/A and stop. -->

## 2. Screens

<!-- Each screen maps to >=1 REQ and the D-06 path it serves. Mockup Ref is the
     committed Claude Design path PER SCREEN (UX-2 design-sync) when used; else `—`. -->

| ID | Screen | REQ Ref | D-06 Path | Mockup Ref (if Claude Design) |
|----|--------|---------|-----------|-------------------------------|
| SCR-01 | … | REQ-{feature}-NNN | path:… | _bmad-output/features/{feature}/ux/… |

## 3. Components

<!-- Reusable units per screen. Visual values reference design tokens by
     {path.to.token} from the SINGLE design_token_source (UX-3 / UX-6);
     do NOT inline hex/px. Code Ref names the component in code (UX-3 component-map
     ↔ code) once implemented — `—` until then. -->

| ID | Component | Screen | Visual tokens | Code Ref | REQ Ref |
|----|-----------|--------|---------------|----------|---------|
| CMP-01 | … | SCR-01 | {color.primary}, {spacing.md} | — | REQ-{feature}-NNN |

## 4. States & Interactions

<!-- Per component: default / loading / empty / error / disabled + interaction behaviour.
     Enumerate beyond the happy path — error/empty/disabled are first-class. -->

| Component | State | Appearance / Behaviour |
|-----------|-------|------------------------|
| CMP-01 | default | … |
| CMP-01 | error | … |

## 5. Traceability (REQ → Screen → Component → Test)

<!-- UX-4: the full UI trace chain. Test Ref is the E2E / UI test id that exercises
     the screen (UX-7 outside-in ATDD — the test is named here BEFORE code exists).
     The living matrix is owned by `hbc-traceability` [TR] (forward-ref); this table
     is D-14's own authoritative slice, which TR ingests. `—` for a not-yet-written test. -->

| REQ Ref | Screen | Component(s) | Test Ref (E2E / UI) |
|---------|--------|--------------|---------------------|
| REQ-{feature}-NNN | SCR-01 | CMP-01 | E2E-{feature}-NNN |

## 6. UI Acceptance & Visual Regression

<!-- UX-5: the PROCEDURE, not a live engine. State, per screen:
     - Acceptance criteria (what "correct UI" means — observable, derived from REQ/states).
     - Visual-regression baseline reference (Mockup Ref above when Claude Design is
       used; else a description / N/A). The visual-diff TOOL is consumer-provided —
       name the contract (baseline path + tolerance), do not assume a specific tool.
     The actual visual-diff run + pass/fail is owned by Phase 4 [TE]/[AC]. -->

| Screen | Acceptance criteria | Visual-regression baseline | Method (consumer tool) |
|--------|---------------------|----------------------------|------------------------|
| SCR-01 | … | _bmad-output/features/{feature}/ux/… or N/A | … |

## 7. Dev Notes

<!-- Non-obvious implementation constraints; accessibility; responsive notes;
     maturity (exploratory relaxes which of the above are mandatory — UX-8). -->

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
