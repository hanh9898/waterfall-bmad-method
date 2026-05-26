# Phase 3: Implementation — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P3-01 | Task breakdown document exists | FILE | yes | _hbc_output/impl/task-breakdown* | | hbc-create-task-breakdown |
| P3-02 | All tasks completed | CONTENT | yes | _hbc_output/impl/task-breakdown* | No rows with status TODO or IN_PROGRESS remaining. All tasks should show DONE. | |
| P3-03 | Test coverage meets threshold | METRIC | yes | _hbc_output/impl/coverage-report* | Coverage percentage >= {coverage_threshold}%. Extract the overall coverage number and compare. | |
| P3-04 | All unit tests passing | QUALITY | yes | _hbc_output/impl/test-results* | Test results show no failures. If no test results artifact exists, ask user to run tests and provide results. | |
| P3-05 | Code follows D-12 coding standards | QUALITY | no | _hbc_output/design/D-12-* | Spot-check implementation code against D-12 standards. Flag obvious violations in naming, formatting, or patterns. | |
| P3-06 | E2E test scripts exist (if D-26 specifies E2E) | FILE | no | _hbc_output/impl/e2e-* | | |
