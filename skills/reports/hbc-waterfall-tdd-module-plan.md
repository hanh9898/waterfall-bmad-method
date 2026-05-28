---
title: 'HBC Waterfall-TDD Module Plan'
status: 'complete'
module_name: 'HBLab Waterfall-TDD Lifecycle'
module_code: 'hbc'
module_description: 'Framework-agnostic waterfall + TDD development lifecycle with D-xx document generation, phase gates, and traceability'
architecture: 'hybrid — agents coordinate workflows'
standalone: false
expands_module: 'hbc (HBLAB BMad Custom)'
skills_planned: [hbc-agent-ba, hbc-agent-architect, hbc-agent-qa, hbc-agent-dev, hbc-agent-tester, hbc-create-requirements, hbc-create-glossary, hbc-create-business-flow-diagram, hbc-create-er-diagram, hbc-create-coding-standards, hbc-create-test-plan, hbc-create-test-spec, hbc-create-api-spec, hbc-task-breakdown, hbc-implement, hbc-test-execution, hbc-acceptance-check, hbc-phase-gate, hbc-traceability]
config_variables: [acceptance_owner, coverage_threshold, e2e_framework, gate_mode, output_language, project_context_path]
created: '2026-05-26'
updated: '2026-05-28'
---

# HBC Waterfall-TDD Module Plan

## Vision

Module cung cấp quy trình phát triển phần mềm hoàn chỉnh theo waterfall kết hợp TDD cho team HBLab. Mỗi D-xx document template (chuẩn Nhật) được phục vụ bởi 1 skill riêng biệt — user gọi skill, skill tạo document. 4 phase tuần tự với gate cứng giữa mỗi phase đảm bảo chất lượng. Framework-agnostic ở base, customize cho từng tech stack (Odoo, Django, Next.js...) qua `project-context.md` + `customize.toml`.

**Đối tượng sử dụng:** Dev team HBLab, BA, QA, Tech Lead — bất kỳ ai tham gia lifecycle dự án.

**Giá trị cốt lõi:** Đảm bảo không skip bước, mọi requirement được trace từ phân tích → thiết kế → code → test → acceptance.

## Architecture

**Quyết định: Hybrid — Agents coordinate Workflows.**

4 agents đóng vai trò expert coordinators, mỗi agent gom các workflows liên quan qua menu. User gọi 1 agent thay vì nhớ 14 skill names. Workflows vẫn là nơi thực hiện công việc — agents chỉ là layer điều phối.

Lý do chọn hybrid:
1. **UX tốt hơn** — user nhớ 4 agents thay vì 14 skills. Agent show menu, suggest next step
2. **Context carry** — agent giữ context xuyên suốt session, không mất khi chuyển workflow
3. **Party Mode** — agents tham gia roundtable discussion cross-functional
4. **Vẫn flexible** — user CÓ THỂ gọi trực tiếp workflow skill khi cần (bypass agent)

### 4 Agents + 14 Workflows + 2 Cross-cutting

```
┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  💼 hbc-agent-ba    │  │ 🏗️ hbc-agent-architect│  │ 💻 hbc-agent-dev│  │ 🧪 hbc-agent-qa  │
│  Business Analyst   │  │ System Architect      │  │ Developer       │  │ QA Engineer      │
│                     │  │                       │  │                 │  │                  │
│  Menu:              │  │  Menu:                │  │  Menu:          │  │  Menu:           │
│  [REQ] Requirements │  │  [DB] DB Design       │  │  [TB] Task Break│  │  [TP] Test Plan  │
│  [GLO] Glossary     │  │  [CS] Coding Standards│  │  [IM] Implement │  │  [TS] Test Spec  │
│  [BF] Business Flow │  │  [API] API Spec       │  │                 │  │  [TE] Test Exec  │
│                     │  │                       │  │                 │  │  [AC] Acceptance │
│  + [PG] Phase Gate  │  │  + [PG] Phase Gate    │  │  + [PG] Phase G.│  │  + [PG] Phase G. │
│  + [TR] Traceability│  │  + [TR] Traceability  │  │  + [TR] Trace.  │  │  + [TR] Trace.   │
└─────────────────────┘  └──────────────────────┘  └─────────────────┘  └──────────────────┘
         │                         │                        │                      │
    Phase 1: Analysis        Phase 2: Design          Phase 3: Impl         Phase 4: Test
         │                         │                        │                      │
         ▼                         ▼                        ▼                      ▼
    [GATE 1] ──────────────→ [GATE 2] ─────────────→ [GATE 3] ───────────→ [GATE 4/ACCEPT]
         │                         │                        │                      │
         └──── hbc-phase-gate (cross-cutting engine) ───────┘                      │
         └──── hbc-traceability (living matrix, updated after each phase) ──────────┘
```

### Agent → Workflow Mapping

| Agent | Phase | Workflows (menu items) |
|-------|-------|----------------------|
| 💼 `hbc-agent-ba` | 1-Analysis | `hbc-create-requirements` [REQ], `hbc-create-glossary` [GLO], `hbc-create-business-flow-diagram` [BF] |
| 🏗️ `hbc-agent-architect` | 2-Design | `hbc-create-er-diagram` [DB], `hbc-create-coding-standards` [CS], `hbc-create-api-spec` [API] |
| 🧪 `hbc-agent-qa` | 2-Design (Test) | `hbc-create-test-plan` [TP], `hbc-create-test-spec` [TS] |
| 💻 `hbc-agent-dev` | 3-Impl | `hbc-task-breakdown` [TB], `hbc-implement` [IM] |
| 🔍 `hbc-agent-tester` | 4-Testing | `hbc-test-execution` [TE], `hbc-acceptance-check` [AC] |

Mọi agent đều có thêm: `[PG]` Phase Gate, `[TR]` Traceability — cross-cutting skills accessible từ bất kỳ agent nào.

### Tổng kết: 19 skills

| Loại | Số lượng | Chi tiết |
|------|----------|----------|
| Agents | 5 | 1 agent/phase (ba, architect, qa, dev, tester) |
| Workflows | 14 | 12 phase workflows + 2 cross-cutting (phase-gate, traceability) |
| **Tổng** | **19** | |

### Gate Dependency Chain

Mỗi phase skill đầu tiên (hoặc bất kỳ skill nào trong phase) kiểm tra gate artifact của phase trước:
- Phase 2 skills → require `_hbc_output/gates/phase-1-gate.md` status=PASSED
- Phase 3 skills → require `_hbc_output/gates/phase-2-gate.md` status=PASSED
- Phase 4 skills → require `_hbc_output/gates/phase-3-gate.md` status=PASSED

Gate checklist content sống trong `assets/` của skill cuối mỗi phase. `hbc-phase-gate` chỉ là validation engine — nhận checklist, evaluate, xuất gate report.

### Framework Adaptation (không hardcode)

