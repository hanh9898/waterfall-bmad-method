# Headless Contract — hbc-check-implementation-readiness

This skill is evaluate-only: it reconciles D-02 against the downstream design/test
documents and emits a JSON verdict. It writes no document other than the report.

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature inputs resolve under `_bmad-output/features/<feature>/planning-artifacts/`. |
| `--d02` | Yes | Path to the feature's D-02 requirements (the authoritative REQ set). |
| `--d27` | No | Path to the per-feature D-27 test spec (TC-scoped coverage; gating). |
| `--d26` | No | Path to the per-feature D-26 test plan (mention-level; gating). |
| `--d21` | No | Path to the resolved D-21 API spec — DUAL: per-feature override if present, else shared baseline (informational, not gating). |
| `--matrix` | No | Path to the **per-feature** traceability matrix (NOT the rollup — a rollup carries other features' REQ ids and would surface them as false orphans). |

Example: `check-readiness.py --d02 _bmad-output/features/auth/planning-artifacts/D-02-auth.md --d27 …/D-27-auth.md --matrix …/traceability/matrix.md`

## Return Schema

```json
{
  "ready": true,
  "structure_ok": true,
  "semantic_review": "n/a",
  "passed": true,
  "d02_req_count": 12,
  "checked_documents": ["D-27", "D-26", "matrix"],
  "uncovered_by_test": [],
  "uncovered_by_plan": [],
  "missing_from_matrix": [],
  "orphan_reqs_downstream": [],
  "reason": "string (only when blocked)"
}
```

## Status / Exit Codes

- exit `0` — `ready: true` (all gating sets empty, ≥1 gating doc reconciled).
- exit `1` — gaps found (`ready: false`); do NOT close Phase 2.
- exit `2` — D-02 missing/unreadable/no functional section, or arg error.

## Blocked Reasons

- `"feature_required"` — headless invocation with no resolvable feature (per-feature inputs cannot be located otherwise).
- `"d02_unreadable"` — D-02 not readable at the given path.
- `"no_functional_section"` — D-02 has no functional requirements section, so no authoritative REQ set can be determined.
