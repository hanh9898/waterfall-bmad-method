# Stage Guide — hbc-create-er-diagram

Communicate with the user in `{communication_language}`.

Detailed prose for the five-stage workflow. `SKILL.md` carries the lean control flow and points here for the verbose menus, Mermaid notation, and per-stage judgment detail. Behavior is identical to what SKILL.md mandates — this file expands it, it does not override it.

## Conventions (path & placeholder resolution)

- Bare paths (e.g. `references/foo.md`) resolve from the skill root.
- `{skill-root}` = this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` = the skill directory basename.
- Placeholders (`{skill-name}`, `{primary}`, `{user_name}`, …) are substituted with resolved values before any output is emitted or written.

## Language Rules

- Communicate with the user in `{communication_language}`.
- Templates from `{workflow.er_diagram_template}` and `{workflow.decision_log_template}` are English-source i18n skeletons: when rendering, translate all prose (headings, table headers/contents, comments, revision-history entries) to `{document_output_language}` — never emit the template verbatim. File and folder names stay English (kebab/snake-case); never embed `{document_output_language}` characters in a path.
- Carve-outs that keep original form: Mermaid keywords (`erDiagram`, `PK`, `FK`, `UK`, `||--o{`, `}o--||`, …), SQL types (`INTEGER`, `VARCHAR`, `TIMESTAMP`, `TEXT`, `BOOLEAN`), constraint labels (`NOT NULL`, `AUTO_INCREMENT`, `UNIQUE`).

## On Activation (detail)

> **Scope DUAL + feature (B):** by default write/read the baseline `shared/erd/` (`{workflow.er_diagram_output_path}`); pass `feature=<slug>` → a per-feature override (`{workflow.er_diagram_feature_path}`, path-existence precedence).

1. **Resolve the workflow block.** Run `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`. On failure, hand-merge `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml` (scalars override, tables deep-merge, arrays-of-tables keyed by `code`/`id` replace+append, other arrays append). Keep the resolved `{workflow.*}` block (incl. `{workflow.on_complete}`) in memory all session.
2. **Execute `{workflow.activation_steps_prepend}`** in order.
3. **Load `{workflow.persistent_facts}`** (entries prefixed `file:` are paths/globs; others are verbatim facts).
4. **Load config** from `{project-root}/_bmad/config.yaml` and `config.user.yaml` (root + `core` + `modules.bmm`). Fall back to `.toml`, then legacy `bmm/config.yaml`. Resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, `{planning_artifacts}`, `{project_knowledge}`, `{project_name}`.
5. **Greet `{user_name}`** in `{communication_language}` with a one-sentence orientation (D-19 produces a database design document with Mermaid ER diagrams, built conceptual → logical → physical across five stages). D-19 opens Phase 2, so it expects the Phase 1 gate (`hbc-phase-gate` evaluate 1) to have passed. Execute `{workflow.activation_steps_append}` in order.

## Autonomy (A5) — detail

Separate **mechanical** decisions (entity layout, attribute ordering, snake_case formatting, which Mermaid notation to use — decide and proceed, note in the decision log) from **domain** decisions (which entities/relationships are in scope, the normalization level/tier, the ondelete behavior on each FK, whether a no-REQ entity is a phantom — **ASK; never invent a default**).

The three tier confirmations (conceptual → logical → physical, Stage 3) are **hard ASK-gates**: generation does not descend to the next tier until the current tier is confirmed. The previous behavior (infer the whole physical schema, then ask "anything to adjust?") is the pattern that let an un-scoped entity or a silently-chosen CASCADE slip through.

**Headless (the Autonomy modes):**
- `--strict` returns `blocked` with `reason: "tier_unconfirmed"` at the first domain decision (a tier confirmation, an ondelete behavior, or an entity/relationship scope choice) that the flags did not pin down.
- `--assumptions-allowed` (CI default) takes the most defensible option, logs it to `.decision-log.md` as an `ASSUMPTION` (which tier/ondelete/scope it assumed and why), and continues. It never blocks on the first question.

## Parallel-lens menu

Used at the end of Stage 3 and Stage 4. In headless mode the choice is taken from `--review-lenses=skip|advanced|party` (default `skip`); every fire is appended to `review_lenses_run` in the JSON return contract. If the invoked lens skill is not installed, perform the review inline using the same analytical framing and log the fallback to `.decision-log.md`.

```
[A] Advanced Elicitation — single deep lens via bmad-advanced-elicitation (~5 min).
[P] Party Mode — three parallel lenses (analyst + architect + DBA) via bmad-party-mode (~15 min).
[C] Continue — proceed without an additional review pass.
```

Headless mapping: `--review-lenses=skip` → `[C]`, `advanced` → `[A]`, `party` → `[P]`.

## Stage 1 — Prerequisites and Scope (expanded)

### 1a. DUAL scope, workspace bind, resume detect

**Scope resolution (DUAL — path-existence precedence).** D-19 has two homes: a project-wide **shared baseline** (`{workflow.er_diagram_output_path}`, under `shared/erd/`) and a **per-feature override** (`{workflow.er_diagram_feature_path}`, under `features/{feature}/planning-artifacts/`). Resolve the active scope before binding:

1. Resolve `{feature}`: a `feature=<slug>` arg wins; else an active-feature value carried in the session; else — **interactive**: ask whether this D-19 is the shared baseline or a per-feature override (and for which feature); **headless**: if no feature is resolvable, default to the shared baseline (do NOT block — D-19 baseline is legitimately shared).
2. Bind the active output FILE `{primary}` and its workspace dir `{ws}`:
   - **Per-feature override** (feature resolved): `{primary} = {workflow.er_diagram_feature_path}` (substitute `{feature}`); `{ws} = {output_folder}/features/{feature}/planning-artifacts`.
   - **Shared baseline** (no feature): `{primary} = {workflow.er_diagram_output_path}`; `{ws} = {output_folder}/shared/erd`.
3. **Path-existence precedence** (resume/read): if a per-feature override already exists for the active feature, it takes precedence over the shared baseline for resume/update detection; a downstream reader resolves D-19 by checking the per-feature path first, then falling back to the shared baseline.

**Resolve log line (REQUIRED — no silent baseline pickup).** After binding, emit one explicit log line — to the user (interactive) and to `.decision-log.md` (always) — naming which path won and why, so a wrong-baseline pickup is never silent. Use the form:
- per-feature override taken: `D-19 resolved to per-feature override <{primary}> (feature=<slug>)`
- shared baseline taken: `D-19 resolved to shared baseline <{primary}> (no feature override)`
- when a per-feature override exists and shadows the baseline on a resume/read, state that explicitly: `D-19 per-feature override <path> takes precedence over shared baseline <path>`.

`{primary}` is a single output FILE (no per-document folder). The decision log lives at `{ws}/.decision-log.md` and scan artifacts at `{ws}/.scan/` — both peers of `{primary}`. Create `{ws}` and `{ws}/.scan/` if absent. The decision-log / `.scan` / output references resolve against `{ws}` for the active scope; PRD / Architecture / brownfield **source** discovery still scans the project-level `{planning_artifacts}` (and `{project_knowledge}` when brownfield).

Run the discover script (see SKILL.md for the exact invocation, including `--project-knowledge` when brownfield). Consume the JSON. If the script exits non-zero or produces no output, proceed as if `artifacts_dir_exists: false` and `resume_state.recommended_intent: "Fresh"` — log the error and exit code to `.decision-log.md`. If `fatal: "template_missing"` → HALT (interactive) or return `blocked` with `reason: "template_missing"` (headless). Otherwise read `resume_state.recommended_intent` / `fresh_reason`:

- `Fresh` / `no_primary` — no primary document at all. Initialize from template.
- `Fresh` / `crashed_no_progress` — primary exists but `stepsCompleted` is empty (prior run crashed before stage-1 write). Surface the crash in the menu and decision log. Headless: log `fresh_reason`.
- `Fresh` / `stale_artifact` — inconsistent step state (e.g. stage-2 completed but stage-1 missing). Surface the inconsistency; offer to reset or continue from the last consistent stage.
- `Resume` — primary has `stage-1` and not `stage-5`. Show `resume_state.last_session_summary`; offer to continue from `primary_last_step`.
- `Update` — primary completed (`stage-5`). Treat as revisable: read latest revision-history version. Stage 3 gates the version bump on scope-of-change.

Present this menu (interactive only):

```
Recommended: {recommended_intent}{ if fresh_reason: " ({fresh_reason})" }
Last session: {resume_state.last_session_summary}
Steps complete: {resume_state.primary_steps_completed}

