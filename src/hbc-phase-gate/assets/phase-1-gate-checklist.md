# Phase 1: Analysis — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P1-01 | D-02 Requirements document exists | FILE | yes | {output_folder}/features/{feature}/planning-artifacts/D-02-* | | hbc-create-requirements |
| P1-02 | D-02 contains requirement IDs | CONTENT | yes | {output_folder}/features/{feature}/planning-artifacts/D-02-* | REQ-(?:[A-Z0-9]+-)?\d{3,} | hbc-create-requirements |
| P1-03 | D-03 Glossary document exists | FILE | yes | {output_folder}/shared/glossary/D-03-* | | hbc-create-glossary |
| P1-04 | D-06 Business Flow document exists | FILE | yes | {output_folder}/features/{feature}/planning-artifacts/D-06-* | | hbc-create-business-flow-diagram |
| P1-05 | D-06 contains Mermaid flowcharts | CONTENT | yes | {output_folder}/features/{feature}/planning-artifacts/D-06-* | ```mermaid | hbc-create-business-flow-diagram |
| P1-05b | D-06 semantic review completed (R-1/#5) | REVIEW | yes | {output_folder}/features/{feature}/planning-artifacts/D-06-* | | hbc-create-business-flow-diagram |
| P1-06 | Requirements traceable to business flows | QUALITY | yes | {output_folder}/features/{feature}/planning-artifacts/D-02-*,{output_folder}/features/{feature}/planning-artifacts/D-06-* | Each REQ-xxx should map to at least one business flow. Check cross-references between D-02 requirements and D-06 flow diagrams. | |
| P1-06b | D-06 covers every PRD functional requirement (D3) | QUALITY | yes | {output_folder}/features/{feature}/planning-artifacts/D-06-* | Run `check-fr-coverage.py --prd <PRD> --d06 <D-06> -o <tmp>` (hbc-create-business-flow-diagram) — `passed` must be true (no uncovered FR-ids, no phantom flows). This re-runs the deterministic coverage check at the gate, catching PRD churn after D-06 was authored. | hbc-create-business-flow-diagram |
| P1-07 | No vague or unmeasurable requirements | QUALITY | no | {output_folder}/features/{feature}/planning-artifacts/D-02-* | Requirements should be specific and testable. Flag any containing vague terms like 'fast', 'easy', 'user-friendly' without measurable criteria. | |
