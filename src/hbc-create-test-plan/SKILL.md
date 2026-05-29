---
name: hbc-create-test-plan
description: "Generate D-26 Test Plan with strategy, scope, and schedule. Use when user says 'test plan', 'テスト計画書', 'kế hoạch test', or agent menu [TP]."
---

# Create Test Plan

## Overview

Generate D-26 テスト計画書 (Test Plan) — test strategy, scope, schedule, environment setup, entry/exit criteria, and risk assessment. This is the strategic "WHAT to test" document; D-27 Test Specification covers the detailed "HOW."

Five-stage workflow: Prerequisites → Discovery → Generation → Validation → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (revise existing D-26), `validate` (check existing D-26). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons).

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

## Open Floor

Before structured discovery, invite the user to share what they already know about testing strategy — priorities, constraints, known risks, team context. Absorb this before proceeding to Stage 1.

## Stage 1: Prerequisites

1a. **Source scan.** Run pre-pass to discover project state:

```
python3 {workflow.scan_script} --project-root {project-root} --output-dir {workflow.output_dir}
```

Returns JSON with `state` (fresh/resume/update), `existing_d26`, `d02_path`, `d06_path`, `framework`, and `project_context_path`. Use this to route:
   - **Fresh** — no prior D-26. Proceed to Stage 2.
   - **Resume** — partial D-26 found. Read `.decision-log.md` first for context recovery. Show summary, offer resume or restart.
   - **Update** — complete D-26 exists. Read `.decision-log.md` first for context recovery. Show what to update, load as baseline.

   If the scan script is unavailable, ask the user for source document paths and proceed with manual state detection.

1b. **Source inventory.** D-02 (requirements) is the primary input — test scope derives from requirement scope. D-06 (business flow) informs integration and E2E test scenarios. Load both as context.

1c. **Intent gate.** Confirm test plan (strategy), not test specification (detailed cases). If user wants cases: redirect to `hbc-create-test-spec`. Once intent is confirmed, initialize `.decision-log.md` alongside the output — create if absent, append session heading if present. Canonical memory for this workflow.

1d. **Brainstorming suggestion** (interactive only, Fresh state only). If D-02 reveals complex business logic or high-risk areas, suggest: _"Requirements có nhiều edge cases — muốn chạy `bmad-brainstorming` trước để brainstorm risk areas và test scenarios không? Kết quả sẽ feed vào D-26 test strategy."_ If declined or in headless mode, proceed. If accepted, pause for separate brainstorming session. If a brainstorming session file exists in `{output_folder}/brainstorming/`, load relevant risk/scenario ideas as input for test strategy.

## Stage 2: Discovery

Discover test strategy covering scope, levels, approach, environment, team, schedule, entry/exit criteria, and risk. Pre-populate from D-02 and `project-context.md` where available. At each area boundary, soft-gate: _"Anything else on [area], or move to [next]?"_

Capture any D-27 material (specific test case ideas) to decision log without interrupting the strategy flow.

**Compaction flush:** Write test levels, scope boundaries, and key decisions to decision log.

## Stage 3: Generation

Populate `{workflow.template_path}` with discovered content. Write to `{workflow.output_dir}/D-26-{project_name}-test-plan.md`. Ensure:

- Test scope maps to D-02 requirement scope — every in-scope area has a test approach.
- Entry/exit criteria include measurable thresholds (use `{workflow.coverage_threshold}` config).
- Schedule includes a Mermaid Gantt chart for visual timeline.
- Risk table has likelihood/impact ratings and mitigation actions.
- E2E test approach references `{workflow.e2e_framework}` if configured.

**Revision history:** If Update mode, detect scope-of-change:
- Same strategy, polish only → append note, no version bump.
- New/changed strategy → new row, bump version.

**Compaction flush:** Write section count and version to decision log.

**Parallel-lens menu:** After generation, offer `[A]` Advanced (deeper risk analysis, edge case coverage gaps) / `[P]` Party Mode (multi-agent test strategy review) / `[C]` Continue.

## Stage 4: Validation

Run deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-26-{project_name}-test-plan.md"
```

Script checks: all required sections present and non-empty, entry/exit criteria defined, risk table has entries, schedule section is non-empty. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable, fall back to LLM-only validation.

**LLM judgment checks:**
- Test levels are appropriate for the project complexity.
- Entry/exit criteria are realistic and measurable.
- Risk assessment covers technical AND process risks.
- Schedule is realistic given team size and project scope.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write validation results summary to decision log.

**Parallel-lens menu:** `[A]` Advanced (test strategy completeness) / `[P]` Party Mode / `[C]` Continue.

## Stage 5: Save and Handoff

Finalize document — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`). Audit decision-log entries against D-26. Append closing session.

Write `test-plan-distillate.json` alongside D-26 — `{"strategy": ..., "scope": ..., "entry_exit": ..., "risks": [...]}` for downstream D-27 consumption.

If `{workflow.on_complete}` is non-empty, run it after saving.

Suggest next steps: _"D-26 complete. Recommended: create D-27 Test Specification (`hbc-create-test-spec` [TS]) for detailed test cases. After both, run Phase 2 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.
