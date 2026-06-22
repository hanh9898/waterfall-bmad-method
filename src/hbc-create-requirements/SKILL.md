---
name: hbc-create-requirements
description: "Generate D-02 Requirements Specification with REQ-xxx IDs. Use when user says 'requirements', 'yêu cầu', or agent menu [REQ]."
---

# Create Requirements

## Overview

Generate D-02 (Requirements Specification) — structured requirements with unique REQ-xxx IDs, scope boundaries, user roles, functional and non-functional requirements. REQ IDs are the foundation of the entire traceability chain.

Workflow: Prerequisites → **Intake pipeline** (Feasibility → Quick Discovery → optional brainstorm → supplementary Discovery) → Generation → Validation → Semantic Review → Save. Supports resume, headless, adversarial + parallel-lens review. Requires Python 3.10+.

**Args:** `create` (default), `update` (revise existing D-02), `validate` (check existing D-02); **`feature=<slug>`** (increment unit — required in headless; interactive takes the active feature in the session or asks). Optional: `--headless` / `-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths and `{skill-root}` resolve from this skill's installed directory; `{skill-name}` is its basename.
- `{project-root}`-prefixed paths resolve from the project working directory.

## Autonomy (A5)

Separate **mechanical** decisions from **domain** decisions. Mechanical — REQ numbering, table formatting, which section a row belongs to — decide and proceed. Domain — feasibility verdict, scope boundaries, a requirement's meaning/wording, an NFR numeric target, whether an ask is a real requirement, `discovery_risk`/`facets`/`maturity` — **ASK; never invent a default**. Missing data → do not fabricate (e.g. an NFR number) — record an `ASSUMPTION`/ADR.

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision, return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option, log it as an `ASSUMPTION`, continue. Never block on the first question.

## Headless Mode

When `--headless`: all stages run non-interactively per `references/headless-contract.md` (args, return schema, blocked reasons); domain decisions follow the Autonomy mode above.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

**Resolve active feature (B):** arg `feature=<slug>` → active feature in session → ask user. Headless: required, missing → `blocked` (`feature_required`). Validate slug `^[a-z0-9][a-z0-9-]*$`. D-02 saves at `{workflow.output_dir}/D-02-{feature}.md` (output_dir is per-feature namespaced).

## Stage 1: Prerequisites

1a. **Source scan.** Pre-pass to discover project state and sources:

```
python3 {workflow.scan_script} --project-root {project-root}
```

Returns JSON with `state` (fresh/resume/update), `existing_d02`, `source_docs`, `project_context`, a `brownfield` flag (a `project_context` was found), `brownfield_suspected` (code markers but no project-context.md), and — when brownfield — an `existing_system` catalog (`sources_present`, `entities`←D-19, `endpoints`←D-21, `hint` when thin). Route:
   - **Fresh** — no prior D-02 → Stage 2.
   - **Resume** — partial D-02 (`lastStep` < `complete`) → show summary, offer resume/restart.
   - **Update** — complete D-02 → show what to update, load as baseline.

**Brownfield-suspected nudge:** if `brownfield_suspected`, ask whether the feature touches the existing system; if yes, recommend `hbc-project-init` [PI] / `bmad-document-project` first so requirements ground against AS-IS. Headless: log it and proceed.

1b. **Source inventory.** Supplement scan results with user-provided inputs (interview notes, descriptions). Headless: sources required via `--sources`.

1c. **Intent gate.** Confirm the user wants requirements (not another artifact). Wrong skill: product brief → `bmad-product-brief`, brainstorming → `bmad-brainstorming`, project setup → `hbc-project-init`.

## Stage 2: Intake pipeline (Feasibility → Discovery)

The raw-idea→ready-to-generate path. Run these four stages **in order** — they are **distinct, never collapse them** (the historical re-merge bug). Full procedure, the 3-concept boundary box, checklists, headless, brownfield grounding and the NFR-number rule: [`references/intake-pipeline.md`](references/intake-pipeline.md).

1. **① Feasibility — MANDATORY, every feature, early (B1-5/B1-10).** Read source + framework first, then judge if the idea is buildable against real platform/constraints/existing-system invariants. **Kill or park an infeasible idea now**, before discovery effort. If feasibility hinges on an unproven model, flag `discovery_risk: uncertain` for the later [DSC] spike (B1-4 hand-off) — Feasibility does NOT run the spike itself.
2. **② Quick Discovery — ALWAYS (B1-6).** Always elicit the need (source-has-structured-reqs → confirm + probe gaps; thin source → full elicitation). Covers Overview/Scope/Roles/FRs(EARS · `REQ-<FEAT>-NNN`)/NFRs/Constraints + `discovery_risk`/`facets`/`maturity` (suggest, user confirms). **NFR numbers (B1-3):** ASK the target; unknown → ASSUMPTION/ADR, never fabricate. Brownfield: reconcile per [`brownfield-grounding.md`](references/brownfield-grounding.md).
3. **③ Deep brainstorming — ALWAYS OFFER; running it is optional (B1-7).** Mandatory stop — never skip the offer on perceived simplicity: offer `bmad-brainstorming` with **two seeds** (*topic*=weakest area, *output*=what to produce), or go to generation. Picked → pause + resume. Headless: skip.
4. **④ Supplementary Discovery after brainstorm — MANDATORY (B1-8).** If brainstorming ran, fold its output back in (confirm which ideas become REQs, update scope/roles/REQs, re-probe gaps). Skipped → no-op.

Silently capture glossary terms + business-flow processes for Stage 5. **Compaction flush** at discovery end (see reference).

## Stage 3: Generation

**REQ-list confirmation first (B1-1) — a mandatory stop, not the model's call.** Before writing the full document, present the **list of REQ titles/one-liners** (+ roles + scope) from discovery; wait for the user to confirm/add/drop/reorder. Generate the full EARS requirements only once the list is agreed. Headless: log the list and proceed (`--strict` blocks on an ambiguous REQ).

Then populate `{workflow.template_path}`; write to `{workflow.output_dir}/D-02-{feature}.md`. Ensure:
- Every FR has a unique `REQ-<FEAT>-NNN` ID (sequential) in EARS; reference `REQ-SHARED-NNN` for shared ones.
- Scope lists out-of-scope items; NFRs have measurable criteria (not "fast" but "< 2s").
- Cross-reference user roles with the requirements that mention them.
- Frontmatter records confirmed `discovery_risk` / `facets` / `maturity` (drive applicability + the P1-11 gate).
- **Brownfield** (`brownfield: true`): use the template's **extended functional table** (`Change Type` + `Existing System Ref`) + a `Change Spec` per `CHANGE`/`REMOVE`. Greenfield: base table.

**Revision history & anti-churn (T2.11):** If Update mode, bump the version **once per session**, not per edit:
- Same requirements, polish only → append note, no version bump.
- New/changed requirements → one new row for the whole session, bump version once.

The validator returns `churn`; when `churn.high_churn` is true the model isn't frozen yet — surface it and suggest `maturity: exploratory` or a `[DSC]` spike instead of another bump (the fix for the "13 versions" symptom).

**Compaction flush:** Write REQ count, scope summary, and version to the decision log.

**Mandatory adversarial + edge-case review (B1-9 / T2.8) — before the gate.** Run `bmad-review-adversarial-general` AND `bmad-review-edge-case-hunter` over the D-02 (contradictions, vague/untestable REQs, missing scope/edge cases, unowned facets). **Availability fallback:** these ship with bmm/core — if absent, apply both lenses inline and log "ran inline"; do NOT hard-block. The Phase 2 gate expects evidence both ran; feed findings into Stage 4/4b.

**Parallel-lens decision:** then a stop — render this menu as a numbered list, wait for the user's pick (don't auto-continue/default): `[A]` Advanced Elicitation · `[P]` Party Mode · `[C]` Continue. Headless, or if subagents are unavailable — skip the menu, apply the lens directly (say so).

## Stage 4: Validation

Run the deterministic validator:

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-02-{feature}.md" --project-root {project-root} --vague-terms "{workflow.vague_terms}" [--brownfield]
```

