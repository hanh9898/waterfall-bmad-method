# Headless Contract — hbc-test-execution

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--suite` | No | Test suite to execute: `all` (default), `unit`, `integration`, `e2e` |
| `--report-only` | No | Generate report from existing results without executing |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature output paths resolve under `_bmad-output/features/<feature>/...` |

## Return Schema

```json
{
  "status": "PASS | FAIL | PARTIAL",
  "summary": {
    "total": 50,
    "passed": 48,
    "failed": 2,
    "skipped": 0,
    "coverage_pct": 85.2
  },
  "defects": [
    {
      "defect_id": "DEF-001",
      "test_id": "test_user_creation",
      "tc_ref": "TC-001",
      "classification": "code_bug",
      "action": "Return to Phase 3"
    }
  ],
  "report_path": "_bmad-output/features/<feature>/implementation-artifacts/test-execution-report.md",
  "reason": "string (only when status != PASS)"
}
```

## Status Definitions

- `PASS` — All tests passed, coverage meets threshold.
- `FAIL` — One or more tests failed.
- `PARTIAL` — Some test suites could not run (environment issue).

## Blocked Reasons

- `"no_test_runner"` — Test command not found or not configured.
- `"no_tests_found"` — No test files detected.
- `"environment_error"` — Test environment not ready.
- `"feature_required"` — headless invocation with no resolvable feature.
