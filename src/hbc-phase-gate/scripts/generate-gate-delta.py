#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Generate a gate log delta entry from prior and current evaluation results.

Compares item-by-item statuses and produces a ready-to-append markdown block
with a delta table and summary line.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_results(path: str) -> dict[str, str]:
    """Load evaluation JSON and return {item_id: status} map."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    results = data.get("results", [])
    return {r["item_id"]: r["status"] for r in results}


def compute_delta(
    prior: dict[str, str], current: dict[str, str]
) -> list[dict[str, str]]:
    all_ids = list(dict.fromkeys(list(prior.keys()) + list(current.keys())))
    rows = []
    for item_id in all_ids:
        prev = prior.get(item_id, "—")
        curr = current.get(item_id, "—")
        if prev == "—":
            change = "NEW"
        elif prev != curr:
            change = f"{prev}→{curr}"
        else:
            change = "—"
        rows.append({
            "item_id": item_id,
            "previous": prev,
            "current": curr,
            "change": change,
        })
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, int]:
    fixed = sum(1 for r in rows if "FAIL→PASS" in r["change"])
    regressed = sum(1 for r in rows if "PASS→FAIL" in r["change"])
    new = sum(1 for r in rows if r["change"] == "NEW")
    unchanged = sum(1 for r in rows if r["change"] == "—")
    return {"fixed": fixed, "regressed": regressed, "new": new, "unchanged": unchanged}


def render_markdown(
    rows: list[dict[str, str]], summary: dict[str, int], overall_status: str
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## {now} — {overall_status}",
        "",
        "| Item ID | Previous | Current | Change |",
        "|---------|----------|---------|--------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['item_id']} | {r['previous']} | {r['current']} | {r['change']} |"
        )
    lines.append("")
    lines.append(
        f"{summary['fixed']} fixed, {summary['regressed']} regressed, "
        f"{summary['new']} new, {summary['unchanged']} unchanged."
    )
    lines.append("")
    return "\n".join(lines)


def render_json(
    rows: list[dict[str, str]], summary: dict[str, int]
) -> dict:
    return {
        "fixed": [r["item_id"] for r in rows if "FAIL→PASS" in r["change"]],
        "regressed": [r["item_id"] for r in rows if "PASS→FAIL" in r["change"]],
        "new": [r["item_id"] for r in rows if r["change"] == "NEW"],
        "unchanged": [r["item_id"] for r in rows if r["change"] == "—"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate gate log delta entry from prior and current results."
    )
    parser.add_argument("current", help="Path to current evaluation JSON")
    parser.add_argument("--prior", help="Path to prior evaluation JSON (omit for first run)")
    parser.add_argument("--status", required=True, help="Overall gate status (PASSED/FAILED/WARNING)")
    parser.add_argument("--format", choices=["markdown", "json", "both"], default="markdown")
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    args = parser.parse_args()

    current = load_results(args.current)

    if args.prior and Path(args.prior).exists():
        prior = load_results(args.prior)
        rows = compute_delta(prior, current)
    else:
        rows = []

    summary = summarize(rows) if rows else {"fixed": 0, "regressed": 0, "new": 0, "unchanged": 0}

    if args.format == "json" or args.format == "both":
        delta_json = render_json(rows, summary) if rows else None
        output_data = {
            "is_first_run": not rows,
            "delta": delta_json,
            "summary": summary,
        }
        if args.format == "json":
            result = json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            md = render_markdown(rows, summary, args.status) if rows else f"First evaluation — no prior results to compare.\n"
            result = md + "\n---\n" + json.dumps(output_data, indent=2, ensure_ascii=False)
    else:
        if rows:
            result = render_markdown(rows, summary, args.status)
        else:
            result = "First evaluation — no prior results to compare.\n"

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(result, encoding="utf-8")
    else:
        print(result)

    sys.exit(1 if summary.get("regressed", 0) > 0 else 0)


if __name__ == "__main__":
    main()
