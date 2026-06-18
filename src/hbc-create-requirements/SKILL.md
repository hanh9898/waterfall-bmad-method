---
name: hbc-create-requirements
description: "Generate D-02 Requirements Specification with REQ-xxx IDs. Use when user says 'requirements', 'yêu cầu', or agent menu [REQ]."
---

# Create Requirements

## Overview

Generate D-02 (Requirements Specification) — structured requirements with unique REQ-xxx IDs, scope boundaries, user roles, functional and non-functional requirements. REQ IDs are the foundation of the entire traceability chain.

Five-stage workflow: Prerequisites → Discovery → Generation → Validation → Save. Supports resume state, headless mode, and parallel-lens review. Requires Python 3.10+ for validation scripts.

**Args:** `create` (default), `update` (revise existing D-02), `validate` (check existing D-02); **`feature=<slug>`** (increment unit — required in headless; interactive takes the active feature in the session or asks). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (input args, return schema, blocked reasons).

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

**Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask user. Headless: required, missing → `blocked` (`feature_required`). Validate slug `^[a-z0-9][a-z0-9-]*$`. The feature's D-02 is saved at `{workflow.output_dir}/D-02-{feature}.md` (output_dir is already namespaced per feature).

## Stage 1: Prerequisites

1a. **Source scan.** Run pre-pass to discover project state and sources:

```
python3 {workflow.scan_script} --project-root {project-root}
```

Returns JSON with `state` (fresh/resume/update), `existing_d02` (path + frontmatter), `source_docs` list, `project_context` path, a `brownfield` flag (true when a `project_context` was found), `brownfield_suspected` (existing code markers but no project-context.md), and — when brownfield — an `existing_system` catalog (`sources_present`, `entities` from baseline D-19, `endpoints` from baseline D-21, plus a `hint` when thin). Use this to route:
   - **Fresh** — no prior D-02. Proceed to Stage 2.
   - **Resume** — partial D-02 found (`lastStep` < `complete`). Show summary, offer resume or restart.
   - **Update** — complete D-02 exists. Show what to update, load as baseline.

**Brownfield-suspected nudge:** if `brownfield_suspected` (existing code, no project-context.md), ask whether the feature touches the existing system; if yes, recommend `hbc-project-init` [PI] / `bmad-document-project` first so requirements ground against AS-IS — don't go greenfield-style on an existing system. Headless: log it and proceed.

1b. **Source inventory.** Supplement scan results with user-provided inputs (interview notes, descriptions). In headless mode, sources are required via `--sources` arg.

1c. **Intent gate.** Confirm user wants to create/update requirements (not a different artifact). If wrong skill: product brief → `hbc-create-prd`, brainstorming → `hbc-brainstorming`, project setup → `hbc-project-setup`.

1d. **Brainstorming decision** (interactive, Fresh only) — a **mandatory** stop, not the model's call: present the choice and wait for the user — run `bmad-brainstorming` first (output feeds D-02), or go straight to Discovery? Do not decide for them based on perceived complexity. If they pick brainstorming, pause — they run it separately and resume (1a detects the partial D-02). A file in `{output_folder}/brainstorming/` counts as a source. Headless: proceed to Stage 2.

## Stage 2: Discovery

Pre-populate fields from `project-context.md` where available (stakeholders, timeline, tech stack) — present as defaults for confirmation. Open with an invitation for the user to share everything else — goals, constraints, concerns, prior art. If source documents already contain structured requirements (tables, numbered lists with IDs), present them for confirmation and skip to gaps. Then identify which areas still need elicitation:

- **Project background** — purpose, stakeholders, timeline constraints.
- **Scope** — explicit in-scope and out-of-scope boundaries. Out-of-scope is as important as in-scope.
- **User roles** — actors who interact with the system. Each gets a name and description.
- **Functional requirements** — each gets a unique `REQ-<FEAT>-NNN` ID (sequential within the feature; e.g. `REQ-{feature}-001`), written per **EARS** (English keyword + content in the document output language: `WHEN … THE SYSTEM SHALL …`). Requirements shared across features → `REQ-SHARED-NNN` (defined in the shared D-02, only **referenced** here). Must be specific and testable.
- **Non-functional requirements** — performance, security, availability, usability. Each with measurable criteria. Brownfield: when an NFR tightens an existing guarantee, state the **current baseline → target** (e.g. "p95 5s → < 2s"), not just the target — so the change is grounded like a functional CHANGE.
- **Constraints and assumptions** — technical, business, legal constraints.

### Brownfield grounding (only when the scan reports `brownfield: true`)

Reconcile every ask against the existing system before it becomes a requirement: classify `NEW`/`CHANGE`/`REMOVE`, anchor to an existing feature/flow/entity from the scan's `existing_system` catalog, and add a Change Spec (AS-IS → TO-BE) for each `CHANGE`/`REMOVE`. Full procedure — catalog use, compaction flush, headless behavior — in [`references/brownfield-grounding.md`](references/brownfield-grounding.md). Greenfield: skip.

