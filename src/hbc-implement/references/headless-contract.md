# Headless Contract — hbc-implement

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--task` | No | Specific task ID to implement (e.g., `TASK-001`) |
| `--all` | No | Implement all remaining TODO tasks |
| `--coverage` | No | Check coverage only, no implementation |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |
| `--strict` / `--assumptions-allowed` | No | Domain-decision policy (see SKILL.md Autonomy). Default in CI: `--assumptions-allowed` (infer + log ADR + continue; never block first turn). |

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
- `"stale_design"` — the task-breakdown cites a design version older than the live design (B5-4); re-derive the breakdown before implementing.
- `"tests_failing"` — implementation cannot pass tests.
- `"coverage_below_threshold"` — coverage below configured minimum.
- `"domain_decision"` — `--strict` only: an unresolved business/domain decision (B5-10); the question is in `reason`.
- `"feature_required"` — headless invocation with no resolvable feature.
