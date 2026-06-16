#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Shared helpers for hbc-sync scripts (analyze-impact, sync-state).

Pure functions only — no I/O side effects beyond reading file content passed by
the caller. Kept dependency-free (stdlib) so it imports cleanly in every script.

Covers the deterministic core of:
  - body hashing for change detection (BR-06)
  - DAG descendant traversal + dedupe (BR-02, BR-03, P-2, P-6)
  - topological order restricted to a subgraph (BR-02, P-3)
  - selection gap detection (BR-14, P-7)
"""
from __future__ import annotations

import hashlib
import re

_FRONTMATTER_RE = re.compile(r"^\s*---\s*\n.*?\n---\s*\n", re.DOTALL)


def strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block so hash reflects body only.

    Frontmatter carries volatile metadata (updated timestamp, stepsCompleted)
    that changes without a semantic edit — excluding it makes the hash a stable
    signal of real content change (BR-06).
    """
    return _FRONTMATTER_RE.sub("", text, count=1)


def body_hash(text: str) -> str:
    """sha256 of the document body (frontmatter stripped, trailing ws normalised)."""
    body = strip_frontmatter(text).strip()
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def descendants(graph: dict, roots: set[str]) -> set[str]:
    """All nodes reachable downstream from ``roots`` via the child relation.

    ``graph`` maps node_id -> {"depends_on": [parents...]}. We invert to children
    and BFS. Roots themselves are NOT included (they are the changed docs, not
    their own downstream impact) unless reachable from another root.
    """
    children: dict[str, list[str]] = {n: [] for n in graph}
    for node, spec in graph.items():
        for parent in spec.get("depends_on", []):
            if parent in children:
                children[parent].append(node)

    seen: set[str] = set()
    frontier = [c for r in roots for c in children.get(r, [])]
    while frontier:
        n = frontier.pop()
        if n in seen:
            continue
        seen.add(n)
        frontier.extend(children.get(n, []))
    return seen


def topological_order(graph: dict, subset: set[str]) -> list[str]:
    """Kahn's algorithm restricted to ``subset``.

    In-degree counts only parents that are themselves in ``subset`` — so a node
    is emitted after all its in-subset parents (BR-02). Each node appears exactly
    once even with multiple parents (BR-03, P-6). Deterministic via sorted ids.
    """
    in_degree = {n: 0 for n in subset}
    children: dict[str, list[str]] = {n: [] for n in subset}
    for node in subset:
        for parent in graph.get(node, {}).get("depends_on", []):
            if parent in subset:
                in_degree[node] += 1
                children[parent].append(node)

    ready = sorted(n for n in subset if in_degree[n] == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in sorted(children[node]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                ready.append(child)
        ready.sort()
    return order


def selection_gaps(graph: dict, affected: set[str], selected: set[str]) -> list[dict]:
    """Detect selection gaps (BR-14).

    A gap exists when a selected node has a parent that is in the affected set
    but NOT selected — updating the child without its changed parent risks
    inconsistency. Returns one entry per (selected_node, missing_ancestor).
    """
    gaps: list[dict] = []
    for node in selected:
        for parent in graph.get(node, {}).get("depends_on", []):
            if parent in affected and parent not in selected:
                gaps.append({"selected_node": node, "missing_ancestor": parent})
    return gaps


def close_gaps(graph: dict, affected: set[str], selected: set[str]) -> set[str]:
    """Auto-include missing affected ancestors so the selection is gap-free.

    Repeatedly adds any affected parent of a selected node until a fixed point —
    guarantees the post-condition checked by P-7 (no remaining gap).
    """
    closed = set(selected)
    changed = True
    while changed:
        changed = False
        for node in list(closed):
            for parent in graph.get(node, {}).get("depends_on", []):
                if parent in affected and parent not in closed:
                    closed.add(parent)
                    changed = True
    return closed
