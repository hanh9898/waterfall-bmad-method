---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - templates/D-00 → D-31 (30 templates)
  - _bmad/core/config.yaml
  - _bmad/bmm/config.yaml
  - _bmad/bmb/config.yaml
  - src/hbc-setup/assets/module.yaml
  - src/hbc-setup/assets/module-help.csv
  - src/hbc-create-business-flow-diagram/SKILL.md
  - src/hbc-create-er-diagram/SKILL.md
  - src/hbc-create-invest-epics-and-stories/SKILL.md
  - .claude/skills/bmad-module-builder/SKILL.md
  - .claude/skills/bmad-workflow-builder/SKILL.md
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'Thiết kế custom BMad module tối ưu theo bộ tài liệu HBLab D-00→D-31'
research_goals: 'Đúc kết pattern từ BMad core/BMM để thiết kế multi-module system chia theo phase, với workflow mandatory/optional templates'
user_name: 'Hanhnt2'
date: '2026-05-20'
web_research_enabled: true
source_verification: true
---

# Nghiên cứu kỹ thuật: Thiết kế Custom BMad Module tối ưu cho bộ tài liệu HBLab

**Ngày:** 2026-05-20
**Tác giả:** Hanhnt2
**Loại nghiên cứu:** Technical Architecture

---

## Tổng quan nghiên cứu

### Mục tiêu
Phân tích sâu cách BMad Method xây dựng skill, workflow và module system, từ đó đúc kết pattern tối ưu để thiết kế hệ thống custom module cho bộ 30 template tài liệu HBLab (D-00 → D-31), chia theo phase giống BMM, với cơ chế mandatory/optional.

### Phạm vi
- Phân tích kiến trúc BMad Module System (Core, BMM, BMB)
- Phân tích 30 templates và dependency graph
- Đề xuất phân chia module theo phase
- Đề xuất thiết kế skill cho từng template
- Chiến lược mandatory/optional workflow

### Phương pháp
- Đọc và phân tích source code BMad installed modules (core, bmm, bmb)
- Đọc và phân tích 3 HBC custom skills đã có
- Nghiên cứu BMad module builder, workflow builder patterns
- Web research: DeepWiki, GitHub bmad-code-org, bmad-builder docs
- Đọc toàn bộ 30 template files

---

## 1. Đúc kết Pattern từ BMad

### 1.1 Kiến trúc Module

BMad tổ chức module theo **registry-based architecture**:

```
_bmad/
├── core/           # Module gốc (help, brainstorming, editorial)
│   ├── config.yaml
│   └── module-help.csv
├── bmm/            # BMad Method Module (agile workflow)
│   ├── config.yaml
│   ├── module-help.csv
│   └── 1-analysis/ → 4-implementation/
├── bmb/            # BMad Builder (meta-tools)
│   ├── config.yaml
│   └── module-help.csv
└── _config/
    ├── manifest.yaml        # Installation metadata
    └── skill-manifest.csv   # Canonical skill registry
```

**Pattern rút ra:**
- Mỗi module có `config.yaml` riêng cho module-specific variables
- Mỗi module có `module-help.csv` đăng ký capabilities cho help system
- Skills được tổ chức trong sub-folders theo phase
- Module manifest (`module.yaml`) định nghĩa identity, dependencies, config variables

### 1.2 Skill Activation Pattern (Bắt buộc)

Mọi skill BMad tuân thủ chuỗi 6 bước activation:

| Bước | Mô tả | Mục đích |
|------|--------|----------|
| 1 | Resolve Workflow Block | 3-layer TOML merge (base → team → user) |
| 2 | Execute Prepend Steps | Pre-flight checks trước config load |
| 3 | Load Persistent Facts | Context tĩnh cho toàn session |
| 4 | Load Config | Resolve variables ({user_name}, {planning_artifacts}...) |
| 5 | Greet User | Chào bằng {communication_language} |
| 6 | Execute Append Steps | Setup context sau greet |

### 1.3 Workflow Stages Pattern (5-stage cho artifact skills)

Mỗi skill tạo artifact tuân thủ 5 stage:

```
Stage 1: Prerequisites & Scope
  ├── Bind workspace + detect resume state
  ├── Consume source inventory (discover script)
  ├── Inferred-defaults confirmation
  └── Initialize from template

Stage 2: Discovery
  ├── Extract actors, triggers, steps, decisions, outcomes
  ├── Compaction-flush (write to decision-log for crash recovery)
  └── Present for confirmation

Stage 3: Generation
  ├── Render artifact content
  ├── Revision history gate (create vs polish vs semantic)
  └── Parallel-lens review menu [A/P/C]

Stage 4: Validation
  ├── Deterministic validators (scripts)
  ├── LLM judgment checks
  ├── Fix loop (interactive) or auto-fix (headless)
  └── Parallel-lens review menu [A/P/C]

Stage 5: Save & Handoff
  ├── Finalize artifact
  ├── Close decision-log session
  └── Declare downstream consumers
```

### 1.4 Customize.toml Pattern

