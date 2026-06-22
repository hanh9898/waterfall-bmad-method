#!/usr/bin/env python
"""TA.0 build-graph kernel (THROWAWAY SPIKE — not shippable).

Models the HBC artifact set as a BUILD GRAPH per the redesign doc §3:

  - each artifact (D-02, D-19, matrix, task-breakdown, gate-report, code) is a NODE
  - edges are declared by a node's `sources:` (what it derives from)
  - each node carries a content-hash of its source-of-record
  - when an upstream node's hash changes, downstream nodes whose RECORDED
    source-hash no longer matches go into a dirty-set (STALE) — transitively
  - a GROUND-TRUTH node (the real code) is what design nodes reconcile against

The graph + dirty-set is what CATCHES the 4 known errors. The 4 leaf detections
lean on the shared hbc_validation primitives (missing_from_matrix, model_drift,
model_tokens_from_design, reqs_without_task) but the STALENESS / MISSING-EDGE /
HASH-MISMATCH evidence comes from the graph, not from hardcoded answers.

stdlib only + a sys.path bootstrap to the shared lib. Run with `python`.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

# --- bootstrap the shared validation lib (leaf-checks only) ----------------
import sys

_REPO_ROOT = Path(__file__).resolve().parents[4]  # .../stc-erp-bmad-custom
sys.path.insert(0, str(_REPO_ROOT / "src" / "hbc-shared" / "lib"))
from hbc_validation import (  # noqa: E402
    missing_from_matrix,
    model_drift,
    model_tokens_from_design,
    reqs_without_task,
    req_num_map,
    doc_version,
    REQ_ID_RE,
)


# ===========================================================================
# GRAPH PRIMITIVES — the novel part of the spike
# ===========================================================================


def content_hash(text: str) -> str:
    """Stable content-hash of a node's source-of-record. SHA-256 over the
    NORMALIZED text (line endings unified, trailing whitespace trimmed) so a
    CRLF/LF or trailing-space difference is not mistaken for a real change.
    Deterministic — no time/random input — so re-runs are identical."""
    norm = "\n".join(line.rstrip() for line in (text or "").replace("\r\n", "\n").split("\n"))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


@dataclass
class Node:
    """A build-graph node = one artifact (or the ground-truth code node).

    sources: maps an UPSTREAM node id -> the source-of-record token this node
    recorded when it was last built. The token is either a content-hash
    (preferred, what the kernel emits going forward) OR a legacy version-string
    like "v1.8" (what HBC artifacts carry today via `sources: D-19 v1.3`).
    The kernel reconciles whichever form is present against the upstream node's
    CURRENT hash / version.
    """

    id: str
    kind: str                       # doc | matrix | task-breakdown | gate | code
    text: str = ""
    version: str | None = None      # declared version (frontmatter), if any
    sources: dict[str, str] = field(default_factory=dict)  # upstream-id -> recorded token
    reconcile_to: str | None = None  # ground-truth node id this design node reconciles against

    @property
    def hash(self) -> str:
        return content_hash(self.text)


_LEGACY_VER_RE = re.compile(r"^v?(\d+\.\d+(?:\.\d+)?)$", re.IGNORECASE)


class BuildGraph:
    """The HBC artifact set as a dependency graph with a dirty-set."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}

    def add(self, node: Node) -> None:
        self.nodes[node.id] = node

    # --- edges -------------------------------------------------------------
    def edges(self) -> list[tuple[str, str]]:
        """(downstream, upstream) edges declared by every node's `sources:`."""
        out: list[tuple[str, str]] = []
        for n in self.nodes.values():
            for up in n.sources:
                if up in self.nodes:
                    out.append((n.id, up))
        return out

    def _recorded_matches_current(self, node: Node, up_id: str) -> tuple[bool, str]:
        """Does `node`'s recorded source token for `up_id` still match upstream's
        CURRENT state? Returns (matches, evidence). Handles both hash-form and
        legacy version-string-form recorded tokens."""
        recorded = node.sources[up_id]
        up = self.nodes[up_id]
        mv = _LEGACY_VER_RE.match(recorded.strip())
        if mv:  # recorded a version string (the legacy `sources: D-19 v1.3` form)
            current = (up.version or "").lstrip("vV")
            ok = current == mv.group(1)
            return ok, f"recorded v{mv.group(1)} vs current v{current or '?'}"
        # recorded a content-hash
        ok = recorded == up.hash
        return ok, f"recorded hash {recorded[:8]} vs current {up.hash[:8]}"

    def stale_edges(self) -> list[dict]:
        """Edges whose downstream node's recorded source token no longer matches
        the upstream node's current hash/version. Each is direct staleness."""
        out: list[dict] = []
        for n in self.nodes.values():
            for up_id in n.sources:
                if up_id not in self.nodes:
                    continue
                ok, ev = self._recorded_matches_current(n, up_id)
                if not ok:
                    out.append({"node": n.id, "source": up_id, "evidence": ev})
        return out

    def dirty_set(self) -> dict[str, list[str]]:
        """Nodes that are STALE: directly (recorded source token mismatches
        upstream current state) OR transitively (an upstream node is itself
        dirty). Propagated by BFS over the sources-edges. Returns
        {dirty_node_id: [reasons]}."""
        dirty: dict[str, list[str]] = {}
        # seed: direct staleness
        for e in self.stale_edges():
            dirty.setdefault(e["node"], []).append(
                f"direct: source '{e['source']}' changed ({e['evidence']})"
            )
        # propagate: any node whose source is dirty becomes dirty too
        changed = True
        while changed:
            changed = False
            for n in self.nodes.values():
                if n.id in dirty:
                    continue
                for up_id in n.sources:
                    if up_id in dirty:
                        dirty.setdefault(n.id, []).append(
                            f"transitive: upstream '{up_id}' is dirty"
                        )
                        changed = True
                        break
        return dirty


