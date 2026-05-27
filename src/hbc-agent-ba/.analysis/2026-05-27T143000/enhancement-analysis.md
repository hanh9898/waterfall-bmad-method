# Enhancement Analysis — hbc-agent-ba

**Scanner:** L4 Enhancement Opportunities
**Date:** 2026-05-27
**Skill:** `src/hbc-agent-ba`

---

## Skill Understanding

`hbc-agent-ba` is a persistent agent persona that coordinates Phase 1 of the HBC waterfall lifecycle. It acts as a menu hub — scanning existing Phase 1 artifacts, presenting a BA persona to the user, and dispatching to five workflow skills (REQ, GLO, BF, PG, TR). The primary user is an analyst or PM working through the structured HBC document lifecycle who needs a consistent identity across multiple work sessions and workflow switches. The key assumption is that the user invokes the BA explicitly, returns to it across sessions, and relies on it to carry cross-artifact domain context (glossary terms informing requirements, requirements informing business flow).

---

## User Journeys

### First-Timer Invoking the BA

**Narrative:** Developer or junior BA types "BA" or invokes the agent. They have a project in mind but no artifacts yet.

**Bright spots:**
- Phase 1 state scan on activation immediately tells them what's missing — no guesswork.
- Suggested flow (REQ → GLO → BF → PG → TR) is present, though briefly.
- Menu numbers allow zero-friction selection.

**Friction points:**

1. **No open-floor opening.** The skill jumps straight from greeting to menu presentation. A first-timer has context to share — a project brief, an existing Confluence page, a half-formed idea. There is no invitation to dump this before the menu appears. The principles file explicitly names "Open-floor opening" as a pattern BMad has seen pay off; this agent skips it entirely. The user is forced into menu-driven mode even when they arrived with a full mental model ready to share.

2. **Menu order mismatch with recommended flow.** The menu shows REQ → GLO → BF → PG → TR (codes ordered in menu declaration). Step 7 recommends "REQ → GLO → BF → PG → TR" — which happens to match. But the display is just a numbered table; there is no narrative arrow, no "here's where you start and why." A first-timer with all artifacts missing sees five equal options and must read the recommendation text carefully to understand the intended sequence.

3. **No explanation of what Phase 1 IS for a first-timer.** The state scan shows "D-02: missing, D-03: missing, D-06: missing" — but a true newcomer may not know what D-02 or the Phase 1 gate mean. The agent name and principles assume prior knowledge of the HBC lifecycle.

---

### Expert Who Knows What They Want

**Narrative:** Senior BA returning after a week. They know they need to update requirements after a stakeholder call. They type "update REQ for the payment module."

**Bright spots:**
- The "If the user's initial message already names an intent that maps to a menu item, skip the menu and dispatch directly" rule handles this well.
- Context carry across workflows (terms from GLO informing REQ review) is explicitly stated.

**Friction points:**

4. **Resume experience is undefined.** The expert returning to a partially complete Phase 1 sees the state scan, but there is no explicit "resume" affordance. The bmad pattern (Decision-Log Workspace) describes a resume protocol: "On activation, check whether a workspace already exists… surface it with the `updated` timestamp… and offer to resume." This agent scans artifacts and builds a status summary, but does not offer a structured resume path. If D-02 was last edited two weeks ago, the agent won't surface that timestamp or ask "pick up where we left off?"

5. **No session continuity hint after workflow completes.** After [REQ] finishes, the agent returns to menu with an "updated status summary." But there is no mechanism to carry insight from the just-completed workflow into the greeting for the next one. The stated "context carry" (GLO terms inform REQ review) is present as a principle but there is no guidance on _how_ the agent should operationalize that — e.g., when dispatching to REQ after GLO exists, should it load and pass a distillate of D-03 to the REQ workflow? The intent is good but the mechanics are unspecified, leaving it to chance.

---

### Confused User (Wrong Intent)

**Narrative:** PM invokes "phân tích" expecting a general analysis tool, not the Phase 1 BA. They want to analyze a competitor landscape, not write D-02 requirements.

