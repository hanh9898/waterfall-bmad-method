# Headless Contract — hbc-create-api-spec

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | No | Comma-separated file paths to source documents (D-02, D-19, OpenAPI files) |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--skip` | No | If present, mark D-21 as intentionally skipped (project has no API) |
| `feature` | No | `feature=<slug>` (optional): when set, output resolves to the per-feature override `_bmad-output/features/<feature>/planning-artifacts/`; when absent, the shared baseline `_bmad-output/shared/api/` — path-existence precedence |

Example: `hbc-create-api-spec --headless --sources "D-02-reqs.md,D-19-db.md" --mode create`

## Return Schema

```json
{
  "status": "complete | blocked | skipped",
  "output_path": "_bmad-output/shared/api/D-21-project-name-api-spec.md (shared baseline) | _bmad-output/features/<feature>/planning-artifacts/D-21-project-name-api-spec.md (per-feature override)",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "manual_fix_count": 0,
    "endpoint_count": 12
  },
  "reason": "string (only when status=blocked or skipped)"
}
```

## Status Values

- **complete** — D-21 generated and validation passed.
- **blocked** — cannot proceed without human input. `reason` describes the blocker.
- **skipped** — project confirmed as not needing API specification.

## Blocked Reasons

- `"no_requirements"` — D-02 not found; cannot derive endpoints.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"api_necessity_unclear"` — cannot determine if project needs API; human input required.
- `"mode_conflict"` — existing complete D-21 found but `--mode create` specified.
