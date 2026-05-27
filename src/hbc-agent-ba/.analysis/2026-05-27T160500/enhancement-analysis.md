# Enhancement Analysis — hbc-agent-ba

**Scanner:** L4 Enhancement Opportunities
**Date:** 2026-05-27T160500
**Skill:** `src/hbc-agent-ba`
**Context:** Second-run analysis. First run (T143000) identified 18 findings (4 HIGH, 7 MEDIUM, 7 LOW). This run evaluates the current state of the skill after updates made between runs, identifies what was resolved, what remains open, and adds fresh perspective.

---

## Skill Understanding

`hbc-agent-ba` is a persistent coordinator agent for Phase 1 of the HBC waterfall lifecycle. It adopts a Business Analyst persona, scans existing Phase 1 artifacts (D-02, D-03, D-06, gate), and dispatches to five workflow skills via a menu (REQ, GLO, BF, PG, TR). The primary user is an analyst, PM, or developer working through structured HBC documentation who expects a consistent BA identity across multiple sessions and workflow switches. The key assumption: the user invokes the BA explicitly and returns to it repeatedly; the agent's value accrues over sessions, not just within one.

---

## What Changed Since the First Run

The SKILL.md was substantially updated between T143000 and T160500. Tracking changes against the first-run findings:

| Finding | First-Run Status | Current Status |
|---|---|---|
| O1: Missing output_path scalar | HIGH — absent | **Resolved.** `output_path = "{project-root}/_hbc_output/plan"` now in customize.toml; SKILL.md references `{agent.output_path}`. |
| O2: No open-floor opening | HIGH — absent | **Resolved.** Greet and Present now: "If the user's initial message already names an intent... skip the menu and dispatch directly. If it contains substantive context... acknowledge and absorb it before presenting the menu. Otherwise, briefly invite the user to share what they're working with — then render `{agent.menu}`." |
| O3: No headless path | HIGH — absent | **Resolved.** `## Headless Mode` section added with `-H`/`--headless` flag, explicit JSON return schema, and correct `status: complete/blocked` contract. |
| O4: No resume protocol | HIGH — absent | **Partially resolved.** "If existing artifacts found, surface the most recently updated one with its date and offer to resume where the user left off or start fresh." Timestamp sourcing now comes from the scan script's `updated` field. |
| O5: Prescriptive step numbering | MEDIUM | **Partially resolved.** Steps 2-4 collapsed; "Step 1: Resolve the Agent Block" and "Scan Phase 1 State" remain labeled (correctly, as fragile operations). Embody Persona and Load Context and Greet and Present are outcome-style headings without step numbers — improvement. |
| O9: No redirect for confused users | MEDIUM | **Resolved.** Menu Dispatch now: "If no menu item fits the user's stated goal, acknowledge the mismatch, suggest an appropriate adjacent skill (e.g., `hbc-create-er-diagram`... `bmad-help`...), and offer to dismiss the BA persona." |
| O10: State scan should be a script | MEDIUM | **Resolved.** `scripts/scan-phase1-state.py` exists, accepts output_path, returns JSON with status/phase1_state/next_recommended/reason. |
| O11: name comment unclear | LOW | **Resolved.** Comment now: "Non-configurable. Name is intentionally blank for this module agent; the title field is the display identity. Fork the skill to change it." |
| O12: No stop-and-wait signal | LOW | **Resolved.** Last line of SKILL.md: "Present the menu and stop. Wait for the user's selection." |
| O13: Overview lacks domain framing | LOW | **Resolved.** Overview now includes: "In waterfall, the cost of a vague requirement compounds: a missed term in D-03 produces an ambiguous function in D-02 that produces an untestable acceptance criterion at the gate." |
| O16: Post-workflow lacks artifact confirmation | LOW | **Resolved.** Menu Dispatch: "After each workflow completes, confirm the artifact produced and its path (e.g., 'D-03 Glossary written to `[path]`'), then return to the menu with an updated status summary." |

**Net change:** 4 HIGH → 0 HIGH remaining (all resolved or partially resolved). 7 MEDIUM → 4 remaining open. 7 LOW → approximately 4 remaining open. This is a meaningful quality improvement.

---

## User Journeys

### First-Timer

