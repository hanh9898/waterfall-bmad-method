# Enhancement Analysis: hbc-phase-gate

## Skill Understanding

**hbc-phase-gate** is a deterministic quality gate engine for the HBC Waterfall-TDD lifecycle. It evaluates four sequential project phases (Analysis, Design, Implementation, Testing) against bundled checklists with four evaluation types (FILE, CONTENT, METRIC, QUALITY), producing a gate report with PASSED/FAILED/WARNING status. The skill now supports headless invocation, delta tracking across re-evaluations, and per-failure skill remediation suggestions.

**Primary user:** Phase reviewers (architects, QA leads, dev leads) invoking from agent context menus. **Key assumptions:** Projects follow HBC artifact conventions (`_hbc_output/` paths), `_bmad/config.yaml` is configured, and the phase inferred from agent context is correct.

---

## Evolution Note (Relative to Previous Analysis)

The previous analysis (2026-05-26T160200) identified four high-opportunity gaps: re-evaluation transparency, artifact discovery, headless mode, and QUALITY parallel review. The current SKILL.md has addressed the first three substantially:

- **Headless mode** — fully documented with JSON schema and `--headless` flag.
- **Delta tracking** — `prior_results` map, session-by-session gate log, fixed/regressed/new/unchanged columns.
- **Artifact discovery** — `find {project-root} -name "*{artifact_keyword}*"` fallback on FILE failures plus `skill_to_create` → skill suggestion chain.
- **Quantified QUALITY evidence** — instruction to cite specific counts, IDs, and gaps (not vague prose).

Remaining gaps and new observations are below.

---

## User Journey Analysis

### Archetype 1: The Gatekeeper (Phase Reviewer Re-running After Fixes)

**Context:** Architect re-runs gate on Phase 2 after developers fixed three failures.

**Journey:**
1. Invokes gate — phase 2 inferred from context, confirmed (`"Proceed?"` prompt).
2. Script evaluates FILE/CONTENT/METRIC. LLM evaluates QUALITY items.
3. Delta report surfaces: "2 fixed, 1 still failing, 0 regressed."
4. Regression column: `PASS→FAIL` is highlighted prominently.

**Friction points:**
- **Gate log is append-only but the format is defined inline in SKILL.md** — each entry is a markdown table with `| {timestamp} — {overall_status} |` as a heading. This is good, but if a gate has 10 items and is run 5 times, the log file becomes a 50-row table-per-session structure. There is no instruction to add a session-level summary line at the top (like a changelog header) to help someone scanning the log for "did we ever PASS this phase?"
- **The `on_complete` hook fires on FAILED results** — the skill says "if `{workflow.on_complete}` is non-empty, treat it as a skill invocation and execute it." No condition on `status`. If a team configures `on_complete = "invoke hbc-traceability"`, that hook fires even when the gate fails, which can cause unintended side effects (traceability update on a gate that blocked progression).

**Bright spots:**
- Delta summary is a genuinely useful addition.
- "Regressions prominently highlighted" is a good instruction.

---

### Archetype 2: The First-Timer (Builder Unfamiliar with HBC)

**Context:** New developer runs gate on Phase 3 after finishing implementation.

**Journey:**
1. Invokes gate; phase inferred from dev context → phase 3.
2. Confirmed with `"Inferred phase 3 (Implementation) from Dev context. Proceed?"` — good.
3. Report: P3-03 (coverage) fails (no `coverage-report*` file at all).
4. `find` fallback runs — no near-matches found anywhere.
5. Report says: "No files matching ... No files found for broader search."
6. P3-04 (unit tests passing) — script returns `PENDING_LLM`. LLM is told "If no test results artifact exists, ask user to run tests and provide results."

**Friction points:**
- **P3-03 and P3-04 assume artifacts exist as files.** Many projects generate coverage and test results on-the-fly (not persisted to `_hbc_output/impl/`). The first-timer has run the tests — they passed — but never exported results to a file. The gate fails two required items with no useful path forward beyond "create the file." The skill doesn't say how to generate a coverage report artifact.
- **No suggestion for how to create the expected output artifacts** (unlike FILE failures on document skills, where `skill_to_create` is populated). P3-01 (`hbc-create-task-breakdown`) and P3-03/P3-04 have no `skill_to_create` — the checklist is blank. So the builder sees failures with no skill suggestion.
- **P3-04's QUALITY fallback** — "ask user to run tests and provide results" is an inline pause in evaluation. In a checklist with 6 items, this interrupts the flow. The skill doesn't say whether to stop and wait for user input or continue evaluating other items and circle back.

