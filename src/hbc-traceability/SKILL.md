---
name: hbc-traceability
description: "Living traceability matrix + cascade document sync for the HBC incremental + TDD lifecycle. Use when user says 'traceability', 'ma trận', 'truy vết', 'sync', 'đồng bộ tài liệu', 'cascade', 'lan truyền thay đổi', or agent menu [TR]/[SYNC]."
---

# Traceability Matrix

## Overview

Maintain a living traceability matrix **per feature** that maps requirements through design, implementation, and testing. Updated incrementally after each phase — each invoke adds data, never removes. Each feature has its own matrix at `{workflow.matrix_path}` (`{feature}` resolved at runtime); a cross-feature **roll-up** at `{workflow.rollup_path}` aggregates them. The matrix is the single source of truth for "which requirement is covered where."

Eight-column matrix: `feature` (the primary grouping — the matrix file is per-feature; rows for shared REQs are marked `feature = shared`), `req_id`, `story_id` (optional — links the REQ to a BMM story ID when one exists; left empty otherwise, and never counted toward coverage), `design_ref`, `code_ref`, `test_ref`, `gate_status`, `timestamp`. Coverage/completeness is measured only on `design_ref`, `code_ref`, `test_ref` — **per feature**. Five capabilities: **Initialize**, **Update**, **Report** (includes the cross-feature roll-up), **Audit**, **Impact** (cascade sync — reads matrix + task-status + phase-gate + git to suggest propagating a change; never edits content itself).

**Args:** Capability name (`init`, `update`, `report`, `audit`, `impact`); **`feature=<slug>`** (mandatory in headless; interactive resolves the active feature in the session or asks). Optional: `--headless` for non-interactive JSON output. Requires Python 3.10+ for the deterministic scripts.

## Conventions