| Layer | Chứa gì | Ví dụ |
|-------|---------|-------|
| **Skill base** | Logic chung, D-xx template | "Hỏi entities, relations, constraints" |
| **customize.toml** | Workflow config, roles, thresholds | `acceptance_owner = "PM"`, `coverage_min = 80` |
| **project-context.md** | Tech stack, framework conventions | Odoo: `_inherit`, `Many2one`, `ir.model.access.csv` |

Skill đọc `project-context.md` qua `persistent_facts` → LLM tự adapt output theo framework. Cùng `hbc-create-er-diagram` nhưng output khác nhau: Odoo models vs Django ORM vs Prisma schema.

### Traceability Matrix (Cross-cutting)

7 cột MVP — living document cập nhật incremental:

```
| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
```

- Khởi tạo sau Phase 1 (populate req_id)
- Update sau Phase 2 (populate design_ref)
- Update sau Phase 3 (populate code_ref)
- Final sau Phase 4 (populate test_ref, gate_status)

`hbc-traceability` là standalone skill, invoked mid-workflow từ các phase skills.

### Memory Architecture

**Pattern: Personal memory only** — mỗi agent có memory folder riêng, không shared memory.

Lý do: 4 agents phục vụ 4 phase khác nhau với domain khác nhau (BA ≠ QA ≠ Dev). Overlap ít — shared memory không cần thiết. Cross-phase context flow qua output artifacts (`_hbc_output/`), không qua memory.

```
_bmad/memory/
├── hbc-agent-ba/           # BA nhớ: stakeholder preferences, domain terms, requirement patterns
├── hbc-agent-architect/    # Architect nhớ: tech decisions, design rationale, framework specifics
├── hbc-agent-dev/          # Dev nhớ: coding patterns, TDD preferences, implementation notes
└── hbc-agent-qa/           # QA nhớ: test strategies, defect patterns, coverage preferences
```

Mỗi agent đọc memory on activation, write sau mỗi session. Lightweight — không cần daily/curated pattern cho module này.

### Memory Contract

| File | Agent | Read | Write | Nội dung |
|------|-------|------|-------|----------|
| `preferences.md` | Mỗi agent | On activation | After meaningful session | User preferences cho phase đó (e.g., BA: "user thích Given/When/Then format") |
| `learned.md` | Mỗi agent | On activation | When learning something new | Domain knowledge tích lũy (e.g., Dev: "project dùng Odoo 11, prefer @api.model") |

### Cross-Agent Patterns

**User là router chính** — user gọi agent phù hợp cho phase hiện tại. Agents không gọi nhau trực tiếp.

**Cross-agent flow qua artifacts:**
```
hbc-agent-ba tạo D-02 → file nằm trong _hbc_output/plan/
  → hbc-agent-architect đọc D-02 khi thiết kế D-19
    → hbc-agent-dev đọc D-19 + D-27 khi implement
      → hbc-agent-qa đọc D-02 + D-27 khi test + acceptance
```

**Party Mode:** 4 agents có thể join roundtable discussion — ví dụ khi cần review cross-functional (BA + QA review requirements coverage, Architect + Dev review design feasibility).

**Cross-skill invocation trong workflows:**
- Workflow skills invoke `hbc-phase-gate` ở step cuối để validate gate
- Workflow skills invoke `hbc-traceability` để update matrix sau khi tạo document
- Agent persona carries through khi invoke workflow — context không mất

## Skills

### Phase 1 Agent: hbc-agent-ba

**Type:** agent

**Persona:** 💼 Business Analyst chuyên nghiệp. Tỉ mỉ, hỏi kỹ trước khi viết. Nói ngắn gọn, tập trung vào requirements clarity. Luôn challenge assumptions — "Tại sao user cần feature này?" Communication style: structured, dùng bullet points và tables.

**Core Outcome:** User hoàn thành Phase 1 (Analysis) với đầy đủ D-02 Requirements, D-03 Glossary, D-06 Business Flow — tất cả consistent và cross-referenced.

**The Non-Negotiable:** Mọi requirement phải có ID duy nhất (`REQ-xxx`) và trace được từ business flow. Không để requirement mơ hồ ("hệ thống cần nhanh") lọt qua.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| [REQ] Create Requirements | D-02 Requirements Spec hoàn chỉnh | User descriptions, existing docs, interviews | `_hbc_output/plan/D-02-*.md` via `hbc-create-requirements` |
| [GLO] Create Glossary | D-03 Glossary với domain terms thống nhất | D-02 output, user input | `_hbc_output/plan/D-03-*.md` via `hbc-create-glossary` |
| [BF] Business Flow Diagram | D-06 Business Flow Mermaid diagrams | D-02 output, user input | `_hbc_output/plan/D-06-*.md` via `hbc-create-business-flow-diagram` |
| [PG] Phase Gate | Validate Phase 1 completeness | Phase 1 artifacts | `_hbc_output/gates/phase-1-gate.md` via `hbc-phase-gate` |
| [TR] Traceability | Update matrix with req_id population | Phase 1 artifacts | `_hbc_output/traceability/matrix.md` via `hbc-traceability` |

**Memory:** `_bmad/memory/hbc-agent-ba/` — `preferences.md` (user preferences: requirement format, detail level, language), `learned.md` (domain terms, stakeholder patterns, recurring clarification points).

**Init Responsibility:** On first run, introduce Phase 1 scope, show menu, check if any Phase 1 artifacts already exist. If existing: offer to review/update or start fresh.

**Activation Modes:** Interactive only. BA work requires conversation to elicit requirements.

**Tool Dependencies:** None beyond Claude Code.

**Design Notes:**
- Agent shows menu on activation và sau mỗi workflow complete, suggest next step.
- Recommended flow: REQ → GLO → BF → PG → TR. Nhưng user có thể chọn bất kỳ order.
- Agent giữ context xuyên suốt session — khi user chuyển từ REQ sang GLO, BA nhớ domain terms đã identify.
- Menu code [PG] và [TR] luôn available nhưng suggest sau khi hoàn thành ít nhất 1 workflow.

**Relationships:** Precedes `hbc-agent-architect` và `hbc-agent-qa`. Phase 1 gate must PASS before Phase 2 skills start.

---

### Phase 2 Agent: hbc-agent-architect

**Type:** agent

**Persona:** 🏗️ System Architect pragmatic. Tư duy systems-level, luôn consider trade-offs. Hỏi "Nó scale thế nào?" và "Edge case gì?". Communication style: technical nhưng accessible, dùng diagrams khi cần.

**Core Outcome:** User hoàn thành Phase 2 design artifacts — DB design, coding standards, API spec (optional) — all traceable back to Phase 1 requirements.