**Bright spots:**
- Phase confirmation prompt is present and helpful.
- `find` fallback for near-miss discovery is a real improvement.

---

### Archetype 3: The Automator (Headless Pipeline Agent)

**Context:** A sprint-planning skill invokes gate headlessly before auto-assigning next-phase tasks.

**Journey:**
1. Invokes with `--headless`, `phase=2`.
2. JSON return includes `delta` field: `{"fixed": [...], "regressed": [], "new": [...], "unchanged": [...]}`.
3. Caller parses `status` and `required_failed` fields.

**Friction points:**
- **`pending_llm` count in headless JSON is declared but behavior is unclear.** The schema shows `"pending_llm": 1` in the summary. In headless mode, QUALITY items still need LLM judgment. Does the skill evaluate QUALITY items headlessly (LLM judges without user interaction — fine) or skip them (marking as PENDING_LLM, leaving them unevaluated)? SKILL.md says "Skip all user-facing output" and "return a single JSON block" but doesn't say what happens to QUALITY evaluation itself. If QUALITY items are skipped, `required_failed` may undercount failures. If evaluated, the caller's `status` may be FAILED when QUALITY judgment would have been PASS.
- **`delta.new` vs `delta.unchanged` semantics** — SKILL.md says "NEW (first evaluation)" for items with no prior result. But on the very first ever run of a gate (no prior gate report), every item is `NEW`. The headless caller gets back a delta with all items in `new`, which looks confusing (not a change signal at all).
- **`log_path` in headless return** — the JSON schema includes `log_path` but SKILL.md describes the log as the delta table. If the caller reads `log_path`, they get the session table, not the full decision context. For headless audit purposes, this is fine — but calling it `log_path` may mislead callers expecting a full decision log.

**Bright spots:**
- Structured JSON schema is clear and well-formed.
- `required_failed` array (not just count) lets callers act on specific items.
- `gate_mode` in return is correctly surfaced.

---

### Archetype 4: The Edge-Case User (Non-Standard Artifact Paths)

**Context:** Team stores design artifacts in `docs/design/` instead of `_hbc_output/design/`.

**Journey:**
1. Gate runs; all FILE checks fail (wrong paths).
2. `find` fallback finds D-19 at `docs/design/D-19-database-design.md`.
3. Report evidence: "No files matching `{project-root}/_hbc_output/design/D-19-*`. Near-match found: `docs/design/D-19-database-design.md`."
4. User realizes they need to override checklist paths.
5. User reads customize.toml: `phase_2_checklist = "assets/phase-2-gate-checklist.md"`. They can replace it with a custom checklist file. But editing the checklist means recreating the whole table.

**Friction points:**
- **No per-item path override.** The team's entire checklist is correct except for the path prefix. Their only option is to fork the entire checklist file and change every artifact path. The customize.toml scalar `phase_N_checklist` is the right mechanism but is coarse (whole-file override, not item-level).
- **The `find` fallback only informs — it doesn't offer to temporarily use the discovered path.** The gate still fails. It says "near-match found" but doesn't ask "should I evaluate using this path instead?" even in interactive mode. Missing the opportunity to use the discovery productively.

**Bright spots:**
- `find` fallback narrows the diagnostic gap significantly over the previous version.
- `customize.toml` path override at the checklist level is documented.

---

### Archetype 5: The Confused User (Wrong Phase / Wrong Skill)

**Context:** BA invokes gate mid-analysis thinking it will tell them what's left to do (not a go/no-go check).

**Journey:**
1. BA says "check our analysis phase" — gate infers phase 1, confirms, evaluates.
2. Report: P1-06 FAILED (requirements not traceable to business flows), P1-07 optional FAILED.
3. BA expected a "what do I still need to do" list. Instead gets "you FAILED" with an artifact gap list.
4. BA is demoralized or confused about what the gate is for.

