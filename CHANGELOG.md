# Changelog

All notable changes to the **HBLAB BMad Custom (HBC)** module. Versions follow
[Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH. A **BREAKING** entry
under a MINOR bump is, per HBC policy, always accompanied by an automated, idempotent
`[MIG]` migration path so existing-HBC consumer projects can upgrade without manual edits.

## [2.1.0] — 2026-06-22

### BREAKING — design D-code reconcile (D-08 → D-09, D-17 → D-16)

The pre-reconcile HBC assigned design documents codes that **collided** with the
canonical HBLAB numbering. They are now reconciled to the canonical codes:

| Document            | Old code | New (canonical) code |
| ------------------- | -------- | -------------------- |
| Architecture Design | `D-08`   | **`D-09`**           |
| Behavioral Design   | `D-17`   | **`D-16`**           |

This is a **breaking change for any project that already ran HBC**: its per-feature
artifacts are named `D-08-*` / `D-17-*` and its traceability matrix `design_ref` cells
reference those codes.

#### Migration path (required for existing projects)

Run **`[MIG]` (`hbc-migrate`)** — dry-run → confirm → apply. The migration:

- Renames per-feature `D-08-*` → `D-09-*` and `D-17-*` → `D-16-*`.
- Rewrites matrix `design_ref` cells `D-08`/`D-17` → `D-09`/`D-16` (the matrix does **not** break).
- Is **idempotent**: an already-reconciled tree (already `D-09`/`D-16`) is detected and
  **skipped — never renamed twice**. A **MIXED** tree (some old, some new) is reconciled
  to all-canonical; a same-target filename **collision** is flagged (`dcode_collision`)
  and left for human resolution rather than silently overwritten.
- Emits a **dry-run diff** before any write, and a `.decision-log.md` of every change.

> Cross-feature **rebaseline** (re-baselining when a shared/core model changes after
> Phase 3) is **out of scope** for migrate and is a separate, spike-gated engine
> (`hbc-rebaseline`). Migrate is a one-time layout + D-code upgrade only.

### Fixed — `hbc-migrate` correctness (T1.7)

- **B14-1** Migrate now emits `missing_from_matrix` (REQ ids defined in D-02 but absent
  from the traceability matrix) in both dry-run and apply output, using the shared
  `hbc_validation` primitive — traceability gaps surface instead of hiding behind a
  "green" migrate. Faithful: migrate never fabricates matrix rows.
- **B14-2** The `REQ-NNN` → `REQ-<FEAT>-NNN` re-prefix is now strictly **id-only** — bare
  years, version numbers, and `TC-NNN` ids are never over-matched — and a per-file
  **dry-run diff** (`before → after`) is shown before apply.
- **B14-3** Implementation artifacts (`task-breakdown`) and gate files are now re-prefixed
  correctly on move (previously only the planning D-docs were).
- **B14-4** Dirty-worktree guard plus **timestamp-unique** backup folders — a re-run can no
  longer overwrite a prior `.archive/migrate-<ts>/` backup.
- **B14-5** The headless **contract and engine JSON are kept in sync**; the engine's
  `--json` shape is the documented single source of truth.

### Added

- **A5 autonomy** for `hbc-migrate`: mechanical decisions proceed deterministically;
  domain decisions (feature slug, multi-feature split, mixed-tree collision) **ASK**.
  Headless `--strict` blocks on the first domain decision; `--assumptions-allowed`
  (CI default) infers, logs an `ASSUMPTION`, and continues — never blocking the first turn.

### Notes

- `hbc-migrate` produces no new versioned D-xx document and no semantic-review artifact,
  so per-session version-bump (anti-churn) and `semanticReview` wiring are **N/A** by design.