**The Non-Negotiable:** Mọi design decision phải reference requirement ID. Không design feature mà Phase 1 không define.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| [DB] DB Design | D-19 Database Design (ER + table defs) | D-02, D-06, project-context.md | `_hbc_output/design/D-19-*.md` via `hbc-create-er-diagram` |
| [CS] Coding Standards | D-12 Coding Standards per-project | project-context.md, team preferences | `_hbc_output/design/D-12-*.md` via `hbc-create-coding-standards` |
| [API] API Spec | D-21 API Specification (optional) | D-02, D-19, project-context.md | `_hbc_output/design/D-21-*.md` via `hbc-create-api-spec` |
| [PG] Phase Gate | Validate Phase 2 completeness | Phase 2 artifacts + Phase 1 gate | `_hbc_output/gates/phase-2-gate.md` via `hbc-phase-gate` |
| [TR] Traceability | Update matrix with design_ref | Phase 2 artifacts | `_hbc_output/traceability/matrix.md` via `hbc-traceability` |

**Memory:** `_bmad/memory/hbc-agent-architect/` — `preferences.md` (naming conventions, diagram preferences), `learned.md` (tech decisions, framework-specific patterns, design rationale).

**Init Responsibility:** Check Phase 1 gate status. If not PASSED: warn user and suggest returning to `hbc-agent-ba`. If PASSED: show menu, note which Phase 1 artifacts are available as input.

**Activation Modes:** Interactive only.

**Tool Dependencies:** None.

**Design Notes:**
- Gate check on activation — soft block if Phase 1 gate not passed (warn, user can override with `gate_mode = lenient`).
- `hbc-create-er-diagram` is the D-19 skill (already built, Grade A). No rename or wrapper needed.
- [API] is optional — some projects (Odoo internal modules) don't expose APIs. Agent should ask, not assume.
- Reads `project-context.md` để adapt output: Odoo models vs Django ORM vs Prisma schema.

**Relationships:** Requires Phase 1 gate PASSED. Precedes `hbc-agent-dev`. Parallel with `hbc-agent-qa` (Phase 2 design + test design can happen concurrently).

---

### Phase 2 Agent: hbc-agent-qa

**Type:** agent

**Persona:** 🧪 QA Engineer methodical. Thinks in test scenarios, edge cases, and coverage gaps. Asks "What could go wrong?" and "How do we verify this?". Communication style: precise, checklist-oriented.

**Core Outcome:** Test Plan (D-26) và Test Specification (D-27) hoàn chỉnh — covering all Phase 1 requirements, ready for Phase 3 TDD implementation.

**The Non-Negotiable:** Mỗi requirement ID phải có ít nhất 1 test case. Zero-coverage requirements = gate fail.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| [TP] Test Plan | D-26 Test Plan (strategy, scope, schedule) | D-02, D-06, project-context.md | `_hbc_output/design/D-26-*.md` via `hbc-create-test-plan` |
| [TS] Test Spec | D-27 Test Specification (detailed cases) | D-26, D-02, D-19 | `_hbc_output/design/D-27-*.md` via `hbc-create-test-spec` |
| [PG] Phase Gate | Validate test design completeness | D-26, D-27, coverage vs D-02 | `_hbc_output/gates/phase-2-gate.md` via `hbc-phase-gate` |
| [TR] Traceability | Update matrix with test_ref | Phase 2 test artifacts | `_hbc_output/traceability/matrix.md` via `hbc-traceability` |

**Memory:** `_bmad/memory/hbc-agent-qa/` — `preferences.md` (test format preferences, severity definitions), `learned.md` (test strategies, common edge case patterns, defect patterns).

**Init Responsibility:** Check Phase 1 gate status. Show menu. If D-19 exists, note it as additional input for test cases (test data design).

**Activation Modes:** Interactive only.

**Tool Dependencies:** None.

**Design Notes:**
- QA designs tests BEFORE code (waterfall + TDD alignment). D-27 test specs become input for `hbc-implement` TDD cycle.
- D-26 (plan) nên làm trước D-27 (spec). Agent suggest order nhưng không enforce.
- Phase 2 gate tổng hợp: Architect's gate + QA's gate = Phase 2 PASSED. Cả design VÀ test design phải complete.
- QA agent đọc D-02 requirements để verify coverage — mỗi REQ-xxx cần ít nhất 1 test case ID.

**Relationships:** Requires Phase 1 gate PASSED. Parallel with `hbc-agent-architect`. Both contribute to Phase 2 gate.

---

### Phase 3 Agent: hbc-agent-dev

**Type:** agent

**Persona:** 💻 Developer pragmatic. Code-first mindset nhưng respects process. Prefers concrete examples over abstract discussion. Communication style: direct, code snippets khi cần, minimal ceremony.

**Core Outcome:** Requirements → working code via TDD. Task breakdown complete, code implemented with tests passing, coverage meets threshold.

**The Non-Negotiable:** TDD workflow — RED → GREEN → REFACTOR. Không commit code mà test chưa pass. Không skip test writing.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| [TB] Task Breakdown | Granular implementation tasks from design | D-19, D-27, D-12, D-21 | `_hbc_output/impl/task-breakdown.md` via `hbc-task-breakdown` |
| [IM] Implement | Code + tests via TDD cycle | Task breakdown, D-27, D-12, project-context.md | Code files + test files via `hbc-implement` |
| [PG] Phase Gate | Validate implementation completeness | Code, tests, coverage report | `_hbc_output/gates/phase-3-gate.md` via `hbc-phase-gate` |
| [TR] Traceability | Update matrix with code_ref | Implementation artifacts | `_hbc_output/traceability/matrix.md` via `hbc-traceability` |

**Memory:** `_bmad/memory/hbc-agent-dev/` — `preferences.md` (TDD preferences, code style beyond D-12), `learned.md` (coding patterns, framework gotchas, implementation notes).

**Init Responsibility:** Check Phase 2 gate status. Load D-12 coding standards. Show menu. Suggest TB → IM → PG → TR flow.

**Activation Modes:** Interactive (recommended for TDD pairing) and headless (for batch task implementation).

**Tool Dependencies:** None from module perspective. User's project needs test runner (pytest, jest, etc.) pre-installed.

**Design Notes:**
- TB trước IM — task breakdown creates the implementation roadmap.
- IM runs TDD per task: write test (from D-27 spec) → run (RED) → implement → run (GREEN) → refactor → verify coverage.
- E2E boundary: IM writes Playwright/E2E test scripts. Execution belongs to Phase 4 (`hbc-test-execution`).
- `coverage_threshold` config variable checked in Phase 3 gate.

**Relationships:** Requires Phase 2 gate PASSED. Precedes `hbc-agent-tester`.

---

### Phase 4 Agent: hbc-agent-tester

**Type:** agent

**Persona:** 🔍 Tester thorough. Executes methodically, documents every finding. Skeptical — assumes code has bugs until proven otherwise. Communication style: report-oriented, evidence-based.

**Core Outcome:** All tests executed, results documented, acceptance decision made (ACCEPTED/REJECTED/DEFERRED/PENDING).

