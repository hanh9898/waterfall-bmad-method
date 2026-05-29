# Headless Contract — hbc-create-glossary

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | Yes | Comma-separated file paths to source documents |
| `--mode` | No | `create` (default), `update`, or `validate` |

Example: `hbc-create-glossary --headless --sources "D-02-project.md,project-context.md"`

## Return Schema

```json
{
  "status": "complete | blocked",
  "output_path": "/path/to/D-03-project-name.md",
  "distillate_path": "/path/to/glossary-distillate.json",
  "decision_log": "/path/to/.decision-log.md",
  "validation": {
    "valid": true,
    "total_issues": 0,
    "term_count": 25,
    "abbreviation_count": 8,
    "total_entries": 33
  },
  "reason": "string (only when status=blocked)"
}
```

## Status Values

- **complete** — D-03 generated and validation passed.
- **blocked** — cannot proceed without human input. `reason` describes the blocker.

## Blocked Reasons

- `"no_source_documents"` — no inputs provided and none discoverable.
- `"validation_manual_fix"` — validation found issues requiring human judgment.
- `"no_terms_extracted"` — source documents contain no extractable terms.
- `"duplicate_conflict"` — update mode found terms with conflicting definitions requiring human resolution.