**Narrative:** Developer or junior BA invokes the BA for the first time, no artifacts exist, they have a mental model of the project but nothing written.

**Bright spots:**
- Open-floor opening now present: the agent absorbs context before forcing the menu. This is a genuine improvement.
- Phase 1 state scan gives immediate orientation ("D-02 missing, D-03 missing, D-06 missing — start with REQ").
- Suggested flow REQ → GLO → BF → PG → TR is present.
- Domain framing in Overview now explains *why* precision matters.

**Friction points:**

1. **D-02/D-03/D-06 codes are opaque to a true first-timer.** The greeting shows artifact codes from the scan ("D-02: missing, D-03: missing") before any explanation of what these are. The menu maps them: "REQ → D-02 Requirements Specification." But a user who doesn't know the HBC document taxonomy sees codes in the status before seeing the menu that decodes them. Small reordering — show menu then status, or decode codes in status — would help.

2. **No onboarding path for a truly blank-slate first-timer.** A first-timer with no project context and no artifacts sees the menu immediately after the open-floor check. There is no "would you like me to walk you through Phase 1 step by step?" option. This is a low-opportunity gap — most users of this skill have some project context — but it's a friction point for the genuinely new.

---

### Expert Returning User

**Narrative:** Senior BA returning after a two-week break. They need to update requirements after a stakeholder call. They type the BA trigger and expect to be back in context quickly.

**Bright spots:**
- Resume protocol now present: "If existing artifacts found, surface the most recently updated one with its date and offer to resume where the user left off or start fresh."
- Direct dispatch on named intent ("update REQ for payment module") still works.
- Proactive gate suggestion when all three artifacts exist is still correctly wired.

**Friction points:**

3. **Resume offer is singular.** The current text says "surface the *most recently updated one* with its date." If the expert has all three artifacts and D-02 was updated yesterday while D-03 was updated last month, they see only D-02's timestamp. For a returning expert managing multiple active artifacts, surfacing all three timestamps in a compact table would be more useful. The resume offer would then be: "D-02 updated yesterday, D-03 last month, D-06 two weeks ago — pick up where you left off on any of these?"

4. **Context carry still unoperationalized.** O6 from the first run remains open. "Carry domain context forward — terms from GLO inform REQ review, requirements from REQ inform BF design" is stated but the mechanism is still undefined. When dispatching [REQ] after [GLO] exists, does the agent pass a D-03 distillate? Load D-03? The new dispatch section adds: "When dispatching to a workflow skill whose predecessor artifact exists (e.g., dispatching [BF] when D-02 is available), mention the predecessor path so the workflow can load it." This is an improvement — it now explicitly says "mention the predecessor path." But it depends on the receiving workflow skill self-loading from the mentioned path. If `hbc-create-requirements` doesn't know to look for D-03, the context pass silently fails. The agent cannot verify this. The finding remains medium-opportunity: the mechanism is now documented but its effectiveness is contingent on downstream skills.

---

### Confused User (Wrong Intent)

**Narrative:** PM invokes "phân tích" meaning competitive analysis.

**Bright spots:**
- The redirect/mismatch path now exists in Menu Dispatch.
- "bmad-help" is always available outside menu.

**Friction points:**

5. **Description trigger phrase "phân tích" still present.** O8 from the first run remains unresolved. The current description is: `"Phase 1 Analysis coordinator for HBC waterfall lifecycle. Use when user says 'BA', 'business analyst', 'phân tích yêu cầu', 'phân tích nghiệp vụ', 'giai đoạn 1', or agent menu [BA]."` — this has already been tightened to `'phân tích yêu cầu'` and `'phân tích nghiệp vụ'` (specific compound phrases) rather than bare `'phân tích'`. The first-run finding was that bare `'phân tích'` was in the description — it is not. O8 is actually **resolved** on re-read. The description already uses the specific forms. *Finding corrected: O8 was resolved and not flagged correctly in the change tracking above.*

---

### Automator (Headless / Pipeline)

**Narrative:** Orchestrator agent wants Phase 1 completeness status post-sprint.

**Bright spots:**
- Headless mode now fully documented with `-H`/`--headless` flag.
- JSON return schema is explicit and matches BMad contract.
- `scripts/scan-phase1-state.py` is deterministic and supports `-o` output-to-file flag.

