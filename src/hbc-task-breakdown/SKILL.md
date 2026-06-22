---
name: hbc-task-breakdown
description: "Break down design artifacts into granular TDD tasks. Use when user says 'task breakdown', 'phân chia task', or agent menu [TB]."
---

# Task Breakdown

## Overview

Break down Phase 2 design artifacts into granular **vertical-slice** tasks ordered for TDD. Each task slices through model + behavior + (where relevant) UI — never a horizontal layer — satisfies INVEST, is split with SPIDR, and carries a Kent-Beck-style **test list** (B4-1; full catalog in `references/splitting-patterns.md`). Each task = one TDD cycle (RED → GREEN → REFACTOR) in `hbc-implement`, ≤ `{workflow.max_hours_per_task}` hours.

Workflow: Prerequisites → Input gate → Analysis → **Mapping review** → Generation → Validation → Semantic review → Save. Headless-capable. Python 3.10+.

**Args:** `create` (default), `update` (re-prioritize/split tasks), `validate` (check coverage). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths resolve from the skill root; `{skill-root}` = this skill's installed dir.
- `{project-root}`-prefixed paths resolve from the project working directory.

## Autonomy (A5 / B4-8)

Separate **mechanical** decisions from **domain** decisions. Mechanical — dependency ordering, id numbering, formatting, which category a task belongs to — decide and proceed. Domain — **how to slice a REQ**, where a SPIDR split falls, whether a behavior is its own slice, sizing, its test list — **ASK; never invent a default**.

