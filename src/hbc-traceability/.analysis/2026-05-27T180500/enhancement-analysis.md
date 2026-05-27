# Enhancement Analysis — hbc-traceability

**Scanner:** enhancement-opportunities
**Date:** 2026-05-27
**Skill path:** src/hbc-traceability

---

## Skill Understanding

Living traceability matrix manager for HBC waterfall lifecycle. Four capabilities — Initialize, Update, Report, Audit — maintain a seven-column markdown table mapping requirements through design, implementation, and testing phases. Primary users are BAs who initialize the matrix from D-02, architects and developers who populate design/code references, and QA engineers who cross-reference test specs and run audits. Key assumption: the project follows the HBC phased delivery structure with artifacts at known paths (`_hbc_output/plan/D-02-*`, `_hbc_output/design/D-19-*`, `_hbc_output/design/D-27-*`).

**Context note:** This is a second-pass scan (first scan: 2026-05-26T173617). The current SKILL.md (107 lines) has been substantially revised since the first scan (161 lines). Several HIGH and MEDIUM findings from the first scan have been resolved: `## On Complete` / exit hook removed, On Activation collapsed to outcome language, headless JSON schema reduced to prose description, and per the current SKILL.md the runtime `.trace-decisions.md` file was added to Update. Findings below focus on remaining gaps and new opportunities identified from the revised state.

---

## User Journeys

### The First-Timer (BA after Phase 1 gate)

**Narrative:** BA runs `traceability init` for the first time. D-02 exists at the standard path.

**Friction points:**
- If D-02 uses a non-standard ID format (`RQ-01`, `FR-001`), `extract-trace-ids.py` returns `NO_MATCHES` status. SKILL.md still hardcodes the regex pattern in the Initialize script invocation (`--pattern "REQ-\d{3,}"`). There is no `req_id_pattern` scalar in `customize.toml` — a team must modify the SKILL.md directly or override the script call, neither of which is a supported BMad customization path.
- No mention of what happens if the D-02 glob finds zero files. The script returns `NO_FILES` and exits 1. The SKILL.md does not tell the LLM to help the user locate the document or suggest running `hbc-create-prd` first to generate it.

**Bright spots:**
- The "Initialized matrix with {count} requirements. Next: run Phase 1 gate, then update after Phase 2" report text is clear and actionable — a first-timer knows exactly what comes next.

### The Expert (Dev mid-Phase 3, repeat user)

**Narrative:** Developer runs `traceability update` for the third time this sprint, doing incremental code_ref population after each PR merge.

**Friction points:**
- `source_code_path` is empty by default and asks interactively if unset. The expert who runs Phase 3 Update repeatedly gets prompted every session. The skill does not hint that setting `source_code_path` in `customize.toml` would eliminate the prompt. One sentence — "Tip: set `source_code_path` in `_bmad/custom/hbc-traceability.toml` to skip this prompt." — would reduce repeated friction with zero implementation cost.
- The Update diff output at the end ("Updated code_ref. Coverage: X/Y requirements now have code_ref populated") tells aggregate numbers but not which REQs changed. A dev doing incremental updates wants to see "These 5 REQs got code_ref this run" to verify their PR covered what they expected.

**Bright spots:**
- Phase detection from column fill state (via `--detect-phase` script flag) is genuinely useful for the expert who just wants to run an update without knowing which phase they're in.
- The `.trace-decisions.md` runtime log (added in this revision) gives the expert an artifact they can include in PR descriptions: "mapping rationale on file."

### The Confused User (triggered by "trace" in unrelated context)

**Narrative:** User asks Claude to "trace through this function's call stack" during debugging. The skill activates because "trace" appears.

**Friction points:**
- The description trigger phrases are `'traceability'`, `'ma trận'`, `'truy vết'`, and `agent menu [TR]`. The word "traceability" is unlikely to appear in a debugging session — so the confusion scenario is low probability. However, "truy vết" in Vietnamese colloquially means "to trace/track" and could appear in non-HBC contexts. This is a minor risk, acceptable given the domain.
- If triggered by accident with no matrix initialized and no D-02 artifacts present, the user hits a capability question then an empty result. The skill does not detect "this looks like a non-HBC project" early and offer a graceful exit.

**Bright spots:**
- `[TR]` agent menu code is unambiguous for intentional invocation — the main protection against accidental activation.

### The Edge-Case User (non-standard artifact paths)