[R] Resume — pick up where the previous session stopped
[U] Update — revise this ER diagram as a new revision-history row
   [U1] Update all entities
   [U2] Update a single named entity (specify name)
[V] Validate-only — re-run Stage 4 against the current output
[N] Start fresh — archive the current primary and begin again
[X] Exit
```

**Headless resolution:** take `resume_state.recommended_intent`; log the auto-choice (plus `fresh_reason` if applicable) to `.decision-log.md`. For targeted single-entity update, the automator uses `--update-entity=<name>` (see headless contract).

If `.decision-log.md` is absent at session start, initialize it from `{workflow.decision_log_template}` — interpolate placeholders (`{skill-name}`, `{project_name}`, `{user_name}`, date) the same way Stage 1e interpolates the primary template.

### 1b. Open-floor, intent gate, wrong-skill off-ramp (interactive only)

Before consuming the source inventory from 1a, invite the user to share anything not yet captured — existing database schemas, SQL DDL files, prior ER diagrams, data dictionaries, ORM model files. Adapt the invitation to context.

Then one intent check: capturing an existing database schema, designing a new one, or both.

**Wrong-skill off-ramp** (must fire before any heavier work): if the reply signals a different artifact, redirect. Trigger terms — D-20 or "column-level DDL" / "all constraints" / "every column spec" → D-20 table definitions; D-17 or "sequence diagram" / "API flow" / "call flow" → D-17; D-18 or "class diagram" / "class hierarchy" / "service structure" → D-18. D-19 focuses on the high-level ER diagram and entity overview, not per-column DDL.

**Short-circuit Stage 1e** — strict gate. Only skip 1e when the open-floor reply *explicitly* covers **all three** of: scope (which domain areas), sources (which docs to include or exclude), and normalization level (conceptual vs logical vs physical). A partial reply falls through to 1e for confirmation. Log which dimensions were inferred from 1b vs confirmed in 1e to `.decision-log.md`.

In headless mode 1b is skipped entirely.

### 1b′. Brainstorming suggestion (interactive only, Fresh state only)

If the user is designing a new database (not capturing existing schema) and the domain model is complex or ambiguous, suggest: _"The domain model is complex — want to run `bmad-brainstorming` first to explore entity relationships and normalization trade-offs? The output will feed into D-19."_ If declined, proceed. If accepted, pause for a separate brainstorming session. If a brainstorming session file exists in `{output_folder}/brainstorming/`, load it as supplementary context for entity discovery. Skip for schema-capture intent or Update/Resume states.

### 1c. Consume source inventory

Consume `artifacts.json` from Stage 1a into:
- PRD set (whole-doc or shard set — the discover script enumerates every shard automatically; do not re-glob)
- Architecture docs
- UX, use-case, research candidates
- Existing D-20 table definitions (if any)
- **Brownfield only:** `project_knowledge` block — the `bmad-document-project` index, project docs, and existing DB schema files (`*.sql`, `*schema*`, `*.prisma`, ORM model dirs). Treat existing schema as authoritative ground truth for the baseline ERD: the real DB shape wins over PRD inference where they disagree, and the discrepancy is logged.

If `artifacts_dir_exists` is false → note it and proceed to the no-PRD HALT-menu below.

### 1d. No-PRD HALT menu

If `artifacts.json` returned zero PRDs AND `--prd-path` was not provided:

```
No PRD found in {planning_artifacts}
Options:
[1] Run `bmad-prd` first (recommended)
[2] Provide PRD path
[3] Continue with interactive elicitation (greenfield, no source)
[q] Quit
```

**Headless resolution:** if `--no-prd-ok` is set, take option 3 silently and log it. Otherwise return `blocked` with `reason: "no_prd_and_no_interactive_in_headless"`.

### 1e. Inferred-defaults confirmation (interactive only, unless short-circuited by 1b)

```
Detected: {prd_count} PRD doc(s), {arch_count} Architecture doc(s), {d20_count} D-20 doc(s)
Inferred: scope={single-domain|multi-domain}, level={conceptual|logical|physical}

