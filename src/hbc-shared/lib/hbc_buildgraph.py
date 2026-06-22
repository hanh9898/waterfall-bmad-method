#!/usr/bin/env python3
"""HBC build-graph kernel (TA.1) — the foundation of trục A enforcement.

WHAT THIS IS
============
HBC's artifacts (D-02, D-06, D-19, the traceability matrix, the task-breakdown,
the phase gate, the real code) form a *dependency graph* in the Make/Bazel sense:
each artifact is a target derived from upstream artifacts + the ground-truth code.
This module models that graph so the consistency questions HBC keeps re-asking —
"is this gate stale?", "is the matrix missing a requirement?", "did the code drift
from the design?" — become *queries on one substrate* instead of bespoke engines.

This is the productionized kernel proven by the TA.0 throwaway spike
(`process-review/spikes/ta0/`). The spike answered the risk question (do the
artifacts carry enough machine-parseable signal? — yes); this module is the real,
importable, tested version that TA.2–TA.8 build on.

DESIGN DECISIONS (the L·needs-design part)
==========================================
1. NODE — `Node(id, kind, text, version, sources, reconcile_to)`. Each artifact is
   one node. `kind` is one of doc | matrix | task-breakdown | gate | code. The
   *source-of-record* is the node's normalized `text`; everything derived (hash,
   tokens) is computed from it, never stored redundantly. The ground-truth code/DB
   is a first-class `code` node — a leaf with no upstream — so "grounding" is graph
   topology, not an afterthought a skill can forget.

2. CONTENT-HASH — `content_hash(text)` = SHA-256 over normalized text (CRLF→LF,
   trailing whitespace trimmed). Deterministic: no time, no random, no path input,
   so re-running on identical content yields an identical hash. This is what makes
   "frozen" a checkable hash snapshot rather than a sentiment.

3. EDGE — a directed (downstream → upstream) edge declared by a node's `sources:`
   map: `{upstream_id: recorded_token}`. The recorded token is what the downstream
   node captured about its upstream at build time, in EITHER form:
     * a content-hash (what the kernel emits going forward — `sha256:...` or bare
       64-hex), OR
     * a legacy version-string (`v1.8` / `2.3`) — what HBC artifacts carry today
       via `sources: D-02 v1.8 / D-19 v1.3`.
   The kernel reconciles whichever form is present against the upstream node's
   CURRENT hash/version. This deliberately matches the catalog's `reconcile_seam` /
   `ground_truth` schema (deliverable-catalog.yaml) so edges align with declared data.

4. DIRTY-SET — `dirty_set()`. A node is STALE if:
     * DIRECT: its recorded token for some upstream no longer matches that
       upstream's current hash/version, OR
     * TRANSITIVE: any upstream is itself dirty.
   Propagation is a BFS/fixpoint over the sources-edges. A "living graph" = re-run
   the kernel on current artifact state and the dirty-set re-derives itself; nothing
   is cached to disk. Cycle-safe (the fixpoint terminates because dirty only grows)
   and None-safe (missing upstream ids are skipped, never crash).

5. GROUND-TRUTH NODE & DRIFT — code/DB is a `code` leaf node. A design node carries
   `reconcile_to=<code_node_id>`. `ground_truth_drift()` exposes the drift signal by
   delegating to `hbc_validation.model_drift` (the shared primitive). The kernel only
   MODELS the node + edge + exposes the signal; the reconcile verdict logic
   (machine-floor + semantic-ceiling, CONTESTED) is TA.2 — deliberately deferred.

6. MATRIX-AS-VIEW — `matrix_view()`. The REQ→design→code→test matrix is COMPUTED
   from the graph (the D-02 node's REQ set + the matrix node's rows + the design/
   code edges), not read from a hand-maintained table. `missing_edges()` flags REQs
   defined upstream in D-02 with no row (edge) in the matrix node — reusing
   `missing_from_matrix` / `req_num_map`. A matrix can no longer silently omit a REQ
   because the view is derived from D-02, not from the matrix's own row count.

WHAT IS DEFERRED (clean APIs exposed, logic NOT implemented here)
=================================================================
  * TA.2 reconcile primitive (machine-floor + semantic-ceiling, CONTESTED state) —
    `ground_truth_drift()` exposes the machine-floor signal; the verdict ladder is TA.2.
  * TA.3 gate RECYCLE state-machine, TA.4 2-tier exit-criteria, TA.5 100%-rule
    coverage, TA.6 v_pair-edge enforcement, TA.7 hbc-rebaseline, TA.8 circuit-breaker.
  * Semantic judgement ("is this drift *meaningful*?", renamed-but-same-concept) —
    that is the LLM layer per CLAUDE.md's 3-layer rule, never Python.

This module is structure/graph/hash only (the machine floor). It is stdlib-only and
importable exactly like `hbc_validation` (same dir). Run helpers with `python`.
"""
from __future__ import annotations

