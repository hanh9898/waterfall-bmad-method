# Headless Contract — hbc-migrate

Migrate a **v1** project (flat `_bmad-output/`) to the **v2** per-feature + shared layout. Default headless run is a non-destructive **dry-run plan**; moving files requires `feature=<slug>` + `--apply`. Output is rewritten **in place** — no `feature` namespacing on the output root.

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `plan` | No | Default. Dry-run preview via the engine's `--json` plan. Writes nothing. |
| `apply` | No | Execute the migration (move + re-prefix + matrix rebuild + decision-log). |
| `feature=<slug>` | Yes (for `apply`) | Active feature slug. Routes per-feature artifacts and the `REQ-<FEAT>` / `TC` re-prefix. Cannot be inferred → `feature_required`. |
| `--apply` | Yes (headless apply) | Required alongside `apply` headless to actually move files. Absent ⇒ dry-run. |
| `--force` | No | Override the git dirty-worktree guard. |
| `-H`, `--headless` | No | Run `plan` / `apply` non-interactively. |

Example (preview): `hbc-migrate --headless plan`
Example (execute): `hbc-migrate --headless apply feature=auth --apply`

## Return Schema

Plan (dry-run) and apply share one shape; `applied` distinguishes them.

```json
{
  "status": "complete | blocked",
  "applied": false,
  "feature": "auth",
  "moves": [{ "src": "_bmad-output/planning-artifacts/D-02-x.md",
              "dst": "_bmad-output/features/auth/planning-artifacts/D-02-x.md" }],
  "reprefix": { "REQ-001": "REQ-AUTH-001", "TC-001": "TC-001" },
  "matrix": { "from_cols": 7, "to_cols": 8, "rebuilt": true },
  "backup": "_bmad-output/.archive/20260617-101500/",
  "decision_log": "/path/to/.decision-log.md",
  "validation": { "valid": true, "gaps": [] },
  "reason": "string (only when status=blocked)"
}
```

For `plan`: `applied=false`, `backup`/`decision_log` null, `matrix.rebuilt=false` (planned only).

## Status Values

- **complete** — `plan`: a valid dry-run plan emitted (nothing written). `apply`: files relocated, REQ+TC re-prefixed, 8-col matrix rebuilt, validators passed.
- **blocked** — cannot proceed without human input; `reason` describes the blocker.

## Blocked Reasons

Closed set:
- `"feature_required"` — `apply` requested but no `feature=<slug>` and it cannot be inferred.
- `"multi_feature_ambiguous"` — multiple features detected in flat docs; needs manual split or one `--feature` per run.
- `"nothing_to_migrate"` — already v2 (or no legacy artifacts found). Idempotent stop.
- `"dirty_worktree"` — uncommitted git changes; refuse to move without `--force`.
