# Headless Contract — hbc-create-test-spec

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | No | Comma-separated file paths to source documents (D-26, D-02, D-19, D-06) |
| `--mode` | No | `create` (default), `update`, or `validate` |

Example: `hbc-create-test-spec --headless --sources "D-26-plan.md,D-02-reqs.md" --mode create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-27-project-name-test-spec.md",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "manual_fix_count": 0,
    "tc_count": 45,
    "req_coverage_pct": 100
  },
  "reason": "string (only when status=blocked)"
}
```

## Blocked Reasons

- `"no_requirements"` — D-02 not found; cannot derive test cases.
- `"no_test_plan"` — D-26 not found; test strategy unknown.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"zero_coverage"` — some REQ-xxx IDs have no test cases.
- `"mode_conflict"` — existing complete D-27 found but `--mode create` specified.
