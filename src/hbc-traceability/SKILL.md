---
name: hbc-traceability
description: "Living traceability matrix + cascade document sync for the HBC incremental + TDD lifecycle. Use when user says 'traceability', 'ma trận', 'truy vết', 'sync', 'đồng bộ tài liệu', 'cascade', 'lan truyền thay đổi', or agent menu [TR]/[SYNC]."
---

# Traceability Matrix

## Overview

Maintain a living traceability matrix **per feature** that maps requirements through design, implementation, and testing. Updated incrementally after each phase — each invoke adds data, never removes. Each feature has its own matrix at `{workflow.matrix_path}` (`{feature}` resolved at runtime); a cross-feature **roll-up** at `{workflow.rollup_path}` aggregates them. Single source of truth for "which requirement is covered where."

Eight-column matrix: `feature` (primary grouping; shared REQs marked `feature = shared`), `req_id`, `story_id` (optional BMM story link; never counted toward coverage), `design_ref`, `code_ref`, `test_ref`, `gate_status`, `timestamp`. Coverage is measured only on `design_ref`/`code_ref`/`test_ref` — **per feature**. Five capabilities: **Initialize**, **Update**, **Report** (incl. roll-up), **Audit**, **Impact** (cascade sync — reads matrix + task-status + phase-gate + git to suggest propagating a change; never edits content).

**Args:** Capability name (`init`, `update`, `report`, `audit`, `impact`); **`feature=<slug>`** (mandatory in headless; interactive resolves the active feature or asks). Optional: `--headless` for non-interactive JSON output. Requires Python 3.10+ for the deterministic scripts.

## Conventions

Bare paths resolve from the skill root; `{skill-root}` = this skill's installed dir; `{project-root}`-prefixed paths resolve from the project working dir. Capability report strings follow `{communication_language}`.

## Headless Mode

`--headless` / `headless=true` from another skill (full I/O contract: `references/headless-contract.md`): capability is **required** (no prompt); skip user-facing output; return JSON with `status` (`complete`/`blocked`), `capability`, `matrix_path`, `decision_log` (when Update writes), summary stats, and `reason` on `blocked`. Matrix is still written on disk. For `impact`: return `changed`, `affected`, `frozen` (→ new-task), `suggested`, and after apply `reconciled`/`blocked`. Closed-set blocked reasons: `matrix_not_found`, `empty_changeset`, `untraced_change`, `skill_no_update_contract`, `skill_runtime_error`, `reconcile_unverified`.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation.

**Resolve active feature (B):** `feature=<slug>` arg, else the session's active feature, else ask. Headless: `feature=<slug>` is **mandatory** — missing → `blocked` `reason=feature_required`. Validate slug `^[a-z0-9][a-z0-9-]*$`; resolve every `{feature}` below.

Then determine capability: explicit arg → use it; agent context → infer (BA after Phase 1 gate → `init`; Architect/Dev/Tester after gate → `update`); else ask. When inferred, confirm with the user (skip in headless).

## Initialize

Create the traceability matrix from D-02 requirements.

