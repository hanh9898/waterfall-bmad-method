# Phase 4: Testing — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P4-01 | Test execution report exists | FILE | yes | {output_folder}/implementation-artifacts/test-execution-report* | | hbc-test-execution |
| P4-02 | All specified test cases executed (D-27 ↔ report, D1) | QUALITY | yes | {output_folder}/implementation-artifacts/test-execution-report*,{output_folder}/planning-artifacts/D-27-* | Run `validate-test-execution.py <report> --d27 <D-27>` (hbc-test-execution) — there must be NO `TC_UNEXECUTED` issues (every TC specified in D-27 has a result) and no `TC_PHANTOM_RESULT`. This is the deterministic mirror of the Phase 2 D-02↔D-27 seam, one phase later — do not pass on an eyeballed count. | hbc-test-execution |
| P4-03 | No critical defects open | CONTENT | yes | {output_folder}/implementation-artifacts/test-execution-report* | No rows with classification 'critical' or 'blocker' in failed state. | |
| P4-04 | Acceptance report exists | FILE | yes | {output_folder}/implementation-artifacts/acceptance-report* | | hbc-acceptance-check |
| P4-05 | Acceptance decision is ACCEPTED or DEFERRED | CONTENT | yes | {output_folder}/implementation-artifacts/acceptance-report* | status:\s*(ACCEPTED\|DEFERRED) | hbc-acceptance-check |
| P4-06 | Traceability matrix fully populated | QUALITY | yes | {output_folder}/traceability/matrix* | Every row in the traceability matrix should have non-empty values in: req_id, design_ref, code_ref, test_ref. Report any rows with empty cells. | hbc-traceability |
| P4-07 | All previous gates PASSED | CONTENT | yes | {output_folder}/gates/phase-1-gate*,{output_folder}/gates/phase-2-gate*,{output_folder}/gates/phase-3-gate* | Each gate report must contain **Status:** PASSED (not FAILED or WARNING). | |