**The Non-Negotiable:** Acceptance decision phải có evidence (test results, coverage report). Không accept chỉ vì "trông ổn".

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| [TE] Test Execution | Execute tests, document results | D-27, code, test scripts | `_hbc_output/test/test-execution-report.md` via `hbc-test-execution` |
| [AC] Acceptance Check | Final acceptance decision | All artifacts, test results | `_hbc_output/test/acceptance-report.md` via `hbc-acceptance-check` |
| [PG] Phase Gate | Validate Phase 4 / final gate | Acceptance report, test results | `_hbc_output/gates/phase-4-gate.md` via `hbc-phase-gate` |
| [TR] Traceability | Final matrix update with test results + gate status | All Phase 4 artifacts | `_hbc_output/traceability/matrix.md` via `hbc-traceability` |

**Memory:** `_bmad/memory/hbc-agent-tester/` — `preferences.md` (reporting format, severity thresholds), `learned.md` (defect patterns, regression areas, test environment quirks).

**Init Responsibility:** Check Phase 3 gate status. Load test execution report template. Show menu. Verify test environment is ready.

**Activation Modes:** Interactive (for exploratory testing + acceptance discussion) and headless (for automated test execution report).

**Tool Dependencies:** None from module perspective. User's test runner must be available.

**Design Notes:**
- Tester ≠ QA. QA designs tests (Phase 2). Tester executes and judges results (Phase 4).
- Defect management: failed_test → return to Dev (fix in place), no_coverage → return to Phase 2 (QA add tests), wrong_requirement → escalate to PO/BA.
- Acceptance decision by `acceptance_owner` (from config). Tester presents evidence, owner decides.
- Phase 4 gate = final gate. PASSED = project deliverable complete.

**Relationships:** Requires Phase 3 gate PASSED. Terminal phase — no successor.

---

### Workflow: hbc-create-requirements

**Type:** workflow

**Purpose:** Generate D-02 要件定義書 (Requirements Specification) — structured requirements with unique IDs, scope boundaries, user roles, functional and non-functional requirements.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | New D-02 from scratch | User descriptions, interviews, existing docs | `_hbc_output/plan/D-02-{project_name}-requirements.md` |
| Update | Revise existing D-02 | Existing D-02 + change requests | Updated D-02 with revision history |
| Validate | Check D-02 completeness and quality | Existing D-02 | Validation report (pass/fail per section) |

**Template:** `{project-root}/templates/D-02_要件定義書_template.md`

**Workflow stages:**
1. Prerequisites + resume detection (check workspace for existing D-02)
2. Discovery — elicit from user: project background, scope in/out, users & roles, functional requirements (each gets REQ-xxx ID), non-functional requirements
3. Generation — populate D-02 template, ensure every FR has unique ID, cross-reference with roles
4. Validation — completeness check (all sections filled), quality check (no vague requirements, no duplicates, IDs sequential)
5. Save + downstream handoff (suggest: GLO → BF → PG)

**Design Notes:**
- REQ-xxx IDs are the foundation of traceability. Format: `REQ-001`, `REQ-002`, etc.
- Scope in/out is critical — explicitly list what's NOT in scope to prevent scope creep.
- Non-functional requirements use severity table (性能, セキュリティ, 可用性...).
- Follows established HBC 5-stage workflow pattern with resume state, decision-log, parallel-lens menu.

**Relationships:** First skill in Phase 1. Feeds into all subsequent skills. `preceded-by: none`, `followed-by: hbc-create-glossary`.

---

### Workflow: hbc-create-glossary

**Type:** workflow

**Purpose:** Generate D-03 用語集 (Glossary) — unified domain terminology extracted from D-02 and user input.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | New D-03 glossary | D-02, user domain knowledge | `_hbc_output/plan/D-03-{project_name}-glossary.md` |
| Update | Add/revise terms | Existing D-03 + new terms | Updated D-03 with revision history |
| Validate | Check completeness vs D-02 terms | D-03 + D-02 | Validation report |

**Template:** `{project-root}/templates/D-03_用語集_template.md`

**Workflow stages:**
1. Prerequisites + load D-02 as source
2. Discovery — extract domain terms from D-02, ask user for additional terms, resolve ambiguities
3. Generation — populate glossary table (用語, 定義), sort alphabetically or by category
4. Validation — all D-02 domain terms present, no contradictory definitions, no duplicates
5. Save + handoff

**Design Notes:**
- Lighter workflow — D-03 template is a single table. 3-4 stages sufficient.
- Auto-extract candidates from D-02 (nouns, domain-specific terms, abbreviations).
- Glossary becomes reference for all subsequent documents — consistency enforcer.
- Framework-specific terms từ `project-context.md` cũng nên include (e.g., "inherit" in Odoo context).

**Relationships:** `preceded-by: hbc-create-requirements`, `followed-by: hbc-create-business-flow-diagram`.

---

### Workflow: hbc-create-business-flow-diagram

**Type:** workflow — **ALREADY BUILT** ✅

**Purpose:** Generate D-06 業務フロー図 (Business Flow Diagram) — Mermaid flowcharts showing business processes, actors, and decision points.

**Status:** Existing skill at `src/hbc-create-business-flow-diagram/`. Follows full 5-stage HBC workflow pattern with resume state, decision-log, parallel-lens menu, deterministic validation.

**Role in lifecycle:** Phase 1 final document. Combined with D-02 and D-03, completes the Analysis phase artifacts needed for Phase 1 gate.

**Relationships:** `preceded-by: hbc-create-glossary`, `followed-by: hbc-phase-gate (Phase 1)`.

---

### Workflow: hbc-create-er-diagram

**Type:** workflow — **ALREADY BUILT** ✅ (Grade A)

**Purpose:** Generate D-19 データベース設計書 (Database Design) — ER diagrams in Mermaid adapted to project framework.

**Status:** Existing skill at `src/hbc-create-er-diagram/`. Full 5-stage HBC workflow pattern with resume state, decision-log, headless contract, 3 validation scripts (discover-planning-artifacts, validate-mermaid-er, check-entity-coverage), 21 unit tests. Grade A quality.

**Decision (2026-05-28):** This IS the D-19 skill. No rename to `hbc-create-db-design` needed. The skill already covers the full D-19 template scope. D-20 (table definitions) is optional and out of 19-skill scope.

**Role in lifecycle:** Phase 2 first document. Combined with D-12, D-26, D-27 (and optional D-21), completes the Design phase artifacts.

**Relationships:** `preceded-by: Phase 1 gate PASSED`, `followed-by: hbc-create-coding-standards`.

---

### Workflow: hbc-create-coding-standards

**Type:** workflow

**Purpose:** Generate D-12 コーディング規約 (Coding Standards) — per-project coding conventions adapted to project framework and team preferences.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | D-12 coding standards | project-context.md, team input | `_hbc_output/design/D-12-{project_name}-coding-standards.md` |
| Update | Revise standards | Existing D-12 + changes | Updated D-12 |
| Validate | Check completeness | D-12 | Validation report |