**Bright spots:**
- "Chat, clarifying questions, and `bmad-help` are always available outside the menu" is a safety valve.

**Friction points:**

6. **No graceful exit / redirect path.** When a user is confused or in the wrong place, there is no explicit handling. The menu dispatch section only describes dispatch on a clear match or continuing the conversation. It does not tell the agent to recognize "I'm in the wrong place for you" and suggest an alternative skill. A confused user gets a menu that doesn't match their need and has to figure their own way out. A single line — "If none of the menu items fit the user's goal, tell them which adjacent skills might help and offer to dismiss the persona" — would close this gap.

7. **Description trigger phrases may be too broad.** The description uses "phân tích" (Vietnamese for "analyze") as a trigger. This is a very common word — any analytical task in a Vietnamese-language context could trip this. The quality principles warn against descriptions that "hijack unrelated conversations." An analyst asking to "phân tích performance metrics" or "phân tích đối thủ cạnh tranh" would land here unintentionally.

---

### Automator (CI / Another Agent Invoking Headless)

**Narrative:** An orchestrator agent wants to verify Phase 1 completeness after a sprint without human interaction. It invokes the BA, expects a structured state report, and routes based on result.

**Friction points:**

8. **No headless path exists.** The skill is 100% HITL. There is no headless invocation shape, no structured return format, and no documented way for a calling agent to get a machine-readable Phase 1 status. The Phase 1 state scan in Step 6 produces a "compact status summary to present after greeting" — conversational output, not a parseable return value.

   The quality principles describe the headless contract: "`status` is `complete` or `blocked`; on `blocked`, include a one-line `reason` and still return the log path so the caller can read the detail." None of this is present.

   For an orchestrator needing to decide "is Phase 1 done enough to proceed to Phase 2?" this agent is a dead end.

---

### Edge Case: Partial / Contradictory Input

**Narrative:** User has D-02 from a previous project, wants to adapt it, but has no project-context.md.

**Friction points:**

9. **Silent failure on missing project-context.md.** `persistent_facts` loads `file:{project-root}/**/project-context.md`. If the file doesn't exist, the glob silently resolves to nothing. There is no guidance on what the agent should do when foundational context is absent — proceed with reduced context? Ask the user to provide it? Warn that REQ/GLO quality may suffer? This is a recoverable situation that currently produces a silent, invisible degradation.

10. **Phase 1 state scan assumes output location is known.** Step 6 says "check existing Phase 1 artifacts at the configured output location" but the config loading step (Step 5) says the output location comes from "the `hbc` module section" of the config. If the config is missing or the `hbc` section is absent, the scan either fails or scans the wrong path. There is no fallback or user-facing signal.

---

## Headless Assessment

**Level: Partially adaptable.**

The core value of this agent is persona, state awareness, and workflow dispatch — all interactive by nature. However, a meaningful subset is automatable:

- Phase 1 state scan (Step 6) is deterministic and could return a JSON status object.
- Gate readiness check (all three core artifacts exist → suggest PG) is a yes/no derivation from file existence.
- Menu dispatch is trivially headless when the intent is pre-supplied.

**What a headless invocation would need:**

```
Input:  { "intent": "status" | "dispatch", "workflow_code": "REQ|GLO|BF|PG|TR" (if intent=dispatch) }
Return: { "status": "complete|blocked", "phase1_state": { "D-02": "exists|missing", "D-03": "exists|missing", "D-06": "exists|missing", "gate": "exists|missing" }, "next_recommended": "REQ|GLO|BF|PG|TR", "reason": "..." }
```

A `headless: true` activation path in `customize.toml` with a documented return schema would make this viable. The `intent: status` path requires no workflow dispatch — just state scan and return.

---

## Facilitative Patterns Check