**Friction points:**
- **No framing of what the gate is for at report start.** The report template (`gate-report-template.md`) goes straight to Summary table. No sentence like "This is a phase progression check — PASSED means your artifacts meet the bar for moving to Phase 2." Users who invoke it by accident or with the wrong mental model get the raw verdict without context.
- **No link from gate to a "checklist preview" mode.** A read-only "what does phase gate 1 check?" query (without evaluating anything) would serve the confused user and the planner archetype without the overhead of a full evaluation run.

**Bright spots:**
- The overall status and gate mode are prominent at the top of the report.

---

## Headless Assessment

**Current level: Headless-ready** (newly implemented).

The headless path is documented with an explicit JSON schema, `--headless` flag, and `on_complete` hook preservation. The main gaps:

- **QUALITY item handling in headless mode is undefined** — needs one sentence clarifying whether QUALITY items are evaluated by LLM judgment (headlessly, no user prompts) or returned as `PENDING_LLM`. Recommendation: evaluate headlessly (LLM judges artifact content without user interaction) and include the result in the JSON. This is the most useful default for automation callers.
- **First-run delta semantics** — when no prior gate report exists, all items appear in `delta.new`. A headless caller should not interpret this as "everything changed." Suggest treating `new` items separately in downstream logic or adding a top-level `is_first_run: true` flag.
- **No `--dry-run` flag** — headless callers may want to test invocation without writing gate report to disk. Low-priority but worth noting.

**Headless invocation inputs needed:**
- `phase` (int, 1-4) — required
- `project_root` (path) — required (no fallback to cwd in headless)
- `coverage_threshold` (int, optional, falls back to config default)

**Return format:** well-defined in SKILL.md; add `is_first_run` bool to summary block.

---

## Facilitative Pattern Check

| Pattern | Present? | Assessment |
|---------|----------|------------|
| **Open-floor opening** | N/A | Deterministic engine, not a discovery workflow. Correctly absent. |
| **Soft-gate elicitation** | Partial | Phase confirmation prompt is present. No mid-report "anything else before I finalize?" but this is appropriate for an engine. |
| **Intent-before-ingestion** | Present | Phase inference + confirmation before scanning artifacts. Good. |
| **Capture-don't-interrupt** | N/A | Single-turn evaluation, not a multi-turn conversation. |
| **Dual-output** | Present | Gate report (human) + headless JSON (machine). Well-implemented. |
| **Parallel review lenses** | Absent | QUALITY items still single-evaluated. Previous analysis flagged this; it remains unaddressed. Would meaningfully improve confidence in high-stakes gates. |
| **Three-mode architecture** | Mostly present | Interactive + Headless implemented. "Guided" onboarding mode (for confused/first-timer) not present, but may not warrant full implementation. |
| **Graceful degradation** | Partial | `find` fallback for FILE failures. No fallback when `evaluate-gate-checklist.py` script fails (only "resolve manually" instruction without fallback output format). |
| **Decision-Log Workspace** | Partial | Gate log exists as append-only session delta table. But there is no formal workspace with a `decision-log.md` companion that survives compaction and enables proper resume. The gate log is a delta table, not a conversational decision record. |

### Most Valuable Missing Pattern

**Parallel review lenses for QUALITY items** is the highest-impact remaining gap. The skill explicitly instructs "Be strict — vague or incomplete artifacts fail" but a single-evaluator bias means:
- A lenient pass on P2-08 (test coverage completeness) can hide real coverage gaps.
- A harsh fail on P1-06 (traceability) can block a project that has good informal traceability not yet formalized.

Fanning out two lenses (skeptic + acceptance) for required QUALITY items, then PASSING only when both agree, would reduce both false positives and false negatives without heavy overhead.

---

## Findings

### High-Opportunity

#### H1: QUALITY Item Handling in Headless Mode Is Undefined
**Location:** SKILL.md § Headless Mode  
**Observed:** The headless JSON schema includes `pending_llm` in the summary, implying QUALITY items may be left unevaluated. But headless callers need a definitive `status` — a PASSED gate with unresolved QUALITY items is a false positive. The skill doesn't say whether LLM judgment runs headlessly or items are skipped.

**Suggestion:** Add one sentence to the Headless Mode section: "QUALITY items are evaluated headlessly using the same LLM judgment logic as interactive mode — no user prompts are issued. Evidence is embedded in the JSON result."

