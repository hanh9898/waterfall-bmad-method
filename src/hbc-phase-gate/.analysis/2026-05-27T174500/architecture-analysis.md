# Architecture Analysis — hbc-phase-gate

**Scan date:** 2026-05-27  
**Skill path:** `src/hbc-phase-gate`  
**Pre-pass status:** workflow-integrity=FAIL (3 critical), prompt-metrics=INFO

---

## Assessment

`hbc-phase-gate` is a well-conceived validation engine with clean separation between deterministic script evaluation and LLM judgment — the intelligence-placement principle is correctly applied throughout. The core design is sound: the `On Activation` resolver chain, fallback logic for custom checklists, and the delta-comparison pattern in `Evaluate Gate` all reflect good BMad institutional knowledge. However, the skill has a critical structural failure — SKILL.md references three files (`1-gate-checklist.md`, `2-gate-log.md`, `2-gate.md`) that do not exist anywhere in the skill tree, making the workflow non-executable as shipped. There is also a decision-log inconsistency: the log records "No headless mode" as a settled decision, but SKILL.md implements a full `## Headless Mode` section — a direct promise-vs-behavior contradiction.

---

## Findings

### CRITICAL

**F-01 — Three dangling file references in SKILL.md**  
Severity: Critical | File: `SKILL.md` (lines reported as 0 by prepass — actual references are in `Evaluate Gate` section)

The workflow-integrity prepass found three referenced stage files that do not exist:
- `1-gate-checklist.md`
- `2-gate-log.md`
- `2-gate.md`

These appear to be numbered-prefix carve-out artifacts from an earlier iteration of the skill. The actual checklist files ship in `assets/` (correctly named `phase-{N}-gate-checklist.md`), but some references in SKILL.md still point to the old numbered filenames. An executing agent following these references will get a file-not-found error.

**Fix:** Audit every reference in SKILL.md against actual files on disk. Remove or correct the three dangling paths. No carved-out `references/` files are needed here — the skill is correctly classified as simple-workflow with inline content; the `references/` directory contains only `.decision-log.md` (correct).

---

**F-02 — Decision log contradicts implemented headless mode**  
Severity: Critical | Files: `references/.decision-log.md` (line 22), `SKILL.md` (line 18)

Decision log entry: _"No headless mode — Gate is invoked interactively from agent menus [PG]. Quality checks involve judgment that benefits from user context."_

SKILL.md implements a full `## Headless Mode` section (lines 18–41) with a structured JSON return schema, skip rules for user-facing output, and explicit `--headless` flag handling. The decision was reversed but the log was never updated.

This violates the promise-vs-behavior check (principles file, §Promises-vs-behavior). An agent resuming from the decision log would believe headless is out of scope and may not activate that path correctly.

**Fix:** Append a new session entry to `.decision-log.md` recording the headless mode reversal, the rationale (likely: callers need machine-readable gate results), and which prior decision it overrides. The log is append-only; don't edit the old entry.

---

### HIGH

