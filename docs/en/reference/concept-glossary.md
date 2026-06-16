# Concept Glossary

> 🌐 **English** · [Tiếng Việt](../../vi/reference/concept-glossary.md)
>
> 📖 **Reference** — hit an unfamiliar term in the HBC docs? Look it up here. Each entry is a short answer-first definition with a link to go deeper.
>
> ℹ️ This is a glossary of **HBC concepts**. If you want the lookup of **deliverable codes** (D-02, D-19…), see the [Deliverables Glossary](deliverables-glossary.md). Don't confuse it with *D-03 Glossary* — that's a glossary of **your project's business terminology**, produced by you, not an explanation of HBC.

## Process & lifecycle

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **Waterfall** | A sequential model: finish one phase before the next, no skipping. | [Why Waterfall + TDD](../explanation/why-waterfall-tdd.md) |
| **Phase** | One of HBC's 4 ordered stages: Analysis → Design → Implementation → Testing. | [Core Concepts](../explanation/concepts.md) |
| **Deliverable** | A handover artifact from a phase (a document or code), usually coded `D-xx`. | [Core Concepts](../explanation/concepts.md) |
| **Phase Gate** | A control checkpoint at each phase boundary — must "pass" to advance (command `PG <n>`). | [Core Concepts](../explanation/concepts.md) |
| **Entry/Exit criteria** | The conditions to *start* a phase and to consider it *done*. | [Deliverables Glossary (D-26)](deliverables-glossary.md) |

## Traceability

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **Traceability** | Linking each requirement to its design, code, and tests — so no requirement is missed. | [Core Concepts](../explanation/concepts.md) |
| **Traceability matrix** | The table that does it: one row per requirement, columns for design/code/test. | [Manage Traceability](../how-to/manage-traceability.md) |
| **REQ ID** | The identifier of a requirement (e.g. `REQ-001`), created in D-02, the anchor for all tracing. | [D-02 Requirements](deliverables-glossary.md) |
| **TC ID** | The identifier of a test case (e.g. `TC-001`), created in D-27. | [D-27 Test Spec](deliverables-glossary.md) |
| **Coverage** | The share of requirements that have a complete trace chain (design + code + test). | [Manage Traceability](../how-to/manage-traceability.md) |

## Implementation & testing

| Term | Short definition | Go deeper |
| --- | --- | --- |
| **TDD** | Test-Driven Development: **write the test first**, then write code to make it pass. | [Why Waterfall + TDD](../explanation/why-waterfall-tdd.md) |
| **RED → GREEN → REFACTOR** | The TDD cycle: 🔴 write a failing test → 🟢 write minimal code to pass → ♻️ clean up, tests stay green. | [Why Waterfall + TDD](../explanation/why-waterfall-tdd.md) |
| **ERD (ER Diagram)** | Entity-Relationship Diagram — describes data tables and the links between them (deliverable D-19). | [D-19 Database Design](deliverables-glossary.md) |
| **Triage (defects)** | Classifying and prioritizing the defects found, so the important ones are handled first. | [Deliverables Glossary](deliverables-glossary.md) |
| **Deterministic** | "Gives a fixed result" — automated checks by hard rules (yes/no), not subjective judgment. | [Core Concepts](../explanation/concepts.md) |

## Acceptance

| Term | Short definition |
| --- | --- |
| **Acceptance** | The final evaluation: does the feature meet requirements to be handed over (command `AC review`). |
| **ACCEPTED** | Passed — accepted for handover. |
| **REJECTED** | Failed — has defects/gaps that must be fixed and re-evaluated. |
| **DEFERRED** | Postponed — conditionally accepted, the missing part is handled later (by agreement). |
| **PENDING** | Undecided — waiting on information/results to make the call. |

## Related

- 💡 Understand the 4 foundational concepts in depth: [Core Concepts](../explanation/concepts.md).
- 📖 Look up deliverable codes: [Deliverables Glossary](deliverables-glossary.md).
- 📖 Look up skills: [Skills Catalog](skills-catalog.md).
