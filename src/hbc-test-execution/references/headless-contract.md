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
- `"no_test_spec"` — D-27 (test specification) not found in headless mode. Required-but-missing: without the TC inventory, a "passed" result would silently hide unrun TCs, so headless blocks (interactive only warns and continues).
- `"environment_error"` — Test environment not ready.
- `"feature_required"` — headless invocation with no resolvable feature.

## Ref verification (B16-1/B16-3)

`verify-refs.py` runs in Stage 1 against the matrix + D-02 (+ optional D-19/code/D-27/D-26). It does NOT trust matrix strings: it checks referenced files exist (`missing_code_ref`/`missing_test_ref`), every D-02 REQ has a row (`missing_from_matrix`), the code matches the design (`model_drift`), and no downstream doc cites a stale D-02 (`stale_citations`). A non-empty finding means the suite is verifying the wrong substrate — fold it into the report and do not present a clean PASS over it. Under `--assumptions-allowed` (CI default) such a finding yields `FAIL`/`PARTIAL`, never a false green.
