# Phase 2: Design — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P2-00 | Phase 1 gate PASSED | CONTENT | yes | _bmad-output/gates/phase-1-gate* | Status:.*PASSED | |
| P2-01 | D-19 Database Design document exists | FILE | yes | _bmad-output/planning-artifacts/D-19-* | | hbc-create-er-diagram |
| P2-02 | D-19 contains ER diagram | CONTENT | yes | _bmad-output/planning-artifacts/D-19-* | erDiagram | hbc-create-er-diagram |
| P2-03 | D-19 contains table definitions | CONTENT | yes | _bmad-output/planning-artifacts/D-19-* | \|[-:]+\|[-:]+\|[-:]+\| | hbc-create-er-diagram |
| P2-04 | D-12 Coding Standards document exists | FILE | yes | _bmad-output/planning-artifacts/D-12-* | | hbc-create-coding-standards |
| P2-05 | D-26 Test Plan document exists | FILE | yes | _bmad-output/planning-artifacts/D-26-* | | hbc-create-test-plan |
| P2-06 | D-27 Test Specification document exists | FILE | yes | _bmad-output/planning-artifacts/D-27-* | | hbc-create-test-spec |
| P2-07 | D-27 contains test case IDs | CONTENT | yes | _bmad-output/planning-artifacts/D-27-* | TC-\d{3} | hbc-create-test-spec |
| P2-08 | Test coverage — every REQ has at least one TC | QUALITY | yes | _bmad-output/planning-artifacts/D-02-*,_bmad-output/planning-artifacts/D-27-* | Cross-reference REQ-xxx IDs from D-02 against TC-xxx entries in D-27. Every REQ-xxx must appear as a reference in at least one test case. Report any uncovered requirements. | |
| P2-09 | D-21 API Specification exists (if applicable) | FILE | no | _bmad-output/planning-artifacts/D-21-* | | hbc-create-api-spec |
| P2-10 | Design references trace to requirements | QUALITY | yes | _bmad-output/planning-artifacts/D-19-*,_bmad-output/planning-artifacts/D-02-* | D-19 entities and tables should trace back to D-02 requirements. No orphan entities that serve no requirement. | |
