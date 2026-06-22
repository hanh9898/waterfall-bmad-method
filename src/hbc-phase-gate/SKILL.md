---
name: hbc-phase-gate
description: "Phase gate validation engine for HBC incremental + TDD lifecycle. Use when user says 'phase gate', 'gate check', 'kiểm tra gate', or 'đánh giá gate'."
---

# Phase Gate

## Overview

Validation engine for phase transitions in the HBC Incremental-TDD lifecycle. Receives a phase number, loads the gate checklist, evaluates each item against project artifacts, and produces a gate report. Act as a strict, evidence-based reviewer — no handwaving.

This is a **GATE** — blocking is its job. The cardinal sin is a false PASS (the RCA case passed a Phase-2 gate whose evaluator had crashed and whose matrix was missing REQ-040/041/042). Never go green on un-computed, ambiguous, or unadjudicated evidence.

Four phases: Analysis (1), Design (2), Implementation (3), Testing (4). Each checklist defines items with evaluation types: `[FILE]` (artifact exists), `[CONTENT]` (pattern present), `[METRIC]` (numeric threshold), `[MATRIX]` (REQ→matrix coverage, script-computed), `[REVIEW]` (semanticReview passed), `[QUALITY]` (LLM judgment). Gate PASSES only when every required item is PASS or `NA`.

**Correctness items** (entry-gate · `[MATRIX]` · any item tagged `[correctness]`) are non-negotiable: a FAIL is never downgraded by lenient mode and never silenced by a waiver. **Verdicts:** `PASSED` / `FAILED` / `WARNING` (lenient, non-correctness) / `CONTESTED` (unresolvable required item or QUALITY-lens disagreement — adjudicate, never auto-pass) / `BLOCKED` (evaluator crashed — never a PASS). Full semantics in [`references/gate-semantics.md`](references/gate-semantics.md).

`gate_mode` config: `strict` blocks next phase on failure, `lenient` warns — **except** correctness + CONTESTED items, which block in either mode.

**Args:** Phase number (1-4); **`feature=<slug>`** (gate is per-feature — required in headless mode; in interactive mode it takes the active feature from the session); or inferred from calling agent context. Optional: `--headless` for non-interactive JSON output. To preview a checklist without evaluation, ask _"show phase N checklist"_.

## Conventions

