# Headless Contract — hbc-task-breakdown

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | No | Comma-separated paths to D-19, D-27, D-12, D-21 |
| `--mode` | No | `create` (default), `update`, or `validate` |

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/task-breakdown.md",
  "validation": {
    "valid": true,
    "total_tasks": 15,
    "entity_coverage_pct": 100,
    "test_coverage_pct": 100
  },
  "reason": "string (only when status=blocked)"
}
```

## Blocked Reasons

- `"no_design_artifacts"` — D-19 and D-27 not found.
- `"validation_manual_fix"` — circular dependencies or coverage gaps.
