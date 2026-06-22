---
name: hbc-create-er-diagram
description: "Generate D-19 Database Design Document with ER Diagram in Mermaid from PRD, Architecture, or interactive input. Use when user says 'create ER diagram', 'create D-19', 'tạo sơ đồ ER', 'vẽ sơ đồ ER', or 'vẽ D-19'."
---

# Create ER Diagram (D-19)

## Overview

Produces a D-19 Database Design Document — a Mermaid `erDiagram` with entities, relationships, attribute specs, and table/index definitions — built tier-by-tier (conceptual → logical → physical) with an ASK-gate at each descent. Reads PRD / Architecture / D-06 / UX from `{planning_artifacts}` (and `bmad-document-project` output + real DB schema from `{project_knowledge}` when brownfield), else interactive elicitation. Output is a single D-19 file in the resolved workspace; `.decision-log.md` and `.scan/` are its peers.

Five stages: prerequisites → discovery → generation → validation → handoff. Supports `-H` / `--headless` with `--strict` / `--assumptions-allowed` (see Autonomy). Two references carry the detail:

- [`references/stage-guide.md`](references/stage-guide.md) — full per-stage detail (On Activation, Conventions, Language Rules, 3-tier ASK-gate, ondelete/index/decision-record prose, grounding-to-code, Semantic Review, lens menu). **Read before executing any stage.**
- [`references/headless-contract.md`](references/headless-contract.md) — the full `--headless` flag set, defaults table, JSON return contract.

## Autonomy (A5)

Separate **mechanical** decisions (entity layout, attribute ordering, snake_case, Mermaid notation — decide and proceed) from **domain** decisions (entity/relationship scope, normalization level, **ondelete behavior** B2-3, whether a no-REQ entity is a phantom — **ASK; never invent a default**). The conceptual / logical / physical tier confirmations are **hard ASK-gates** before generation descends a tier (B2-1); ondelete (CASCADE / RESTRICT / SET NULL) is asked per FK with rationale recorded, never silently picked (B2-3). Headless: `--strict` blocks at the first unresolved domain decision; `--assumptions-allowed` (CI default) logs the most defensible option to `.decision-log.md` as an `ASSUMPTION` and continues (never blocks the first question).

Carve-outs kept verbatim: Mermaid keywords/identifiers, SQL types, constraint labels. Communicate in `{communication_language}`; translate output prose to `{document_output_language}`; file/folder names always English. Full Language Rules + Conventions: stage-guide.

## On Activation

> **Scope DUAL + feature (B):** by default write/read the baseline `shared/erd/` (`{workflow.er_diagram_output_path}`); pass `feature=<slug>` → a **per-feature override** (`{workflow.er_diagram_feature_path}`, path-existence precedence).

Execute the full activation sequence per [`references/stage-guide.md`](references/stage-guide.md) § *On Activation (detail)*: resolve the `workflow` block (`resolve_customization.py --skill {skill-root} --key workflow`; on failure hand-merge `customize.toml` → team → user, keep `{workflow.*}` incl. `{workflow.on_complete}` in memory all session) → run `{workflow.activation_steps_prepend}` → load `{workflow.persistent_facts}` → load config (`config.yaml`(+`.user`) → `.toml` → legacy `bmm/config.yaml`) resolving `{user_name}`/`{communication_language}`/`{document_output_language}`/`{planning_artifacts}`/`{project_knowledge}`/`{project_name}` → greet `{user_name}` (D-19 opens Phase 2 — expects the Phase 1 gate passed) and run `{workflow.activation_steps_append}`.

## Headless Mode

`-H` / `--headless` runs without prompts. Full contract: [`references/headless-contract.md`](references/headless-contract.md). Closed-set blocker `reason` values (compaction-survival mirror — extend this list and the contract file together): `template_missing`, `no_prd_and_no_interactive_in_headless`, `planning_artifacts_unreadable`, `mermaid_validation_failed`, `entity_coverage_gap`, `no_entities_found`, `tier_unconfirmed` (`--strict` + unconfirmed tier/ondelete/scope, B2-1/B2-3), `resolver_missing`.

