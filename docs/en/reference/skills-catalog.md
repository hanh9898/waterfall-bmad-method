# HBC Skills Catalog

> 🌐 **English** · [Tiếng Việt](../../vi/reference/skills-catalog.md)
>
> 📖 **Reference** — the full list of every agent and skill. New here? Don't memorize this table — start with [Get Started with HBC](../tutorials/getting-started-hbc.md).

Invoke skills by **menu code** (e.g. `REQ`), **skill name** (`hbc-create-requirements`), or via an **agent**. Each workflow skill supports 3 modes — **Create / Update / Validate**; most support `--headless` / `-H` for non-interactive runs.

## Coordinator agents

| Code | Skill | Role |
| --- | --- | --- |
| `BA` | `hbc-agent-ba` | Phase 1 Analysis coordinator — guides requirements elicitation, glossary creation, business flow mapping. |
| `ARCH` | `hbc-agent-architect` | Phase 2 Design coordinator — database design, coding standards, API spec. |
| `QA` | `hbc-agent-qa` | Phase 2 Test Design coordinator — test plan and test cases. |
| `DEV` | `hbc-agent-dev` | Phase 3 Implementation coordinator — task breakdown and TDD. |
| `TST` | `hbc-agent-tester` | Phase 4 Testing coordinator — test execution, defect triage, acceptance decision. |

## Phase 1 — Analysis

| Code | Skill | Description | Deliverable | Required |
| --- | --- | --- | --- | :---: |
| `REQ` | `hbc-create-requirements` | Generate a requirements spec with REQ-xxx IDs and scope boundaries | D-02 | ✅ |
| `GLO` | `hbc-create-glossary` | Unified domain terminology from project docs & requirements | D-03 | — |
| `BFD` | `hbc-create-business-flow-diagram` | AS-IS/TO-BE business flow diagrams (Mermaid) from the PRD | D-06 | — |

## Phase 2 — Design (ARCH) + Test Design (QA)

| Code | Skill | Description | Deliverable | Required |
| --- | --- | --- | --- | :---: |
| `ERD` | `hbc-create-er-diagram` | DB design + ER Diagram (Mermaid) from requirements & architecture | D-19 | ✅ |
| `CS` | `hbc-create-coding-standards` | Per-project coding standards, adapted to the framework | D-12 | ✅ |
| `API` | `hbc-create-api-spec` | API spec — endpoints and request/response schemas | D-21 | — |
| `TP` | `hbc-create-test-plan` | Test plan — strategy, scope, schedule, entry/exit criteria, risk | D-26 | ✅ |
| `TS` | `hbc-create-test-spec` | Detailed test cases with TC-xxx IDs, steps & expected results | D-27 | ✅ |

## Phase 3 — Implementation

| Code | Skill | Description | Args | Required |
| --- | --- | --- | --- | :---: |
| `TB` | `hbc-task-breakdown` | Break design into small TDD tasks, dependency-ordered, with test-case assignment | `create\|update\|validate -H` | ✅ |
| `IM` | `hbc-implement` | Implement via the TDD cycle (RED-GREEN-REFACTOR) per task | `task TASK-xxx \| all \| coverage -H` | ✅ |

## Phase 4 — Testing

| Code | Skill | Description | Args | Required |
| --- | --- | --- | --- | :---: |
| `TE` | `hbc-test-execution` | Run test suites, collect results, classify failures, generate report | `all \| unit \| integration \| e2e \| report -H` | ✅ |
| `AC` | `hbc-acceptance-check` | Final acceptance evaluation — ACCEPTED/REJECTED/DEFERRED/PENDING | `review \| status -H` | ✅ |

## Cross-cutting — Phase Gate & Traceability

| Code | Skill | Description | Args |
| --- | --- | --- | --- |
| `PG` | `hbc-phase-gate` | Validate phase (1–4) completion against a checklist — deterministic + LLM, reports PASSED/FAILED | `1\|2\|3\|4 -H` |
| `TRI` | `hbc-traceability` (init) | Create the matrix from D-02 REQ IDs. Run once after requirements are final | `-H` |
| `TRU` | `hbc-traceability` (update) | Fill `design_ref`/`code_ref`/`test_ref`/`gate_status` columns as each phase completes | `-H` |
| `TRR` | `hbc-traceability` (report) | Coverage report — how many REQ IDs have complete traceability chains | `-H` |
| `TRA` | `hbc-traceability` (audit) | Gap identification and severity classification for missing links | `-H` |

## Suggested execution order

```
BA → REQ → (GLO, BFD) → TRI → PG 1
ARCH → ERD → CS → (API) ┐
QA   → TP  → TS         ┘ → TRU → PG 2
DEV  → TB  → IM         → TRU → PG 3
TST  → TE  → AC         → TRA → PG 4
```

> 💡 `bmad-help` always suggests the next step based on your project state — you don't need to memorize this order.

## Related

- 📖 Look up deliverable codes & content: [Deliverables Glossary](deliverables-glossary.md).
- 🗺️ Whole-workflow overview: [Workflow Map](../tutorials/workflow-map.md).