[C] Confirm and proceed
Or specify overrides: scope=… / level=… / sources=include:…,exclude:… (e.g. sources=include:planning/prd-orders.md,exclude:*research*)
```

Initialize the primary document from `{workflow.er_diagram_template}`, translating template prose to `{document_output_language}` per the Language Rules. Append a new session block to `.decision-log.md`. Mark `stepsCompleted` to include `stage-1`. Set primary frontmatter `updated` to today.

## Stage 2 — Discovery (expanded)

Run the entity-candidate pre-pass on the chosen sources:

```
python3 {skill-root}/scripts/extract-entity-candidates.py <source-paths...> -o {ws}/.scan/entity-candidates.json
```

Use the candidate JSON as a starting point — confirm, merge, and fill gaps rather than free-reading raw sources. If the script returns `"warn": "entity_extraction_empty"`, note that mechanical extraction found nothing and proceed with full LLM extraction from sources.

From the candidates and source documents, extract:
- **Entities** — domain objects, data models, aggregates (in `{document_output_language}` for logical names, English for physical names)
- **Attributes** — key fields per entity with types (PK, FK, data type)
- **Relationships** — cardinality between entities (one-to-one, one-to-many, many-to-many)
- **Constraints** — unique keys, NOT NULL, business rules that affect schema
- **Indexes** — performance-critical access patterns identified from use cases

Present extracted entities and relationships for confirmation. For multi-domain scope, group entities by bounded context / domain area.

**Conceptual reconciliation against REQ + D-06 (B2-5).** The conceptual entity set reconciles against **both** the requirements (D-02 REQ ids) **and** the D-06 business-flow — not the PRD prose alone. A business-flow actor, state, or hand-off that has no entity to persist it is a gap; an entity that no flow ever touches is a candidate phantom. Every entity and every relationship should trace to **≥1 REQ** (B2-2) — record the REQ id(s) against each (in the table-definition prose or a Mermaid `%% REQ-…` comment) so the advisory `check-er-consistency.py` (Stage 4) finds the trace. An entity that genuinely has no REQ (a pure join table, an audit-only table) is recorded with a one-line reason, not left silently un-traced.

**Zero-entity branch** — if the source contains no identifiable data entities (e.g. pure API gateway or static content project), do not render a vacuous diagram. Inform the user that D-19 may not be applicable and suggest alternative documentation. Interactive: confirm with the user. Headless: log and return `blocked` with `reason: "no_entities_found"`.

**Compaction-flush at the end of this stage** (required, not optional). Before moving on:
- Write entity list as `stage_2_entities: ["EntityA", "EntityB", ...]` and relationship list as `stage_2_relationships: ["EntityA->EntityB:one-to-many", ...]` to the primary document's frontmatter.
- Append a `### Discovery snapshot (Stage 2 flush)` block to `.decision-log.md` carrying entities, relationships, and attribute summaries verbatim.
- Update primary frontmatter `stepsCompleted` to include `stage-2` and `updated` to today.

