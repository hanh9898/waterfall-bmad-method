---
name: hbc-phase-gate
description: "Phase gate validation engine for HBC waterfall lifecycle. Use when user says 'phase gate', 'gate check', 'kiểm tra gate', or 'đánh giá gate'."
---

# Phase Gate

## Overview

Validation engine for phase transitions in the HBC Waterfall-TDD lifecycle. Receives a phase number, loads the corresponding gate checklist, evaluates each item against project artifacts, and produces a gate report with PASSED/FAILED status. Act as a strict quality gate reviewer — objective, evidence-based, no handwaving.

Four phases: Analysis (1), Design (2), Implementation (3), Testing (4). Each checklist defines items with evaluation types: `[FILE]` (artifact exists), `[CONTENT]` (pattern present), `[METRIC]` (numeric threshold), `[QUALITY]` (LLM judgment). Gate PASSES only when all required items pass.

`gate_mode` config: `strict` blocks next phase on failure, `lenient` warns but allows.

**Args:** Phase number (1-4), or inferred from calling agent context. Optional: `--headless` for non-interactive JSON output.

## Conventions

- Bare paths (e.g. `assets/phase-1-gate-checklist.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails, resolve manually: `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays append.

### Step 2: Load Context and Determine Phase

Execute `{workflow.activation_steps_prepend}`, load `{workflow.persistent_facts}`, then load config from `{project-root}/_bmad/config.yaml` (root and `hbc` section) — resolve `{gate_mode}` (default: `strict`), `{coverage_threshold}` (default: `80`), `{project_name}`, `{communication_language}`, `{document_output_language}`. Execute `{workflow.activation_steps_append}`. Determine target phase:
- Explicit argument (e.g. "phase gate 2") → use that number.
- Agent context → infer: BA→1, Architect/QA→2, Dev→3, Tester→4. **Confirm with user:** _"Inferred phase {N} ({phase_name}) from {agent} context. Proceed?"_ Only skip confirmation in headless mode.
- Otherwise → ask user which phase to evaluate (1-4).

## Evaluate Gate

1. **Load checklist** from `{workflow.phase_N_checklist}` where N is the target phase. Variable substitution: `{coverage_threshold}` in criteria fields, `{project_name}` in artifact patterns. If file not found at resolved path, fall back to `assets/phase-{N}-gate-checklist.md`.

2. **Check previous gate report** at `{workflow.gate_output_path}/phase-{N}-gate.md`. If present, extract per-item statuses into a `prior_results` map (`item_id → status`). This enables delta comparison after evaluation.

3. **Evaluate deterministic items** via script, then judge QUALITY items:

   ```
   python3 scripts/evaluate-gate-checklist.py {checklist_path} --project-root {project-root} --var coverage_threshold={coverage_threshold} --var project_name={project_name}
   ```

   The script evaluates `[FILE]`, `[CONTENT]`, and `[METRIC]` items deterministically and returns JSON with per-item status + evidence. `[QUALITY]` items return as `PENDING_LLM`. If the script fails, evaluate manually following the same JSON schema: `{"summary": {...}, "results": [{"item_id", "status", "evidence", ...}]}` per item.

   For each `PENDING_LLM` item: read the referenced artifacts, apply judgment against the stated criteria. PASS/FAIL with **quantified evidence** — cite specific counts, IDs, and gaps (e.g., "found 23 requirements but only 19 test cases; missing coverage for REQ-002, REQ-015, REQ-021"). Never use vague evidence like "looks good" or "mostly complete". Be strict — vague or incomplete artifacts fail.

   For each `FAIL` on a `[FILE]` item: search for near-matches across `{project-root}` (typos, alternate locations) and include any discoveries in the evidence. If the checklist item references a document ID (e.g. D-19), map it to the creating skill from the module catalog and suggest it: _"Missing D-19. Create with `hbc-create-db-design`."_

4. **Determine overall status:**
   - **PASSED** — every `required=yes` item is PASS.
   - **FAILED** — any `required=yes` item is FAIL.
   - If `{gate_mode}=lenient` and FAILED → downgrade to **WARNING**.

5. **Write gate report and decision log:**
   - Write gate report to `{workflow.gate_output_path}/phase-{N}-gate.md` using `{workflow.gate_report_template}` in `{document_output_language}`. Include: timestamp, phase, overall status, item-by-item results with evidence, summary statistics.
   - Generate the delta entry via script and append to `{workflow.gate_output_path}/phase-{N}-gate-log.md`:

     ```
     python3 scripts/generate-gate-delta.py {current_results_json} --prior {prior_results_json} --status {overall_status} -o {delta_entry_file}
     ```

     Omit `--prior` on first evaluation. The script produces a ready-to-append markdown block (delta table with summary, or "First evaluation" note). Append the output verbatim. Create the log file with a `# Phase {N} Gate Log` heading and a two-line status header (`Current status: {overall_status}` / `Last evaluated: {timestamp}`) if it doesn't exist; update the header on each run.

6. **Present results:**
   - If re-evaluation (prior_results exists), lead with delta summary: items fixed, items regressed, items unchanged. Highlight regressions prominently.
   - PASSED → congratulate, suggest invoking `hbc-traceability` [TR] to update matrix, then proceeding to next phase.
   - FAILED (strict) → list failures with fix guidance, recommend addressing each before re-running gate.
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
     "delta": { "fixed": ["P2-01"], "regressed": [], "new": ["P2-10"], "unchanged": ["P2-02", "..."] },
     "report_path": "_hbc_output/gates/phase-2-gate.md",
     "log_path": "_hbc_output/gates/phase-2-gate-log.md"
   }
   ```

5. Gate report and decision log are still written to disk as normal.
6. `on_complete` hook still fires if configured (PASSED only — see On Complete).

## On Complete

If `{workflow.on_complete}` is non-empty and the gate status is PASSED, treat it as a skill invocation command (e.g., `"invoke hbc-traceability"`) and execute it. If the value is not a recognized skill, present it to the user as a suggested next step. For FAILED or WARNING, mention the configured hook as a next step after failures are resolved — do not execute it.
