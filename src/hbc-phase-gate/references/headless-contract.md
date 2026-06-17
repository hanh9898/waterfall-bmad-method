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
  "status": "PASSED | FAILED | WARNING | PENDING_LLM",
  "gate_mode": "strict | lenient",
  "summary": {
    "total": 10,
    "evaluated": 9,
    "passed": 8,
    "failed": 1,
    "skipped": 0,
    "pending_llm": 0,
    "required_failed": 1,
    "entry_gate_failed": 0
  },
  "results": [
    {
      "item_id": "P2-03",
      "description": "string",
      "type": "FILE | CONTENT | METRIC | QUALITY | REVIEW",
      "required": true,
      "status": "PASS | FAIL | SKIP | PENDING_LLM | CONTESTED",
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
- Per-item `results[]` carry type-specific extra fields from the script: FILE → `matched_files`, `near_matches`, `skill_to_create` (on FAIL); CONTENT → `match_count`, `sample_matches`; METRIC → `actual_value`, `threshold`; REVIEW → `review_status`.
- The gate report (`.md`) and `phase-N-gate-results.json` are still written to disk in headless mode.

## Status Values

- **PASSED** — every `required=yes` item is PASS.
- **FAILED** — any `required=yes` item FAILs (strict mode), or an entry-gate item FAILs in any mode (a prior phase gate did not PASS — never downgraded by lenient mode).
- **WARNING** — `gate_mode=lenient` and a non-entry-gate required item FAILs; the user may proceed at their own risk.
- **PENDING_LLM** — deterministic phase only; `[QUALITY]` items still need LLM judgment before the final verdict.

## Blocked Reasons

- `"feature_required"` — headless invocation with no resolvable `feature=<slug>`.
- `"phase_required"` — headless invocation with no phase number (1–4) supplied.
- `"checklist_not_found"` — no checklist resolvable at `{workflow.phase_N_checklist}` nor the `assets/phase-{N}-gate-checklist.md` fallback.
