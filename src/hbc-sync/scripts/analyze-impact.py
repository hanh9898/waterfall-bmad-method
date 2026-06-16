#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""Analyze cascade impact for hbc-sync.

Given the dependency graph, a baseline manifest, and (optionally) an explicit
list of changed documents, compute:
  - changed set    — docs whose body hash differs from the manifest (BR-06),
                     plus any docs passed via --changed (override)
  - affected set   — all downstream descendants of the changed set (BR-02)
  - order          — topological processing order over the affected subgraph
  - gaps           — selection gaps when --selected is supplied (BR-14)

Emits structured JSON for the orchestrator. Deterministic — LLM applies impact
level + classification on top of this (BR-05, BR-07).

Exit codes: 0 ok · 1 graph/file error · 2 pyyaml unavailable.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_common import body_hash, close_gaps, descendants, selection_gaps, topological_order  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _load_yaml(path: str) -> dict:
    try:
        import yaml  # noqa: E402
    except ImportError:
        print(json.dumps({"error": "PyYAML not installed.",
                          "suggestion": "pip install pyyaml"}, ensure_ascii=False))
        sys.exit(2)
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def build_graph(doc: dict) -> dict:
    nodes = doc.get("nodes", {}) or {}
    return {
        nid: {
            "skill": (spec or {}).get("skill", ""),
            "output_glob": (spec or {}).get("output_glob", ""),
            "depends_on": list((spec or {}).get("depends_on", []) or []),
            "terminal": bool((spec or {}).get("terminal", False)),
            "strategy": (spec or {}).get("strategy"),
        }
        for nid, spec in nodes.items()
    }


def resolve_doc_path(project_root: Path, output_glob: str) -> Path | None:
    """Resolve a node's output_glob to an existing file under project_root.

    Tokens like {planning_artifacts} are resolved naively to known defaults;
    the orchestrator may pass already-resolved globs. Returns first match.
    """
    if not output_glob:
        return None
    glob = (output_glob
            .replace("{planning_artifacts}", "_bmad-output/planning-artifacts")
            .replace("{implementation_artifacts}", "_bmad-output/implementation-artifacts")
            .replace("{project-root}/", "")
            .replace("{workflow.source_code_path}", ""))
    if not glob:
        return None
    matches = sorted(project_root.glob(glob))
    return matches[0] if matches else None


def detect_changed(graph: dict, manifest: dict, project_root: Path,
                   forced: set[str]) -> dict:
    """Return {changed: [...], detail: {node: reason}} (BR-06).

    A node is changed if explicitly forced (--changed), or its current body hash
    differs from the manifest baseline. Nodes with no resolvable file are skipped
    unless forced.
    """
    baseline = manifest.get("doc_hashes", {})
    changed: list[str] = []
    detail: dict[str, str] = {}
    for node, spec in graph.items():
        if node in forced:
            changed.append(node)
            detail[node] = "forced (--changed)"
            continue
        path = resolve_doc_path(project_root, spec.get("output_glob", ""))
        if path is None:
            continue
        current = body_hash(path.read_text(encoding="utf-8"))
        prior = baseline.get(node)
        if prior is None:
            changed.append(node)
            detail[node] = "no_baseline (treated as changed)"
        elif current != prior:
            changed.append(node)
            detail[node] = "hash_differs"
    return {"changed": sorted(changed), "detail": detail}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze cascade impact for hbc-sync.")
    parser.add_argument("--graph", required=True, help="dependency-graph.yaml")
    parser.add_argument("--manifest", help=".sync-manifest.json (baseline hashes)")
    parser.add_argument("--project-root", required=True, help="Project root for doc resolution")
    parser.add_argument("--changed", nargs="*", default=[],
                        help="Explicit changed node ids (override hash detection)")
    parser.add_argument("--selected", nargs="*", default=None,
                        help="User-selected node ids (for gap analysis); omit = all affected")
    parser.add_argument("--auto-close-gaps", action="store_true",
                        help="Auto-include missing ancestors (headless default per BR-14)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    graph_path = Path(args.graph)
    if not graph_path.exists():
        print(json.dumps({"error": f"Graph not found: {args.graph}"}, ensure_ascii=False))
        sys.exit(1)

    graph = build_graph(_load_yaml(str(graph_path)))
    project_root = Path(args.project_root)

    manifest = {}
    if args.manifest and Path(args.manifest).exists():
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    detection = detect_changed(graph, manifest, project_root, set(args.changed))
    changed_set = set(detection["changed"])
    affected = descendants(graph, changed_set)
    order = topological_order(graph, affected)

    result = {
        "changed": detection["changed"],
        "change_detail": detection["detail"],
        "affected": sorted(affected),
        "order": order,
        "is_noop": len(affected) == 0,  # P-5 idempotence signal
    }

    if args.selected is not None:
        selected = set(args.selected) & affected
        gaps = selection_gaps(graph, affected, selected)
        result["selection_gaps"] = gaps
        if args.auto_close_gaps:
            closed = close_gaps(graph, affected, selected)
            result["selected_resolved"] = topological_order(graph, closed)
            result["auto_included"] = sorted(closed - selected)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Impact analysis written to {args.output}", file=sys.stderr)
    else:
        print(text)
    sys.exit(0)


if __name__ == "__main__":
    main()
