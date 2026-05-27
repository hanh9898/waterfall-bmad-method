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

## Headless Mode

When invoked with `--headless` or by another skill passing `headless=true`:

1. Phase number is **required** (no interactive prompt, no inference).
2. Skip all user-facing output (no congratulations, no fix guidance).
3. After evaluation, return a **single JSON block** to the caller:

   ```json
   {
     "phase": 2,
     "status": "PASSED | FAILED | WARNING",
     "gate_mode": "strict | lenient",
     "summary": { "total": 10, "passed": 8, "failed": 1, "skipped": 0, "pending_llm": 1 },
     "required_failed": ["P2-03"],
     "delta": { "fixed": ["P2-01"], "regressed": [], "new": ["P2-10"], "unchanged": ["P2-02", "..."] },
     "report_path": "_hbc_output/gates/phase-2-gate.md",
     "log_path": "_hbc_output/gates/phase-2-gate-log.md"
   }
   ```

4. Gate report and decision log are still written to disk as normal.
5. `on_complete` hook still fires if configured.

## Conventions

- Bare paths (e.g. `assets/phase-1-gate-checklist.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails, resolve manually: `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays append.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order.

### Step 3: Load Persistent Facts

Load `{workflow.persistent_facts}` as foundational context. `file:` prefixed entries load file contents.

### Step 4: Load Config

Load from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (root and `hbc` section). If missing, `hbc-setup` can configure. Resolve `{gate_mode}` (default: `strict`), `{coverage_threshold}` (default: `80`), `{project_name}`, `{communication_language}`, `{document_output_language}`.

### Step 5: Execute Append Steps and Determine Phase

Execute `{workflow.activation_steps_append}`. Determine target phase:
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

   The script evaluates `[FILE]`, `[CONTENT]`, and `[METRIC]` items deterministically and returns JSON with per-item status + evidence. `[QUALITY]` items return as `PENDING_LLM`.

   For each `PENDING_LLM` item: read the referenced artifacts, apply judgment against the stated criteria. PASS/FAIL with **quantified evidence** — cite specific counts, IDs, and gaps (e.g., "found 23 requirements but only 19 test cases; missing coverage for REQ-002, REQ-015, REQ-021"). Never use vague evidence like "looks good" or "mostly complete". Be strict — vague or incomplete artifacts fail.

   For each `FAIL` on a `[FILE]` item: run `find {project-root} -name "*{artifact_keyword}*"` to discover near-matches (typos, alternate locations). Include any near-matches in the evidence. If the checklist item references a document ID (e.g. D-19), map it to the creating skill from the module catalog and suggest it: _"Missing D-19. Create with `hbc-create-db-design`."_

4. **Determine overall status:**
   - **PASSED** — every `required=yes` item is PASS.
   - **FAILED** — any `required=yes` item is FAIL.
   - If `{gate_mode}=lenient` and FAILED → downgrade to **WARNING**.

5. **Write gate report and decision log:**
   - Write gate report to `{workflow.gate_output_path}/phase-{N}-gate.md` using `assets/gate-report-template.md`. Include: timestamp, phase, overall status, item-by-item results with evidence, summary statistics.
   - Append a session entry to `{workflow.gate_output_path}/phase-{N}-gate-log.md`. Create the file with a `# Phase {N} Gate Log` heading if it doesn't exist. Each entry:
     ```
     ## {timestamp} — {overall_status}
     | Item ID | Previous | Current | Change |
     |---------|----------|---------|--------|
     ```
     Populate from `prior_results` map. Mark changes: `FAIL→PASS` (fixed), `PASS→FAIL` (regression), `NEW` (first evaluation), or `—` (unchanged). End with a one-line delta summary: _"X fixed, Y regressed, Z unchanged."_

6. **Present results:**
   - If re-evaluation (prior_results exists), lead with delta summary: items fixed, items regressed, items unchanged. Highlight regressions prominently.
   - PASSED → congratulate, suggest invoking `hbc-traceability` [TR] to update matrix, then proceeding to next phase.
   - FAILED (strict) → list failures with fix guidance, recommend addressing each before re-running gate.
   - WARNING (lenient) → list failures as risks, note user chose to proceed at own discretion.

## On Complete

If `{workflow.on_complete}` is non-empty, treat it as a skill invocation command (e.g., `"invoke hbc-traceability"`) and execute it. If the value is not a recognized skill, present it to the user as a suggested next step.
