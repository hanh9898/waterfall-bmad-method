# Concept Glossary

> 🌐 **English** · [Tiếng Việt](../../vi/reference/concept-glossary.md)
>
> 📖 **Reference** — hit an unfamiliar term in the HBC docs? Look it up here. Each entry is a short answer-first definition with a link to go deeper.
>
> ℹ️ This is a glossary of **HBC concepts**. If you want the lookup of **deliverable codes** (D-02, D-19…), see the [Deliverables Glossary](deliverables-glossary.md); for **skills/agents** see the [Skills Catalog](skills-catalog.md). Don't confuse it with *D-03 Glossary* — that's a glossary of **your project's business terminology**, produced by you, not an explanation of HBC.

## Delivery model & lifecycle

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **Incremental (staged delivery)** | **HBC's delivery model**: ship **one feature at a time**, each a gated cycle + TDD, shipped independently of other features. | [Why Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **Feature** | HBC's unit of delivery: one slice of scope that runs through all 4 phases + TDD, then ships on its own. Each feature has a `<slug>` (e.g. `auth`) that keys its folders and IDs. | [Why Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **Phase** | One of HBC's 4 ordered stages: Analysis → Design → Implementation → Testing. | [Core Concepts](../explanation/concepts.md) |
| **Phase 0 (Project Init)** | A step run **once, project-wide** before any feature (skill `PI` / hbc-project-init): produces the **shared** deliverables (D-12, D-03) + baseline D-19/D-21. Idempotent (skips what exists), no `feature` arg. | [Skills Catalog (PI)](skills-catalog.md) |
| **Phase Gate** | A control checkpoint at each phase boundary — must "pass" to advance (command `PG <n>`, carrying `feature=`). | [Core Concepts](../explanation/concepts.md) |
| **Entry/Exit criteria** | The conditions to *start* a phase and to consider it *done*. | [Deliverables Glossary (D-26)](deliverables-glossary.md) |

## Scope & deliverables

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **Scope** | A deliverable belongs to one of three scopes: **per-feature** (specific to one feature), **shared** (project-wide, reused), or **dual** (a shared baseline + optional per-feature override). | [Deliverables Glossary](deliverables-glossary.md) |
| **Shared deliverable** | A document produced **once for the whole project** and reused by every feature: D-03 Glossary, D-12 Coding Standards. Stored under `_bmad-output/shared/…`. | [Deliverables Glossary (D-12)](deliverables-glossary.md) |
| **Per-feature override** | For a **dual** deliverable (D-19 ERD, D-21 API): if a feature needs its own version, place a file in `features/<feature>/planning-artifacts/` to **override** the shared baseline. | [Deliverables Glossary (D-19)](deliverables-glossary.md) |
| **Path-existence precedence** | The rule for picking a dual deliverable: **if a per-feature override file exists it wins**, otherwise the shared baseline is used. No config needed — it depends only on which path actually exists. | [Deliverables Glossary](deliverables-glossary.md) |

## Traceability

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **Traceability** | Linking each requirement to its design, code, and tests — so no requirement is missed. | [Core Concepts](../explanation/concepts.md) |
| **Traceability matrix (8-column)** | The per-feature trace table, **8 columns**: `feature \| req_id \| story_id \| design_ref \| code_ref \| test_ref \| gate_status \| timestamp`. Coverage counts `design_ref`/`code_ref`/`test_ref`. | [Manage Traceability](../how-to/manage-traceability.md) |
| **Rollup (TRR — cross-feature)** | The `TRR` skill rolls several features' matrices into one summary; **shared** rows are counted only once. | [Manage Traceability](../how-to/manage-traceability.md) |
| **REQ-\<FEAT\>-NNN** | The **per-feature** requirement ID namespace (e.g. `REQ-AUTH-001`), created in D-02. Shared requirements use **`REQ-SHARED-NNN`**. Legacy `REQ-NNN` still parses. | [D-02 Requirements](deliverables-glossary.md) |
| **TC-NNN** | The test-case identifier, numbered **sequentially within each feature's D-27** (e.g. `TC-001`). | [D-27 Test Spec](deliverables-glossary.md) |
| **Coverage** | The share of requirements that have a complete trace chain (design + code + test). | [Manage Traceability](../how-to/manage-traceability.md) |
| **Cascade Sync (SYNC)** | When a source document changes, the `SYNC` skill analyzes impact and **proposes cascade updates** down to the dependent documents/tests/code. | [Manage Traceability](../how-to/manage-traceability.md) |

## Implementation & testing

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **TDD** | Test-Driven Development: **write the test first**, then write code to make it pass. | [Why Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **RED → GREEN → REFACTOR** | The TDD cycle: 🔴 write a failing test → 🟢 write minimal code to pass → ♻️ clean up, tests stay green. | [Why Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **RED evidence — soft TDD** | **Soft enforcement**: before writing code you must record evidence that a test is failing (🔴); the Phase 3 gate checks for RED evidence (self-attested, not cryptographic proof). The spirit: "test-first with RED evidence", not just "tests exist". | [Why Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **EARS** | A syntax for clear, conditional requirements; keywords stay in English (`WHEN … THE SYSTEM SHALL …`), prose follows `{document_output_language}`. | [D-02 Requirements](deliverables-glossary.md) |
| **Readiness check (IR)** | The **Phase-2 seam gate** (skill `IR` / hbc-check-implementation-readiness): reconciles D-02 ↔ D-21/D-26/D-27 + the matrix before Phase 3, to catch gaps between design and implementation. | [Skills Catalog (IR)](skills-catalog.md) |
| **ERD (ER Diagram)** | Entity-Relationship Diagram — describes data tables and the links between them (deliverable D-19). | [D-19 Database Design](deliverables-glossary.md) |
| **Triage (defects)** | Classifying and prioritizing the defects found, so the important ones are handled first. | [Deliverables Glossary](deliverables-glossary.md) |
| **Deterministic** | "Gives a fixed result" — automated checks by hard rules (yes/no), not subjective judgment. | [Core Concepts](../explanation/concepts.md) |

## Acceptance

| Term | Short definition |
| --- | --- |
| **Acceptance** | The final evaluation: does the feature meet requirements to be handed over (command `AC review`) — each feature ships independently. |
| **ACCEPTED** | Passed — accepted for handover. |
| **REJECTED** | Failed — has defects/gaps that must be fixed and re-evaluated. |
| **DEFERRED** | Postponed — conditionally accepted, the missing part is handled later (by agreement). |
| **PENDING** | Undecided — waiting on information/results to make the call. |

## Related

- 💡 Understand the 4 foundational concepts in depth: [Core Concepts](../explanation/concepts.md).
- 📖 Look up deliverable codes: [Deliverables Glossary](deliverables-glossary.md).
- 📖 Look up skills: [Skills Catalog](skills-catalog.md).
- ❓ Not sure what's next? Call **`bmad-help`** — the always-available "what next" helper.