Pass `--brownfield` when the scan reports `brownfield: true` — it makes grounding blocking (every CHANGE/REMOVE REQ needs an `Existing System Ref` + `Change Spec`; `BROWNFIELD_*` messages name any gap). Omit for greenfield. (Frontmatter `project_kind: brownfield` enables them without the flag.)

Script checks: REQ IDs unique/sequential, no vague terms, required sections present/non-empty, NFR criteria present; advisory cues for NFRs lacking a numeric target (`NFR_NO_NUMBER` — B1-3) and revision `churn`; with `--brownfield`, also the grounding above. Returns JSON with per-issue `auto_fixable` flag. If the script is unavailable, fall back to LLM-only validation and note the limitation. (Deeper LLM judgment — testability, contradictions, scope clarity — happens in Stage 4b.)

**Fix logic:** Interactive — collaborative fix loop. Headless — apply auto-fixable, return `blocked` for non-fixable.

**Compaction flush:** Write the validation summary (issue counts, auto-fixed) to the decision log.

## Stage 4b: Semantic Review (Layer 2)

Structure-passing isn't meaning. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** — challenge each REQ: testable, unambiguous, source-grounded, non-contradictory? NFRs measurable? Apply the **facet-split discipline** per REQ (read/write · api/admin · lifecycle): flag any write/admin/lifecycle facet so downstream D-21/D-26/D-27 own it — don't let a facet be implied but unowned (the seam). **Brownfield:** also apply the rubric's *AS-IS reconciliation* facet — judge whether each CHANGE/REMOVE Change Spec is a *meaningful* delta; list any vacuous/ungrounded REQ in `openFacets`. Set `semanticReview.status: passed` **only when `openFacets` is empty AND the user signs off** (headless follows Autonomy); else `pending` + list. The shared `semantic_review_status` is the single structural read; the Phase 2 gate REVIEW item (#5) enforces it.

## Stage 5: Save and Handoff

Finalize — update frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`; set `project_kind: brownfield` when the scan was brownfield, so grounding stays enforced on later validate-only runs). Audit decision-log entries against D-02: each reflected, in an addendum, or explicitly set aside. Append closing session.

Suggest next steps, seeding [GLO]/[BFD] with the captured terms/flows: _"D-02 complete. Next: D-03 Glossary [GLO] (seed: {terms}) → D-06 Business Flow [BFD] (seed: {processes}) → Phase 1 gate [PG]."_ When `discovery_risk: uncertain`, insert [DSC] before the gate (P1-11 requires a VALIDATED discovery-note).

Headless: return JSON per `references/headless-contract.md`.

## Sync Handoff (hbc-traceability impact integration)

`update` mode only. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** invoked with `--invoked-by-sync` / `invoked_by_sync=true` → skip this whole section (prevents the update→sync→update loop).
- **Default:** after a successful update, suggest running `hbc-traceability impact` to sync dependent docs/tests/code.
- **Auto-chain:** if `{workflow.auto_sync_after_update}` is true (default false), invoke `hbc-traceability impact` directly.
