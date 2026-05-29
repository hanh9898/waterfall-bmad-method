---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - _bmad-output/planning-artifacts/research/technical-bmad-custom-module-design-research-2026-05-20.md
session_topic: 'Tối ưu hóa thiết kế module system cho bộ tài liệu HBLab D-00→D-31'
session_goals: 'Khám phá ý tưởng đột phá về tổ chức module, workflow chain, automation, và cải tiến vượt ngoài research ban đầu'
selected_approach: 'ai-recommended'
techniques_used: ['Assumption Reversal']
ideas_generated:
  - 'Grouping #1: Composite Skill Pattern'
  - 'Grouping #2: Hub Scaffold — REJECTED'
  - 'Flow #1: Strict Pipeline Enforcement'
  - 'Flow #3: Soft Dependency — REJECTED'
  - 'Module #1: Ops as Optional Module'
  - 'Module #2: Full Implementation Module'
  - 'Module #3: Waterfall Implementation Module'
  - 'Anti-Pattern #1: Blind BMad Copy — REJECTED'
context_file: '_bmad-output/planning-artifacts/research/technical-bmad-custom-module-design-research-2026-05-20.md'
session_status: 'in-progress — Phase 1 complete, Phase 2+3 pending'
---

# Brainstorming Session Results

**Facilitator:** Hanhnt2
**Date:** 2026-05-20

## Session Overview

**Chủ đề:** Tối ưu hóa thiết kế module system cho bộ tài liệu HBLab D-00→D-31
**Mục tiêu:** Khám phá ý tưởng đột phá về tổ chức module, workflow chain, automation, và cải tiến vượt ngoài research ban đầu

### Context Guidance

_Research document đã phân tích 7 BMad skills gốc, đề xuất 3 module (hbc-plan, hbc-design, hbc-ops), 4 tier complexity, shared scripts pattern, và blueprint cho 30 D-xx skills. Session này tập trung vào những ý tưởng chưa được khai phá._

### Session Setup

_Session mới, sử dụng research output làm context nền tảng._

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Thiết kế module system với focus vào phá giả định và mượn pattern ngoài domain

**Recommended Techniques:**

- **Assumption Reversal:** Thách thức giả định trong research để tìm thiết kế tốt hơn ✅ DONE
- **Cross-Pollination:** Mượn pattern từ CI/CD, Design System, Game Engine ⏳ PENDING
- **Morphological Analysis:** Tổ hợp tham số thành phương án thiết kế cụ thể ⏳ PENDING

## Technique Execution: Phase 1 — Assumption Reversal

### Giả định #1: "Mỗi template D-xx = 1 skill riêng biệt" → CHALLENGED

**[Grouping #1]**: Composite Skill Pattern
_Concept_: Gộp các templates có cùng bản chất thành 1 skill với flag `--type`, giảm từ ~30 skills xuống ~15-18 skills.
_Novelty_: BMad gốc mỗi skill = 1 artifact. HBLab phá pattern này vì nhiều D-xx chỉ khác nhau ở template, workflow gần như giống nhau.

Nhóm gộp tự nhiên:

| Composite Skill | Templates gộp | Lý do |
|----------------|---------------|-------|
| `hbc-create-diagram` | D-05, D-17, D-18 | Cùng Mermaid/PlantUML generation |
| `hbc-create-db-design` | D-19 + D-20 | ER luôn kèm Table Definition |
| `hbc-create-manual` | D-28 + D-31 | Cùng là manual cho end-user |
| `hbc-create-interface-spec` | D-15 + D-21 | External IF → API spec, cùng workflow |
| `hbc-create-test-docs` | D-26 + D-27 | Test plan luôn kèm test spec |

### Giả định #2: "1 skill có thể tạo nhiều files cùng lúc" → REJECTED

**[Grouping #2]**: Hub Scaffold — **REJECTED**
_Lý do bác bỏ_: Skeleton files sẽ outdated khi downstream skill chạy, gây confusion cho team. Giữ nguyên rule 1 skill = 1 output artifact.

### Giả định #3: "Dependency có thể soft/lazy-load" → REJECTED

**[Flow #3]**: Soft Dependency — **REJECTED**
_Lý do_: Team HBLab tuân thủ flow top-down. Hard dependency giữ chất lượng downstream docs.

**[Flow #1]**: Strict Pipeline Enforcement — **ACCEPTED**
_Concept_: Mỗi skill validate upstream docs tồn tại và đầy đủ trước khi chạy. HALT nếu thiếu. Không fallback sang elicitation.
_Novelty_: Khác BMad gốc (luôn có fallback). HBLab enforce quality chain.

### Giả định #4: "Module chia 3 theo phase" → REVISED to 4 modules

**[Module #1]**: Ops as Optional Module — **ACCEPTED**
_Concept_: Ops docs (D-22→D-28, D-31) không phải project nào cũng cần. Tách thành module optional.
_Novelty_: BMad bundle tất cả vào BMM. HBLab cho team chọn module theo scale dự án.

Project profiles:

| Profile | Modules |
|---------|---------|
| MVP/PoC | hbc-plan only |
| Standard | hbc-plan + hbc-design |
| Enterprise | hbc-plan + hbc-design + hbc-impl + hbc-ops |

### Giả định #5: "Implementation = Agile ceremonies" → REJECTED

**[Anti-Pattern #1]**: Blind BMad Copy — **REJECTED**
_Lý do_: BMad là agile. HBLab dùng waterfall/V-model. Không copy sprint-planning, sprint-status, retrospective.

**[Module #2]**: Full Implementation Module — **ACCEPTED**
_Concept_: hbc-impl gồm cả D-xx docs + workflow skills riêng, custom cho flow HBLab.

**[Module #3]**: Waterfall Implementation Module — **ACCEPTED**
_Concept_: hbc-impl thiết kế theo V-model waterfall. Task-based từ D-16, milestone tracking từ D-01, acceptance verify từ D-02.
_Novelty_: BMad variant đầu tiên cho waterfall + AI-driven development.

Waterfall workflow skills:

| Skill | Mục đích | Thay thế agile |
|-------|----------|----------------|
| hbc-task-breakdown | Chia D-16 → task list cho dev | Thay sprint-planning |
| hbc-code-review | Review code theo D-12 + D-16 | Giữ nguyên |
| hbc-test-execution | Chạy test theo D-27, ghi kết quả | Thay QA agile |
| hbc-milestone-status | Track tiến độ theo D-01 milestones | Thay sprint-status |
| hbc-acceptance-check | Verify deliverables vs D-02 | Thay retrospective |

## Kết quả Phase 1: Module Architecture (Revised)

| Module | Phase | D-xx Docs | Workflow Skills | Tính chất |
|--------|-------|-----------|-----------------|-----------|
| **hbc-plan** | 1-Planning | D-01→D-07 (7) | — | Bắt buộc |
| **hbc-design** | 2-Design | D-08→D-21 (14) | — | Bắt buộc |
| **hbc-impl** | 3-Implementation | D-00, D-26, D-27, D-29 (4) | task-breakdown, code-review, test-execution, milestone-status, acceptance-check (5) | Bắt buộc |
| **hbc-ops** | 4-Operations | D-22→D-25, D-28, D-31 (7) | — | Optional |

**Tổng: 32 D-xx docs + 5 workflow skills = ~25 skills (sau composite grouping)**

## Pending Phases

- **Phase 2: Cross-Pollination** — Mượn pattern từ CI/CD Pipeline, Design System, Game Engine
- **Phase 3: Morphological Analysis** — Tổ hợp tham số thành phương án thiết kế cụ thể
