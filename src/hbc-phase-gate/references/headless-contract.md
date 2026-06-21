# Headless Contract — hbc-phase-gate

## Input Args

| Arg | Required | Description |
|-----|----------|-------------|
| Phase number | Yes (headless) | Target phase `1`–`4` (Analysis/Design/Implementation/Testing) — passed positionally (e.g. `phase gate 2`). No interactive prompt and no agent-context inference in headless mode. |
| `feature` | Yes (headless) | `feature=<slug>` — the active feature the gate evaluates. Checklist artifact patterns resolve under `_bmad-output/features/<feature>/...` (plus `shared/...` for D-12/D-03 and dual-path D-19/D-21). Slug must match `^[a-z0-9][a-z0-9-]*$`. |
| `--var key=value` | No | Passthrough to `evaluate-gate-checklist.py` for pattern substitution. `output_folder` and `feature` are always passed; `gate_mode`, `coverage_threshold`, `project_name` are resolved from config and forwarded. Repeatable. |

Example: `hbc-phase-gate --headless 2 feature=auth-login`

## Return Schema

```json
{
  "phase": 2,
  "status": "PASSED | PASSED_PENDING_SIGNOFF | FAILED | WARNING | CONTESTED | BLOCKED | PENDING_LLM",
  "gate_mode": "strict | lenient",
  "summary": {
    "total": 10,
    "evaluated": 9,
    "passed": 8,
    "failed": 1,
    "skipped": 0,
    "contested": 0,
    "pending_llm": 0,
    "required_failed": 1,
    "entry_gate_failed": 0,
    "correctness_failed": 0
  },
  "results": [
    {
      "item_id": "P2-03",
      "description": "string",
      "type": "FILE | CONTENT | METRIC | MATRIX | QUALITY | REVIEW",
      "required": true,
      "status": "PASS | FAIL | NA | SKIP | PENDING_LLM | CONTESTED",
      "evidence": "quantified evidence string"
    }
  ],
  "required_failed": ["P2-03"],
  "delta": {
    "is_first_run": false,
    "fixed": ["P2-01"],
    "regressed": [],
    "new": ["P2-10"],
    "unchanged": ["P2-02"]
  },
  "report_path": "{workflow.gate_output_path}/phase-2-gate.md",
  "log_path": "{workflow.gate_output_path}/phase-2-gate-log.md",
  "reason": "string (only when status omitted / blocked)"
}
```

Notes:
- `status` (overall) mirrors the script's `summary.overall_status` after QUALITY items are resolved by the LLM. The deterministic script returns `PENDING_LLM` while `[QUALITY]` items await judgment; the final headless return collapses these to `PASSED`/`FAILED`/`WARNING`.
- Per-item `results[]` carry type-specific extra fields from the script: FILE → `matched_files`, `near_matches`, `skill_to_create` (on FAIL); CONTENT → `match_count`, `sample_matches`; METRIC → `actual_value`, `threshold`; MATRIX → `missing_from_matrix`, `coverage_gaps`, `traced`, `total`; REVIEW → `review_status`. An item whose `--na` waiver was refused (a correctness item) carries `waiver_rejected`.
- The gate report (`.md`) and `phase-N-gate-results.json` are still written to disk in headless mode.

## Status Values

- **PASSED** — every `required=yes` item is PASS or `NA`.
- **PASSED_PENDING_SIGNOFF** — a Phase 1/2 gate that is otherwise PASSED but the B6-5 USER sign-off is not yet recorded (headless `--assumptions-allowed`). Not a clean PASS — do not advance the phase on it.
- **FAILED** — any `required=yes` item FAILs (strict), or an entry-gate / other correctness item FAILs in **any** mode (never downgraded by lenient — B6-3 extend).
- **CONTESTED** — no FAIL, but a required item is unresolvable (ambiguous `[METRIC]`, no D-02 source for a `[MATRIX]` check) or two QUALITY lenses disagree (B6-1). Blocks; a human adjudicates. Never an auto-pass; never lenient-downgraded.
- **BLOCKED** — the evaluator crashed (`reason: "evaluator_crashed"`) or could not run. Never a PASS. Exit code is non-zero (2 for a crash).
- **WARNING** — `gate_mode=lenient` and only **non-correctness** required items FAIL; the user may proceed at their own risk.
- **PENDING_LLM** — deterministic phase only; `[QUALITY]` items still need LLM judgment before the final verdict.

Exit code is non-zero whenever `required_failed`, `correctness_failed`, or `contested` is > 0 (and 2 on a crash) — CI never reads exit 0 as a clean gate on broken / ambiguous / un-adjudicated evidence.

## Autonomy modes (A5)

- `--strict` — stop at the first possible deliberate-deferral or design-phase sign-off and return `blocked` with the question; never assume.
- `--assumptions-allowed` (CI default) — treat every surfaced gap as real (safe non-green default), log that no deferral/sign-off was confirmed, and return the honest verdict (`FAILED`/`CONTESTED`, or `PASSED_PENDING_SIGNOFF`) rather than blocking the first turn. **The CI default never fabricates a PASS.**

## Blocked Reasons

- `"feature_required"` — headless invocation with no resolvable `feature=<slug>`.
- `"phase_required"` — headless invocation with no phase number (1–4) supplied.
- `"checklist_not_found"` — no checklist resolvable at `{workflow.phase_N_checklist}` nor the `assets/phase-{N}-gate-checklist.md` fallback.
- `"evaluator_crashed"` — the deterministic evaluator raised an unhandled exception; the gate is BLOCKED, not PASS (B6-6).
