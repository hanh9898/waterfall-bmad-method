#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Load and validate the hbc-sync dependency graph (DAG).

Parses dependency-graph.yaml, builds the node/edge structure, verifies the
graph is a Directed Acyclic Graph (BR-11), and emits a topological order.
Returns structured JSON for the orchestrator.

Exit codes:
  0 — graph valid (DAG)
  1 — graph invalid (cycle detected) or file not found
  2 — pyyaml unavailable (cannot parse)
"""

import argparse
import json
import sys
from pathlib import Path

# Windows stdout defaults to cp1252; force UTF-8 so ensure_ascii=False output is
# identical across platforms (mirrors hbc-traceability scripts).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _load_yaml(path: str) -> dict:
    """Parse YAML, returning the document as a dict. Requires PyYAML."""
    try:
        import yaml  # noqa: E402
    except ImportError:
        print(json.dumps({
            "error": "PyYAML not installed — cannot parse dependency graph.",
            "suggestion": "pip install pyyaml (or add to the module's dev deps).",
        }, ensure_ascii=False))
        sys.exit(2)
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def build_graph(doc: dict) -> dict:
    """Normalise the parsed YAML into {node_id: {skill, depends_on, ...}}."""
    nodes = doc.get("nodes", {}) or {}
    graph: dict[str, dict] = {}
    for node_id, spec in nodes.items():
        spec = spec or {}
        graph[node_id] = {
            "skill": spec.get("skill", ""),
            "output_glob": spec.get("output_glob", ""),
            "depends_on": list(spec.get("depends_on", []) or []),
            "mode": spec.get("mode", "update"),
            "strategy": spec.get("strategy"),
            "terminal": bool(spec.get("terminal", False)),
        }
    return graph


def find_cycle(graph: dict) -> list[str] | None:
    """Return a node sequence forming a cycle, or None if the graph is acyclic.

    DFS with a recursion stack (WHITE/GRAY/BLACK colouring). The edge direction
    used here is child -> parent (depends_on); a back-edge to a GRAY node proves
    a cycle. We report the cycle path for actionable diagnostics (BR-11).
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack: list[str] = []

    def visit(n: str) -> list[str] | None:
        color[n] = GRAY
        stack.append(n)
        for parent in graph[n]["depends_on"]:
            if parent not in graph:
                continue  # dangling edge handled separately by validate()
            if color[parent] == GRAY:
                idx = stack.index(parent)
                return stack[idx:] + [parent]
            if color[parent] == WHITE:
                found = visit(parent)
                if found:
                    return found
        stack.pop()
        color[n] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def topological_order(graph: dict) -> list[str]:
    """Kahn's algorithm over the depends_on edges.

    A node is emitted only after ALL its parents (depends_on) are emitted
    (BR-02). Assumes the graph is already verified acyclic.
    """
    # in_degree = number of parents (depends_on entries that exist in graph)
    in_degree = {n: 0 for n in graph}
    children: dict[str, list[str]] = {n: [] for n in graph}
    for node, spec in graph.items():
        for parent in spec["depends_on"]:
            if parent in graph:
                in_degree[node] += 1
                children[parent].append(node)

    # Deterministic ordering: process ready nodes in sorted id order.
    ready = sorted(n for n, d in in_degree.items() if d == 0)
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


def validate(graph: dict) -> dict:
    """Structural validation: dangling edges + DAG check."""
    issues: list[str] = []
    for node, spec in graph.items():
        for parent in spec["depends_on"]:
            if parent not in graph:
                issues.append(f"Node '{node}' depends on undefined node '{parent}'")
    cycle = find_cycle(graph)
    if cycle:
        issues.append(f"Cycle detected: {' -> '.join(cycle)}")
    return {
        "valid": len(issues) == 0,
        "is_dag": cycle is None,
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load + validate hbc-sync dependency graph.")
    parser.add_argument("--graph", required=True, help="Path to dependency-graph.yaml")
    parser.add_argument("--project-root", help="Project root (for token resolution; reserved)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    graph_path = Path(args.graph)
    if not graph_path.exists():
        print(json.dumps({"error": f"Graph file not found: {args.graph}"}, ensure_ascii=False))
        sys.exit(1)

    doc = _load_yaml(str(graph_path))
    graph = build_graph(doc)
    validation = validate(graph)

    result = {
        "version": doc.get("version", 1),
        "nodes": graph,
        "validation": validation,
        "topological_order": topological_order(graph) if validation["is_dag"] else [],
    }

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Graph analysis written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if validation["valid"] else 1)


if __name__ == "__main__":
    main()
