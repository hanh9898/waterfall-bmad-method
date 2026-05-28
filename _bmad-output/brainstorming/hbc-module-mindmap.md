# HBLab Custom Module — 19-Skill Scope (Finalized 2026-05-28)

## Scope Decision

Original research (2026-05-20) envisioned 30 D-xx documents across 3 modules. After brainstorming (Assumption Reversal) and Party Mode roundtable, scope narrowed to **19 skills** (5 agents + 14 workflows) covering **8 D-xx documents** + 6 process outputs across 4 phases.

**Out-of-scope D-xx (deferred to future expansion):** D-01, D-04, D-05, D-07, D-08, D-09, D-10, D-11, D-13, D-14, D-15, D-16, D-17, D-18, D-20, D-21 (optional, in plan), D-22, D-23, D-24, D-25, D-28, D-29, D-31, D-00.

**Removed:** `hbc-create-invest-epics-and-stories` — not part of waterfall lifecycle.

**Decided:** `hbc-create-er-diagram` = D-19 skill (no rename to hbc-create-db-design).

## Architecture

```mermaid
mindmap
  root((HBC Module<br/>19 Skills))
    **Phase 1: Analysis**
      💼 hbc-agent-ba<br/>Coordinator
        D-02 要件定義書<br/>hbc-create-requirements ✅
        D-03 用語集<br/>hbc-create-glossary ✅
        D-06 Business Flow<br/>hbc-create-business-flow-diagram ✅
    **Phase 2: Design**
      🏗️ hbc-agent-architect<br/>Coordinator
        D-19 データベース設計書<br/>hbc-create-er-diagram ✅
        D-12 コーディング規約<br/>hbc-create-coding-standards
        D-21 API仕様書<br/>hbc-create-api-spec (optional)
      🧪 hbc-agent-qa<br/>Coordinator
        D-26 テスト計画書<br/>hbc-create-test-plan
        D-27 テスト仕様書<br/>hbc-create-test-spec
    **Phase 3: Implementation**
      💻 hbc-agent-dev<br/>Coordinator
        hbc-task-breakdown<br/>Task list from design
        hbc-implement<br/>TDD RED→GREEN→REFACTOR
    **Phase 4: Testing**
      🔍 hbc-agent-tester<br/>Coordinator
        hbc-test-execution<br/>Run & report
        hbc-acceptance-check<br/>Final decision
    **Cross-cutting**
      hbc-phase-gate ✅<br/>Gate engine (1→4)
      hbc-traceability ✅<br/>Living matrix
```

## Dependency Flow

```mermaid
flowchart TD
    subgraph phase1 ["Phase 1: Analysis"]
        REQ[D-02 Requirements] --> GLO[D-03 Glossary]
        REQ --> BF[D-06 Business Flow]
    end

    subgraph phase2 ["Phase 2: Design"]
        REQ --> ER[D-19 ER Diagram]
        REQ --> TP[D-26 Test Plan]
        ER --> CS[D-12 Coding Standards]
        CS --> API[D-21 API Spec]
        TP --> TS[D-27 Test Spec]
    end

    subgraph phase3 ["Phase 3: Implementation"]
        ER --> TB[Task Breakdown]
        TS --> TB
        CS --> TB
        TB --> IM[Implement TDD]
    end

    subgraph phase4 ["Phase 4: Testing"]
        TS --> TE[Test Execution]
        IM --> TE
        TE --> AC[Acceptance Check]
    end

    subgraph crosscut ["Cross-cutting"]
        PG{{Phase Gate}}
        TR{{Traceability}}
    end

    phase1 --> PG
    phase2 --> PG
    phase3 --> PG
    phase4 --> PG
    REQ --> TR
    ER --> TR
    IM --> TR
    TE --> TR

    style REQ fill:#90EE90,stroke:#333
    style GLO fill:#90EE90,stroke:#333
    style BF fill:#90EE90,stroke:#333
    style ER fill:#90EE90,stroke:#333
    style PG fill:#90EE90,stroke:#333
    style TR fill:#90EE90,stroke:#333
    style API fill:#FFFFE0,stroke:#333
```

**Legend:**
- 🟢 Xanh = Built (Grade A)
- 🟡 Vàng nhạt = Optional
- Trắng = Chưa build

## Build Status

| # | Skill | Type | Phase | D-xx | Status |
|---|-------|------|-------|------|--------|
| 1 | hbc-phase-gate | workflow | cross-cutting | — | ✅ Built |
| 2 | hbc-traceability | workflow | cross-cutting | — | ✅ Built, Grade A |
| 3 | hbc-create-requirements | workflow | 1-Analysis | D-02 | ✅ Built, Grade A |
| 4 | hbc-create-glossary | workflow | 1-Analysis | D-03 | ✅ Built, Grade A |
| 5 | hbc-create-business-flow-diagram | workflow | 1-Analysis | D-06 | ✅ Built |
| 6 | hbc-agent-ba | agent | 1-Analysis | — | ✅ Built |
| 7 | hbc-create-er-diagram | workflow | 2-Design | D-19 | ✅ Built, Grade A |
| 8 | hbc-create-coding-standards | workflow | 2-Design | D-12 | ⬜ Not built |
| 9 | hbc-create-api-spec | workflow | 2-Design | D-21 | ⬜ Not built (optional) |
| 10 | hbc-create-test-plan | workflow | 2-Design | D-26 | ⬜ Not built |
| 11 | hbc-create-test-spec | workflow | 2-Design | D-27 | ⬜ Not built |
| 12 | hbc-agent-architect | agent | 2-Design | — | ⬜ Not built |
| 13 | hbc-agent-qa | agent | 2-Design | — | ⬜ Not built |
| 14 | hbc-task-breakdown | workflow | 3-Impl | — | ⬜ Not built |
| 15 | hbc-implement | workflow | 3-Impl | — | ⬜ Not built |
| 16 | hbc-agent-dev | agent | 3-Impl | — | ⬜ Not built |
| 17 | hbc-test-execution | workflow | 4-Test | — | ⬜ Not built |
| 18 | hbc-acceptance-check | workflow | 4-Test | — | ⬜ Not built |
| 19 | hbc-agent-tester | agent | 4-Test | — | ⬜ Not built |

**Progress: 7/19 built (37%)**

## Thống kê

| Metric | Count |
|--------|-------|
| **Agents** | 5 (1 per phase + tester) |
| **Workflows** | 14 (12 phase + 2 cross-cutting) |
| **D-xx Documents** | 8 (7 mandatory + 1 optional) |
| **Process Outputs** | 6 (task-breakdown, code, test-report, acceptance-report, gate-reports, matrix) |
| **Built** | 7 skills |
| **Remaining** | 12 skills |