If compaction drops the conversation mid-stage, the next run resumes from these artifacts rather than re-eliciting.

## Stage 2b — Grounding-to-code (B2-7)

For a **brownfield / migration** D-19, the model must be grounded in the **real database** — the live schema, the ORM model definitions, the migration scripts — not the PRD's narration of "the data we have". A PRD describes intent; the schema is what exists. Read the real models/migrations and, for each entity the design declares, check it against the ground truth:

- The advisory `check-er-consistency.py` (Stage 4, with `--code-dir`) computes `schema_drift` **structurally**: `design_only` = a model the D-19 declares (physical `_name`) but code never defines; `code_only` = a persistent model in code the design never declares. **LOG EVERY divergence** in the template's *Grounding-to-code log* table: the model/entity, the ground-truth source (a code reference like `models/resource_plan.py:_name`, or "migration NNNN"), and the resolution.
- A `design_only` divergence is one of two things, and the **judgment** (not the script) decides which: **planned-not-yet-built** (the design is ahead of code — legitimate, record it as planned) or **stale design** (the code moved on and the design rots — fix the design to match). A `code_only` divergence is an undocumented model — add it to the design or record why it is out of scope.
- A divergence is **never a silent overwrite**: surface it so the user decides whether the diagram follows the code (usual) or the design leads (planned). Greenfield (no existing code/schema): write a single `N/A — greenfield, no existing schema to ground against` row; do not fabricate a code reference.
- **Headless:** run the grounding where code is reachable; log divergences. Under `--strict` an unresolved divergence blocks (domain decision); under `--assumptions-allowed` log it as an `ASSUMPTION` (diagram follows code) and continue.

