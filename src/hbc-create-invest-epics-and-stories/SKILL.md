---
name: hbc-create-invest-epics-and-stories
description: "INVEST + 3C's variant of Create Epics and Stories. Use when the user says 'create invest epics' or 'create invest stories'."
---

# Create INVEST Epics and Stories

This skill produces pure INVEST + 3C's user stories from PRD, Architecture, and UX Design documents. Act as a product strategist who enforces INVEST compliance — every story is Independent, Negotiable, Valuable, Estimable, Small (1-2 days), and Testable. Output goes to `invest-stories.md` for side-by-side comparison with the implementation-oriented `epics.md`.

**Key constraints vs standard epic/story generation:**
- AC describes observable user behavior only — no code, syntax, or file paths
- Stories sized 1-2 days max, estimated in Fibonacci points (1, 2, 3, 5, 8)
- Enabler/foundation work is DoD or Technical Tasks, not user stories
- "As a System" stories are reframed user-centric or moved to Technical Tasks
- Dependencies minimized for parallel implementation
- AC references Architecture.md for HOW — no inline implementation detail

Supports `--headless` / `-H` for non-interactive generation.

## Conventions

- Bare paths (e.g. `references/story-generation.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails, resolve the `workflow` block yourself by reading these three files in base -> team -> user order and applying structural merge rules: `{skill-root}/customize.toml`, `{project-root}/_bmad/custom/{skill-name}.toml`, `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays of tables keyed by `code`/`id` replace matching entries and append new ones, all other arrays append.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order before proceeding.

### Step 3: Load Persistent Facts

Treat every entry in `{workflow.persistent_facts}` as foundational context for the whole run. Entries prefixed `file:` are paths or globs — load the referenced contents as facts. All other entries are facts verbatim.

### Step 4: Load Config

Load available config from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (root level, `hbc` section, and `bmm` section for shared variables). Fall back to `{project-root}/_bmad/bmm/config.yaml`. Resolve `{user_name}`, `{communication_language}`, `{document_output_language}`, `{planning_artifacts}`, `{project_knowledge}`.

### Step 5: Greet and Execute Append Steps

Greet `{user_name}` in `{communication_language}`. Execute each entry in `{workflow.activation_steps_append}` in order.

**Language rules for the entire workflow:**
- Communicate with the user in `{communication_language}`
- Write all output document content (epics, stories, AC, technical tasks) in `{document_output_language}`
- Template structural markers (Given/When/Then, As a/I want/So that) stay in English

## Workflow

### Stage 1: Prerequisites and Requirements Extraction

Validate that required input documents exist in `{planning_artifacts}`:
- **PRD** (required) — `*prd*.md` or `*prd*/index.md`
- **Architecture** (required) — `*architecture*.md` or `*architecture*/index.md`
- **UX Design** (optional) — `*ux*.md` or `*ux*/index.md`

Ask the user if additional documents should be included or any found documents excluded. Once confirmed, read all input documents and extract:
- **FRs** — functional requirements (numbered, testable)
- **NFRs** — non-functional requirements
- **Additional requirements** — from Architecture (infrastructure, integration, security)
- **UX Design Requirements** — from UX spec if present (each specific enough for story creation)

Initialize `{planning_artifacts}/invest-stories.md` from `{workflow.stories_template}`. Populate the requirements sections. Present extracted requirements for user review and confirmation.

### Stage 2: Epic Design

Design epics organized around **user value**, not technical layers. Each epic delivers complete, standalone functionality. Apply these principles:
- Group related FRs by user outcome
- Each epic is independently valuable
- Consider file overlap — consolidate epics that repeatedly modify the same core files
- Create an FR Coverage Map ensuring every FR maps to an epic

Present the epic structure for collaborative refinement and get explicit approval before proceeding.

### Stage 3: INVEST Story Generation

Read fully and follow: `references/story-generation.md`

### Stage 4: Final Validation

Validate the complete document:

1. **FR Coverage** — every FR appears in at least one story with testable AC
2. **INVEST Compliance** — each story passes all six INVEST criteria
3. **3C's Check** — each story has Card (user story format), Conversation (context notes), Confirmation (observable AC)
4. **No implementation leakage** — AC contains zero code, syntax, file paths, or class names
5. **Size check** — no story exceeds 5 points (8 = must split)
6. **Dependency check** — stories within an epic have no forward dependencies; cross-epic dependencies are minimized
7. **Technical Tasks** — enabler work properly separated from user stories
8. **Architecture references** — AC points to Architecture.md sections for implementation HOW

Present validation results. Fix any issues collaboratively. Save final document.

## On Complete

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow.on_complete`

If resolved `{workflow.on_complete}` is non-empty, follow it as the final instruction. Otherwise, invoke `bmad-help`.
