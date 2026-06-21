# Headless Contract — hbc-check-implementation-readiness

This skill is evaluate-only and a **hard gate**: it reconciles D-02 against the
downstream design / test / implementation-planning documents and emits a JSON
verdict. It writes no document other than the report. Blocking is its job — a
non-empty gating set means `ready: false`, never a soft pass.

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| `feature` | Yes (headless) | `feature=<slug>` — the active feature slug; per-feature inputs resolve under `_bmad-output/features/<feature>/planning-artifacts/`. |
| `--d02` | Yes | Path to the feature's D-02 requirements (the authoritative REQ set). |
| `--d27` | No | Path to the per-feature D-27 test spec (TC-scoped coverage — a `### TC-` block must bind the REQ; gating). |
| `--d26` | No | Path to the per-feature D-26 test plan (mention-level; gating). |
| `--matrix` | No | Path to the **per-feature** traceability matrix (NOT the rollup — a rollup carries other features' REQ ids and would surface them as false orphans). Gating: row-present + non-empty `design_ref`/`code_ref`/`test_ref`. |
| `--task-breakdown` | No | Path to the per-feature task-breakdown. Gating: 3-way REQ↔TASK↔design reconcile (B13-2). |
| `--d19` | No | Path to the D-19 ER diagram (model-drift design side, B13-3). **Pair with `--code-dir`** — given alone, the drift check is skipped (with a stderr warning). |
| `--code-dir` | No | Path to the feature code root (model-drift code side, B13-3). Globbed by `--code-glob` (default `models/**/*.py` — persistent models only; transient wizards excluded to avoid false `code_only`). |
| `--code-glob` | No | Override the code glob under `--code-dir`. |
| `-o`, `--output` | No | Write the report JSON to this path (stdout otherwise carries a stderr note). |

Example:
`check-readiness.py --d02 …/D-02-auth.md --d27 …/D-27-auth.md --d26 …/D-26-auth.md --matrix …/traceability/matrix.md --task-breakdown …/task-breakdown.md --d19 …/D-19-auth.md --code-dir …/code -o …/readiness-report.json`

## Return Schema

```json
{
  "ready": false,
  "structure_ok": false,
  "semantic_review": "n/a",
  "passed": false,
  "d02_req_count": 42,
  "checked_documents": ["D-27", "D-26", "matrix", "task-breakdown", "D-19/code"],
  "uncovered_by_test": [],
  "uncovered_by_plan": [],
  "uncovered_by_api": [],
  "missing_from_matrix": ["REQ-FEAT-040", "REQ-FEAT-041", "REQ-FEAT-042"],
  "matrix_coverage_gaps": {"REQ-FEAT-007": ["code_ref"]},
  "reqs_without_task": ["REQ-FEAT-040"],
  "orphan_tasks": [],
  "stale_citations": [{"source": "D-26", "doc": "D-02", "cited": "2.2", "declared": "2.3"}],
  "model_drift": {"design_only": ["resource.plan.request"], "code_only": []},
  "orphan_reqs_downstream": [],
  "test_ref_drift": {},
  "tc_without_req_id": 0,
  "reason": "string (only when blocked/error)"
}
```

Keys for an optional input appear only when that input was given; the verdict shape
(`structure_ok`/`semantic_review`/`passed`/`checked`/`not_checked`) is always present,
including on an error result.

## Status / Exit Codes

- exit `0` — `ready: true` (all gating sets empty AND ≥1 gating doc reconciled).
- exit `1` — gaps found (`ready: false`); do NOT close Phase 2.
- exit `2` — D-02 missing/unreadable/no functional section, or arg error.

A run that reconciled NOTHING gating (only `--d02`, or only the informational
`--d21`) is **not** a meaningful green: it returns `ready: false` (exit 1) with a
`note`, because nothing that can fail was verified.

## Gating vs informational

- **Gating** (a non-empty set ⇒ `ready: false`): `uncovered_by_test`, `uncovered_by_plan`, `missing_from_matrix`, `matrix_coverage_gaps`, `reqs_without_task`, `orphan_tasks`, `stale_citations`, `model_drift`, `orphan_reqs_downstream`, `test_ref_drift`.
- **Informational** (reported, never flips `ready`): `uncovered_by_api` (a UI/batch-only REQ legitimately has no API surface), `tc_without_req_id` (surfaced for transparency).

## Autonomy / blocked reasons

The gate verdict is mechanical (a real gap always blocks). The one domain decision is
whether a surfaced gap is a **confirmed deliberate deferral** vs a real omission.
- `--strict` — stop at the first possibly-deferred gap and return `blocked` with the question (do not assume).
- `--assumptions-allowed` (default in CI) — treat every surfaced gap as real (safe default), log that no deferral was confirmed, return `ready: false`; never block the first turn, never emit a false green.

## Blocked / error reasons (closed set)

- `"feature_required"` — headless invocation with no resolvable feature (per-feature inputs cannot be located otherwise).
- `"d02_unreadable"` — D-02 not readable at the given path (exit 2).
- `"no_functional_section"` — D-02 has no functional requirements section, so no authoritative REQ set can be determined (exit 2).
- `"deferral_unconfirmed"` — `--strict` only: a surfaced gap may be a deliberate deferral but no confirmation is available; blocked pending the domain decision.