```toml
[workflow]
activation_steps_prepend = []
activation_steps_append = []
persistent_facts = ["file:{project-root}/**/project-context.md"]

# Skill-specific scalars
<purpose>_template = "{skill-root}/templates/<template-file>"
<purpose>_output_path = "{planning_artifacts}/<category>/<doc-id>-{project_name}/"
on_complete = ""  # hook to next skill
```

**Merge rules:**
- Scalars: rightmost wins (user > team > base)
- Tables: deep-merge
- Arrays of tables (keyed `code`/`id`): key-merge
- Plain arrays: append-only

### 1.5 Decision-Log Workspace Pattern

```
{doc_workspace}/
├── <primary-artifact>.md      # Tài liệu chính
├── .decision-log.md           # Session history, auto-decisions
└── .scan/
    ├── artifacts.json         # Source inventory
    └── <validator>.json       # Validation results
```

**Resume protocol:** Frontmatter `stepsCompleted` array → Resume/Update/Start fresh menu.

### 1.6 Headless Mode Pattern

- Flag: `-H` / `--headless`
- Input: command-line flags thay user interaction
- Output: JSON return contract (`status: complete|blocked`, `reason: <closed-set>`)
- Auto-decisions logged to `.decision-log.md`
- Only `auto_fixable: true` issues get patched silently

### 1.7 Core Quality Test

> **Mỗi dòng trong SKILL.md phải pass test: "LLM có làm đúng cái này mà không cần được chỉ?"**
> Nếu có → cắt bỏ. Nếu không → giữ lại.

**Giữ lại:** paths, schema, BMad conventions, hard rules, script invocations, design rationale.
**Cắt bỏ:** procedural steps tự nhiên, scoring formulas, greeting templates, defensive padding.

---

## 2. Phân tích bộ tài liệu HBLab D-00→D-31

### 2.1 Dependency Graph

```
D-01 企画書 (Business Plan)
  ├── D-03 用語集 (Glossary) ← referenced by ALL
  ├── D-06 Business Flow (AS-IS/TO-BE) ← existing skill
  └── D-02 要件定義書 (Requirements/PRD)
       ├── D-04 ユースケース記述 (Use Case Description)
       │    └── D-05 ユースケース図 (Use Case Diagram)
       ├── D-07 運用シナリオ (Operational Scenario)
       └── D-08 基本設計書 (Basic Design) ← HUB document
            ├── D-09 アーキテクチャ設計書 (Architecture)
            │    └── D-10 システム構成図 (System Config)
            ├── D-11 ディレクトリ構成図 (Directory Structure)
            ├── D-14 画面仕様書 (Screen/UI Spec)
            ├── D-15 外部IF設計書 (External Interface)
            │    └── D-21 API仕様書 (API Spec)
            ├── D-16 詳細設計書 (Detailed Design)
            │    ├── D-17 シーケンス図 (Sequence Diagram)
            │    └── D-18 クラス図 (Class Diagram)
            ├── D-19 データベース設計書 (DB Design/ER) ← existing skill
            │    └── D-20 テーブル定義書 (Table Definition)
            └── D-23 バッチスケジュール表 (Batch Schedule)

D-12 コーディング規約 (Coding Standards) ← standalone
D-13 採用技術一覧 (Tech Stack) ← standalone

D-22 ログ設計書 (Logging Design)
D-24 運用設計書 (Operations Design)
  ├── D-28 運用・保守マニュアル (Ops Manual)
  └── D-25 移行設計書 (Migration Design)

D-26 テスト計画書 (Test Plan)
  └── D-27 テスト仕様書 (Test Spec)

D-29 プロジェクトサマリー (Project Summary) ← references ALL
D-31 運用部門マニュアル (Operations Dept Manual) ← references many

D-00 README ← references D-11, D-12, D-13
```

### 2.2 Phân loại Mandatory vs Optional

| Tài liệu | Bắt buộc? | Lý do |
|-----------|-----------|-------|
| D-01 企画書 | **Mandatory** | Khởi đầu mọi dự án, context gốc |
| D-02 要件定義書 | **Mandatory** | PRD - nền tảng cho tất cả downstream |
| D-03 用語集 | **Mandatory** | Nhất quán thuật ngữ toàn dự án |
| D-04 ユースケース記述 | Optional | Chi tiết hơn D-02, phụ thuộc complexity |
| D-05 ユースケース図 | Optional | Visual của D-04, cần khi nhiều use cases |
| D-06 Business Flow | **Mandatory** | Luồng nghiệp vụ AS-IS/TO-BE |
| D-07 運用シナリオ | Optional | Cần cho operational systems |
| D-08 基本設計書 | **Mandatory** | Hub document, overview toàn bộ design |
| D-09 アーキテクチャ | **Mandatory** | Quyết định kiến trúc hệ thống |
| D-10 システム構成図 | Optional | Cần cho infra phức tạp |
| D-11 ディレクトリ構成図 | **Mandatory** | Chuẩn hóa codebase structure |
| D-12 コーディング規約 | **Mandatory** | Coding standards cho team |
| D-13 採用技術一覧 | **Mandatory** | Giải trình lựa chọn tech |
| D-14 画面仕様書 | Optional | Cần cho web/mobile có UI |
| D-15 外部IF設計書 | Optional | Cần khi tích hợp external systems |
| D-16 詳細設計書 | Optional | Cần cho complex modules |
| D-17 シーケンス図 | Optional | Visual bổ sung cho D-16 |
| D-18 クラス図 | Optional | OOP projects |
| D-19 データベース設計書 | **Mandatory** | ER diagram cho mọi DB project |
| D-20 テーブル定義書 | Optional | Chi tiết column-level từ D-19 |
| D-21 API仕様書 | Optional | Cần cho API-based systems |
| D-22 ログ設計書 | Optional | Cần cho production systems |
| D-23 バッチスケジュール表 | Optional | Cần khi có batch processing |
| D-24 運用設計書 | Optional | Cần cho production operations |
| D-25 移行設計書 | Optional | Cần khi migration từ system cũ |
| D-26 テスト計画書 | **Mandatory** | QA strategy cho mọi dự án |
| D-27 テスト仕様書 | Optional | Chi tiết test cases từ D-26 |
| D-28 運用・保守マニュアル | Optional | Cần cho handover |
| D-29 プロジェクトサマリー | Optional | Project closure |
| D-31 運用部門マニュアル | Optional | End-user department manual |
| D-00 README | **Mandatory** | Project entry point |