**Narrative:** Team stores D-02 in `_hbc_output/requirements/` instead of `_hbc_output/plan/`, or uses a different deliverable numbering convention.

**Friction points:**
- All artifact glob paths are hardcoded in SKILL.md: `{project-root}/_hbc_output/plan/D-02-*`, `{project-root}/_hbc_output/design/D-27-*`, `{project-root}/_hbc_output/design/D-19-*`, `{project-root}/_hbc_output/gates/phase-*-gate.md`. These paths appear in script invocations and prose descriptions. None are exposed as `customize.toml` scalars.
- This was flagged as a MEDIUM finding in the first scan and remains unaddressed in the current revision. The gap matters because HBC module artifacts (D-02, D-19, D-27) are created by other skills with their own configurable output paths. If any upstream skill overrides its output path, this skill silently finds nothing.
- Similarly, the `REQ-\d{3,}` and `TC-\d{3,}` regex patterns are hardcoded. A team using `TC-\d{2,}` (two-digit test case IDs) or `FR-\d{3,}` for functional requirements would get zero extractions.

**Bright spots:**
- `matrix_path` and `matrix_template` are already exposed as customize.toml scalars. The pattern is established — extending it to artifact paths is consistent with what's already there.

### The Hostile Environment (compaction during Update)

**Narrative:** Long Phase 2 Update (30+ REQs to map) gets context-compacted mid-way through LLM mapping of design entities.

**Friction points:**
- The first scan's MEDIUM finding about compaction recovery was partially addressed: the current Update section now checks for `{project-root}/_hbc_output/traceability/.trace-state.json` and surfaces interrupted updates. This is good.
- However, the recovery path on "Resume or restart?" is unspecified. If the user says "resume," what does the agent do? The matrix may have been partially written (some rows updated, others not). The `.trace-state.json` records `update_in_progress` and `phase` but not which rows were already written. A resumed update might re-process already-mapped rows, generating duplicate decisions log entries or overwriting mappings that were correct.
- The SKILL.md says "restart automatically" in headless mode for interrupted updates. This means headless will silently discard any partial work and start fresh — correct behavior, but the calling agent gets no signal that a restart happened vs. a clean run. The headless JSON return does not include a `restarted: true` flag.

**Bright spots:**
- The `.trace-state.json` state marker pattern is cheap and recoverable — surface is visible, disk-resident, and survives compaction.

### The Automator (phase gate calling traceability headless)

**Narrative:** `hbc-phase-gate` invokes `traceability report --headless` after a gate passes to embed coverage stats in the gate report.

**Friction points:**
- The headless return is now described as prose ("Return JSON with `status`, `capability`, `matrix_path`, and summary stats. On `blocked`, include `reason`.") rather than a fenced JSON schema. The calling skill (`hbc-phase-gate`) cannot predict the exact JSON shape without running it. A distillate or example in the Headless Mode section would help integrators.
- `trace-report.py` still exits 1 when gaps exist (line 200 in the script: `sys.exit(1 if args.strict and result.get("gaps") else 0)`). Checking the code: `--strict` is required to exit 1 on gaps; without `--strict`, the exit is 0. This was the first scan's headless concern, and it is **already fixed** — exit 1 only when `--strict` is passed. The headless mode in SKILL.md does not use `--strict`, so the automator gets correct exit codes. This finding from the first scan was resolved in the scripts.
- However, the headless JSON return schema does not include a `decision_log` path. BMad headless convention says on non-trivial operations the log path should be in the return. Phase 2/3 Update in headless mode writes to `.trace-decisions.md` — the caller cannot find this without knowing the convention.

**Bright spots:**
- Headless mode is declared as first-class from day one, with a dedicated `## Headless Mode` section. Capability requirement on headless is clear.
- The `status: complete | blocked` convention is present in the headless description.

---

## Headless Assessment

**Level: Easily Adaptable** — core flow works headless today; 2 interaction points need attention.

**Interaction points that could auto-resolve:**
1. Capability determination — already required in headless. Resolved.
2. Phase 2/3 confirmation — skipped in headless per SKILL.md. Resolved.
3. Source code path prompt (Phase 3) — will block headless if `source_code_path` is unconfigured. This is the one interaction point that could silently block a headless caller with no clear signal.
4. "Resume or restart?" on interrupted update — automatically restarts in headless. Resolved, but no signal to caller that a restart occurred.

