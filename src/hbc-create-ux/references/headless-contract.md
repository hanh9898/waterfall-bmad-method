# Headless Contract — hbc-create-ux (D-14)

`--headless` / `-H` runs every stage non-interactively. Screens/components are
derived from D-02/D-06; every inferred decision is logged. The Claude Design gate
(Stage 1c) defaults to the value of frontmatter `uses_claude_design` or
`--uses-claude-design` (default false in headless).

## Input args

- `feature=<slug>` — **required** (missing → blocked `feature_required`).
- `--sources "<p1,p2>"` — explicit source paths.
- `--uses-claude-design` — opt into Claude Design linkage (default false headless).
- intent: `create` (default) | `update` | `validate`.

## Return JSON

```json
{
  "status": "complete | blocked",
  "skill": "hbc-create-ux",
  "feature": "<slug>",
  "document": "<path to D-14>",
  "uses_claude_design": false,
  "validation": { "valid": true, "screen_count": 0, "advisories": [] },
  "semanticReview": { "status": "passed | pending", "openFacets": [] },
  "assumptions": ["<derived screen/component>", "..."]
}
```

## Blocked reasons (closed set)

- `feature_required` — no resolvable feature.
- `not_applicable` — feature has no `has-ui` facet (D-14 is N/A); not an error.
- `sources_missing` — no D-02 for the feature and no `--sources`.
- `template_missing` — `{workflow.template_path}` not found.
- `validation_failed` — structural issues not all `auto_fixable`.

Advisories (e.g. inline visual values) never block; they are returned for the
caller to triage. Element ids (`SCR-/CMP-`) are stable across updates (the
traceability matrix references them) — new ids are appended, never renumbered.