**Tổng kết: 12 mandatory + 18 optional**

---

## 3. Đề xuất thiết kế Module System

### 3.1 Phân chia Module theo Phase

```
Module: hbc-plan (Phase 1-2: Analysis & Planning)
├── hbc-create-business-plan         D-01 企画書          [Mandatory]
├── hbc-create-requirements          D-02 要件定義書      [Mandatory]
├── hbc-create-glossary              D-03 用語集          [Mandatory]
├── hbc-create-use-case-desc         D-04 ユースケース記述 [Optional]
├── hbc-create-use-case-diagram      D-05 ユースケース図   [Optional]
├── hbc-create-business-flow-diagram D-06 Business Flow   [Mandatory] ← EXISTS
├── hbc-create-operational-scenario  D-07 運用シナリオ     [Optional]
└── hbc-plan-setup                   Module setup skill

Module: hbc-design (Phase 3: Solutioning/Design)
├── hbc-create-basic-design          D-08 基本設計書       [Mandatory]
├── hbc-create-architecture          D-09 アーキテクチャ   [Mandatory]
├── hbc-create-system-config         D-10 システム構成図    [Optional]
├── hbc-create-directory-structure   D-11 ディレクトリ構成図 [Mandatory]
├── hbc-create-coding-standards      D-12 コーディング規約  [Mandatory]
├── hbc-create-tech-stack            D-13 採用技術一覧     [Mandatory]
├── hbc-create-screen-spec           D-14 画面仕様書       [Optional]
├── hbc-create-external-interface    D-15 外部IF設計書     [Optional]
├── hbc-create-detailed-design       D-16 詳細設計書       [Optional]
├── hbc-create-sequence-diagram      D-17 シーケンス図     [Optional]
├── hbc-create-class-diagram         D-18 クラス図         [Optional]
├── hbc-create-er-diagram            D-19 DB設計書/ER     [Mandatory] ← EXISTS
├── hbc-create-table-definition      D-20 テーブル定義書    [Optional]
├── hbc-create-api-spec              D-21 API仕様書       [Optional]
├── hbc-create-invest-stories        INVEST stories       [Optional] ← EXISTS
└── hbc-design-setup                 Module setup skill

Module: hbc-ops (Phase 4: Implementation & Operations)
├── hbc-create-logging-design        D-22 ログ設計書       [Optional]
├── hbc-create-batch-schedule        D-23 バッチスケジュール [Optional]
├── hbc-create-operations-design     D-24 運用設計書       [Optional]
├── hbc-create-migration-design      D-25 移行設計書       [Optional]
├── hbc-create-test-plan             D-26 テスト計画書     [Mandatory]
├── hbc-create-test-spec             D-27 テスト仕様書     [Optional]
├── hbc-create-ops-manual            D-28 運用・保守マニュアル [Optional]
├── hbc-create-project-summary       D-29 プロジェクトサマリー [Optional]
├── hbc-create-dept-manual           D-31 運用部門マニュアル  [Optional]
├── hbc-create-readme                D-00 README          [Mandatory]
└── hbc-ops-setup                    Module setup skill
```

### 3.2 Tại sao 3 module thay vì 4?

BMM chia 4 phase nhưng HBLab templates có đặc thù:
- **Analysis + Planning** gộp vì D-01→D-07 là chuỗi liên tục, tách ra sẽ tạo module quá nhỏ (phase 1 chỉ có brainstorming/research — đã có sẵn trong BMM)
- **Solutioning** (Design) là nhóm lớn nhất (15 skills) — xứng đáng 1 module riêng
- **Implementation + Operations** gộp vì operations docs thường làm song song implementation

### 3.3 Module Config Variables

