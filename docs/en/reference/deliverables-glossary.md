# Deliverables Glossary (D-xx)

> 🌐 **English** · [Tiếng Việt](../../vi/reference/deliverables-glossary.md)
>
> 📖 **Reference** — quick lookup of every deliverable HBC produces. To understand *what a deliverable is / why the codes*, see [Core Concepts](../explanation/concepts.md).

The `D-xx` codes belong to HBLAB's standard document set. HBC currently produces the **11 D-xx documents** below, plus a few non-D-coded artifacts (task breakdown, test reports, gate, traceability matrix).

HBC ships **incrementally, per feature (incremental per-feature)**: each feature goes through Phase 1→4 and then ships independently. Each deliverable therefore has a **scope**:

- **per-feature** — produced separately for each feature, stored under `features/<feature>/…`.
- **shared** — project-wide, stored under `shared/…`, produced **once** in Phase 0 (`hbc-project-init`).
- **dual** — a shared baseline at `shared/…` plus an optional **per-feature override**; resolved by path-existence precedence (the override wins if it exists).

> 📌 **Phase 0 — Project Init** (`PI`): **mandatory and runs first**, once for the whole project (or re-run to update directly). **Brownfield-aware** — for an existing codebase it documents the code first (`bmad-document-project` + `project-context.md`) then derives the shared deliverables; greenfield derives them from the PRD/choices. Creates the shared deliverables — **D-12 Coding Standards, D-03 Glossary** — and baseline D-19 ERD / D-21 API. No `feature` argument.

## D-xx documents

> **Required** column: ✅ = required (a condition for passing the Phase Gate) · ◑ = **required by facet** (the applicability-catalog decides per-feature — see the note below) · `—` = optional.
> **Scope** column: per-feature · shared · dual.

| Code | Name | Phase | Skill | Required | Scope | Output location |
| --- | --- | --- | --- | :---: | --- | --- |
| **D-02** | Requirements Specification | 1 · Analysis | `REQ` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-03** | Glossary | 1 · Analysis | `GLO` | — | shared | `shared/glossary/` |
| **D-06** | Business Flow Diagram (AS-IS/TO-BE) | 1 · Analysis | `BFD` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-09** | Architecture Design | 2 · Design | `AD` | ◑ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-12** | Coding Standards | 2 · Design | `CS` | ✅ | shared | `shared/coding-standards/` |
| **D-14** | UX / Screen Design | 2 · Design | `UX` | ◑ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-16** | Behavioral Design | 2 · Design | `BD` | ◑ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-19** | Database Design / ER Diagram | 2 · Design | `ERD` | ✅ | dual | `shared/erd/` (+ per-feature override) |
| **D-21** | API Specification | 2 · Design | `API` | — | dual | `shared/api/` (+ per-feature override) |
| **D-26** | Test Plan | 2 · Design | `TP` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-27** | Test Specification | 2 · Design | `TS` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |

> 📌 **Applicability by facet (◑).** D-09, D-14, D-16 are **conditional design deliverables**: they are only required when the feature carries the matching **facet** (see `src/hbc-shared/references/deliverable-catalog.yaml`). If the feature lacks that facet → the deliverable is **N/A** and does not block the gate. A minimal feature (pure CRUD, no UI, no integration) only requires D-02 + D-06.
>
> 📌 The "missing" codes (D-04, D-05, **D-08 Basic Design / 基本設計書**, **D-17 Sequence Diagram / シーケンス図**, D-18 Class Diagram…) belong to the **broader HBLAB standard** (see `templates/`) but are **not** produced by HBC — don't mistake them for gaps. **D-01 (Feature Overview)** has been **folded into the D-02 header** and is no longer a separate document.
>
> 📌 **Aligned to canonical HBLAB numbering:** HBC's codes follow the standard — **D-09 = Architecture** (アーキテクチャ設計書) and **D-16 = Behavioral/Detailed Design** (詳細設計書). (Before 2026-06-21 HBC mis-used D-08/D-17; now reconciled — see `process-review/hbc-dcode-reconcile-2026-06-21.md`.)

## Per-document detail

### D-02 — Requirements Specification ✅
Requirements with **REQ IDs** and scope boundaries. IDs follow **`REQ-<FEAT>-NNN`** (e.g. `REQ-AUTH-001`) for per-feature requirements, plus **`REQ-SHARED-NNN`** for shared requirements (legacy `REQ-NNN` still parses). The foundation for every later phase and the source for initializing traceability (`TRI`). Scope: per-feature → `features/<feature>/planning-artifacts/`.