Remove `pending_llm` from the headless JSON schema (it would always be 0 in headless), or redefine it as "items awaiting human sign-off" if some QUALITY items are intentionally deferred.

**Impact:** Prevents automation callers from treating a PASSED gate (with unresolved QUALITY) as a true green light.

---

#### H2: `on_complete` Hook Fires Regardless of Gate Status
**Location:** SKILL.md § On Complete  
**Observed:** "If `{workflow.on_complete}` is non-empty, treat it as a skill invocation and execute it." No condition on `status`. A configured `on_complete` hook will fire after a FAILED gate evaluation, potentially triggering downstream workflows (e.g., traceability update, next-phase task assignment) on a failed gate.

**Suggestion:** Gate the hook on status: "If `{workflow.on_complete}` is non-empty and the gate status is PASSED, treat it as a skill invocation and execute it. For FAILED or WARNING, present it as a suggested next step after the user resolves failures."

**Impact:** Prevents unintended downstream side effects from failed gate runs.

---

#### H3: P3-03 / P3-04 Have No Remediation Path for Artifact-Less Projects
**Location:** assets/phase-3-gate-checklist.md (P3-03, P3-04)  
**Observed:** P3-03 expects a `coverage-report*` file; P3-04 expects `test-results*`. Many projects don't export these as persistent files. Both items are `required=yes`. `skill_to_create` is blank for P3-03 and P3-04, so there is no remediation suggestion on failure.

**Suggestion:** Add `skill_to_create` values or `documentation_hint` for P3-03/P3-04:
- P3-03: hint = "Export coverage report: `pytest --cov=. --cov-report=html:_hbc_output/impl/coverage-report` or equivalent."
- P3-04: hint = "Export test results: `pytest --tb=short > _hbc_output/impl/test-results.txt` or equivalent."

Or add a new checklist column `hint` for FILE/METRIC failures that produces no file result at all. This column would surface a "how to generate this artifact" note rather than a skill name.

**Impact:** Builders who ran tests correctly but didn't persist results can self-serve without help.

---

### Medium-Opportunity

#### M1: Gate Log Has No "Did We Ever Pass?" Summary Line
**Location:** SKILL.md § Evaluate Gate (step 5, gate log)  
**Observed:** The gate log is an append-only delta table per session. With multiple re-runs, the file becomes a series of tables. There is no instruction to maintain a top-level "current status" line or a chronological summary list that lets a reviewer scan for "first PASS on 2026-05-15."

**Suggestion:** Add an instruction: "Maintain a two-line header at the top of the gate log file: `Current status: {overall_status}` and `Last evaluated: {timestamp}`. Update on each run. Below the header, append per-session delta tables." This lets any reader see current status without scanning the full log.

**Impact:** Gatekeeper and automator can read gate health at a glance from the log header without parsing tables.

---

#### M2: `find` Fallback Discovery Doesn't Offer to Use Discovered Path
**Location:** SKILL.md § Evaluate Gate (step 3, FILE failure fallback)  
**Observed:** When `find` discovers a near-match, the skill includes the finding in evidence but still marks the item FAIL. In interactive mode, this is a missed opportunity — the user could confirm the discovered file is the right one, and the gate could re-evaluate that item using the discovered path.

**Suggestion:** In interactive mode only (not headless): after reporting a near-match, ask: "Found `docs/design/D-19-database-design.md` — is this your D-19? (y/n). If yes, I'll re-evaluate P2-01 using this path." If confirmed, re-evaluate the specific item and update its status. Write the path override to a note in the gate log for auditability.

**Impact:** Edge-case users with non-standard paths get a recovery path instead of a manual TOML edit.

---

#### M3: First-Run Delta Is Semantically Misleading
**Location:** SKILL.md § Evaluate Gate (step 5, delta table) and Headless Mode (JSON schema)  
**Observed:** On the very first gate run, no prior results exist, so every item appears in the `NEW` column of the delta table. The delta summary reads: "0 fixed, 0 regressed, N unchanged" (or all N as new). This looks like a change report when there is no prior baseline.

**Suggestion:** Add a conditional: "If `prior_results` map is empty (first evaluation), skip the delta table entirely and write a single note: 'First evaluation — no prior results to compare.' In headless JSON, add `is_first_run: true` to the summary block." This prevents callers from misinterpreting an all-NEW delta as a signal.