```yaml
# hbc-plan/config.yaml
module_code: hbc-plan
planning_artifacts: "{project-root}/_bmad-output/planning-artifacts"
mandatory_docs:
  - D-01
  - D-02
  - D-03
  - D-06

# hbc-design/config.yaml
module_code: hbc-design
mandatory_docs:
  - D-08
  - D-09
  - D-11
  - D-12
  - D-13
  - D-19

# hbc-ops/config.yaml
module_code: hbc-ops
mandatory_docs:
  - D-26
  - D-00
```

### 3.4 Module Help CSV Format

```csv
module,skill,display-name,menu-code,description,action,args,phase,after,before,required,output-location,outputs
HBLab Plan,hbc-create-business-plan,Create Business Plan,BP,"Generate D-01 企画書 from stakeholder input",,-H,1-planning,,hbc-create-requirements,true,planning_artifacts,D-01 business plan
HBLab Plan,hbc-create-requirements,Create Requirements,REQ,"Generate D-02 要件定義書 from D-01",,-H,1-planning,hbc-create-business-plan,hbc-create-basic-design,true,planning_artifacts,D-02 requirements
...
```

---

## 4. Chiến lược tái sử dụng & Tối ưu

### 4.1 Shared Scripts Pattern

Thay vì mỗi skill có script riêng, tạo shared scripts:

```
src/hbc-shared/
├── scripts/
│   ├── discover-planning-artifacts.py    # Dùng chung cho tất cả skills
│   ├── validate-mermaid.py              # Cho D-05, D-06, D-09, D-10, D-17, D-18, D-19
│   ├── validate-template-sections.py    # Generic section validator
│   └── check-dependency-docs.py         # Kiểm tra upstream docs tồn tại
└── assets/
    └── decision-log-template.md         # Shared decision log template
```

Mỗi skill reference: `python3 {project-root}/src/hbc-shared/scripts/discover-planning-artifacts.py`

### 4.2 Skill Complexity Tiers

Không phải mọi template đều cần 5-stage complex workflow:

| Tier | Complexity | Workflow type | Templates |
|------|-----------|---------------|-----------|
| **Tier 1** | Complex | 5-stage + scripts + headless | D-01, D-02, D-06, D-08, D-09, D-19 |
| **Tier 2** | Medium | 3-stage inline + headless | D-03, D-11, D-12, D-13, D-14, D-16, D-21, D-24, D-26 |
| **Tier 3** | Simple | 2-stage inline | D-04, D-05, D-07, D-10, D-15, D-17, D-18, D-20, D-22, D-23, D-25, D-27, D-28, D-29, D-31, D-00 |

**Tier 1 (Complex):** Interactive discovery, multiple sources, validation scripts, resume/update state, revision history gate.

**Tier 2 (Medium):** Source-driven generation từ upstream docs, inline validation, basic headless support.

**Tier 3 (Simple):** Template fill từ existing docs, minimal interaction, straightforward generation.

### 4.3 Workflow Orchestration: Pipeline Runner

Tạo 1 meta-skill `hbc-pipeline-runner` để orchestrate toàn bộ:

```
hbc-pipeline-runner --profile full         # Tất cả mandatory + optional
hbc-pipeline-runner --profile minimal      # Chỉ mandatory (12 docs)
hbc-pipeline-runner --profile design-only  # D-08→D-21
hbc-pipeline-runner --docs D-01,D-02,D-06  # Cherry-pick
```

Pipeline tự động:
1. Resolve dependency graph
2. Chạy từng skill theo thứ tự topological
3. Pass output của skill trước làm input skill sau
4. Skip optional docs trừ khi --profile yêu cầu
5. Report progress và blocked skills

### 4.4 on_complete Chain

Mỗi skill's `customize.toml` khai báo `on_complete` để chain sang skill tiếp theo:

```toml
# D-01 customize.toml
on_complete = "invoke hbc-create-requirements"

# D-02 customize.toml  
on_complete = "invoke hbc-create-glossary"

# D-09 customize.toml
on_complete = "invoke hbc-create-system-config"
```

### 4.5 Template Bundling Strategy

Dựa trên bài học D-06 template missing:

**Rule:** Mỗi skill PHẢI bundle template của mình trong `{skill-root}/templates/`

```toml
# customize.toml — ĐÚNG
business_plan_template = "{skill-root}/templates/D-01_企画書_template.md"

# customize.toml — SAI (sẽ miss sau install)
business_plan_template = "{project-root}/templates/D-01_企画書_template.md"
```

Nhưng vẫn cho phép override qua team/user TOML khi project muốn dùng template riêng.

---

## 5. Skeleton cho 1 skill mới (Tier 2 example)

### Ví dụ: hbc-create-tech-stack (D-13)

```
src/hbc-create-tech-stack/
├── SKILL.md
├── customize.toml
├── templates/
│   └── D-13_採用技術一覧_template.md
├── assets/
│   └── decision-log-template.md     # hoặc symlink → shared
└── references/
    └── headless-contract.md
```

**customize.toml:**
```toml
[workflow]
activation_steps_prepend = []
activation_steps_append = []
persistent_facts = ["file:{project-root}/**/project-context.md"]
tech_stack_template = "{skill-root}/templates/D-13_採用技術一覧_template.md"
tech_stack_output_path = "{planning_artifacts}/design/D-13-{project_name}/"
on_complete = ""
```

