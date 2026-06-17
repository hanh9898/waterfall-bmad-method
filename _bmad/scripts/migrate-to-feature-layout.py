#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Migrate a legacy (project-level) HBC output layout to the v2 per-feature layout.

v1 layout (everything project-global):
    _bmad-output/planning-artifacts/D-02-*.md, D-19-*, D-12-*, D-03-*, ...
    _bmad-output/implementation-artifacts/task-breakdown.md, ...
    _bmad-output/gates/phase-*-gate.md
    _bmad-output/traceability/matrix.md

v2 layout (per-feature + shared):
    _bmad-output/features/<feature>/{planning-artifacts,implementation-artifacts,gates,traceability}/
    _bmad-output/shared/{coding-standards(D-12),glossary(D-03),erd(D-19),api(D-21)}/

Default: a NON-destructive DRY-RUN (prints the plan). Pass --apply to move files.
Legacy artifacts go to feature `--feature` (default: "default"). Shared deliverables
(D-12, D-03, D-19, D-21) are routed to shared/. Optionally re-prefixes legacy
REQ-NNN / TC-NNN to REQ-<FEAT>-NNN with --reprefix.

NOTE: this is for CONSUMER projects upgrading from HBC v1. This repo itself has no
legacy D-02 to migrate, so it ships unused here.

Usage:
    python _bmad/scripts/migrate-to-feature-layout.py [--out _bmad-output]
        [--feature default] [--apply] [--reprefix]
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# D-xx → shared subdir (deliverables that are project-global in v2).
SHARED = {"D-12": "coding-standards", "D-03": "glossary", "D-19": "erd", "D-21": "api"}


def plan_moves(out: Path, feature: str) -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []
    feat = out / "features" / feature
    pa = out / "planning-artifacts"
    if pa.is_dir():
        for f in sorted(pa.glob("*")):
            m = re.match(r"(D-\d{2})", f.name)
            if f.is_file() and m and m.group(1) in SHARED:
                moves.append((f, out / "shared" / SHARED[m.group(1)] / f.name))
            else:
                moves.append((f, feat / "planning-artifacts" / f.name))
    for sub in ("implementation-artifacts", "gates", "traceability"):
        d = out / sub
        if d.is_dir():
            for f in sorted(d.glob("*")):
                moves.append((f, feat / sub / f.name))
    return moves


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate legacy HBC output to per-feature layout.")
    ap.add_argument("--out", default="_bmad-output", help="Output folder root")
    ap.add_argument("--feature", default="default", help="Feature slug for legacy artifacts")
    ap.add_argument("--apply", action="store_true", help="Actually move (default: dry-run)")
    ap.add_argument("--reprefix", action="store_true",
                    help="Re-prefix REQ-NNN/TC-NNN → REQ-<FEAT>-NNN in moved D-02 + matrix")
    args = ap.parse_args()

    out = Path(args.out)
    if not out.is_dir():
        print(f"Output folder not found: {out}")
        return 2

    moves = plan_moves(out, args.feature)
    legacy_dirs = [out / s for s in ("planning-artifacts", "implementation-artifacts", "gates", "traceability")]
    if not any(d.is_dir() for d in legacy_dirs):
        print("No legacy project-level layout found — nothing to migrate (already v2 or empty).")
        return 0

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] feature='{args.feature}' · {len(moves)} item(s)")
    for src, dst in moves:
        print(f"  {src}  ->  {dst}")
        if args.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

    if args.reprefix:
        feat = args.feature.upper()
        targets = list((out / "features" / args.feature).rglob("D-02-*.md")) + \
                  list((out / "features" / args.feature / "traceability").glob("matrix*.md"))
        print(f"\n[reprefix] REQ-/TC- → *-{feat}- in {len(targets)} file(s){'' if args.apply else ' (dry-run)'}")
        if args.apply:
            for t in targets:
                txt = t.read_text(encoding="utf-8")
                txt = re.sub(r"\bREQ-(\d{3,})", rf"REQ-{feat}-\1", txt)
                t.write_text(txt, encoding="utf-8")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to perform the migration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
