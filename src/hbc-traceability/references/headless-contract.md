# Headless Contract — hbc-traceability

Covers the five capabilities (TRI/TRU/TRR/TRA/SYNC). For the full **impact** (SYNC) lifecycle and its stage-by-stage CLI, see `references/impact-capability.md`; this file is the headless I/O contract.

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| Capability | Yes (headless) | One of `init` (TRI), `update` (TRU), `report` (TRR), `audit` (TRA), `impact` (SYNC). No interactive prompt and no agent-context inference in headless mode. |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature. Matrix resolves to `{workflow.matrix_path}` under `_bmad-output/features/<feature>/traceability/matrix.md`; `report` roll-up aggregates `_bmad-output/features/*/traceability/matrix.md` into `{workflow.rollup_path}`. Slug must match `^[a-z0-9][a-z0-9-]*$`. |
| `--invoked-by-sync` | No | Set when `impact` (APPLY) calls an owning-skill's `update` mode — anti-loop guard. |

Example: `hbc-traceability --headless report feature=auth-login`

## Return Schema

Common envelope for `init`/`update`/`report`/`audit`:

```json
{
  "status": "complete | blocked",
  "capability": "init | update | report | audit | impact",
  "matrix_path": "_bmad-output/features/<feature>/traceability/matrix.md",
  "decision_log": "_bmad-output/features/<feature>/traceability/.trace-decisions.md",
  "rollup_path": "{workflow.rollup_path} (report only)",
  "summary": {
    "total_requirements": 15,
    "coverage": { "design_ref": 15, "code_ref": 12, "test_ref": 15 },
    "fully_traced": 12,
    "fully_traced_pct": 80.0,
    "gaps": ["REQ-AUTH-013"],
    "gap_details": [{ "req_id": "REQ-AUTH-013", "missing_columns": ["code_ref"] }]
  },
  "reason": "string (only when status=blocked)"
}
```

Per-capability notes (fields sourced from the real scripts):
- **init** — `extract-trace-ids.py` returns the discovered REQ IDs (`REQ-<FEAT>-NNN` + referenced `REQ-SHARED-NNN`); summary carries the populated row count. Script returns `NO_FILES` when no D-02 is found → `blocked` `no_d02`.
- **update** — `trace-report.py --detect-phase` returns `{next_phase, empty_columns, total_rows}` to route which columns to fill; `decision_log` is present when new LLM-judged mappings are written.
- **report** — `trace-report.py --matrix` returns the `summary` block above (`total_requirements`, `coverage`, `fully_traced`, `fully_traced_pct`, `gaps`, `gap_details`); `--rollup` adds `{features:[{feature,total,fully_traced,pct}], shared:{...}, grand_total, grand_fully_traced, grand_pct, matrices_found}` and writes `rollup_path`.
- **audit** — same report data plus per-gap severity (CRITICAL/HIGH/INFO) classification; with `--d02`, `summary.d02_sync` carries `{in_sync, d02_req_count, matrix_req_count, orphan_in_matrix, missing_from_matrix}`.

### `impact` (SYNC) return

```json
{
  "status": "complete | blocked",
  "capability": "impact",
  "matrix_path": "...",
  "changed": ["REQ-AUTH-001"],
  "affected": {
    "apply": [{ "req": "REQ-AUTH-001", "column": "design_ref", "ref": "...", "kind": "apply" }],
    "verify": [{ "req": "REQ-AUTH-007", "shared_ref": "...", "via_column": "test_ref", "kind": "verify" }]
  },
  "frozen": [{ "req": "REQ-AUTH-002", "frozen": true, "decided_by": "task | phase-gate | matrix", "disposition": "new-task" }],
  "suggested": [{ "ref": "...", "skill": "hbc-create-er-diagram", "order": 1 }],
  "reconciled": ["REQ-AUTH-001"],
  "reason": "string (only when status=blocked)"
}
```

The deterministic core (`impact.py`) backs this: `detect` → `changed_set`/`untraced_changes`; `analyze` → `apply`/`verify`/`flood`/`unknown_reqs`/`incomplete_rows`; `freeze` → per-REQ `{frozen, decided_by, task_status, phase_gate, matrix_gate_status}`; `complete` → `{complete, accounted, missing}`.

## Status Values

- **complete** — capability finished; matrix/roll-up written to disk.
- **blocked** — cannot proceed without human input; `reason` describes the blocker. Matrix is still written/updated where partial work was done.

## Blocked Reasons

Shared:
- `"feature_required"` — headless invocation with no resolvable `feature=<slug>`.
- `"capability_required"` — headless invocation with no capability supplied.
- `"no_matrix"` / `"matrix_not_found"` — matrix file absent; run `init` first (`trace-report.py`/`impact.py` emit `matrix_not_found`).
- `"no_d02"` — `init` found no D-02 source (`extract-trace-ids.py` → `NO_FILES`).

`impact`-specific (closed set, per `impact.py` + `references/impact-capability.md`):
- `"empty_changeset"` — no-op, nothing changed (`detect`/`analyze` exit 2).
- `"untraced_change"` — a changed file maps to no REQ in the matrix.
- `"invalid_since"` — bad `--since` git ref.
- `"skill_no_update_contract"` — an owning-skill targeted by APPLY has no headless `update` contract.
- `"skill_runtime_error"` — owning-skill failed at runtime during APPLY (branch-stop, other branches continue).
- `"reconcile_unverified"` — re-suggest loop exhausted `{workflow.impact_reconcile_max_retries}` without verifying the cascade.
- `"state_unreadable"` — cascade state file (`.cascade-state.json`) could not be parsed during `complete`.
