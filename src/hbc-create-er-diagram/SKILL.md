---
name: hbc-create-er-diagram
description: "Generate D-19 Database Design Document with ER Diagram in Mermaid from PRD, Architecture, or interactive input. Use when user says 'create ER diagram', 'create D-19', 'tạo sơ đồ ER', 'vẽ sơ đồ ER', or 'vẽ D-19'."
---

# Create ER Diagram (D-19)

## Overview

Produces a D-19 Database Design Document (データベース設計書) following HBLab document conventions — Mermaid `erDiagram` with entity definitions, relationships, and attribute specifications. Reads PRD / Architecture / UX artifacts from `{planning_artifacts}` when available, falls back to interactive elicitation when none exist. Output is a workspace folder under `{planning_artifacts}` containing the primary document plus a session decision log that carries identity across runs.

Supports `-H` / `--headless` for non-interactive generation. Stage 1 honours an input contract so automators can drive it deterministically — see [`references/headless-contract.md`](references/headless-contract.md) for the full flag set, defaults table, and JSON return contract. Stage 5 enumerates the canonical downstream consumers.

## Conventions

- Bare paths (e.g. `references/foo.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
- Placeholders like `{skill-name}`, `{doc_workspace}`, `{user_name}` are substituted with their resolved values before any output is emitted to the user or written to disk.

## Language Rules

- Communicate with the user in `{communication_language}`.
- Templates loaded from `{workflow.er_diagram_template}` and `assets/decision-log-template.md` are English-source i18n skeletons. When rendering an output document or decision log, translate all prose (section headings, table headers and contents, comments, revision-history entries) to `{document_output_language}`. Never emit the template verbatim.
- File names and folder names are always English (kebab-case or snake_case). Never embed `{document_output_language}` characters in any file path.
- Carve-outs that stay in their original form in both template and output: Mermaid keywords (`erDiagram`, `PK`, `FK`, `UK`, `||--o{`, `}o--||`, etc.), SQL type names (`INTEGER`, `VARCHAR`, `TIMESTAMP`, `TEXT`, `BOOLEAN`), and constraint labels (`NOT NULL`, `AUTO_INCREMENT`, `UNIQUE`).

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails or is missing, resolve the `workflow` block yourself by reading these three files in base → team → user order and applying structural merge rules: `{skill-root}/customize.toml`, `{project-root}/_bmad/custom/{skill-name}.toml`, `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays of tables keyed by `code`/`id` replace matching entries and append new ones, all other arrays append.

The resolved `{workflow.*}` block stays in memory for the rest of the session, including `{workflow.on_complete}`; do not re-resolve in `## On Complete`.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order before proceeding.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context for the whole run. Entries prefixed `file:` are paths or globs — load the referenced contents as facts. All other entries are facts verbatim.

### Step 4: Load Config

Load available config from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (root, `core` section, and `modules.bmm` section). Fall back to `{project-root}/_bmad/config.toml` and `{project-root}/_bmad/config.user.toml`, then to legacy `{project-root}/_bmad/bmm/config.yaml`. Resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, `{planning_artifacts}`, `{project_knowledge}`, `{project_name}`.

### Step 5: Greet and Execute Append Steps

Greet `{user_name}` in `{communication_language}`. Execute each entry in `{workflow.activation_steps_append}` in order.

## Headless Mode

`-H` / `--headless` runs without user prompts. The full contract lives in [`references/headless-contract.md`](references/headless-contract.md). The closed-set of blocker `reason` values returned via the JSON contract:

- `template_missing` — `{workflow.er_diagram_template}` not found on disk.
- `no_prd_and_no_interactive_in_headless` — no PRD found, no `--prd-path`, no `--no-prd-ok`.
- `planning_artifacts_unreadable` — `{planning_artifacts}` directory missing or unreadable.
- `mermaid_validation_failed` — `validate-mermaid-er.py` returned issues not all `auto_fixable: true`.
- `entity_coverage_gap` — `check-entity-coverage.py` reported uncovered or phantom entities.
- `resolver_missing` — customization resolver failed and the hand-merge fallback could not complete.

Add new reasons only by extending this list and the contract file together.

## Parallel-lens menu

Used at the end of Stage 3 and Stage 4. In headless mode the choice is taken from `--review-lenses=skip|advanced|party` (default `skip`); every fire is appended to `review_lenses_run` in the JSON return contract.

```
[A] Advanced Elicitation — single deep lens via bmad-advanced-elicitation.
    Cost: ~5 minutes. Current draft preserved on cancel.
[P] Party Mode — three parallel lenses (analyst + architect + DBA) via bmad-party-mode.
    Cost: ~15 minutes. Heavier; use when the artifact will drive multiple downstream skills.
[C] Continue — proceed without an additional review pass.
```

`[A]` and `[P]` are structurally different patterns; the labels make the cost and shape explicit so the user (or automator) chooses with eyes open.

## Workflow

### 1. Prerequisites and Scope

#### 1a. Bind workspace and detect resume state

Bind `{doc_workspace} = {workflow.er_diagram_output_path}` (resolves to a single path). Create the workspace if absent.

Run the discover script with the workspace flag to get both source inventory and resume state in one JSON:

```
python3 {skill-root}/scripts/discover-planning-artifacts.py {planning_artifacts} --template-path {workflow.er_diagram_template} --workspace {doc_workspace} -o {doc_workspace}/.scan/artifacts.json
```

Consume the JSON. If `fatal: "template_missing"` → HALT (interactive) or return `blocked` with `reason: "template_missing"` (headless). Otherwise read `resume_state.recommended_intent` and `resume_state.fresh_reason`:

- `Fresh` with `fresh_reason: "no_workspace"` — no primary at all. Initialize from template.
- `Fresh` with `fresh_reason: "crashed_no_progress"` — primary exists but `stepsCompleted` is empty (prior run crashed before stage-1 write). Surface the crash explicitly in the menu and decision log so the audit trail does not lose the signal. Headless: log `fresh_reason` to `.decision-log.md`.
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

If `.decision-log.md` is absent at the start of the session, initialize it from `assets/decision-log-template.md` — interpolate placeholders (`{skill-name}`, `{project_name}`, `{user_name}`, date) the same way Stage 1e interpolates the primary template.

#### 1b. Open-floor invitation, intent gate, and wrong-skill off-ramp (interactive only)

Before consuming the source inventory from 1a, invite the user to share anything not yet captured — existing database schemas, SQL DDL files, prior ER diagrams, data dictionaries, ORM model files. Adapt the invitation to context.

Then one intent check: capturing an existing database schema, designing a new one, or both.

**Wrong-skill off-ramp** (must fire before any heavier work): if the user's reply makes it clear they want detailed table definitions with column-level specs (D-20), sequence diagrams (D-17), or class diagrams (D-18), say so and point at the right skill. D-19 focuses on the high-level ER diagram and entity overview, not per-column DDL.

**Short-circuit Stage 1e** — strict gate. Only skip 1e when the open-floor reply *explicitly* covers **all three** of: scope (which domain areas), sources (which docs to include or exclude), and normalization level (conceptual vs logical vs physical). A partial reply falls through to 1e for confirmation. Log which dimensions were inferred from 1b vs confirmed in 1e to `.decision-log.md`.

In headless mode 1b is skipped entirely.

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
Or specify overrides: scope=… / level=…  / sources=include:…,exclude:…
```

Initialize the primary document from `{workflow.er_diagram_template}`, translating template prose to `{document_output_language}` per the Language Rules. Append a new session block to `.decision-log.md`. Mark `stepsCompleted` to include `stage-1`. Set primary frontmatter `updated` to today.

### 2. Discovery

From the chosen sources or interactive elicitation, extract:
- **Entities** — domain objects, data models, aggregates (in `{document_output_language}` for logical names, English for physical names)
- **Attributes** — key fields per entity with types (PK, FK, data type)
- **Relationships** — cardinality between entities (one-to-one, one-to-many, many-to-many)
- **Constraints** — unique keys, NOT NULL, business rules that affect schema
- **Indexes** — performance-critical access patterns identified from use cases

Present extracted entities and relationships for confirmation. For multi-domain scope, group entities by bounded context / domain area.

**Zero-entity branch** — if the source contains no identifiable data entities (e.g. pure API gateway or static content project), do not render a vacuous diagram. Inform the user that D-19 may not be applicable and suggest alternative documentation. Interactive: confirm with the user. Headless: log and return `blocked` with `reason: "no_entities_found"`.

**Compaction-flush at the end of this stage** (required, not optional). Before moving on:
- Write entity list and relationship inventory to the primary document's frontmatter (`stage_2_entities`, `stage_2_relationships`).
- Append a `### Discovery snapshot (Stage 2 flush)` block to `.decision-log.md` carrying entities, relationships, and attribute summaries verbatim.
- Update primary frontmatter `stepsCompleted` to include `stage-2` and `updated` to today.

If compaction drops the conversation mid-stage, the next run resumes from these artifacts rather than re-eliciting.

### 3. Diagram Generation

For each domain area (or single diagram for single-domain scope), render one Mermaid `erDiagram` block:
- Declare every entity with its key attributes (PK, FK, important columns).
- Use Mermaid ER relationship notation: `||--o{` (one-to-many), `||--||` (one-to-one), `}o--o{` (many-to-many), with relationship labels.
- Physical names for entity and attribute identifiers; logical names as comments or in the table definitions section.
- Group related entities visually where possible.
- For large schemas (>15 entities), split into sub-domain diagrams with a master overview diagram showing only entity names and relationships (no attributes).

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

Then present the **Parallel-lens menu** (defined above). Stage-3 lens-targets: stress-test entity completeness, relationship cardinality correctness, and normalization level appropriateness.

### 4. Validation

Run the two deterministic validators:

```
python3 {skill-root}/scripts/validate-mermaid-er.py {doc_workspace}/D-19-er-diagram.md --expected-entities "<comma-separated stage-2 entities>" -o {doc_workspace}/.scan/mermaid-er.json

python3 {skill-root}/scripts/check-entity-coverage.py --prd <each-prd-path-or-shard> --d19 {doc_workspace}/D-19-er-diagram.md -o {doc_workspace}/.scan/entity-coverage.json
```

Pass each PRD path (or each shard from `artifacts.json` for sharded PRDs) as a separate `--prd` argument. If the PRD has no entity identifiers, `uncovered` and `phantom` will both be empty.

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

Then present the **Parallel-lens menu** (defined above). Stage-4 lens-targets: challenge edge cases (nullable FKs, soft deletes, polymorphic associations, temporal data) and check the artifact reads cleanly to a fresh reviewer.

### 5. Save and Handoff

Finalize `{doc_workspace}/D-19-er-diagram.md`. Set `stepsCompleted` to the full list (`stage-1..5`), `lastStep` to `complete`, and `updated` to today. Append a closing session block to `.decision-log.md` summarising:
- Sources used, scope, normalization level
- Scope-of-change classification (Update mode only)
- Auto-fixes applied (headless)
- Lenses run (`review_lenses_run`)
- Handoff target — which downstream skill should consume this output

Downstream consumers: `bmad-create-epics-and-stories`, `hbc-create-invest-epics-and-stories`.

If the ER diagram will feed downstream LLM consumers, offer to invoke `bmad-distillator` against the primary to produce a token-efficient distillate. Skip with a note if distillator is unavailable; never inline a substitute.

**Headless mode:** emit the JSON return contract per [`references/headless-contract.md`](references/headless-contract.md), substituting every placeholder with its resolved value before emission.

## On Complete

Read `{workflow.on_complete}` from the already-resolved workflow block (Step 1 of On Activation kept it in memory). If non-empty, follow it as the final instruction. Otherwise, invoke `bmad-help`.
