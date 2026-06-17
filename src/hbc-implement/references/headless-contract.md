# Headless Contract — hbc-implement

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--task` | No | Specific task ID to implement (e.g., `TASK-001`) |
| `--all` | No | Implement all remaining TODO tasks |
| `--coverage` | No | Check coverage only, no implementation |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

## Return Schema

```json
{
  "status": "complete | blocked | partial",
  "tasks_completed": ["TASK-001", "TASK-002"],
  "tasks_remaining": ["TASK-003"],
  "coverage": 85.2,
  "reason": "string (only when status=blocked)"
}
```

## Blocked Reasons

- `"no_task_breakdown"` — task-breakdown.md not found.
- `"tests_failing"` — implementation cannot pass tests.
- `"coverage_below_threshold"` — coverage below configured minimum.
- `"feature_required"` — headless invocation with no resolvable feature.