import hashlib
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

# Shared leaf primitives — reuse, never duplicate (CLAUDE.md). Same-dir import; the
# bootstrap below also lets a corpus-loader run this file directly.
import sys

_LIB_DIR = Path(__file__).resolve().parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))
from hbc_validation import (  # noqa: E402
    missing_from_matrix,
    model_drift,
    model_tokens_from_design,
    parse_matrix,
    req_num_map,
    REQ_ID_RE,
)

VALID_KINDS = {"doc", "matrix", "task-breakdown", "gate", "code"}

# A recorded source token that is a legacy version-string (v1.8 / 2.3), vs a hash.
_LEGACY_VER_RE = re.compile(r"^v?(\d+\.\d+(?:\.\d+)?)$", re.IGNORECASE)
# A recorded source token that is a content-hash (optionally `sha256:`-prefixed).
_HASH_TOKEN_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$", re.IGNORECASE)


def content_hash(text: str) -> str:
    """Deterministic SHA-256 of a node's normalized source-of-record.

    Normalization unifies line endings (CRLF→LF) and trims trailing whitespace per
    line, so a CRLF/LF flip or a trailing space is NOT mistaken for a real change.
    No time/random/path input → identical text always yields the identical hash, so
    two kernel runs are byte-identical. ``None`` hashes as empty string.
    """
    norm = "\n".join(line.rstrip() for line in (text or "").replace("\r\n", "\n").split("\n"))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


@dataclass
class Node:
    """One build-graph node = one HBC artifact (or the ground-truth code node).

    sources: {upstream_id -> recorded_token}. The recorded token is what THIS node
    captured about that upstream when it was last built — a content-hash (preferred,
    what the kernel emits going forward) or a legacy version-string (what artifacts
    carry today). An upstream id with no node in the graph is tolerated (skipped).

    reconcile_to: id of the ground-truth node this design node reconciles against
    (e.g. D-19.reconcile_to == "code"). Modeled here; the reconcile verdict is TA.2.
    """

    id: str
    kind: str
    text: str = ""
    version: str | None = None
    sources: dict[str, str] = field(default_factory=dict)
    reconcile_to: str | None = None

    @property
    def hash(self) -> str:
        return content_hash(self.text)


