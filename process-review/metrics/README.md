# HBC F-6 metrics harness (TF.3)

Re-derives the six F-6 outcome metrics of the HBC improvement plan from the frozen
TD.0 regression fixture (`../fixtures/resource-plan-billable/`), so each
remediation wave can be measured **before/after against a fixed substrate** instead
of self-reported numbers.

## Run

```bash
# JSON report to stdout (default fixture = resource-plan-billable TD.0)
python process-review/metrics/hbc_metrics_harness.py

# point at another fixture
python process-review/metrics/hbc_metrics_harness.py --fixture <dir>

# assert the frozen baselines still hold
python -m pytest process-review/metrics/tests
```

(`python` on Windows dev; `python3` on Linux/Mac CI — stdlib only, no deps.)

## Metrics

| id | what it counts | mechanical | RCA→target |
| --- | --- | --- | --- |
| `d02_churn` | D-02 revision-history rows | yes | 13 → ≤4 |
| `spec_ref_leak` | REQ-/TC-/NFR- ids embedded in `code/` | yes | 65 → 0 |
| `req_without_matrix_row` | REQ in D-02 absent from matrix | yes | 3 → 0 |
| `gate_false_pass` | gates PASSED despite an at-gate-time failure/override (structural) | yes | 3 → 0 (measured 2; +1 stale-only) |
| `model_drift` | v2.3 design tokens absent from code | yes | drift → 0 missing |
| `recascade` | manual cascade rounds | **no** (historical) | 4+ → 1 |

`recascade` is a process metric that cannot be reconstructed from a single static
snapshot; it is reported with `mechanical: false` and its documented baseline (4)
rather than fabricated as if measured.

## Usage in the wave loop

Run before a wave to record the baseline, and after to record the new number. The
baselines are also pinned as assertions in `tests/` — if they drift, the fixture
changed (it must not) or a metric definition changed (update both deliberately).
See `../fixtures/resource-plan-billable/FIXTURE.md` for the known-bug contract.
