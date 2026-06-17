# Plan: `hbc-migrate` — Migrate legacy outputs → HBC v2 layout

**Status:** planned · **Author:** module-builder ideate · **Date:** 2026-06-17
**Builds:** a new first-class HBC skill wrapping/extending `_bmad/scripts/migrate-to-feature-layout.py`.

## 1. Problem & Goal

HBC v2 changed the output model:
- **Layout:** flat `_bmad-output/{planning-artifacts,implementation-artifacts,gates,traceability}/` → per-feature `_bmad-output/features/<feature>/{…}/` + shared `_bmad-output/shared/{coding-standards,glossary,erd,api}/`.
- **IDs:** `REQ-NNN` → `REQ-<FEAT>-NNN` (+ `REQ-SHARED-NNN`); TC stays `TC-NNN` but per-feature.
- **Matrix:** 7-col → 8-col (added leading `feature`).

Projects that ran HBC v1 have outputs in the OLD shape. There is a script
(`migrate-to-feature-layout.py`: dry-run default, moves flat→shared/per-feature,
`--reprefix` REQ, `--feature` default) but it is **not a first-class capability**:
no menu code, not agent-discoverable, no headless contract, no guidance/validation,
and it has gaps (single-feature only, re-prefixes REQ but not TC, doesn't rebuild
the 8-col matrix, no backup, no post-migrate validation).

**Goal:** a discoverable, guided, safe (dry-run→confirm→apply, idempotent) migration
capability that takes a v1 project to a valid v2 layout and hands off to the normal
per-feature flow.

## 2. Architecture decision

**New standalone skill `hbc-migrate`** (NOT a mode of `hbc-project-init`). Rationale:
migration is a one-time, destructive (file moves), judgment-heavy (which feature?
how to split multi-feature docs?) operation with its own dry-run→apply lifecycle —
too heavy to fold into PI. Instead, **PI hooks it**: `hbc-project-init` Stage 1
(Status) detects a legacy flat layout and recommends running `hbc-migrate` first
(before creating shared deliverables, to avoid double-creation).

Reuse: the skill orchestrates an EXTENDED `migrate-to-feature-layout.py` (+ a
`rebuild-matrix.py` helper if cleaner). Deterministic file ops live in scripts;
the feature-assignment judgment + preview/confirm live in the skill.

| Field | Value |
|---|---|
| name | `hbc-migrate` |
| menu-code | `MIG` |
| phase | `0-init` |
| action | `plan` (default, dry-run) · `apply` |
| args | `feature=<slug>` · `--apply` · `-H` |
| required | false (only relevant to v1 projects) |
| scope/output | rewrites `_bmad-output/**` in place (backup first) |

## 3. Stages

1. **Detect & Classify.** Scan for legacy flat layout (`planning-artifacts/D-*`,
   flat `implementation-artifacts/`, `gates/`, `traceability/matrix*` with 7 cols,
   `REQ-NNN` ids). Classify each artifact → shared vs per-feature. **Idempotent:**
   if already v2 (or nothing legacy) → report "nothing to migrate", stop.
2. **Plan (judgment).** Route: D-12/D-03 + baseline D-19/D-21 → `shared/`; D-02/D-06/
   D-26/D-27, task-breakdown, gates, matrix → `features/<feature>/`. **Resolve
   feature:** single project → ask/`feature=<slug>`; multi-feature flat docs →
   warn + offer split (v1: require one `--feature` per run / flag manual split).
3. **Dry-run preview (default).** Print the full plan: each `src → dst` move, the
   `REQ-NNN→REQ-<FEAT>-NNN` + `TC` re-prefix map, the 7→8-col matrix rebuild plan.
   No writes. User reviews.
4. **Apply (`apply`/`--apply`).** Git-dirty guard + backup (`.archive/<ts>/` or git
   stash note); move files; re-prefix REQ **and** TC in moved D-02/D-26/D-27/matrix;
   **rebuild matrix to 8 cols** (inject `feature` column); write decision-log of
   every change. Idempotent (skip already-v2 artifacts).
5. **Verify & Handoff.** Run the validators on migrated artifacts +
   `trace-report.py --d02` (d02-sync) + `IR` readiness; report pass/gaps; hand off
   to the per-feature flow (PI for shared if still missing, then BA/REQ per feature).

## 4. Script extensions (gaps to close in `migrate-to-feature-layout.py`)

- Re-prefix **TC-NNN** (currently only REQ).
- **Rebuild 8-col matrix** (inject `feature` column), not just re-prefix cells.
- **Multi-feature** support (currently everything → one `default` feature).
- **Backup** before move + **git-dirty guard**.
- **Post-migrate validation** hook (invoke validators / trace-report).
- Emit a structured **plan JSON** (for the dry-run preview) + **decision-log**.

## 5. Headless contract

`-H`: needs `feature=<slug>` + `--apply` to actually move. Default headless = dry-run
plan JSON. Blocked reasons (closed set): `feature_required` (can't infer feature),
`multi_feature_ambiguous` (multiple features detected — needs manual split / per-feature
runs), `nothing_to_migrate`, `dirty_worktree` (uncommitted changes — refuse to move
without `--force`).

## 6. Edge cases

- Flat D-19/D-21 → **shared baseline** (not per-feature); D-06 → per-feature.
- TC number collisions across features after split.
- Idempotency: detect already-migrated (v2) artifacts, skip them.
- A flat D-02 with REQ for several features → split (advanced) or one-feature-per-run.
- Don't double-create: if `shared/` already populated (PI ran), don't overwrite.

## 7. Registration & wiring

- `marketplace.json` skills[] += `./src/hbc-migrate`.
- `hbc-setup/assets/module-help.csv` += `[MIG]` row.
- `hbc-setup/assets/module.yaml` post-install-notes += a one-line "migrating from v1?
  run [MIG]".
- `hbc-project-init` SKILL Stage 1: detect legacy flat layout → recommend `[MIG]`.
- Docs: a `how-to/migrate-from-v1.md` (vi+en) + skills-catalog/deliverables note.

## 8. Acceptance criteria

- `hbc-migrate plan` on a v1 fixture prints a correct dry-run plan; writes nothing.
- `hbc-migrate apply feature=<slug>` produces a valid v2 layout: files relocated,
  REQ+TC re-prefixed, 8-col matrix, and the migrated artifacts PASS their validators
  + `IR` + `trace-report` d02-sync.
- Idempotent: re-running reports "nothing to migrate".
- Headless returns the documented JSON + blocked reasons.
- VM still passes (1 expected hbc-shared finding); 3-way registration consistent.

## 9. Build roadmap

1. Extend `migrate-to-feature-layout.py` (TC re-prefix, 8-col matrix rebuild,
   multi-feature, backup, plan JSON) + tests.
2. Author `src/hbc-migrate/SKILL.md` (5 stages above) + `customize.toml` +
   `references/headless-contract.md`.
3. Register (marketplace.json, module-help.csv, module.yaml) + PI hook.
4. Docs how-to (vi+en) + catalog/deliverables note.
5. Verify: tests, VM, check:docs, a v1→v2 fixture round-trip.
