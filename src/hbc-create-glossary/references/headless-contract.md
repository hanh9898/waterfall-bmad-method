# Headless Contract — hbc-create-glossary

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `--sources` | Yes | Comma-separated file paths to source documents (also the orphan corpus, B11-2) |
| `--design` | No | D-19 path for the Stage 3a ubiquitous-language reconcile (B11-3) |
| `--code-dir` | No | Model source dir for the Stage 3a reconcile (B11-3) |
| `--mode` | No | `create` (default), `update`, or `validate` |
| `--strict` / `--assumptions-allowed` | No | Autonomy mode for domain decisions (A5). `--assumptions-allowed` is the CI default: infer + log an `ASSUMPTION` and continue. `--strict`: stop at the first domain decision. |

Example: `hbc-create-glossary --headless --sources "D-02-project.md,project-context.md" --assumptions-allowed`

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
    "total_entries": 33,
    "churn": { "revisions": 2, "threshold": 4, "high_churn": false }
  },
  "consistency": {
    "grounded": true,
    "missing_from_glossary": [],
    "orphan_terms": []
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
- `"domain_decision"` — `--strict` only: a domain decision (e.g. an inferred definition needing confirmation, B11-1) was reached. `--assumptions-allowed` logs an `ASSUMPTION` and continues instead.
- `"consistency_gap"` — `--strict` only: Stage 3a found `missing_from_glossary` or `orphan_terms` (B11-2/B11-3). The return includes both lists; `--assumptions-allowed` logs them and continues.
