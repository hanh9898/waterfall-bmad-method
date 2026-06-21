# Headless Contract — hbc-discovery-spike (discovery-note)

`--headless` / `-H` runs the non-interactive path. Assumptions and methods are
derived from D-02/D-06 + the real code/DB/business-flow; every inference is
logged. **The verdict requires a USER sign-off, which cannot be fabricated** — so
in headless the skill produces the draft note and returns `blocked signoff_required`
for a human to sign off (the LLM must never self-certify the model as validated).

## Input args

- `feature=<slug>` — **required** (missing → blocked `feature_required`).
- `--sources "<p1,p2>"` — explicit ground-truth paths (code/schema/flow).
- intent: `create` (default) | `update` | `validate`.

## Return JSON

```json
{
  "status": "blocked | complete | not_applicable",
  "skill": "hbc-discovery-spike",
  "feature": "<slug>",
  "document": "<path to discovery-note>",
  "validation": { "valid": true, "assumption_count": 0, "verdict_value": null, "issues": [] },
  "assumptions": ["<derived assumption>", "..."],
  "blocked_reason": "signoff_required"
}
```

## Blocked / status reasons (closed set)

- `feature_required` — no resolvable feature.
- `not_applicable` — feature is `discovery_risk: known` (or no uncertain model) → discovery-spike is N/A; not an error.
- `signoff_required` — draft note produced, but the VALIDATED/RESHAPE/KILL verdict needs a human sign-off (headless cannot self-certify).
- `sources_missing` — no D-02 for the feature and no `--sources` ground-truth.
- `template_missing` — `{workflow.template_path}` not found.
- `validation_failed` — structural issues not all `auto_fixable`.

`status: complete` is only returned for `validate` of an already-signed-off note,
or for `update` that preserves an existing sign-off.
