---
name: hbc-create-behavioral-design
description: Generate D-17 Behavioral Design — state transitions, decision tables, invariants, and sequences for non-CRUD logic. Use when user says 'behavioral design', 'thiết kế hành vi', 'tạo D-17', or agent menu [BD].
---

# Create Behavioral Design (D-17)

## Overview

Generate D-17 (Behavioral Design) — the **behaviour/logic** of non-CRUD requirements, captured BEFORE code so the logic isn't decided implicitly while implementing. One D-17 per feature, with a section per complex requirement; each behaviour is expressed in up to four block types, every element carrying a stable id so D-27 test cases and (later) code can reference it:

- **State-transition table** (`ST-NN`) — lifecycle/status changes, including illegal transitions.
- **Decision table** (`DR-NN`) — condition → action business rules.
- **Invariant list** (`INV-NN`) — integrity rules that must always hold (e.g. immutability, hash).
- **Sequence / interaction** (`SEQ-NN`) — ordering/timing across entities (the cross-entity sync that data models alone can't express).

Sits in Phase 2 **after D-19, before D-27** — D-27 derives its behavioural test cases from these elements. Supports `create` / `update` / `validate` and `--headless`. Requires Python 3.10+.

**Applicability (trigger):** required only when the feature has a non-CRUD facet (`has-state-machine` · `has-cross-entity-sync` · `has-invariant` · `has-algorithm` · `has-concurrency`) per the applicability-catalog. Pure CRUD → N/A. The decision is **asked** (the facet checklist is the suggestion, not an auto-verdict).

## Conventions

- Bare paths resolve from skill root. `{skill-root}` / `{project-root}` / `{skill-name}` as usual.
- Communicate in `{communication_language}`; document prose in `{document_output_language}`; file/folder names + Mermaid keywords English.

## On Activation

Resolve customization (`resolve_customization.py --skill {skill-root} --key workflow`; fallback hand-merge). Load persistent facts + config. **Resolve feature (B):** `feature=<slug>` → session → ask (headless: required → blocked `feature_required`); validate slug. Written per-feature at `{workflow.output_dir}/D-17-{feature}-behavioral-design.md`.

## Stage 1: Prerequisites

1a. **Source scan.** Read `D-02` (the REQ set + which have non-CRUD facets), `D-06` (flows — paths feed sequences/transitions), and `D-19` (entities/fields the behaviour references — every entity/field named here must exist in D-19).

1b. **Applicability + REQ selection.** Determine which REQs are complex (facet-triggered). **Ask the user** to confirm the set (suggest from facets); if none, say D-17 is N/A and stop.

1c. **Intent gate.** Behaviour, not data (→ `hbc-create-er-diagram` [ERD]) and not test cases (→ `hbc-create-test-spec` [TS]).

## Stage 2: Discovery (ASK every domain decision — trục C)

For each selected REQ, choose which block(s) apply and elicit them — **never auto-author the logic; confirm each with the user** (headless: derive from D-06/D-19, log assumptions):

- **State transitions:** confirm states, valid events+guards, and **illegal** transitions (the cut that catches bugs). One `ST-NN` row per transition.
- **Decision rules:** confirm conditions and resulting actions. One `DR-NN` per rule.
- **Invariants:** confirm what must always hold and where it's enforced. One `INV-NN` each.
- **Sequences:** confirm ordering/timing between entities (esp. cross-entity sync). One `SEQ-NN` per step or a Mermaid `sequenceDiagram`.

Every element references the entities/fields it touches (must exist in D-19). Soft-gate per REQ.

## Stage 3: Generation

Populate `{workflow.template_path}` → `{workflow.output_dir}/D-17-{feature}-behavioral-design.md`. Ensure: a section per complex REQ; every element has a unique id (`ST-/DR-/INV-/SEQ-NN`); every section names its `REQ-<FEAT>-NNN`; no empty sections. Element ids are stable across updates (D-27 references them — don't renumber on edit; append).

## Stage 4: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-17-{feature}-behavioral-design.md" --project-root {project-root}
```

Structural checks: Overview + Revision History present + non-empty; ≥1 behavioural element; element ids well-formed + unique; ≥1 REQ reference. Returns JSON with `auto_fixable`. Fix loop / headless apply+block.

**LLM judgment:** transitions cover illegal paths (not only happy); decision tables are complete (no uncovered condition combo); invariants are enforceable; entities referenced exist in D-19.

## Stage 4b: Semantic Review (Layer 2)

Per `.claude/skills/hbc-shared/references/semantic-review-rubric.md`. Facet-split: flag any complex REQ whose state/invariant/timing facet is implied by D-02/D-06 but has no element here. Record `semanticReview` frontmatter (`passed` only when `openFacets` empty).

## Stage 5: Save and Handoff

Finalize frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview`). Suggest next: D-27 Test Spec [TS] (derives behavioural test cases from `ST-/DR-/INV-/SEQ-` ids). Headless: JSON per `references/headless-contract.md`.

## Validate / Update modes

- **validate:** run Stage 4 only.
- **update:** load baseline, present changed elements, re-validate; **append** new element ids (never renumber existing — D-27 depends on them); bump version on semantic change.

## Sync Handoff

`update` only. Skip if `--invoked-by-sync`. Default: suggest `hbc-traceability impact`. Contract: `hbc-traceability/references/impact-capability.md`.
