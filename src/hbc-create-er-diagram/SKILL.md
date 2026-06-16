---
name: hbc-create-er-diagram
description: "Generate D-19 Database Design Document with ER Diagram in Mermaid from PRD, Architecture, or interactive input. Use when user says 'create ER diagram', 'create D-19', 'tạo sơ đồ ER', 'vẽ sơ đồ ER', or 'vẽ D-19'."
---

# Create ER Diagram (D-19)

## Overview

Produces a D-19 Database Design Document following HBLab document conventions — Mermaid `erDiagram` with entity definitions, relationships, and attribute specifications. Reads PRD / Architecture / UX artifacts from `{planning_artifacts}` when available, falls back to interactive elicitation when none exist. Output is a single D-19 file written directly into `{planning_artifacts}` (alongside the other D-* documents); the session decision log (`.decision-log.md`) and scan artifacts (`.scan/`) are shared peers in `{planning_artifacts}` that carry identity across runs.

Supports `-H` / `--headless` for non-interactive generation. Stage 1 honours an input contract so automators can drive it deterministically — see [`references/headless-contract.md`](references/headless-contract.md) for the full flag set, defaults table, and JSON return contract. Stage 5 enumerates the canonical downstream consumers.

## Conventions

- Bare paths (e.g. `references/foo.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
- Placeholders like `{skill-name}`, `{primary}`, `{user_name}` are substituted with their resolved values before any output is emitted to the user or written to disk.

## Language Rules

- Communicate with the user in `{communication_language}`.
- Templates loaded from `{workflow.er_diagram_template}` and `assets/decision-log-template.md` are English-source i18n skeletons. When rendering an output document or decision log, translate all prose (section headings, table headers and contents, comments, revision-history entries) to `{document_output_language}`. Never emit the template verbatim.
- File names and folder names are always English (kebab-case or snake_case). Never embed `{document_output_language}` characters in any file path.
- Carve-outs that stay in their original form in both template and output: Mermaid keywords (`erDiagram`, `PK`, `FK`, `UK`, `||--o{`, `}o--||`, etc.), SQL type names (`INTEGER`, `VARCHAR`, `TIMESTAMP`, `TEXT`, `BOOLEAN`), and constraint labels (`NOT NULL`, `AUTO_INCREMENT`, `UNIQUE`).

## On Activation

Resolve the `{workflow.*}` block: run `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`. If missing, hand-merge `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml` (scalars override, arrays append, arrays-of-tables keyed by `code`/`id` replace matching entries). Keep the resolved block in memory for the entire session.

Execute `{workflow.activation_steps_prepend}` in order. Load `{workflow.persistent_facts}` (entries prefixed `file:` are paths/globs; others are verbatim facts).

Load config from `{project-root}/_bmad/config.yaml` and `config.user.yaml` (root + `core` + `modules.bmm`). Fall back to `.toml` variants, then legacy `{project-root}/_bmad/bmm/config.yaml`. Resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, `{planning_artifacts}`, `{project_knowledge}`, `{project_name}`.

Greet `{user_name}` in `{communication_language}` with a one-sentence orientation: D-19 produces a database design document with Mermaid ER diagrams across five stages (prerequisites → discovery → generation → validation → handoff). D-19 opens Phase 2, so it expects the Phase 1 gate (`hbc-phase-gate` evaluate 1) to have passed. Execute `{workflow.activation_steps_append}` in order.

## Headless Mode

`-H` / `--headless` runs without user prompts. The full contract — flags, defaults, JSON return shape, and the closed-set of blocker `reason` values — lives in [`references/headless-contract.md`](references/headless-contract.md). Reason values: `template_missing`, `no_prd_and_no_interactive_in_headless`, `planning_artifacts_unreadable`, `mermaid_validation_failed`, `entity_coverage_gap`, `no_entities_found`, `resolver_missing`. Extend both this list and the contract file together.

## Workflow

### 1. Prerequisites and Scope

#### 1a. Bind workspace and detect resume state

Bind `{primary} = {workflow.er_diagram_output_path}` — a single output FILE written directly into `{planning_artifacts}` (no per-document folder). The session decision log lives at `{planning_artifacts}/.decision-log.md` and scan artifacts at `{planning_artifacts}/.scan/` — both shared peers alongside the other D-* documents. Create `{planning_artifacts}` and `{planning_artifacts}/.scan/` if absent.

Run the discover script, pointing `--primary` at the output file so it can read resume state from the document and its peer decision log in one JSON:

```
python3 {skill-root}/scripts/discover-planning-artifacts.py {planning_artifacts} --template-path {workflow.er_diagram_template} --primary {primary} -o {planning_artifacts}/.scan/artifacts.json
```

Consume the JSON. If the script exits with a non-zero code or produces no output, proceed as if `artifacts_dir_exists: false` and `resume_state.recommended_intent: "Fresh"` — log the error and exit code to `.decision-log.md`. If `fatal: "template_missing"` → HALT (interactive) or return `blocked` with `reason: "template_missing"` (headless). Otherwise read `resume_state.recommended_intent` and `resume_state.fresh_reason`:

- `Fresh` with `fresh_reason: "no_primary"` — no primary document at all. Initialize from template.
- `Fresh` with `fresh_reason: "crashed_no_progress"` — primary exists but `stepsCompleted` is empty (prior run crashed before stage-1 write). Surface the crash explicitly in the menu and decision log so the audit trail does not lose the signal. Headless: log `fresh_reason` to `.decision-log.md`.
- `Fresh` with `fresh_reason: "stale_artifact"` — primary has inconsistent step state (e.g. stage-2 completed but stage-1 missing). Surface the inconsistency explicitly and offer to reset or continue from the last consistent stage.
- `Resume` — primary has at least `stage-1` in `stepsCompleted` and not yet `stage-5`. Show the user the prior session summary (`resume_state.last_session_summary`) and offer to continue from `primary_last_step`.
- `Update` — primary completed (`stage-5` in `stepsCompleted`). Treat as revisable artifact: read latest revision-history version. Stage 3 will gate the version bump on scope-of-change.

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

If `.decision-log.md` is absent at the start of the session, initialize it from `{workflow.decision_log_template}` — interpolate placeholders (`{skill-name}`, `{project_name}`, `{user_name}`, date) the same way Stage 1e interpolates the primary template.

#### 1b. Open-floor invitation, intent gate, and wrong-skill off-ramp (interactive only)

Before consuming the source inventory from 1a, invite the user to share anything not yet captured — existing database schemas, SQL DDL files, prior ER diagrams, data dictionaries, ORM model files. Adapt the invitation to context.

Then one intent check: capturing an existing database schema, designing a new one, or both.

**Wrong-skill off-ramp** (must fire before any heavier work): if the user's reply signals a different artifact, redirect. Trigger terms — D-20 or "column-level DDL" / "all constraints" / "every column spec" → D-20 table definitions; D-17 or "sequence diagram" / "API flow" / "call flow" → D-17; D-18 or "class diagram" / "class hierarchy" / "service structure" → D-18. D-19 focuses on the high-level ER diagram and entity overview, not per-column DDL.

**Short-circuit Stage 1e** — strict gate. Only skip 1e when the open-floor reply *explicitly* covers **all three** of: scope (which domain areas), sources (which docs to include or exclude), and normalization level (conceptual vs logical vs physical). A partial reply falls through to 1e for confirmation. Log which dimensions were inferred from 1b vs confirmed in 1e to `.decision-log.md`.

In headless mode 1b is skipped entirely.

#### 1b′. Brainstorming suggestion (interactive only, Fresh state only)

If the user is designing a new database (not capturing existing schema) and the domain model is complex or ambiguous, suggest: _"Domain model phức tạp — muốn chạy `bmad-brainstorming` trước để explore entity relationships và normalization trade-offs không? Output sẽ feed vào D-19."_ If declined, proceed. If accepted, pause for separate brainstorming session. If a brainstorming session file exists in `{output_folder}/brainstorming/`, load it as supplementary context for entity discovery. Skip for schema-capture intent or Update/Resume states.

#### 1c. Consume source inventory

Consume `artifacts.json` from Stage 1a into:
- PRD set (whole-doc or shard set — the discover script enumerates every shard automatically; do not re-glob)
- Architecture docs
- UX, use-case, research candidates
- Existing D-20 table definitions (if any)

If `artifacts_dir_exists` is false → note it and proceed to the no-PRD HALT-menu below.

#### 1d. No-PRD HALT menu

If `artifacts.json` returned zero PRDs AND `--prd-path` was not provided:

```
No PRD found in {planning_artifacts}
Options:
[1] Run `bmad-create-prd` first (recommended)
[2] Provide PRD path
[3] Continue with interactive elicitation (greenfield, no source)
[q] Quit
```

**Headless resolution:** if `--no-prd-ok` is set, take option 3 silently and log it. Otherwise return `blocked` with `reason: "no_prd_and_no_interactive_in_headless"`.

#### 1e. Inferred-defaults confirmation (interactive only, unless short-circuited by 1b)

```
Detected: {prd_count} PRD doc(s), {arch_count} Architecture doc(s), {d20_count} D-20 doc(s)
Inferred: scope={single-domain|multi-domain}, level={conceptual|logical|physical}

[C] Confirm and proceed
Or specify overrides: scope=… / level=… / sources=include:…,exclude:… (e.g. sources=include:planning/prd-orders.md,exclude:*research*)
```

Initialize the primary document from `{workflow.er_diagram_template}`, translating template prose to `{document_output_language}` per the Language Rules. Append a new session block to `.decision-log.md`. Mark `stepsCompleted` to include `stage-1`. Set primary frontmatter `updated` to today.

### 2. Discovery

Run the entity-candidate pre-pass on the chosen sources:

```
python3 {skill-root}/scripts/extract-entity-candidates.py <source-paths...> -o {planning_artifacts}/.scan/entity-candidates.json
```

Use the candidate JSON as a starting point — confirm, merge, and fill gaps rather than free-reading raw sources. If the script returns `"warn": "entity_extraction_empty"`, note that mechanical extraction found nothing and proceed with full LLM extraction from sources.

From the candidates and source documents, extract:
- **Entities** — domain objects, data models, aggregates (in `{document_output_language}` for logical names, English for physical names)
- **Attributes** — key fields per entity with types (PK, FK, data type)
- **Relationships** — cardinality between entities (one-to-one, one-to-many, many-to-many)
- **Constraints** — unique keys, NOT NULL, business rules that affect schema
- **Indexes** — performance-critical access patterns identified from use cases

Present extracted entities and relationships for confirmation. For multi-domain scope, group entities by bounded context / domain area.

**Zero-entity branch** — if the source contains no identifiable data entities (e.g. pure API gateway or static content project), do not render a vacuous diagram. Inform the user that D-19 may not be applicable and suggest alternative documentation. Interactive: confirm with the user. Headless: log and return `blocked` with `reason: "no_entities_found"`.

**Compaction-flush at the end of this stage** (required, not optional). Before moving on:
- Write entity list as `stage_2_entities: ["EntityA", "EntityB", ...]` and relationship list as `stage_2_relationships: ["EntityA->EntityB:one-to-many", ...]` to the primary document's frontmatter.
- Append a `### Discovery snapshot (Stage 2 flush)` block to `.decision-log.md` carrying entities, relationships, and attribute summaries verbatim.
- Update primary frontmatter `stepsCompleted` to include `stage-2` and `updated` to today.

If compaction drops the conversation mid-stage, the next run resumes from these artifacts rather than re-eliciting.

### 3. Diagram Generation

For each domain area (or single diagram for single-domain scope), render one Mermaid `erDiagram` block:
- Declare every entity with its key attributes (PK, FK, important columns).
- Use Mermaid ER relationship notation: `||--o{` (one-to-many), `||--||` (one-to-one), `}o--o{` (many-to-many), with relationship labels.
- Physical names for entity and attribute identifiers; logical names as comments or in the table definitions section.
- Group related entities visually where possible.
- For large schemas (>15 entities), split into sub-domain diagrams as H2-separated sections within the single primary file, plus a master overview diagram showing only entity names and relationships (no attributes). Keep everything in one file so Stage 4 validation covers all sections.

**Table definitions section** — below each ER diagram block, generate a table definition summary per entity:
- Logical name, physical name, description
- Key columns with types and constraints
- Foreign key references

**Index definitions section** — if indexes were identified in Stage 2, generate the index table.

**Revision history table — scope-of-change gate:**

- **Create / Fresh**: today's date, version `1.0`, "Initial version" → `{user_name}`, translated to `{document_output_language}`.
- **Update** — determine scope-of-change:
  - **Auto-detect default:** compare current `stage_2_entities` and `stage_2_relationships` against the prior session's flush block in `.decision-log.md`. If both arrays are identical → **polish**. If either differs → **semantic** (bump minor).
  - **Manual override** (interactive): ask "polish (typo / wording / layout) or semantic (entities / relationships / attributes)?".
  - **Headless override:** `--scope-of-change=polish|semantic|auto` (default `auto`).
  - Log the chosen scope and rationale to `.decision-log.md`.

Update primary frontmatter `stepsCompleted` to include `stage-3` and `updated` to today.

Then present the **Parallel-lens menu**. Headless: taken from `--review-lenses=skip|advanced|party` (default `skip`); every fire appended to `review_lenses_run`. If the invoked lens skill is not installed, perform the review inline using the same analytical framing and log the fallback to `.decision-log.md`.

```
[A] Advanced Elicitation — single deep lens via bmad-advanced-elicitation (~5 min).
[P] Party Mode — three parallel lenses (analyst + architect + DBA) via bmad-party-mode (~15 min).
[C] Continue — proceed without an additional review pass.
```

Stage-3 lens-targets: stress-test entity completeness, relationship cardinality correctness, and normalization level appropriateness.

### 4. Validation

Run the two deterministic validators (both may run concurrently — they are independent):

```
python3 {skill-root}/scripts/validate-mermaid-er.py {primary} --expected-entities "<comma-separated stage-2 entities>" -o {planning_artifacts}/.scan/mermaid-er.json

python3 {skill-root}/scripts/check-entity-coverage.py --prd <each-prd-path-or-shard> --d19 {primary} -o {planning_artifacts}/.scan/entity-coverage.json
```

Pass each PRD path (or each shard from `artifacts.json` for sharded PRDs) as a separate `--prd` argument. If the result contains `"warn": "prd_entity_extraction_empty"`, surface it: "PRD entity extraction found zero entities — coverage check may be incomplete; manual review recommended."

Judgment checks (LLM, not script):
- **Normalization** — entities are appropriately normalized for the chosen level (no unnecessary redundancy at logical level; acceptable denormalization at physical level with justification).
- **Relationship completeness** — every FK has a corresponding relationship line; no orphan entities.
- **Naming consistency** — physical names follow a consistent convention (snake_case preferred).
- **Revision history** — populated with version, date, author, change description.
- **Language consistency** — output prose in `{document_output_language}`, carve-outs preserved.

Present consolidated findings (script issues + LLM findings). Fix issues:
- **Interactive:** collaborative fix loop.
- **Headless:** apply only validator issues marked `auto_fixable: true` in `mermaid-er.json`. Log every auto-fix to `.decision-log.md` citing the validator's `fix_hint`. For non-auto-fixable issues, return `blocked` with `reason: "mermaid_validation_failed"` or `reason: "entity_coverage_gap"`.

Update primary frontmatter `stepsCompleted` to include `stage-4` and `updated` to today.

Then present the **Parallel-lens menu** (same as Stage 3). Stage-4 lens-targets: challenge edge cases (nullable FKs, soft deletes, polymorphic associations, temporal data) and check the artifact reads cleanly to a fresh reviewer.

### 4b. Semantic Review (Lớp 2)

Script validation only proves cấu trúc. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`). Apply the **facet-split discipline** per entity (read vs write/admin surface · entity lifecycle — `create` / `update` / `suspend` / `revoke` / `rotate` where the entity has one · relationship cardinality): an entity with a real lifecycle (account, key, subscription) whose state transitions have no representation (no status column, no state machine), or an admin-managed entity with no downstream owner, has an open facet — name it so downstream `hbc-create-api-spec` (D-21) and the test skills (D-26/D-27) know it must be designed and tested, rather than letting the cut-out facet vanish silently (the seam). Record `semanticReview` frontmatter (A-3: `status` is `passed` only when `openFacets` is empty, else `pending` + the list). The Phase 2 gate REVIEW item reads it.

**Headless:** run the same rubric and write the frontmatter; if `openFacets` is non-empty, leave `status: pending`, log the open facets to `.decision-log.md`, and proceed (this layer does not block — the Phase 2 gate enforces it). Never fabricate coverage to force `passed`.

### 5. Save and Handoff

Finalize `{primary}`. Set `stepsCompleted` to the full list (`stage-1..5`), `lastStep` to `complete`, `updated` to today, and the `semanticReview` block from Stage 4b. Append a closing session block to `.decision-log.md` summarising:
- Sources used, scope, normalization level
- Scope-of-change classification (Update mode only)
- Auto-fixes applied (headless)
- Lenses run (`review_lenses_run`)
- Handoff target — which downstream skill should consume this output

Downstream consumers: `hbc-create-coding-standards`, `hbc-create-api-spec`, `hbc-task-breakdown`.

Check `{workflow.on_complete_distillate}`: if `"always"`, invoke `bmad-distillator` against the primary (headless and interactive). If `"offer"` (default), offer interactively; headless skips. If `"never"`, skip entirely. Skip with a note if distillator is unavailable; never inline a substitute.

**Headless mode:** emit the JSON return contract per [`references/headless-contract.md`](references/headless-contract.md), substituting every placeholder with its resolved value before emission.

## On Complete

Read `{workflow.on_complete}` from the already-resolved workflow block (Step 1 of On Activation kept it in memory). If non-empty, follow it as the final instruction. Otherwise, invoke `bmad-help`.

## Sync Handoff (hbc-sync integration)

Applies only in `update` mode. Full contract: `hbc-sync/references/skill-integration.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest: _"Tài liệu đã cập nhật. Chạy `hbc-sync` để đồng bộ các tài liệu/test/code phụ thuộc?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-sync` directly (it will cascade downstream). Default is false.
