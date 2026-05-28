# Headless Contract — hbc-create-test-plan

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | No | Comma-separated file paths to source documents (D-02, D-06) |
| `--project-name` | No | Project name for output filename (default: derived from project-context.md or directory name) |
| `--mode` | No | `create` (default), `update`, or `validate` |

Example: `hbc-create-test-plan --headless --sources "D-02-reqs.md,D-06-flow.md" --project-name "myapp" --mode create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-26-project-name-test-plan.md",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "manual_fix_count": 0,
    "section_count": 10
  },
  "reason": "string (only when status=blocked)"
}
```

## Blocked Reasons

- `"no_requirements"` — D-02 not found; cannot derive test scope.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"mode_conflict"` — existing complete D-26 found but `--mode create` specified.
