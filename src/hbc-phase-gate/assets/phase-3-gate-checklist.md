# Phase 3: Implementation — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P3-00 | Phase 1 and Phase 2 gates PASSED | CONTENT | yes | _bmad-output/gates/phase-1-gate*,_bmad-output/gates/phase-2-gate* | Status:.*PASSED | |
| P3-01 | Task breakdown document exists | FILE | yes | _bmad-output/implementation-artifacts/task-breakdown* | | hbc-create-task-breakdown |
| P3-02 | All tasks completed | CONTENT | yes | _bmad-output/implementation-artifacts/task-breakdown* | No rows with status TODO or IN_PROGRESS remaining. All tasks should show DONE. | |
| P3-03 | Test coverage meets threshold | METRIC | yes | _bmad-output/implementation-artifacts/coverage-report* | Coverage percentage >= {coverage_threshold}%. Extract the overall coverage number and compare. If no coverage artifact exists, guide the user: run `pytest --cov=. --cov-report=html:_bmad-output/implementation-artifacts/coverage-report` (or framework equivalent) and re-run gate. | |
| P3-04 | All unit tests passing | QUALITY | yes | _bmad-output/implementation-artifacts/test-results* | Test results show no failures. If no test results artifact exists, guide the user: run `pytest --tb=short > _bmad-output/implementation-artifacts/test-results.txt` (or framework equivalent) and re-run gate. | |
| P3-05 | Code follows D-12 coding standards | QUALITY | no | _bmad-output/planning-artifacts/D-12-* | Spot-check implementation code against D-12 standards. Flag obvious violations in naming, formatting, or patterns. | |
| P3-06 | E2E test scripts exist (if D-26 specifies E2E) | FILE | no | _bmad-output/implementation-artifacts/e2e-* | | |
