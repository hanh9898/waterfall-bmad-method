# Headless Contract — hbc-migrate

Migrate a **v1** project (flat `_bmad-output/`) to the **v2** per-feature + shared layout. Default headless run is a non-destructive **dry-run plan**; moving files requires `feature=<slug>` + `--apply`. Output is rewritten **in place** — no `feature` namespacing on the output root.

> **Source of truth (B14-5):** this contract mirrors the engine's `--json` output exactly. The engine (`migrate-to-feature-layout.py`) prints the shape below; this file documents it. If one changes, change both.

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `plan` | No | Default. Dry-run preview via the engine's `--json` plan. Writes nothing. |
| `apply` | No | Execute the migration (move + id-only re-prefix + D-code reconcile + matrix rebuild + decision-log). |
| `feature=<slug>` | Yes (for `apply`) | Active feature slug → `--feature`. Routes per-feature artifacts and the `REQ-<FEAT>` re-prefix. Cannot be inferred → `feature_required`. |
| `--apply` | Yes (headless apply) | Required alongside `apply` to actually move files. Absent ⇒ dry-run. |
| `--reprefix` | No | Id-only `REQ-NNN`→`REQ-<FEAT>-NNN` re-prefix in moved docs + matrix (TC ids untouched). |
| `--force` | No | Override the git dirty-worktree guard. |
| `--strict` / `--assumptions-allowed` | No | Autonomy mode for domain decisions. `--strict` blocks on the first; `--assumptions-allowed` (CI default) infers + logs + continues, never blocking the first turn. |
| `-H`, `--headless` | No | Run `plan` / `apply` non-interactively. |

Example (preview): `hbc-migrate --headless plan`
Example (execute): `hbc-migrate --headless apply feature=auth --apply --reprefix`

## Return Schema

Plan (dry-run) and apply share one shape; `applied` distinguishes them. This is the engine's `--json` object verbatim:

```json
{
  "status": "ready | migrated | nothing_to_migrate | dirty_worktree | out_not_found",
  "applied": false,
  "feature": "auth",
  "moves": [{ "src": "_bmad-output/planning-artifacts/D-08-arch.md",
              "dst": "_bmad-output/features/auth/planning-artifacts/D-09-arch.md" }],
  "reprefix": { "REQ-001": "REQ-AUTH-001" },
  "reprefix_diff": [{ "file": "D-02-x.md",
                      "before": ["REQ-001"], "after": ["REQ-AUTH-001"] }],
  "dcode_rename": [{ "from": "D-08-arch.md", "to": "D-09-arch.md", "collision": false }],
  "matrix": { "from_cols": 7, "to_cols": 8, "rebuilt": true },
  "missing_from_matrix": ["REQ-AUTH-002"],
  "backup": "_bmad-output/.archive/migrate-20260622-101500/",
  "decision_log": "_bmad-output/.decision-log.md",
  "validation": { "valid": null, "gaps": [] },
  "warnings": ["multi_feature_suspected", "dcode_collision:D-08-arch.md->D-09-arch.md"],
  "reason": null
}
```

For `plan` (dry-run): `applied=false`, `backup`/`decision_log` null, `matrix.rebuilt=false` (planned only). `reprefix`/`reprefix_diff` are populated only with `--reprefix`. `validation.valid` is null until Stage 5 validators run (the engine does not validate).

## Status / Blocked Mapping

The engine's `status` maps to the agent-facing **complete / blocked** as follows:

- **complete** — `status: ready` (a valid dry-run plan emitted, nothing written) or `status: migrated` (files relocated, REQ re-prefixed id-only, D-08/D-17 reconciled to D-09/D-16, 8-col matrix rebuilt, backup + decision-log written).
- **blocked** — `reason` describes the blocker; the agent surfaces it for human input.

## Blocked Reasons

Closed set (the engine emits the matching `status`/`reason`; the agent adds `feature_required` / `multi_feature_ambiguous` from the plan):
- `"feature_required"` — `apply` requested but no `feature=<slug>` and it cannot be inferred. (Agent-side: refuse apply without a slug.)
- `"multi_feature_ambiguous"` — plan `warnings` contains `multi_feature_suspected`; needs a manual split or one `--feature` per run. In `--strict` the agent blocks; in `--assumptions-allowed` it proceeds with the given `feature` and logs an ASSUMPTION.
- `"nothing_to_migrate"` — engine `status: nothing_to_migrate`; already v2 (or no legacy artifacts). Idempotent stop.
- `"dirty_worktree"` — engine `status: dirty_worktree` (exit 3); uncommitted git changes, refuse to move without `--force`.

> A `dcode_collision:*` warning (MIXED tree) is a **domain decision**, not a hard block: `--strict` asks the user; `--assumptions-allowed` keeps the existing canonical file and preserves the incoming under an `.incoming-<ts>` suffix.
