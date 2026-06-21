# Headless Contract — hbc-create-architecture (D-09)

`--headless` / `-H` runs every stage non-interactively. No user prompts: domain
decisions are derived from sources (D-02, D-06, integration-map) and every
inferred decision is logged to the decision log.

## Input args

- `feature=<slug>` — **required** in headless (missing → blocked `feature_required`).
- `--sources "<p1,p2>"` — explicit source paths (skips auto-discovery).
- intent: `create` (default) | `update` | `validate`.

## Return JSON

```json
{
  "status": "complete | blocked",
  "skill": "hbc-create-architecture",
  "feature": "<slug>",
  "document": "<path to D-09>",
  "validation": { "valid": true, "issues": [] },
  "semanticReview": { "status": "passed | pending", "openFacets": [] },
  "assumptions": ["<derived decision>", "..."]
}
```

## Blocked reasons (closed set)

- `feature_required` — no resolvable feature.
- `sources_missing` — no D-02 for the feature and no `--sources`.
- `template_missing` — `{workflow.template_path}` not found.
- `validation_failed` — structural issues that are not all `auto_fixable`.

On `blocked`, include `reason` and a one-line `detail`. The document is still
written to disk when generation completed before the blocker.
