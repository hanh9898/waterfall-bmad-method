# Build-Graph view (TA.1 — build-graph kernel)

The matrix is a **view derived from a build-graph**, not a hand-maintained table.
`scripts/build-graph.py` constructs the HBC artifact dependency graph for one
feature and emits the graph state as JSON. It is thin wiring around the kernel
`hbc-shared/lib/hbc_buildgraph.py` (importable like `hbc_validation`); the kernel
owns all graph/hash/dirty logic.

```
python3 {skill-root}/scripts/build-graph.py --feature-dir <feature-dir>
```

`<feature-dir>` is the feature's artifact tree — either the per-feature layout
(`planning/`, `implementation/`, `traceability/`, `gates/`, `code/`) or the nested
`artifacts/…` + sibling `code/` layout. Missing files are skipped; the graph is
built from whatever is present.

## What it is

- **Node** — each artifact (D-02, D-19, matrix, task-breakdown, gate) + a
  first-class **ground-truth `code` node**. Source-of-record = the node's text.
- **content-hash** — deterministic SHA-256 over normalized text (CRLF→LF, trailing
  whitespace trimmed); no time/random, so re-runs are byte-identical.
- **Edge** — declared by a node's `sources:` map (what it derives from), recorded as
  a content-hash (preferred) or a legacy version-string (`sources: D-19 v1.3`, what
  artifacts carry today). Aligns with `deliverable-catalog.yaml`'s
  `reconcile_seam`/`ground_truth`.
- **dirty-set** — a node is STALE if its recorded source token no longer matches the
  upstream node's current hash/version (direct), or any upstream is itself dirty
  (transitive). A *living graph*: re-running re-derives the dirty-set from current
  state — nothing cached.

## Output (stdout JSON)

| Key | Meaning |
| --- | --- |
| `dirty_set` | `{node: [reasons]}` — stale nodes (direct + transitive). Non-empty ⇒ something downstream was never re-derived. |
| `matrix_view` | the REQ→design→code→test matrix computed FROM the graph (`reqs` from upstream D-02, `rows` from the matrix node). |
| `missing_edges` | REQs defined in D-02 with NO matrix row (the "39/39 green but 040/041/042 never added" failure). |
| `ground_truth_drift` | per design node: `{design_node, ground_truth_node, design_only, code_only, drift}` — the machine-FLOOR code↔design drift signal. |
| `edges` / `nodes` / `stale_edges` | the raw graph for inspection. |

## Scope boundary

This is the **machine floor only** (structure/graph/hash). The reconcile *verdict*
(machine-floor + semantic-ceiling, CONTESTED) is **TA.2**; gate RECYCLE (TA.3),
2-tier exit-criteria (TA.4), 100%-rule coverage (TA.5), v_pair-edge enforcement
(TA.6), `hbc-rebaseline` (TA.7), circuit-breaker (TA.8) build ON these kernel APIs —
they are not implemented here. Whether drift is *meaningful* (rename vs real
divergence) is the LLM layer, never Python.

## Relation to the cascade pre-check

`cascade-precheck.py` is the minimal, ship-now enforcement gate (B7-1/3/5/6); this
build-graph view is the kernel that supersedes the version-set/drift-watch heuristics
once trục A lands. They share the shared primitives (`missing_from_matrix`,
`model_drift`, `version_coherence`) and agree on the TD.0 fixture's known failures.
