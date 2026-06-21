#!/usr/bin/env python3
"""Content-hash integrity for the TD.0 regression fixture(s).

The fixture's whole value is being a *fixed* substrate. mtime survives no copy and
proves nothing once snapshotted; a content-hash manifest is the real tamper-evidence.
This writes/verifies `<fixture>/manifest.sha256` covering every file under the
fixture (except the manifest itself), so any byte-level edit — not just an aggregate
count change — is caught.

    python process-review/fixtures/fixture_integrity.py --write   # regenerate (deliberate)
    python process-review/fixtures/fixture_integrity.py --check   # verify (CI / tests)

stdlib-only. `--check` exits non-zero on any mismatch/added/removed file.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).resolve().parent / "resource-plan-billable"
MANIFEST = "manifest.sha256"
# Hash only the frozen error-state payload, not the meta files (FIXTURE.md prose,
# the manifest itself) — editing the docs must not churn the integrity manifest.
PAYLOAD_DIRS = ("artifacts", "code")


def _iter_files(root: Path):
    for sub in PAYLOAD_DIRS:
        for p in sorted((root / sub).rglob("*")):
            # skip transient compiled artifacts — not part of the frozen payload
            if "__pycache__" in p.parts or p.suffix == ".pyc":
                continue
            if p.is_file():
                yield p


def compute_manifest(root: Path) -> str:
    lines = []
    for p in _iter_files(root):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        rel = str(p.relative_to(root)).replace("\\", "/")
        lines.append(f"{digest}  {rel}")
    return "\n".join(lines) + "\n"


def write_manifest(root: Path) -> int:
    (root / MANIFEST).write_text(compute_manifest(root), encoding="utf-8")
    n = sum(1 for _ in _iter_files(root))
    print(f"wrote {root / MANIFEST} ({n} files)")
    return 0


def check_manifest(root: Path) -> int:
    mf = root / MANIFEST
    if not mf.is_file():
        print(f"error: manifest missing: {mf}", file=sys.stderr)
        return 1
    expected = {}
    for line in mf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        expected[rel] = digest
    actual = {}
    for p in _iter_files(root):
        rel = str(p.relative_to(root)).replace("\\", "/")
        actual[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    problems = []
    for rel, dig in expected.items():
        if rel not in actual:
            problems.append(f"removed: {rel}")
        elif actual[rel] != dig:
            problems.append(f"changed: {rel}")
    for rel in actual:
        if rel not in expected:
            problems.append(f"added:   {rel}")
    if problems:
        print("error: fixture integrity check FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"fixture integrity OK ({len(expected)} files)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="TD.0 fixture content-hash integrity")
    ap.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="(re)generate the manifest")
    g.add_argument("--check", action="store_true", help="verify against the manifest")
    args = ap.parse_args(argv)
    if not args.fixture.is_dir():
        print(f"error: fixture dir not found: {args.fixture}", file=sys.stderr)
        return 1
    return write_manifest(args.fixture) if args.write else check_manifest(args.fixture)


if __name__ == "__main__":
    raise SystemExit(main())