### D-03 — Glossary
Unified domain terminology, compiled from project documents and requirements. Optional. Scope: shared → `shared/glossary/`, **produced in Phase 0 (`PI`)**; `GLO` maintains it thereafter.

### D-06 — Business Flow Diagram ✅
AS-IS / TO-BE business flow diagrams in Mermaid, built from the PRD and planning artifacts. Required — a condition for passing Phase Gate 1. Scope: per-feature → `features/<feature>/planning-artifacts/`.

### D-09 — Architecture Design ◑
Architecture / solution design: components, boundaries, integration flows, and **ADRs** (Architecture Decision Records — decision + rationale). **Required by facet:** required if the feature has `has-integration` (touches an external module/system) or `has-algorithm` (non-trivial computation); otherwise optional. Scope: per-feature → `features/<feature>/planning-artifacts/`.

### D-12 — Coding Standards ✅
Per-project coding standards — naming, formatting, error handling — adapted to the framework in use. Scope: shared → `shared/coding-standards/`, **produced in Phase 0 (`PI`)**; `CS` maintains it thereafter.

### D-14 — UX / Screen Design ◑
Experience & screen design: screens (SCR), components (CMP), states, navigation; optionally uses **Claude Design** to generate `DESIGN.md` tokens. **Required by facet:** required if the feature has `has-ui` (user-facing screens); otherwise N/A. Scope: per-feature → `features/<feature>/planning-artifacts/`.

### D-16 — Behavioral Design ◑
Non-CRUD behavior spec in 4 element-ID blocks: **ST** (state-machine), **DR** (decision-rule), **INV** (invariant), **SEQ** (sequence). **Required by facet:** required if the feature is "non-CRUD complex" — has any of the facets `has-state-machine` / `has-cross-entity-sync` / `has-invariant` / `has-algorithm` / `has-concurrency`; otherwise N/A. The source for QA's unit-test design (V-pair). Scope: per-feature → `features/<feature>/planning-artifacts/`.

### D-19 — Database Design / ER Diagram ✅
Database design document with an ER Diagram (Mermaid), derived from requirements and architecture. Scope: dual — baseline at `shared/erd/`, with an optional per-feature override at `features/<feature>/planning-artifacts/` (the override wins if it exists).

### D-21 — API Specification
API spec — endpoints and request/response schemas. Optional. Scope: dual — baseline at `shared/api/`, with an optional per-feature override at `features/<feature>/planning-artifacts/` (the override wins if it exists).

### D-26 — Test Plan ✅
Test plan — strategy, scope, schedule, entry/exit criteria, and risk assessment. Scope: per-feature → `features/<feature>/planning-artifacts/`.

### D-27 — Test Specification ✅
Detailed test cases with **`TC-NNN` IDs** (numbered sequentially **within each feature**), steps, and expected results. The source for writing tests during TDD in Phase 3. Scope: per-feature → `features/<feature>/planning-artifacts/`.

## Non-D-coded artifacts

| Artifact | Phase | Skill | Output location |
| --- | --- | --- | --- |
| Discovery Note (model validation — pre-freeze, conditional) | 1 · Analysis | `DSC` | `features/<feature>/planning-artifacts/` |
| Task Breakdown | 3 · Implementation | `TB` | `features/<feature>/implementation-artifacts/` |
| Code (TDD) | 3 · Implementation | `IM` | `features/<feature>/implementation-artifacts/` |
| Test Execution Report | 4 · Testing | `TE` | `features/<feature>/implementation-artifacts/` |
| Acceptance Report | 4 · Testing | `AC` | `features/<feature>/implementation-artifacts/` |
| Phase Gate Report | cross-cutting | `PG` | `features/<feature>/gates/` |
| Traceability Matrix | cross-cutting | `TRI`/`TRU` | `features/<feature>/traceability/` |

> Traceability matrix columns — now **8 columns**: `feature` / `req_id` / `story_id` / `design_ref` / `code_ref` / `test_ref` / `gate_status` / `timestamp`. Coverage is counted from `design_ref` / `code_ref` / `test_ref`. The matrix is per-feature; `TRR` can roll up across features (shared rows counted once).

## Related

- 📖 Look up **concepts** (not codes): [Concept Glossary](concept-glossary.md).
- 📖 Full skill list with descriptions & ordering: [Skills Catalog](skills-catalog.md).
- 🗺️ See where deliverables sit in the workflow: [Workflow Map](../tutorials/workflow-map.md).
