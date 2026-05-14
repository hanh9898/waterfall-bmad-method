# Enhancement Analysis — hbc-create-business-flow-diagram

## Skill understanding

Generates the HBLab D-06 Business Flow Diagram (Mermaid) from PRD/UX/research artifacts in `{planning_artifacts}`, or from interactive elicitation when those are absent. Primary user is a BMM-cycle facilitator (BA/PM) in a Vietnamese-speaking team that ships Japanese-titled deliverables; key assumptions are (a) planning artifacts use BMad's standard names/locations, (b) the user can choose between greenfield (TO-BE only) and migration (AS-IS + TO-BE) at Stage 1, and (c) the workspace folder + decision log is the source of truth across sessions.

## User journeys

### First-timer (BA who has only run the PRD skill before)

- *Narrative.* Activates after `bmad-create-prd`. The skill scans `{planning_artifacts}`, finds the PRD, and asks four confirmation questions (sources, mode, scope, diagram type) before discovery.
- *Friction.* Stage 1 asks "greenfield vs migration" as a flat choice, but a first-timer has no anchor for the consequences (TO-BE-only vs dual sections, downstream impact on the architecture skill). No tiny example or "if your PRD already describes a current system, pick migration" cue. They will pick greenfield to keep things simple and lose the AS-IS the PM actually wanted.
- *Friction.* The four Stage-1 questions arrive in a single batch but with no open-floor invitation first. The user can't volunteer "actually I already have a flow sketch in a Miro export, here's the path" — the script gives no slot for it.
- *Bright spot.* The workspace folder is created up front and the decision log captures the mode/scope choice, so a first-timer who picks wrong can re-run and see what they chose last time.

### Expert (BA running this for the fifth project this quarter)

- *Narrative.* Wants to slam through Stage 1 with "use the PRD, migration mode, multi-flow, sequenceDiagram — go". 
- *Friction.* There is no Yolo or quick-confirm path. The four-question dance fires every time, even when the PRD's structure makes the answers obvious. An expert running headless can pre-supply via flags (implicit), but interactive expert mode is the gap.
- *Friction.* No "I've already structured the PRD with explicit AS-IS/TO-BE sections — just lift them" shortcut. The skill re-elicits actors and triggers as if discovering from scratch.

### Confused user (invoked by accident or with wrong intent)

