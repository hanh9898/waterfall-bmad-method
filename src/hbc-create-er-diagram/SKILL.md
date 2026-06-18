---
name: hbc-create-er-diagram
description: "Generate D-19 Database Design Document with ER Diagram in Mermaid from PRD, Architecture, or interactive input. Use when user says 'create ER diagram', 'create D-19', 'tạo sơ đồ ER', 'vẽ sơ đồ ER', or 'vẽ D-19'."
---

# Create ER Diagram (D-19)

## Overview

Produces a D-19 Database Design Document — Mermaid `erDiagram` with entities, relationships, and attribute specs. Reads PRD / Architecture / UX from `{planning_artifacts}` when available (and `bmad-document-project` output from `{project_knowledge}` when brownfield), falls back to interactive elicitation otherwise. Output is a single D-19 file written into the resolved workspace; the decision log (`.decision-log.md`) and scan artifacts (`.scan/`) are its peers.

Five stages: prerequisites → discovery → generation → validation → handoff. Supports `-H` / `--headless`. Verbose per-stage prose, menus, and Mermaid notation live in [`references/stage-guide.md`](references/stage-guide.md); the headless flag set, defaults, and JSON return contract in [`references/headless-contract.md`](references/headless-contract.md). This file is the control flow of record — where the stage guide expands a step, both must agree.

## Conventions

- Bare paths (e.g. `references/foo.md`) resolve from the skill root. `{skill-root}` = this skill's installed directory (where `customize.toml` lives); `{project-root}`-prefixed paths resolve from the project working directory; `{skill-name}` = the skill directory basename.
- Placeholders (`{skill-name}`, `{primary}`, `{user_name}`, …) are substituted with resolved values before any output is emitted or written.

## Language Rules

- Communicate with the user in `{communication_language}`.
- Templates from `{workflow.er_diagram_template}` and `assets/decision-log-template.md` are English-source i18n skeletons: when rendering, translate all prose (headings, table headers/contents, comments, revision-history entries) to `{document_output_language}` — never emit the template verbatim. File and folder names stay English (kebab/snake-case); never embed `{document_output_language}` characters in a path.
- Carve-outs that keep original form: Mermaid keywords (`erDiagram`, `PK`, `FK`, `UK`, `||--o{`, `}o--||`, …), SQL types (`INTEGER`, `VARCHAR`, `TIMESTAMP`, `TEXT`, `BOOLEAN`), constraint labels (`NOT NULL`, `AUTO_INCREMENT`, `UNIQUE`).

## On Activation

> **Scope DUAL + feature (B):** by default write/read the baseline `shared/erd/` (`{workflow.er_diagram_output_path}`); pass `feature=<slug>` → create/read a **per-feature override** (`{workflow.er_diagram_feature_path}`, path-existence precedence).

Resolve the `{workflow.*}` block: run `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`. If missing, hand-merge `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml` (scalars override, arrays append, arrays-of-tables keyed by `code`/`id` replace). Keep the resolved block in memory for the whole session.

Execute `{workflow.activation_steps_prepend}` in order. Load `{workflow.persistent_facts}` (entries prefixed `file:` are paths/globs; others are verbatim facts).

Load config from `{project-root}/_bmad/config.yaml` and `config.user.yaml` (root + `core` + `modules.bmm`). Fall back to `.toml` variants, then legacy `{project-root}/_bmad/bmm/config.yaml`. Resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, `{planning_artifacts}`, `{project_knowledge}`, `{project_name}`.

Greet `{user_name}` in `{communication_language}` with a one-sentence orientation (D-19 produces a database design document with Mermaid ER diagrams across five stages). D-19 opens Phase 2, so it expects the Phase 1 gate (`hbc-phase-gate` evaluate 1) to have passed. Execute `{workflow.activation_steps_append}` in order.

## Headless Mode

`-H` / `--headless` runs without prompts. Full contract — flags, defaults, JSON return shape, closed-set blocker `reason` values — in [`references/headless-contract.md`](references/headless-contract.md). Reason values: `template_missing`, `no_prd_and_no_interactive_in_headless`, `planning_artifacts_unreadable`, `mermaid_validation_failed`, `entity_coverage_gap`, `no_entities_found`, `resolver_missing`. Extend this list and the contract file together.

