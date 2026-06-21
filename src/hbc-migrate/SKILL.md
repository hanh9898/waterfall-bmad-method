---
name: hbc-migrate
description: "Migrate (di chuyển output) một dự án HBC v1 (layout flat) sang layout v2 per-feature + shared. dry-run plan → confirm → apply; idempotent. Use when user says 'migrate', 'migrate v1', 'di chuyển output', 'nâng cấp layout', or agent menu [MIG]."
---

# Migrate v1 → v2 (Phase 0)

## Overview

Convert a project that ran **HBC v1** (flat output: `_bmad-output/{planning-artifacts,implementation-artifacts,gates,traceability}/`, id `REQ-NNN`, 7-column matrix, old design codes `D-08`/`D-17`) to **v2**: per-feature `_bmad-output/features/<feature>/{…}/` + shared `_bmad-output/shared/{coding-standards,glossary,erd,api}/`, id `REQ-<FEAT>-NNN`, 8-column matrix, canonical design codes `D-09`/`D-16`. A one-time, **destructive** operation (moves files) → defaults to **dry-run**; only `apply` writes.

**Args:** `plan` (default — dry-run preview, writes nothing), `apply` (execute). Optional: `feature=<slug>`, `--apply`, `--force`, `-H` / `--headless` with `--strict` or `--assumptions-allowed` (see Autonomy).

Orchestrated engine: `{workflow.migrate_script}` (dry-run default, `--apply`, `--feature`, `--reprefix`, `--json`, `--timestamp`, `--force`). Determinism (move / id-only re-prefix / D-code reconcile / rebuild matrix / backup) lives in the script; judgment (which feature? shared or per-feature? split multi-feature? resolve a mixed-tree collision?) lives in the skill. The engine's `--json` shape is the **single source of truth** for `references/headless-contract.md` (B14-5) — keep them in sync.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename. Output written in `{document_output_language}`, communicate in `{communication_language}`.

## Autonomy (A5)

Separate **mechanical** from **domain** decisions. Mechanical — move routing, the 7→8-col matrix rebuild, the id-only `REQ-NNN`→`REQ-<FEAT>-NNN` re-prefix, the D-08→D-09 / D-17→D-16 D-code reconcile — are deterministic; **decide and proceed**. Domain — **which feature slug** legacy artifacts belong to, whether a multi-feature flat tree should be **split**, how to resolve a **MIXED-tree collision** (both `D-08-x` and `D-09-x` exist → which wins) — **ASK; never silently default**.

Headless resolves domain decisions two ways:
- `--strict` — stop at the first unresolved domain decision, return `blocked` with the question.
- `--assumptions-allowed` (default in CI) — take the most defensible option (use `feature=<slug>` if given; on a collision keep the existing canonical file and preserve the incoming under a timestamped suffix), log it as an `ASSUMPTION`, continue. **Never blocks on the first turn.**

## On Activation

Resolve customization, load persistent facts + config per standard BMad activation.

> No `feature` namespacing on the output — the skill **rewrites `_bmad-output/` in place**. `feature=<slug>` is used only to assign the REQ prefix + route per-feature.

> **Versioned-doc / semantic-review N/A (T2.11/T2.12).** Migrate produces **no new versioned D-xx document** and **no semantic-review artifact** — it relocates and renumbers existing ones. So per-session version bump (T2.11 anti-churn) and `semanticReview` wiring (T2.12) **do not apply**; stated N/A by design. The validators that own those concerns run on the migrated docs in Stage 5.

> **Cross-feature rebaseline is OUT OF SCOPE (B14-6).** Migrate is a one-time layout/D-code upgrade. Re-baselining across features when a core/shared model changes after Phase 3 is a **separate new engine** (`hbc-rebaseline`, spike-gated) — migrate does **not** do it.

## Headless Mode

`-H` runs `plan` (default) / `apply` non-interactively. Full I/O contract — args, return schema, blocked reasons: `references/headless-contract.md`. Headless `apply` requires `feature=<slug>` + `--apply`; the headless default = plan JSON (`--json`). Idempotent.

Blocked reasons (closed set): `feature_required` · `multi_feature_ambiguous` · `nothing_to_migrate` · `dirty_worktree`.

## Stages

### Stage 1: Detect & Classify

