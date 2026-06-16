#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["hypothesis"]
# ///
"""Property-based tests for hbc-sync (PBT Partial mode: PBT-02,03,07,08,09).

Properties (functional-design/testable-properties.md):
  P-1 DAG validity invariant            (PBT-03)
  P-2 downstream closure invariant      (PBT-03)
  P-3 topological order invariant       (PBT-03)
  P-4 state round-trip                  (PBT-02)
  P-5 cascade idempotence (no-op)       (PBT-03)
  P-6 shared-node single-visit          (PBT-03)
  P-7 selection-gap closure             (PBT-03)

Generators (PBT-07) build domain-valid DAGs, not raw primitives. Shrinking is
left enabled (PBT-08). Run: pytest test_properties.py  (or python test_properties.py).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
from sync_common import (  # noqa: E402
    body_hash, close_gaps, descendants, selection_gaps, topological_order,
)


def _load_module(filename: str, mod_name: str):
    """Import a hyphenated script file (e.g. load-graph.py) as a module."""
    spec = importlib.util.spec_from_file_location(mod_name, SCRIPTS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


load_graph = _load_module("load-graph.py", "load_graph_mod")


# --- Generators (PBT-07) -----------------------------------------------------

@st.composite
def dag_strategy(draw, max_nodes: int = 8):
    """Generate a valid DAG as {node_id: {"depends_on": [...]}}.

    Construction guarantees acyclicity: nodes are laid out in a linear order and
    every edge points from a later node to an EARLIER one (depends_on = parents),
    so no cycle can form. Shared nodes arise naturally (a node may depend on
    several earlier nodes).
    """
    n = draw(st.integers(min_value=1, max_value=max_nodes))
    ids = [f"N{i}" for i in range(n)]
    graph: dict[str, dict] = {}
    for i, nid in enumerate(ids):
        earlier = ids[:i]
        parents = draw(st.lists(st.sampled_from(earlier) if earlier else st.nothing(),
                                unique=True, max_size=min(3, len(earlier))))
        graph[nid] = {"depends_on": parents}
    return graph


@st.composite
def graph_with_cycle_strategy(draw):
    """Generate a graph guaranteed to contain at least one cycle."""
    n = draw(st.integers(min_value=2, max_value=6))
    ids = [f"N{i}" for i in range(n)]
    graph = {nid: {"depends_on": []} for nid in ids}
    # Build a simple chain N0<-N1<-...<-N(n-1), then add a back edge to close a cycle.
    for i in range(1, n):
        graph[ids[i]]["depends_on"].append(ids[i - 1])
    graph[ids[0]]["depends_on"].append(ids[n - 1])  # back edge => cycle
    return graph


# --- P-1: DAG validity invariant --------------------------------------------

@given(dag_strategy())
@settings(max_examples=200)
def test_p1_valid_dag_has_no_cycle(graph):
    assert load_graph.find_cycle(graph) is None


@given(graph_with_cycle_strategy())
@settings(max_examples=100)
def test_p1_cycle_is_detected(graph):
    assert load_graph.find_cycle(graph) is not None


# --- P-2: downstream closure invariant --------------------------------------

@given(dag_strategy())
@settings(max_examples=200)
def test_p2_downstream_closure(graph):
    roots = set(list(graph)[:1])
    aff = descendants(graph, roots)
    # Every child of an affected node is also affected (closure).
    children = {n: [] for n in graph}
    for node, spec in graph.items():
        for p in spec["depends_on"]:
            children[p].append(node)
    for node in aff:
        for child in children[node]:
            assert child in aff


# --- P-3: topological order invariant ---------------------------------------

@given(dag_strategy())
@settings(max_examples=200)
def test_p3_topological_order(graph):
    subset = set(graph)
    order = topological_order(graph, subset)
    pos = {n: i for i, n in enumerate(order)}
    for node in subset:
        for parent in graph[node]["depends_on"]:
            if parent in subset:
                assert pos[parent] < pos[node]


# --- P-6: shared-node single visit ------------------------------------------

@given(dag_strategy())
@settings(max_examples=200)
def test_p6_each_node_once(graph):
    order = topological_order(graph, set(graph))
    assert len(order) == len(set(order)) == len(graph)


# --- P-7: selection-gap closure ---------------------------------------------

@given(dag_strategy(), st.randoms())
@settings(max_examples=200)
def test_p7_gap_closure(graph, rnd):
    affected = set(graph)
    sel = {n for n in graph if rnd.random() < 0.5}
    closed = close_gaps(graph, affected, sel)
    # After closing, no selected node has an affected, unselected parent.
    assert selection_gaps(graph, affected, closed) == []


# --- P-5: idempotence (no roots => empty affected) --------------------------

@given(dag_strategy())
@settings(max_examples=100)
def test_p5_no_change_is_noop(graph):
    assert descendants(graph, set()) == set()


# --- P-4: state round-trip (PBT-02) -----------------------------------------

@st.composite
def sync_state_strategy(draw):
    nodes = draw(st.lists(st.from_regex(r"[A-Za-z0-9_-]{1,8}", fullmatch=True),
                          unique=True, min_size=1, max_size=6))
    statuses = ["pending", "in_progress", "done", "blocked"]
    return {
        "sync_in_progress": True,
        "order": nodes,
        "node_status": {n: draw(st.sampled_from(statuses)) for n in nodes},
        "blocked": [],
    }


@given(sync_state_strategy())
@settings(max_examples=100, deadline=None)
def test_p4_state_round_trip(state):
    script = SCRIPTS_DIR / "sync-state.py"
    with tempfile.TemporaryDirectory() as tmp:
        sp = Path(tmp) / ".sync-state.json"
        subprocess.run([sys.executable, str(script), "--action", "save",
                        "--state-path", str(sp), "--payload", json.dumps(state)],
                       capture_output=True, text=True, encoding="utf-8")
        out = subprocess.run([sys.executable, str(script), "--action", "load",
                              "--state-path", str(sp)],
                             capture_output=True, text=True, encoding="utf-8")
        loaded = json.loads(out.stdout)
        for n, s in state["node_status"].items():
            assert loaded["node_status"][n] == s
        assert loaded["order"] == state["order"]


# --- body_hash determinism (supports BR-06 / P-5) ---------------------------

@given(st.text())
@settings(max_examples=100)
def test_body_hash_deterministic(text):
    assert body_hash(text) == body_hash(text)


@given(st.text(min_size=1))
@settings(max_examples=100)
def test_body_hash_ignores_frontmatter(body):
    doc_a = f"---\nupdated: 2026-01-01\n---\n{body}"
    doc_b = f"---\nupdated: 2026-12-31\nversion: 9\n---\n{body}"
    assert body_hash(doc_a) == body_hash(doc_b)


if __name__ == "__main__":
    # Lightweight runner when pytest is unavailable.
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("All hbc-sync property tests passed.")