**Parallel-lens menu** (end of Stage 3 + 4): `[A]` advanced-elicitation, `[P]` party-mode incl. a DBA lens, `[C]` continue. Headless: `--review-lenses=skip|advanced|party` (default `skip`), each fire appended to `review_lenses_run`. Full menu: stage-guide.

## Workflow

Each stage below is a one-line index. **Read [`references/stage-guide.md`](references/stage-guide.md) before executing** — do not act from these summaries alone.

### 1. Prerequisites and Scope

- **1a. Bind DUAL scope + resume** — resolve `{feature}` (arg → session → ask; headless no feature → shared baseline, do NOT block); bind `{primary}`+`{ws}` (path-existence precedence) and **emit the REQUIRED resolve log line** naming which path won (no silent baseline pickup). Run `discover-planning-artifacts.py` (`--primary {primary}`, `+--project-knowledge {project_knowledge}` brownfield) → `{ws}/.scan/artifacts.json`; `template_missing` HALT/block; else branch `resume_state` + menu; init `.decision-log.md` if absent.
- **1b. Open-floor + intent + off-ramp** (interactive) — invite schemas/DDL/ORM/prior ERDs; intent (capture / design / both); off-ramp (D-20 column DDL · D-17 sequence · D-18 class). Short-circuit 1e only when scope + sources + tier all covered.
- **1b′. Brainstorming** (interactive, Fresh, design-new) — offer `bmad-brainstorming`; load any `{output_folder}/brainstorming/` session.
- **1c. Consume source inventory** — `artifacts.json` → PRD set (shards enumerated, don't re-glob) + Architecture + D-06 + UX + D-20; brownfield `project_knowledge` → treat real DB schema as authoritative ground truth, log discrepancies.
- **1d. No-PRD HALT menu** — zero PRDs, no `--prd-path` → menu; headless `--no-prd-ok` → greenfield else blocked `no_prd_and_no_interactive_in_headless`.
- **1e. Tier + scope confirmation** — confirm scope/sources + **starting tier**; init primary from `{workflow.er_diagram_template}` (translate prose); `stepsCompleted += stage-1`, `updated` = today. (Tier ASK-gates fire in Stage 3.)

### 2. Discovery

Run `extract-entity-candidates.py <sources…> -o {ws}/.scan/entity-candidates.json` (full LLM extraction if `warn: entity_extraction_empty`). Extract entities/attributes/relationships/constraints/indexes; group by domain. **Conceptual reconciliation (B2-5):** reconcile against **REQ + D-06 business-flow** (not the PRD alone) — every entity/relationship traces to ≥1 REQ (B2-2). Zero-entity → confirm / headless `blocked` `no_entities_found`. **Compaction-flush (required):** write `stage_2_entities`/`stage_2_relationships` frontmatter, append `### Discovery snapshot (Stage 2 flush)` to `.decision-log.md`, `stepsCompleted += stage-2`. Detail: stage-guide § Stage 2.

### 2b. Grounding-to-code (B2-7)

Ground the model against the **REAL DB schema / models / migrations** (brownfield/migration), not the PRD's narration, and **LOG EVERY divergence** in the template's *Grounding-to-code log* (the advisory `check-er-consistency.py` `schema_drift` in Stage 4 surfaces design-only/code-only models structurally; the row records the resolution). Greenfield → `N/A`. Detail: stage-guide § Stage 2b.

### 3. Diagram Generation — 3-tier ASK-gate (B2-1)

Generate tier-by-tier, confirming before each descent (hard gates): **Conceptual** (entities + relationships, no attributes) → ASK → **Logical** (attributes, keys, normalized; **ondelete asked per FK + rationale recorded** B2-3; **indexes as PROPOSALS, not imposed** B2-4) → ASK → **Physical** (snake_case, SQL types, concrete constraints). Render one `erDiagram` per domain (`||--o{` 1-N, `||--||` 1-1, `}o--o{` N-N; no `;` in labels); >15 entities → H2 sub-domains + master overview, one file. **Anti-churn gate (B2-9/T2.11):** Create → v1.0; Update → bump **once per session** (auto-diff Stage 2 flush → polish vs semantic, or `--scope-of-change`); high churn → suggest `maturity: exploratory` / `[DSC]` not another row. **Decision-record (B2-10):** record each DB decision (ondelete, normalization trade-off) in `.decision-log.md` noting `→ ADR` — *forward-ref* the future ADR object (engine T2.5 not built; wire the touchpoint, don't build it). `stepsCompleted += stage-3`; then the lens menu. Detail: stage-guide § Stage 3.

### 4. Validation

Run three validators in parallel (independent):

```
python3 {skill-root}/scripts/validate-mermaid-er.py {primary} --expected-entities "<stage-2 entities>" -o {ws}/.scan/mermaid-er.json
python3 {skill-root}/scripts/check-entity-coverage.py --prd <each-prd-or-shard> --d19 {primary} -o {ws}/.scan/entity-coverage.json
python3 {workflow.er_consistency_script} {primary} --project-root {project-root} --sources "<D-02,D-06>" [--code-dir {project-root}/<models>] -o {ws}/.scan/er-consistency.json
```

`check-er-consistency.py` is **advisory** (B2-2 entity↔REQ + uncovered-REQ · B2-3 ondelete cue · B2-7 `schema_drift` log-every-divergence · B2-9 churn) — blocking gate is [IR]/Phase-2; surface each finding, never auto-add. Pass each PRD path/shard as separate `--prd`; surface `prd_entity_extraction_empty`. Add LLM judgment (normalization, relationship completeness, naming, index appropriateness, language). Fix: interactive loop; headless applies only `auto_fixable: true` (log via `fix_hint`), else blocked `mermaid_validation_failed`/`entity_coverage_gap`. `stepsCompleted += stage-4`, then the lens menu. Detail: stage-guide § Stage 4.

### 4b. Semantic Review (Layer 2, B2-8)

Before saving, run the semantic review per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** and **facet-split discipline** per entity (read vs write/admin · entity lifecycle · relationship cardinality). Name open facets so downstream D-21 / D-26 / D-27 inherit them. Record `semanticReview` frontmatter: `status: passed` **only when `openFacets` empty AND the user signs off** (T2.12), else `pending` + list. Headless follows the Autonomy mode; never blocks here (Phase 2 gate enforces); never fabricate. Detail: stage-guide § Stage 4b.

### 5. Save and Handoff

Finalize `{primary}` (`stepsCompleted = stage-1..5`, `lastStep = complete`, `updated` = today, `semanticReview` from 4b). Append a closing session block to `.decision-log.md` (sources incl. brownfield `project_knowledge`, scope, tier reached, scope-of-change, decision-records, auto-fixes, lenses, handoff). **B2-6 hand-off note:** the draft logical D-19 is the object the `[DSC]` Model-Spike examines at the P1→P2 seam (T3.17 reposition is a later unit — note the touchpoint, don't reposition). Consumers: `hbc-create-coding-standards`, `hbc-create-api-spec`, `hbc-task-breakdown`. Check `{workflow.on_complete_distillate}` (`always`/`offer`/`never`). Headless: emit the JSON return contract. Detail: stage-guide § Stage 5.

## On Complete

Read `{workflow.on_complete}` from the resolved workflow block. If non-empty, follow it. Otherwise invoke `bmad-help`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`. Suppression guard (BR-13): `--invoked-by-sync` / `invoked_by_sync=true` → skip. Default: suggest `hbc-traceability impact`; auto-chained when `{workflow.auto_sync_after_update}` is true (default false).

**Matrix column (B7-2):** on save (create or update), run `hbc-traceability update feature={feature}` so this phase self-writes its `design_ref` column — don't defer to a manual step (the Phase-2 gate cascade-precheck blocks if missing). This column-write is distinct from / lighter than the `impact` cascade above.
