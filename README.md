# HBLAB BMad Custom

BMad custom module for waterfall + TDD development lifecycle. 5 coordinator agents guide 4 phases producing D-xx deliverables with phase gates and full requirements-to-test traceability. Expansion module — requires BMM.

## Requirements

- [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) v6.3.0+
- BMM (BMad Method Module) installed
- Python 3.10+ (validation and helper scripts)

## Installation

```bash
npx bmad-method install --custom-source git@git.hblab.vn:stc/erp/stc-erp-bmad-custom.git
```

Select "HBLAB BMad Custom" when prompted.

## Skills Included

### Agents

| Code | Skill | Description |
| --- | --- | --- |
| BA | hbc-agent-ba | Phase 1 Analysis coordinator. Guides requirements elicitation, glossary creation, and business flow mapping. |
| ARCH | hbc-agent-architect | Phase 2 Design coordinator. Guides database design, coding standards, and API specification. |
| QA | hbc-agent-qa | Phase 2 Test Design coordinator. Guides test plan creation and test case specification. |
| DEV | hbc-agent-dev | Phase 3 Implementation coordinator. Guides task breakdown and TDD implementation. |
| TST | hbc-agent-tester | Phase 4 Testing coordinator. Guides test execution, defect triage, and acceptance decisions. |

### Phase 1 — Analysis

| Code | Skill | Deliverable | Required |
| --- | --- | --- | --- |
| REQ | hbc-create-requirements | D-02 Requirements Specification | Yes |
| GLO | hbc-create-glossary | D-03 Glossary | No |
| BFD | hbc-create-business-flow-diagram | D-06 Business Flow Diagram | No |

### Phase 2 — Design

| Code | Skill | Deliverable | Required |
| --- | --- | --- | --- |
| ERD | hbc-create-er-diagram | D-19 Database Design / ER Diagram | Yes |
| CS | hbc-create-coding-standards | D-12 Coding Standards | Yes |
| API | hbc-create-api-spec | D-21 API Specification | No |
| TP | hbc-create-test-plan | D-26 Test Plan | Yes |
| TS | hbc-create-test-spec | D-27 Test Specification | Yes |

### Phase 3 — Implementation

| Code | Skill | Deliverable | Required |
| --- | --- | --- | --- |
| TB | hbc-task-breakdown | Task Breakdown | Yes |
| IM | hbc-implement | Code (TDD: RED-GREEN-REFACTOR) | Yes |

### Phase 4 — Testing

| Code | Skill | Deliverable | Required |
| --- | --- | --- | --- |
| TE | hbc-test-execution | Test Execution Report | Yes |
| AC | hbc-acceptance-check | Acceptance Report | Yes |

### Cross-cutting

| Code | Skill | Description |
| --- | --- | --- |
| PG | hbc-phase-gate | Validate phase completion (deterministic + LLM evaluation) |
| TRI | hbc-traceability | Initialize traceability matrix from D-02 REQ IDs |
| TRU | hbc-traceability | Update matrix columns as each phase completes |
| TRR | hbc-traceability | Coverage summary report |
| TRA | hbc-traceability | Gap identification and severity audit |

Each workflow skill supports **Create**, **Update**, and **Validate** modes. Most support `--headless` / `-H`.

## Usage

After installation, invoke skills by menu code, skill name, or agent:

- `BA` or `hbc-agent-ba` — Open Phase 1 coordinator
- `REQ` or `create requirements` — Generate D-02 Requirements Specification
- `PG` or `phase gate 1` — Validate Phase 1 completion
- `TRI` or `init traceability` — Initialize traceability matrix

Recommended flow: work through phases in order, run Phase Gate (`PG`) at each boundary, and use Traceability (`TRI` → `TRU` → `TRA`) for end-to-end coverage tracking.

## Configuration

During installation, you'll be asked:

| Variable | Default | Description |
| --- | --- | --- |
| `user_name` | BMad | Your display name (user-only) |
| `communication_language` | English | Language for agent communication (user-only) |
| `document_output_language` | English | Language for generated documents |
| `output_folder` | `{project-root}/_bmad-output` | Base output directory |

## License

UNLICENSED — Internal use only.
