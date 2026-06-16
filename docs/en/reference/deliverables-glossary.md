# Deliverables Glossary (D-xx)

> 🌐 **English** · [Tiếng Việt](../../vi/reference/deliverables-glossary.md)
>
> 📖 **Reference** — quick lookup of every deliverable HBC produces. To understand *what a deliverable is / why the codes*, see [Core Concepts](../explanation/concepts.md).

The `D-xx` codes belong to HBLAB's standard document set. HBC currently produces the **8 D-xx documents** below, plus a few non-D-coded artifacts (task breakdown, test reports, gate, traceability matrix).

## D-xx documents

> **Required** column: ✅ = required (a condition for passing the Phase Gate) · `—` = optional.

| Code | Name | Phase | Skill | Required | Output location |
| --- | --- | --- | --- | :---: | --- |
| **D-02** | Requirements Specification | 1 · Analysis | `REQ` | ✅ | `planning_artifacts` |
| **D-03** | Glossary | 1 · Analysis | `GLO` | — | `planning_artifacts` |
| **D-06** | Business Flow Diagram (AS-IS/TO-BE) | 1 · Analysis | `BFD` | — | `planning_artifacts` |
| **D-12** | Coding Standards | 2 · Design | `CS` | ✅ | `planning_artifacts` |
| **D-19** | Database Design / ER Diagram | 2 · Design | `ERD` | ✅ | `planning_artifacts` |
| **D-21** | API Specification | 2 · Design | `API` | — | `planning_artifacts` |
| **D-26** | Test Plan | 2 · Design | `TP` | ✅ | `planning_artifacts` |
| **D-27** | Test Specification | 2 · Design | `TS` | ✅ | `planning_artifacts` |

> 📌 The "missing" codes (D-01, D-04, D-05…) belong to the broader HBLAB standard but are **not** produced by HBC — don't mistake them for gaps.

## Per-document detail

### D-02 — Requirements Specification ✅
Requirements with **REQ-xxx IDs** and scope boundaries. The foundation for every later phase and the source for initializing traceability (`TRI`).

### D-03 — Glossary
Unified domain terminology, compiled from project documents and requirements. Optional.

### D-06 — Business Flow Diagram
AS-IS / TO-BE business flow diagrams in Mermaid, built from the PRD and planning artifacts. Optional.

### D-12 — Coding Standards ✅
Per-project coding standards — naming, formatting, error handling — adapted to the framework in use.

### D-19 — Database Design / ER Diagram ✅
Database design document with an ER Diagram (Mermaid), derived from requirements and architecture.

### D-21 — API Specification
API spec — endpoints and request/response schemas. Optional.

### D-26 — Test Plan ✅
Test plan — strategy, scope, schedule, entry/exit criteria, and risk assessment.

### D-27 — Test Specification ✅
Detailed test cases with **TC-xxx IDs**, steps, and expected results. The source for writing tests during TDD in Phase 3.

## Non-D-coded artifacts

| Artifact | Phase | Skill | Output location |
| --- | --- | --- | --- |
| Task Breakdown | 3 · Implementation | `TB` | `implementation_artifacts` |
| Code (TDD) | 3 · Implementation | `IM` | `implementation_artifacts` |
| Test Execution Report | 4 · Testing | `TE` | `implementation_artifacts` |
| Acceptance Report | 4 · Testing | `AC` | `implementation_artifacts` |
| Phase Gate Report | cross-cutting | `PG` | `{output_folder}/gates` |
| Traceability Matrix | cross-cutting | `TRI`/`TRU` | `{output_folder}/traceability` |

> Traceability matrix columns: `design_ref` / `code_ref` / `test_ref` / `gate_status`.

## Related

- 📖 Look up **concepts** (not codes): [Concept Glossary](concept-glossary.md).
- 📖 Full skill list with descriptions & ordering: [Skills Catalog](skills-catalog.md).
- 🗺️ See where deliverables sit in the workflow: [Workflow Map](../tutorials/workflow-map.md).