1. **Extract REQ IDs** deterministically:

   ```
   python3 scripts/extract-trace-ids.py --source {output_folder}/features/{feature}/planning-artifacts/D-02-* --pattern "REQ-[A-Z0-9]+-\d{3,}" --project-root {project-root}
   ```

   Returns JSON array of discovered IDs (the feature's `REQ-<FEAT>-*` plus the `REQ-SHARED-*` it references). If script returns `NO_FILES`, suggest running `hbc-create-requirements` (feature={feature}) to generate D-02 first.

2. **Create matrix** at `{workflow.matrix_path}` using `{workflow.matrix_template}`. Populate one row per REQ ID with `feature` (= active feature; or `shared` for `REQ-SHARED-*`), `req_id`, and `timestamp` filled, all other columns empty.

3. **Report:** _"Initialized matrix for feature '{feature}' with {count} requirements. Next: run Phase 1 gate, then update after Phase 2."_

## Update

Populate columns for the current phase. First check for `{output_folder}/features/{feature}/traceability/.trace-state.json` — if present, an update was interrupted. Surface: _"A Phase {N} update was interrupted. Restarting — written mappings are preserved, this run fills remaining empty cells."_ In headless mode, restart silently.

Detect phase via prepass: `python3 scripts/trace-report.py --matrix {workflow.matrix_path} --detect-phase`. If matrix missing, suggest `init` first. The script returns `{next_phase, empty_columns, total_rows}` — route below. Before starting, note which REQs have empty target columns (the diff baseline). Write state marker: `{"update_in_progress": "{column}", "phase": N, "started": "{timestamp}"}`. Clear on completion.

Each phase self-writes its OWN column (B7-2); Report `--verify-columns` checks the result. **Phase 2 — design_ref + test_ref:** extract TC IDs from D-27 (`python3 scripts/extract-trace-ids.py --source {output_folder}/features/{feature}/planning-artifacts/D-27-* --pattern "TC-\d{3,}" --project-root {project-root}`). Read D-19 by **path-existence precedence**: per-feature `{output_folder}/features/{feature}/planning-artifacts/D-19-*` else `{output_folder}/shared/erd/D-19-*`. Use LLM judgment to map each REQ to the design elements (tables/entities/modules) that realize it, plus its D-27 TCs. **Before writing** present the mappings + confirm (headless: write + log confidence). Populate `design_ref`, `test_ref`, and `story_id` if a BMM story exists.

> **Re-pull `test_ref` when D-27 grows (DF-9).** D-27 is not frozen at Phase 2 — a later cascade appends TCs the matrix never received. On EVERY re-run, re-extract TC↔REQ from the current D-27 and refresh `test_ref`. Trigger: Audit `test_ref_drift` → re-run Phase 2 to back-fill `missing` (and drop `stale`).

**Phase 3 — code_ref:** Use `{workflow.source_code_path}` if configured, otherwise ask user (tip: _"Set `source_code_path` in customize override to skip this prompt."_). For each REQ, use LLM judgment to identify implementing files/functions. **Before writing:** present proposed mappings and confirm. Populate `code_ref` with `file:function`.

**Phase 4 — gate_status + timestamp:** Read gate reports from `{workflow.gate_reports_glob}`. Set `gate_status` per REQ. Set `timestamp` to current date.

Write updated matrix. For each non-obvious LLM-judgment mapping, append a line to `{output_folder}/features/{feature}/traceability/.trace-decisions.md`: `{timestamp} | {req_id} → {target_ref} | {one-line rationale}` (create with a heading if absent). In headless mode, log all mappings with confidence levels.

Report with diff: list which REQs received new mappings this session, and any mappings that changed (if re-running Update). Then: _"Updated {column}. Coverage: {X}/{Y} requirements now have {column} populated. Next: run `hbc-phase-gate` for the next gate check."_

## Report

Generate coverage summary from current matrix state.

1. **Parse matrix** deterministically:

   ```
   python3 scripts/trace-report.py --matrix {workflow.matrix_path}
   ```

   Returns JSON: total requirements, per-column fill counts, fully-traced count (all columns non-empty).

2. **Present summary:** total requirements; per-column coverage (design_ref/code_ref/test_ref {X}/{total}); fully traced {W}/{total} ({%}); list the first 10 gap REQ IDs if any.

3. **Verify per-phase columns (B7-2).** Each phase self-writes its column via Update/TRU; Report VERIFIES the result — no blank trace axis slipped through:

   ```
   python3 scripts/trace-report.py --matrix {workflow.matrix_path} --verify-columns
   ```

   `all_columns_filled` false (exit 1) → list the `gapped_reqs` and route each to the owning phase's Update.

4. **Cross-feature roll-up (TRR):** aggregate coverage across all features:

   ```
   python3 scripts/trace-report.py --rollup "{output_folder}/features/*/traceability/matrix.md" --out {workflow.rollup_path}
   ```

   Write `{workflow.rollup_path}`: one line per feature (total / fully-traced / %) + the project-wide total — which feature is done vs in progress, without mixing.

## Audit

Find gaps — requirements without coverage in any column.

1. **Run report** (same as above) to get per-column data.

1b. **Detect stale `test_ref` against D-27 (DF-9).** A filled `test_ref` is not proof it is current. Cross-check `python3 scripts/trace-report.py --matrix {workflow.matrix_path} --d27 {output_folder}/features/{feature}/planning-artifacts/D-27-*`: `d27_sync.test_ref_drift` = `{req: {missing, stale}}`. Any drift is **HIGH** (matrix misrepresents coverage) → re-run **Update Phase 2**. Same check as `hbc-check-implementation-readiness` at the Phase 2 seam.

2. **For each gap:** name the empty columns + the remediation skill: missing `design_ref` → Update after Phase 2; `code_ref` → Update after Phase 3; `test_ref` → check D-27, run `hbc-create-test-spec`.

3. **Classify gap severity:** required REQ with empty `test_ref` after Phase 4 → **CRITICAL** (untested); empty `code_ref` after Phase 3 → **HIGH** (unimplemented); any column empty in an earlier phase → **INFO** (not yet at that phase).

4. **Present audit** with severity-sorted gap list.

## Impact (Cascade Document Sync)

When a document changes, suggest propagating it to every affected artifact — **READ + SUGGEST only** (every edit goes through the owning-skill `update` mode): present a suggestion table, then stop; apply only when the user acts. Uses the matrix as the impact graph; replaces the former standalone sync skill.

Lifecycle **DECLARE → IMPACT → FREEZE-CHECK → SUGGEST → (validate-plan) → APPLY → RECONCILE → ADVISORY (non-REQ)** — each stage reads a source of truth then suggests; `scripts/impact.py` (detect/analyze/freeze/complete) does the deterministic part.

### Cascade Pre-check — ENFORCED gate (B7-1/3/5/6)

**The cascade is ENFORCED, not advisory.** Before any document with downstream consumers reaches "complete"/phase-transition (and as the first thing `impact` does), run `scripts/cascade-precheck.py` (`--d02 --matrix` + optional `--d27 --task-breakdown --gate-reports-glob --design --code-dir`). Impact stays READ-only — the gate *reports* a blocker; backfill is the owning step's job. On `blocked` (`reason: untraced_change` / `cascade_required: true`, exit 1) the complete/gate step **MUST NOT transition** — prompt backfill, then re-run.

CLI + per-B7 detail (B7-6/1 untraced-block, B7-3 drift-watch, B7-5 rebaseline route, B7-4 reconcile-adversarial) + per-stage flow (`{workflow.*}` flags, freeze priority, anti-loop, reconcile, advisory): `references/impact-capability.md`. Boundary rules: `references/edge-handling.md`.

### Build-Graph view (TA.1) — matrix-as-view

`scripts/build-graph.py --feature-dir <dir>` (kernel `hbc-shared/lib/hbc_buildgraph.py`) → JSON `dirty_set`, `matrix_view` (REQ→design→code→test derived from edges), `missing_edges`, `ground_truth_drift` (machine-floor code↔design). Floor only; reconcile verdict + gate state-machine = TA.2+. Detail: `references/build-graph.md`.

## Autonomy (A5)

Mechanical (path resolution, which capability, report formatting) — decide and proceed. The gate verdict is mechanical: a non-empty blocker set BLOCKS — never soft-pedal an untraced change into a pass (that *is* the RCA cascade failure). Domain — whether a surfaced gap is an accepted deferral (e.g. REQ deliberately out-of-scope this phase): **ASK; never fabricate a clean matrix.** Headless: `--strict` stops at the first gap; `--assumptions-allowed` (CI default) treats every gap as real (non-green), logs that no deferral was confirmed, never blocks the first turn — CI never gets a false green from an untraced change.

> **T2.11 (revision-churn) / T2.12 (semantic-review frontmatter) — N/A:** traceability MANAGES the matrix; it authors no versioned D-xx doc with a revision history or `semanticReview` block (stated per §0.1).