# ===========================================================================
# LEAF DETECTIONS — graph-state queries (evidence from the graph, not hardcoded)
# ===========================================================================


def detect_gate_stale(g: BuildGraph) -> dict | None:
    """ERROR 1 — gate-STALE. A gate node is dirty (its recorded source token for
    an upstream design/requirements node no longer matches that node's current
    hash/version). Evidence = the dirty-set entry, derived purely from the graph."""
    dirty = g.dirty_set()
    gate_dirty = {nid: rs for nid, rs in dirty.items() if g.nodes[nid].kind == "gate"}
    if not gate_dirty:
        return None
    return {
        "error": "gate-STALE",
        "nodes": sorted(gate_dirty),
        "evidence": gate_dirty,
    }


def detect_matrix_missing_reqs(g: BuildGraph) -> dict | None:
    """ERROR 2 — matrix missing REQ-040/041/042. The matrix node derives from the
    D-02 node (a sources-edge); a coverage gap = REQ ids present in the upstream
    D-02 node but with no edge (row) in the matrix node. Leaf-check via
    missing_from_matrix; the EDGE comes from the graph."""
    matrix = next((n for n in g.nodes.values() if n.kind == "matrix"), None)
    if matrix is None:
        return None
    d02_ids = [up for up in matrix.sources if g.nodes.get(up) and g.nodes[up].kind == "doc"
               and g.nodes[up].id.startswith("D-02")]
    if not d02_ids:
        return None
    d02 = g.nodes[d02_ids[0]]
    missing = missing_from_matrix(d02.text, matrix.text)
    if not missing:
        return None
    return {
        "error": "matrix-missing-reqs",
        "missing_edges": missing,
        "evidence": f"matrix node '{matrix.id}' has no edge for {len(missing)} REQ(s) "
                    f"defined in upstream '{d02.id}': {', '.join(missing)}",
    }


