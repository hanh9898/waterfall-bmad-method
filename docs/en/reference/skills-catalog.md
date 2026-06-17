# HBC Skills Catalog

> 🌐 **English** · [Tiếng Việt](../../vi/reference/skills-catalog.md)
>
> 📖 **Reference** — the full list of every agent and skill. New here? Don't memorize this table — start with [Get Started with HBC](../tutorials/getting-started-hbc.md).

Invoke skills by **menu code** (e.g. `REQ`), **skill name** (`hbc-create-requirements`), or via an **agent**. Each workflow skill supports 3 modes — **Create / Update / Validate**; most support `--headless` / `-H` for non-interactive runs.

HBC delivers **incrementally, per-feature** (incremental per-feature delivery): each feature passes through 4 gated phases + TDD, then ships independently. Before that, **Phase 0 is mandatory and runs first** — once for the whole project (or re-run to update directly). Each skill has a **scope**:

- **per-feature** — runs for an individual feature, output goes to `_bmad-output/features/<feature>/...`; in headless mode you must pass `feature=<slug>` (omitting it is blocked with `feature_required`).
- **shared** — project-wide shared deliverable, output goes to `_bmad-output/shared/...`; no `feature` arg.
- **dual** — has a shared baseline at `shared/...` and an optional per-feature override at `features/<feature>/...`; **the override wins if it exists** (path-existence precedence). Headless: `feature` is optional.

## Coordinator agents

| Code | Skill | Role |
| --- | --- | --- |
| `BA` | `hbc-agent-ba` | Phase 1 Analysis coordinator — guides requirements elicitation, glossary creation, business flow mapping. |
| `ARCH` | `hbc-agent-architect` | Phase 2 Design coordinator — database design, coding standards, API spec. |
| `QA` | `hbc-agent-qa` | Phase 2 Test Design coordinator — test plan and test cases. |
| `DEV` | `hbc-agent-dev` | Phase 3 Implementation coordinator — task breakdown and TDD. |
| `TST` | `hbc-agent-tester` | Phase 4 Testing coordinator — test execution, defect triage, acceptance decision. |

## Phase 0 — Project Init

**Mandatory and runs first**, once for the whole project, **before any feature** (or re-run to update the shared deliverables directly). No `feature` arg. `PI` is **brownfield-aware**: for an existing codebase it documents the code first (`bmad-document-project` + `project-context.md`) then derives the shared deliverables from it; for greenfield it derives them from the PRD/choices. **D-12 Coding Standards and D-03 Glossary are shared deliverables created in Phase 0.**

| Code | Skill | Description | Deliverable | Scope |
| --- | --- | --- | --- | --- |
| `PI` | `hbc-project-init` | Mandatory, runs first. Brownfield: document the code (`bmad-document-project` + `project-context.md`) then derive the shared deliverables; greenfield: derive from the PRD/choices. Creates the shared deliverables: D-12 Coding Standards, D-03 Glossary, and baseline D-19 ERD / D-21 API | D-12, D-03, baseline D-19/D-21 | shared |
| `MIG` | `hbc-migrate` | Takes a **HBC v1 (flat layout)** project up to v2 (per-feature + shared): moves files, re-prefixes REQ/TC, rebuilds the 8-column matrix. `MIG plan` = dry-run preview → `MIG apply feature=<slug>`. See [Migrate from v1 to v2](../how-to/migrate-from-v1.md) | v2 layout + 8-column matrix | v1→v2 migration, run once |

Output: `_bmad-output/shared/{coding-standards, glossary, erd, api}/`.

## Phase 1 — Analysis

| Code | Skill | Description | Deliverable | Scope | Required |
| --- | --- | --- | --- | --- | :---: |
| `REQ` | `hbc-create-requirements` | Generate a requirements spec with REQ-<FEAT>-NNN IDs and scope boundaries | D-02 | per-feature | ✅ |
| `GLO` | `hbc-create-glossary` | Maintains the **shared D-03** (originated in Phase 0) — unified domain terminology from project docs & requirements | D-03 | shared | — |
| `BFD` | `hbc-create-business-flow-diagram` | AS-IS/TO-BE business flow diagrams (Mermaid) from the PRD | D-06 | per-feature | ✅ |

Per-feature output: `_bmad-output/features/<feature>/planning-artifacts/`. Shared output: `_bmad-output/shared/glossary/`.

## Phase 2 — Design (ARCH) + Test Design (QA)

