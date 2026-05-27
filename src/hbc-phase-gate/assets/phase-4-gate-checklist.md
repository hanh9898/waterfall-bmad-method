# Phase 4: Testing — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P4-01 | Test execution report exists | FILE | yes | _hbc_output/test/test-execution-report* | | hbc-test-execution |
| P4-02 | All test cases executed | QUALITY | yes | _hbc_output/test/test-execution-report*,_hbc_output/design/D-27-* | Compare executed test case count against D-27 total test cases. All TC-xxx from D-27 should appear in execution report. | |
| P4-03 | No critical defects open | CONTENT | yes | _hbc_output/test/test-execution-report* | No rows with classification 'critical' or 'blocker' in failed state. | |
| P4-04 | Acceptance report exists | FILE | yes | _hbc_output/test/acceptance-report* | | hbc-acceptance-review |
| P4-05 | Acceptance decision is ACCEPTED or DEFERRED | CONTENT | yes | _hbc_output/test/acceptance-report* | status:\s*(ACCEPTED\|DEFERRED) | hbc-acceptance-review |
| P4-06 | Traceability matrix fully populated | QUALITY | yes | _hbc_output/traceability/matrix* | Every row in the traceability matrix should have non-empty values in: req_id, design_ref, code_ref, test_ref. Report any rows with empty cells. | hbc-traceability |
| P4-07 | All previous gates PASSED | FILE | yes | _hbc_output/gates/phase-1-gate*,_hbc_output/gates/phase-2-gate*,_hbc_output/gates/phase-3-gate* | | |