**Friction points:**

6. **Headless mode relies on flag in invocation text, which may not reach SKILL.md.** The headless section says "If invoked with `-H` or `--headless`". In practice, the skill is invoked via the BMad skill dispatch system — the user or orchestrator sends a text message. Whether `-H` reliably signals headless mode depends on how the harness passes flags. There is no `headless` scalar in `customize.toml` that an orchestrator could set as a persistent configuration. An orchestrator that always wants headless behavior cannot set it once — it must include the flag in every invocation message. A `headless_default = false` scalar in customize.toml would let teams configure headless-always at the team level.

7. **Headless mode skips agent block resolution.** The headless section says "skip persona adoption, greeting, and menu. Execute only the agent block resolution, config loading, and Phase 1 state scan." But "agent block resolution" is Step 1 — the `resolve_customization.py` script — which the headless path *does* include. However, config loading (Step 2: "Load config from `{project-root}/_bmad/config.yaml`") is needed to know `{user_name}` and `{communication_language}` — which headless mode doesn't need. The headless path could be lighter: Step 1 (resolver for `output_path`) + scan script. The current description is slightly ambiguous on which "config loading" steps run in headless mode.

---

### Edge Case: Hostile Environment (Missing Deps, Limited Context)

**Narrative:** Script fails, config missing, context compaction drops SKILL.md mid-session.

**Bright spots:**
- Script fallback for resolver failure is correctly documented in Step 1.
- Script fallback for scan failure is documented in Scan Phase 1 State.
- Both fallbacks are self-contained in their respective sections — compaction-safe.

**Friction points:**

8. **Missing project-context.md handling still partial.** O7 from the first run remains open. The current SKILL.md says (in Embody Persona and Load Context): "If a `file:` glob resolves to nothing (e.g., no `project-context.md` found), note the gap in the greeting and ask the user for a brief project summary before proceeding." This is a meaningful improvement — it is now present. However, the instruction is inside the persona adoption block, which runs before the state scan. The greeting note about missing context and the Phase 1 status display are both in the Greet section. There may be a sequencing issue: if the agent notes "no project-context.md found" during persona load and immediately asks for context, the user is prompted *before* seeing the Phase 1 status that would help them understand what to provide. *This is low-severity and likely self-correcting in practice.*

9. **No fallback if `output_path` is not set or invalid.** `customize.toml` declares `output_path = "{project-root}/_hbc_output/plan"`. The scan script handles "directory not found" gracefully (returns all-missing status). But the SKILL.md instruction says "Run: `python3 {skill-root}/scripts/scan-phase1-state.py {agent.output_path}`" — if `{agent.output_path}` is undefined (e.g., resolver failure with no local toml providing the key), the script is invoked with a literal `{agent.output_path}` string. The fallback block says "check `{agent.output_path}` manually for `D-02*`..." — same problem. Consider adding: "If `{agent.output_path}` is unresolved, default to `{project-root}/_hbc_output/plan`."

---

## Headless Assessment

**Level: Headless-ready** (upgrade from "Partially adaptable" in the first run).

The headless path now exists, is documented, and has a concrete JSON return schema. The scan script supports file output (`-o` flag). The main remaining gap is:

- No `customize.toml` scalar for `headless_default = false` — teams wanting always-headless must inject the flag in every invocation.
- Headless section's scope of "config loading" is slightly ambiguous — could specify "load only `output_path` from agent block" rather than full config.

**What a headless invocation needs (current state):**

```
Invocation: /hbc-agent-ba --headless
Or:         /hbc-agent-ba -H
Return:     { "status": "complete|blocked", "phase1_state": { "D-02": {...}, "D-03": {...}, "D-06": {...}, "phase-1-gate": {...} }, "next_recommended": "...", "reason": "..." }
```

The decision log path is not included in the return value. The principles say headless should return the log path for audit trail. Since this agent doesn't maintain a session-level decision log (it defers logging to individual workflow skills), this omission is reasonable — but worth noting.

---

## Facilitative Patterns Check