**Template:** `{project-root}/templates/D-12_コーディング規約_template.md`

**Workflow stages:**
1. Prerequisites + load project-context.md
2. Discovery — detect framework, ask team preferences (indent, naming, error handling style)
3. Generation — populate all D-12 sections (naming, format, comments, best practices) adapted to framework
4. Validation — all sections filled, no contradictions, aligns with framework conventions
5. Save + handoff

**Design Notes:**
- D-12 is per-project, NOT organizational. Mỗi project có conventions riêng based on framework.
- Framework adaptation: Odoo (`@api.multi`, xpath inheritance, jQuery widgets), Django (PEP 8, class-based views), Next.js (hooks, server components).
- This document becomes reference for `hbc-implement` — TDD code must follow these standards.
- Lighter workflow — 4 stages sufficient. No parallel-lens menu needed (standards are opinionated, not discovered).

**Relationships:** `preceded-by: hbc-create-er-diagram`, `followed-by: hbc-create-api-spec (optional)`.

---

### Workflow: hbc-create-api-spec

**Type:** workflow

**Purpose:** Generate D-21 API仕様書 (API Specification) — endpoint definitions, request/response schemas, authentication. **Optional** — not all projects expose APIs.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | D-21 API spec | D-02, D-19, project-context.md | `_hbc_output/design/D-21-{project_name}-api-spec.md` |
| Update | Revise endpoints | Existing D-21 + changes | Updated D-21 |
| Validate | Check against D-02 requirements | D-21, D-02 | Validation report |

**Template:** `{project-root}/templates/D-21_API仕様書_template.md`

**Workflow stages:**
1. Prerequisites — check if project needs API (ask user or detect from project-context.md)
2. Discovery — identify endpoints from D-02 requirements, define auth strategy
3. Generation — populate D-21: base URL, authentication, endpoint list, per-endpoint detail (method, URL, request/response)
4. Validation — all endpoints map to requirements, response schemas match D-19 entities
5. Save + handoff

**Design Notes:**
- Optional skill — `hbc-agent-architect` asks if project needs API before suggesting.
- Odoo projects often don't need this (internal module, no REST API). Django/Next.js projects usually do.
- If skipped, Phase 2 gate adjusts checklist accordingly.
- Standard 5-stage workflow.

**Relationships:** `preceded-by: hbc-create-coding-standards`, `followed-by: hbc-phase-gate (Phase 2, architect side)`.

---

### Workflow: hbc-create-test-plan

**Type:** workflow

**Purpose:** Generate D-26 テスト計画書 (Test Plan) — test strategy, scope, schedule, environment, entry/exit criteria, risk assessment.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | D-26 test plan | D-02, D-06, project-context.md | `_hbc_output/design/D-26-{project_name}-test-plan.md` |
| Update | Revise plan | Existing D-26 + changes | Updated D-26 |
| Validate | Check completeness | D-26 | Validation report |

**Template:** `{project-root}/templates/D-26_テスト計画書_template.md`

**Workflow stages:**
1. Prerequisites + load D-02 for scope reference
2. Discovery — test levels (unit, integration, system, E2E), test approach, team/roles, schedule, environment
3. Generation — populate all D-26 sections including Mermaid Gantt chart for schedule, risk table
4. Validation — entry/exit criteria defined, risk coverage adequate, schedule realistic
5. Save + handoff

**Design Notes:**
- Test plan is strategic — WHAT to test, not HOW. D-27 has the HOW (detailed cases).
- `e2e_framework` config variable referenced for E2E test approach section.
- `coverage_threshold` config variable sets the exit criteria threshold.
- Mermaid Gantt chart for test schedule visualization.

**Relationships:** `preceded-by: Phase 1 gate PASSED`, `followed-by: hbc-create-test-spec`. Parallel with architect workflows.

---

### Workflow: hbc-create-test-spec

**Type:** workflow

**Purpose:** Generate D-27 テスト仕様書 (Test Specification) — detailed test cases with steps, expected results, severity, traceability to requirements.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | D-27 test specification | D-26, D-02, D-19, D-06 | `_hbc_output/design/D-27-{project_name}-test-spec.md` |
| Update | Add/revise test cases | Existing D-27 + changes | Updated D-27 |
| Validate | Coverage check vs D-02 | D-27, D-02 | Validation report (requirement → test case mapping) |

**Template:** `{project-root}/templates/D-27_テスト仕様書_template.md`

**Workflow stages:**
1. Prerequisites + load D-26 (plan) + D-02 (requirements)
2. Discovery — for each REQ-xxx, derive test scenarios: positive, negative, boundary, edge cases
3. Generation — populate test case table (category, ID, content, preconditions, steps, expected, severity) + detailed cases
4. Validation — every REQ-xxx has ≥1 test case, no orphan test cases, severity distribution reasonable
5. Save + handoff

**Design Notes:**
- This is the heaviest document workflow — potentially hundreds of test cases for a complex project.
- Test case IDs format: `TC-xxx` linked to `REQ-xxx`.
- Coverage matrix: REQ-xxx → TC-xxx mapping validated deterministically.
- D-27 is THE input for Phase 3 TDD — `hbc-implement` reads test cases from here to write failing tests first.
- Parallel-lens menu recommended at Stage 3/4 for thoroughness review.

**Relationships:** `preceded-by: hbc-create-test-plan`, `followed-by: hbc-phase-gate (Phase 2, QA side)`.

---

### Workflow: hbc-task-breakdown

**Type:** workflow

**Purpose:** Break down design artifacts into granular, implementable tasks ordered for TDD execution.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Create | Ordered task list for implementation | D-19, D-27, D-12, D-21 (optional) | `_hbc_output/impl/task-breakdown.md` |
| Update | Re-prioritize or split tasks | Existing breakdown + feedback | Updated task-breakdown.md |
| Validate | Check task coverage vs design | Task list, D-19, D-27 | Validation report |

**No D-xx template** — custom format:

```markdown
## Task List
| task_id | description | design_ref | test_refs | priority | status | dependencies |
```

**Workflow stages:**
1. Prerequisites + load all Phase 2 design artifacts
2. Analysis — decompose D-19 entities into implementation tasks, map D-27 test cases to tasks
3. Generation — ordered task list with dependencies, each task references design_ref (D-19 entity/endpoint) and test_refs (TC-xxx from D-27)
4. Validation — all D-19 entities covered, all D-27 test cases assigned to tasks, no circular dependencies
5. Save + handoff

**Design Notes:**
- Tasks ordered for TDD: implement foundational entities first (no dependencies), then dependent entities.
- Each task = 1 TDD cycle in `hbc-implement`. Granularity: ~1-4 hours of work per task.
- Status tracking: TODO → IN_PROGRESS → DONE. Updated by `hbc-implement` during execution.
- Lighter workflow — no resume state needed (re-run regenerates from design artifacts).

