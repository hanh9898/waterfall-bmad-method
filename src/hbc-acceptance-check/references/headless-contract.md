# Headless Contract — hbc-acceptance-check

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--review` | No | Full acceptance review (default) |
| `--status` | No | Check current decision without re-review |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

## Return Schema

```json
{
  "status": "complete | blocked",
  "decision": "ACCEPTED | REJECTED | DEFERRED | PENDING",
  "criteria": {
    "total": 7,
    "passed": 7,
    "failed": 0,
    "skipped": 0
  },
  "traceability": {
    "total_reqs": 15,
    "designed": 15,
    "implemented": 15,
    "tested": 15,
    "coverage_pct": 100
  },
  "report_path": "_bmad-output/features/<feature>/implementation-artifacts/acceptance-report.md",
  "reason": "string"
}
```

## Blocked Reasons

- `"no_test_execution_report"` — Test execution report not found.
- `"phase_gate_failed"` — One or more phase gates not passed.
- `"insufficient_evidence"` — Cannot determine acceptance criteria.
- `"feature_required"` — headless invocation with no resolvable feature.

## Hard acceptance guards (B16-1/B16-2/B16-3)

`acceptance-guards.py` runs before any ACCEPT. A non-empty `blocking` array forbids ACCEPTED regardless of the checklist: headless then decides REJECTED (never ACCEPTED, never DEFERRED). Guard keys: `model_drift` (code never built the D-19 model), `missing_from_matrix` (a D-02 REQ with no trace row), `stale_citations` (D-27/D-26 citing a stale D-02 version). Coverage is reported as necessary-but-not-sufficient — meeting threshold does not by itself license ACCEPT.
