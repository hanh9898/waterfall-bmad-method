#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 3 helper: compare current stage_2_actors/flows frontmatter against
the prior session's discovery flush in .decision-log.md.

Returns scope classification JSON:
  scope: "polish" | "semantic"
  actors_changed: bool
  flows_changed: bool

Exit codes:
  0  diff produced
  2  argument or filesystem error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _extract_yaml_list(fm: str, key: str) -> list[str]:
    pattern = re.compile(rf"^{re.escape(key)}:\s*\[(.*?)\]\s*$", re.MULTILINE)
    m = pattern.search(fm)
    if not m:
        return []
    return sorted(s.strip().strip("\"'") for s in m.group(1).split(",") if s.strip())


def _extract_frontmatter(text: str) -> str:
    fm_match = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    return fm_match.group(1) if fm_match else ""


def _extract_last_flush(log_text: str) -> tuple[list[str], list[str]]:
    """Extract actors and flows from the last Stage 2 flush block in the decision log."""
    flush_pattern = re.compile(
        r"###\s+Discovery snapshot.*?\n(.*?)(?=\n###|\n##|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    flushes = list(flush_pattern.finditer(log_text))
    if not flushes:
        return [], []

    block = flushes[-1].group(1)

    actors: list[str] = []
    flows: list[str] = []

    actors_match = re.search(r"\*\*Actors?:\*\*\s*(.+)", block)
    if actors_match:
        actors = sorted(a.strip().strip("\"'`") for a in actors_match.group(1).split(",") if a.strip())

    flow_inv_match = re.search(r"\*\*Flow inventory:\*\*", block)
    if flow_inv_match:
        after_inventory = block[flow_inv_match.end():]
        flow_matches = re.findall(r"^\s*[-*]\s+\*\*(.+?)\*\*", after_inventory, re.MULTILINE)
        if flow_matches:
            flows = sorted(f.strip() for f in flow_matches)
        else:
            inline = re.search(r"\*\*Flow inventory:\*\*\s*(.+)", block)
            if inline:
                flows = sorted(f.strip().strip("\"'`") for f in inline.group(1).split(",") if f.strip())

    return actors, flows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("primary", help="Path to the primary D-06 markdown file")
    parser.add_argument("decision_log", help="Path to .decision-log.md")
    parser.add_argument("-o", "--output", required=True, help="JSON output path")
    args = parser.parse_args()

    primary = Path(args.primary)
    log = Path(args.decision_log)

    if not primary.exists() or not log.exists():
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({
                "error": "file_missing",
                "primary_exists": primary.exists(),
                "decision_log_exists": log.exists(),
            }),
            encoding="utf-8",
        )
        return 2

    fm = _extract_frontmatter(primary.read_text(encoding="utf-8", errors="replace"))
    current_actors = _extract_yaml_list(fm, "stage_2_actors")
    current_flows = _extract_yaml_list(fm, "stage_2_flows")

    log_text = log.read_text(encoding="utf-8", errors="replace")
    prior_actors, prior_flows = _extract_last_flush(log_text)

    actors_changed = current_actors != prior_actors
    flows_changed = current_flows != prior_flows
    scope = "semantic" if actors_changed or flows_changed else "polish"

    result = {
        "scope": scope,
        "actors_changed": actors_changed,
        "flows_changed": flows_changed,
        "current_actors": current_actors,
        "current_flows": current_flows,
        "prior_actors": prior_actors,
        "prior_flows": prior_flows,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": args.output, "scope": scope}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
