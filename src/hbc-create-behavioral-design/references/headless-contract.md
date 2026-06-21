# Headless Contract — hbc-create-behavioral-design (D-17)

`--headless` / `-H` runs every stage non-interactively. Behaviour is derived from
D-02/D-06/D-19; every inferred element/decision is logged to the decision log.

## Input args

- `feature=<slug>` — **required** (missing → blocked `feature_required`).
- `--sources "<p1,p2>"` — explicit source paths.
- intent: `create` (default) | `update` | `validate`.

## Return JSON

```json
{
  "status": "complete | blocked",
  "skill": "hbc-create-behavioral-design",
  "feature": "<slug>",
  "document": "<path to D-17>",
  "validation": { "valid": true, "element_count": 0, "issues": [] },
  "semanticReview": { "status": "passed | pending", "openFacets": [] },
  "assumptions": ["<derived behaviour>", "..."]
}
```

## Blocked reasons (closed set)

- `feature_required` — no resolvable feature.
- `not_applicable` — feature has no non-CRUD facet (D-17 is N/A); not an error.
- `sources_missing` — no D-02 for the feature and no `--sources`.
- `template_missing` — `{workflow.template_path}` not found.
- `validation_failed` — structural issues not all `auto_fixable`.

`update` never renumbers existing element ids (D-27 references them) — new
elements are appended.