**SKILL.md structure:**
```markdown
---
name: hbc-create-tech-stack
description: "Generate D-13 採用技術一覧 (Technology Stack). Use when user says
  'create tech stack', 'tạo danh sách công nghệ', 'create D-13'."
---

# Create Technology Stack List (D-13)

## Overview
[What/How/Why — 3-4 sentences]

## Conventions
[Standard BMad conventions block]

## Language Rules
[Standard i18n rules]

## On Activation
[6-step standard sequence]

## Workflow

### 1. Prerequisites
- Scan for D-09 architecture, D-00 README, package.json/requirements.txt
- Initialize from template

### 2. Discovery & Generation
- Extract tech from source artifacts
- Categorize: Frontend/Backend/DB/Infra/CI-CD/Other
- Fill adoption reason for each

### 3. Validation & Save
- Check completeness (all categories covered?)
- Verify versions are specific, not "latest"
- Save and declare downstream (D-00 README, D-12 Coding Standards)
```

---

## 6. Lộ trình triển khai đề xuất

### Phase 1: Foundation (Sprint 1-2)
1. Tạo `hbc-shared/` với shared scripts
2. Refactor 3 skills hiện có (D-06, D-19, INVEST) theo pattern mới
3. Tạo `hbc-plan-setup` module setup skill
4. Build D-01, D-02, D-03 (mandatory planning docs)

### Phase 2: Design Module (Sprint 3-4)
1. Tạo `hbc-design-setup` module setup skill
2. Build mandatory design skills: D-08, D-09, D-11, D-12, D-13
3. Move D-19, D-06 vào đúng module
4. Build optional design skills theo priority

### Phase 3: Ops Module (Sprint 5-6)
1. Tạo `hbc-ops-setup` module setup skill
2. Build D-26 (Test Plan), D-00 (README)
3. Build remaining optional skills
4. Build `hbc-pipeline-runner` meta-skill

### Phase 4: Polish (Sprint 7)
1. Headless mode cho tất cả Tier 1 + Tier 2 skills
2. Validation scripts cho cross-document consistency
3. Integration testing toàn pipeline
4. Documentation và module marketplace registration

---

## 7. Nguồn tham khảo

