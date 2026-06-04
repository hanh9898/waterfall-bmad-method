---
name: hbc-task-breakdown
description: "Break down design artifacts into granular TDD tasks. Use when user says 'task breakdown', 'タスク分解', 'phân chia task', or agent menu [TB]."
---

# Task Breakdown

## Overview

Break down Phase 2 design artifacts into granular, implementable tasks ordered for TDD execution. Each task maps to one TDD cycle (RED → GREEN → REFACTOR) in `hbc-implement`, scoped to approximately 1-4 hours of work.

Five-stage workflow: Prerequisites → Analysis → Generation → Validation → Save. Supports headless mode. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (re-prioritize/split tasks), `validate` (check coverage). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

## Stage 1: Prerequisites

Load all Phase 2 design artifacts as input:
- **D-19** (database design) — entities to implement.
- **D-27** (test specification) — test cases to assign to tasks.
- **D-12** (coding standards) — apply during implementation.
- **D-21** (API spec, optional) — endpoints to implement.

Check if `task-breakdown.md` already exists. If so, offer to regenerate (destructive) or update (additive).

## Stage 2: Analysis

Decompose design artifacts into tasks. The categories below are a **starting checklist, not a closed set** (R-2): derive task types from whichever design artifacts actually exist, and add categories the project needs. Do NOT force every piece of work into "entity" — UI/admin screens and standalone behaviors are first-class.

- **Entity tasks** — per D-19 entity. Includes model + migration **and any business logic on that entity** (validation, key generation/hashing, state transitions, derived fields) — NOT just basic CRUD. Split a complex entity into CRUD + behavior tasks when the logic is non-trivial.
- **API tasks** — one task per D-21 endpoint group (if applicable).
- **UI / Screen tasks** — one task per admin/back-office screen, wizard, or page (e.g. from D-14 screen specs or Odoo views/wizards). Critical for systems where the backend UI is core; do not fold these into entity CRUD.
- **Behavior / Service tasks** — logic that does not belong to a single entity: background jobs, schedulers, domain services, cross-cutting policies, lifecycle/admin operations (e.g. key rotation, approval gates).
- **Integration tasks** — cross-entity workflows derived from D-06 business flows.
- **Infrastructure tasks** — project setup, configuration, CI/CD (from project-context.md).
  - **E-2 — không fail im lặng:** nếu `project-context.md` không tồn tại, KHÔNG bỏ qua infra một cách im lặng. Báo rõ cho user: _"Không tìm thấy project-context.md → bỏ qua phần Infrastructure tasks. Chạy `bmad-generate-project-context` nếu cần infra coverage."_ rồi mới tiếp tục.

**Taxonomy completeness check:** trước khi chốt, rà từng artifact đầu vào (D-14 screens, D-06 flows, D-19 entities, D-21 endpoints, REQ có mặt admin/lifecycle) và tự hỏi "loại task nào sinh ra từ đây?" — nếu một artifact không map sang task nào, nêu rõ lý do, đừng bỏ sót im lặng.

For each task, identify:
- `design_ref` — which D-19 entity or D-21 endpoint group this implements.
- `test_refs` — which TC-xxx IDs from D-27 cover this task.
- `dependencies` — which other tasks must complete first.
- `priority` — based on dependency order (foundation first, dependent later).

Present analysis as a dependency graph for confirmation.

## Stage 3: Generation

Write to `{workflow.output_dir}/task-breakdown.md`:

```markdown
---
title: "{project_name} Task Breakdown"
total_tasks: 0
completed: 0
coverage_pct: 0
updated: ""
---

## Task List

| task_id | description | design_ref | test_refs | priority | status | dependencies |
```

Ensure:
- Tasks ordered by dependency (no task depends on a later-listed task).
- Every D-19 entity has at least one task.
- Every TC-xxx from D-27 is assigned to at least one task.
- Task granularity is appropriate (1-4 hours per task).

## Stage 4: Validation

Run deterministic validator:

```
python3 {workflow.validation_script} "{workflow.output_dir}/task-breakdown.md" --d19 "{d19_path}" --d27 "{d27_path}"
```

Checks: all entities covered, all test cases assigned, no circular dependencies, task IDs unique and sequential.

**LLM judgment checks:**
- Task descriptions are actionable and specific.
- Dependency ordering is logical.
- No task is too large (should decompose further).

## Stage 5: Save and Handoff

Finalize document. Suggest next: _"Task breakdown complete with {n} tasks. Start implementation: `hbc-implement` [IM]."_
