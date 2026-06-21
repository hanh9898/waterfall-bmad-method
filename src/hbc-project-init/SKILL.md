---
name: hbc-project-init
description: "Phase 0 — khởi tạo dự án + tạo các deliverable dùng chung (shared) một lần trước khi làm feature. Use when user says 'project init', 'khởi tạo dự án', 'phase 0', 'tạo shared', or agent menu [PI]."
---

# Project Init (Phase 0)

## Overview

Phase 0 runs **once, mandatory, BEFORE** any feature — or **re-run to detect drift and update in place**. It: **(1) understands the project** (brownfield-aware — derive from real code, don't invent), **(2) loads/initializes the applicability-catalog** (which deliverables this project's features will need), then **(3) creates the shared deliverables** that every feature builds on.

| Deliverable | Mandatory | Location |
| --- | --- | --- |
| **constitution.md** (cross-phase invariants) | ✅ | `{workflow.constitution_output_path}` |
| **D-12 Coding Standards** | ✅ | `shared/coding-standards/` |
| **D-03 Glossary** | ✅ | `shared/glossary/` |
| **D-19 ERD (baseline)** | catalog-decided | `shared/erd/` |
| **D-21 API (baseline)** | catalog-decided | `shared/api/` |

D-19/D-21 applicability is **decided by the catalog** (data-model-change / exposes-api), never pre-cut here (framework-complete principle: keep the capability, the catalog marks N/A per project).

Idempotent: an existing deliverable is **never silently overwritten** — but a re-run **detects drift** and proposes an update in place (B15-1).

**Args:** `create` (default — understand + load catalog + create missing + reconcile drift), `status` (only list what exists / is missing / drifted; no generation). Optional: `--headless`/`-H` with `--strict` or `--assumptions-allowed` (see Autonomy).

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename.

## Autonomy (A5)

Separate **mechanical** decisions from **domain** decisions. Mechanical — directory layout, which create-skill owns which D-xx, JSON shape, applying the catalog's stated rule once facets are known — decide and proceed. Domain — the project's **classification** (brownfield/greenfield when signals are mixed), its **stack / domain / conventions**, a **facet** that flips a deliverable required↔N/A, a **constitution principle stance** (a test-first exemption, a simplicity cap) — **ASK; never invent a default** (B15-4 is ASK-before-generate, not auto-classify).

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision, return `blocked` with the question.
- `--assumptions-allowed` (**CI default**) — take the most defensible option (deterministic classification, catalog default applicability), log it to the decision log as an `ASSUMPTION`, and **continue — never block the first turn**.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> Phase 0 **takes no `feature` arg** — it creates project-wide shared artifacts. Per-feature D-19/D-21 overrides and per-feature catalog **instances** are created later (T3.15) via `hbc-create-er-diagram`/`hbc-create-api-spec` and the BA agent with `feature=<slug>`.

## Headless Mode

`-H`/`--headless` runs `create`/`status` non-interactively (full I/O contract: `references/headless-contract.md`). Brownfield vs greenfield is detected deterministically (codebase presence); existing project documentation is the source. Domain decisions follow the Autonomy mode above. No `feature` arg.

Blocked reasons (closed set):
- `missing_sources` — a mandatory deliverable is still missing and there are insufficient sources (no project-context, no codebase, no PRD/brief) to generate it (only under `--strict`; `--assumptions-allowed` continues with limited sources + a logged note).

## Stages

### Stage 1: Scan baseline + load catalog

Run the deterministic pre-pass:

```
python3 {workflow.scan_script} --project-root {project-root} --output-folder {output_folder} --skill-root {skill-root} --catalog-path {workflow.applicability_catalog} --project-knowledge {project_knowledge}
```

Returns JSON: `project_type` (brownfield/greenfield), `is_rerun`, `legacy_v1_layout`, `project_context`, `documented`, per-deliverable `present`/`path`, `present`/`missing` lists, `drift` (structural staleness signals), and `catalog` (the loaded node-set + facets). If the script/Python is unavailable, fall back to asking the user for the project state and proceed with an empty catalog (note the limitation).

Present a **present / missing / drifted** table. If `status` arg → stop here.

**LEGACY (v1) layout (`legacy_v1_layout: true`):** flat `planning-artifacts/D-*` or `traceability/matrix*` with no `features/` dir. **Recommend running `hbc-migrate` ([MIG]) FIRST** — creating shared now would double-create with what migrate is about to build. Surface the warning, then stop so the user runs [MIG], then returns to PI.