- Bare paths (e.g. `assets/phase-1-gate-checklist.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails, resolve manually: `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays append.

### Load Context and Determine Phase

> **Resolve active feature (B):** `{feature}` from arg `feature=<slug>` → session active feature → ask (headless: required, else `blocked` `feature_required`); validate slug. The gate evaluates **this feature** — the checklist is namespaced to `features/{feature}/...` (and `shared/...` for D-12/D-03, dual for D-19/D-21); the per-feature matrix already filters REQs by feature.

Execute `{workflow.activation_steps_prepend}`, load `{workflow.persistent_facts}`, then load config from `{project-root}/_bmad/config.yaml` (root + `hbc` section) — resolve `{gate_mode}` (default `strict`), `{coverage_threshold}` (default `80`), `{project_name}`, `{output_folder}` (absolute — passed to the evaluator so `{output_folder}/...` patterns resolve), `{communication_language}`, `{document_output_language}`. Execute `{workflow.activation_steps_append}`. Determine target phase:
- Explicit argument (e.g. "phase gate 2") → use that number.
- Agent context → infer: BA→1, Architect/QA→2, Dev→3, Tester→4. **Confirm with user:** _"Inferred phase {N} ({phase_name}) from {agent} context. Proceed?"_ Only skip confirmation in headless mode.
- Otherwise → ask user which phase to evaluate (1-4).

## Evaluate Gate

1. **Load checklist** from `{workflow.phase_N_checklist}` where N is the target phase. Variable substitution: `{coverage_threshold}` in criteria fields, `{project_name}` in artifact patterns. If file not found at resolved path, fall back to `assets/phase-{N}-gate-checklist.md`.

2. **Check previous results** at `{workflow.gate_output_path}/phase-{N}-gate-results.json` — if present, load as `prior_results` for delta comparison (fall back to parsing `phase-{N}-gate.md`).

3. **Evaluate deterministic items** via script, then judge QUALITY items:

   ```
   python3 scripts/evaluate-gate-checklist.py {checklist_path} --project-root {project-root} --var output_folder={output_folder} --var feature={feature} --var gate_mode={gate_mode} --var coverage_threshold={coverage_threshold} --var project_name={project_name} [--na D-19,D-21]
   ```

   `--var output_folder` **and `--var feature`** are REQUIRED (artifact patterns use `{output_folder}/features/{feature}/...`); `--var gate_mode` lets the script apply the lenient/correctness rules in step 4.

   **N/A deliverables (per-feature waiver).** Read the feature's D-02 frontmatter `na_deliverables` and pass them as `--na D-19,D-21`. Waived items report **`NA`** (not FAIL). **Only D-19 / D-21 may be waived** — D-02/D-03/D-06 apply to every feature — and a waiver may **never** silence a correctness item (B6-4, see step 4 + reference).

   The script evaluates `[FILE]`, `[CONTENT]`, `[METRIC]`, `[MATRIX]`, and `[REVIEW]` items deterministically and returns JSON with per-item status + evidence. **All numbers the gate reports come from the script (B6-2) — never claim an "X/Y" count from your own reading.** `[QUALITY]` items return as `PENDING_LLM`.

   - **A9 `[MATRIX]` (correctness):** the script reuses shared `missing_from_matrix` / `matrix_coverage_gaps` to verify every D-02 REQ has a matrix row with non-empty refs — the teeth that catch the RCA "39/39 green" false pass. Surface its `missing_from_matrix` / `coverage_gaps` verbatim.
   - **Robustness (B6-6):** a `{"status":"BLOCKED","reason":"evaluator_crashed"}` emission, or any inability to run the script, makes the gate **BLOCKED, not PASS** — report and stop. A required `[METRIC]` whose number can't be extracted is `CONTESTED`. A manual PASS over a crashed correctness check is the RCA false-pass — never do it.
   - **B6-1 adversarial QUALITY:** evaluate every required QUALITY item with two lenses (skeptic + acceptance), each with quantitative evidence; PASS only if both agree, **disagreement → `CONTESTED`**.

   Full rules — correctness classes, verdict precedence, B6-1/B6-5/waiver, autonomy, forward-refs — in [`references/gate-semantics.md`](references/gate-semantics.md). For each `PENDING_LLM` item: read the artifacts, judge against the criteria with **quantified evidence** (counts, IDs, gaps — never "looks good"); vague or incomplete artifacts fail.

   For a `FAIL` on a `[FILE]` item: surface the script's `near_matches` and use `skill_to_create` to suggest the creating skill (_"Missing D-19. Create with `hbc-create-er-diagram`."_); if that skill doesn't exist yet, note the expected document type instead.

### Report and Present

4. **Determine overall status** — the script computes `summary.overall_status`; mirror it after resolving QUALITY items. Precedence: **BLOCKED** (crash) → **FAILED** (any required FAIL) → **CONTESTED** (a required item unresolvable, or lens-disagreement) → **PASSED** (all required PASS/`NA`). Lenient downgrades FAILED→**WARNING** **except** entry-gate (`entry_gate_failed`), other correctness (`correctness_failed`: `[MATRIX]`/MODEL_DRIFT — B6-3 extend), and CONTESTED items — these block in either mode.
   - **Waiver (B6-4):** `--na D-NN` skips an inapplicable D-19/D-21 (one-line rationale in D-02 frontmatter); it may **never** waive a correctness item — the script reports `waiver_rejected` and still evaluates it.
   - **B6-5 design-phase sign-off:** a Phase 1/2 PASS additionally requires explicit **USER sign-off** recorded in the report decision section (headless `--assumptions-allowed` → `PASSED_PENDING_SIGNOFF`, not a clean PASS; `--strict` blocks). `maturity: exploratory` relaxes it to a lightweight ack.
   - Detail + autonomy + forward-refs (A2/A8 stale, A4 ADR, maturity-gating, TA.3 RECYCLE `gate-outcome.py`): [`references/gate-semantics.md`](references/gate-semantics.md).

5. **Write gate report and decision log:**
   - Write gate report to `{workflow.gate_output_path}/phase-{N}-gate.md` using `{workflow.gate_report_template}` in `{document_output_language}`. Include: timestamp, phase, overall status, item-by-item results with evidence, summary statistics. Also save the final evaluation JSON (with QUALITY items resolved) to `{workflow.gate_output_path}/phase-{N}-gate-results.json` — the delta script consumes this directly on re-evaluation.
   - Generate the delta entry via script and append to `{workflow.gate_output_path}/phase-{N}-gate-log.md`:

     ```
     python3 scripts/generate-gate-delta.py {current_results_json} --prior {prior_results_json} --status {overall_status} -o {delta_entry_file}
     ```

     Omit `--prior` on first evaluation. The script produces a ready-to-append markdown block (delta table with summary, or "First evaluation" note). Append the output verbatim. Create the log file with a `# Phase {N} Gate Log` heading and a two-line status header (`Current status: {overall_status}` / `Last evaluated: {timestamp}`) if it doesn't exist; update the header on each run.

6. **Present results:**
   - On re-evaluation, lead with the delta summary (fixed / regressed / unchanged); highlight regressions. For a QUALITY item still FAIL across runs, add a one-line _"Previously: … Now: …"_ note to surface progress (19/23 → 21/23).
   - PASSED → (after B6-5 sign-off for Phase 1/2) suggest `hbc-traceability` [TR], then the next phase.
   - FAILED (strict) / CONTESTED / BLOCKED → list the blocking items with fix guidance; present actionable artifact-generation failures (e.g. P3-03/04) first. WARNING (lenient) → list failures as risks the user accepted.

## Headless Mode

When invoked with `--headless` or by another skill passing `headless=true` (full I/O contract — input args, return schema, blocked reasons: `references/headless-contract.md`):

1. Phase number is **required** (no interactive prompt, no inference).
2. QUALITY items are evaluated headlessly using the same LLM judgment logic — no user prompts are issued. Evidence is embedded in the JSON result.
3. Skip all user-facing output (no congratulations, no fix guidance).
4. **Autonomy mode (A5):** `--strict` blocks at the first possible-deferral / design-phase sign-off; `--assumptions-allowed` (CI default) returns the honest non-green verdict (never fabricates a PASS — see Autonomy in `references/gate-semantics.md`).
5. After evaluation, return a **single JSON block** — `phase`, `status` (`PASSED | PASSED_PENDING_SIGNOFF | FAILED | WARNING | CONTESTED | BLOCKED`), `gate_mode`, `summary` (incl. `contested` / `correctness_failed` / `entry_gate_failed`), `required_failed`, `delta`, `report_path`, `log_path`. Full schema in [`references/headless-contract.md`](references/headless-contract.md).
6. Gate report and decision log are still written to disk as normal.
7. `on_complete` hook still fires if configured (PASSED only — see Post-Gate Hook).

## Post-Gate Hook

If `{workflow.on_complete}` is non-empty and the status is PASSED, treat it as a skill invocation (e.g. `"invoke hbc-traceability"`) and execute it; if it's not a recognized skill, present it as a suggested next step. For FAILED/WARNING/CONTESTED/BLOCKED, mention the hook as a next step after the blockers are resolved — do not execute it.
