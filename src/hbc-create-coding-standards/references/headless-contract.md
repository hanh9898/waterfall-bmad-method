# Headless Contract — hbc-create-coding-standards

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--framework` | No | Framework name override (e.g., `odoo`, `django`, `nextjs`). Auto-detected from project-context.md if omitted. |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--preferences` | No | Path to JSON file with team preferences (indent, naming overrides, etc.) |
| `--code-dir` | No | First-party source dir for the Stage 3a code-grounding reconcile (deviations + spec-ref leaks). |
| `--strict` | No | Autonomy: block at the first unresolved domain decision (returns `blocked`). |
| `--assumptions-allowed` | No | Autonomy (CI default): infer the framework default, log it as an `ASSUMPTION`, continue. Never blocks the first question. |

Example: `hbc-create-coding-standards --headless --framework odoo --mode create --assumptions-allowed`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-12-project-name-coding-standards.md",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "section_count": 11,
    "churn": { "revisions": 0, "threshold": 4, "high_churn": false }
  },
  "reconcile": {
    "grounded": true,
    "deviations": [],
    "spec_ref_leak_count": 0
  },
  "framework": "odoo",
  "semanticReview": { "status": "pending | passed", "openFacets": [] },
  "assumptions": [],
  "reason": "string (only when status=blocked)"
}
```

## Status Values

- **complete** — D-12 generated and validation passed (or auto-fixable issues resolved).
- **blocked** — cannot proceed without human input. `reason` describes the blocker.

## Blocked Reasons

- `"no_project_context"` — project-context.md not found and no `--framework` specified.
- `"domain_decision"` — `--strict`: an unresolved team-preference / deviation decision (B10-3). `reason` carries the question. (`--assumptions-allowed` never raises this.)
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"preference_conflict"` — update mode: a preference change clashes with the existing standard.
- `"no_existing_d12"` — `validate` mode but no D-12 found.
- `"mode_conflict"` — existing complete D-12 found but `--mode create` specified. Pass `--mode update` to revise.