**Impact:** Cleaner gate log; correct headless delta semantics for automation.

---

#### M4: QUALITY Parallel Review Lenses Still Absent
**Location:** SKILL.md § Evaluate Gate (step 3, QUALITY items)  
**Observed:** Previous analysis flagged this; not yet addressed. QUALITY items required for gate pass (e.g., P2-08 test coverage completeness, P4-06 traceability matrix) depend on single-evaluator LLM judgment. The skill instructs "Be strict" but offers no structural check on that strictness.

**Suggestion:** For `required=yes` QUALITY items in non-headless mode: optionally fan out two lenses — a skeptic looking for gaps and an acceptance lens confirming the intent is met. PASS if both agree; surface disagreement for user decision. Gate this behind `{workflow.quality_parallel_review}` (default: `false`) so teams can opt in for critical phases.

**Impact:** Reduces false positives (lenient single-pass) and false negatives (overly harsh single-fail) on high-stakes QUALITY items.

---

### Low-Opportunity

#### L1: Gate Report Template "Revision History" Table Is Obsolete
**Location:** assets/gate-report-template.md  
**Observed:** Template includes a `Revision History` table with `Date | Status | Notes` columns. The gate log now handles re-evaluation history. This table is a dead placeholder that will never be filled.

**Suggestion:** Replace with a one-liner: `**Evaluation history:** See [phase-{N}-gate-log.md]({workflow.gate_output_path}/phase-{N}-gate-log.md).` Remove the empty table.

**Impact:** Cleaner report; no confusion about who fills the revision table.

---

#### L2: Phase Inference Confirmation Uses Freeform Prose — No Consistent Form
**Location:** SKILL.md § On Activation, Step 5  
**Observed:** Confirmation text is: `"Inferred phase {N} ({phase_name}) from {agent} context. Proceed?"` — good framing. But the template is in SKILL.md as prose, leaving exact wording to the LLM. Different invocations may word this differently.

**Suggestion:** This is low-stakes, but if team consistency matters: move the confirmation phrasing to a `references/phase-confirmation.md` template — one sentence, one format. Not urgent, and may be over-engineering for a single sentence.

**Impact:** Consistent user experience across agents and invocations.

---

#### L3: P4-07 Checks Previous Gate Reports By File Existence — Not By Status
**Location:** assets/phase-4-gate-checklist.md (P4-07)  
**Observed:** P4-07: "All previous gates PASSED" — type is FILE, checking `_hbc_output/gates/phase-1-gate*`, etc. FILE type only checks file existence, not whether the gate report says PASSED. A project with FAILED gate reports that still have a report file would pass this check.

**Suggestion:** Change P4-07 type to CONTENT with criteria: `overall_status: PASSED` or `**Status:** PASSED` (matching the gate report template's status field). This would actually validate that previous gates passed, not just that report files exist.

**Impact:** Closes a logical gap — the "all previous gates passed" check currently verifies nothing about gate outcomes.

---

## Top 3 Insights

### Insight 1: The `on_complete` Hook Is a Latent Bug
The skill has matured significantly, but the unconditional `on_complete` firing is a correctness issue that will surface immediately when any team configures the hook. A FAILED gate should not trigger downstream workflows. This is the highest-priority fix — it's one clause change in SKILL.md and prevents silent state corruption in integrated pipelines.

### Insight 2: P4-07 Validates File Presence, Not Gate Outcomes
The Phase 4 "all previous gates passed" check (P4-07) uses FILE type, meaning it verifies that gate report files exist — not that they contain a PASSED status. A project that reached Phase 4 with a FAILED Phase 2 gate report still on disk would pass P4-07. Changing this to a CONTENT check with a status pattern match is a one-line checklist edit that closes a real logical gap in the progression model.

### Insight 3: Headless QUALITY Semantics Is the Core Integration Risk
The headless mode is well-structured, but its value to automation callers depends entirely on whether QUALITY items are evaluated or skipped. If skipped, a headless PASSED status may mean "all deterministic items passed, QUALITY unknown" — which is not a safe signal for auto-advancing a sprint. One sentence clarifying that QUALITY is evaluated headlessly (no prompts, LLM judges artifact content directly) would make the headless contract trustworthy for pipeline use.