| Code | Skill | Description | Deliverable | Scope | Required |
| --- | --- | --- | --- | --- | :---: |
| `ERD` | `hbc-create-er-diagram` | DB design + ER Diagram (Mermaid) from requirements & architecture | D-19 | dual | ✅ |
| `CS` | `hbc-create-coding-standards` | Maintains the **shared D-12** (originated in Phase 0) — per-project coding standards, adapted to the framework | D-12 | shared | ✅ |
| `API` | `hbc-create-api-spec` | API spec — endpoints and request/response schemas | D-21 | dual | — |
| `TP` | `hbc-create-test-plan` | Test plan — strategy, scope, schedule, entry/exit criteria, risk | D-26 | per-feature | ✅ |
| `TS` | `hbc-create-test-spec` | Detailed test cases with TC-xxx IDs, steps & expected results | D-27 | per-feature | ✅ |
| `IR` | `hbc-check-implementation-readiness` | Readiness seam gate — reconcile D-02 ↔ D-21/D-26/D-27 + traceability matrix before closing Phase 2 | readiness-report | per-feature | ✅ |

Dual output (ERD/API): baseline `shared/erd|api/` + optional override `features/<feature>/planning-artifacts/`. Shared output (CS): `shared/coding-standards/`. Per-feature output (TP/TS/IR): `features/<feature>/planning-artifacts/`.

## Phase 3 — Implementation

Soft TDD: `IM` runs RED→GREEN→REFACTOR; **RED evidence** (a failing test before writing code) must be recorded — the Phase 3 gate checks for RED evidence.

| Code | Skill | Description | Args | Scope | Required |
| --- | --- | --- | --- | --- | :---: |
| `TB` | `hbc-task-breakdown` | Break design into small TDD tasks, dependency-ordered, with test-case assignment | `create\|update\|validate -H` | per-feature | ✅ |
| `IM` | `hbc-implement` | Implement via the TDD cycle (RED-GREEN-REFACTOR) per task | `task TASK-xxx \| all \| coverage -H` | per-feature | ✅ |

Output: `_bmad-output/features/<feature>/implementation-artifacts/`.

## Phase 4 — Testing

| Code | Skill | Description | Args | Scope | Required |
| --- | --- | --- | --- | --- | :---: |
| `TE` | `hbc-test-execution` | Run test suites, collect results, classify failures, generate report | `all \| unit \| integration \| e2e \| report -H` | per-feature | ✅ |
| `AC` | `hbc-acceptance-check` | Final acceptance evaluation — ship one feature independently; ACCEPTED/REJECTED/DEFERRED/PENDING | `review \| status -H` | per-feature | ✅ |

Output: `_bmad-output/features/<feature>/implementation-artifacts/`.

## Cross-cutting — Phase Gate & Traceability

| Code | Skill | Description | Args | Scope |
| --- | --- | --- | --- | --- |
| `PG` | `hbc-phase-gate` | Validate phase (1–4) completion against a checklist — deterministic + LLM, reports PASSED/FAILED; carries `feature=` | `1\|2\|3\|4 -H` | per-feature |
| `TRI` | `hbc-traceability` (init) | Create the 8-column matrix from D-02 REQ-<FEAT>-NNN IDs. Run once after requirements are final | `-H` | per-feature |
| `TRU` | `hbc-traceability` (update) | Fill `design_ref`/`code_ref`/`test_ref`/`gate_status` columns as each phase completes | `-H` | per-feature |
| `TRR` | `hbc-traceability` (report) | Coverage report — how many REQ IDs have complete traceability chains; can roll up across features | `-H` | per-feature + rollup |
| `TRA` | `hbc-traceability` (audit) | Gap identification and severity classification for missing links | `-H` | per-feature |
| `SYNC` | `hbc-traceability` (impact) | **Cascade Sync** — impact analysis when a source document changes, proposes cascading updates to downstream docs/tests/code (read-only) | `<change> \| --since <ref> -H` | per-feature |

8-column traceability matrix: `feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp`. Coverage counts `design_ref`/`code_ref`/`test_ref`. Output: `_bmad-output/features/<feature>/traceability/`; gates: `features/<feature>/gates/`.

## Suggested execution order

```
PI                                      (once, first — shared D-12/D-03 + baseline D-19/D-21)
BA → REQ → GLO → BFD → TRI → PG 1   (GLO shared from Phase 0; BFD/D-06 required for Phase 1)
ARCH → ERD → CS → (API) ┐
QA   → TP  → TS         ┘ → IR → TRU → PG 2
DEV  → TB  → IM         → TRU → PG 3
TST  → TE  → AC         → TRA → PG 4
```

> 💡 `bmad-help` always suggests the next step based on your project state — you don't need to memorize this order.

## Related

- 📖 Look up deliverable codes & content: [Deliverables Glossary](deliverables-glossary.md).
- 🗺️ Whole-workflow overview: [Workflow Map](../tutorials/workflow-map.md).