## Workflow

The numbered steps below are the authoritative control flow. [`references/stage-guide.md`](references/stage-guide.md) carries the expanded prose for each (menus, intent gate, off-ramp, Mermaid notation, judgment checks) — consult it as you run each stage.

### 1. Prerequisites and Scope

**1a. Resolve DUAL scope, bind workspace, detect resume.** D-19 has two homes — a **shared baseline** (`{workflow.er_diagram_output_path}`, `shared/erd/`) and a **per-feature override** (`{workflow.er_diagram_feature_path}`, `features/{feature}/planning-artifacts/`):

1. Resolve `{feature}`: `feature=<slug>` arg wins; else session active-feature; else interactive (ask baseline vs per-feature override) / headless (no feature → shared baseline, do NOT block).
2. Bind output FILE `{primary}` and workspace `{ws}`: per-feature → `{workflow.er_diagram_feature_path}` + `{ws}={output_folder}/features/{feature}/planning-artifacts`; shared → `{workflow.er_diagram_output_path}` + `{ws}={output_folder}/shared/erd`.
3. **Path-existence precedence:** an existing per-feature override takes precedence over the baseline for resume/read; downstream readers check per-feature first, then fall back to baseline.

**Resolve log line (REQUIRED).** After binding, emit one explicit log line — to the user (interactive) and always to `.decision-log.md` — naming which path won, so a wrong-baseline pickup is never silent: `D-19 resolved to per-feature override <path> (feature=<slug>)`, or `D-19 resolved to shared baseline <path> (no feature override)`; when an override shadows the baseline on resume/read, log `D-19 per-feature override <path> takes precedence over shared baseline <path>`.

`{primary}` is a single FILE; `.decision-log.md` and `.scan/` are its peers in `{ws}`. Create `{ws}` and `{ws}/.scan/` if absent. The decision-log / `.scan` / output references resolve against `{ws}`; **source** discovery still scans the project-level `{planning_artifacts}` (and `{project_knowledge}` when brownfield).

Run the discover script (add `--project-knowledge {project_knowledge}` when this is a **brownfield** project so the D-19 baseline also ingests the `bmad-document-project` output — its `index.md`, project docs, and existing DB schema — not just the PRD; omit for greenfield):

```
python3 {skill-root}/scripts/discover-planning-artifacts.py {planning_artifacts} --template-path {workflow.er_diagram_template} --primary {primary} [--project-knowledge {project_knowledge}] -o {ws}/.scan/artifacts.json
```

Consume the JSON. Non-zero exit / no output → proceed as if `artifacts_dir_exists: false` and `recommended_intent: "Fresh"` (log the error). `fatal: "template_missing"` → HALT (interactive) / `blocked` `reason: "template_missing"` (headless). Otherwise branch on `resume_state.recommended_intent` / `fresh_reason` and present the resume/update menu — see stage-guide §1a for the menu, every `fresh_reason` branch, and the headless resolution. If `.decision-log.md` is absent at session start, initialize it from `{workflow.decision_log_template}`.

**1b. Open-floor, intent gate, wrong-skill off-ramp (interactive only).** Invite the user to share schemas / SQL DDL / prior ERDs / data dictionaries / ORM models; confirm intent (capture existing / design new / both); fire the wrong-skill off-ramp (D-20 column DDL · D-17 sequence · D-18 class) before heavier work. Short-circuit 1e only when the reply explicitly covers scope + sources + normalization level. Skipped entirely in headless. See stage-guide §1b / §1b′ (brainstorming suggestion).

**1c. Consume source inventory** from `artifacts.json`: PRD set (shards enumerated by the script — do not re-glob), Architecture, UX/use-case/research, existing D-20, and (brownfield) the `project_knowledge` block — treat existing DB schema as authoritative ground truth where it disagrees with PRD inference, and log the discrepancy. `artifacts_dir_exists: false` → 1d.

**1d. No-PRD HALT menu** — zero PRDs and no `--prd-path`: offer run-PRD / provide-path / greenfield-elicitation / quit. Headless: `--no-prd-ok` → greenfield silently; else `blocked` `reason: "no_prd_and_no_interactive_in_headless"`. See stage-guide §1d.