| Pattern | Present | Notes |
|---|---|---|
| Open-floor opening | **Missing** | Agent jumps straight to menu. No invitation to dump context before structured Q&A. |
| Soft-gate elicitation | Partial | "After each workflow completes, return to menu" provides a natural transition but no "anything else before we move on?" |
| Intent-before-ingestion | Partial | Direct dispatch on named intent is good. But the state scan runs before intent is known — minor ordering issue. |
| Capture-don't-interrupt | Not applicable | No multi-turn discovery flow within the agent itself. |
| Dual-output | **Missing** | No distillate. When the agent returns to menu after [GLO] completes, it does not produce a token-efficient summary of D-03 terms to carry into the [REQ] or [BF] dispatch. The stated cross-artifact context carry has no mechanical backing. |
| Parallel review lenses | Not applicable | Agent is a coordinator, not a reviewer. |
| Three-mode architecture | Partial | HITL only. No headless path (see above). Guided mode is the only mode. |
| Graceful degradation | Partial | Script fallback on resolver failure is present and good. No fallback for missing project-context.md or missing config output location. |
| Decision-Log Workspace | Partial | Decision log exists for the skill build, not for user sessions. The agent has no session-level decision log to enable resume across conversations. |

**Highest value to add:** Open-floor opening and the headless status path. The open-floor opening would measurably improve the first-timer experience at near-zero cost. The headless path would unlock pipeline integration.

---

## Findings

### [HIGH] Missing open-floor opening before menu dispatch
**Location:** SKILL.md, Step 7: Greet and Present

**What:** The agent greets and immediately presents the menu with a recommendation. Users arriving with context — a project brief, a Confluence link, prior conversation notes — have no place to put it before the menu appears. This forces structure onto users who need to unload first.

**Suggestion:** Add a single line to Step 7: "If the user's initial message contains substantive context (a project description, a document path, a goals statement), acknowledge and absorb it before presenting the menu. Otherwise, after greeting, invite them to share what they're working with before proceeding to the menu." This is the open-floor opening pattern and costs almost nothing.

---

### [HIGH] No headless path for Phase 1 status query
**Location:** SKILL.md overall; customize.toml

**What:** The Phase 1 state scan is performed interactively and expressed as prose for the user. No machine-readable return exists. An orchestrator agent or CI process cannot query Phase 1 completeness programmatically. The principles describe the headless contract precisely; this agent has none.

**Suggestion:** Add a headless activation branch: if invoked with `{"mode": "headless", "intent": "status"}`, execute Steps 1, 5, and 6, then return `{"status": "complete|blocked", "phase1_state": {...}, "next_recommended": "...", "reason": "..."}` and exit. No persona adoption, no greeting, no menu. This is a 5-line addition to SKILL.md and one scalar in customize.toml.

---

### [HIGH] No resume protocol across sessions
**Location:** SKILL.md, Step 6 and Step 7

**What:** The agent scans artifact existence but does not surface "last touched" timestamps or offer a structured resume. A user returning after two weeks sees the same static status table they saw on day one. The decision-log workspace pattern says the resume path is "surface with `updated` timestamp and offer to resume" — this is absent.

**Suggestion:** In Step 6, when artifacts are found, also read their frontmatter `updated` field if present. In Step 7, if any artifact exists with a recent timestamp, surface it: "D-02 was last updated on [date] — pick up where we left off or start fresh?" One sentence; transforms the returning-user experience.

---

### [MEDIUM] Context carry has no mechanical backing
**Location:** SKILL.md, Menu Dispatch section

**What:** "Carry domain context forward — terms from GLO inform REQ review, requirements from REQ inform BF design" is stated as an aspiration but the mechanism is undefined. When the agent dispatches to [REQ] after [GLO] exists, does it pass a D-03 distillate? Does it load D-03 into context? Without instruction, the LLM will likely not do this unless the dispatched workflow skill itself loads D-03.

**Suggestion:** Add one sentence: "When dispatching to a workflow skill that has a predecessor artifact available (e.g., dispatching [REQ] when D-03 exists), note the predecessor path in the dispatch context so the workflow skill can load it." Alternatively, if the dispatched workflow skills already load their dependencies themselves, say so explicitly to prevent the agent from double-loading.

---

### [MEDIUM] Silent failure on missing project-context.md
**Location:** SKILL.md, Step 4: Load Persistent Facts; customize.toml persistent_facts

