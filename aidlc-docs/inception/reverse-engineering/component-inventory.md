# Component Inventory

## Agents (5)
- `hbc-agent-ba` — Phase 1 Analysis coordinator 💼
- `hbc-agent-architect` — Phase 2 Design coordinator 🏗️
- `hbc-agent-qa` — Phase 2 Test Design coordinator 🧪
- `hbc-agent-dev` — Phase 3 Implementation coordinator 💻
- `hbc-agent-tester` — Phase 4 Testing coordinator 🔍

## Workflow Skills (15)

### Document-Creating Skills (10)
- `hbc-create-requirements` — D-02 (REQ-xxx) [REQ]
- `hbc-create-glossary` — D-03 [GLO]
- `hbc-create-business-flow-diagram` — D-06 [BFD]
- `hbc-create-er-diagram` — D-19 [ERD]
- `hbc-create-coding-standards` — D-12 [CS]
- `hbc-create-api-spec` — D-21 [API] (optional)
- `hbc-create-test-plan` — D-26 [TP]
- `hbc-create-test-spec` — D-27 [TS]
- `hbc-task-breakdown` — task-breakdown.md [TB]
- `hbc-implement` — code (TDD) [IM]

### Execution/Validation Skills (5)
- `hbc-test-execution` — test-execution-report.md [TE]
- `hbc-acceptance-check` — acceptance-report.md [AC]
- `hbc-phase-gate` — gate reports [PG]
- `hbc-check-implementation-readiness` — readiness-report.json [IR]
- `hbc-traceability` — matrix.md [TRI/TRU/TRR/TRA]

## Shared/Support Components (2)
- `hbc-shared` — lib/hbc_validation.py (non-invocable, no menu code)
- `hbc-setup` — config bootstrap

## Total Count
- **Total Skill Directories**: 22
- **Agents**: 5
- **Document-creating workflow skills**: 10
- **Execution/validation skills**: 5
- **Support/setup**: 2
- **Menu codes**: REQ, GLO, BFD, ERD, CS, API, TP, TS, IR, TB, IM, TE, AC, PG, TRI/TRU/TRR/TRA

## Relevance to hbc-sync (new feature)
Tất cả 10 document-creating skills + hbc-traceability là **delegation targets** của hbc-sync. Skill mới sẽ orchestrate gọi chúng ở mode `update` / `--headless` theo dependency order.
