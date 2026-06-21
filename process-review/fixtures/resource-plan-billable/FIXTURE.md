---
title: "TD.0 Regression Fixture — resource-plan-billable (error-state snapshot)"
fixture_id: TD.0
plan_unit: U0
status: frozen
source_repo: "git@git.hblab.vn:.../opms (OPMS)"
source_state: "working-tree (untracked), mtime 2026-06-19 — the state the RCA analyzed on 2026-06-20"
rca: process-review/process-retrospective-rca-2026-06-20.md
frozen_on: 2026-06-22
---

# TD.0 — Regression Fixture: `resource-plan-billable` (error-state)

> **IMMUTABLE.** This directory is a frozen snapshot of the RCA case in its
> *error state*. Do **not** edit, re-generate, or "fix" anything in it — the whole
> point is to keep a fixed substrate so the F-6 metrics harness (TF.3) and the
> build-graph spike (TA.0) can be re-measured against the same known-bug input
> across every remediation wave. To remediate the case itself, work in the OPMS
> repo (plan §7, TD.1–TD.6) — never here.

## Provenance (why this *is* the RCA state, not HEAD)

The plan (TD.0) mandates the source be the **git-ref at RCA time (2026-06-20)**,
not HEAD, because "the case may have changed → the error state can't be rebuilt
from HEAD."

In OPMS the case artifacts under `_bmad-output/features/resource-plan-billable/`
and the `resource_plan*` code are **untracked working-tree files** — they were
never committed, so there is no tag/commit to check out. Two things establish that
this snapshot is the RCA error state:

1. **Source freshness at capture.** In the OPMS working tree every artifact and
   code/test file had **mtime 2026-06-19** (the day before the RCA) and **none was
   modified after 2026-06-20** (`find -newermt 2026-06-20` returned nothing) when
   this snapshot was captured on 2026-06-22. So the source still *was* the error
   state the RCA examined — not a later HEAD. (This is a statement about the OPMS
   source at capture time; mtime does not survive the copy, so it is **not** how
   integrity is verified afterward — see point 2.)
2. **Content-hash integrity (the real tamper-evidence).** `manifest.sha256` pins a
   SHA-256 of every file in this fixture. `fixture_integrity.py --check` (run by the
   test suite) fails on any byte-level change — added, removed, or edited. This,
   plus committing the fixture to git, is what keeps it frozen; mtime is not relied
   on for that.

## Layout

| Path | What |
| --- | --- |
| `artifacts/planning-artifacts/` | D-02 (v2.3, 13 revisions), D-06, D-19 (v2.3 Request+Snapshot model), D-26, D-27 + distillates |
| `artifacts/traceability/matrix.md` | matrix stuck at REQ-039 (missing 040/041/042), empty `gate_status` |
| `artifacts/implementation-artifacts/` | task-breakdown (stale), coverage-report, test-results, tdd-evidence |
| `artifacts/gates/` | phase-1/2/3 gate-results.json — all PASSED on the stale model |
| `code/models/` · `code/wizard/` | `resource.plan` old model: `state` + lifecycle (NO request/snapshot) |
| `code/tests/` | the feature's `resource_plan` test suite (87 tests, locks the old model) |
| `manifest.sha256` | SHA-256 of every file above — the tamper-evidence that keeps it frozen |

## Known-bug checklist (the regression contract)

Each row is a known bug the remediation must catch/fix. **Baseline measured** is
re-derived by `process-review/metrics/hbc_metrics_harness.py` on this fixture; it
is the number to beat. RCA-claimed is the headline figure from the RCA doc.

| # | Known bug | Metric id | RCA-claimed | Baseline measured | Target |
| --- | --- | --- | --- | --- | --- |
| 1 | D-02 rewritten over and over | `d02_churn` | 13 versions | **13** | ≤4 |
| 2 | Spec-refs embedded in code/test | `spec_ref_leak` | 65 (29 prod + 36 test) | **44** (29 prod + 15 test) | 0 |
| 3 | REQ-040/041/042 have no matrix row | `req_without_matrix_row` | 3 | **3** (040/041/042) | 0 |
| 4 | Phase gates PASSED on stale model | `gate_false_pass` | 3 | **2** structural (+1 stale-only, see note) | 0 |
| 5 | Code is 100% old model (drift vs v2.3) | `model_drift` | "code 100% old model" | **5** design tokens absent from code | 0 missing |
| 6 | Manual cascade rounds | `recascade` | 4+ | *historical — not snapshot-derivable* (documented ≥4) | 1 |

### Note on metric 2 (spec-ref count)

The fixture self-measures the **feature code slice** (`code/`): 29 prod + 15 test
= 44. The **prod count matches the RCA exactly (29)**, which validates the counting
method. The RCA test headline (36) used a broader/earlier count (e.g. the whole
`project_invoice` test suite measures 54); the fixture deliberately counts only the
feature's own `resource_plan*` files, which is the scope the `spec_ref 65→0` target
applies to. The harness reports both the measured number and the RCA headline so
neither is hidden.

### Note on metric 4 (gate false-pass: 2 structural vs RCA 3)

All three phase gates PASSED on a stale model, so in hindsight all three are
false-passes (the RCA's "3"). But the harness counts only the **structurally
detectable** ones — a gate PASSED while it had an item failure (`failed>0`) or a
manual/override evaluation. That is P2 (`failed:1` + "manual fallback after evaluator
crash") and P3 (`failed:1`) = **2**. P1 PASSED cleanly (`failed:0`, no override); its
falseness is only knowable by cross-referencing the *later* model drift — that is the
build-graph's job (TA.1), not a single-gate check, so it is listed as
`stale_pass_context`, not counted. Counting only the structural signal keeps the
metric **measurable after remediation**: once TD.4 re-runs real gates on v2.3, the
signal clears and the count → 0 (a plain "count PASSED gates" would wrongly stay at 3).

### Note on test count (87, not the RCA "146")

The fixture's `code/tests/` carries **87 test functions** — matching the RCA's
"87 test PASSED" figure (RCA §1). The RCA also cites "146 test" as the later/broader
count locking the old model; the fixture freezes the feature's own `resource_plan*`
suite (87), which is the slice the metrics measure.

### The 4 bugs the TA.0 spike must catch (build-graph GO bar)

1. gate-STALE after the v2.0 U-turn → `artifacts/gates/` + D-02 frontmatter
2. matrix missing REQ-040/041/042 → `matrix.md` vs D-02
3. MODEL_DRIFT code↔v2.3 → D-19 design tokens absent from `code/`
4. request/snapshot slice missing → task-breakdown vs D-02 v2.3

## Re-measure / verify integrity

```bash
python process-review/metrics/hbc_metrics_harness.py            # JSON to stdout
python process-review/fixtures/fixture_integrity.py --check     # verify nothing changed
python -m pytest process-review/metrics/tests                   # assert baselines + integrity
```

If you ever need to *deliberately* re-snapshot (rare — the point is to freeze),
update the files then regenerate the manifest with
`python process-review/fixtures/fixture_integrity.py --write` and adjust the pinned
baselines in `process-review/metrics/tests/`.
