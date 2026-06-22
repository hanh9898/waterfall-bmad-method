#!/usr/bin/env python3
"""Tests for the build-graph kernel (TA.1) — hbc_buildgraph.py.

Covers: content-hash determinism/normalization, sources-edges, dirty-set (direct +
transitive + cycle + None-safety), matrix-as-view, missing-edges, ground-truth
drift, and the living-graph proof on BOTH corpora (broken → non-empty signal,
clean → empty). Run via pytest or `python test_hbc_buildgraph.py`.
"""
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_LIB))

from hbc_buildgraph import (  # noqa: E402
    BuildGraph,
    Node,
    content_hash,
    load_corpus,
    feature_dirs,
    graph_report,
)

# repo root: lib/tests → lib → hbc-shared → src → repo
_REPO = _LIB.parents[2]
BROKEN = _REPO / "process-review" / "fixtures" / "resource-plan-billable"
CLEAN = _REPO / "process-review" / "spikes" / "ta0" / "corpus-clean"


# --- content-hash ----------------------------------------------------------

def test_content_hash_deterministic():
    assert content_hash("hello\nworld") == content_hash("hello\nworld")


def test_content_hash_normalizes_line_endings_and_trailing_ws():
    assert content_hash("a\r\nb \t") == content_hash("a\nb")


def test_content_hash_none_is_empty():
    assert content_hash(None) == content_hash("")


def test_content_hash_distinguishes_real_change():
    assert content_hash("model: old") != content_hash("model: new")


# --- node / graph construction --------------------------------------------

def test_add_rejects_unknown_kind():
    g = BuildGraph()
    try:
        g.add(Node(id="X", kind="bogus"))
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown kind")


def test_edges_skip_missing_upstream():
    g = BuildGraph()
    g.add(Node(id="X", kind="doc", sources={"GHOST": "v1.0"}))
    assert g.edges() == []  # upstream not in graph → no edge, no crash


def test_edges_declared_from_sources():
    g = BuildGraph()
    g.add(Node(id="D-02", kind="doc", text="r", version="1.0"))
    g.add(Node(id="matrix", kind="matrix", text="m", sources={"D-02": g.get("D-02").hash}))
    assert ("matrix", "D-02") in g.edges()


# --- dirty-set -------------------------------------------------------------

def _chain():
    """A→B→C clean chain: B records A's hash, C records B's hash."""
    g = BuildGraph()
    g.add(Node(id="A", kind="doc", text="v1", version="1.0"))
    g.add(Node(id="B", kind="doc", text="b", sources={"A": g.get("A").hash}))
    g.add(Node(id="C", kind="matrix", text="c", sources={"B": g.get("B").hash}))
    return g


def test_dirty_set_empty_when_in_sync():
    assert _chain().dirty_set() == {}


def test_dirty_set_direct_on_hash_mismatch():
    g = _chain()
    g.get("A").text = "v2"  # A moved; B recorded the old hash
    ds = g.dirty_set()
    assert "B" in ds and any(r.startswith("direct:") for r in ds["B"])


def test_dirty_set_propagates_transitively():
    g = _chain()
    g.get("A").text = "v2"
    ds = g.dirty_set()
    assert "C" in ds, "dirtying A must dirty C transitively (A→B→C)"
    assert any("transitive" in r for r in ds["C"])


def test_dirty_set_legacy_version_string():
    g = BuildGraph()
    g.add(Node(id="D-19", kind="doc", text="d", version="2.3"))
    g.add(Node(id="task-breakdown", kind="task-breakdown", text="t",
               sources={"D-19": "v1.3"}))  # recorded stale version string
    ds = g.dirty_set()
    assert "task-breakdown" in ds


def test_dirty_set_version_match_not_stale():
    g = BuildGraph()
    g.add(Node(id="D-19", kind="doc", text="d", version="2.3"))
    g.add(Node(id="task-breakdown", kind="task-breakdown", text="t",
               sources={"D-19": "v2.3"}))
    assert g.dirty_set() == {}


def test_dirty_set_cycle_safe():
    g = BuildGraph()
    g.add(Node(id="A", kind="doc", text="a", sources={"B": "deadbeef" * 8}))
    g.add(Node(id="B", kind="doc", text="b", sources={"A": "cafef00d" * 8}))
    ds = g.dirty_set()  # must terminate (no hang)
    assert set(ds) == {"A", "B"}


def test_dirty_set_deterministic():
    g = _chain()
    g.get("A").text = "v2"
    assert json.dumps(g.dirty_set(), sort_keys=True) == json.dumps(g.dirty_set(), sort_keys=True)


