# Headless Contract — hbc-rebaseline

Re-baseline cross-feature when a shared / core model changes after Phase 3. Default headless run is a non-destructive **dry-run plan**; writing the baseline-change envelope requires `changed=<model.token>` + `--apply`. A SEPARATE engine from `hbc-migrate` (B14-6) — same dry-run→apply discipline, no shared code.

> **Source of truth:** this contract mirrors the engine's `--json` output exactly. The engine (`rebaseline.py`) prints the shape below; this file documents it. If one changes, change both.

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `plan` | No | Default. Dry-run blast-radius plan. Writes nothing. |
| `apply` | No | Write the baseline-change envelope (plan JSON + decision-log). |
| `changed=<model.token>` | Yes (for a plan) | The shared model that changed (e.g. `project.project`) → `--changed`. Absent ⇒ discovery mode (shared candidates only). |
| `change-id=<id>` | No | Names the baseline-change epic (unit-of-change above feature) → `--change-id`. Default `baseline-change`. |
| `--apply` | Yes (headless apply) | Required alongside `apply` to write the envelope. Absent ⇒ dry-run. |
| `--strict` / `--assumptions-allowed` | No | Autonomy mode. `--strict` blocks on the first domain decision; `--assumptions-allowed` (CI default) infers + logs + continues, never blocking the first turn. |
| `-H`, `--headless` | No | Run `plan` / `apply` non-interactively. |

Map to the engine CLI: `--root {workflow.features_dir}`, `--changed <token>`, `--change-id <id>`, `--apply`, `--out-root {output_folder}`.

Example (discover): `rebaseline.py --root _bmad-output/features`
Example (plan): `rebaseline.py --root _bmad-output/features --changed project.project --change-id bc-2026-06`
Example (apply): `rebaseline.py --root _bmad-output/features --changed project.project --change-id bc-2026-06 --apply --out-root _bmad-output`

## Return Schema

Plan (dry-run) and apply share one shape; `applied` (and `skipped`/`envelope` on apply) distinguish them. This is the engine's `--json` object verbatim:

```json
{
  "change_id": "bc-2026-06",
  "changed_node": "project.project",
  "owners": [],
  "shared_candidates": { "project.project": ["feature-a", "feature-b"] },
  "blast_radius": [
    { "feature": "feature-a", "owns_changed": false,
      "stale_artifacts": ["D-19", "matrix", "task-breakdown", "gate"],
      "code_references_changed": true, "verdict": "rebaseline" }
  ],
  "affected_features": ["feature-a", "feature-b"],
  "applied": false,
  "warnings": []
}
```

On `apply`: `applied=true`, plus `skipped` (true when an identical envelope already existed — idempotent) and `envelope` (the written `baseline-change/<id>/` path). Discovery mode (no `changed`) returns `{root, features, shared_candidates, hint}` instead of a plan.

## Status / Blocked Mapping

- **complete** — a plan emitted (dry-run, nothing written) or the envelope written (`applied=true`). An idempotent re-apply (`skipped=true`) is also complete.
- **blocked** — `reason` describes the blocker; the agent surfaces it for human input.

## Blocked Reasons

Closed set:
- `"changed_required"` — `apply` (or a plan) requested but no `changed=<model.token>`. (Agent-side: refuse without a token; run discovery mode to suggest candidates.)
- `"empty_blast_radius"` — engine `warnings` contains `empty_blast_radius`; nothing references the token. Verify the model name. In `--strict` block; in `--assumptions-allowed` report empty + stop (nothing to do).
- `"not_cross_feature_shared"` — engine `warnings` contains `not_cross_feature_shared`; only one feature touches the token (it is not genuinely shared). In `--strict` ask the user to confirm; in `--assumptions-allowed` proceed treating `changed=` as authoritative + log an ASSUMPTION.
- `"root_not_found"` — engine exits 2 (`--root` missing, or no feature carries a D-02). Idempotent stop.

> Exit codes: `0` plan/discovery emitted · `2` root not found / no feature with a D-02.
