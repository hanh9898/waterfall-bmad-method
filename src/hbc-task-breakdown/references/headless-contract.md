# Headless Contract — hbc-task-breakdown

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output resolves under `_bmad-output/features/<feature>/implementation-artifacts/`. The Phase 2 gate is also checked for this feature. |
| `--sources` | No | Comma-separated paths to D-19, D-27, D-12, D-21. If omitted, resolved by scope: D-27/D-19-override/D-21-override per-feature, D-12/D-19-baseline/D-21-baseline shared. |
| `--mode` | No | `create` (default), `update`, or `validate` |

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "_bmad-output/features/<feature>/implementation-artifacts/task-breakdown.md",
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

- `"feature_required"` — headless invocation with no resolvable feature.
- `"phase_2_gate_not_passed"` — the Phase 2 gate for this feature is not PASSED (no override in headless).
- `"no_requirements"` — D-02 not found (REQ↔task coverage cannot be checked).
- `"no_design_artifacts"` — D-19 and D-27 not found.
- `"input_insufficient"` — `--strict`: an input dimension (D-02 / D-06 paths / acceptance criteria / code-reality) is missing before generation (B4-2). `--assumptions-allowed` logs the gap and continues.
- `"mapping_unconfirmed"` — `--strict`: the source→slice mapping table was not confirmed before generation (B4-6). `--assumptions-allowed` logs the drafted mapping and continues.
- `"validation_manual_fix"` — circular dependencies or coverage gaps.

> `--strict` vs `--assumptions-allowed`: in `--assumptions-allowed` (CI default) the domain-decision blocks above instead log an `ASSUMPTION` to the decision log and continue, never blocking the first turn. B4-5 overrides are always logged regardless of mode.