## Stage 3 — Diagram Generation, 3-tier ASK-gate (B2-1, expanded)

Generation descends **three tiers**, with a **hard ASK-gate before each descent** (B2-1) — confirm the current tier with the user (or, headless, resolve per the Autonomy mode) before building the next. Do not jump straight to the physical schema.

### Tier 1 — Conceptual (ASK-gate before descending)

Entities and relationships only — **no attributes**. One `erDiagram` per domain area showing entity names + relationship lines + cardinality. Reconciled against REQ + D-06 (Stage 2, B2-5). **ASK-gate:** present the conceptual model and confirm the entity set + relationships are right *before* adding attributes. A wrong entity caught here is cheap; caught at the physical tier it has dragged columns, FKs, and indexes with it.

### Tier 2 — Logical (ASK-gate before descending)

Add attributes, keys, and normalization to the confirmed conceptual model. Two domain decisions are asked here, never defaulted:

- **Ondelete behavior (B2-3).** For **each FK**, ASK which referential action applies — `CASCADE` (child dies with parent), `RESTRICT` / `NO ACTION` (block the delete), `SET NULL` (orphan the child), `SET DEFAULT`. Never silently pick `CASCADE` or `RESTRICT`. **Record the chosen behavior AND its rationale** in the table-definition row (e.g. `ON DELETE SET NULL — active_request_id may outlive the request`). The advisory check counts FK lines with vs without an ondelete behavior so an un-decided FK is visible; whether the chosen behavior is *correct* and whether a rationale is present is judgment (here + Stage 4b).
- **Indexes as PROPOSALS (B2-4).** Indexes are **suggested, not imposed**. Derive candidate indexes from the access patterns in the use-cases/flows and present them as *proposals* the user accepts, rejects, or defers — an index is a physical-tuning decision the team owns, not something D-19 mandates. Mark proposed-but-unconfirmed indexes as such in the index table.

**ASK-gate:** confirm the logical model (attributes + keys + ondelete behaviors + index proposals) before generating physical names.

### Tier 3 — Physical

Render physical identifiers: `snake_case` entity/attribute names, concrete SQL types (`INTEGER`, `VARCHAR`, …), concrete constraints (`NOT NULL`, `UNIQUE`, `AUTO_INCREMENT`).

### Rendering rules (all tiers)

- Mermaid ER notation: `||--o{` (one-to-many), `||--||` (one-to-one), `}o--o{` (many-to-many), with labels.
- **No `;` in a relationship label** — Mermaid parses an unquoted semicolon as a statement separator, so `A ||--o{ B : tạo;xử lý` fails to render. Use `,` instead. (Stage 4 flags any leftover `;` as auto-fixable.)
- Physical names for identifiers; logical names as comments or in the table-definitions section. Cite the REQ each entity realizes (a `%% REQ-…` comment or the table-definition prose) so entity↔REQ traceability (B2-2) is checkable.
- Large schemas (>15 entities): split into H2-separated sub-domain sections within the single primary file, plus a master overview diagram (entity names + relationships only, no attributes). One file, so Stage 4 validation covers every section.

**Table definitions section** — below each ER block, per entity: logical name, physical name, description; key columns with types + constraints + **ondelete behavior + rationale**; FK references.

**Index definitions section** — the index table (proposals from Tier 2), marking unconfirmed proposals.

**Decision-record → ADR (B2-10).** Record every non-trivial DB decision — each ondelete choice, normalization vs denormalization trade-off, a STORED-vs-view choice, a partial-unique constraint — in a *decision-record* block in `.decision-log.md`: the decision, the options weighed, the rationale. Note `→ ADR` against each. *Forward-reference (advisory):* these records are the raw material for a future Architecture Decision Record; the first-class ADR engine + decision-gate (T2.5) is **not built yet**, so wire the touchpoint (write the records, tag them `→ ADR`) without building the ADR machinery here — the same forward-ref discipline U3 used for cascade and U6 for the Model-Spike.