Run the engine in scan mode (dry-run, `--json`). Detect a valid flat layout: `planning-artifacts/D-*`, flat `implementation-artifacts/`, `gates/`, `traceability/matrix*` (7 columns), id `REQ-NNN`. Classify each artifact → **shared** vs **per-feature**. The plan also reports `dcode_rename` (old `D-08`/`D-17` files that will become `D-09`/`D-16`).

**Idempotent:** if already v2 (or nothing legacy) → report "nothing to migrate" and **stop** (headless: `blocked: nothing_to_migrate`). An **already-reconciled** D-code tree (files already `D-09`/`D-16`) yields an empty `dcode_rename` — never renamed twice.

### Stage 2: Plan (judgment)

Route:
- **shared/** → D-12 (coding-standards), D-03 (glossary), baseline D-19 (erd), D-21 (api).
- **features/<feature>/** → D-02, D-06, D-09 (was D-08), D-16 (was D-17), D-26, D-27, task-breakdown, gates, matrix.

**Resolve feature (domain → ASK):** single-project flat docs → ask the user / use `feature=<slug>` (headless missing → `blocked: feature_required`). **Multi-feature** flat docs (REQs of several features in one D-02, or >1 `D-02-*`) → the plan flags `multi_feature_suspected`; **warn** + offer to split: v1 needs one `--feature` per run (or a manual split); headless cannot infer it → `blocked: multi_feature_ambiguous`.

**MIXED D-code tree (domain → ASK).** If both an old and its canonical code exist (e.g. `D-08-arch.md` AND `D-09-arch.md`), the plan emits `dcode_collision:<old>-><new>`. Do **not** overwrite: ask the user which is authoritative; in `--assumptions-allowed` the engine keeps the existing canonical file and moves the incoming under an `.incoming-<ts>` suffix for manual reconciliation.

No double-create: if `shared/` already exists (PI has run) → leave it as is, never overwrite.

### Stage 3: Dry-run preview (default)

For the `plan` action: call the engine with `--json` (no `--apply`) → print the **full plan**: each `src → dst`, the `dcode_rename` list, the **id-only** re-prefix `reprefix_diff` (per-file `before → after`, proving years / versions / `TC-NNN` are untouched), the planned 7→8 column matrix rebuild, and `missing_from_matrix` (REQ in D-02 with no matrix row). **Writes nothing.** The user reviews, then confirms to proceed to `apply`.

### Stage 4: Apply (`apply` / `--apply`)

Only runs for the `apply` action (or `--apply`). The engine:
1. **Dirty-guard:** if the git worktree has uncommitted changes → refuse (headless: `blocked: dirty_worktree`), unless `--force`.
2. **Backup** before any move (`.archive/migrate-<ts>/`; the timestamp is **wall-clock-unique** by default so re-runs never overwrite a prior backup — B14-4).
3. Move files per the plan; **id-only re-prefix REQ** in moved D-02/D-06/D-26/D-27 **plus task-breakdown + gates** (B14-3), and **reconcile D-08→D-09 / D-17→D-16** in filenames + matrix `design_ref`.
4. **Rebuild the 8-column matrix** (insert the `feature` column).
5. Write a **decision-log** (`.decision-log.md`) of every change.

Idempotent: an artifact already at v2 / a D-code already canonical → skip.

### Stage 5: Verify & Handoff

Run the validators on the migrated artifacts + `{workflow.trace_script} --d02` (d02-sync) + readiness `[IR]` (`hbc-check-implementation-readiness`). Report pass/gaps.

> **Matrix gap after migrate (B14-1).** Migration **stays faithful** to the v1 matrix — it never fabricates rows. The plan/apply JSON already carries `missing_from_matrix`: REQ ids that D-02 defines but the matrix lacks (the classic "39/39 green but 040/041/042 never added" gap). This is NOT a migrate bug — **surface the listed REQs clearly** and **suggest running `[TRU]`** (`hbc-traceability update`) to backfill so the matrix matches D-02. Likewise, an orphan (a REQ no longer in D-02) → suggest cleanup.

Handoff (communicate in `{communication_language}`):

_"Migrate done → v2 layout (REQ-<FEAT>, 8-col matrix, D-09/D-16). If shared is still missing, run `[PI]` (`hbc-project-init`). Then continue per-feature: `[BA]` / `hbc-create-requirements` with `feature=<slug>`. Backfill any `missing_from_matrix` REQ via `[TRU]`."_

Headless: return JSON per `references/headless-contract.md` (`status`, `applied`, `moves`, `reprefix`, `dcode_rename`, `matrix`, `missing_from_matrix`, `validation`, or `blocked` + `reason`).
