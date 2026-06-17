---
name: hbc-phase-gate
description: "Phase gate validation engine for HBC incremental + TDD lifecycle. Use when user says 'phase gate', 'gate check', 'kiểm tra gate', or 'đánh giá gate'."
---

# Phase Gate

## Overview

Validation engine for phase transitions in the HBC Incremental-TDD lifecycle. Receives a phase number, loads the corresponding gate checklist, evaluates each item against project artifacts, and produces a gate report with PASSED/FAILED status. Act as a strict quality gate reviewer — objective, evidence-based, no handwaving.

Four phases: Analysis (1), Design (2), Implementation (3), Testing (4). Each checklist defines items with evaluation types: `[FILE]` (artifact exists), `[CONTENT]` (pattern present), `[METRIC]` (numeric threshold), `[QUALITY]` (LLM judgment). Gate PASSES only when all required items pass.

`gate_mode` config: `strict` blocks next phase on failure, `lenient` warns but allows.

**Args:** Phase number (1-4), or inferred from calling agent context. Optional: `--headless` for non-interactive JSON output. To preview a checklist without evaluation, ask _"show phase N checklist"_.

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

Execute `{workflow.activation_steps_prepend}`, load `{workflow.persistent_facts}`, then load config from `{project-root}/_bmad/config.yaml` (root and `hbc` section) — resolve `{gate_mode}` (default: `strict`), `{coverage_threshold}` (default: `80`), `{project_name}`, `{output_folder}` (resolved to an absolute path — passed to the evaluator so checklist `{output_folder}/...` patterns resolve), `{communication_language}`, `{document_output_language}`. Execute `{workflow.activation_steps_append}`. Determine target phase:
- Explicit argument (e.g. "phase gate 2") → use that number.
- Agent context → infer: BA→1, Architect/QA→2, Dev→3, Tester→4. **Confirm with user:** _"Inferred phase {N} ({phase_name}) from {agent} context. Proceed?"_ Only skip confirmation in headless mode.
- Otherwise → ask user which phase to evaluate (1-4).

## Evaluate Gate

1. **Load checklist** from `{workflow.phase_N_checklist}` where N is the target phase. Variable substitution: `{coverage_threshold}` in criteria fields, `{project_name}` in artifact patterns. If file not found at resolved path, fall back to `assets/phase-{N}-gate-checklist.md`.

2. **Check previous results** at `{workflow.gate_output_path}/phase-{N}-gate-results.json`. If present, load directly as `prior_results` (structured JSON — no markdown parsing needed). Fall back to parsing `phase-{N}-gate.md` if the JSON doesn't exist. This enables delta comparison after evaluation.

3. **Evaluate deterministic items** via script, then judge QUALITY items:

   ```
   python3 scripts/evaluate-gate-checklist.py {checklist_path} --project-root {project-root} --var output_folder={output_folder} --var gate_mode={gate_mode} --var coverage_threshold={coverage_threshold} --var project_name={project_name}
   ```

   `--var output_folder` is REQUIRED — checklist artifact patterns use `{output_folder}/...` so they resolve under any configured output folder (pass the resolved absolute path). `--var gate_mode` lets the script flag entry-gate failures (see step 4).

   The script evaluates `[FILE]`, `[CONTENT]`, and `[METRIC]` items deterministically and returns JSON with per-item status + evidence. `[QUALITY]` items return as `PENDING_LLM`. Script exit code 1 means required items failed deterministically — this is a partial signal, not the final gate verdict (QUALITY items still need evaluation). If the script fails entirely, evaluate manually following the same JSON schema: `{"summary": {...}, "results": [{"item_id", "status", "evidence", ...}]}` per item.

   For each `PENDING_LLM` item: read the referenced artifacts, apply judgment against the stated criteria. PASS/FAIL with **quantified evidence** — cite specific counts, IDs, and gaps (e.g., "found 23 requirements but only 19 test cases; missing coverage for REQ-002, REQ-015, REQ-021"). Never use vague evidence like "looks good" or "mostly complete". Be strict — vague or incomplete artifacts fail.

   If `{workflow.quality_parallel_review}` is true: for `required=yes` QUALITY items, evaluate with two lenses — skeptic (actively looks for gaps) and acceptance (evaluates whether the artifact meets stated intent). PASS only when both agree. If they disagree, mark as `CONTESTED` with both evidence summaries; in interactive mode surface the disagreement for user decision, in headless mode include both in the JSON.

   For each `FAIL` on a `[FILE]` item: the script returns a `near_matches` array of candidate files found via relaxed glob. Surface any near-matches in the evidence. Use the `skill_to_create` field from the JSON (if present) to suggest the creating skill: _"Missing D-19. Create with `hbc-create-er-diagram`."_ If the suggested skill doesn't exist yet, note the expected document type and content instead.

