#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Cascade state + baseline manifest manager for hbc-sync.

Two persistent artifacts under {output_folder}/sync/:
  - .sync-state.json    — resume point for an in-progress cascade (BR-10, NFR-002)
  - .sync-manifest.json — baseline body hashes per document (BR-06)

Actions:
  save           — write/merge cascade state
  load           — read cascade state (or {"sync_in_progress": false})
  clear          — delete cascade state (cascade complete)
  hash           — compute body hash of a file (change-detection helper)
  update-manifest — set a node's baseline hash to its current body hash

Exit codes: 0 ok · 1 io/arg error.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_common import body_hash  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def action_save(state_path: Path, payload: dict) -> dict:
    """Merge ``payload`` into existing state and persist. Round-trip safe (P-4)."""
    state = _read_json(state_path)
    state.update(payload)
    state["sync_in_progress"] = True
    _write_json(state_path, state)
    return {"action": "save", "state_path": str(state_path), "ok": True}


def action_load(state_path: Path) -> dict:
    state = _read_json(state_path)
    if not state:
        return {"sync_in_progress": False}
    return state


def action_clear(state_path: Path) -> dict:
    existed = state_path.exists()
    if existed:
        state_path.unlink()
    return {"action": "clear", "removed": existed}


def action_hash(file_path: Path) -> dict:
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    return {"file": str(file_path), "hash": body_hash(file_path.read_text(encoding="utf-8"))}


def action_update_manifest(manifest_path: Path, node: str, file_path: Path) -> dict:
    """Advance the baseline hash for ``node`` (BR-06 — only after node success)."""
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}
    manifest = _read_json(manifest_path)
    manifest.setdefault("version", 1)
    manifest.setdefault("doc_hashes", {})
    manifest["doc_hashes"][node] = body_hash(file_path.read_text(encoding="utf-8"))
    _write_json(manifest_path, manifest)
    return {"action": "update-manifest", "node": node, "ok": True}


def main() -> None:
    parser = argparse.ArgumentParser(description="hbc-sync state + manifest manager.")
    parser.add_argument("--action", required=True,
                        choices=["save", "load", "clear", "hash", "update-manifest"])
    parser.add_argument("--state-path", help="Path to .sync-state.json")
    parser.add_argument("--manifest-path", help="Path to .sync-manifest.json")
    parser.add_argument("--node", help="Node id (for update-manifest)")
    parser.add_argument("--file", help="Document path (for hash / update-manifest)")
    parser.add_argument("--payload", help="JSON string to merge into state (for save)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    if args.action in ("save", "load", "clear") and not args.state_path:
        print(json.dumps({"error": "--state-path required"}, ensure_ascii=False)); sys.exit(1)

    if args.action == "save":
        payload = json.loads(args.payload) if args.payload else {}
        result = action_save(Path(args.state_path), payload)
    elif args.action == "load":
        result = action_load(Path(args.state_path))
    elif args.action == "clear":
        result = action_clear(Path(args.state_path))
    elif args.action == "hash":
        if not args.file:
            print(json.dumps({"error": "--file required"}, ensure_ascii=False)); sys.exit(1)
        result = action_hash(Path(args.file))
    else:  # update-manifest
        if not (args.manifest_path and args.node and args.file):
            print(json.dumps({"error": "--manifest-path, --node, --file required"},
                             ensure_ascii=False)); sys.exit(1)
        result = action_update_manifest(Path(args.manifest_path), args.node, Path(args.file))

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(text)
    sys.exit(1 if isinstance(result, dict) and result.get("error") else 0)


if __name__ == "__main__":
    main()
