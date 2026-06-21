# Headless Contract — hbc-create-requirements

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | Yes | Comma-separated file paths to source documents |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--vague-terms` | No | Comma-separated custom vague terms (overrides config) |
| `--strict` / `--assumptions-allowed` | No | Autonomy mode for domain decisions (A5). `--strict` blocks at the first unresolved domain decision; `--assumptions-allowed` (default in CI) logs an ASSUMPTION and continues, never blocking the first turn. See SKILL.md › Autonomy. |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

Brownfield is auto-derived (no arg): if the source scan finds a `project_context`, the run is brownfield and the validator is invoked with `--brownfield` (grounding becomes blocking). See `references/brownfield-grounding.md` for the headless grounding rule.

Example: `hbc-create-requirements --headless --sources "brief.md,interviews.md" --mode create`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-02-project-name.md",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "auto_fixable_count": 0,
    "auto_fixes": [],
    "manual_fix_count": 0,
    "req_count": 15
  },
  "brownfield": false,
  "reason": "string (only when status=blocked)"
}
```

## Status Values

- **complete** — D-02 generated and validation passed (or auto-fixable issues resolved).
- **blocked** — cannot proceed without human input. `reason` describes the blocker.

## Blocked Reasons

- `"no_source_documents"` — no inputs provided and none discoverable.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"empty_discovery"` — source documents contain insufficient information to extract requirements.
- `"infeasible"` — the ① Feasibility step (B1-5) judged the idea unbuildable against the source/framework; killed early before discovery. Only under `--strict`; `--assumptions-allowed` logs the risk and continues. See `references/intake-pipeline.md`.
- `"domain_decision"` — `--strict` only: an unresolved domain decision (scope boundary, NFR number, ambiguous REQ) needs human input. `--assumptions-allowed` logs an ASSUMPTION instead.
- `"mode_conflict"` — existing complete D-02 found but `--mode create` specified. Pass `--mode update` to revise or remove existing D-02 first.
- `"feature_required"` — headless invocation with no resolvable feature.
- `"brownfield_ungrounded"` — brownfield run where a `CHANGE`/`REMOVE` ask can't be grounded against the existing system (no catalog anchor / delta needs judgment), so a `BROWNFIELD_*` finding would block. The validator's `BROWNFIELD_NO_EXISTING_REF` / `NO_CHANGE_SPEC` / `NO_CHANGE_TYPE` issues appear under `validation`.
