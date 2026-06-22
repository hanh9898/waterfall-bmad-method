---
name: hbc-create-test-plan
description: "Generate D-26 Test Plan with strategy, scope, and schedule. Use when user says 'test plan', 'kế hoạch test', or agent menu [TP]."
---

# Create Test Plan

## Overview

Generate D-26 (Test Plan) — test strategy, scope, schedule, environment, entry/exit criteria, and risk. The strategic "WHAT to test"; D-27 covers the detailed "HOW." Each in-scope area states a test technique linked to D-27 (B9-4). Risk likelihood/impact is **proposed by the LLM, confirmed by the user** (B9-2). The schedule is never fabricated (B9-1); in/out-scope is **confirmed with the user before the plan body is generated** (B9-3). Doc structure follows **ISO/IEC/IEEE 29119-3** (B9 / principle #6; IEEE 829 withdrawn 2013 — historical naming reference only).

Workflow: Prerequisites → Scope confirmation → Discovery → Generation → Grounding → Validation → Semantic review → Save. Supports resume, headless, parallel-lens. Python 3.10+.

**Args:** `create` (default), `update` (revise existing D-26), `validate` (check existing D-26). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- `{skill-root}` = installed dir (bare paths resolve from it); `{project-root}` = project working dir; `{skill-name}` = skill dir basename.

## Autonomy (A5)

Separate **mechanical** decisions from **domain** decisions. Mechanical — section ordering, formatting, REQ→scope-area mapping — decide and proceed. Domain — **in vs out of scope** (B9-3), a **risk's likelihood/impact** (B9-2), a **schedule date** not grounded in real input (B9-1), whether a technique fits an area — **ASK; never invent a default** (ungrounded schedule → ASSUMPTION/ADR or pending).

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision and return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option, log it to the decision log as an `ASSUMPTION`, and continue. Never block on the first question.

## Headless Mode

When `--headless`: stages run non-interactively per `references/headless-contract.md`; domain decisions follow the Autonomy mode above.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> **Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask (headless: required, missing → blocked `feature_required`). Substitute `{feature}` in every workflow path.

## Open Floor

Before structured discovery, invite the user to share what they know about testing strategy — priorities, constraints, known risks, team context. Absorb before Stage 1.

## Stage 1: Prerequisites

1a. **Source scan.** Run the pre-pass:

```
python3 {workflow.scan_script} --project-root {project-root} --output-dir {workflow.output_dir}
```

Returns JSON with `state` (fresh/resume/update), `existing_d26`, `d02_path`, `d06_path`, `framework`, `project_context_path`. Route on `state`:
   - **Fresh** — no prior D-26. Proceed to Stage 1b.
   - **Resume** — partial D-26 found. Read `.decision-log.md` first for context recovery. Show summary, offer resume or restart.
   - **Update** — complete D-26 exists. Read `.decision-log.md` first. Show what to update, load as baseline (see Update Mode).

   If the scan script is unavailable, ask the user for source document paths and proceed with manual state detection.

1b. **Source inventory.** D-02 (requirements) is the primary input — test scope derives from requirement scope; missing D-02 (headless) → blocked `no_requirements`. D-06 (business flow) informs integration/E2E scenarios. Load both as context.

1c. **Intent gate.** Confirm test plan (strategy), not test specification (detailed cases → `hbc-create-test-spec` [TS]). Then initialize `.decision-log.md` alongside the output — create if absent, append a session heading if present. Canonical memory for this workflow.

1d. **Brainstorming suggestion** (interactive, Fresh only). If D-02 reveals complex business logic or high-risk areas, suggest `bmad-brainstorming` first to surface risk areas/scenarios that feed the strategy. If declined or headless, proceed. If a session file exists under `{output_folder}/brainstorming/`, load its risk/scenario ideas.

## Stage 1e: Scope Confirmation (B9-3 — HARD pre-gate)

**Before any plan body is generated**, confirm the scope boundary with the user — out-of-scope matters as much as in-scope. From D-02 + Open Floor, draft two lists: **in-scope** areas (each mapping to ≥1 REQ) and **explicitly out-of-scope** items (with the reason each is excluded, e.g. unchanged legacy flow, deferred perf suite). Present both, get explicit confirmation — a domain decision, never inferred silently. Headless: Autonomy mode (`--strict` → blocked `scope_unconfirmed`; `--assumptions-allowed` → log the drafted boundary as `ASSUMPTION` and continue). Record the confirmed boundary to the decision log; Stage 2/3 fill only within it.

## Stage 2: Discovery

Discover the strategy covering levels, approach, environment, team, schedule, entry/exit, and risk — within the confirmed scope. Pre-populate from D-02 and `project-context.md`. At each area boundary, soft-gate: _"Anything else on [area], or move to [next]?"_

**Risk (B9-2).** For each risk you propose a likelihood and impact rating — but the user **confirms** them; present your proposal as a draft to ratify, never as fact. An unconfirmed rating stays flagged (headless: Autonomy mode).

**Schedule (B9-1).** Only enter calendar dates grounded in real input (a stated deadline, a dependency date, the decision log). If none exist, do **not** invent a timeline — record the schedule as an ASSUMPTION/ADR or leave milestones `pending`.

Capture any D-27 material (specific test-case ideas) to the decision log without interrupting the strategy flow.

**Compaction flush:** Write test levels, scope boundaries, risk drafts, and key decisions to the decision log.

## Stage 3: Generation

Populate `{workflow.template_path}` to `{workflow.output_dir}/D-26-{project_name}-test-plan.md`. Ensure:

- Every in-scope area has a **stated test technique/approach cross-linked to D-27** (B9-4). D-27 is authored after D-26 — a forward-reference to it is fine; do not block on the file existing.
- Test scope maps to D-02 requirement scope (the confirmed boundary from Stage 1e).
- Entry/exit criteria include measurable thresholds (use `{workflow.coverage_threshold}`).
- Risk table carries the **user-confirmed** likelihood/impact + mitigation (B9-2).
- Schedule: only grounded dates; if ungrounded, marked provisional (B9-1). A Gantt and/or milestone table for the timeline.
- E2E approach references `{workflow.e2e_framework}` if configured.

**Compaction flush:** Write section count and version to the decision log.

**Parallel-lens menu:** `[A]` Advanced (deeper risk analysis, coverage-gap edge cases) / `[P]` Party Mode (multi-agent strategy review) / `[C]` Continue. If subagents unavailable, apply the lenses directly. Headless: skip to Stage 3a.

## Stage 3a: Grounding reconcile (B9-1 / B9-4)

Reconcile the plan against its inputs — advisory, not a hard gate (the blocking cross-doc gate is `hbc-check-implementation-readiness` [IR]). If unavailable, skip and proceed.

```
python3 {workflow.grounding_script} "{workflow.output_dir}/D-26-{project_name}-test-plan.md" --project-root {project-root} [--sources "<D-02,D-06,.decision-log>"]
```

It returns:
- **`fabricated_dates` (B9-1)** — schedule dates grounded in no source and not marked provisional. Ground each in a real date or mark the schedule ASSUMPTION/pending; **do not silently keep** an invented date (domain decision).
- **`technique_gaps` (B9-4)** — in-scope areas with no stated technique and no D-27 hand-off. Add the approach or link D-27 for each.

Whether a technique *fits* and whether a risk rating is *realistic* stay LLM judgment (Stage 4b). Headless: include both lists; `--strict` blocks if either is non-empty, `--assumptions-allowed` logs and continues.

## Stage 4: Validation

Run the deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-26-{project_name}-test-plan.md"
```

Script checks: required sections present and non-empty, entry/exit criteria defined, risk table has data rows, schedule present; returns per-issue `auto_fixable` and a `churn` block. If unavailable, fall back to LLM-only validation.

**LLM judgment:** test levels fit complexity; entry/exit criteria realistic+measurable; risks cover technical AND process; schedule realistic given team/scope.

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write the validation summary to the decision log.

## Stage 4b: Semantic Review (Layer 2)

Structural validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** — challenge each item: is every in-scope area's technique real and adequate? Each risk's likelihood/impact realistic and **user-confirmed** (B9-2)? Apply the **facet-split discipline**: REQs with an admin/lifecycle/write facet (e.g. approval, key rotation) need a fenced test area — even when D-21 cut them from REST — or be explicitly out-of-scope. List unresolved concerns in `openFacets`. Set `semanticReview.status: passed` **only when `openFacets` is empty AND the user signs off** (headless: Autonomy mode); else `pending`. The Phase 2 gate REVIEW item (#5) enforces it.

## Validate Mode

When invoked with `validate`: run Stage 1a scan to locate the existing D-26, then run the validation (and optionally grounding) script against it. Present results (interactive) or return headless JSON. No discovery/generation. If no D-26 found, return `blocked` with `reason: "no_existing_d26"`.

## Update Mode

When `state: update` from scan or `update` arg: load the existing D-26 as baseline. Present what changes; re-confirm the scope boundary (Stage 1e) if scope shifts. Then proceed to Stage 3 → 3a → 4 → 4b.

**Anti-churn (T2.11).** Bump the version **once per session**, not per edit. Append a single Revision-History row for the session. The validator returns `churn` (`revisions` vs `threshold`); when `churn.high_churn` is true the model isn't frozen yet — surface it and suggest `maturity: exploratory` or a `[DSC]` model-spike instead of another bump.

## Stage 5: Save and Handoff

Finalize — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). On create: fill the blank date in the pre-seeded Revision-History row; on update: the session row was appended in Update Mode. Audit decision-log entries against D-26 — each reflected or explicitly set aside. Append the closing session.

Write `test-plan-distillate.json` alongside D-26 — `{"strategy", "scope": {"in", "out"}, "entry_exit", "risks": [...]}` for downstream D-27 consumption.

If `{workflow.on_complete}` is a non-empty string, run it after saving.

Suggest next steps: _"D-26 complete. Recommended: create D-27 Test Specification (`hbc-create-test-spec` [TS]) for detailed test cases. After both, run Phase 2 gate (`hbc-phase-gate` [PG])."_

Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this section. Prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest running `hbc-traceability impact` to sync dependent documents/tests/code.
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly. Default false.
