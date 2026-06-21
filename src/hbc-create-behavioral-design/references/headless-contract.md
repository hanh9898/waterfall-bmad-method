# Headless Contract — hbc-create-behavioral-design (D-16)

`--headless` / `-H` runs every stage non-interactively. Behaviour is derived from
D-02/D-06/D-19 (+ real code when `--code-dir` given); every inferred element/decision
is logged to the decision log.

## Autonomy mode (A5)

- `--strict` — block at the first unresolved **domain** decision (the actual
  states/events/guards, illegal transitions, rule conditions/actions, invariant
  guarantees, cross-entity ordering). Blocked `reason: domain_decision`.
- `--assumptions-allowed` (CI default) — derive the most defensible behaviour from
  D-02/D-06/D-19, log it as an `ASSUMPTION` in the decision log, and continue.
  Never blocks the first question (a complex feature must not deadlock CI).

Mechanical decisions (element-id numbering, table layout, Mermaid notation) are
always taken without asking, in both modes.

## Input args

- `feature=<slug>` — **required** (missing → blocked `feature_required`).
- `--sources "<p1,p2>"` — explicit source paths (D-02 + D-06) for grounding/coverage.
- `--code-dir <path>` — code tree to ground behaviour against (behavioral-vs-code).
- intent: `create` (default) | `update` | `validate`.

## Return JSON

```json
{
  "status": "complete | blocked",
  "skill": "hbc-create-behavioral-design",
  "feature": "<slug>",
  "document": "<path to D-16>",
  "validation": { "valid": true, "element_count": 0, "churn": {}, "issues": [] },
  "grounding": { "valid": true, "bdd": {}, "behavior_drift": {}, "uncovered_reqs": [], "issues": [] },
  "semanticReview": { "status": "passed | pending", "openFacets": [] },
  "assumptions": ["<derived behaviour>", "..."]
}
```

## Blocked reasons (closed set)

- `feature_required` — no resolvable feature.
- `not_applicable` — feature has no non-CRUD facet (D-16 is N/A); not an error.
- `sources_missing` — no D-02 for the feature and no `--sources`.
- `template_missing` — `{workflow.template_path}` not found.
- `validation_failed` — structural issues not all `auto_fixable`.
- `domain_decision` — `--strict` + an unresolved domain decision (the actual logic).

`update` never renumbers existing element ids (D-27 references them) — new
elements are appended. The grounding check (`check-behavioral-grounding.py`) is
ADVISORY and never blocks: its findings are surfaced, not gated.
