# API Documentation

> hbc không có REST API. "API" ở đây là internal skill-to-skill contracts (headless mode) và script CLI interfaces.

## Skill Invocation Interface (Headless)

### Common Return Schema
```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-xx.md",
  "distillate_path": "/path/to/xxx-distillate.json",
  "decision_log": "/path/to/.decision-log.md",
  "validation": { "valid": true, "total_issues": 0 },
  "reason": "string (only when status=blocked)"
}
```

### Invocation Convention
- `hbc-<skill> --headless --sources "<paths>" [--mode create|update|validate]`
- Skill được trigger qua: explicit arg, agent context inference, hoặc user phrase (trigger phrases trong description)

## Script CLI Interface (Convention)

### Scan/Discover Scripts
- **Input**: `--project-root <path>` (required), `--output-dir`, `--template-path`, `-o <output.json>`
- **Output**: JSON `{state: fresh|resume|update, existing_doc, source_docs[]}`
- **Exit**: luôn 0 (status trong JSON)

### Validate Scripts
- **Input**: positional doc path, cross-doc refs (`--d02`, `--d19`, `--d27`, `--matrix`), `--project-root`
- **Output**: JSON với per-issue `auto_fixable` flag
- **Exit**: 2 + JSON error nếu `hbc_validation` missing

### Extract/Report Scripts
- `extract-trace-ids.py --source <glob> --pattern "REQ-\d{3,}" --project-root <path>`
- `trace-report.py --matrix <path> [--detect-phase]`
- `evaluate-gate-checklist.py <checklist> --project-root <path> --var key=value`

## Internal APIs (hbc_validation.py)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `find_section` | `(content, *labels) -> Match\|None` | Tìm heading (language-aware) |
| `section_body` | `(content, match) -> str` | Lấy body section |
| `parse_table` | `(content, *labels) -> list[list[str]]` | Parse markdown table data rows |
| `extract_column` | `(rows, index) -> list[str]` | Lấy cột |
| `iter_tc_blocks` | `(text) -> list[str]` | Split TC blocks |
| `tc_ids` | `(text) -> set[str]` | Extract TC IDs |
| `tc_field` | `(block, label) -> str\|None` | Lấy field trong TC block |
| `check_required_sections` | `(content, sections, empty_check) -> list[dict]` | SECTION_MISSING/EMPTY |
| `verdict` | `(structure_ok, *, semantic_review, checked, not_checked) -> dict` | Honest verdict |

## Data Models (Documents)
| Document | Key IDs | Fields |
|----------|---------|--------|
| D-02 | REQ-xxx | functional/non-functional requirements, scope, roles |
| D-19 | entities | Mermaid erDiagram, table defs, relationships |
| D-27 | TC-xxx | preconditions, steps, expected, severity, REQ link |
| task-breakdown.md | task_id | design_ref, test_refs, dependencies, priority, status |
| matrix.md | req_id | story_id, design_ref, code_ref, test_ref, gate_status, timestamp |