### Report and Present

4. **Determine overall status:**
   - **PASSED** — every `required=yes` item is PASS.
   - **FAILED** — any `required=yes` item is FAIL.
   - If `{gate_mode}=lenient` and FAILED → downgrade to **WARNING**, **EXCEPT** when the failure includes an entry-gate item (a `required` CONTENT check that a PRIOR phase gate PASSED — the script reports these as `summary.entry_gate_failed > 0`). Entry-gate failures keep the gate **FAILED** even in lenient mode: a phase must never proceed on top of a failed predecessor gate (B2).

5. **Write gate report and decision log:**
   - Write gate report to `{workflow.gate_output_path}/phase-{N}-gate.md` using `{workflow.gate_report_template}` in `{document_output_language}`. Include: timestamp, phase, overall status, item-by-item results with evidence, summary statistics. Also save the final evaluation JSON (with QUALITY items resolved) to `{workflow.gate_output_path}/phase-{N}-gate-results.json` — the delta script consumes this directly on re-evaluation.
   - Generate the delta entry via script and append to `{workflow.gate_output_path}/phase-{N}-gate-log.md`:

     ```
     python3 scripts/generate-gate-delta.py {current_results_json} --prior {prior_results_json} --status {overall_status} -o {delta_entry_file}
     ```

     Omit `--prior` on first evaluation. The script produces a ready-to-append markdown block (delta table with summary, or "First evaluation" note). Append the output verbatim. Create the log file with a `# Phase {N} Gate Log` heading and a two-line status header (`Current status: {overall_status}` / `Last evaluated: {timestamp}`) if it doesn't exist; update the header on each run.

6. **Present results:**
   - If re-evaluation (prior_results exists), lead with delta summary: items fixed, items regressed, items unchanged. Highlight regressions prominently. For QUALITY items that remain FAIL across runs, include a one-line prior-evidence note: _"Previously: {prior evidence summary}. Now: {current evidence summary}."_ — this surfaces progress even when the status hasn't changed (e.g. 19/23 → 21/23).
   - PASSED → congratulate, suggest invoking `hbc-traceability` [TR] to update matrix, then proceeding to next phase.
   - FAILED (strict) → list failures with fix guidance. Separate actionable failures (missing artifacts with a generation command in criteria, e.g. P3-03/P3-04) from quality failures — present actionable items first with their commands so the user can generate artifacts and re-run immediately.
   - WARNING (lenient) → list failures as risks, note user chose to proceed at own discretion.

## Headless Mode

When invoked with `--headless` or by another skill passing `headless=true`:

1. Phase number is **required** (no interactive prompt, no inference).
2. QUALITY items are evaluated headlessly using the same LLM judgment logic — no user prompts are issued. Evidence is embedded in the JSON result.
3. Skip all user-facing output (no congratulations, no fix guidance).
4. After evaluation, return a **single JSON block** to the caller:

   ```json
   {
     "phase": 2,
     "status": "PASSED | FAILED | WARNING",
     "gate_mode": "strict | lenient",
     "summary": { "total": 10, "passed": 8, "failed": 1, "skipped": 0 },
     "required_failed": ["P2-03"],
     "delta": { "is_first_run": false, "fixed": ["P2-01"], "regressed": [], "new": ["P2-10"], "unchanged": ["P2-02", "..."] },
     "report_path": "{workflow.gate_output_path}/phase-2-gate.md",
     "log_path": "{workflow.gate_output_path}/phase-2-gate-log.md"
   }
   ```

5. Gate report and decision log are still written to disk as normal.
6. `on_complete` hook still fires if configured (PASSED only — see Post-Gate Hook).

## Post-Gate Hook

If `{workflow.on_complete}` is non-empty and the gate status is PASSED, treat it as a skill invocation command (e.g., `"invoke hbc-traceability"`) and execute it. If the value is not a recognized skill, present it to the user as a suggested next step. For FAILED or WARNING, mention the configured hook as a next step after failures are resolved — do not execute it.
