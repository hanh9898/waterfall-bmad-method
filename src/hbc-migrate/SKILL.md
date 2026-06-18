---
name: hbc-migrate
description: "Migrate (di chuyển output) một dự án HBC v1 (layout flat) sang layout v2 per-feature + shared. dry-run plan → confirm → apply; idempotent. Use when user says 'migrate', 'migrate v1', 'di chuyển output', 'nâng cấp layout', or agent menu [MIG]."
---

# Migrate v1 → v2 (Phase 0)

## Overview

Convert a project that ran **HBC v1** (flat output: `_bmad-output/{planning-artifacts,implementation-artifacts,gates,traceability}/`, id `REQ-NNN`, 7-column matrix) to **v2**: per-feature `_bmad-output/features/<feature>/{…}/` + shared `_bmad-output/shared/{coding-standards,glossary,erd,api}/`, id `REQ-<FEAT>-NNN`, 8-column matrix. A one-time, **destructive** operation (moves files) → defaults to **dry-run**; only `apply` writes.

**Args:** `plan` (default — dry-run preview, writes nothing), `apply` (execute). Optional: `feature=<slug>`, `--apply`, `--force`, `-H` / `--headless`.

Orchestrated engine: `{skill-root}/scripts/migrate-to-feature-layout.py` (dry-run default, `--apply`, `--feature`, `--reprefix`, `--json`, `--timestamp`, `--force`). Determinism (move/re-prefix/rebuild matrix/backup) lives in the script; judgment (which feature? shared or per-feature? split multi-feature?) lives in the skill.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename. Output written in `{document_output_language}`, communicate in `{communication_language}`.

## On Activation

Resolve customization, load persistent facts + config per standard BMad activation.

> No `feature` namespacing on the output — the skill **rewrites `_bmad-output/` in place**. `feature=<slug>` is used only to assign the REQ/TC prefix + route per-feature.

## Headless Mode

`-H` runs `plan` (default) / `apply` non-interactively. Full I/O contract — args, return schema, blocked reasons: `references/headless-contract.md`. Headless `apply` requires `feature=<slug>` + `--apply`; the headless default = plan JSON (`--json`). Idempotent.

Blocked reasons (closed set): `feature_required` · `multi_feature_ambiguous` · `nothing_to_migrate` · `dirty_worktree`.

## Stages

### Stage 1: Detect & Classify

Run the engine in scan mode (dry-run, `--json`). Detect a valid flat layout: `planning-artifacts/D-*`, flat `implementation-artifacts/`, `gates/`, `traceability/matrix*` (7 columns), id `REQ-NNN`. Classify each artifact → **shared** vs **per-feature**.

**Idempotent:** if already v2 (or nothing legacy) → report "nothing to migrate" and **stop** (headless: `blocked: nothing_to_migrate`).

### Stage 2: Plan (judgment)

Route:
- **shared/** → D-12 (coding-standards), D-03 (glossary), baseline D-19 (erd), D-21 (api).
- **features/<feature>/** → D-02, D-06, D-26, D-27, task-breakdown, gates, matrix.

**Resolve feature:** single-project flat docs → ask the user / use `feature=<slug>` (headless missing → `blocked: feature_required`). **Multi-feature** flat docs (REQs of several features in one D-02) → **warn** + offer to split: v1 requires one `--feature` per run (or a manual split); headless cannot infer it → `blocked: multi_feature_ambiguous`.

No double-create: if `shared/` already exists (PI has run) → leave it as is, never overwrite.

### Stage 3: Dry-run preview (default)

For the `plan` action: call the engine with `--json` (no `--apply`) → print the **full plan**: each `src → dst`, the re-prefix map `REQ-NNN → REQ-<FEAT>-NNN` **and** `TC-NNN`, the planned 7→8 column matrix rebuild (insert the `feature` column). **Writes nothing.** The user reviews, then confirms to proceed to `apply`.

### Stage 4: Apply (`apply` / `--apply`)

Only runs for the `apply` action (or `--apply`). The engine:
1. **Dirty-guard:** if the git worktree has uncommitted changes → refuse (headless: `blocked: dirty_worktree`), unless `--force`.
2. **Backup** before any move (`.archive/<ts>/`, `--timestamp`).
3. Move files per the plan; **re-prefix REQ and TC** in the moved D-02/D-26/D-27/matrix (`--reprefix`).
4. **Rebuild the 8-column matrix** (insert the `feature` column).
5. Write a **decision-log** of every change.

Idempotent: an artifact already at v2 → skip.

### Stage 5: Verify & Handoff

Run the validators on the migrated artifacts + `trace-report.py --d02` (d02-sync) + readiness `[IR]` (`hbc-check-implementation-readiness`). Report pass/gaps.

> **Matrix gap after migrate.** Migration **stays faithful** to the v1 matrix — it does NOT fabricate rows. If the v1 matrix was already missing a REQ (e.g. D-02 has `REQ-AUTH-003` but the matrix has no such row), `trace-report --d02` after migrate will report `missing_from_matrix: [REQ-AUTH-003]`. This is NOT a migrate bug — **surface the missing REQ clearly** to the user and **suggest running `[TRU]`** (`hbc-traceability update`) to backfill it so it matches D-02. Likewise, an orphan (a REQ no longer in D-02) → suggest cleanup.

Handoff (communicate in `{communication_language}`):

_"Migrate done → v2 layout. If shared is still missing, run `[PI]` (`hbc-project-init`). Then continue per-feature: `[BA]` / `hbc-create-requirements` with `feature=<slug>`."_

Headless: return JSON per `references/headless-contract.md` (`status`, `moves`, `reprefix`, `matrix`, `validation`, or `blocked` + `reason`).