**No silent default-override (B4-5).** If you would override a default, a stated preference, or a design decision (e.g. drop a slice, merge two REQs into one task, change a sizing cap), **HALT** and **log the reason in `.decision-log.md` at THIS skill** before proceeding — not only in the agent layer. An unlogged override is a defect.

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision and return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option, log it to the decision log as an `ASSUMPTION`, and continue. Never block on the first question.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md`; domain decisions follow the Autonomy mode above.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> **Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask (headless: required, missing → blocked `feature_required`). Substitute `{feature}` in every workflow path.

## Stage 1: Prerequisites

**Phase-entry gate (enforced, overridable).** This skill opens Phase 3. Run `hbc-phase-gate` for phase 2 headless (`-H`) **with `feature={feature}`**; if `overall_status` is not `PASSED`, **HALT** and cite the failing items. Proceed only on explicit user override (record it in the intro). Headless: non-PASSED returns `blocked` (no override).

**project-context.md warn-gate (E-2).** If absent, warn up front that Infrastructure tasks (setup/config/CI-CD) will be skipped and the breakdown may miss infra (suggest `bmad-generate-project-context`). Warn-gate, not a halt — record the note, continue.

Initialize `.decision-log.md` alongside the output (canonical memory; where B4-5 overrides are logged). If `task-breakdown.md` already exists, offer regenerate (destructive) or update (→ Update Mode).

## Stage 1b: Input set + sufficiency gate (B4-2 — HALT before generate)

A complete breakdown is grounded in **four input dimensions** (B4-2 keeps all four) — gather and load each before any task is generated:

- **D-02 requirements** — the REQ set every task must trace to. Missing D-02 → cannot check coverage (headless: blocked `no_requirements`).
- **D-06 business-flow paths** — vertical slices follow flow paths (the SPIDR **Path** axis).
- **Acceptance criteria per REQ** — what "done" means for each slice's test list (from D-02 §AC / decision log).
- **Code-reality classification** — read the real code/models and classify each entity/endpoint/screen **NEW / CHANGE / already-exists**; never assume greenfield. A CHANGE/already-exists slice must not re-create what exists.

Also load (as available) the implementation inputs: **D-27** (test cases to assign), **D-19** (entities — DUAL: per-feature override else shared baseline), **D-12** (coding standards), **D-21** (API, optional, DUAL), and any **ADR** (optional, advisory — forward-ref to T2.5, never block on absence). For each DUAL artifact log the resolved path (or that an optional one is absent).

**Sufficiency gate.** Before generating, judge whether the input is enough to slice without guessing. If you **suspect a dimension is missing or stale** (no D-06 paths, no acceptance criteria, code not classified), **HALT** and ask — do not generate blind. Headless: Autonomy mode (`--strict` → blocked `input_insufficient`; `--assumptions-allowed` → log the gap + assumption, continue). The Stage 4 coverage script reports `input_gaps` as a backstop, but the judgment to halt is here.

## Stage 2: Analysis

Decompose into **vertical-slice** tasks. Task types are a **starting checklist, not a closed set** (R-2): derive them from whichever artifacts exist — entity (model+migration **+ its business logic**, not just CRUD), API (per D-21 group), UI/screen (first-class — do not fold into CRUD), behavior/service (jobs, schedulers, lifecycle/admin ops, cross-cutting policies), integration (D-06 flows), infrastructure (project-context.md; honor the E-2 warn-gate). Do NOT force everything into "entity". When a candidate task is too large or looks like a horizontal layer, split it with **SPIDR** and the vertical-slice patterns in `references/splitting-patterns.md`, then run INVEST on each result.

For each task, identify `req_refs` (REQ(s) sliced — canonical ids), `design_ref` (D-19 entity / D-21 group), `test_refs` (TC-xxx), a Kent-Beck **test list** (B4-1, see references), a **code-reality tag** (NEW / CHANGE / already-exists, from Stage 1b — so `hbc-implement` does not duplicate existing code), `dependencies`, and `priority` (foundation first).

## Stage 2b: Mapping review (B4-6 — HARD gate, ASK before generate)

**Before writing any task**, present a **mapping table** to the user and get explicit confirmation — this is a hard gate, not a soft "look ok?". It is the direct fix for the RCA root-cause (slices silently missed). Build the table from the loaded inputs:

| source artifact | item (path / REQ-facet / entity / screen) | → slice (task) |
|---|---|---|

One row per D-06 path, per REQ facet (read/write/admin/lifecycle), per D-19 entity, per D-21 group, per D-14 screen. Every source item maps to a named slice — or is **explicitly** marked out-of-scope with a reason. **Do not generate tasks until the user confirms the mapping** — that is exactly where a missed slice hides. Headless: Autonomy mode (`--strict` → blocked `mapping_unconfirmed`; `--assumptions-allowed` → log the drafted mapping and continue). Record the confirmed mapping to the decision log.

## Stage 3: Generation

Write to `{workflow.output_dir}/task-breakdown.md` with a frontmatter `sources:` block naming the four input dimensions (so the coverage script sees the input set) and a task table:

```markdown
| task_id | description | req_refs | design_ref | test_refs | code_reality | test_list | priority | status | dependencies |
```

Ensure: dependency-ordered (none depends on a later-listed task); **every D-02 REQ covered by ≥1 task** (B4-7); every D-19 entity has ≥1 task; every D-27 TC-xxx assigned; each task carries a test list; granularity ≤ `{workflow.max_hours_per_task}` h.

## Stage 4: Validation

Run both scripts, then LLM judgment:

```
python3 {workflow.validation_script} "{workflow.output_dir}/task-breakdown.md" --d19 "{d19_path}" --d27 "{d27_path}"
python3 {workflow.coverage_script} "{workflow.output_dir}/task-breakdown.md" --project-root {project-root} --d02 "{d02_path}"
```

`validate-task-breakdown.py` checks task-id uniqueness, dependency ordering, D-19 entity coverage (design_ref column), D-27 assignment; returns `churn`. `check-task-coverage.py` is **advisory** (the blocking REQ↔task↔design reconcile is `hbc-check-implementation-readiness` [IR], B13-2) and returns the machine **two-way 100%-rule** `two_way_coverage` — a view over the TA.1 build-graph (`references/two-way-coverage.md`): `reqs_without_task` (B4-7), `orphan_tasks` (TA.5 — tasks citing only dangling REQs), `two_way_complete` (both empty), and `input_gaps` (B4-2). Slash-shorthand `REQ-005/006/007` expands so dense cells aren't false-flagged; a missing REQ → add a slice or mark out-of-scope, never silently drop. If a script is unavailable, fall back to LLM-only validation.

**LLM judgment:** each task is a genuine vertical slice (INVEST); SPIDR splits are sound; the test list is concrete and behavioral; no task is too large; dependency ordering is logical.

## Stage 4b: STALE re-derive (B4-3 — advisory, forward-ref T2.4)

If this is an update and an **upstream input changed** (D-02/D-06/D-19 version newer than the breakdown's recorded `sources:` versions), note the breakdown may be stale and **re-derive the affected slices** — re-run Stage 2b mapping review for the changed area. Advisory only; the real dirty-set engine is T2.4 (interim) / TA.1 (kernel) — do not build a tracker here.

## Stage 4c: Semantic Review (Layer 2)

Structural validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** — challenge each slice: genuinely vertical (not a horizontal layer)? Every REQ gets value from some slice? Each test list real and behavioral? Apply the **facet-split discipline**: a REQ with an admin/lifecycle/write facet (approval, key rotation, re-sync) needs its own slice + test-list items, or be explicitly out-of-scope. List unresolved concerns in `openFacets`. Set `semanticReview.status: passed` **only when `openFacets` is empty AND the user signs off** (headless: Autonomy mode); else `pending`. The Phase-3 gate REVIEW item enforces it.

## Stage 5: Save and Handoff

Finalize — update frontmatter (`total_tasks`, `coverage_pct`, `updated`, `semanticReview`). Audit decision-log entries (incl. any B4-5 overrides) against the breakdown — each reflected or explicitly set aside. Append the closing session. Suggest next: _"Task breakdown complete ({n} tasks). Start `hbc-implement` [IM]."_ Headless: return JSON per `references/headless-contract.md`.

## Update Mode

When updating an existing breakdown: load it as baseline, present what changes, re-run Stage 2b mapping review for any added/changed REQ, then Stage 3 → 4 → 4b → 4c.

**Anti-churn (T2.11).** Bump the version **once per session**, not per edit. The validator returns `churn` (`revisions` vs `threshold`); when `churn.high_churn` is true the model isn't frozen — surface it and suggest `maturity: exploratory` or a `[DSC]` model-spike instead of another bump.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), skip this whole section — prevents the update→sync→update loop.
- **Hybrid (default):** after a successful update, suggest running `hbc-traceability impact` to sync dependent tests/code.
- **Auto-chained:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly. Default false.