**1e. Inferred-defaults confirmation** (interactive, unless short-circuited by 1b) — see stage-guide §1e for the menu. Then initialize the primary from `{workflow.er_diagram_template}` (translated), append a session block to `.decision-log.md`, mark `stepsCompleted` += `stage-1`, set `updated` to today.

### 2. Discovery

Run the entity-candidate pre-pass:

```
python3 {skill-root}/scripts/extract-entity-candidates.py <source-paths...> -o {ws}/.scan/entity-candidates.json
```

Use the candidate JSON as a starting point (full LLM extraction if `"warn": "entity_extraction_empty"`). Extract entities, attributes, relationships, constraints, indexes; group by domain for multi-domain scope; present for confirmation. **Zero-entity branch:** no identifiable entities → do not render a vacuous diagram; interactive confirm / headless `blocked` `reason: "no_entities_found"`.

**Compaction-flush (required)** at stage end: write `stage_2_entities` and `stage_2_relationships` to primary frontmatter, append a `### Discovery snapshot (Stage 2 flush)` block to `.decision-log.md`, mark `stepsCompleted` += `stage-2`. See stage-guide §2.

### 3. Diagram Generation

Render one Mermaid `erDiagram` per domain area (`||--o{` one-to-many, `||--||` one-to-one, `}o--o{` many-to-many; physical names as identifiers). Large schemas (>15 entities): split into H2 sub-domain sections + a master overview, all in one file. Add the **table definitions** section per entity and an **index definitions** section if indexes were found. Populate the **revision history** with the scope-of-change gate (Create → v1.0; Update → polish vs semantic, auto-detect by diffing Stage 2 flush, `--scope-of-change` override). Mark `stepsCompleted` += `stage-3`. Then present the **Parallel-lens menu** (`--review-lenses`, default `skip`; inline fallback if a lens skill is missing). Full notation, large-schema rules, and lens menu in stage-guide §3.

### 4. Validation

Run the two deterministic validators (independent, may run concurrently):

```
python3 {skill-root}/scripts/validate-mermaid-er.py {primary} --expected-entities "<comma-separated stage-2 entities>" -o {ws}/.scan/mermaid-er.json

python3 {skill-root}/scripts/check-entity-coverage.py --prd <each-prd-path-or-shard> --d19 {primary} -o {ws}/.scan/entity-coverage.json
```

Pass each PRD path/shard as a separate `--prd`; surface `"warn": "prd_entity_extraction_empty"`. Add the LLM judgment checks (normalization, relationship completeness, naming consistency, revision history, language consistency). Fix: interactive collaborative loop; headless applies only `auto_fixable: true` issues (log each via `fix_hint`), else `blocked` `reason: "mermaid_validation_failed"` / `"entity_coverage_gap"`. Mark `stepsCompleted` += `stage-4`, then the Parallel-lens menu (Stage-4 targets: edge cases). See stage-guide §4.

**4b. Semantic Review (Layer 2).** Before saving, run the semantic review per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with the facet-split discipline (read vs write/admin surface · entity lifecycle · relationship cardinality). Name open facets so downstream D-21 / D-26 / D-27 inherit them. Record `semanticReview` frontmatter (`status: passed` only when `openFacets` empty, else `pending` + list). Headless: same rubric, never block here (Phase 2 gate enforces), never fabricate coverage. See stage-guide §4b.

### 5. Save and Handoff

Finalize `{primary}`: `stepsCompleted` = `stage-1..5`, `lastStep` = `complete`, `updated` today, `semanticReview` block from 4b. Append a closing session block to `.decision-log.md` (sources used incl. brownfield `project_knowledge` ingest, scope, level, scope-of-change, auto-fixes, lenses, handoff target). Downstream consumers: `hbc-create-coding-standards`, `hbc-create-api-spec`, `hbc-task-breakdown`. Check `{workflow.on_complete_distillate}` (`always` / `offer` default / `never`); skip with a note if distillator unavailable. Headless: emit the JSON return contract per [`references/headless-contract.md`](references/headless-contract.md). See stage-guide §5.

## On Complete

Read `{workflow.on_complete}` from the resolved workflow block. If non-empty, follow it as the final instruction. Otherwise, invoke `bmad-help`.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"The document has been updated. Run `hbc-traceability impact` to sync the dependent documents/tests/code?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly. Default is false.