**What a headless invocation needs (current gaps):**
- `source_code_path` pre-configured in `customize.toml` for Phase 3 Update; or passed as a runtime arg
- `decision_log` path in JSON return for Update operations (so caller can surface rationale trail)
- `restarted: true` flag in JSON return when an interrupted update was discarded and restarted

---

## Facilitative Patterns Check

| Pattern | Present? | Assessment |
|---------|----------|------------|
| Open-floor opening | N/A | Utility skill — not applicable |
| Soft-gate elicitation | **Yes (added)** | Phase 2/3 Update now presents proposed mappings as a table and confirms before writing. The first scan's key missing item is now present. |
| Intent-before-ingestion | Partial | Capability inference checks context before acting; no explicit "is this a traceability question or something else?" check for confused activations |
| Capture-don't-interrupt | N/A | No discovery flow |
| Dual-output | Partial | `.trace-decisions.md` is the distillate for mapping rationale. But the matrix itself has no paired `.matrix-summary.json` for downstream skills to consume coverage stats without invoking Report. The Audit capability still requires invoking the skill explicitly. |
| Parallel review lenses | N/A | Not applicable for this utility |
| Three-mode architecture | Partial | Interactive + headless. No yolo mode. For a utility skill this is acceptable — yolo would just mean skipping mapping confirmation, which the current headless mode effectively provides. |
| Graceful degradation | Partial | `.trace-state.json` for interrupted updates is new. Python unavailability still has no fallback. |
| Decision-Log Workspace | **Partially addressed** | `.trace-decisions.md` captures runtime mapping rationales. Build-time `.decision-log.md` is still in `references/` as skill design history. The two logs serve distinct purposes and should remain separate — this is correct. |

---

## Findings

### HIGH-OPPORTUNITY: Artifact paths and ID patterns not customizable

**Location:** SKILL.md, Initialize (line 47), Update Phase 2 (line 62), Update Phase 3 (line 64), Update Phase 4 (line 66)

**Observation:** All four D-xx artifact glob paths and both regex patterns (`REQ-\d{3,}`, `TC-\d{3,}`) are hardcoded in SKILL.md. This was flagged as MEDIUM in the first scan and remains unresolved. It has elevated since then because the Update section now also hardcodes the D-19 and D-27 paths in the phase 2 script invocation. A team that deviates from standard HBC artifact paths cannot use this skill without editing SKILL.md directly — which is an unsupported BMad customization path.

**Cross-skill risk:** `hbc-create-prd` and `hbc-create-test-spec` each have their own configurable `output_path` scalars. If those output paths are overridden, this skill cannot find the artifacts it needs. The integration is silently fragile.

**Suggestion:** Add `customize.toml` scalars: `requirements_glob` (default: `{project-root}/_hbc_output/plan/D-02-*`), `design_glob` (default: `{project-root}/_hbc_output/design/D-19-*`), `test_spec_glob` (default: `{project-root}/_hbc_output/design/D-27-*`), `gates_glob` (default: `{project-root}/_hbc_output/gates/phase-*-gate.md`), `req_id_pattern` (default: `REQ-\d{3,}`), `test_case_pattern` (default: `TC-\d{3,}`). Reference in SKILL.md as `{workflow.requirements_glob}` etc. Four-line change to customize.toml; minor updates to four SKILL.md script invocations. Preserves zero-config behavior for standard HBC projects, unlocks customization for non-standard ones.

### MEDIUM-OPPORTUNITY: Resume path on interrupted Update is unspecified

**Location:** SKILL.md, Update capability (line 58)

**Observation:** The Update section checks for `.trace-state.json` and asks "Resume or restart?" — but the resume path is not described. If the user says "resume," the agent has no instruction on how to determine which rows were already processed vs. still empty, whether to re-run LLM mapping for partially-mapped REQs, or how to avoid duplicate decision-log entries. In practice, the agent will likely restart anyway because resume is hard to implement without more state. The user is given a choice that has only one meaningful path.

**Suggestion:** Either specify the resume behavior explicitly — "Resume: re-run LLM mapping only for rows where the target column is still empty; skip rows already populated" — or remove the choice and always restart with a note: "Restarting interrupted update. Previously written mappings are preserved; this run will fill any remaining empty cells." The latter is simpler and achieves the same result without an ambiguous prompt.

### MEDIUM-OPPORTUNITY: Update diff shows aggregate but not per-REQ changes

**Location:** SKILL.md, Update capability (line 70)