- [BMad Method GitHub](https://github.com/bmad-code-org/BMAD-METHOD) — Source code chính
- [BMad Builder](https://github.com/bmad-code-org/bmad-builder) — Module builder tools
- [BMad Module Template](https://github.com/bmad-code-org/bmad-module-template) — Starter template
- [BMad DeepWiki - Module System](https://deepwiki.com/bmad-code-org/BMAD-METHOD/6-module-system) — Architecture docs
- [BMad DeepWiki - Overview](https://deepwiki.com/bmad-code-org/BMAD-METHOD) — Full framework reference
- [Build Your First Module Tutorial](https://bmad-builder-docs.bmad-method.org/tutorials/build-your-first-module/) — Step-by-step guide
- [BMad Framework Overview](https://pasqualepillitteri.it/en/news/171/bmad-framework-claude-code-agile-development) — Third-party analysis

---

## 8. Phân tích chi tiết cấu trúc từng loại Skill BMad

### 8.1 Bảng tổng quan 7 skills phân tích

| Skill | Loại | Số stages | Output | Prerequisites | Pattern chính |
|-------|------|-----------|--------|---------------|---------------|
| bmad-product-brief | Analysis | 5 stages | brief.md | Không | Subagent fan-out, mode detection |
| bmad-create-prd | Document | 12 steps | prd.md | Không | Step-file, continuation, lookup table |
| bmad-create-ux-design | Specification | 14 steps | ux-design-spec.md | PRD | Step-file, collaborative design |
| bmad-create-architecture | Decision | 8 steps | architecture.md | PRD (bắt buộc) | Step-file, technical decisions |
| bmad-create-epics-stories | Decomposition | 4 steps | epics.md | PRD + Architecture | Step-file, requirements extraction |
| bmad-domain-research | Research | 6 steps | research/domain-*.md | Web search | Step-file, web research |
| bmad-dev-story | Implementation | 10 steps | (modify story) | Story spec file | XML workflow, no blocking |

### 8.2 Cấu trúc file chi tiết theo Tier

#### TIER 1: Complex (5-stage + scripts + headless)

**Mẫu chuẩn: bmad-create-prd (12 steps)**

```
bmad-create-prd/
├── SKILL.md                          # Master workflow + activation + routing
├── customize.toml                    # Workflow configuration surface
├── templates/
│   └── prd-template.md              # Output template với frontmatter
├── data/                             # CSV/MD classification data
│   ├── project-types.csv            # 11 project types + signals
│   ├── domain-complexity.csv        # 15 domains + signals
│   └── prd-purpose.md              # Philosophy guide
└── steps-c/                          # Sequential step files
    ├── step-01-init.md              # Init + input discovery
    ├── step-01b-continue.md         # Resume từ session trước
    ├── step-02-discovery.md         # Project classification
    ├── step-02b-vision.md           # Product vision
    ├── step-02c-executive-summary.md
    ├── step-03-success.md           # Success criteria
    ├── step-04-journeys.md          # User journey mapping
    ├── step-05-domain.md            # Domain-specific
    ├── step-06-innovation.md        # Innovation analysis
    ├── step-07-project-type.md      # Project-type specific
    ├── step-08-scoping.md           # MVP/Growth/Vision
    ├── step-09-functional.md        # Functional requirements
    ├── step-10-nonfunctional.md     # Non-functional requirements
    ├── step-11-polish.md            # Final review
    └── step-12-complete.md          # Completion & handoff
```

**Mẫu chuẩn: bmad-create-architecture (8 steps)**

```
bmad-create-architecture/
├── SKILL.md
├── customize.toml
├── architecture-decision-template.md  # Output template
├── data/
│   ├── domain-complexity.csv          # Shared với PRD
│   └── project-types.csv             # Shared với PRD
└── steps/
    ├── step-01-init.md               # PRD validation + discovery
    ├── step-01b-continue.md          # Resume
    ├── step-02-context.md            # Project context analysis
    ├── step-03-starter.md            # Starter template selection
    ├── step-04-decisions.md          # Arch decisions (ADR)
    ├── step-05-patterns.md           # Patterns & libraries
    ├── step-06-structure.md          # System decomposition
    ├── step-07-validation.md         # Validation vs PRD
    └── step-08-complete.md           # Handoff
```

**Mẫu HBC hiện có: hbc-create-business-flow-diagram (5 stages inline)**

```
hbc-create-business-flow-diagram/
├── SKILL.md                          # 5-stage workflow inline
├── customize.toml                    # Template path, output path, diagram type
├── templates/
│   └── D-06_business-flow-diagram_template.md
├── assets/
│   └── decision-log-template.md     # Decision log template
├── references/
│   └── headless-contract.md         # JSON return contract
└── scripts/
    ├── discover-planning-artifacts.py
    ├── validate-mermaid.py
    ├── check-fr-coverage.py
    └── tests/
        ├── __init__.py
        ├── run-tests.py
        ├── test_check-fr-coverage.py
        ├── test_discover-planning-artifacts.py
        └── test_validate-mermaid.py
```

#### TIER 2: Medium (3-stage inline hoặc step-file ngắn)

**Mẫu chuẩn: bmad-create-epics-and-stories (4 steps)**

```
bmad-create-epics-and-stories/
├── SKILL.md
├── customize.toml
├── templates/
│   └── epics-template.md            # Structured epic/story template
└── steps/
    ├── step-01-validate-prerequisites.md  # Validate PRD + Architecture
    ├── step-02-design-epics.md            # Epic design
    ├── step-03-create-stories.md          # Story creation
    └── step-04-final-validation.md        # Validation
```

#### TIER 3: Analysis/Research

**Mẫu chuẩn: bmad-domain-research (6 steps)**

```
bmad-domain-research/
├── SKILL.md                          # Quick topic discovery + routing
├── customize.toml
├── research.template.md              # Output template
└── domain-steps/
    ├── step-01-init.md              # Scope confirmation
    ├── step-02-domain-analysis.md   # Industry analysis
    ├── step-03-competitive-landscape.md
    ├── step-04-regulatory-focus.md
    ├── step-05-technical-trends.md
    └── step-06-research-synthesis.md
```

**Mẫu alternative: bmad-product-brief (5 stages, subagent)**

```
bmad-product-brief/
├── SKILL.md                          # 5-stage + subagent routing
├── customize.toml
├── bmad-manifest.json
├── resources/
│   └── brief-template.md            # 1-2 page brief template
├── prompts/                          # Subagent instructions
│   ├── contextual-discovery.md
│   ├── guided-elicitation.md
│   ├── draft-and-review.md
│   └── finalize.md
└── agents/                           # Specialized subagents
    ├── artifact-analyzer.md
    ├── opportunity-reviewer.md
    ├── skeptic-reviewer.md
    └── web-researcher.md
```

#### TIER 4: Implementation

**Mẫu chuẩn: bmad-dev-story (single-file XML)**

```
bmad-dev-story/
├── SKILL.md                          # 10-step XML workflow (ALL inline)
├── customize.toml
└── checklist.md                      # Definition-of-done checklist
```

### 8.3 Mandatory Execution Rules (áp dụng cho MỌI step-file skill)

```
🛑 NEVER generate content without user input
📖 ALWAYS read entire step file before action
🔄 When loading next step, ensure full file is read first
🚫 NEVER skip steps or optimize sequence
💾 ALWAYS update frontmatter when writing step output
🎯 ALWAYS follow exact instructions in step file
⏸️ ALWAYS halt at menus and wait for user input
📋 NEVER create mental todo lists from future steps
📋 YOU ARE A FACILITATOR, not a content generator
✅ YOU MUST ALWAYS SPEAK OUTPUT in communication_language
```

### 8.4 Continuation/Resume Pattern

**Detection:**
```
1. Check if output file exists
2. Read frontmatter → stepsCompleted array
3. If incomplete → load step-01b-continue.md
4. step-01b reads lookup table → determines next step
```

**Lookup Table (ví dụ PRD):**
```
step-01-init → step-02-discovery
step-02-discovery → step-02b-vision
step-02b-vision → step-02c-executive-summary
...
step-11-polish → step-12-complete
```

**step-01b behavior:**
- Reloads ALL `inputDocuments` (KHÔNG discovery mới!)
- Shows progress summary to user
- Halts for 'C' before proceeding

### 8.5 Menu Pattern (mọi step cuối)

```
[A] Advanced Elicitation — single deep-dive lens
[P] Party Mode — 3 parallel reviewer lenses
[C] Continue — proceed to next step
```

- A/P quay về menu sau khi hoàn thành
- Chỉ C mới advance sang step tiếp
- Frontmatter updated SAU KHI chọn C

### 8.6 Input Discovery Pattern

```
Tìm kiếm theo thứ tự:
1. {planning_artifacts}/**     (primary location)
2. {project_knowledge}/**      (docs folder)
3. docs/**                     (fallback)

Tìm kiếm theo format:
1. Whole file: *prd*.md, *architecture*.md
2. Sharded: *prd*/index.md, *architecture*/index.md
3. User confirmation TRƯỚC KHI load

Track tất cả files đã load vào inputDocuments array
```

### 8.7 Output Document Frontmatter Convention

```yaml
---
stepsCompleted: []        # Array step names đã hoàn thành
inputDocuments: []        # Array file paths đã load
workflowType: 'prd'       # Skill type identifier
lastStep: 1               # Current step number
# Skill-specific fields:
classification: ''        # PRD: project type
documentCounts: {}        # PRD: input doc counts
session_topic: ''         # Research: topic
research_goals: ''        # Research: goals
---
```

### 8.8 Customize.toml — Cấu trúc chuẩn

```toml
[workflow]
# Pre/post activation hooks
activation_steps_prepend = []
activation_steps_append = []

# Persistent context cho toàn session
persistent_facts = [
  "file:{project-root}/**/project-context.md",
]

# Skill-specific scalars
<doc_type>_template = "{skill-root}/templates/<template-file>"
<doc_type>_output_path = "{planning_artifacts}/<category>/<doc-id>-{project_name}/"

# Post-completion hook
on_complete = ""
```

### 8.9 Dependency Graph giữa các BMad Skills

```
Product Brief (bmad-product-brief)
    ↓
PRD (bmad-create-prd)  ← Domain Research (optional input)
    ↓ [requires PRD]
    ├→ UX Design (bmad-create-ux-design)
    ├→ Architecture (bmad-create-architecture)
    │
    └→ Epics & Stories (bmad-create-epics-and-stories)
         [requires PRD + Architecture, optional UX]
            ↓
        Dev Story (bmad-dev-story)
            [consumes story spec files]
```

---

## 9. Áp dụng vào HBLab: Blueprint cho từng D-xx Skill

### 9.1 Mapping D-xx → Tier + Step count

| Doc | Tên | Tier | Steps | Lý do |
|-----|-----|------|-------|-------|
| D-01 | 企画書 | 1-Complex | 8 | Multi-source: stakeholder input, budget, schedule, team, flows |
| D-02 | 要件定義書 | 1-Complex | 10 | Tương tự PRD: classification, discovery, FRs, NFRs, scoping |
| D-03 | 用語集 | 3-Simple | 2 | Extract từ tất cả docs hiện có + user input |
| D-04 | ユースケース記述 | 2-Medium | 4 | Từ D-02 requirements → use case narratives |
| D-05 | ユースケース図 | 3-Simple | 2 | Từ D-04 → PlantUML diagram generation |
| D-06 | Business Flow | 1-Complex | 5 | ĐÃ CÓ — giữ nguyên pattern hiện tại |
| D-07 | 運用シナリオ | 2-Medium | 3 | Từ D-02 + D-04 → operational scenarios |
| D-08 | 基本設計書 | 1-Complex | 6 | HUB: aggregates refs to D-09→D-20, feature mapping |
| D-09 | アーキテクチャ | 1-Complex | 8 | Tương tự bmad-create-architecture: ADR, C4, layers |
| D-10 | システム構成図 | 2-Medium | 3 | Từ D-09 → infra diagram (Mermaid flowchart) |
| D-11 | ディレクトリ構成図 | 3-Simple | 2 | Scan codebase + D-09 patterns → tree structure |
| D-12 | コーディング規約 | 2-Medium | 4 | Từ D-09 tech decisions + team conventions |
| D-13 | 採用技術一覧 | 3-Simple | 2 | Extract từ D-09 + package files |
| D-14 | 画面仕様書 | 2-Medium | 4 | Per-screen spec: layout, elements, actions, validation |
| D-15 | 外部IF設計書 | 2-Medium | 4 | Per-interface: endpoint, request/response, error codes |
| D-16 | 詳細設計書 | 2-Medium | 4 | Per-module: class diagram, function specs |
| D-17 | シーケンス図 | 3-Simple | 2 | Từ D-16 → Mermaid sequence diagrams |
| D-18 | クラス図 | 3-Simple | 2 | Từ D-16 → PlantUML class diagrams |
| D-19 | DB設計書/ER | 1-Complex | 5 | ĐÃ CÓ — giữ nguyên pattern hiện tại |
| D-20 | テーブル定義書 | 2-Medium | 3 | Từ D-19 ER → column-level detail |
| D-21 | API仕様書 | 2-Medium | 4 | Từ D-15 + D-16 → OpenAPI-style spec |
| D-22 | ログ設計書 | 3-Simple | 2 | Logging strategy + event catalog |
| D-23 | バッチスケジュール | 2-Medium | 3 | Batch jobs: schedule, dependencies, Gantt |
| D-24 | 運用設計書 | 2-Medium | 4 | Monitoring, incident response, backup |
| D-25 | 移行設計書 | 2-Medium | 4 | Data mapping, migration plan, rollback |
| D-26 | テスト計画書 | 2-Medium | 4 | Test strategy, scope, environments, entry/exit |
| D-27 | テスト仕様書 | 2-Medium | 3 | Test cases: steps, expected results, priority |
| D-28 | 運用・保守マニュアル | 3-Simple | 2 | Startup/shutdown, monitoring, troubleshooting |
| D-29 | プロジェクトサマリー | 3-Simple | 2 | Aggregate từ all docs → executive summary |
| D-31 | 運用部門マニュアル | 2-Medium | 3 | Department-specific workflows, screens |
| D-00 | README | 3-Simple | 2 | Extract từ D-11, D-12, D-13 → README |

### 9.2 Skeleton chuẩn cho mỗi Tier

#### Tier 1 Skeleton (Complex — 5+ steps)

```
hbc-create-<doc>/
├── SKILL.md                    # Activation + routing (KHÔNG chứa workflow inline)
├── customize.toml              # Template, output, on_complete
├── templates/
│   └── D-xx_<name>_template.md # Bundled template
├── assets/
│   └── decision-log-template.md
├── references/
│   └── headless-contract.md    # JSON contract cho headless mode
├── data/                       # Classification CSVs (nếu cần)
│   └── <classification>.csv
├── scripts/                    # Deterministic validators
│   ├── discover-planning-artifacts.py
│   ├── validate-<type>.py
│   └── tests/
│       └── test_*.py
└── steps/
    ├── step-01-init.md         # Init + input discovery + resume detect
    ├── step-01b-continue.md    # Resume from prior session
    ├── step-02-discovery.md    # Extract content from sources
    ├── step-03-generation.md   # Generate document sections
    ├── step-04-validation.md   # Script + LLM validation
    └── step-05-complete.md     # Save + handoff
```

#### Tier 2 Skeleton (Medium — 3-4 steps)

```
hbc-create-<doc>/
├── SKILL.md                    # Activation + 3-stage workflow INLINE
├── customize.toml
├── templates/
│   └── D-xx_<name>_template.md
└── steps/                      # Optional — có thể inline trong SKILL.md
    ├── step-01-prerequisites.md
    ├── step-02-generation.md
    └── step-03-validation.md
```

#### Tier 3 Skeleton (Simple — 2 stages)

```
hbc-create-<doc>/
├── SKILL.md                    # Activation + 2-stage workflow ALL INLINE
├── customize.toml
└── templates/
    └── D-xx_<name>_template.md
```

### 9.3 Ví dụ SKILL.md Structure cho Tier 2 (D-13 Tech Stack)

```markdown
---
name: hbc-create-tech-stack
description: "Generate D-13 採用技術一覧 (Technology Stack List).
  Use when 'create tech stack', 'tạo D-13', '採用技術一覧を作成'."
---

# Create Technology Stack List (D-13)

## Overview
Scans architecture (D-09), package files, and project context
to produce a categorized technology inventory with adoption rationale.

## Conventions
[Standard BMad block]

## Language Rules
[Standard i18n block]

## On Activation
[6-step standard sequence]

## Headless Mode
`-H` / `--headless`. Flags: `--arch-path`, `--scan-packages`.
Blockers: `architecture_missing`, `no_technologies_found`.

## Workflow

### Stage 1: Prerequisites
- Scan for D-09 Architecture (required), D-00 README (optional)
- Scan for package.json, requirements.txt, go.mod, Cargo.toml
- Initialize from {workflow.tech_stack_template}
- Update frontmatter stepsCompleted: [stage-1]

### Stage 2: Discovery & Generation
- Extract technologies from Architecture ADR + tech decisions
- Extract from package files (name, version)
- Categorize: Frontend / Backend / Database / Infrastructure / CI-CD / Other
- For each: fill adoption_reason from Architecture rationale
- Present for confirmation
- Menu [A/P/C]
- Update frontmatter stepsCompleted: [stage-1, stage-2]

### Stage 3: Validation & Save
- Check: all categories have entries?
- Check: versions are specific (not "latest")?
- Check: adoption_reason filled for all?
- Save to {workflow.tech_stack_output_path}
- Declare downstream: D-00 README, D-12 Coding Standards

## On Complete
Read {workflow.on_complete}. If non-empty, follow. Otherwise invoke bmad-help.
```
