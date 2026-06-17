---
name: hbc-task-breakdown
description: "Break down design artifacts into granular TDD tasks. Use when user says 'task breakdown', 'phân chia task', or agent menu [TB]."
---

# Task Breakdown

## Overview

Break down Phase 2 design artifacts into granular, implementable tasks ordered for TDD execution. Each task maps to one TDD cycle (RED → GREEN → REFACTOR) in `hbc-implement`, scoped to approximately ≤ `{workflow.max_hours_per_task}` hours of work.

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

> **Resolve active feature (B):** arg `feature=<slug>` → active feature trong phiên → hỏi (headless: bắt buộc, thiếu → blocked `feature_required`). Thay `{feature}` trong mọi path workflow.

## Stage 1: Prerequisites

**Phase-entry gate (enforced, overridable).** This skill opens Phase 3. Before doing anything, verify the **Phase 2 gate PASSED for the active feature** — run `hbc-phase-gate` for phase 2 headless (`-H`) **with `feature={feature}`** and read `overall_status`. If it is not `PASSED` (FAILED / WARNING / never run), **HALT** and tell the user Phase 2 is not closed for this feature, citing the failing items. Proceed only if the user explicitly overrides (e.g. "override gate" / "proceed anyway") — record that an override was used in the task-breakdown intro. In headless mode, a non-PASSED Phase 2 gate returns `blocked` (no override). This is the runtime teeth behind the gated phase ordering — do not silently build tasks on an unclosed design phase.

**Entry check — project-context.md presence (E-2 warn-gate).** Before loading design artifacts, check whether `project-context.md` exists. If it is **absent**, surface this explicitly up front — do NOT silently proceed to produce incomplete infrastructure tasks. Warn: _"Không tìm thấy project-context.md → Infrastructure tasks (project setup, config, CI/CD) sẽ bị bỏ qua, task breakdown có thể thiếu phần hạ tầng. Chạy `bmad-generate-project-context` nếu cần infra coverage."_ This is a warn-gate (not a hard halt) — record the missing-context note in the task-breakdown intro and continue, so the gap is visible rather than implied. Stage 2 Infrastructure handling (E-2) then honors the same fact.

Load all Phase 2 design artifacts as input, resolving each by its scope:
- **D-27** (test specification) — test cases to assign to tasks. **Per-feature**: `{d27_path} = {output_folder}/features/{feature}/planning-artifacts/D-27-*.md`.
- **D-19** (database design) — entities to implement. **DUAL** (path-existence precedence): prefer the per-feature override `{output_folder}/features/{feature}/planning-artifacts/D-19-{feature}-*.md` if it exists, else the shared baseline `{output_folder}/shared/erd/D-19-*.md`. Bind the resolved path as `{d19_path}`.
- **D-12** (coding standards) — apply during implementation. **Shared**: `{output_folder}/shared/coding-standards/D-12-*.md`.
- **D-21** (API spec, optional) — endpoints to implement. **DUAL** (same precedence as D-19): per-feature override `{output_folder}/features/{feature}/planning-artifacts/D-21-{feature}-*.md` else shared baseline `{output_folder}/shared/api/D-21-*.md`.

**Dual-path resolution log (D-19 / D-21).** For each DUAL artifact, after applying path-existence precedence, emit a log line stating which path was chosen so the resolution is auditable — e.g. _"D-19: dùng per-feature override `…/features/{feature}/planning-artifacts/D-19-{feature}-*.md`"_ or _"D-19: override không tồn tại → dùng shared baseline `…/shared/erd/D-19-*.md`"_; likewise for D-21 (note when D-21 is absent in both, since it is optional). Record these lines in the `.decision-log`/task-breakdown intro so a reader can tell which source actually drove the breakdown.

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
- Task granularity is appropriate (≤ `{workflow.max_hours_per_task}` hours per task).

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

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"Task breakdown đã cập nhật. Chạy `hbc-traceability impact` để đồng bộ test/code phụ thuộc?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly (it will cascade downstream). Default is false.