**What:** The `file:{project-root}/**/project-context.md` glob silently resolves to nothing if the file doesn't exist. The agent proceeds without foundational context, and the user gets no signal that requirements quality may be compromised.

**Suggestion:** Add to Step 4: "If no `project-context.md` is found, note the gap and ask the user to provide a brief project summary before proceeding, or acknowledge that responses will be less project-specific."

---

### [MEDIUM] Description trigger phrase "phân tích" is too broad
**Location:** SKILL.md frontmatter, description field

**What:** "phân tích" is Vietnamese for "analyze" — a general-purpose word. Any analytical task in a Vietnamese-language session could inadvertently activate this agent. This matches the quality principles warning against descriptions that "hijack unrelated conversations."

**Suggestion:** Tighten to more specific phrases: `'phân tích yêu cầu'` (requirements analysis), `'phân tích nghiệp vụ'` (business analysis), or `'giai đoạn 1'` (Phase 1). Keep "phân tích" only if organic triggering on any analysis task is actually desired.

---

### [MEDIUM] No explicit redirect for confused or wrong-place users
**Location:** SKILL.md, Menu Dispatch section

**What:** When no menu item fits the user's actual goal, the skill falls back to "just continue the conversation." There is no "this isn't the right agent for you" path, no suggestion of adjacent skills, and no clean persona dismissal offer.

**Suggestion:** Add one line: "If no menu item fits the user's stated goal, acknowledge the mismatch, suggest the appropriate adjacent skill or agent (e.g., bmad-agent-analyst for general analysis, hbc-phase-gate standalone for gate-only work), and offer to dismiss the BA persona."

---

### [LOW] Post-workflow return lacks artifact confirmation
**Location:** SKILL.md, Menu Dispatch section

**What:** "After each workflow completes, return to the menu with an updated status summary." The updated status summary is good, but there is no instruction to confirm what artifact was actually produced and where it landed. A user who ran [GLO] and sees the menu again may not know whether D-03 was written successfully.

**Suggestion:** When returning to menu after a workflow completes, lead with: "D-03 Glossary written to `[path]`" before the updated status table. This is a single sentence and closes the "where did my artifact go?" confusion loop.

---

### [LOW] "Activate step 8" ordering relative to greeting is unusual
**Location:** SKILL.md, Steps 7 and 8

**What:** Step 7 greets the user and presents the menu. Step 8 executes `activation_steps_append`. The user is presented with the menu before append steps run — if an append step modifies context or loads something relevant to the menu recommendation, it runs after the user has already seen potentially stale guidance.

**Suggestion:** Consider whether append steps belong before menu presentation (making their output available for the recommendation logic) or whether they are deliberately post-greeting hooks. Add a comment in customize.toml clarifying intent: "Use append steps for context-heavy setup that should complete before the user makes their first selection."

The current SKILL.md already has this comment in customize.toml but the ordering in SKILL.md has the user seeing the menu before append steps execute. Align the ordering, or clarify that append steps are fire-and-forget side effects that don't affect menu content.

---

## Top 3 Insights

**1. The agent lacks an entry ramp for context-rich arrivals.**
The most impactful single addition is the open-floor opening before menu dispatch. The entire activation flow assumes users arrive with nothing — but the typical BA session starts with "here's what happened in the stakeholder call." Absorbing that before forcing menu selection would make the agent feel like a collaborator rather than a form.

**2. The headless gap closes a pipeline integration door.**
Phase 1 state is deterministic file-presence information. An orchestrator agent, a pre-merge CI check, or a project dashboard could query it in seconds if a headless status path existed. Right now that door is locked. A 5-line addition would unlock it.

**3. Cross-artifact context carry is stated but unoperationalized.**
The design correctly identifies that GLO terms should inform REQ and REQ should inform BF — this is the core value of having a coordinator agent rather than standalone workflows. But the mechanism is undefined. Without explicit dispatch-time context passing or a clear statement that the dispatched workflows self-load their predecessors, this aspiration silently fails on every session that crosses workflows.