**F-03 — Numbered-prefix filenames referenced (though files don't exist)**  
Severity: High | File: `SKILL.md`, workflow-integrity prepass

The three missing files (`1-gate-checklist.md`, `2-gate-log.md`, `2-gate.md`) carry numbered prefixes — a pattern the principles file explicitly bans: _"Carved-out files use descriptive names (`press-release.md`), NOT numbered prefixes (`01-discover.md`)."_ Even if these files were created, the naming convention would be wrong.

**Fix:** If any of these were intended as carved-out references (which the content of this skill does not seem to warrant), rename them descriptively (`gate-checklist.md`, `gate-log-format.md`, etc.) and inline them rather than carving them out, since SKILL.md at 118 lines is well under the carve-out threshold.

---

**F-04 — `On Activation` over-prescribed with numbered steps**  
Severity: High | File: `SKILL.md` (lines 49–74)

`## On Activation` is split into five titled sub-steps (`Step 1` through `Step 5`). Steps 2, 3, and 4 are single-line instructions that could be one sentence. The principles file is explicit: _"Numbered procedural steps for things the LLM does naturally"_ don't earn their place. Loading config, executing prepend/append arrays, and loading persistent facts are all LLM-native sequential operations.

The only step that warrants precision is Step 1 (the script invocation with exact command) and the phase-inference logic in Step 5 (non-obvious agent-context mapping). Steps 2–4 are padding.

**Fix:** Collapse Steps 2–4 into a single sentence: _"Execute `{workflow.activation_steps_prepend}`, load `{workflow.persistent_facts}`, then load config from `{project-root}/_bmad/config.yaml` (root and `hbc` section), resolving `{gate_mode}`, `{coverage_threshold}`, `{project_name}`, `{communication_language}`, `{document_output_language}`."_ Keep Step 1 and Step 5 intact.

---

**F-05 — `references/` directory misused**  
Severity: High | File: `src/hbc-phase-gate/references/`

The `references/` directory contains only `.decision-log.md`. Per principles: _"`references/` is for prompt content carved out of SKILL.md."_ A decision log is workspace state, not a carved-out workflow section. The decision log belongs at the workspace root — either at `src/hbc-phase-gate/.decision-log.md` or alongside the primary artifact.

More importantly, the principles file states the Decision-Log Workspace pattern applies to _"multi-turn workflows producing a revisable artifact"_ — this is a simple utility that regenerates on each run with no revisable state. The decision log here is the **author's build log**, not a workflow decision log. That's fine to have, but it should live at skill root, not in `references/`.

**Fix:** Move `.decision-log.md` to `src/hbc-phase-gate/.decision-log.md` (skill root, as a peer of `SKILL.md` and `customize.toml`). Remove the now-empty `references/` directory.

---

### MEDIUM

**F-06 — `## Evaluate Gate` step 3 description slightly prescriptive**  
Severity: Medium | File: `SKILL.md` (lines 78–93)

The `find` command for near-match discovery (`find {project-root} -name "*{artifact_keyword}*"`) is embedded inline in prose rather than being in the script. This is borderline — the script handles FILE evaluation deterministically, but the near-match fallback requires the LLM to run a separate shell command. If the near-match logic is worth keeping, it should either be added to `scripts/evaluate-gate-checklist.py` (which already handles FILE evaluation) or stated as an outcome: _"For FAIL FILE items, search for near-matches to include in evidence."_ The exact `find` command teaches the LLM something it already knows.

**Fix:** Either move near-match discovery into `evaluate-gate-checklist.py` as an option flag (cleaner, deterministic), or drop the explicit `find` command and express the outcome: _"Include any near-matches (typos, alternate locations) in the evidence."_

---

**F-07 — `scripts/tests/` directory is empty**  
Severity: Medium | File: `src/hbc-phase-gate/scripts/tests/`

The tests directory exists but is empty. `scripts/evaluate-gate-checklist.py` is 271 lines of non-trivial parsing and evaluation logic (glob resolution, regex matching, metric extraction). The principles file doesn't mandate tests for scripts, but an empty test directory signals intent never acted on — it's dead structure that creates false confidence.

**Fix:** Either populate with basic tests for `parse_checklist`, `evaluate_file`, `evaluate_content`, and `evaluate_metric`, or remove the empty directory if tests aren't being maintained.

---

**F-08 — `{communication_language}` not referenced in headless output path**  
Severity: Medium | File: `SKILL.md` (lines 18–41)

The headless JSON schema returns `report_path` and `log_path` but the report and log are written using `assets/gate-report-template.md`, which contains no `{communication_language}` or `{document_output_language}` substitution. The checklists themselves also lack language variables. For a skill that includes Vietnamese trigger phrases (`'kiểm tra gate'`, `'đánh giá gate'`), the gate report will always be in whatever language the template is written in, ignoring the configured output language.

**Fix:** Add `{document_output_language}` to the gate report template header, and add a note in `## Evaluate Gate` that the report is produced in `{document_output_language}`.

---

### LOW

**F-09 — `## Headless Mode` placement before `## Conventions`**  
Severity: Low | File: `SKILL.md` (structure)

Standard BMad SKILL.md order: Overview → Conventions → On Activation → workflow sections. `## Headless Mode` appears between Overview and Conventions, interrupting the standard activation flow. Readers scanning for the conventions block have to skip a long JSON schema first.

**Fix:** Move `## Headless Mode` after `## Evaluate Gate` or just before `## On Complete`, where it reads as a modifier to the output behavior rather than a structural section.

---

**F-10 — Gate report template uses HTML comment syntax for placeholder guidance**  
Severity: Low | File: `assets/gate-report-template.md` (lines 23–28)

Comments like `<!-- For each FAIL item: what was expected, what was found, suggested fix -->` and `<!-- PASSED: Phase {N} complete, proceed to Phase {N+1} -->` are author instructions embedded in a template the LLM fills. These will appear in the rendered output if an LLM naively writes the template verbatim. They should either be removed (the LLM knows how to write a "Failed Items Detail" section) or replaced with actual placeholder markers (`{failed_items_detail}`) that signal substitution rather than commentary.

**Fix:** Remove the HTML comment instructions. The LLM will produce the right content from the section headings alone.

---

## Strengths

**Intelligence placement is correct.** The script handles FILE, CONTENT, and METRIC evaluation deterministically; QUALITY items pass through to LLM judgment with the criterion stated. The boundary is drawn exactly where the principles file says it should be. No regex deciding what content "means" in the script; no counting or pattern-matching delegated to the LLM prompt.

**`customize.toml` design is well-considered.** The four `phase_N_checklist` scalars let teams override individual phase checklists without touching others. The explicit comment that `gate_mode` lives in project config (not per-skill override) reflects good policy-vs-configuration thinking. The `on_complete` hook scalar is the right shape for post-gate automation.

**Delta comparison pattern is strong.** The `prior_results` map and the structured delta log (fixed/regressed/new/unchanged) give re-evaluations meaningful signal. This is the kind of domain framing the principles file says earns its place.

**Description format is correct.** Quoted trigger phrases, bilingual coverage (EN + VI), conservative explicit triggering — all correct per BMad naming conventions.

**Fallback checklist resolution is correct.** `{workflow.phase_N_checklist}` with fallback to `assets/phase-{N}-gate-checklist.md` is the right pattern: config-resolvable paths with graceful degradation to bundled defaults.

**Conventions block is present and correctly stamped.** The canonical four-line Conventions block is in place exactly as the principles file requires for any SKILL.md referencing multiple internal files.