At each area boundary, soft-gate: _"Anything else on [area], or move to [next]?"_ Silently capture glossary-worthy terms and business-flow processes mentioned during Discovery — surface them in Stage 5 handoff.

**Compaction flush:** Write discovered requirements to decision log at end of Stage 2 — actor list, REQ count, scope boundaries. **Brownfield:** also one line per probed ask (`<REQ> · <Change Type> · <Existing System Ref>`) so the change classifications survive a mid-probe compaction (see `references/brownfield-grounding.md`).

## Stage 3: Generation

Populate `{workflow.template_path}` with discovered content. Write to `{workflow.output_dir}/D-02-{feature}.md`. Ensure:
- Every functional requirement has a unique `REQ-<FEAT>-NNN` ID (sequential within the feature) written per EARS; reference `REQ-SHARED-NNN` for shared requirements.
- Scope section explicitly lists out-of-scope items.
- Non-functional requirements have measurable criteria (not "fast" but "< 2s response time").
- Cross-reference user roles with requirements that mention them.
- **Brownfield** (scan `brownfield: true`): use the template's **extended functional table** (`Change Type` + `Existing System Ref`) — NOT the greenfield one — and add a `Change Spec` block per `CHANGE`/`REMOVE` REQ. Greenfield: use the base table.

**Revision history:** If Update mode, detect scope-of-change:
- Same requirements, polish only → append note, no version bump.
- New/changed requirements → new row, bump version.

**Compaction flush:** Write generated REQ count, scope summary, and version to decision log.

**Parallel-lens decision:** After generation, a **mandatory** stop — render this menu as a numbered list and wait for the user's pick (don't auto-continue/skip/default): `[A]` Advanced Elicitation (deeper probing on weak areas) · `[P]` Party Mode (multi-agent lateral review) · `[C]` Continue. The user decides. Headless only — or if the lens subagents are genuinely unavailable — skip the menu and apply the lens perspective directly (and say so).

## Stage 4: Validation

Run deterministic validator, then LLM judgment checks:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-02-{feature}.md" --project-root {project-root} --vague-terms "{workflow.vague_terms}" [--brownfield]
```

Pass `--brownfield` when the scan reports `brownfield: true` — it makes the grounding checks blocking (every CHANGE/REMOVE REQ needs an `Existing System Ref` + `Change Spec`; the script's `BROWNFIELD_*` messages name any gap). Omit for greenfield. (A D-02 with `project_kind: brownfield` in frontmatter enables them even without the flag.)

Script checks: REQ IDs unique and sequential, no vague terms (configurable word list), all required sections present, no empty sections; with `--brownfield`, also the grounding above. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable (Python not installed), fall back to LLM-only validation and note the limitation in the decision log.

**LLM judgment checks:**
- Requirements are testable and unambiguous.
- No contradictions between requirements.
- Non-functional requirements have measurable criteria.
- Scope boundaries are clear.

In `update`, the loaded D-02 carries `project_kind: brownfield`, so grounding re-runs on revised requirements too (a new CHANGE/REMOVE REQ meets the same bar).

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable issues, return `blocked` for non-fixable.

**Compaction flush:** Write validation results summary (issue counts, auto-fixed items) to decision log.

## Stage 4b: Semantic Review (Layer 2)

Structural validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`). Apply the **facet-split discipline** per REQ (read/write · api/admin · lifecycle): flag any REQ with a write/admin/lifecycle facet so downstream D-21/D-26/D-27 know it must be designed and tested — don't let a facet be implied but unowned (the seam). Confirm requirements are testable, unambiguous, non-contradictory; NFRs measurable. **Brownfield:** also apply the rubric's *AS-IS reconciliation* facet — judge whether each CHANGE/REMOVE Change Spec is a *meaningful* AS-IS → TO-BE delta (the deterministic check already proved it's present); list any vacuous/ungrounded REQ in `openFacets`. Record `semanticReview` frontmatter (A-3: `status` passed only when `openFacets` empty, else `pending` + list). The Phase 2 gate REVIEW item (#5) reads it.

## Stage 5: Save and Handoff

Finalize document — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`; set `project_kind: brownfield` when the scan was brownfield, so the grounding checks stay enforced on later validate-only runs). Audit decision-log entries against D-02: every logged decision reflected in the document, captured in addendum, or explicitly set aside. Append closing session.

Suggest next steps, seeding [GLO]/[BFD] with the terms/flows captured during Discovery: _"D-02 complete. Next: D-03 Glossary [GLO] (seed terms: {captured terms}) → D-06 Business Flow [BFD] (seed flows: {captured processes}) → Phase 1 gate [PG]."_

Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"Document updated. Run `hbc-traceability impact` to sync the dependent documents/tests/code?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly (it will cascade downstream). Default is false.