class BuildGraph:
    """The HBC artifact set as a directed dependency graph with a derived dirty-set.

    Edges point downstream→upstream (a node → what it derives from). The graph holds
    no cached state: every query (edges, dirty-set, matrix view, drift) recomputes
    from current node text — that is what makes it a *living* graph.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}

    # --- construction ------------------------------------------------------
    def add(self, node: Node) -> Node:
        """Add/replace a node. Raises on an unknown kind so a typo can't silently
        create a node that no detector recognizes."""
        if node.kind not in VALID_KINDS:
            raise ValueError(f"unknown node kind {node.kind!r}; expected one of {sorted(VALID_KINDS)}")
        self.nodes[node.id] = node
        return node

    def get(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def nodes_of_kind(self, kind: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.kind == kind]

    def one_of_kind(self, kind: str) -> Node | None:
        """The single node of ``kind`` (first by id for determinism), or None."""
        hits = sorted(self.nodes_of_kind(kind), key=lambda n: n.id)
        return hits[0] if hits else None

    # --- edges -------------------------------------------------------------
    def edges(self) -> list[tuple[str, str]]:
        """All (downstream, upstream) edges declared by every node's ``sources:``.

        Edges to an upstream id not present in the graph are skipped (None-safe).
        Sorted for deterministic output.
        """
        out: list[tuple[str, str]] = []
        for n in self.nodes.values():
            for up in n.sources:
                if up in self.nodes:
                    out.append((n.id, up))
        return sorted(out)

    def _recorded_matches_current(self, node: Node, up_id: str) -> tuple[bool, str]:
        """Does ``node``'s recorded source token for ``up_id`` still match upstream's
        CURRENT state? Returns ``(matches, evidence)``. Handles hash-form, legacy
        version-string form, and an unrecognized token (treated as a hash compare).
        """
        recorded = (node.sources.get(up_id) or "").strip()
        up = self.nodes[up_id]
        mv = _LEGACY_VER_RE.match(recorded)
        if mv:  # legacy `sources: D-19 v1.3` form
            current = (up.version or "").lstrip("vV")
            return current == mv.group(1), f"recorded v{mv.group(1)} vs current v{current or '?'}"
        # hash-form (or any non-version token): compare against upstream's current hash
        norm_recorded = recorded[len("sha256:"):] if recorded.lower().startswith("sha256:") else recorded
        cur = up.hash
        return norm_recorded.lower() == cur.lower(), f"recorded hash {norm_recorded[:8] or '?'} vs current {cur[:8]}"

    def stale_edges(self) -> list[dict]:
        """Edges whose downstream node's recorded source token no longer matches the
        upstream node's current hash/version — i.e. DIRECT staleness. Each entry is
        ``{node, source, evidence}``. Sorted for determinism.
        """
        out: list[dict] = []
        for n in self.nodes.values():
            for up_id in sorted(n.sources):
                if up_id not in self.nodes:
                    continue
                ok, ev = self._recorded_matches_current(n, up_id)
                if not ok:
                    out.append({"node": n.id, "source": up_id, "evidence": ev})
        return sorted(out, key=lambda e: (e["node"], e["source"]))

    def dirty_set(self) -> dict[str, list[str]]:
        """Nodes that are STALE: directly (recorded token mismatches upstream) OR
        transitively (an upstream is itself dirty). Returns ``{node_id: [reasons]}``.

        Propagated by a worklist BFS over the sources-edges. Cycle-safe: a node only
        enters ``dirty`` once and the worklist drains, so a sources-cycle (A→B→A)
        cannot loop forever — it simply marks every node in the cycle dirty if any
        member is dirty. Deterministic: reasons are appended in sorted node order.
        """
        dirty: dict[str, list[str]] = {}
        # build downstream adjacency: upstream_id -> [downstream nodes that cite it]
        downstream: dict[str, list[str]] = {}
        for n in self.nodes.values():
            for up_id in n.sources:
                if up_id in self.nodes:
                    downstream.setdefault(up_id, []).append(n.id)

        # seed: direct staleness
        work: deque[str] = deque()
        for e in self.stale_edges():
            reasons = dirty.setdefault(e["node"], [])
            reasons.append(f"direct: source '{e['source']}' changed ({e['evidence']})")
            if e["node"] not in work:
                work.append(e["node"])

        # propagate downstream: anyone citing a dirty node becomes dirty too
        while work:
            up = work.popleft()
            for down in sorted(downstream.get(up, [])):
                if down not in dirty:
                    dirty[down] = [f"transitive: upstream '{up}' is dirty"]
                    work.append(down)
                elif not any(r.startswith("direct:") for r in dirty[down]):
                    # already transitively-dirty; record additional dirty upstream once
                    msg = f"transitive: upstream '{up}' is dirty"
                    if msg not in dirty[down]:
                        dirty[down].append(msg)
        return {k: dirty[k] for k in sorted(dirty)}

    def is_dirty(self, node_id: str) -> bool:
        return node_id in self.dirty_set()

    # --- matrix-as-view ----------------------------------------------------
    def matrix_view(self) -> dict:
        """Derive the REQ→design→code→test matrix as a VIEW computed FROM the graph.

        The authoritative REQ set comes from the upstream D-02 node (not the matrix's
        own rows), and each REQ's trace cells come from the matrix node's table. This
        is "matrix as a derived view": a matrix can't silently omit a REQ, because the
        REQ universe is D-02's, surfaced via ``missing_edges``.

        Returns ``{reqs: [...], rows: {req: {design_ref, code_ref, test_ref}}, ...}``.
        Reuses ``req_num_map`` / ``parse_matrix`` — no duplicated parsing.
        """
        d02 = self._d02_node()
        matrix = self.one_of_kind("matrix")
        req_ids = sorted(req_num_map(d02.text)[0].values(), key=_req_sort_key) if d02 else []
        rows: dict[str, dict[str, str]] = {}
        if matrix is not None:
            header, data = parse_matrix(matrix.text)
            ri = header.get("req_id", 0)
            for cells in data:
                if ri >= len(cells):
                    continue
                rid = cells[ri].strip()
                rows[rid] = {
                    col: (cells[header[col]].strip() if header.get(col, -1) >= 0 and header[col] < len(cells) else "")
                    for col in ("design_ref", "code_ref", "test_ref")
                }
        return {
            "source_doc": d02.id if d02 else None,
            "matrix_node": matrix.id if matrix else None,
            "reqs": req_ids,
            "rows": rows,
            "missing_edges": self.missing_edges(),
        }

    def missing_edges(self) -> list[str]:
        """REQ ids defined in the upstream D-02 node but with NO row (edge) in the
        matrix node — the "39/39 green but 040/041/042 never added" failure. Reuses
        ``missing_from_matrix``. Empty list when D-02 or matrix node is absent (a
        missing input is a different problem, not a false missing-edge)."""
        d02 = self._d02_node()
        matrix = self.one_of_kind("matrix")
        if d02 is None or matrix is None:
            return []
        return missing_from_matrix(d02.text, matrix.text)

    # --- ground-truth drift (machine-floor only; verdict ladder = TA.2) ----
    def ground_truth_drift(self, *, extra_token_fields=()) -> list[dict]:
        """For every design node with a ``reconcile_to`` code node, expose the
        model-drift signal via the shared ``model_drift`` primitive. Returns a list
        of ``{design_node, ground_truth_node, design_only, code_only, drift}``.

        The load-bearing signal is the generic model-NAME drift (D-19 physical
        names vs code ``_name=``), computed with no feature-specific input.
        ``extra_token_fields`` is an OPT-IN list of field-level tokens a caller
        (e.g. the TF.3 metrics harness) may track; the kernel default is empty so
        no feature-derived literal lives in kernel source. Only fields the DESIGN
        ACTUALLY declares are passed to ``model_drift`` (an unrelated feature can't
        have drift manufactured against it). This is the machine FLOOR — whether the
        drift is *meaningful* (rename vs real divergence) is TA.2's semantic ceiling,
        deliberately not decided here.
        """
        out: list[dict] = []
        for design in sorted(self.nodes.values(), key=lambda n: n.id):
            if not design.reconcile_to:
                continue
            gt = self.nodes.get(design.reconcile_to)
            if gt is None or gt.kind != "code":
                continue
            extra = {
                t for t in extra_token_fields
                if re.search(r"(?<![\w.])" + re.escape(t) + r"(?![\w.])", design.text)
            }
            drift = model_drift(design.text, gt.text, extra_tokens=extra)
            out.append({
                "design_node": design.id,
                "ground_truth_node": gt.id,
                "design_only": drift["design_only"],
                "code_only": drift["code_only"],
                "drift": drift["drift"],
            })
        return out

    # --- internals ---------------------------------------------------------
    def _d02_node(self) -> Node | None:
        """The D-02 (requirements) doc node — the authoritative REQ universe."""
        hits = sorted(
            (n for n in self.nodes.values() if n.kind == "doc" and n.id.upper().startswith("D-02")),
            key=lambda n: n.id,
        )
        return hits[0] if hits else None


def _req_sort_key(rid: str):
    m = re.search(r"\d+$", rid)
    return (int(m.group()) if m else 0, rid)


# ===========================================================================
# REPORT — the JSON a consumer (e.g. hbc-traceability build-graph) emits.
# ===========================================================================


def graph_report(g: BuildGraph) -> dict:
    """Single graph snapshot a consumer serializes. Pure derivation from current
    node state (living graph): dirty-set, matrix view, missing edges, ground-truth
    drift, plus the edge list and node inventory. No hardcoded expectations.
    """
    view = g.matrix_view()
    return {
        "nodes": {n.id: {"kind": n.kind, "version": n.version, "hash": n.hash[:12],
                         "sources": n.sources, "reconcile_to": n.reconcile_to}
                  for n in sorted(g.nodes.values(), key=lambda x: x.id)},
        "edges": g.edges(),
        "dirty_set": g.dirty_set(),
        "stale_edges": g.stale_edges(),
        "matrix_view": view,
        "missing_edges": view["missing_edges"],
        "ground_truth_drift": g.ground_truth_drift(),
    }


# ===========================================================================
# CORPUS LOADER — build a graph from an on-disk feature directory.
#
# Tolerant of BOTH layouts the corpora use:
#   * the TD.0 fixture: artifacts/planning-artifacts/D-02*, .../implementation-
#     artifacts/task-breakdown.md, artifacts/gates/*gate*.md, code/ as a sibling.
#   * the flat clean-corpus feature: planning/D-02*, implementation/task-breakdown.md,
#     traceability/matrix.md, gates/*gate*.md, code/.
# Edges are parsed from what the artifacts DECLARE (sources: frontmatter, gate
# evidence prose, frontmatter version), not annotated by hand.
# ===========================================================================


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def _frontmatter_version(text: str) -> str | None:
    m = re.search(r"^version:\s*[\"']?(\d+\.\d+(?:\.\d+)?)", text or "", re.MULTILINE)
    return m.group(1) if m else None


_SRC_VER_RE = re.compile(r"(D-\d{2})\s+v?(\d+\.\d+(?:\.\d+)?)")


def _parse_taskbreakdown_sources(text: str) -> dict[str, str]:
    """`sources:` frontmatter entries like 'D-02 v1.8 (39 REQ)' → {'D-02': '1.8'}."""
    out: dict[str, str] = {}
    for m in _SRC_VER_RE.finditer(text or ""):
        out.setdefault(m.group(1), m.group(2))
    return out


def _parse_gate_recorded_sources(text: str) -> dict[str, str]:
    """Doc versions a gate RECORDS evaluating against, scraped from its evidence
    prose ('consistent with D-02 v1.8', 'D-19 ... (v1.3)'). First win per doc.

    NOTE (honest limitation, carried from the spike): gates have no machine
    `sources:` block today, so this is prose-regex. TA-followups should make gates
    emit a real `sources: {node: hash}` block so staleness rests on hashes.
    """
    out: dict[str, str] = {}
    for m in re.finditer(r"(D-\d{2})\b[^\n]{0,40}?\bv(\d+\.\d+(?:\.\d+)?)", text or ""):
        out.setdefault(m.group(1), m.group(2))
    return out


def load_corpus(root: Path) -> BuildGraph:
    """Build a graph from a single feature directory (either supported layout).

    Missing files are skipped — the graph is built from whatever is present, so a
    partially-authored feature still yields a usable (smaller) graph.
    """
    root = Path(root)
    g = BuildGraph()

    def find(*globs: str) -> Path | None:
        for gl in globs:
            hits = sorted(root.rglob(gl))
            if hits:
                return hits[0]
        return None

    d02_p = find("D-02*.md")
    d19_p = find("D-19*er*.md", "D-19*.md")
    matrix_p = find("matrix.md")
    tb_p = find("task-breakdown.md")
    gate_ps = sorted(root.rglob("*gate*.md")) + sorted(root.rglob("*gate*results*.json"))
    code_dir = next((p for p in sorted(root.rglob("code")) if p.is_dir()), None)

    # ground-truth code node: persistent-model code only (models/ or top-level), not
    # transient wizards — keeps the code_only drift signal meaningful (model_drift).
    code_text = ""
    if code_dir:
        for py in sorted(code_dir.rglob("*.py")):
            parts = py.relative_to(code_dir).parts
            if "models" in parts or py.parent == code_dir:
                code_text += _read(py) + "\n"
    g.add(Node(id="code", kind="code", text=code_text))

    if d02_p:
        t = _read(d02_p)
        g.add(Node(id="D-02", kind="doc", text=t, version=_frontmatter_version(t)))
    # NOTE (loader edge model — F-3 nit): for D-19 and matrix the loader records the
    # CURRENT upstream hash, so these two nodes are "always-fresh by construction" and
    # will NOT appear in dirty_set via the loader. That is intentional: their real
    # failure modes are caught by orthogonal queries — D-19↔code by ground_truth_drift,
    # matrix coverage by missing_edges — not by version-staleness. Only gate and
    # task-breakdown carry real recorded version strings, so only they can go dirty via
    # the loader. dirty_set itself is fully general (see tests); a TA-followup should
    # capture a real recorded hash once artifacts emit machine `sources:` blocks.
    if d19_p:
        t = _read(d19_p)
        g.add(Node(id="D-19", kind="doc", text=t, version=_frontmatter_version(t),
                   reconcile_to="code" if code_dir else None,
                   sources={"code": g.nodes["code"].hash} if code_dir else {}))

    if matrix_p:
        t = _read(matrix_p)
        src = {"D-02": g.nodes["D-02"].hash} if "D-02" in g.nodes else {}
        g.add(Node(id="matrix", kind="matrix", text=t, sources=src))

    if tb_p:
        t = _read(tb_p)
        recorded = _parse_taskbreakdown_sources(t)
        sources = {doc: f"v{ver}" for doc, ver in recorded.items() if doc in g.nodes}
        g.add(Node(id="task-breakdown", kind="task-breakdown", text=t, sources=sources))

    if gate_ps:
        gate_text = ""
        recorded: dict[str, str] = {}
        for gp in gate_ps:
            gt = _read(gp)
            gate_text += gt + "\n"
            for doc, ver in _parse_gate_recorded_sources(gt).items():
                recorded.setdefault(doc, ver)
        sources = {doc: f"v{ver}" for doc, ver in recorded.items() if doc in g.nodes}
        g.add(Node(id="gate", kind="gate", text=gate_text, sources=sources))

    return g


# Dir names that are artifact-CATEGORIES inside one feature, not separate features.
_CATEGORY_DIRS = {"artifacts", "code", "planning", "planning-artifacts",
                  "traceability", "implementation", "implementation-artifacts", "gates"}


def feature_dirs(root: Path) -> list[Path]:
    """Feature subdirs under ``root``. A corpus holds ONE feature (the fixture: root
    has category subdirs + a sibling code/) or MANY (the clean corpus: one named
    subdir per feature). A feature subdir = an immediate child that is NOT a category
    dir AND has a D-02 beneath it; if none qualify, ``root`` is the single feature.
    """
    root = Path(root)
    children = [p for p in sorted(root.iterdir()) if p.is_dir()]
    feat = [c for c in children if c.name.lower() not in _CATEGORY_DIRS and any(c.rglob("D-02*.md"))]
    return feat if feat else [root]