- *Narrative.* User says "tạo sơ đồ" meaning a class diagram or system architecture diagram; the trigger phrase matches loosely enough that this skill activates.
- *Friction.* No early intent-confirm step. The skill moves straight into scanning `{planning_artifacts}` and asking about modes, which feels like the right thing until the user realizes "wait, this is for business flows, not class diagrams". Time wasted, decision log polluted with a session that goes nowhere.
- *Friction.* No off-ramp suggestion ("if you wanted a class diagram, try D-18 / `hbc-create-class-diagram`" — if such a skill exists in the family, it's worth signposting).

### Edge-case user (technically valid but unexpected input)

Several genuine cases the skill does not call out and where the LLM will improvise differently each run:

- **PRD exists but has zero named actors** — pure data-pipeline product, batch jobs only. Stage 2's "user roles, external systems, scheduled processes" is broad enough to cover this, but the validation in Stage 4 ("every Stage-2 actor appears in at least one diagram") becomes vacuous and the diagram may end up with a single `participant System` talking to itself. No guidance for "promote the trigger / cron / event to a first-class actor".
- **PRD is sharded** — Stage 1 says "search whole docs first, fall back to sharded `*/index.md`". But the sharded PRD's actors and flows live in `prd/epics/*.md`, not in `index.md`. Reading only `index.md` will miss everything. The fallback rule is half-finished.
- **Multiple PRDs in `{planning_artifacts}`** — versioned PRDs, or sub-product PRDs in the same folder. The pattern `*prd*.md` matches all of them. The skill doesn't say "pick one and log why" or "ask the user".
- **No PRD AND no UX AND no use-cases** — falls back to "interactive elicitation". Fine in guided mode; in headless mode this is a silent infinite-question dead-end unless the caller pre-loads facts.
- **PRD describes a system that doesn't exist yet, but project mode was set to migration** — Stage 2 says "run discovery twice: once for AS-IS, once for TO-BE". For pure greenfield mistakenly marked migration, AS-IS discovery has nothing to find. The skill will likely fabricate an AS-IS rather than surface the mismatch.
- **User wants to regenerate** — re-running on the same workspace. Stage 1 says "append a new session heading to `.decision-log.md` if it already exists" but doesn't surface the prior primary document for resume/update intent. The user gets a fresh discovery loop on top of an existing artifact — the Decision-Log Workspace pattern's resume protocol is not actually enforced. Principle violated: **Decision-Log Workspace — Resume protocol**.
- **User wants to update one flow without touching the others** — no targeted-update path. Re-running rebuilds everything. Principle violated: **Decision-Log Workspace — Update mode**.
- **`output_folder_name = "D-06-{project_name}-{date}"`** — re-running on the same day overwrites/appends to the same folder; re-running the next day creates a *new* workspace and orphans the previous decision log. The dated folder name actively works against resume. (Flagging as a UX consequence of the default, not a structural fix.)

### Hostile environment

- **`resolve_customization.py` missing or fails** — Stage 1 has a manual fallback. Good. But the rest of the script invocations (the second one in `## On Complete`) have no fallback.
- **`bmad-distillator` unavailable** — Stage 5 says "skip with a note; never inline a substitute". Good — principle followed (**Graceful degradation**).
- **Template file missing** — `{workflow.business_flow_template}` may be absent in a stripped install. No fallback to "render the primary from scratch with frontmatter + revision-history skeleton". Skill will halt.
- **Compaction mid-discovery** — Stage 2 (discovery) is a single dense paragraph in SKILL.md. If compaction drops SKILL.md mid-flow the agent loses the AS-IS/TO-BE discipline ("run discovery twice; surface the deltas") because it isn't in the decision log. The decision log is described as canonical memory, but only mode/scope/source-docs are explicitly captured there — not the discovered actor lists. Principle violated: **Compaction survival** (Stage 2's enumeration of actors/triggers/steps/decisions/outcomes should be flushed to the workspace as it accumulates, not held in the conversation).

### The automator (headless caller — pipeline or another agent)

- *Narrative.* `bmad-create-prd` finishes, calls `hbc-create-business-flow-diagram --headless` with the PRD path. Expects a JSON return.
- *Friction.* Stage 1 has four interactive confirmations. Headless mode is mentioned ("Absence of PRD is a normal mode" / "log every auto-fix to the decision log" / Stage 5 JSON contract) but the four Stage-1 questions are never explicitly mapped to headless defaults. What does headless pick for mode? For scope? For diagram-type override? The skill says "log inferred defaults" but not what they are. An automator gets non-deterministic mode choice from run to run.
- *Friction.* No headless input contract. A caller pipeline has no documented way to *override* the inferred defaults — e.g. `--mode migration --scope multi-flow --diagram-type flowchart`. The skill mentions `--headless` / `-H` once in the description and never re-grounds the flag's semantics.
- *Friction.* When PRD is absent AND headless is set, what happens? Stage 1 says "switch to interactive elicitation" — that's a contradiction. Should return `status: blocked` with `reason: "no PRD found and headless mode prohibits elicitation"`, but that branch isn't called out.
- *Bright spot.* JSON contract format is correct and minimal (`status`, `skill`, `primary`, `decision_log`) — matches the principles file.

## Headless assessment

**Level: Easily adaptable** — core artifact creation can run headless, but Stage 1's four-question discovery and Stage 2's actor/trigger confirmation need a headless contract spelling out auto-resolutions.

**Interaction points that could auto-resolve:**

| Stage | Question | Default for headless |
| --- | --- | --- |
| 1 | Which source docs to include | All `*prd*.md`, `*ux*.md`, `*use-case*.md`, `D-04*`, `D-05*` found; log inclusion set |
| 1 | greenfield vs migration | Detect from PRD: if PRD has an "AS-IS / current state" section or migration-related keywords → migration; else greenfield |
| 1 | Scope (single vs multiple flows) | Detect from PRD epic count or use-case count: 1 → single, >1 → multi |
| 1 | Diagram type override | Use `{workflow.diagram_type}` |
| 2 | Actor confirmation | Skip confirmation; log inferred actor list |
| 4 | Fix issues collaboratively | Auto-fix Mermaid syntax errors; auto-extend on actor-coverage gaps; log each fix |

