# Enhancement Analysis — hbc-create-requirements

**Scanner:** enhancement-opportunities
**Skill:** `src/hbc-create-requirements`
**Date:** 2026-05-27 (T193000 run)
**Prior analysis:** `.analysis/2026-05-27T103000/enhancement-analysis.md`

---

## Delta from Prior Analysis

All three HIGH findings and seven of eight MEDIUM/LOW findings from the T103000 run are resolved in the current SKILL.md and references. The table below tracks disposition:

| Finding | Prior severity | Status |
|---------|---------------|--------|
| H1: No open-floor opening in Discovery | HIGH | **Resolved** — Stage 2 opens with explicit invitation |
| H2: Headless input contract missing | HIGH | **Resolved** — `headless-contract.md` has full Input Args table + example |
| H3: Decision-log path absent from headless return | HIGH | **Resolved** — `decision_log` field in return schema |
| M1: No soft-gate transitions in Discovery | MEDIUM | **Resolved** — Stage 2 soft-gate sentence added |
| M2: Parallel-lens menu unexplained | MEDIUM | **Resolved** — Stage 3 and 4 menus now have parenthetical descriptions |
| M3: No compaction flush at Stages 3-4 | MEDIUM | **Resolved** — Stages 3 and 4 both have explicit compaction flush notes |
| M4: No "import and convert" path for experts | MEDIUM | **Partially resolved** — Stage 2 detects pre-structured requirements and skips to gaps; no formal `import` arg, but the flow gap is addressed |
| M5: Capture-don't-interrupt for cross-artifact insights | MEDIUM | **Resolved** — Stage 2 silently captures glossary terms and business-flow processes for Stage 5 |
| L1: No graceful degradation when Python unavailable | LOW | **Resolved** — Stage 4 has LLM-only fallback with decision-log note |
| L2: Decision-log finalize audit missing | LOW | **Open** — Stage 5 still says "Append closing session" without an audit pass |
| L3: Smart defaults from project-context.md | LOW | **Resolved** — Stage 2 pre-populates from project-context.md |

One prior medium finding had a secondary dimension that remains open — the headless return does not itemize auto-fix changes (the auto-fix changelog). Noted below as a new finding.

---

## Skill Understanding

Generates a D-02 Requirements Specification document with unique REQ-xxx IDs, scope boundaries, user roles, functional and non-functional requirements. Primary user is a BA or PM running Phase 1 Analysis of an HBC project. Key assumption: the user has source material and wants structured, traceable requirements that feed downstream artifacts (glossary, business flows, traceability matrix). Headless mode is declared and now has a complete input/output contract.

---

## User Journeys

### The First-Timer

**Narrative:** User invokes on a new project with only a vague idea and no documents. They don't know what REQ IDs are.

**Friction points:**
- The open-floor opening in Stage 2 now handles this well — "share everything you have" replaces the interrogation pattern.
- The soft-gate transitions prevent the user from being rushed through discovery areas they need more time on.
- **Remaining gap:** Stage 1c ("If wrong skill, suggest the right one") still doesn't name specific sibling skills. A first-timer routed to the wrong skill gets a generic suggestion. Impact is low — the prompt context usually resolves this — but it remains a missed opportunity.

**Bright spots:**
- Resume detection + decision-log workspace means a first-timer who stops halfway can pick up exactly where they left off.
- Stage 5 handoff now names specific next skills (`hbc-create-glossary [GLO]`, `hbc-create-business-flow-diagram [BF]`, `hbc-phase-gate [PG]`), teaching the workflow.
- Smart defaults from `project-context.md` eliminate redundant re-asking of basic facts.

### The Expert

**Narrative:** Senior BA with 30 structured requirements already drafted in a spreadsheet.

**Friction points:**
- Stage 2 now detects structured requirements in source documents and skips to gaps — this is the right behavior for this user. No formal `import` arg, but the smart detection is sufficient for interactive use.
- The expert still needs to enter Stage 2 before the detection kicks in. A quick-win mode that bypasses the open-floor invitation when structured requirements are detected would be cleaner, but this is a low-priority refinement.

**Bright spots:**
- The parallel-lens menu (`[A]/[P]/[C]`) with explanations now lets the expert choose exactly the review depth they want.
- Validation is the expert's fastest path to quality; the script delivers deterministic, fast, actionable output.

### The Confused User (Wrong Skill)

**Narrative:** User says "requirements" but means "set up my project" or "write a PRD."

