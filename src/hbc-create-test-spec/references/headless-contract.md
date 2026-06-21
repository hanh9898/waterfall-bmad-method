# Headless Contract — hbc-create-test-spec

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | No | Comma-separated file paths to source documents (D-26, D-02, D-19, D-06) |
| `--code-dir` | No | Code tree to reconcile TCs against (B3-7 model_drift, Stage 3a) |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--strict` / `--assumptions-allowed` | No | Autonomy mode for domain decisions (A5). `--assumptions-allowed` is the CI default: infer + log + continue, never block the first turn. `--strict`: stop at the first unresolved domain decision. |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

Example: `hbc-create-test-spec --headless --sources "D-26-plan.md,D-02-reqs.md,D-19-er.md" --code-dir code/ --mode create --assumptions-allowed`

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
- `"scope_unconfirmed"` — `--strict`: per-REQ facet/edge in/out-scope not confirmed before generation (B3-4 hard gate). `--assumptions-allowed` logs the drafted boundary and continues.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"zero_coverage"` — some REQ-xxx IDs have no test cases.
- `"grounding_unreconciled"` — `--strict`: Stage 3a returned model_drift / ungrounded test-data / sanity gaps (B3-1/B3-2/B3-7) not yet reconciled. `--assumptions-allowed` logs and continues (advisory).
- `"no_existing_d27"` — `validate`/`update` with no D-27 found.
- `"mode_conflict"` — existing complete D-27 found but `--mode create` specified.
- `"feature_required"` — headless invocation with no resolvable feature.