**Relationships:** `preceded-by: Phase 2 gate PASSED`, `followed-by: hbc-implement`.

---

### Workflow: hbc-implement

**Type:** workflow

**Purpose:** Implement code via TDD cycle (RED → GREEN → REFACTOR) per task from breakdown. Writes test code AND implementation code.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Implement task | Working code + passing tests for 1 task | Task from breakdown, D-27 test cases, D-12 standards | Code files + test files |
| Implement all | Batch implementation of remaining tasks | Full task breakdown | All code + test files |
| Check coverage | Verify test coverage meets threshold | Code + tests | Coverage report |

**No D-xx template** — produces code artifacts directly.

**Workflow stages per task:**
1. Load task from `task-breakdown.md` + relevant D-27 test cases + D-12 coding standards
2. RED — Write failing test(s) based on D-27 spec for this task
3. GREEN — Write minimal implementation code to pass tests
4. REFACTOR — Clean up code while keeping tests green. Apply D-12 standards.
5. Update task status to DONE. Check coverage. If below `coverage_threshold`: add more tests.
6. Repeat for next task or return to agent menu.

**Design Notes:**
- Each task is a mini TDD cycle. Agent coaches through RED → GREEN → REFACTOR.
- Reads `project-context.md` for framework-specific code generation (Odoo models, Django views, React components...).
- E2E test scripts written here (Playwright, Selenium) but NOT executed — execution is Phase 4.
- Coverage check uses project's test runner (`pytest --cov`, `jest --coverage`, etc.).
- Headless mode: batch-implement all TODO tasks sequentially.
- This is the most interactive workflow — Dev agent pairs with user throughout.

**Relationships:** `preceded-by: hbc-task-breakdown`, `followed-by: hbc-phase-gate (Phase 3)`.

---

### Workflow: hbc-test-execution

**Type:** workflow

**Purpose:** Execute test suites (unit, integration, E2E), collect results, generate execution report.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Execute all | Run full test suite, document results | Code + tests + D-27 | `_hbc_output/test/test-execution-report.md` |
| Execute subset | Run specific test category | Test filter criteria | Partial execution report |
| Generate report | Format results into D-xx style report | Raw test output | Formatted execution report |

**No D-xx template** — custom execution report format:

```markdown
## Test Execution Summary
| total | passed | failed | skipped | coverage |
## Failed Tests Detail
| test_id | test_case_ref | error | classification |
## Defect Triage
| defect_id | type | action | assigned_to |
```

**Workflow stages:**
1. Prerequisites — verify test environment, load D-27 for expected test inventory
2. Execute — run test suites (user provides commands or auto-detect from project-context.md)
3. Collect — parse test output, map results to D-27 test case IDs
4. Triage — classify failures: `failed_test` (code bug → Dev fix), `no_coverage` (missing test → QA), `wrong_requirement` (spec issue → BA/PO)
5. Report — generate execution report with evidence (pass/fail counts, coverage %, defect list)

**Design Notes:**
- Tester agent runs this, not Dev. Fresh eyes on test results.
- Defect classification drives routing: back to Phase 3 (Dev), Phase 2 (QA), or Phase 1 (BA).
- If defects found: report generated but gate blocked until defects resolved + re-execution.
- E2E tests executed here — scripts written in Phase 3, run in Phase 4.

**Relationships:** `preceded-by: Phase 3 gate PASSED`, `followed-by: hbc-acceptance-check`.

---

### Workflow: hbc-acceptance-check

**Type:** workflow

**Purpose:** Final acceptance evaluation — review all artifacts, test results, and traceability for sign-off by `acceptance_owner`.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Review | Comprehensive acceptance review | All phase artifacts + test results | `_hbc_output/test/acceptance-report.md` |
| Decide | Record acceptance decision | Review findings + owner input | Decision: ACCEPTED/REJECTED/DEFERRED/PENDING |

**No D-xx template** — custom acceptance report format:

```markdown
## Acceptance Criteria Checklist
| criterion | status | evidence |
## Traceability Summary
| total_reqs | designed | implemented | tested | coverage_% |
## Decision
status: ACCEPTED | REJECTED | DEFERRED | PENDING
decided_by: {acceptance_owner}
reason: ...
```

**Workflow stages:**
1. Prerequisites — load test execution report, traceability matrix, all gate reports
2. Review — walk through acceptance criteria: all requirements traced, all tests passed, coverage ≥ threshold, all gates PASSED
3. Present — summarize findings to `acceptance_owner` with evidence
4. Decide — record decision with rationale. If REJECTED: list specific blocking issues + return-to phase.
5. Report — generate acceptance report, update traceability matrix final status

**Design Notes:**
- `acceptance_owner` from config decides. Tester agent presents evidence but doesn't decide.
- 4 states: ACCEPTED (done), REJECTED (blocking issues, return to specific phase), DEFERRED (acceptable but with known issues), PENDING (needs more info).
- REJECTED routes: specify which phase to return to based on defect type.
- This is the final workflow. ACCEPTED + Phase 4 gate PASSED = project lifecycle complete.

**Relationships:** `preceded-by: hbc-test-execution`, `followed-by: hbc-phase-gate (Phase 4, final)`.

---

### Cross-cutting: hbc-phase-gate

**Type:** workflow

**Purpose:** Validation engine for phase transitions. Receives phase-specific checklist, evaluates artifacts against criteria, produces gate report with PASSED/FAILED status.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Evaluate gate | Gate report with PASSED/FAILED | Phase number + phase artifacts | `_hbc_output/gates/phase-{N}-gate.md` |
| Re-evaluate | Re-run gate after fixes | Updated artifacts + previous gate report | Updated gate report |

**Workflow:**
1. Determine phase number (from caller context or user input)
2. Load gate checklist from calling skill's `assets/phase-{N}-gate-checklist.md`
3. For each checklist item: verify artifact exists, check completeness criteria, evaluate quality criteria
4. Generate gate report: item-by-item PASS/FAIL/SKIP with evidence
5. Overall decision: PASSED (all required items PASS), FAILED (any required item FAIL)
6. If `gate_mode = lenient`: FAILED becomes WARNING (allow proceed with notice)

**Design Notes:**
- This skill is an ENGINE — it doesn't own checklist content. Gate checklists live in `assets/` of each phase's final skill.
- Phase 1 gate checklist: D-02 exists + has REQ IDs, D-03 exists, D-06 exists, requirements traceable to flows.
- Phase 2 gate checklist: D-19 exists, D-12 exists, D-26 exists, D-27 exists + covers all REQ-xxx, design refs traceable.
- Phase 3 gate checklist: all tasks DONE, tests pass, coverage ≥ `coverage_threshold`, code follows D-12.
- Phase 4 gate checklist: test execution complete, acceptance decision made, traceability matrix fully populated.
- Invoked from any agent's [PG] menu. Cross-cutting — same engine, different checklists.
- Deterministic where possible (file exists? coverage number?), LLM judgment where needed (quality check).