**Friction points:**
- **Stage 1c still generic.** The intent gate works but says "suggest the right one" without specifying which skills to name. Given the HBC module context, the sibling skills are `hbc-create-prd` and `hbc-brainstorming`. Naming them would make this gate useful rather than advisory.

**Bright spots:**
- The intent gate still exists and fires before any discovery work begins — the user doesn't waste time on stage 2.

### The Edge-Case User

**Narrative:** 200+ requirements across subsystems; or output language is English.

**Friction points:**
- **Language mismatch is still present.** `validate-requirements.py` hardcodes Japanese section names in `REQUIRED_SECTIONS`. An English D-02 will show all sections as missing. This is a functional gap, but it lives in the script and belongs primarily to the determinism scanner. Flagged here for completeness.
- REQ ID ceiling (REQ-999+) works correctly — the regex handles 3+ digits, and the format string only produces shorter IDs for sequential numbering. Non-issue.

**Bright spots:**
- Bilingual template (Japanese headers + English parentheticals) handles the common case of mixed-language projects.

### The Hostile Environment

**Narrative:** Python not available; no `project-context.md`; context compaction mid-flow.

**Friction points:**
- Python fallback is now in place — LLM-only validation with a decision-log note. Clean.
- Compaction coverage is now complete across all three flush points (Stage 2, Stage 3, Stage 4).
- No `project-context.md`: Stage 2 pre-populates "where available" — implicitly handles absence. Clear enough.

**Bright spots:**
- The three-point compaction flush strategy (Stage 2: actor list + REQ count + scope; Stage 3: REQ count + scope + version; Stage 4: issue counts + auto-fixed) provides excellent compaction resilience.

### The Automator (Headless / Pipeline)

**Narrative:** Another agent or CI pipeline invokes with source documents expecting a D-02 without interaction.

**Friction points:**
- **Auto-fix changelog absent from return.** When the headless path applies 3 auto-fixable issues, the caller receives `auto_fixable_count: 3` but not what was fixed. The caller cannot audit silent modifications. This was noted in the prior analysis but not addressed in the headless contract update.
- **Blocked reason list is narrow.** The contract documents three reasons (`no_source_documents`, `validation_manual_fix`, `empty_discovery`). A fourth scenario is possible: scan-sources.py finds an existing complete D-02 but the caller passed `--mode create`. The current skill would enter Update mode, which is a behavior change the caller didn't expect. The contract should document this as a blocker or define the resolution.

**Bright spots:**
- Input schema is now complete: `--sources`, `--mode`, `--vague-terms` with example invocation.
- `decision_log` path in the return allows the caller to read all assumptions made during headless execution.
- `blocked` on `empty_discovery` gives a clear, actionable failure mode.

---

## Headless Assessment

**Level: Headless-Ready**

The skill has crossed the threshold from "Easily Adaptable" (prior assessment) to headless-ready. All interaction points can now be auto-resolved:

| Interaction Point | Current Status |
|---|---|
| Stage 1a (Resume/Update routing) | Resolved via scan-sources.py state detection |
| Stage 1b (Source inventory) | `--sources` arg required; blocked if none provided |
| Stage 2 (Discovery) | Extracted from source documents; `empty_discovery` blocked |
| Stage 3 (Parallel-lens menu) | Skipped in headless — always continue |
| Stage 4 (Fix loop) | Auto-fix applied; `blocked` on manual-fix |

**Remaining gap:** Auto-fix changelog not returned. Medium-priority addition to the return schema.

---

## Facilitative Patterns Check

| Pattern | Prior Status | Current Status |
|---|---|---|
| **Open-floor opening** | Absent | **Present** — Stage 2 explicitly invites full brain-dump before structured elicitation |
| **Soft-gate elicitation** | Absent | **Present** — Stage 2 has soft-gate sentence at each area boundary |
| **Intent-before-ingestion** | Present | Present — unchanged |
| **Capture-don't-interrupt** | Absent | **Present** — Stage 2 silently captures glossary terms and business-flow processes |
| **Dual-output** | Absent | Still absent — low value here; D-02 is already structured for LLM consumption |
| **Parallel review lenses** | Present | Present — menu now explained |
| **Three-mode architecture** | Partially present | Present — Guided, Headless; Yolo/quick still absent but lower value for this skill |
| **Graceful degradation** | Absent | **Present** — Python fallback; subagent fallback not explicit |
| **Decision-Log Workspace** | Partially present | **Complete** — flush at Stages 2, 3, 4; only finalize audit still missing |

