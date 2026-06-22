---
name: hbc-create-behavioral-design
description: Generate D-16 Behavioral Design — state transitions, decision tables, invariants, sequences, and BDD scenarios for non-CRUD logic. Use when user says 'behavioral design', 'thiết kế hành vi', 'tạo D-16', or agent menu [BD].
---

# Create Behavioral Design (D-16)

## Overview

Generate D-16 (Behavioral Design) — the **behaviour/logic** of non-CRUD requirements, captured BEFORE code so the logic isn't decided implicitly while implementing. One D-16 per feature, with a section per complex requirement; each behaviour is expressed in up to four block types plus a BDD scenario, every element carrying a stable id so D-27 test cases and (later) code can reference it. Each element maps to ≥1 REQ and to its **unit-test** v_pair (D-16 ground_truth = code).

- **State-transition table** (`ST-NN`) — lifecycle/status changes, including illegal transitions.
- **Decision table** (`DR-NN`) — condition → action business rules.
- **Invariant list** (`INV-NN`) — integrity rules that must always hold (e.g. immutability, hash, snapshot).
- **Sequence / interaction** (`SEQ-NN`) — ordering/timing across entities (the cross-entity sync that data models alone can't express).
- **BDD scenarios** (Given/When/Then) — the acceptance-facing expression of each behaviour, from which D-27/[AC] derive ATDD cases.

Sits in Phase 2 **after D-19, before D-27** — D-27 derives its behavioural test cases from these elements. Supports `create` / `update` / `validate` and `--headless` (`--strict` / `--assumptions-allowed`, see Autonomy). Requires Python 3.10+.

**Applicability (trigger):** required only when the feature has a non-CRUD facet (`has-state-machine` · `has-cross-entity-sync` · `has-invariant` · `has-algorithm` · `has-concurrency`) per the applicability-catalog. Pure CRUD → N/A. The decision is **asked** (the facet checklist is the suggestion, not an auto-verdict).

## Autonomy (A5)

Separate **mechanical** decisions (element-id numbering, table layout, Mermaid notation, which block type a clearly-state behaviour uses — decide and proceed) from **domain** decisions (which REQs are complex, the *actual* states/events/guards, which transitions are illegal, the rule conditions/actions, what an invariant guarantees, cross-entity ordering — **ASK; never invent the logic**). Headless: `--strict` blocks at the first unresolved domain decision (`domain_decision`); `--assumptions-allowed` (CI default) derives the most defensible behaviour from D-02/D-06/D-19, logs it to the decision log as an `ASSUMPTION`, and continues (never blocks the first question). Communicate in `{communication_language}`; document prose in `{document_output_language}`; file/folder names + Mermaid keywords + model/method names English.

## Conventions

- Bare paths resolve from skill root. `{skill-root}` / `{project-root}` / `{skill-name}` as usual.

## On Activation

Resolve customization (`resolve_customization.py --skill {skill-root} --key workflow`; fallback hand-merge). Load persistent facts + config. **Resolve feature (B):** `feature=<slug>` → session → ask (headless: required → blocked `feature_required`); validate slug. Written per-feature at `{workflow.output_dir}/D-16-{feature}-behavioral-design.md`.

## Stage 1: Prerequisites

1a. **Source scan.** Read `D-02` (the REQ set + which have non-CRUD facets), `D-06` (flows — paths feed sequences/transitions), and `D-19` (entities/fields the behaviour references — every entity/field named here must exist in D-19).

1b. **Applicability + REQ selection.** Determine which REQs are complex (facet-triggered). **Ask the user** to confirm the set (suggest from facets); if none, say D-16 is N/A and stop.

1c. **Intent gate.** Behaviour, not data (→ `hbc-create-er-diagram` [ERD]) and not test cases (→ `hbc-create-test-spec` [TS]).

## Stage 2: Discovery (ASK every domain decision — trục C)

For each selected REQ, choose which block(s) apply and elicit them — **never auto-author the logic; confirm each with the user** (headless follows Autonomy: derive from D-06/D-19, log assumptions):

- **State transitions:** confirm states, valid events+guards, and **illegal** transitions (the cut that catches bugs). One `ST-NN` row per transition.
- **Decision rules:** confirm conditions and resulting actions. One `DR-NN` per rule.
- **Invariants:** confirm what must always hold and where it's enforced. One `INV-NN` each.
- **Sequences:** confirm ordering/timing between entities (esp. cross-entity sync). One `SEQ-NN` per step or a Mermaid `sequenceDiagram`.
- **BDD scenario:** for each behaviour, confirm a Given/When/Then capturing its acceptance condition — the bridge to ATDD/[AC]. Reference the element ids it exercises.

Every element references the entities/fields it touches (must exist in D-19) and names its `REQ-<FEAT>-NNN`. Soft-gate per REQ.

### Stage 2b: Grounding-to-code (D-16 ground_truth = code)

The behaviour spec must be **reconcilable against real code behaviour** (`reconcile_seam: behavioral-vs-code`), not only D-02/D-06 narration. Brownfield/migration: ground each transition/rule/invariant/sequence against the REAL model methods (e.g. `resource.plan.action_submit`), and **LOG EVERY divergence** in the template's *Grounding-to-code log* — `design_only` (a behaviour/model the design names but code lacks: planned-not-built or stale) and `code_only` (behaviour in code the design never mentions). Whether a divergence is intended is **judgment** recorded here; the advisory `check-behavioral-grounding.py` (Stage 4) surfaces model drift structurally. Greenfield → `N/A (no code yet)`.

## Stage 3: Generation

Populate `{workflow.template_path}` → `{workflow.output_dir}/D-16-{feature}-behavioral-design.md`. Ensure: a section per complex REQ; every element has a unique id (`ST-/DR-/INV-/SEQ-NN`) and a REQ in its row; every section names its `REQ-<FEAT>-NNN`; ≥1 BDD scenario per behaviour; no empty sections. Element ids are stable across updates (D-27 references them — don't renumber on edit; append). Mark open questions `[NEEDS CLARIFICATION: …]` (the gate reads a leftover marker as `pending`).

**Anti-churn (T2.11):** Create → v1.0; Update → bump the version **once per session**, not per small edit (group the session's changes into one Revision-History row). When the validator reports `churn.high_churn` (revisions > threshold), the behaviour model isn't frozen — **suggest `maturity: exploratory` / run `[DSC]`** instead of adding another revision row.

## Stage 4: Validation

```
python3 {workflow.validation_script} "{workflow.output_dir}/D-16-{feature}-behavioral-design.md" --project-root {project-root}
python3 {workflow.grounding_script} "{workflow.output_dir}/D-16-{feature}-behavioral-design.md" --project-root {project-root} --sources "<D-02,D-06>" [--code-dir {project-root}/<models>]
```

`validate-behavioral-design.py` (structural): Overview + Revision History present + non-empty; ≥1 behavioural element; element ids well-formed + unique; ≥1 REQ reference; `churn` surfaced. `check-behavioral-grounding.py` is **advisory** (E-2 element↔REQ + uncovered-REQ facet · T3.13d BDD-presence · behavioral-vs-code `behavior_drift` via `--code-dir` · churn) — blocking gate is [IR]/Phase-2; surface each finding, never auto-add. Pass D-02+D-06 as `--sources`; supply `--code-dir` when code exists. Both return JSON with `auto_fixable`. Fix loop / headless apply+block.

**LLM judgment:** transitions cover illegal paths (not only happy); decision tables are complete (no uncovered condition combo); invariants are enforceable; BDD scenarios are meaningful; entities referenced exist in D-19.

## Stage 4b: Semantic Review (Layer 2, T2.12)

Run the semantic review per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** and **facet-split discipline** per behaviour (read vs write/admin · lifecycle/state · invariant/integrity · timing/sequence): flag any complex REQ whose state/invariant/timing/decision facet is implied by D-02/D-06 but has no element here, and name open facets so downstream D-27/[AC] inherit them. Record `semanticReview` frontmatter: `status: passed` **only when `openFacets` empty AND the user signs off**, else `pending` + list. Headless follows Autonomy; never blocks here (Phase 2 gate enforces); never fabricate.

## Stage 5: Save and Handoff

Finalize frontmatter (`stepsCompleted`, `lastStep = complete`, `updated`, `semanticReview` from 4b). Suggest next: D-27 Test Spec [TS] (derives behavioural test cases from `ST-/DR-/INV-/SEQ-` ids + BDD scenarios). Headless: JSON per `references/headless-contract.md`.

## Validate / Update modes

- **validate:** run Stage 4 only.
- **update:** load baseline, present changed elements, re-validate; **append** new element ids (never renumber existing — D-27 depends on them); bump version **once per session** on semantic change (Anti-churn).

## Sync Handoff

`update` only. Skip if `--invoked-by-sync`. Default: suggest `hbc-traceability impact`. Contract: `hbc-traceability/references/impact-capability.md`.

**Matrix column (B7-2):** on save (create or update), run `hbc-traceability update feature={feature}` so this phase self-writes its `design_ref` column — don't defer to a manual step (the Phase-2 gate cascade-precheck blocks if missing). Distinct from / lighter than the `impact` cascade.