**Revision history table — scope-of-change gate (anti-churn, B2-9 / T2.11).** Bump the version **once per session**, not once per edit — batch a session's changes into one revision row:

- **Create / Fresh**: today's date, version `1.0`, "Initial version" → `{user_name}`, translated to `{document_output_language}`.
- **Update** — determine scope-of-change first:
  - **Auto-detect default:** compare current `stage_2_entities` / `stage_2_relationships` against the prior session's flush block in `.decision-log.md`. Both identical → **polish** (append a note to the latest row). Either differs → **semantic** (append a new row, bump minor).
  - **Manual override** (interactive): "polish (typo / wording / layout) or semantic (entities / relationships / attributes)?".
  - **Headless override:** `--scope-of-change=polish|semantic|auto` (default `auto`).
  - Log the chosen scope + rationale to `.decision-log.md`.
- **High churn:** if the revision history is already long (the advisory `check-er-consistency.py` `churn.high_churn` is true, or the table is visibly long), the model is **not frozen yet**. Surface it and suggest the user set `maturity: exploratory` or run a `[DSC]` model-spike to stabilize the schema, rather than appending yet another revision row.

Update primary frontmatter `stepsCompleted` to include `stage-3` and `updated` to today.

Then present the **Parallel-lens menu** (above). Stage-3 lens-targets: stress-test entity completeness, relationship cardinality correctness, and normalization-tier appropriateness.

## Stage 4 — Validation (expanded)

Run the three deterministic validators (independent — may run concurrently):

```
python3 {skill-root}/scripts/validate-mermaid-er.py {primary} --expected-entities "<comma-separated stage-2 entities>" -o {ws}/.scan/mermaid-er.json

python3 {skill-root}/scripts/check-entity-coverage.py --prd <each-prd-path-or-shard> --d19 {primary} -o {ws}/.scan/entity-coverage.json

python3 {workflow.er_consistency_script} {primary} --project-root {project-root} --sources "<D-02 path,D-06 path>" [--code-dir {project-root}/<models-dir>] -o {ws}/.scan/er-consistency.json
```

`check-er-consistency.py` is **advisory** (B2-2/B2-3/B2-5/B2-7/B2-9) — the *blocking* cross-doc gate is `hbc-check-implementation-readiness` [IR] / the Phase-2 gate, and Mermaid *rendering* is `validate-mermaid-er.py` / `npm run check:mermaid`. Per the honest-verdict contract it reports:
- `phantom_entity_blocks` (B2-2) — erDiagram blocks citing no REQ id. Surface each: cite the REQ each entity realizes, or record why it is structural-only. Never auto-add.
- `uncovered_reqs` (B2-2/B2-5) — REQs defined in `--sources` (D-02 **+ D-06**) referenced nowhere in D-19: model them, or record why they need no schema. Only computed when `--sources` is supplied; `multi_feature_sources: true` means >1 feature slug appeared and the count is unreliable (single-feature trailing-number identity collides).
- `schema_drift` (B2-7) — `design_only` / `code_only` models when `--code-dir` is supplied. Every divergence is logged to the Grounding-to-code log (Stage 2b). Only computed with `--code-dir`.
- `ondelete` (B2-3 cue) — `fk_lines` vs `fk_with_ondelete`: a large `fk_without_ondelete` count means FKs were left without a decided behavior. Cue only; the rationale is judgment.
- `churn` (B2-9 cue) — revision-row count + `high_churn` (order-robust). Advisory; never blocks.

The flow-coverage findings are **advisory**: log them and surface to the user; they do not block the headless run, and the skill never auto-adds an entity/REQ to satisfy them.

Pass each PRD path (or each shard from `artifacts.json`) as a separate `--prd` to `check-entity-coverage`; pass D-02 **and D-06** to `--sources` of the consistency check. If `entity-coverage.json` contains `"warn": "prd_entity_extraction_empty"`, surface it: "PRD entity extraction found zero entities — coverage check may be incomplete; manual review recommended." If any validator cannot run at all (Python missing, crash), note in `.decision-log.md` that script validation was unavailable and fall back to LLM-only judgment for that check.