**Drift (B15-1, re-run only).** When `is_rerun` and `drift` is non-empty: a present deliverable looks stale (incomplete frontmatter, semantic review not passed) or its grounding source changed. Surface each; for each, propose **re-running that create-skill in `update` mode** (it carries its own anti-churn + semantic review — do not re-implement those here). Never overwrite blindly. Headless: list drift in the return; `--strict` blocks if a mandatory deliverable drifted, `--assumptions-allowed` logs and continues.

### Stage 2: Understand + confirm the project (B15-4)

Establish enough **context** to seed the deliverables — and **confirm it with the user**, don't just classify:

1. **Classify + confirm brownfield/greenfield** and **confirm stack / domain / conventions** (B15-4). Brownfield = source code exists outside `_bmad`/`docs`/`_bmad-output`. Present the scan's classification + detected stack and **ask the user to confirm or correct** (this replaces a separate soft "tell me about your stack" step — net-ceremony stays ≤0). These confirmed facts seed D-12 (conventions), D-03 (domain), and the constitution. Headless follows the Autonomy mode.
2. **Ensure `project-context.md`.** If missing, orchestrate `bmad-generate-project-context` (AI rules + project context) — the persistent fact every HBC skill relies on.
3. **Brownfield — document first.** If brownfield and project docs (`{project_knowledge}/index.md`) are missing, orchestrate **`bmad-document-project`** to scan the codebase (architecture, DB schema, endpoints, conventions). These are the **source** for deriving: conventions → D-12, schema → baseline D-19, endpoints → baseline D-21.
4. **Confirm the catalog node-set.** From the loaded `catalog` + the confirmed facets, state which shared deliverables this project needs (D-12/D-03 always; D-19 when there's a data model; D-21 **when the project exposes an API** — B15-3). Mark any **N/A with its reason** (catalog decides; you never pre-cut a layer). Forward-ref: per-feature catalog **instances** are written later at feature start (T3.15) — Phase 0 only seeds the project-level baseline + advisory.

### Stage 3: Create the constitution (T3.13a)

The constitution is the project's **cross-phase invariant principles** — written once, stable, referenced by the 5 personas. If `constitution` is missing, create it from `{workflow.constitution_template}` → `{workflow.constitution_output_path}`, filling the five invariants from the confirmed context: **test-first · language-policy · SoD · handoff-through-artifact · simplicity-caps**. Any value you cannot ground, mark `[NEEDS CLARIFICATION: …]` (the convention) and **ask** — never invent it.

Validate structure, then run the **semantic review**:

```
python3 {workflow.constitution_validation_script} {workflow.constitution_output_path} --lang-label "{document_output_language}"
```

Script (structure-only): five principles present + non-empty, no `[NEEDS CLARIFICATION]` left, semantic-review frontmatter readable. Then run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an independent skeptic lens — is each principle concrete and project-true, not boilerplate? List unresolved concerns in `openFacets`; set `semanticReview.status: passed` **only when `openFacets` empty AND the user signs off** (headless follows the Autonomy mode), else `pending`.

> **Anti-churn (T2.11): N/A — with reasoning.** The constitution is a **one-time, stable** invariant doc (not an iterated per-feature artifact), so doc-version churn does not apply: there is no per-edit version bump to throttle. Amendments are rare cascade events recorded in its Amendment table, not churn. (Stated explicitly per the tường-minh rule — not silently omitted.)

If the deliverable already exists: this is a re-run — apply Stage 1 drift handling (propose an update, don't overwrite).

### Stage 4: Create the missing shared deliverables (idempotent)

For each **missing** deliverable the catalog marks needed, orchestrate its create-skill, **passing the confirmed Stage-2 context** (each create-skill carries its own anti-churn + semantic-review — T2.11/T2.12 live there, not here):
- D-12 → `hbc-create-coding-standards` (always) — brownfield: extract conventions from real code.
- D-03 → `hbc-create-glossary` (always) — from the domain/project docs.
- D-19 baseline → `hbc-create-er-diagram` (when data model) — brownfield: reverse-engineer the real DB schema.
- D-21 baseline → `hbc-create-api-spec` (**when the project exposes an API** — B15-3) — brownfield: from existing endpoints.

**Never overwrite** an existing deliverable. Headless: create the missing needed deliverables if sources suffice; `--strict` → `blocked` (`missing_sources`) when a mandatory one can't be sourced; `--assumptions-allowed` continues with a logged note.

### Stage 5: Handoff

Communicate in `{communication_language}`:

_"Phase 0 done — the project now has its constitution + project-context + shared deliverables, and the applicability-catalog is loaded. Start the first feature: open `hbc-agent-ba` ([BA]) with a feature slug (it confirms the feature's facets → catalog instance), then `hbc-create-requirements` (feature=<slug>)."_

Headless: return JSON `{status, project_type, is_rerun, project_context, documented, catalog_loaded, constitution, created, skipped, drifted, missing}` per `references/headless-contract.md`.