| Pattern | Status | Notes |
|---|---|---|
| Open-floor opening | **Present** (added) | "If it contains substantive context... acknowledge and absorb it before presenting the menu. Otherwise, briefly invite the user to share what they're working with." Good implementation. |
| Soft-gate elicitation | Partial | Menu dispatch returns to menu after each workflow, but no explicit "anything else before we move on?" The proactive gate suggestion after 3 artifacts exist is the closest approximation. |
| Intent-before-ingestion | Present | Direct dispatch on named intent still works. Open-floor opening improves this further. |
| Capture-don't-interrupt | Not applicable | No multi-turn discovery within the agent. |
| Dual-output | Missing | No distillate. Context carry is now documented as "mention the predecessor path" — better than nothing, but not a real distillate. The dispatched skills receive a path pointer, not a pre-processed token-efficient summary. |
| Parallel review lenses | Not applicable | Coordinator, not reviewer. |
| Three-mode architecture | Now two modes | HITL (guided) + Headless. "Yolo" (expert fast-track) not present, but given the waterfall lifecycle structure, this is appropriate — Yolo would undermine quality gates. |
| Graceful degradation | Present | Script fallback for both resolver and scan. Missing project-context.md handled. |
| Decision-Log Workspace | Not applicable to sessions | Decision log exists for skill build. Session-level log not needed for a coordinator agent — individual workflow skills own their artifacts. Correct call. |

---

## Findings

### [HIGH] Headless mode has no customize.toml configuration scalar

**Location:** SKILL.md `## Headless Mode`; customize.toml

**What:** Headless mode is invoked via `-H`/`--headless` flag in the invocation message. There is no `headless_default` or `headless` scalar in `customize.toml`. An orchestration team that always wants this agent to run headless (e.g., in CI) must include the flag in every pipeline call. There is no "configure once, apply always" option.

**Suggestion:** Add `headless_default = false` to `customize.toml` `[agent]` block. In SKILL.md headless section, add: "Also activates if `{agent.headless_default}` is `true`." This lets teams override once rather than injecting the flag in every invocation.

---

### [MEDIUM] Resume protocol surfaces only the most recently updated artifact

**Location:** SKILL.md, Greet and Present

**What:** "If existing artifacts found, surface the most recently updated one with its date and offer to resume where the user left off or start fresh." This is good for a single-artifact project but insufficient for a returning user who has all three core artifacts active. If D-02 was updated two weeks ago and D-03 was updated yesterday, only D-03's timestamp surfaces — the user doesn't see that D-02 may be stale relative to last week's stakeholder meeting.

**Suggestion:** When multiple artifacts exist, surface a compact status table with all their timestamps rather than only the most recently updated one. The scan script already returns `updated` for all artifacts — the data is there. Example: "D-02 Requirements (2026-05-10), D-03 Glossary (2026-05-26), D-06 Business Flow (2026-05-15) — pick up where you left off or start fresh?"

---

### [MEDIUM] Context carry mechanism depends on downstream skill behavior

**Location:** SKILL.md, Menu Dispatch

**What:** "When dispatching to a workflow skill whose predecessor artifact exists (e.g., dispatching [BF] when D-02 is available), mention the predecessor path so the workflow can load it." This is a reasonable mechanism but its effectiveness depends entirely on whether the receiving workflow skill (`hbc-create-business-flow-diagram`, `hbc-create-requirements`) actually loads the mentioned path. If those skills don't, the path mention is noise.

**Suggestion:** Either (a) verify that each downstream skill loads mentioned predecessor paths, and add a note here that the mechanism is confirmed end-to-end, or (b) change the instruction to have this agent proactively read the predecessor's summary/frontmatter and pass a brief context capsule (key terms from D-03, requirement IDs from D-02) in the dispatch — rather than leaving it to the downstream skill to decide what to load. Option (b) is the dual-output pattern applied at dispatch time.

---

### [MEDIUM] Headless scope of "config loading" is ambiguous

**Location:** SKILL.md `## Headless Mode`

**What:** "Execute only the agent block resolution, config loading, and Phase 1 state scan." Config loading in the interactive path reads `config.yaml`/`config.user.yaml` to resolve `{user_name}`, `{communication_language}`, `{document_output_language}` — none of which are needed in headless mode. The headless path only needs `{agent.output_path}` to run the scan. Loading full config in headless adds unnecessary steps and potential failure points.

