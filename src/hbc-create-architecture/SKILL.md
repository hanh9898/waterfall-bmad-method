---
name: hbc-create-architecture
description: Generate D-09 Architecture Design — components, layers, integration points, and NFR-driven decisions. Use when user says 'architecture design', 'thiết kế kiến trúc', 'tạo D-09', or agent menu [AD].
---

# Create Architecture Design (D-09)

## Overview

Generate D-09 (Architecture Design) for a feature — the **components/layers**, **integration points** into the existing system, and **NFR-driven decisions** (each recorded as a short ADR with rationale). D-09 sits at the start of Phase 2 (before D-19/D-16), capturing the structural decisions that would otherwise be made implicitly while coding. Every component and decision traces to ≥1 `REQ-<FEAT>-NNN`.

Four-stage workflow: Prerequisites → Discovery → Generation → Validation. Supports `create` (default) / `update` / `validate` and `--headless` / `-H`. Requires Python 3.10+ for the validator.

**Applicability:** per the applicability-catalog, D-09 is **required when the feature has the `has-integration` or `has-algorithm` facet**, else optional. Skip (mark N/A in the feature's catalog instance) for a pure-CRUD feature with no integration.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = this skill's dir; `{project-root}` = project root; `{skill-name}` = skill basename.
- Communicate in `{communication_language}`; write document prose in `{document_output_language}`; file/folder names always English. Mermaid keywords/identifiers stay English.

## On Activation

Resolve customization (`python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`; on failure hand-merge `customize.toml` → `_bmad/custom/{skill-name}.toml` → `.user.toml`). Load `{workflow.persistent_facts}` and config. **Resolve active feature (B):** `feature=<slug>` arg → active session feature → ask (headless: required, missing → blocked `feature_required`); validate slug `^[a-z0-9][a-z0-9-]*$`. D-09 is written per-feature at `{workflow.output_dir}/D-09-{feature}-architecture.md`.

## Stage 1: Prerequisites

1a. **Source scan.** Read the feature's `D-02` (REQ + NFRs), `D-06` (flows), and the shared **integration-map** (existing models/modules — the ground-truth inventory) if present. NFRs in D-02 §5 drive the structural decisions; integration points anchor to entries in the integration-map, not invented.

1b. **Intent gate.** Confirm the user wants architecture design (not ER data design → `hbc-create-er-diagram` [ERD]; not behavior → `hbc-create-behavioral-design` [BD]).

1c. **Applicability check.** If the feature's catalog instance marks D-09 N/A (no `has-integration`/`has-algorithm`), say so and stop unless the user overrides.

## Stage 2: Discovery (ASK at every domain decision — trục C)

Do not auto-decide architecture. For each area, present a proposal **derived from D-02/D-06/integration-map** plus the suggested option, then let the user confirm/override (headless: derive from sources, log assumptions):

- **Components** — the units this feature adds/changes; each named, one-line responsibility, mapped to the REQ(s) it realizes.
- **Layers / boundaries** — where each component sits (e.g. model / service / controller / view / job) and what it may depend on.
- **Integration points** — which **existing** models/modules/services it touches (anchor to integration-map entries; classify NEW vs CHANGE), and the contract at each seam.
- **NFR-driven decisions** — for each relevant NFR in D-02 §5, the structural choice it forces (e.g. "p95 < 2s → read-model cache"). Record as an ADR (decision · rationale · alternatives considered · REQ/NFR ref).

Soft-gate at each area: _"Anything else on [area], or move on?"_

## Stage 3: Generation

Populate `{workflow.template_path}` → write to `{workflow.output_dir}/D-09-{feature}-architecture.md`. Ensure: every component and every Decision Record references ≥1 REQ/NFR; integration points name an existing-system anchor; no empty sections. Optional Mermaid `flowchart`/`graph` for the component/layer view (`participant`/nodes in English). On `update`, bump version + add a Revision History row when components/decisions change (polish → note only).

## Stage 4: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-09-{feature}-architecture.md" --project-root {project-root}
```

Structural checks: required sections present + non-empty; each Decision Record has a rationale; ≥1 REQ reference present; integration points table parses. Returns JSON with per-issue `auto_fixable`. Fix loop (interactive) / apply auto-fixable + return `blocked` (headless).

**LLM judgment:** decisions are justified (not arbitrary); components cover the REQ set; integration points are grounded in the real system; NFR decisions are traceable to a measurable NFR.

## Stage 4b: Semantic Review (Layer 2)

Run the semantic review per `.claude/skills/hbc-shared/references/semantic-review-rubric.md`. Facet-split: flag any REQ whose architectural facet (integration / cross-cutting / NFR) is implied but unowned by a component or decision. Record `semanticReview` frontmatter (`status: passed` only when `openFacets` empty).

## Stage 5: Save and Handoff

Finalize frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). Suggest next: D-19 ER Diagram [ERD] (data), D-16 Behavioral Design [BD] (if a non-CRUD facet fired), then D-26/D-27. Headless: return JSON per `references/headless-contract.md`.

## Validate / Update modes

- **validate:** run Stage 4 against the existing D-09; no discovery/generation.
- **update:** load existing D-09 as baseline, present the diff of changed components/decisions, re-validate; bump version on semantic change.

## Sync Handoff

Applies in `update` only. Suppression guard: skip if `--invoked-by-sync`. Default: suggest `hbc-traceability impact` to cascade. Full contract: `hbc-traceability/references/impact-capability.md`.