**Relationships:** Invoked after each phase's workflows complete. Gate report is hard dependency for next phase (unless `gate_mode = lenient`).

---

### Cross-cutting: hbc-traceability

**Type:** workflow

**Purpose:** Maintain living traceability matrix — maps requirements through design, implementation, and testing. Updated incrementally after each phase.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
|------------|---------|--------|---------|
| Initialize | Create matrix with REQ IDs from D-02 | D-02 | `_hbc_output/traceability/matrix.md` |
| Update | Populate columns for current phase | Phase artifacts | Updated matrix.md |
| Report | Generate coverage summary | Current matrix | Coverage statistics (% traced through each column) |
| Audit | Find gaps — requirements without design/code/test refs | Current matrix | Gap report |

**Matrix format (7 columns MVP):**

```markdown
| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|--------|----------|------------|----------|----------|-------------|-----------|
| REQ-001 | | | | | | |
```

**Workflow:**
1. Detect current state — which columns are populated?
2. Based on invoking phase, populate relevant columns:
   - After Phase 1: `req_id` (from D-02)
   - After Phase 2: `design_ref` (from D-19 entities), `test_ref` (from D-27 TC-xxx IDs)
   - After Phase 3: `code_ref` (from implementation file/function refs)
   - After Phase 4: `gate_status` (from gate reports), `timestamp` (final)
3. Report coverage: X/Y requirements fully traced
4. Highlight gaps: requirements missing coverage in any column

**Design Notes:**
- Living document — not generated once, updated incrementally. Each invoke adds data, never removes.
- `story_id` column optional — populated only if project uses story-level tracking.
- Cross-cutting: invoked from any agent's [TR] menu. Most valuable after phase gate passes.
- Audit capability is the "health check" — shows exactly where traceability breaks.
- Future: HTML report output for visual matrix with color-coded coverage.

**Relationships:** Invoked after each phase. No hard dependencies — can be run anytime to check current state.

## Configuration

| Variable | Prompt | Default | Result Template | User Setting |
|----------|--------|---------|-----------------|--------------|
| `acceptance_owner` | "Ai sẽ sign-off acceptance ở Phase 4? (PM, Tech Lead, PO)" | `""` (bắt buộc) | `acceptance_owner = "{value}"` | Yes |
| `coverage_threshold` | "% test coverage tối thiểu cho phase gate?" | `80` | `coverage_threshold = {value}` | Yes |
| `e2e_framework` | "E2E test framework?" | `playwright` | `e2e_framework = "{value}"` | Yes |
| `gate_mode` | "Gate mode: strict (block next phase) hay lenient (warn but allow)?" | `strict` | `gate_mode = "{value}"` | Yes |
| `output_language` | "Ngôn ngữ nội dung D-xx documents? (ja/vi/en)" | `ja` | `output_language = "{value}"` | Yes |
| `project_context_path` | "Đường dẫn project-context.md?" | `_hbc_output/project-context.md` | `project_context_path = "{value}"` | No |

**Ghi chú:**
- `acceptance_owner` là required — setup skill sẽ hỏi cho đến khi user điền.
- `gate_mode = strict` là recommended cho production projects. `lenient` dùng khi pilot/POC cần flexibility.
- `output_language` chỉ ảnh hưởng nội dung bên trong — section headers giữ tiếng Nhật theo D-xx template chuẩn.
- Mọi variable đều có sensible default (trừ `acceptance_owner`). Skill tự hỏi runtime nếu config chưa set.

## External Dependencies

Không yêu cầu CLI tool hay MCP server bên ngoài. Tất cả skills chạy trong Claude Code context, output là markdown files.

- **Mermaid diagrams**: Render native trong markdown viewers (GitHub, VS Code preview). Không cần tool riêng.
- **Test frameworks** (Playwright, pytest...): User tự cài theo project stack. Skills chỉ generate test code/specs, không execute trực tiếp.
- **Git**: Cần cho traceability (link code_ref). Có sẵn trong mọi dev environment.

## UI and Visualization

Không có web app hay dashboard riêng cho MVP.

**Traceability matrix** (`_hbc_output/traceability/matrix.md`) đóng vai trò progress dashboard — columns populated dần qua các phases cho thấy trạng thái tổng thể.

**Gate reports** (`_hbc_output/gates/phase-X-gate.md`) là status view cho mỗi phase — checklist items với PASS/FAIL/SKIP.

**Future consideration:** `hbc-traceability` có thể thêm HTML report output (bảng interactive, filter theo status) khi cần visual reporting mạnh hơn. Không cần cho MVP.

## Setup Extensions

Setup skill thực hiện:

1. **Scaffold output directory:**
   ```
   _hbc_output/
   ├── plan/           # D-02 Requirements, D-03 Glossary, D-06 Business Flow
   ├── design/         # D-19 DB Design, D-12 Coding Standards, D-26 Test Plan, D-27 Test Spec, D-21 API Spec
   ├── impl/           # Task breakdown, code artifacts
   ├── test/           # Test execution reports, acceptance reports
   ├── gates/          # phase-1-gate.md, phase-2-gate.md, ...
   └── traceability/   # matrix.md
   ```

2. **Collect required config:** Prompt user cho `acceptance_owner` (required) + optional overrides.

3. **Generate project-context.md skeleton:** Nếu chưa tồn tại tại `project_context_path`, tạo skeleton với sections: Tech Stack, Framework Conventions, Project Structure, Naming Conventions. User điền manual hoặc dùng auto-detect nếu codebase đã có.

4. **Write customize.toml defaults:** Ghi config variables vào `_bmad/custom/hbc.toml` để 3-layer merge hoạt động.

## Integration

**Expansion module** — mở rộng `hbc (HBLAB BMad Custom)` module hiện tại.

- Sử dụng existing `_hbc_output/` structure đã có từ các skills hiện tại (`hbc-create-er-diagram`, `hbc-create-business-flow-diagram`).
- Existing skills vẫn hoạt động standalone — không phụ thuộc vào module mới.
- New workflow skills reference existing outputs khi relevant (e.g., `hbc-create-er-diagram` output tại `_hbc_output/design/`).
- Module help CSV mở rộng entries hiện có, không replace.
- Phase gate skills kiểm tra artifacts từ cả existing và new skills.

## Creative Use Cases

