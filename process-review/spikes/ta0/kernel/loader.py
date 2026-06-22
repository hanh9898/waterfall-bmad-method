#!/usr/bin/env python
"""Load a corpus directory into a BuildGraph (TA.0 spike).

The loader builds the graph HONESTLY from what each artifact actually declares:

  - A doc node's version comes from its frontmatter `version:`.
  - A node's `sources:` edges are parsed from the artifact itself:
      * task-breakdown: its `sources:` frontmatter list ("D-02 v1.8 / D-19 v1.3")
        — the recorded source token is the version string it names.
      * gate node: the version it RECORDS having evaluated against, parsed from
        its own evidence text ("D-02 v1.8", "D-19 (v1.3)", "matrix 39/39"). This
        is the gate's recorded source-of-record — NOT a hardcoded expected value.
      * matrix / D-19: their upstream is fixed by HBC topology (matrix derives
        from D-02; D-19 reconciles to code), recorded as the CURRENT upstream
        hash so a clean corpus is clean unless the upstream actually moved.

The recorded token form (version-string vs hash) is whatever the artifact carries;
the kernel reconciles either against the upstream node's current state.
"""
from __future__ import annotations

import re
from pathlib import Path

from buildgraph import BuildGraph, Node


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def _frontmatter_version(text: str) -> str | None:
    m = re.search(r"^version:\s*[\"']?(\d+\.\d+(?:\.\d+)?)", text, re.MULTILINE)
    return m.group(1) if m else None


def _parse_taskbreakdown_sources(text: str) -> dict[str, str]:
    """Parse `sources:` frontmatter entries like 'D-02 v1.8 (39 REQ)' /
    'D-19 v1.3 (...)' into {doc-id-prefix: recorded-version}. The recorded token
    is the version string the task-breakdown itself names."""
    out: dict[str, str] = {}
    for m in re.finditer(r"(D-\d{2})\s+v?(\d+\.\d+(?:\.\d+)?)", text):
        out[m.group(1)] = m.group(2)
    return out


def _parse_gate_recorded_sources(text: str) -> dict[str, str]:
    """Parse the doc versions a gate RECORDS having evaluated against, from its
    own evidence prose. Patterns the real gates use:
        'consistent with D-02 v1.8', 'D-19 ... (v1.3)', 'D-19 v1.3 reviewed'.
    Returns {doc-id: recorded-version}. If a doc is named several times we keep
    the first (the gate evaluated one coherent baseline)."""
    out: dict[str, str] = {}
    # D-XX immediately followed (within a few words) by a vN.N token
    for m in re.finditer(r"(D-\d{2})\b[^\n]{0,40}?\bv(\d+\.\d+(?:\.\d+)?)", text):
        out.setdefault(m.group(1), m.group(2))
    return out


def load_corpus(root: Path) -> BuildGraph:
    """Build a graph from a corpus laid out like the TD.0 fixture / clean corpus.

    Expected (best-effort) paths under `root`:
      planning/D-02*.md, planning/D-19*.md,
      traceability/matrix.md, implementation/task-breakdown.md,
      gates/*gate*.md (+ *.json), code/  (the ground-truth code tree)
    Missing files are skipped — the graph is built from whatever is present.
    """
    g = BuildGraph()

    # --- locate files (tolerant of the fixture's nested dirs) -------------
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
    code_dir = next((p for p in root.rglob("code") if p.is_dir()), None)

    # --- ground-truth code node ------------------------------------------
    code_text = ""
    if code_dir:
        # only persistent-model code (models/), not transient wizards — keeps the
        # code_only drift signal meaningful (per model_drift docstring).
        for py in sorted(code_dir.rglob("*.py")):
            if "models" in py.relative_to(code_dir).parts or py.parent == code_dir:
                code_text += _read(py) + "\n"
    g.add(Node(id="code", kind="code", text=code_text))

    # --- doc nodes -------------------------------------------------------
    if d02_p:
        t = _read(d02_p)
        g.add(Node(id="D-02", kind="doc", text=t, version=_frontmatter_version(t)))
    if d19_p:
        t = _read(d19_p)
        # D-19 reconciles against the ground-truth code node
        g.add(Node(id="D-19", kind="doc", text=t, version=_frontmatter_version(t),
                   reconcile_to="code" if code_dir else None,
                   sources={"code": g.nodes["code"].hash} if code_dir else {}))

    # --- matrix node (derives from D-02) ---------------------------------
    if matrix_p:
        t = _read(matrix_p)
        src = {}
        if "D-02" in g.nodes:
            # a clean matrix records the CURRENT D-02 hash; the fixture matrix
            # simply has fewer rows (caught by the coverage detector, not staleness)
            src = {"D-02": g.nodes["D-02"].hash}
        g.add(Node(id="matrix", kind="matrix", text=t, sources=src))

    # --- task-breakdown node (records its own stale source versions) -----
    if tb_p:
        t = _read(tb_p)
        recorded = _parse_taskbreakdown_sources(t)  # e.g. {"D-02":"1.8","D-19":"1.3"}
        sources = {doc: f"v{ver}" for doc, ver in recorded.items() if doc in g.nodes}
        g.add(Node(id="task-breakdown", kind="task-breakdown", text=t, sources=sources))

    # --- gate node (records the doc versions it evaluated against) --------
    if gate_ps:
        # merge all gate reports into one gate node; record the source versions
        # they evaluated against (parsed from their own evidence text)
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