- Bare paths (e.g. `assets/matrix-template.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.
- Capability report strings follow `{communication_language}`.

## Headless Mode

When invoked with `--headless` or by another skill passing `headless=true` (full I/O contract — input args, per-capability return schema, blocked reasons: `references/headless-contract.md`):

1. Capability is **required** (no interactive prompt).
2. Skip all user-facing output.
3. Return JSON with `status` (`complete` or `blocked`), `capability`, `matrix_path`, `decision_log` (path to `.trace-decisions.md`, present when Update writes new entries), and summary stats. On `blocked`, include `reason`. Matrix file is still written/updated on disk.
4. For `impact`: return `changed`, `affected` (each labeled apply/verify), `frozen` (→ new-task), `suggested` (skill + order), and after apply `reconciled`/`blocked`. Closed-set blocked reasons: `matrix_not_found`, `empty_changeset` (no-op), `untraced_change`, `skill_no_update_contract`, `skill_runtime_error`, `reconcile_unverified`. Full contract: `references/impact-capability.md`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation.

**Resolve active feature (B):** use the `feature=<slug>` arg if present; otherwise take the active feature the orchestrating agent holds in the session; if still none → ask the user. In **headless**, `feature=<slug>` is **mandatory** — if missing, return `blocked` with `reason=feature_required`. Validate the slug against `^[a-z0-9][a-z0-9-]*$`. Use it to resolve every `{feature}` in the paths below.

Then determine capability:
- Explicit argument (e.g. "traceability init") → use that capability.
- Agent context → infer: BA after Phase 1 gate → `init`, Architect/Dev/Tester after gate → `update`.
- Otherwise → ask user which capability (`init`, `update`, `report`, `audit`, `impact`).

When capability is inferred (not explicit), confirm with user: _"Inferred 'update' from Dev context. Proceed?"_ Skip confirmation in headless mode.

## Initialize

Create the traceability matrix from D-02 requirements.

1. **Extract REQ IDs** deterministically:

   ```
   python3 scripts/extract-trace-ids.py --source {output_folder}/features/{feature}/planning-artifacts/D-02-* --pattern "REQ-[A-Z0-9]+-\d{3,}" --project-root {project-root}
   ```

   Returns JSON array of discovered IDs (including the feature's `REQ-<FEAT>-*` and the `REQ-SHARED-*` the feature references). If script returns `NO_FILES`, suggest running `hbc-create-requirements` (feature={feature}) to generate D-02 first.

2. **Create matrix** at `{workflow.matrix_path}` using `{workflow.matrix_template}`. Populate one row per REQ ID with `feature` (= active feature; or `shared` for `REQ-SHARED-*`), `req_id`, and `timestamp` filled, all other columns empty.

3. **Report:** _"Initialized matrix for feature '{feature}' with {count} requirements. Next: run Phase 1 gate, then update after Phase 2."_

## Update

Populate columns for the current phase. First check for `{output_folder}/features/{feature}/traceability/.trace-state.json` — if present, an update was interrupted. Surface: _"A Phase {N} update was interrupted. Restarting — previously written mappings are preserved, this run fills remaining empty cells."_ In headless mode, restart silently.

Detect phase via prepass: `python3 scripts/trace-report.py --matrix {workflow.matrix_path} --detect-phase`. If matrix missing, suggest `init` first. The script returns `{next_phase, empty_columns, total_rows}` — use this to route below. Before starting, note which REQs have empty target columns (the diff baseline). Write state marker: `{"update_in_progress": "{column}", "phase": N, "started": "{timestamp}"}`. Clear on completion.

**Phase 2 — design_ref + test_ref:** Extract TC IDs from D-27 via `python3 scripts/extract-trace-ids.py --source {output_folder}/features/{feature}/planning-artifacts/D-27-* --pattern "TC-\d{3,}" --project-root {project-root}`. Read D-19 by **path-existence precedence (b)**: if `{output_folder}/features/{feature}/planning-artifacts/D-19-*` exists, use it; otherwise fall back to `{output_folder}/shared/erd/D-19-*`. D-19 is the ER/component diagram — use LLM judgment to extract named tables, entities, or modules and map each REQ to the design elements that structurally realize it, plus test cases from D-27. **Before writing:** present proposed mappings as a table and confirm with user. In headless mode, write directly and log confidence levels. Populate `design_ref` and `test_ref`. If the REQ traces to a BMM story, also populate `story_id` with that story ID; otherwise leave it empty.

**Phase 3 — code_ref:** Use `{workflow.source_code_path}` if configured, otherwise ask user (tip: _"Set `source_code_path` in customize override to skip this prompt."_). For each REQ, use LLM judgment to identify implementing files/functions. **Before writing:** present proposed mappings and confirm. Populate `code_ref` with `file:function` references.

**Phase 4 — gate_status + timestamp:** Read gate reports from `{workflow.gate_reports_glob}`. Set `gate_status` per REQ. Set `timestamp` to current date.

Write updated matrix. For each non-obvious mapping made by LLM judgment, append a line to `{output_folder}/features/{feature}/traceability/.trace-decisions.md`: `{timestamp} | {req_id} → {target_ref} | {one-line rationale}`. Create the file with a heading if it doesn't exist. In headless mode, log all mappings with confidence levels.

Report with diff: list which REQs received new mappings this session, and any mappings that changed (if re-running Update). Then: _"Updated {column}. Coverage: {X}/{Y} requirements now have {column} populated. Next: run `hbc-phase-gate` for the next gate check."_

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

3. **Cross-feature roll-up (TRR):** aggregate coverage across all features:

   ```
   python3 scripts/trace-report.py --rollup "{output_folder}/features/*/traceability/matrix.md" --out {workflow.rollup_path}
   ```

   Write `{workflow.rollup_path}`: one line per feature (total / fully-traced / %) + the project-wide total. Shows "which feature is done, which is still in progress" without mixing them up.

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

## Impact (Cascade Document Sync)

When a document changes, suggest propagating the change down to every affected artifact — **READ + SUGGEST only** (every edit goes through the owning-skill in `update` mode): present a suggestion table, then stop; apply only when the user acts. Uses the matrix itself as the impact graph; replaces the former standalone sync skill.

Lifecycle **DECLARE → IMPACT → FREEZE-CHECK → SUGGEST → (validate-plan) → APPLY → RECONCILE → ADVISORY (non-REQ)** — each stage reads a source of truth then suggests, with `scripts/impact.py` (detect/analyze/freeze/complete) doing the deterministic part.

Per-stage operational detail (CLI + `{workflow.*}` flags, freeze priority, anti-loop, reconcile, advisory): `references/impact-capability.md`. Boundary rules: `references/edge-handling.md`.
