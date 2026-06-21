<!-- {project_name}: filled by LLM from project context at generation time. -->
---
document_id: D-17
feature: "{feature}"
title: "{project_name} — Behavioral Design — feature: {feature}"
version: "1.0"
status: draft
stepsCompleted: []
lastStep: ""
updated: ""
---

# {project_name} — Behavioral Design

## 1. Overview

<!-- Which requirements are complex (non-CRUD) and why; which block types each uses.
     1–2 paragraphs. Every behavioural element below carries a stable id that D-27
     test cases reference. -->

<!-- One section per complex REQ. Keep only the block types that apply to that REQ. -->

## 2. REQ-{feature}-NNN: (requirement title)

### 2.1 State Transitions

<!-- Include illegal transitions, not only the happy path. -->

| ID | From | Event | Guard | To |
|----|------|-------|-------|-----|
| ST-01 | draft | submit | có ≥1 dòng | submitted |
| ST-02 | submitted | submit | — | (rejected: illegal) |

### 2.2 Decision Table

| ID | Conditions | Action |
|----|-----------|--------|
| DR-01 | … | … |

### 2.3 Invariants

| ID | Invariant (always holds) | Enforcement point |
|----|--------------------------|-------------------|
| INV-01 | … | … |

### 2.4 Sequence / Interaction

<!-- Cross-entity ordering/timing. SEQ-NN per step, or a Mermaid sequenceDiagram. -->

| ID | Step (ordering / timing) |
|----|--------------------------|
| SEQ-01 | … |

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