---

## Findings

### MEDIUM-OPPORTUNITY

**M1. Auto-fix changelog absent from headless return**
*Location:* `references/headless-contract.md`, return schema
*Noticed:* When headless mode auto-fixes REQ ID duplicates, gaps, or ordering issues, the `auto_fixable_count` in the return says how many were fixed but not what was changed. A pipeline comparing expected IDs to the output can be surprised by silent renumbering.
*Suggestion:* Add `"auto_fixes": [{"type": "REQ_ID_ORDER", "description": "Reordered REQ-003 and REQ-005"}]` to the return schema as an optional list, populated only when auto-fixes were applied.

**M2. Stage 1c names no specific sibling skills**
*Location:* SKILL.md, Stage 1c
*Noticed:* "If wrong skill, suggest the right one" is the current text. The HBC module's sibling skills are known and stable. Without names, the LLM improvises, which usually works but occasionally suggests non-existent skills.
*Suggestion:* Specify: "If user wants a product brief or PRD, suggest `hbc-create-prd`. If they want exploratory idea generation, suggest `hbc-brainstorming`. If they want project setup, suggest `hbc-project-setup`."

**M3. Unexpected mode collision in headless not documented**
*Location:* `references/headless-contract.md`, Blocked Reasons
*Noticed:* If `--mode create` is passed but a complete D-02 already exists, scan-sources.py returns `state: update`. The skill silently enters Update mode. The automator expecting a fresh Create gets unexpected behavior with no documented resolution.
*Suggestion:* Add a fourth blocked reason: `"mode_conflict"` — "existing complete D-02 found but `--mode create` was specified. Pass `--mode update` to revise or delete the existing D-02 to create fresh."

### LOW-OPPORTUNITY

**L1. Decision-log finalize audit still absent**
*Location:* SKILL.md, Stage 5
*Noticed:* Stage 5 says "Append closing session to decision log" but the Decision-Log Workspace pattern requires a finalize audit — every meaningful decision-log entry confirmed against the primary artifact, addendum, or explicitly set aside. This step ensures the user ends the session with a shared accounting rather than a one-sided delivery.
*Suggestion:* Add to Stage 5: "Before closing, audit decision-log entries against the D-02 — confirm every logged decision is reflected in the document, captured in the addendum, or explicitly set aside as process noise."

**L2. Graceful degradation for unavailable subagents not specified**
*Location:* SKILL.md, Stages 3 and 4 (parallel-lens menu)
*Noticed:* The quality principles require that subagent-dependent features fall back to sequential when subagents are unavailable. The parallel-lens options (`[P]` Party Mode, `[A]` Advanced Elicitation) depend on subagents. No fallback is specified.
*Suggestion:* Add a note to the parallel-lens menu descriptions: "If subagents are unavailable, apply the lens perspective directly in the current conversation rather than delegating."

**L3. Script hardcodes Japanese section names; English output fails validation**
*Location:* `scripts/validate-requirements.py`, `REQUIRED_SECTIONS`
*Noticed:* `REQUIRED_SECTIONS` contains hardcoded Japanese strings. Any D-02 generated with `document_output_language = English` will report all required sections as missing. This is a functional gap for non-Japanese projects using this skill.
*Suggestion:* Make `REQUIRED_SECTIONS` language-aware, or add `--language` arg that selects the appropriate section name set. Alternatively, match against both Japanese and English section names by default (the template uses bilingual headers, so the English parenthetical form is available).

---

## Top Insights

1. **The skill has gone from B+ to A- since the T103000 run.** All three high findings and the most visible medium findings are resolved. The facilitative patterns are now all present or deliberately absent. The headless contract is complete enough to use in a pipeline today.

2. **One meaningful headless gap remains: the auto-fix changelog.** The return contract tells the caller *how many* things were silently fixed but not *what* was fixed. For a pipeline that does traceability downstream (the traceability matrix depends on stable REQ IDs), silent renumbering without a changelog is an audit blind spot. This is the single addition that would make headless mode fully trustworthy for automated use.

3. **The script's Japanese-only section matching is a latent bug for non-Japanese deployments.** It doesn't affect the primary use case (Japanese/English bilingual projects), but it would cause confusing false failures for any team deploying this skill in a pure-English context. Worth addressing in the next script revision alongside other deterministic fixes.