Judgment checks (LLM, not script):
- **Normalization** — entities are appropriately normalized for the chosen tier (no unnecessary redundancy at the logical tier; acceptable denormalization at the physical tier with justification).
- **Relationship completeness** — every FK has a corresponding relationship line; no orphan entities.
- **Index appropriateness (B2-4)** — proposed indexes match real access patterns; no redundant index; no missing index for a frequent query path. Proposals, not mandates.
- **Naming consistency** — physical names follow a consistent convention (snake_case preferred).
- **Revision history** — populated with version, date, author, change description.
- **Language consistency** — output prose in `{document_output_language}`, carve-outs preserved.

Present consolidated findings (script issues + LLM findings). Fix issues:
- **Interactive:** collaborative fix loop.
- **Headless:** apply only validator issues marked `auto_fixable: true` in `mermaid-er.json`. Log every auto-fix to `.decision-log.md` citing the validator's `fix_hint`. For non-auto-fixable issues, return `blocked` with `reason: "mermaid_validation_failed"` or `reason: "entity_coverage_gap"`.

Update primary frontmatter `stepsCompleted` to include `stage-4` and `updated` to today.

Then present the **Parallel-lens menu** (same as Stage 3). Stage-4 lens-targets: challenge edge cases (nullable FKs, soft deletes, polymorphic associations, temporal data) and check the artifact reads cleanly to a fresh reviewer.

### 4b. Semantic Review (Layer 2)

Script + render validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** (review the schema as an adversary who assumes a facet was cut, not as its author). Apply the **facet-split discipline** per entity (read vs write/admin surface · entity lifecycle — `create` / `update` / `suspend` / `revoke` / `rotate` where the entity has one · relationship cardinality): an entity with a real lifecycle (account, key, subscription) whose state transitions have no representation (no status column, no state machine), or an admin-managed entity with no downstream owner, has an open facet — name it so downstream `hbc-create-api-spec` (D-21) and the test skills (D-26/D-27) know it must be designed and tested, rather than letting the cut-out facet vanish silently (the seam).

Record `semanticReview` frontmatter: `status` is `passed` **only when `openFacets` is empty AND the user signs off** (T2.12); otherwise `pending` + the facet list. The shared `semantic_review_status` is the single structural read of this block, and the Phase 2 gate REVIEW item enforces it.

**Headless:** run the same rubric and write the frontmatter; the sign-off follows the Autonomy mode (`--strict` blocks on a non-empty `openFacets`; `--assumptions-allowed` leaves `status: pending`, logs the open facets, and proceeds). This layer does not block the interactive→gate handoff — the Phase 2 gate enforces it. Never fabricate coverage to force `passed`.

## Stage 5 — Save and Handoff (expanded)

Finalize `{primary}`. Set `stepsCompleted` to the full list (`stage-1..5`), `lastStep` to `complete`, `updated` to today, and the `semanticReview` block from Stage 4b. Append a closing session block to `.decision-log.md` summarising:
- Sources used (including brownfield `project_knowledge` ingest when applicable), scope, normalization tier reached
- Scope-of-change classification (Update mode only) + decision-records written (`→ ADR` tagged)
- Auto-fixes applied (headless)
- Lenses run (`review_lenses_run`)
- Handoff target — which downstream skill should consume this output

**B2-6 — Model-Spike hand-off note (touchpoint only).** The draft **logical** D-19 (Tier 2, before the physical tier hardens it) is the object the `[DSC]` Model-Spike examines at the P1→P2 seam: it is the stable-enough model a spike can stress before the team commits to physical names and migrations. The DSC reposition itself (which spans `[DSC]` / phase-gate / `hbc-agent-architect`) is a **later needs-design unit (T3.17)** — do **not** reposition it here. Just record the hand-off: note in the closing decision-log block that the logical D-19 is available as the Model-Spike input.

Downstream consumers: `hbc-create-coding-standards`, `hbc-create-api-spec`, `hbc-task-breakdown`.

Check `{workflow.on_complete_distillate}`: if `"always"`, invoke `bmad-distillator` against the primary (headless and interactive). If `"offer"` (default), offer interactively; headless skips. If `"never"`, skip entirely. Skip with a note if distillator is unavailable; never inline a substitute.

**Headless mode:** emit the JSON return contract per [`headless-contract.md`](headless-contract.md), substituting every placeholder with its resolved value before emission.
