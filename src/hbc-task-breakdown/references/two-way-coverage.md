# Two-way 100%-rule coverage (TA.5 / IMP-05)

The machine bidirectional REQ↔task coverage check emitted by `check-task-coverage.py`
as `two_way_coverage`. Advisory — the blocking enforcement stays with
`hbc-check-implementation-readiness` [IR] and the phase gate; this is the machine
coverage *signal*.

## How it uses the build-graph (a view, not a re-parse)

D-02 and the task-breakdown are added as nodes to the TA.1 build-graph kernel
(`hbc-shared/lib/hbc_buildgraph.py`): D-02 as a `doc` node, the breakdown as a
`task-breakdown` node. The coverage is then derived from the living graph's node
**text** — not from a hand-maintained matrix table. This mirrors the kernel's own
`matrix_view` / `missing_edges` design: the REQ universe is taken from the D-02 node,
so a breakdown can't silently omit a REQ by under-counting its own rows. Re-running
the kernel on current artifact state re-derives the result; nothing is cached.

## The two directions

- **REQ→task** (`reqs_without_task`, B4-7) — every REQ defined in the D-02 node has
  ≥1 task referencing it. Reuses the local shorthand-aware `reqs_without_task` so a
  dense `REQ-005/006/007` cell is expanded (5, 6, 7 each count as cited) and isn't
  false-flagged. A missed REQ is a missed vertical slice — the exact case failure
  (REQ-040/041/042 never got a task).
- **task→REQ** (`orphan_tasks`, TA.5) — every task maps to ≥1 **live** REQ. An
  **orphan** task cites REQ number(s) **none of which** still exist in D-02 — a
  stale/dangling reference to a REQ that was renumbered or removed. Each entry is
  `{task_id, dangling: [bare ids]}`.

`two_way_complete` is `true` iff **both** `reqs_without_task` and `orphan_tasks` are
empty.

## Identity: trailing number

A requirement's identity is its trailing number, so the canonical id
(`REQ-FEAT-040`) and the bare prose form (`REQ-040`) reconcile — a task citing
`REQ-040` against a D-02 defining `REQ-FEAT-040` is **not** a false orphan. This
matches `req_num_map` / `reqs_without_task` / `missing_from_matrix` in the shared lib.

## Tasks citing no REQ (`tasks_without_req`)

A task that cites **zero** REQ (legitimate for infra/scaffold slices — manifest,
CI, security stubs) is reported separately as `tasks_without_req` and does **not**,
on its own, fail the two-way rule. Whether such a task is *legitimately* REQ-free is
LLM/semantic judgment (Stage 4c), not a machine verdict — so the machine surfaces it
without failing on it. Only dangling references fail the rule.

## Output shape

```json
{
  "two_way_coverage": {
    "reqs_without_task": ["REQ-FEAT-040", "REQ-FEAT-041", "REQ-FEAT-042"],
    "orphan_tasks": [{"task_id": "TASK-009", "dangling": ["REQ-999"]}],
    "tasks_without_req": ["TASK-001"],
    "two_way_complete": false
  }
}
```

`two_way_coverage` is `null` when no `--d02` is supplied — the REQ universe is then
unknown, so the rule cannot be run (the forward direction is also skipped).

## Determinism & safety

Deterministic (sorted output, no time/random/path input), None-safe (empty/missing
text yields empty lists and `two_way_complete: true` vacuously), and reuses the
shared primitives — no second, divergent parser.
