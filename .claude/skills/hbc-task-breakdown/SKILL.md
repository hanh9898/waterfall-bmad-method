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

Decompose design artifacts into tasks:

- **Entity tasks** — one task per D-19 entity (model + migration + basic CRUD).
- **API tasks** — one task per D-21 endpoint group (if applicable).
- **Integration tasks** — cross-entity workflows derived from D-06 business flows.
- **Infrastructure tasks** — project setup, configuration, CI/CD (from project-context.md).

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
