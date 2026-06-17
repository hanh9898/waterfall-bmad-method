# Headless Contract — hbc-create-requirements

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | Yes | Comma-separated file paths to source documents |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--vague-terms` | No | Comma-separated custom vague terms (overrides config) |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

Example: `hbc-create-requirements --headless --sources "brief.md,interviews.md" --mode create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-02-project-name.md",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "auto_fixes": [],
    "manual_fix_count": 0,
    "req_count": 15
  },
  "reason": "string (only when status=blocked)"
}
```

## Status Values

- **complete** — D-02 generated and validation passed (or auto-fixable issues resolved).
- **blocked** — cannot proceed without human input. `reason` describes the blocker.

## Blocked Reasons

- `"no_source_documents"` — no inputs provided and none discoverable.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"empty_discovery"` — source documents contain insufficient information to extract requirements.
- `"mode_conflict"` — existing complete D-02 found but `--mode create` specified. Pass `--mode update` to revise or remove existing D-02 first.
- `"feature_required"` — headless invocation with no resolvable feature.
