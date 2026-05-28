# Headless Contract — hbc-create-coding-standards

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--framework` | No | Framework name override (e.g., `odoo`, `django`, `nextjs`). Auto-detected from project-context.md if omitted. |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--preferences` | No | Path to JSON file with team preferences (indent, naming overrides, etc.) |

Example: `hbc-create-coding-standards --headless --framework odoo --mode create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-12-project-name-coding-standards.md",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "manual_fix_count": 0,
    "section_count": 10
  },
  "framework": "odoo",
  "reason": "string (only when status=blocked)"
}
```

## Status Values

- **complete** — D-12 generated and validation passed (or auto-fixable issues resolved).
- **blocked** — cannot proceed without human input. `reason` describes the blocker.

## Blocked Reasons

- `"no_project_context"` — project-context.md not found and no `--framework` specified.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"mode_conflict"` — existing complete D-12 found but `--mode create` specified. Pass `--mode update` to revise or remove existing D-12 first.
