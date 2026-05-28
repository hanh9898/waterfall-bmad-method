# Phase 1: Analysis — Gate Checklist

| item_id | description | type | required | artifact_pattern | criteria | skill_to_create |
|---------|-------------|------|----------|------------------|----------|-----------------|
| P1-01 | D-02 Requirements document exists | FILE | yes | _bmad-output/planning-artifacts/D-02-* | | hbc-create-requirements |
| P1-02 | D-02 contains requirement IDs | CONTENT | yes | _bmad-output/planning-artifacts/D-02-* | REQ-\d{3} | hbc-create-requirements |
| P1-03 | D-03 Glossary document exists | FILE | yes | _bmad-output/planning-artifacts/D-03-* | | hbc-create-glossary |
| P1-04 | D-06 Business Flow document exists | FILE | yes | _bmad-output/planning-artifacts/D-06-* | | hbc-create-business-flow-diagram |
| P1-05 | D-06 contains Mermaid flowcharts | CONTENT | yes | _bmad-output/planning-artifacts/D-06-* | ```mermaid | hbc-create-business-flow-diagram |
| P1-06 | Requirements traceable to business flows | QUALITY | yes | _bmad-output/planning-artifacts/D-02-*,_bmad-output/planning-artifacts/D-06-* | Each REQ-xxx should map to at least one business flow. Check cross-references between D-02 requirements and D-06 flow diagrams. | |
| P1-07 | No vague or unmeasurable requirements | QUALITY | no | _bmad-output/planning-artifacts/D-02-* | Requirements should be specific and testable. Flag any containing vague terms like 'fast', 'easy', 'user-friendly' without measurable criteria. | |