**Observation:** The Update report output states "Updated {column}. Coverage: {X}/{Y} requirements now have {column} populated. Next: run `hbc-phase-gate`..." This aggregate summary is useful but does not tell the user which REQs received new mappings this session. For developers running incremental Phase 3 updates (one PR at a time), knowing exactly which REQs got code_ref added is the primary validation that their PR covered what was expected.

**Suggestion:** After writing the matrix, run a brief diff: list which REQs received new mappings this session, and any mappings that changed if Update was re-run. The `.trace-state.json` already records `update_in_progress` and `phase` — a simple approach would be to snapshot the filled-column state before and after and diff the two. One instruction line: "Report with diff: list which REQs received new mappings this session, and any mappings that changed (if re-running Update)." Already present in the prose of Update but not as an explicit instruction — make it explicit.

**Note:** Re-reading the current SKILL.md line 70: "Report with diff: list which REQs received new mappings this session, and any mappings that changed (if re-running Update)." This is already in the SKILL.md. The diff instruction exists. However it's phrased as a desired output without specifying the mechanism — the LLM has no state snapshot to diff against unless it remembers what the matrix looked like before the Update started. An explicit "read the matrix before starting, compare after writing" instruction would make this reliable rather than aspirational.

### MEDIUM-OPPORTUNITY: `decision_log` path missing from headless return

**Location:** SKILL.md, Headless Mode (line 27)

**Observation:** BMad headless convention specifies the JSON return includes the `decision_log` path so callers have an audit trail. Phase 2 and Phase 3 Updates write to `.trace-decisions.md` — this path is not included in the headless return. A calling skill (`hbc-phase-gate`) that wants to attach mapping rationale to the gate report has no way to find the decisions file from the JSON return alone.

**Suggestion:** Add `decision_log` to the headless return description: "Return JSON with `status`, `capability`, `matrix_path`, `decision_log` (path to `.trace-decisions.md`, present when Update capability writes new entries), and summary stats." One-line addition to the Headless Mode section.

### LOW-OPPORTUNITY: Tip for `source_code_path` not surfaced at friction point

**Location:** SKILL.md, Update Phase 3 (line 64)

**Observation:** Phase 3 asks for source code root interactively when `source_code_path` is empty. For a user who runs this repeatedly, the repeated prompt is friction. The skill has a `source_code_path` scalar in `customize.toml` specifically for this, but the skill never hints that configuring it would eliminate the prompt.

**Suggestion:** After the interactive prompt, add a one-line hint: "Tip: set `source_code_path` in `_bmad/custom/hbc-traceability.toml` to skip this prompt in future sessions." Cost: one sentence. Benefit: self-documenting skill for repeat users.

### LOW-OPPORTUNITY: Initialize has no "D-02 not found" guidance

**Location:** SKILL.md, Initialize (lines 44-54)

**Observation:** If `extract-trace-ids.py` returns `NO_FILES` (D-02 glob matches nothing), the script exits 1. SKILL.md gives no instruction for what to tell the user. The LLM will likely improvise, but "go run `hbc-create-prd` first" is a specific, actionable next step that only an HBC-aware skill would know to suggest.

**Suggestion:** Add a one-line fallback: "If script returns `NO_FILES`, suggest running `hbc-create-prd` to generate D-02 first." Matches the Audit capability's pattern of recommending adjacent skills for specific gaps.

---

## Top 3 Insights

1. **Artifact paths as customize.toml scalars is the single highest-ROI change.** The skill's cross-skill integration story depends on finding upstream artifacts. With `requirements_glob`, `design_glob`, `test_spec_glob` configurable, teams with non-standard paths get full value; and future changes to upstream skill output paths can be reconciled without touching SKILL.md. The pattern is already established (`matrix_path`, `source_code_path`) — this is extension, not invention.

2. **The resume vs. restart prompt is a false choice that creates confusion.** Giving users an option with only one implementable path ("resume" without row-level state tracking is effectively "restart") is worse than making the right decision for them. The interrupted-update detection is valuable; the ambiguous recovery prompt undermines it. Pick one path and make it explicit.

3. **The diff output in Update is already specified but relies on LLM memory rather than explicit state.** "Report with diff" works if the LLM remembers the pre-Update matrix state. In a long Update with compaction risk, that memory may not persist. A two-line instruction to "read and snapshot filled-column state before starting, compare to post-Update state when reporting" would make the diff reliable across sessions.
