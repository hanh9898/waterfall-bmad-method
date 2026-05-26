---
name: hbc-traceability
description: "Living traceability matrix for HBC waterfall lifecycle. Use when user says 'traceability', 'ma trận', 'truy vết', or agent menu [TR]."
---

# Traceability Matrix

## Overview

Maintain a living traceability matrix that maps requirements through design, implementation, and testing. Updated incrementally after each phase — each invoke adds data, never removes. The matrix is the single source of truth for "which requirement is covered where."

Seven-column matrix: `req_id`, `story_id`, `design_ref`, `code_ref`, `test_ref`, `gate_status`, `timestamp`. Four capabilities: **Initialize**, **Update**, **Report**, **Audit**.

**Args:** Capability name (`init`, `update`, `report`, `audit`), or inferred from current phase context. Optional: `--headless` for non-interactive JSON output.

## Conventions

- Bare paths (e.g. `assets/matrix-template.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Headless Mode

When invoked with `--headless` or by another skill passing `headless=true`:

1. Capability is **required** (no interactive prompt).
2. Skip all user-facing output.
3. Return a **single JSON block**:

   ```json
   {
     "capability": "init | update | report | audit",
     "matrix_path": "_hbc_output/traceability/matrix.md",
     "total_requirements": 23,
     "coverage": {
       "design_ref": 20,
       "code_ref": 18,
       "test_ref": 15,
       "fully_traced": 15
     },
     "gaps": ["REQ-002", "REQ-015"]
   }
   ```

4. Matrix file is still written/updated on disk.

## On Activation

### Step 1: Resolve the Workflow Block

Run: `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`

If the script fails, resolve manually: `{skill-root}/customize.toml` → `{project-root}/_bmad/custom/{skill-name}.toml` → `{project-root}/_bmad/custom/{skill-name}.user.toml`. Scalars override, tables deep-merge, arrays append.

### Step 2: Execute Prepend Steps

Execute each entry in `{workflow.activation_steps_prepend}` in order.

### Step 3: Load Persistent Facts

Load `{workflow.persistent_facts}` as foundational context. `file:` prefixed entries load file contents.

### Step 4: Load Config

Load from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (root and `hbc` section). Resolve `{project_name}`, `{communication_language}`, `{document_output_language}`.

### Step 5: Execute Append Steps and Determine Capability

Execute `{workflow.activation_steps_append}`. Determine capability:
- Explicit argument (e.g. "traceability init") → use that capability.
- Agent context → infer: BA after Phase 1 gate → `init`, Architect/Dev/Tester after gate → `update`.
- Otherwise → ask user which capability (`init`, `update`, `report`, `audit`).

When capability is inferred (not explicit), confirm with user: _"Inferred 'update' from Dev context. Proceed?"_ Skip confirmation in headless mode.

## Initialize

Create the traceability matrix from D-02 requirements.

1. **Extract REQ IDs** deterministically:

   ```
   python3 scripts/extract-trace-ids.py --source {project-root}/_hbc_output/plan/D-02-* --pattern "REQ-\d{3,}" --project-root {project-root}
   ```

   Returns JSON array of discovered IDs.

2. **Create matrix** at `{workflow.matrix_path}` using `assets/matrix-template.md`. Populate one row per REQ ID with `req_id` and `timestamp` filled, all other columns empty.

3. **Report:** _"Initialized matrix with {count} requirements from D-02. Next: run Phase 1 gate, then update after Phase 2."_

## Update

Populate columns for the current phase. Detect which columns need filling by reading the existing matrix.

1. **Read current matrix** from `{workflow.matrix_path}`. If missing, suggest running `init` first.

2. **Detect phase** from which columns are empty:
   - `design_ref` empty → Phase 2 update needed.
   - `code_ref` empty → Phase 3 update needed.
   - `test_ref` empty → Phase 4 update needed.

3. **Phase 2 update — design_ref + test_ref:**
   - Extract entity/table names from D-19: `python3 scripts/extract-trace-ids.py --source {project-root}/_hbc_output/design/D-19-* --pattern "(?:テーブル|Table|Entity)[\s:：]*(\w+)" --project-root {project-root}`
   - Extract TC IDs from D-27: `python3 scripts/extract-trace-ids.py --source {project-root}/_hbc_output/design/D-27-* --pattern "TC-\d{3,}" --project-root {project-root}`
   - For each REQ, use LLM judgment to match design entities and test cases. Read D-02, D-19, D-27 to determine which entities and TCs trace to which REQs. Populate `design_ref` and `test_ref` columns.

4. **Phase 3 update — code_ref:**
   - Ask user for the source code root path (or use `{workflow.source_code_path}` if configured).
   - For each REQ, use LLM judgment to identify implementing files/functions. Populate `code_ref` column with file:function references.

5. **Phase 4 update — gate_status + timestamp:**
   - Read gate reports from `{project-root}/_hbc_output/gates/phase-*-gate.md`.
   - For each REQ, set `gate_status` to PASSED if all gates passed, or note which gate failed.
   - Set `timestamp` to current date.

6. **Write updated matrix** back to `{workflow.matrix_path}`.

7. **Report coverage** after update: _"Updated {column}. Coverage: {X}/{Y} requirements now have {column} populated."_

## Report

Generate coverage summary from current matrix state.

1. **Parse matrix** deterministically:

   ```
   python3 scripts/trace-report.py --matrix {workflow.matrix_path}
   ```

   Returns JSON: total requirements, per-column fill counts, fully-traced count (all columns non-empty).

2. **Present summary:**
   - Total requirements: {total}
   - Per-column coverage: design_ref {X}/{total}, code_ref {Y}/{total}, test_ref {Z}/{total}
   - Fully traced (all columns): {W}/{total} ({percentage}%)
   - If gaps exist, list the first 10 gap REQ IDs.

## Audit

Find gaps — requirements without coverage in any column.

1. **Run report** (same as above) to get per-column data.

2. **For each gap:** identify which columns are empty and suggest the remediation skill:
   - Missing `design_ref` → _"REQ-002: no design reference. Update after Phase 2 design completion."_
   - Missing `code_ref` → _"REQ-015: no code reference. Update after Phase 3 implementation."_
   - Missing `test_ref` → _"REQ-021: no test reference. Check D-27 for missing test cases — use `hbc-create-test-spec`."_

3. **Classify gap severity:**
   - Required REQ with empty `test_ref` after Phase 4 → **CRITICAL** — untested requirement.
   - Required REQ with empty `code_ref` after Phase 3 → **HIGH** — unimplemented requirement.
   - Any column empty in earlier phase → **INFO** — expected, not yet at that phase.

4. **Present audit** with severity-sorted gap list.

## On Complete

If `{workflow.on_complete}` is non-empty, treat it as a skill invocation command and execute it. If the value is not a recognized skill, present it to the user as a suggested next step.
