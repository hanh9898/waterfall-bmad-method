#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Build-graph view for hbc-traceability (TA.1 — build-graph kernel).

Constructs the HBC artifact build-graph for one feature directory and emits the
graph state as JSON. This is the thin wiring around the kernel
(`hbc-shared/lib/hbc_buildgraph.py`): the kernel owns the graph/hash/dirty logic;
this script locates the feature's artifacts, loads them into a graph, and prints
the derived view.

The matrix is treated as a VIEW computed FROM the graph (not a hand-maintained
table): `matrix_view` surfaces every REQ defined in the upstream D-02 node and
`missing_edges` flags the ones with no matrix row. `dirty_set` re-derives staleness
from current artifact state (a living graph), and `ground_truth_drift` exposes the
machine-floor code↔design drift signal (the reconcile VERDICT is TA.2, not here).

Output JSON (stdout):
  {
    "feature": "<dir name>",
    "dirty_set": {node: [reasons]},
    "matrix_view": {reqs, rows, missing_edges, ...},
    "missing_edges": [REQ ids defined in D-02 with no matrix row],
    "ground_truth_drift": [{design_node, ground_truth_node, design_only, code_only, drift}],
    "edges": [[downstream, upstream], ...],
    "nodes": {id: {kind, version, hash, sources, reconcile_to}}
  }

Run with `python` (Windows dev) or `python3` (Linux/Mac CI):
    python3 {skill-root}/scripts/build-graph.py --feature-dir <dir>

Exit: 0 graph built · 2 io error (feature dir missing / no D-02 present).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- shared lib bootstrap (parents[2] → hbc-shared/lib) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_buildgraph import load_corpus, graph_report  # noqa: E402
except Exception as exc:  # pragma: no cover - import wiring
    print(json.dumps({"error": f"cannot import hbc_buildgraph: {exc}"}), file=sys.stderr)
    raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the HBC artifact build-graph for a feature.")
    ap.add_argument("--feature-dir", required=True,
                    help="Feature directory containing the artifacts (planning/, code/, gates/, ...).")
    args = ap.parse_args(argv)

    root = Path(args.feature_dir)
    if not root.is_dir():
        print(json.dumps({"error": f"feature dir not found: {root}"}), file=sys.stderr)
        return 2

    g = load_corpus(root)
    if g.get("D-02") is None and not any(n.kind == "doc" for n in g.nodes.values()):
        print(json.dumps({"error": f"no D-02 (requirements) artifact found under {root}"}),
              file=sys.stderr)
        return 2

    report = graph_report(g)
    out = {
        "feature": root.name,
        "dirty_set": report["dirty_set"],
        "matrix_view": report["matrix_view"],
        "missing_edges": report["missing_edges"],
        "ground_truth_drift": report["ground_truth_drift"],
        "edges": report["edges"],
        "nodes": report["nodes"],
        "stale_edges": report["stale_edges"],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
