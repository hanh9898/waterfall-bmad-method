# Stage Guide — Business Flow Diagram (D-06)

Communicate with the user in `{communication_language}`.

Authoritative per-stage detail for `hbc-create-business-flow-diagram`. `SKILL.md` carries the lean control flow and cites this file; the closed-set blocker `reason` values and flag table live in [`headless-contract.md`](headless-contract.md).

## Conventions (path & placeholder resolution)

- Bare paths (e.g. `references/foo.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
- Placeholders like `{skill-name}`, `{primary}`, `{user_name}` are substituted with their resolved values before any output is emitted to the user or written to disk.

## Language Rules

- Communicate with the user in `{communication_language}`.
- Templates loaded from `{workflow.business_flow_template}` and `{workflow.decision_log_template}` are English-source i18n skeletons. Translate all output prose to `{document_output_language}`. Never emit the template verbatim.
- File names and folder names are always English (kebab-case or snake_case).
- Carve-outs (keep in original form): Mermaid keywords (`sequenceDiagram`, `flowchart`, `participant`, `actor`, `->>`, `-->>`, etc.), Mermaid code identifiers (`User`, `System`, `NewSystem`), and `AS-IS` / `TO-BE`.

## On Activation (detail)

> **Resolve active feature (B):** arg `feature=<slug>` → active feature in the session → ask (headless: required, missing → blocked `feature_required`). Substitute `{feature}` in every workflow path (D-06 is written per-feature).

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

## Parallel-lens menu

Used at the end of Stage 3 and Stage 4. In headless mode the choice is taken from `--review-lenses=skip|advanced|party` (default `skip`); every fire is appended to `review_lenses_run` in the JSON return contract.

```
[A] Advanced Elicitation — bmad-advanced-elicitation
[P] Party Mode — bmad-party-mode (analyst + architect + UX)
[C] Continue
```

Headless mapping: `--review-lenses=skip` → `[C]`, `advanced` → `[A]`, `party` → `[P]`.

## Stage 1 — Prerequisites and Scope

### 1a. Bind workspace and detect resume state

Bind `{primary} = {workflow.business_flow_output_path}` — a single output FILE. D-06 is **per-feature**: `{primary}` resolves under the active feature's own dir (`{output_folder}/features/{feature}/planning-artifacts/`), NOT the flat project-level `{planning_artifacts}`. Resolve `{feature}` first (arg `feature=<slug>` → active feature in session → ask; headless: required, missing → blocked `feature_required`). Let `{ws}` = the directory of `{primary}` (the feature's planning-artifacts dir). The session decision log lives at `{ws}/.decision-log.md` and scan artifacts at `{ws}/.scan/` — both peers of `{primary}`. Create `{ws}` and `{ws}/.scan/` if absent. Throughout this workflow, decision-log / `.scan` references resolve against `{ws}`; PRD / source **discovery** still scans the project-level `{planning_artifacts}`.

Run the discover script, pointing `--primary` at the output file so it can read resume state from the document and its peer decision log in one JSON:

```
python3 {skill-root}/scripts/discover-planning-artifacts.py {planning_artifacts} --template-path {workflow.business_flow_template} --primary {primary} --check-as-is -o {ws}/.scan/artifacts.json
```

If the discover script fails to execute (Python missing, crash), fall back to globbing `{planning_artifacts}` yourself and constructing a minimal inventory; note the fallback in `{ws}/.decision-log.md`.

Consume the JSON. If `fatal: "template_missing"` → HALT (interactive) or return `blocked` with `reason: "template_missing"` (headless). Otherwise read `resume_state.recommended_intent` and `resume_state.fresh_reason`:

- `Fresh` with `fresh_reason: "no_primary"` — no primary document at all. Initialize from template.
- `Fresh` with `fresh_reason: "crashed_no_progress"` — primary exists but `stepsCompleted` is empty (prior run crashed before stage-1 write). Surface the crash explicitly in the menu and decision log so the audit trail does not lose the signal. Headless: log `fresh_reason` to `.decision-log.md`.
- `Resume` — primary has at least `stage-1` in `stepsCompleted` and not yet `stage-5`. Show the user the prior session summary (`resume_state.last_session_summary`) and offer to continue from `primary_last_step`.
- `Update` — primary completed (`stage-5` in `stepsCompleted`). Treat as revisable artifact: read latest revision-history version. Stage 3 will gate the version bump on scope-of-change.

Present this menu (interactive only). When `recommended_intent` is `Fresh` and `fresh_reason` is `no_primary`, show only `[N] Start fresh` and `[X] Exit`. Otherwise show the full menu:

```
Recommended: {recommended_intent}{ if fresh_reason: " ({fresh_reason})" }
Last session: {resume_state.last_session_summary}
Steps complete: {resume_state.primary_steps_completed}

[R] Resume — pick up where the previous session stopped
[U] Update — revise this flow as a new revision-history row
   [U1] Update all flows
   [U2] Update a single named flow (specify name)
[V] Validate-only — re-run Stage 4 against the current output
[N] Start fresh — archive the current primary and begin again
[X] Exit
```

**Headless resolution:** take `resume_state.recommended_intent`; log the auto-choice (plus `fresh_reason` if applicable) to `.decision-log.md`. For targeted single-flow update, the automator uses `--update-flow=<name>` (see headless contract).

If `.decision-log.md` is absent at the start of the session, initialize it from `{workflow.decision_log_template}` — interpolate placeholders (`{skill-name}`, `{project_name}`, `{user_name}`, date) the same way Stage 1e interpolates the primary template.

### 1b. Open-floor invitation, intent gate, and wrong-skill off-ramp (interactive only)

Before consuming the source inventory from 1a, invite the user to share anything not yet captured — references, sketches, prior flows, side notes, paths the discovery scan won't have found (Miro exports, hand-drawn photos, ticket links). Adapt the invitation to context. A soft "anything else?" surfaces what they almost forgot.

Then one intent check: capturing an existing flow, designing a new one, or both. The answer feeds the mode default.

**Wrong-skill off-ramp** (must fire before any heavier work): the description trigger `'tạo sơ đồ'` / `'vẽ sơ đồ'` can match class-diagram, sequence-diagram-for-a-single-feature, or system-architecture intent. If the user's reply makes that clear, say so and point at the right skill (`bmad-create-architecture` for system architecture; class/sequence diagrams within a single feature usually belong inside a Story or PRD context, not D-06).

**Short-circuit Stage 1e** — strict gate. Only skip 1e when the open-floor reply *explicitly* covers **all four** of: mode, scope, sources (which docs to include or exclude), and diagram type. A partial reply (any of the four absent or ambiguous) falls through to 1e for confirmation. Log which dimensions were inferred from 1b vs confirmed in 1e to `.decision-log.md`.

In headless mode 1b is skipped entirely.

### 1b′. Brainstorming suggestion (interactive only, Fresh state only)

If the user is designing TO-BE flows and the domain is complex or requirements are sparse, suggest (emit the message in `{communication_language}`): _"Designing a TO-BE flow benefits from creative exploration — want to run `bmad-brainstorming` first to explore alternative flows and improvement ideas? Its output will feed into D-06."_ If declined, proceed. If accepted, pause — user runs brainstorming separately, then resumes here. If a brainstorming session file exists in `{output_folder}/brainstorming/`, load it as supplementary source alongside PRD and D-02. Skip this suggestion for AS-IS capture or Update/Resume states.

### 1c. Consume source inventory

Consume `artifacts.json` from Stage 1a into:
- PRD set (whole-doc or shard set — the discover script enumerates every shard automatically; do not re-glob)
- UX, use-case, research candidates

If `artifacts_dir_exists` is false → note it and proceed to the no-PRD HALT-menu below.

### 1d. No-PRD HALT menu

If `artifacts.json` returned zero PRDs AND `--prd-path` was not provided:

```
🚫 No PRD found in {planning_artifacts}
Options:
[1] Run `bmad-prd` first (recommended)
[2] Provide PRD path
[3] Continue with interactive elicitation (greenfield, no source)
[q] Quit
```

**Headless resolution:** if `--no-prd-ok` is set, take option 3 silently and log it. Otherwise return `blocked` with `reason: "no_prd_and_no_interactive_in_headless"`.

### 1e. Scope confirmation — HARD gate (interactive only, unless short-circuited by 1b) — B8-4

Present detected sources (PRD, UX, use-case counts), inferred mode/scope/type, **and the candidate flow/actor/path inventory**, and let the user confirm or override any dimension. This is a **hard gate**, not a soft "anything to adjust?": which flows, actors, and paths are in scope is a **domain decision** (Autonomy A5) — do not generate any diagram until the scope is confirmed. The previous behavior (infer scope, generate, ask later) is the exact pattern that let an un-scoped flow slip through.

**Migration-vs-AS-IS sanity check** (fires at confirmation): if mode resolves to `migration` (either auto-inferred or via `--mode=migration`) but `artifacts.json` reports `as_is.has_as_is: false`, warn the user and offer to switch to `greenfield`. In headless mode this returns `blocked` with `reason: "migration_without_as_is"` unless the user passes `--allow-migration-without-as-is` to acknowledge.

**Headless resolution (Autonomy):** `--strict` returns `blocked` with `reason: "scope_unconfirmed"` at the first flow/actor/path scope decision that the flags did not pin down. `--assumptions-allowed` (CI default) takes the inferred scope, logs it to `.decision-log.md` as an `ASSUMPTION` (which flows/actors/paths it assumed), and continues — it never blocks on the first question.

Initialize the primary document from `{workflow.business_flow_template}`, translating template prose to `{document_output_language}` per the Language Rules. Append a new session block to `.decision-log.md`. Mark `stepsCompleted` to include `stage-1`. Set primary frontmatter `updated` to today.

## Stage 2 — Discovery

From the chosen sources or interactive elicitation, extract:
- **Actors** — user roles, external systems, scheduled processes (in `{document_output_language}`)
- **Triggers** — what initiates each flow
- **Steps** — sequence of interactions between actors and the system
- **Decision points** — conditional branches (for `flowchart` variant)
- **Outcomes** — success and failure end states
- **Paths (use-case coverage)** — per flow, enumerate the **main / alternate / exception** paths (actor-goal use-case style; never stop at the happy path). Assign each path a **stable path-ID** (`PATH-NN`) so task-breakdown and test cases can reference it. A flow with no alternate/exception path is surfaced for the user to confirm or fill.

Present extracted actors and flows for confirmation. For migration mode, run discovery twice — once for AS-IS, once for TO-BE — surfacing the deltas explicitly. Capture non-flow insights surfaced during discovery (performance, security, integration constraints) to an `### Addendum` block in `{ws}/.decision-log.md` without pausing the flow.

**Zero-actor branch** — if the source contains no human or system actors (e.g. pure data-pipeline products triggered solely by cron or queue events), do not render a vacuous "System talks to itself" diagram. Promote the trigger (scheduled job, queue, webhook) to a first-class actor and explain the choice in the decision log. Interactive: confirm with the user. Headless: log and continue.

**Compaction-flush at the end of this stage** (required, not optional). Before moving on:
- Write actor list and flow inventory to the primary document's frontmatter (`stage_2_actors`, `stage_2_flows`).
- Append a `### Discovery snapshot (Stage 2 flush)` block to `.decision-log.md` carrying actors, triggers, and the flow inventory verbatim.
- Update primary frontmatter `stepsCompleted` to include `stage-2` and `updated` to today.

If compaction drops the conversation mid-stage, the next run resumes from these artifacts rather than re-eliciting.

**Soft gate (interactive only):** Present the actor/flow summary and ask "anything to adjust before I generate diagrams?" before proceeding. Headless: skip, proceed immediately.

## Stage 2b — Grounding-to-code (AS-IS reality check) — B8-3

For a **migration / brownfield** flow, the AS-IS must be grounded in the **real code or observed behavior**, not just the PRD's narration of "how it works today" — the PRD is a description, and descriptions drift from what the system actually does. Read the relevant code (or run/observe the behavior), and for each AS-IS path that the PRD describes, check it against the ground truth.

Record the result in the template's **Grounding-to-code log** table: the AS-IS path (by `PATH-NN`), the ground-truth source (a code reference like `module/file.py:func`, or "observed: …"), and any **divergence** from the PRD with its resolution. A divergence is *not* a silent overwrite — surface it so the user decides whether the diagram follows the code (usual) or the PRD (rare, with a reason).

- **Greenfield** (no existing code/behavior): write a single row `N/A — greenfield, no existing behavior to ground against`. Do not fabricate a code reference.
- **Headless:** run the same grounding where code is reachable; log divergences to `.decision-log.md`. Under `--strict`, an unresolved divergence blocks (domain decision); under `--assumptions-allowed`, log it as an `ASSUMPTION` (diagram follows code) and continue.
- This layer does not call a script — code↔diagram grounding is judgment. (The model↔code drift *detector* `model_drift` lives in D-19's reconcile; here the comparison is behavioral, not structural.)

## Stage 3 — Diagram Generation

For each in-scope flow, render one Mermaid block per the resolved diagram type:
- **Swimlane by actor (BPMN-style)** — make each actor's responsibility visible: in `sequenceDiagram` declare one `actor`/`participant` per lane (3–7 lanes) and route every message through them; in `flowchart` group nodes into per-actor `subgraph` lanes. Hand-offs between lanes are the integration seams. Avoid a single-lane "system talks to itself" diagram.
- Annotate each path with its **path-ID** (`PATH-NN` from Stage 2) — e.g. a `Note over` / `%% PATH-NN` marker — so the alternate/exception branches are traceable to task-breakdown and tests.
- Use `actor` for human users, `participant` for systems.
- Label messages with action verbs in `{document_output_language}`; keep Mermaid keywords and code identifiers in English (Language Rules).
- **No `;` in message or Note text** — Mermaid parses a semicolon as a statement separator, so `A->>B: kiểm tra; khóa` fails to render. Use `,` instead, or split into two message lines. (Stage 4 flags any leftover `;` as auto-fixable.)
- One flow per Mermaid block — split long flows by sub-process.
- Migration mode: AS-IS section first, TO-BE section second, with brief delta notes between them.
- Update mode with `--update-flow=<name>` (or interactive U2): re-render only the specified flow, leaving other Mermaid blocks untouched.

**Revision history table — scope-of-change gate:**

- **Create / Fresh** (`fresh_reason: "no_primary"` or `"crashed_no_progress"`): today's date, version `1.0`, "Initial version" → `{user_name}`, translated to `{document_output_language}`.
- **Update** — *do not bump the minor version mechanically*. Determine scope-of-change first:
  - **Auto-detect default:** run `python3 {skill-root}/scripts/diff-stage2-flush.py {primary} {ws}/.decision-log.md -o {ws}/.scan/scope-diff.json`. The script returns `scope: "polish"|"semantic"`, `actors_changed`, `flows_changed`. Polish → append a note to the existing latest revision row. Semantic → append a new row, bumping minor: `1.2` → `1.3`.
  - **Manual override** (interactive): ask the user "polish (typo / wording / layout) or semantic (actors / flows / outcomes)?".
  - **Headless override:** `--scope-of-change=polish|semantic|auto` (default `auto`). Polish and semantic skip the diff; `auto` runs the script.
  - Either path: log the chosen scope and the rationale to `.decision-log.md`.

**Anti-churn (T2.11).** Bump the version **once per session**, not once per edit — batch a session's changes into a single revision row. If the revision history is already long (the model keeps churning), the model is not frozen yet: surface it and suggest the user set `maturity: exploratory` or run a `[DSC]` model-spike to stabilize the flow, rather than appending yet another revision row. (The shared `churn_assessment` is the structural read other skills use; here the cue is the visible length of the revision-history table.)

Update primary frontmatter `stepsCompleted` to include `stage-3` and `updated` to today.

Then present the **Parallel-lens menu** (above). Stage-3 lens-targets: stress-test actor coverage, decision-branch completeness, and AS-IS/TO-BE delta clarity.

## Stage 4 — Validation

Run the three deterministic validators in parallel (they are independent):

```
python3 {skill-root}/scripts/validate-mermaid.py {primary} --expected-actors "<comma-separated stage-2 actors>" -o {ws}/.scan/mermaid.json

python3 {skill-root}/scripts/check-fr-coverage.py --prd <each-prd-path-or-shard> --d06 {primary} --pattern "{workflow.fr_id_pattern}" -o {ws}/.scan/fr.json

python3 {workflow.flow_coverage_script} {primary} --project-root {project-root} --sources "<D-02 path,…>" --path-id-pattern "{workflow.path_id_pattern}" -o {ws}/.scan/flow.json
```

`check-flow-coverage.py` is **advisory** (B8-2/B8-5/B8-6) — the *blocking* cross-doc gate is `hbc-check-implementation-readiness` [IR] / the Phase-1 gate, and Mermaid *rendering* is `validate-mermaid.py`'s job. It reports, per the honest-verdict contract:
- `single_path_flows` (B8-2) — Mermaid blocks with no alternate/exception branch (a `sequenceDiagram` with no `alt/opt/par`, a `flowchart` with no decision diamond; `stateDiagram` is exempt). For each, **confirm with the user** the flow is genuinely happy-path-only, or add the missing alternate/exception path. Never auto-add a path.
- `phantom_flows` (B8-5) — blocks that reference no REQ id: either a phantom (no requirement backs it) or an un-annotated flow (cite the REQ it realizes). Surface each.
- `uncovered_reqs` (B8-5) — REQs defined in `--sources` (D-02) referenced nowhere in D-06: draw them, or record in the REQ↔flow-facet table why they are not flows (e.g. "traced via test only"). Only computed when `--sources` is supplied.
- `malformed_path_ids` (B8-6) — `PATH-…` tokens that do not match `{workflow.path_id_pattern}` (e.g. `PATH-1` instead of `PATH-01`). Fix the id.

If any validator fails to execute (not "returns issues" but "cannot run at all"), note in `.decision-log.md` that script validation was unavailable and fall back to LLM-only judgment for that check. The flow-coverage findings are **advisory**: log them and surface to the user, but they do not block the headless run.

**Render check (S-2):** `validate-mermaid.py` now actually renders each block with the Mermaid CLI (`mmdc`) when available. Inspect `mermaid.json` → `render_check`: `"ok"` = every block renders; `"failed"` = a block has a `render_failed` issue (real Mermaid syntax error — fix it); `"skipped: mmdc not installed"` = rendering was **not verified** (structural checks only — do NOT treat a green result as "renders"; install `@mermaid-js/mermaid-cli` for the full check, or pass `--no-render` to silence intentionally).

Pass each PRD path (or each shard from `artifacts.json` for sharded PRDs) as a separate `--prd` argument. If `fr.json` reports `vacuous: true` (zero identifiers in both PRD and D-06), surface a warning: "FR coverage check passed vacuously — PRD contains no FR-*/NFR-* identifiers. Consider whether your PRD uses a different naming convention." In headless mode, log the vacuous result to `.decision-log.md`.

Judgment checks (LLM, not script):
- **Layout readability** — message ordering reads naturally; participant ordering minimises crossings.
- **AS-IS / TO-BE delta clarity** — migration mode only; deltas are explicit, not implied.
- **Revision history** — populated with version, date, author, change description.
- **Language consistency** — output prose in `{document_output_language}`, carve-outs preserved.

Present consolidated findings (script issues + LLM findings). Fix issues:
- **Interactive:** collaborative fix loop.
- **Headless:** apply only validator issues marked `auto_fixable: true` in `mermaid.json`. The validator decides what counts as safely-auto-applicable (e.g. adding a `participant` declaration where the alias appears in arrow lines and no declared participant conflicts). Log every auto-fix to `.decision-log.md` citing the validator's `fix_hint`. For non-auto-fixable issues (uncovered FRs, missing expected actors, orphan declarations the user may have wanted), do not silently invent — return `blocked` with `reason: "mermaid_validation_failed"` or `reason: "fr_coverage_gap"` so the automator can decide.

Update primary frontmatter `stepsCompleted` to include `stage-4` and `updated` to today.

Then run the **Mandatory review (Stage 4a)**, then present the **Parallel-lens menu** (above). Stage-4 lens-targets: challenge edge cases (failure paths, race conditions, hostile inputs) and check the artifact reads cleanly to a fresh reviewer.

## Stage 4a — Mandatory adversarial + edge-case review (B8-7 / T2.8)

Before D-06 reaches the Phase-1 gate it must pass an **independent** review pass — D-06 is one of the documents that enters mandatory review (alongside D-02, D-27):

1. Invoke `bmad-review-adversarial-general` (cynical review: is each flow justified, grounded, internally consistent?) and `bmad-review-edge-case-hunter` (every branch / boundary: missing exception path, unhandled state transition, an actor with no failure handling) against the D-06 flows.
2. Triage findings: fix structural/path gaps now; record judgment calls in `.decision-log.md`.

**Availability fallback (load-bearing).** `bmad-review-adversarial-general` and `bmad-review-edge-case-hunter` ship in `bmm`/`core`, not HBC. If the consumer does **not** have them installed, do **not** hard-block: apply the same two review lenses **inline** (the adversarial and edge-case perspectives, as in the Parallel-lens party-mode), and record `review: ran inline (skills unavailable)` in `.decision-log.md`. Either way, record which path ran (real skill vs inline) so the gate sees the review happened.

**Headless:** run the review (or inline fallback) non-interactively; record the outcome to `.decision-log.md` and into `review_lenses_run`. This stage does not block the headless run — the Phase-1 gate enforces that the review evidence exists.

## Stage 4b — Semantic Review (Layer 2)

Script + render validation only proves structure. Before saving, run the **semantic review** per the shared rubric (`.claude/skills/hbc-shared/references/semantic-review-rubric.md`) with an **independent skeptic lens** (review the flows as an adversary who assumes a facet was cut, not as their author). Apply the **facet-split discipline** per flow (read vs write/state-change · the surface the flow runs on — UI / admin / back-office / API / batch · lifecycle transitions): a diagram that draws only the happy read path while D-02 implies a write, admin, or exception variant has an open facet — name it so downstream `hbc-create-er-diagram` (D-19) and the test skills (D-26/D-27) know it must be modelled and tested, rather than letting the cut-out facet vanish silently (the seam).

Record `semanticReview` frontmatter: `status` is `passed` **only when `openFacets` is empty AND the user signs off** (T2.12); otherwise `pending` + the facet list. The shared `semantic_review_status` is the single structural read of this block, and the Phase 1 gate REVIEW item enforces it.

**Headless:** run the same rubric and write the frontmatter; the sign-off follows the Autonomy mode (`--strict` blocks on a non-empty `openFacets`; `--assumptions-allowed` leaves `status: pending`, logs the open facets, and proceeds). This layer does not block the interactive→gate handoff — the Phase 1 gate enforces it. Never fabricate coverage to force `passed`.

## Stage 5 — Save and Handoff

Finalize `{primary}`. Set `stepsCompleted` to the full list (`stage-1..5`), `lastStep` to `complete`, `updated` to today, and the `semanticReview` block from Stage 4b. Append a closing session block to `.decision-log.md` summarising:
- Sources used, mode, scope, diagram type
- Scope-of-change classification (Update mode only)
- Auto-fixes applied (headless)
- Lenses run (`review_lenses_run`)
- Handoff target — which downstream skill should consume this output

Workflow successor (next step): run the Phase 1 gate (`hbc-phase-gate` [PG]) — D-06 is the last Phase 1 artifact before the gate. Data consumers (later, in Phase 2): `hbc-create-er-diagram` (D-19) and `hbc-create-test-plan` (D-26) read this flow.

If the flow will feed downstream LLM consumers, offer to invoke `bmad-distillator` against the primary to produce a token-efficient distillate. Skip with a note if distillator is unavailable; never inline a substitute.

**Headless mode:** emit the JSON return contract per [`headless-contract.md`](headless-contract.md), substituting every placeholder with its resolved value before emission.

## Sync Handoff (hbc-traceability impact integration)

Applies only in `update` mode. Full contract: `hbc-traceability/references/impact-capability.md`.

- **Suppression guard (BR-13):** if invoked with `--invoked-by-sync` (or `invoked_by_sync=true`), do NOT suggest or trigger sync — skip this whole section. This prevents the update→sync→update loop.
- **Hybrid trigger (default):** after a successful update, suggest (emit the message in `{communication_language}`): _"The document has been updated. Run `hbc-traceability impact` to sync the dependent documents/tests/code?"_
- **Auto-chained trigger:** if `{workflow.auto_sync_after_update}` is true, invoke `hbc-traceability impact` directly (it will cascade downstream). Default is false.
