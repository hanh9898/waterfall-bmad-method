# v_pair-edge enforcement (TA.6 — V-Model design↔test coverage)

The deliverable catalog (`hbc-shared/references/deliverable-catalog.yaml`) declares,
per design deliverable, the V-Model **test level** it must be paired with — its
`v_pair`:

| Deliverable | v_pair (required test level) |
| --- | --- |
| D-02 Requirements, D-06 Business Flow | `acceptance` |
| D-09 Architecture, D-19 ER/Data, D-21 API Spec | `integration-test` |
| D-16 Behavioral Design, D-27 Test Spec | `unit-test` |
| D-14 UX/Screen | `e2e-test` |
| D-03, D-12, D-26, constitution, … (`v_pair: null`) | — none — |

A design deliverable that **exists** for a feature must carry that v_pair edge in
the traceability matrix: the requirements it contributes to must actually be traced
to a test (a non-empty `test_ref`). A missing v_pair edge is a real V-Model gap — a
model designed in D-19 with no integration-test edge, the 040/041/042 requirements
designed but never test-traced.

## Run

```
python3 {skill-root}/scripts/check-vpair.py --feature-dir <feature-dir>
```

Builds on the TA.1 build-graph kernel (`hbc_buildgraph`): the requirement universe
is the upstream D-02 node (matrix-as-view, so the matrix can't silently omit a REQ),
and `present_design_deliverables` is read from the filesystem so an **absent**
deliverable is never flagged. Exit `0` no gap · `1` ≥1 gap · `2` io error.

## Severity model

For each PRESENT design deliverable that declares a non-null `v_pair: L`:

| Status | Severity | When |
| --- | --- | --- |
| `MISSING` | `high` | the whole pairing is absent — no matrix node, or the matrix carries **no** test edge for any requirement (`test_ref` blank everywhere). |
| `MISSING` | `medium` | the pairing is **partial** — some requirements have no test edge (a REQ in D-02 with no matrix row, or a row with blank `test_ref`). `uncovered_reqs` lists them. |
| `present` | — | every requirement carries a test edge. |

Deliverables with `v_pair: null` declare no pairing and are skipped. An absent /
N-A-by-catalog deliverable has nothing to pair and is **not** flagged MISSING.

## Scope boundary (machine floor; T3.12 forward-ref)

This is the machine **FLOOR**: does a test EDGE exist for each requirement of a
present, v_pair-bearing design deliverable. Whether the traced test is actually **at
level L** (an integration test, not a unit test) needs the per-row test-level
**label**, which lives in D-26/D-27's level sections (often absent at matrix time).
That level-MATCH is surfaced as an honest `level_match: pending` — the V-Model
surface (T3.12) owns it; TA.6 does not decide it.