- **Cross-project template reuse:** `project-context.md` swap giữa projects → cùng workflow nhưng output khác nhau (Odoo vs Django vs Next.js).
- **Partial adoption:** Team chỉ dùng Phase 1-2 (document generation) mà không enforce gates — set `gate_mode = lenient`.
- **Retrospective tracing:** Dùng `hbc-traceability` trên project đã có documents → reverse-populate matrix để audit coverage gaps.
- **Training mode:** Junior dev chạy full workflow trên toy project để học waterfall + TDD process. Gate feedback = learning mechanism.
- **Party Mode cross-review:** 4 agents join roundtable để review cross-phase artifacts — BA kiểm tra requirements coverage trong test specs, QA review design feasibility.

## Ideas Captured

### Bối cảnh dự án
- HBLab team phát triển dự án theo waterfall methodology (KHÔNG dùng agile)
- Kết hợp TDD (Test-Driven Development) trong phase implementation
- Template tài liệu theo chuẩn Nhật (D-xx series, 30 templates từ D-00→D-31)
- MVP: chỉ tạo workflow tối thiểu nhưng chia phase rõ ràng
- Framework-agnostic: base chung cho mọi project, customize qua project-context.md + customize.toml

### Quyết định kiến trúc đã thống nhất (từ Party Mode roundtable)
- 14 skills, mỗi skill = 1 document hoặc 1 việc cụ thể (đúng BMad pattern: 1 skill = 1 output)
- 4 phases: Analysis → Design → Implementation → Testing
- 2 cross-cutting skills: phase-gate (engine validate), traceability (living matrix)
- Phase gate = hard dependency — phase sau refuse start nếu gate chưa PASSED
- Traceability matrix 7 cột MVP: req_id, story_id, design_ref, code_ref, test_ref, gate_status, timestamp
- Gate checklist nằm trong assets/ của phase skill, hbc-phase-gate chỉ là engine
- Mỗi skill theo BMad file layout: SKILL.md, customize.toml, assets/, references/, scripts/, steps/
- Cross-cutting skills invoked mid-workflow (BMad A/P/C menu pattern)

### Document → Skill mapping
- Phase 1 (Analysis): D-02 Requirements, D-03 Glossary, D-06 Business Flow
- Phase 2 (Design): D-19 DB Design, D-12 Coding Standards, D-26 Test Plan, D-27 Test Spec, D-21 API Spec (optional)
- Phase 3 (Implementation): Task Breakdown, Implement (TDD RED→GREEN→REFACTOR)
- Phase 4 (Testing): Test Execution, Acceptance Check

### Insights từ agents
- Mary (BA): Traceability matrix là single source of truth, gate là hard dependency không phải convention
- Winston (Architect): project-context.md = what project IS, customize.toml = how workflow behaves
- Amelia (Dev): TDD = loop steps (RED→GREEN→REFACTOR), E2E boundary: code scripts = P3, execute = P4
- John (PM): D-12 Coding Standards là per-project, acceptance cần owner rõ ràng

### Odoo-specific context (ví dụ customize)
- Odoo 11: old framework, jQuery widgets, @api.multi/@api.model, _inherit/_name patterns
- D-19 cần phân biệt: _name mới vs _inherit extend vs custom fields
- D-12 cần cover: @api.multi usage, xpath view inheritance, jQuery widget lifecycle
- API exposure optional (controller pattern)
- Nhưng tất cả Odoo-specific nằm trong project-context.md, KHÔNG hardcode vào skill

### Patterns từ research
- BMad 3-layer merge: skill defaults → team overrides → personal overrides
- BMad step file pattern: step-01-init.md → step-02-xxx.md (numbered + named)
- BMad cross-skill invocation: standalone skills invoked mid-workflow
- Module registry: module.yaml + module-help.csv + marketplace.json
- Acceptance protocol: 4 trạng thái ACCEPTED/REJECTED/DEFERRED/PENDING
- Defect management: 3 loại (failed_test → fix tại chỗ, no_coverage → return Phase 2, wrong_requirement → escalate PO)

## Build Roadmap

### Recommended Build Order

Build trong 5 waves, mỗi wave có thể build parallel nếu đủ resource:

**Wave 1: Cross-cutting foundation (build first — mọi thứ khác depend on these)**
1. `hbc-phase-gate` (workflow) — gate engine cần sẵn trước khi bất kỳ phase skill nào invoke nó
2. `hbc-traceability` (workflow) — traceability matrix cần sẵn trước Phase 1 skills

**Wave 2: Phase 1 — Analysis skills**
3. `hbc-create-requirements` (workflow) — D-02, foundation cho tất cả downstream
4. `hbc-create-glossary` (workflow) — D-03, lightweight, depends on D-02
5. `hbc-create-business-flow-diagram` — ✅ **ALREADY BUILT**, skip
6. `hbc-agent-ba` (agent) — coordinator cho Wave 2 workflows

**Wave 3: Phase 2 — Design skills**
7. `hbc-create-er-diagram` — ✅ **ALREADY BUILT (Grade A)**, skip
8. `hbc-create-coding-standards` (workflow) — D-12, per-project
9. `hbc-create-api-spec` (workflow) — D-21, optional
10. `hbc-create-test-plan` (workflow) — D-26, test strategy
11. `hbc-create-test-spec` (workflow) — D-27, detailed test cases, heaviest workflow
12. `hbc-agent-architect` (agent) — coordinator cho design workflows
13. `hbc-agent-qa` (agent) — coordinator cho test design workflows

**Wave 4: Phase 3 — Implementation skills**
14. `hbc-task-breakdown` (workflow) — design → tasks
15. `hbc-implement` (workflow) — TDD cycle, most interactive
16. `hbc-agent-dev` (agent) — coordinator

**Wave 5: Phase 4 — Testing skills**
17. `hbc-test-execution` (workflow) — run & report
18. `hbc-acceptance-check` (workflow) — final decision
19. `hbc-agent-tester` (agent) — coordinator

### Rationale

- **Cross-cutting first**: Phase gate + traceability are invoked by every phase. Build once, reuse everywhere.
- **Phase order matches lifecycle**: Each wave's outputs become inputs for the next wave's skills. Tester naturally tests earlier phases' outputs.
- **Agents last within each wave**: Agents coordinate workflows. Build the workflows first, then the agent that menus them.
- **Already-built skills**: `hbc-create-business-flow-diagram` (D-06) exists. `hbc-create-er-diagram` (D-19) partially exists — evaluate reuse vs extend at Wave 3.

### Build Method per Type

| Type | Build with | Notes |
|------|-----------|-------|
| Workflow skills | **Build a Workflow (BW)** | Pass this plan doc as context. Follow existing HBC 5-stage pattern. |
| Agent skills | **Build an Agent (BA)** | Pass this plan doc as context. Lean agent: SKILL.md + customize.toml only. |
| Module packaging | **Create Module (CM)** | After all skills built. Generates setup skill, help CSV, marketplace entry. |

**Next steps:**

1. Build each skill using **Build an Agent (BA)** or **Build a Workflow (BW)** — share this plan document as context
2. When all skills are built, return to **Create Module (CM)** to scaffold the module infrastructure