def detect_model_drift(g: BuildGraph) -> dict | None:
    """ERROR 3 — MODEL_DRIFT code↔v2.3. A design node (D-19) carries a reconcile
    edge to the ground-truth code node. Drift = D-19 model tokens absent from the
    code node's content (hash of the two no longer reconciles). Leaf-check via
    model_drift; the reconcile EDGE + ground-truth node come from the graph."""
    design = next((n for n in g.nodes.values()
                   if n.reconcile_to and g.nodes.get(n.reconcile_to)
                   and g.nodes[n.reconcile_to].kind == "code"), None)
    if design is None:
        return None
    gt = g.nodes[design.reconcile_to]
    # field-level tokens the metrics harness also tracks (request/snapshot model).
    # Only count those the DESIGN actually declares — never inject a token the
    # design doesn't mention (that would manufacture drift on an unrelated feature).
    candidate_fields = {"active_request_id", "snapshot_hash", "request_line"}
    extra = {t for t in candidate_fields if re.search(r"(?<![\w.])" + re.escape(t) + r"(?![\w.])", design.text)}
    drift = model_drift(design.text, gt.text, extra_tokens=extra)
    if not drift["drift"]:
        return None
    return {
        "error": "model-drift",
        "design_node": design.id,
        "ground_truth_node": gt.id,
        "design_only": drift["design_only"],
        "code_only": drift["code_only"],
        "evidence": f"reconcile({design.id} -> {gt.id}) FAILED: design tokens absent "
                    f"from code: {', '.join(drift['design_only'])}",
    }


def _request_snapshot_reqs(d02_text: str) -> list[str]:
    """REQ ids in D-02 whose requirement TEXT introduces the new request/snapshot
    model. Detected structurally: a REQ-table row (cell starting with the REQ id)
    whose row text mentions 'request'/'snapshot' (the v2.3 U-turn vocabulary).
    This isolates the NEW slices the old task-breakdown could not have covered,
    rather than relying on a hardcoded {040,041,042}."""
    out: list[str] = []
    for line in d02_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        m = REQ_ID_RE.search(s.split("|", 2)[1] if s.count("|") >= 2 else s)
        if not m:
            continue
        if re.search(r"\brequest\b|\bsnapshot\b", s, re.IGNORECASE):
            out.append(m.group(0))
    return sorted(set(out), key=lambda r: (len(r), r))


def detect_taskbreakdown_missing_slices(g: BuildGraph) -> dict | None:
    """ERROR 4 — request/snapshot slice missing. The task-breakdown node derives
    from D-02 (a sources-edge). A slice gap = a REQ in upstream D-02 with no task
    in the task-breakdown node. Leaf-check via reqs_without_task; the EDGE comes
    from the graph. The catch is keyed on the NEW request/snapshot reqs being
    absent (the v2.3 U-turn slices), so over-counting on compound-cell REQ refs
    can't falsely satisfy the bar."""
    tb = next((n for n in g.nodes.values() if n.kind == "task-breakdown"), None)
    if tb is None:
        return None
    d02_ids = [up for up in tb.sources if g.nodes.get(up) and g.nodes[up].id.startswith("D-02")]
    if not d02_ids:
        return None
    d02 = g.nodes[d02_ids[0]]
    d02_req_ids = list(req_num_map(d02.text)[0].values())
    all_missing = reqs_without_task(d02_req_ids, tb.text)
    if not all_missing:
        return None
    # the load-bearing subset: NEW request/snapshot reqs with no slice
    rs_reqs = _request_snapshot_reqs(d02.text)
    missing_nums = {int(re.search(r"\d+$", r).group()) for r in all_missing}
    rs_missing = sorted(r for r in rs_reqs
                        if int(re.search(r"\d+$", r).group()) in missing_nums)
    if not rs_missing:
        return None  # the specific request/snapshot gap is what the bar requires
    return {
        "error": "taskbreakdown-missing-slices",
        "missing_request_snapshot_slices": rs_missing,
        "all_missing_slices": all_missing,
        "evidence": f"task-breakdown node '{tb.id}' has no slice for the new "
                    f"request/snapshot REQ(s) from upstream '{d02.id}': "
                    f"{', '.join(rs_missing)} "
                    f"(broader slice gap: {len(all_missing)} REQ total)",
    }


DETECTORS = [
    ("gate-STALE", detect_gate_stale),
    ("matrix-missing-reqs", detect_matrix_missing_reqs),
    ("model-drift", detect_model_drift),
    ("taskbreakdown-missing-slices", detect_taskbreakdown_missing_slices),
]


def run_graph(g: BuildGraph) -> dict:
    """Run all 4 detectors over a built graph. Returns the caught errors with
    their graph evidence (no hardcoded expectations)."""
    caught = []
    for name, det in DETECTORS:
        hit = det(g)
        if hit:
            caught.append(hit)
    return {
        "dirty_set": g.dirty_set(),
        "stale_edges": g.stale_edges(),
        "caught": caught,
    }
