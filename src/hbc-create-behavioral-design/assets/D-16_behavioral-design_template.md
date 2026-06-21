<!-- {project_name}: filled by LLM from project context at generation time. -->
---
document_id: D-16
feature: "{feature}"
title: "{project_name} — Behavioral Design — feature: {feature}"
version: "1.0"
status: draft
stepsCompleted: []
lastStep: ""
updated: ""
semanticReview:
  status: pending   # pending | passed — passed ONLY when openFacets empty AND user signs off
  openFacets: []
---

# {project_name} — Behavioral Design

## 1. Overview

<!-- Which requirements are complex (non-CRUD) and why; which block types each uses.
     1–2 paragraphs. Every behavioural element below carries a stable id that D-27
     test cases reference; each element maps to ≥1 REQ and to its unit-test v_pair. -->

<!-- One section per complex REQ. Keep only the block types that apply to that REQ.
     Mark any open question as [NEEDS CLARIFICATION: …] — the gate reads it as pending. -->

## 2. REQ-{feature}-NNN: (requirement title)

<!-- v_pair: this behaviour is verified at the UNIT-TEST level (D-16 ground_truth = code). -->

### 2.1 State Transitions

<!-- Include illegal transitions, not only the happy path. -->

| ID | From | Event | Guard | To | REQ |
|----|------|-------|-------|-----|-----|
| ST-01 | draft | submit | có ≥1 dòng | submitted | REQ-{feature}-NNN |
| ST-02 | submitted | submit | — | (rejected: illegal) | REQ-{feature}-NNN |

### 2.2 Decision Table

| ID | Conditions | Action | REQ |
|----|-----------|--------|-----|
| DR-01 | … | … | REQ-{feature}-NNN |

### 2.3 Invariants

| ID | Invariant (always holds) | Enforcement point | REQ |
|----|--------------------------|-------------------|-----|
| INV-01 | … | … | REQ-{feature}-NNN |

### 2.4 Sequence / Interaction

<!-- Cross-entity ordering/timing. SEQ-NN per step, or a Mermaid sequenceDiagram. -->

| ID | Step (ordering / timing) | REQ |
|----|--------------------------|-----|
| SEQ-01 | … | REQ-{feature}-NNN |

### 2.5 BDD Scenarios (Given / When / Then)

<!-- One scenario per behaviour that downstream acceptance/ATDD (D-26/D-27 [TS], [AC])
     derives from. Reference the element ids it exercises. Keep Given/When/Then. -->

- **Scenario (ST-01):** Given a plan in draft với ≥1 dòng, When người dùng submit,
  Then trạng thái chuyển sang submitted và `submitted_at` được ghi.
- **Scenario (INV-01):** Given một plan đã submitted, When ai đó sửa dòng đơn,
  Then thao tác bị chặn (snapshot bất biến).

## 3. Grounding-to-code log

<!-- D-16 ground_truth = code (reconcile_seam: behavioral-vs-code). Record where each
     behaviour was reconciled against the REAL code (model/method), and EVERY divergence
     (design-only = planned-not-built / stale; code-only = undocumented behaviour) with
     its resolution. Greenfield → "N/A (no code yet)". The advisory
     check-behavioral-grounding.py surfaces model drift structurally; this row records
     the human resolution. -->

| Element | Grounded against (model.method) | Divergence | Resolution |
|---------|---------------------------------|------------|------------|
| ST-01 | resource.plan.action_submit | — | matches |

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | | | Initial creation |
