# Headless Contract — hbc-create-test-plan

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | No | Comma-separated source documents (D-02, D-06, decision-log) — also the corpus that grounds schedule dates (B9-1) |
| `--project-name` | No | Project name for output filename (default: derived from project-context.md or directory name) |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--strict` / `--assumptions-allowed` | No | Autonomy mode for domain decisions (A5). `--assumptions-allowed` is the CI default: infer + log an `ASSUMPTION` and continue. `--strict`: stop at the first domain decision (scope boundary, risk L/I, ungrounded schedule). |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

Example: `hbc-create-test-plan --headless --sources "D-02-reqs.md,D-06-flow.md" --project-name "myapp" --mode create --assumptions-allowed`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-26-project-name-test-plan.md",
  "distillate_path": "/path/to/test-plan-distillate.json",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "manual_fix_count": 0,
    "section_count": 10,
    "churn": { "revisions": 2, "threshold": 4, "high_churn": false }
  },
  "grounding": {
    "grounded": true,
    "schedule_provisional": false,
    "fabricated_dates": [],
    "technique_gaps": []
  },
  "reason": "string (only when status=blocked)"
}
```

## Status Values

- **complete** — D-26 generated and validation passed.
- **blocked** — cannot proceed without human input. `reason` describes the blocker.

## Blocked Reasons

- `"no_requirements"` — D-02 not found; cannot derive test scope.
- `"scope_unconfirmed"` — `--strict` only: the in/out-scope boundary (B9-3) needs user confirmation before generation. `--assumptions-allowed` logs the drafted boundary as an `ASSUMPTION` and continues.
- `"domain_decision"` — `--strict` only: a risk likelihood/impact (B9-2) or an ungrounded schedule date (B9-1) needs user confirmation. `--assumptions-allowed` logs an `ASSUMPTION` and continues.
- `"grounding_gap"` — `--strict` only: Stage 3a found `fabricated_dates` or `technique_gaps` (B9-1/B9-4). The return includes both lists; `--assumptions-allowed` logs them and continues.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"mode_conflict"` — existing complete D-26 found but `--mode create` specified.
- `"no_existing_d26"` — `validate`/`update` mode but no D-26 found.
- `"feature_required"` — headless invocation with no resolvable feature.