**Suggestion:** Specify: "Execute only agent block resolution (to resolve `{agent.output_path}`) and the Phase 1 state scan. Skip config.yaml, communication_language, and persona loading — they are not needed for the JSON return."

---

### [MEDIUM] D-02/D-03/D-06 codes appear in status before menu decodes them

**Location:** SKILL.md, Greet and Present

**What:** The greeting leads with Phase 1 status ("D-02: missing, D-03: missing") derived from the scan script, then renders the menu (which maps D-02 → Requirements Specification, D-03 → Glossary, etc.). A first-timer sees artifact codes before the menu that explains them. The typical user of this agent knows the HBC taxonomy, so this is low-friction — but it is friction.

**Suggestion:** Either (a) show menu first, then status table (so codes are decoded before they appear in status), or (b) expand status to include artifact names: "D-02 Requirements: missing, D-03 Glossary: missing, D-06 Business Flow: missing." The scan script returns `file` and `exists` — names could be added as a thin mapping in the SKILL.md instruction.

---

### [LOW] Soft-gate elicitation missing at workflow transitions

**Location:** SKILL.md, Menu Dispatch

**What:** After a workflow completes and the agent returns to menu, there is no "is there anything else about [D-03] before we move on?" moment. The agent confirms the artifact, shows updated status, and presents the menu. Users frequently remember one more thing at this exact moment — the "anything else?" question is the soft-gate pattern.

**Suggestion:** Add one sentence: "After artifact confirmation, briefly ask if there's anything the user wants to adjust or add before presenting the next menu choice." This costs nothing and captures the most common "oh wait I forgot..." moment.

---

### [LOW] Fallback if {agent.output_path} is unresolved

**Location:** SKILL.md, Scan Phase 1 State

**What:** The scan command is `python3 {skill-root}/scripts/scan-phase1-state.py {agent.output_path}`. If the resolver fails (script not found, merge error) and `{agent.output_path}` is not resolvable, the fallback block references the same unresolved token. The script invocation would fail with a literal `{agent.output_path}` path argument, and the fallback would search the same invalid path.

**Suggestion:** Add one line to the scan fallback: "If `{agent.output_path}` is unresolved, default to `{project-root}/_hbc_output/plan` (the declared default in `customize.toml`)."

---

### [LOW] Communication_language applied to Headless is undefined

**Location:** SKILL.md `## Headless Mode`

**What:** The skill uses `{communication_language}` for greetings and menu presentation. Headless mode skips this — correctly. But if headless mode encounters an error (script not found, output path invalid), the error message in the JSON `reason` field will be in whatever the LLM defaults to. A Vietnamese-language project might get an English error reason, or vice versa.

**Suggestion:** Either specify that `reason` is always English in headless mode (machine-readable, language-neutral), or add one word to the headless return schema: `"reason_lang": "en"` to make this explicit. The former (always English) is simpler and more pipeline-friendly.

---

## Top 3 Insights

**1. The skill resolved its most impactful gaps and the improvements are genuine.**

The four HIGH findings from the first run are all resolved or substantively addressed. The headless path, open-floor opening, artifact state scan script, and domain framing are real improvements that change user experience. This is a skill that has been thoughtfully updated in response to analysis — not patched superficially. The grade should move from B- to B or B+.

**2. The remaining medium-priority gap is the context-carry mechanism.**

The "carry domain context forward" aspiration has been documented as "mention the predecessor path." This is the right direction but it creates a hidden dependency: the mechanism only works if the downstream workflow skills (hbc-create-requirements, hbc-create-business-flow-diagram) actually consume the mentioned path. If one of them doesn't, the context carry silently fails and the agent cannot know. The highest-value addition now would be to either confirm the end-to-end mechanism or promote this agent to a brief active distillation step at dispatch time (read the predecessor's key terms or REQ IDs and pass them as a few-line context capsule, not just a path).

**3. Headless mode is now the agent's strongest engineering feature — protect it.**

The headless path is clean, schema-complete, and backed by a real deterministic script. The one fragility is that it relies on flag injection in every invocation rather than a persistent configuration. Adding `headless_default = false` to `customize.toml` would make this a first-class configurable behavior rather than a per-invocation convention. Given that pipeline integration is likely the primary headless use case, making it configurable-by-default protects against invocation-level mistakes.