# --- matrix-as-view + missing edges ---------------------------------------

def _matrix_graph(d02_reqs, matrix_reqs):
    g = BuildGraph()
    d02 = "## Functional Requirements\n\n| REQ ID | Desc |\n|---|---|\n" + \
        "".join(f"| REQ-F-{n:03d} | x |\n" for n in d02_reqs)
    mtx = "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n" + \
        "|---|---|---|---|---|---|---|---|\n" + \
        "".join(f"| f | REQ-F-{n:03d} | | E | c.py | TC-{n:03d} | | 2026 |\n" for n in matrix_reqs)
    g.add(Node(id="D-02", kind="doc", text=d02, version="1.0"))
    g.add(Node(id="matrix", kind="matrix", text=mtx, sources={"D-02": g.get("D-02").hash}))
    return g


def test_matrix_view_reqs_from_d02_not_matrix():
    g = _matrix_graph([1, 2, 3], [1, 2])  # matrix omits REQ-003
    view = g.matrix_view()
    assert "REQ-F-003" in view["reqs"], "REQ universe derives from D-02, not matrix rows"
    assert view["missing_edges"] == ["REQ-F-003"]


def test_matrix_view_rows_carry_trace_cells():
    g = _matrix_graph([1], [1])
    rows = g.matrix_view()["rows"]
    assert rows["REQ-F-001"]["code_ref"] == "c.py"
    assert rows["REQ-F-001"]["test_ref"] == "TC-001"


def test_missing_edges_empty_when_matrix_complete():
    g = _matrix_graph([1, 2], [1, 2])
    assert g.missing_edges() == []


def test_missing_edges_empty_without_d02_or_matrix():
    g = BuildGraph()
    g.add(Node(id="code", kind="code", text=""))
    assert g.missing_edges() == []


# --- ground-truth drift ----------------------------------------------------

def test_ground_truth_drift_detected():
    g = BuildGraph()
    g.add(Node(id="code", kind="code", text="class P:\n    _name = 'old.model'\n"))
    g.add(Node(id="D-19", kind="doc",
               text="Physical name (Tên vật lý): `new.model`\n",
               reconcile_to="code"))
    drift = g.ground_truth_drift()
    assert len(drift) == 1 and drift[0]["drift"] is True
    assert "new.model" in drift[0]["design_only"]


def test_ground_truth_drift_clean_when_aligned():
    g = BuildGraph()
    g.add(Node(id="code", kind="code", text="_name = 'm.model'\n"))
    g.add(Node(id="D-19", kind="doc",
               text="Physical name: `m.model`\n", reconcile_to="code"))
    assert g.ground_truth_drift()[0]["drift"] is False


def test_ground_truth_drift_skips_non_code_target():
    g = BuildGraph()
    g.add(Node(id="D-19", kind="doc", text="x", reconcile_to="nowhere"))
    assert g.ground_truth_drift() == []


# --- living-graph proof on BOTH corpora -----------------------------------

def test_living_graph_broken_fixture_non_empty():
    g = load_corpus(BROKEN)
    assert g.dirty_set(), "broken fixture must have a non-empty dirty-set"
    assert g.missing_edges(), "broken fixture matrix must miss REQ rows"
    me = set(g.missing_edges())
    assert any("040" in r for r in me) and any("041" in r for r in me) and any("042" in r for r in me)
    drift = g.ground_truth_drift()
    assert drift and drift[0]["drift"] is True


def test_living_graph_broken_gate_and_taskbreakdown_stale():
    g = load_corpus(BROKEN)
    ds = g.dirty_set()
    assert "gate" in ds and "task-breakdown" in ds


def test_living_graph_clean_corpus_empty():
    feats = feature_dirs(CLEAN)
    assert len(feats) >= 2, "clean corpus must be multi-feature (else proof is vacuous)"
    for fd in feats:
        g = load_corpus(fd)
        # all six nodes present → no detector skipped because input is missing
        assert {"D-02", "D-19", "matrix", "task-breakdown", "gate", "code"} <= set(g.nodes), fd.name
        assert g.dirty_set() == {}, f"{fd.name}: clean corpus must have empty dirty-set"
        assert g.missing_edges() == [], f"{fd.name}: clean corpus must have no missing edges"
        assert all(d["drift"] is False for d in g.ground_truth_drift()), f"{fd.name}: no false drift"


def test_graph_report_deterministic_on_fixture():
    a = json.dumps(graph_report(load_corpus(BROKEN)), sort_keys=True)
    b = json.dumps(graph_report(load_corpus(BROKEN)), sort_keys=True)
    assert a == b


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
