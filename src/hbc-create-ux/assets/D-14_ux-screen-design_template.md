<!-- {project_name}: filled by LLM from project context at generation time. -->
---
document_id: D-14
feature: "{feature}"
title: "{project_name} — UX / Screen Design — feature: {feature}"
version: "1.0"
status: draft
uses_claude_design: false   # set true when the feature uses Claude Design (asked at Stage 1c)
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — UX / Screen Design

## 1. Overview

<!-- Which UI-facing requirements this covers; whether Claude Design is used; the
     DESIGN.md token contract it references. 1–2 paragraphs. -->

## 2. Screens

<!-- Each screen maps to >=1 REQ and the D-06 path it serves. -->

| ID | Screen | REQ Ref | D-06 Path | Mockup Ref (if Claude Design) |
|----|--------|---------|-----------|-------------------------------|
| SCR-01 | … | REQ-{feature}-NNN | path:… | _bmad-output/features/{feature}/ux/… |

## 3. Components

<!-- Reusable units per screen. Visual values reference DESIGN.md tokens by {path.to.token}; do NOT inline hex/px. -->

| ID | Component | Screen | Visual tokens | REQ Ref |
|----|-----------|--------|---------------|---------|
| CMP-01 | … | SCR-01 | {color.primary}, {spacing.md} | REQ-{feature}-NNN |

## 4. States & Interactions

<!-- Per component: default / loading / empty / error / disabled + interaction behaviour. -->

| Component | State | Appearance / Behaviour |
|-----------|-------|------------------------|
| CMP-01 | default | … |
| CMP-01 | error | … |

## 5. Dev Notes

<!-- Non-obvious implementation constraints; accessibility; responsive notes. -->

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