**Headless invocation contract the skill should declare:**

```
Inputs (flags):
  --headless / -H
  --prd <path>                  override auto-detected PRD
  --mode greenfield|migration   override inferred mode
  --scope single|multi          override inferred scope
  --diagram-type <type>         override workflow default
  --no-prd-ok                   allow elicitation-less generation from {project_knowledge}

Returns:
  { "status": "complete" | "blocked",
    "skill": "hbc-create-business-flow-diagram",
    "primary": "<path>",
    "decision_log": "<path>",
    "reason": "<one-line; only when blocked>" }
```

The skill currently states the return shape but not the input contract — automators reading SKILL.md cannot tell what they're allowed to pass.

## Facilitative patterns check

| Pattern | Present? | Notes |
| --- | --- | --- |
| **Open-floor opening** | Missing | Stage 1 dives straight into "scan `{planning_artifacts}`" then four confirmation questions. No "tell me what you have / what you're building / paste a flow sketch if you've got one" invitation. Would cost ~1 paragraph and front-load the unexpected inputs (Miro link, hand-drawn photo, prior architect's notes) before the four-question grid. |
| **Soft-gate elicitation** | Missing | Stage 2 lists five extraction categories and presents them for confirmation, but no "anything else about these actors or flows before we draw?" pause. Migration mode especially benefits — users always remember one more legacy edge case after they see the AS-IS list. |
| **Intent-before-ingestion** | Partially missing | The skill scans `{planning_artifacts}` *before* confirming intent. For a user who triggered by accident (see Confused-user journey) the scan is wasted; for a user who has artifacts elsewhere it's misleading. A one-line "are you here to capture an existing process, design a new one, or compare both?" *before* the scan would frame ingestion. |
| **Capture-don't-interrupt** | Missing | Stage 2 is structured-elicitation only. If the user volunteers "by the way the warehouse module also has an inventory-sync flow that runs nightly" while we're discussing the order flow, no slot to silently capture it for later. The decision log is described as memory, not as a side-channel capture surface. |
| **Dual-output** | Present (deferred) | Stage 5 offers `bmad-distillator` invocation for downstream LLM consumption. Good — but it's opt-in; given the explicit downstream chain (`bmad-create-architecture`, etc.) the distillate is almost always wanted. Consider defaulting to "yes" with opt-out. |
| **Parallel review lenses** | Missing | Stage 4 (Validation) is single-pass. A flow diagram is exactly the kind of artifact where two cheap parallel lenses transform quality: a *skeptic* ("does the happy path hide failure branches?") and an *actor-coverage scout* ("which roles from the PRD never appear?"). Currently Stage 4 reduces to a checklist. |
| **Three-mode architecture** | Partial | Guided + Headless present. No Yolo / quick-confirm middle. Expert users have to either run headless (and lose the chance to course-correct) or sit through Stage 1's four questions. |
| **Graceful degradation** | Present | Bmad-distillator skip path is correct. Customization-resolver fallback is correct. Missing: template-absent fallback, sharded-PRD fallback, multiple-PRD disambiguation. |
| **Decision-Log Workspace — Resume protocol** | Missing (canonical violation) | Workspace creation is correct, decision log is correct, but on re-activation the skill does not surface the prior `.decision-log.md` and offer Create/Update/Validate intents. It treats every run as a fresh create. |

**Most valuable to add, in order:**

1. Resume protocol on re-activation — biggest user-impact win, and the Decision-Log Workspace pattern is the principle most explicitly called out for revisable artifacts.
2. Headless input contract + per-question default declarations — the skill is HITL-shaped today even though it claims headless support.
3. Open-floor + intent-before-ingestion combo at Stage 1 — cheap, high-feel improvement.

## Findings

### High — Resume protocol absent for revisable artifact

*Location.* Stage 1, "Bind `{doc_workspace}` ... append a new session heading to `.decision-log.md` if it already exists."

*What I noticed.* The skill knows the workspace may already exist but does not surface the prior primary document, summarize the previous session, or offer an Update / Validate intent. The principles file's **Decision-Log Workspace** pattern names this as the canonical violation for skills that "look fine on the first pass and fall apart on revisit". The downstream chain (architecture, UX, stories) will revisit D-06 every time a PRD changes — re-runs are the norm, not the exception.

*Suggestion.* On Stage 1 entry, after binding `{doc_workspace}`, check whether the primary already exists; if it does, read `.decision-log.md` and surface a one-line summary plus `updated` timestamp, then ask whether the user wants to **Create fresh / Update one or more flows / Validate the existing diagram**. Each branch reads the prior decisions before proceeding. The dated `output_folder_name` default also fights this — consider documenting that resume looks across same-`{project_name}` folders, or recommending overriding the date out of the folder name when re-runs are expected.

### High — Headless mode declared but interaction defaults undefined

*Location.* Stage 1 questions 1–4; Stage 2 confirmation; Stage 4 "fix issues collaboratively".

*What I noticed.* `--headless` is named in the description and the JSON return is specified, but every interactive decision point lacks a "headless default" line. The principles file requires the decision log to "absorb every assumption made without the user" — that's only auditable if the assumptions are pre-named. Different runs against the same PRD will choose different modes / scopes / fixes silently.

*Suggestion.* For each interactive decision in Stages 1, 2, and 4, add a one-clause headless default (see the table in the Headless Assessment above). Where the default depends on PRD content, name the heuristic ("if PRD contains an AS-IS section or 'current system' keyword, infer migration; else greenfield"). When the heuristic is uncertain, return `status: blocked` with `reason` rather than guessing.

### High — Sharded PRD fallback is half-finished

*Location.* Stage 1: "search whole docs first, fall back to sharded `*/index.md`".

*What I noticed.* Sharded PRDs put their actors and FRs in `prd/epics/*.md` (or similar), not in `index.md`. Reading only the index gets the table of contents and misses the substance. The skill will run discovery on near-empty input and either elicit interactively (in guided mode) or hallucinate (in headless mode).

*Suggestion.* When falling back to a sharded structure, the rule should be "read `index.md` to discover shard paths, then read each linked shard". Or — keep the rule shorter — "for sharded PRDs, read the full shard set, not just the index". The current text invites the wrong behavior.

### Medium — No early intent gate before artifact scan

*Location.* Stage 1 enters scanning before any intent-confirm with the user.

*What I noticed.* Principle violated: **Intent-before-ingestion**. Users invoked by accident, or with a clear pre-existing flow file they want to import, or wanting to update an existing D-06 (see resume finding), all suffer the same wasted scan. Stage 1's four questions also feel less like a conversation and more like a form because they're not preceded by an open invitation.

*Suggestion.* Open Stage 1 with two sentences: an open-floor invitation ("share anything you already have — PRD path, sketches, prior flows, or just describe the process") and a one-line intent check ("are we capturing an existing flow, designing a new one, or both?"). The four-question grid then adapts to what the user volunteered.

### Medium — Stage 2 holds discovered state only in the conversation

*Location.* Stage 2 enumerates actors / triggers / steps / decisions / outcomes and "presents extracted actors and flows for confirmation".

*What I noticed.* The decision log is described as canonical memory, but Stage 2 doesn't flush its discovery output there. If compaction drops the conversation mid-discovery (especially in migration mode, where discovery runs twice), the agent can't recover the AS-IS work. Principle violated: compaction survival via Decision-Log Workspace.

*Suggestion.* After Stage 2 confirmation, write the actor list and flow inventory into the decision log (or directly into the primary as draft sections). Stage 3 then renders from disk rather than from conversation memory.

### Medium — Validation is single-lens

*Location.* Stage 4.

*What I noticed.* Validation is a five-item checklist run by the same agent that just authored the diagram. A flow diagram benefits sharply from a parallel critical lens — the same agent will not spot the failure paths it forgot to draw. Principle: **Parallel review lenses**.

*Suggestion.* Add a brief "fan out a skeptic and an actor-coverage scout (or run sequentially if subagents unavailable)" sub-step before finalizing the diagram. Skeptic asks "what happens on the unhappy path?"; scout asks "which PRD actors or epics aren't represented?". Findings feed the collaborative fix loop already in Stage 4.

### Medium — No quick-confirm path for experts

*Location.* Stage 1.

*What I noticed.* Expert users in guided mode have no way to say "all four defaults are fine, proceed". Forces a four-question dialog every run. Principle: **Three-mode architecture** (Yolo middle).

*Suggestion.* After computing defaults from PRD content, present them as a single confirmation block ("Inferred: migration mode, multi-flow scope, sequenceDiagram, all four PRD docs as sources — confirm or edit?") instead of asking four serial questions. Headless mode then == "auto-confirm this block".

### Low-opportunity — Multiple PRDs / multiple D-06 disambiguation

*Location.* Stage 1 source detection.

*What I noticed.* The glob `*prd*.md` is generous. Versioned PRDs, sub-product PRDs, or stale archived ones all match. Same for prior D-06 outputs that live in the workspace.

*Suggestion.* When more than one match is found, present the list with `updated` timestamps and ask the user (or pick the most recent in headless and log the choice).

### Low-opportunity — Distillate is opt-in, downstream chain is documented

*Location.* Stage 5.

*What I noticed.* The skill names four downstream LLM consumers but makes the distillate optional. Given those four named consumers, the distillate is almost always the right move.

*Suggestion.* Default distillate to on; allow `--no-distillate` to skip. Keep the graceful-skip on `bmad-distillator` unavailable.

### Low-opportunity — Revision history on re-run

*Location.* Stage 3: "Populate the revision history table with today's date, version 1.0, an initial entry, and `{user_name}`."

*What I noticed.* "Version 1.0" / "初版作成" is hardcoded as the initial entry — fine for first run. On re-run (after a resume protocol is added) the revision table should append a new row with bumped version, not overwrite. The skill currently doesn't address this because it doesn't have resume; once resume is added, the revision-history append needs naming.

*Suggestion.* When entering Update mode (after resume protocol), read the latest version from the existing revision-history table, increment (1.0 → 1.1 for minor, 1.x → 2.0 for actor/flow restructure — let the LLM judge), and append a new row describing the change. Don't replace.

### Low-opportunity — Off-ramp for wrong-diagram invocations

*Location.* Description trigger phrases.

*What I noticed.* The Vietnamese trigger "tạo sơ đồ luồng nghiệp vụ" is specific, but "tạo sơ đồ" (just "create a diagram") is a common phrasing. Confused-user activations cost time.

*Suggestion.* At the start of Stage 1, after the open-floor invitation, if the user's described content is clearly not a business flow (class hierarchy, system architecture, ER diagram), signpost the appropriate sibling skill and offer to exit. One sentence in SKILL.md.

## Top insights

1. **The Decision-Log Workspace pattern is half-built.** Workspace creation and append-on-existing are correct, but resume — the entire reason the pattern exists — isn't wired in. The downstream chain (architecture / UX / stories) will trigger re-runs of D-06 constantly when PRDs change; without resume + Update mode, every re-run is a fresh draft that forgets why the last one looked the way it did. This is the single biggest user-facing gap.

2. **Headless mode is named but not specified.** The flag, the JSON return, and the "log every assumption" instruction are all present. What's missing is the table that says *which* assumptions get made for *which* questions and *which* heuristic produces *which* default. Today an automator pipeline gets non-deterministic mode/scope/fix decisions across runs. The fix is a small headless-defaults table — not a redesign.

3. **Stage 1 trades open-floor warmth for a four-question form.** Cheapest delight win: replace the serial questions with (a) one-line open invitation, (b) one-line intent check, (c) a single inferred-defaults confirmation block. Reduces friction for experts, captures unexpected inputs from first-timers, gives confused users an early off-ramp — all in roughly the same word count Stage 1 already spends.
