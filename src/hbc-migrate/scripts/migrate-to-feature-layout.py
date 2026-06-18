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
(D-12, D-03, D-19, D-21) are routed to shared/.

With --reprefix, legacy REQ-NNN ids are namespaced to REQ-<FEAT>-NNN across every
moved D-02 / D-06 / D-26 / D-27 / matrix (D-06 business-flow may reference REQ ids
in its flows, so it is re-prefixed too). TC ids are NOT namespaced — they stay TC-NNN
(numeric, per-feature) and are left untouched. The traceability matrix is also
rebuilt from the legacy 7-col shape to the v2 8-col shape (a leading `feature`
column is injected; REQ-SHARED rows get `shared`, everything else the feature slug).

Safety (--apply): refuses to move when the worktree/target has uncommitted changes
unless --force, and first copies the legacy tree into
`_bmad-output/.archive/migrate-<ts>/` (timestamp from --timestamp).

With --json, emits a machine-readable plan to stdout (always computed in dry-run):
    {status, feature, moves:[{src,dst}], reprefix:{REQ-001:REQ-FEAT-001,...},
     matrix_rebuild:bool, warnings:[...]}

NOTE: this is for CONSUMER projects upgrading from HBC v1. This repo itself has no
legacy D-02 to migrate, so it ships unused here.

Usage (engine ships with the skill; the skill invokes it via {skill-root}/scripts):
    python .claude/skills/hbc-migrate/scripts/migrate-to-feature-layout.py [--out _bmad-output]
        [--feature default] [--apply] [--reprefix] [--json]
        [--force] [--timestamp <ts>]
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# D-xx → shared subdir (deliverables that are project-global in v2).
SHARED = {"D-12": "coding-standards", "D-03": "glossary", "D-19": "erd", "D-21": "api"}

# Deliverables that carry REQ ids and thus get re-prefixed when moved.
REPREFIX_DOCS = ("D-02", "D-06", "D-26", "D-27")  # D-06 may reference REQ ids in flows

# Legacy 7-col matrix header (no leading `feature`).
LEGACY_MATRIX_COLS = ["req_id", "story_id", "design_ref", "code_ref",
                      "test_ref", "gate_status", "timestamp"]
# v2 8-col header (leading `feature` injected).
V2_MATRIX_COLS = ["feature"] + LEGACY_MATRIX_COLS

LEGACY_DIRS = ("planning-artifacts", "implementation-artifacts", "gates", "traceability")

DEFAULT_TIMESTAMP = "00000000-000000"


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


def has_legacy_layout(out: Path) -> bool:
    """True only if a legacy dir exists AND still contains files to migrate.

    After an --apply the (now-empty) legacy dirs may linger; an empty legacy tree
    means there is nothing left to migrate (idempotent re-run → nothing_to_migrate).
    """
    for s in LEGACY_DIRS:
        d = out / s
        if d.is_dir() and any(f.is_file() for f in d.rglob("*")):
            return True
    return False


def is_reprefix_target(name: str) -> bool:
    m = re.match(r"(D-\d{2})", name)
    return bool(m and m.group(1) in REPREFIX_DOCS)


def is_matrix(name: str) -> bool:
    return bool(re.match(r"matrix.*\.md$", name))


def collect_req_ids(out: Path) -> set[str]:
    """Find legacy REQ-NNN ids (un-namespaced) across moved D-02/D-26/D-27 + matrix.

    Scans the *source* (pre-move) locations so the map can be previewed in dry-run.
    A REQ id already shaped REQ-<WORD>-NNN is considered already-migrated and skipped.
    """
    ids: set[str] = set()
    pa = out / "planning-artifacts"
    sources: list[Path] = []
    if pa.is_dir():
        sources += [f for f in pa.glob("*") if f.is_file() and is_reprefix_target(f.name)]
    tr = out / "traceability"
    if tr.is_dir():
        sources += [f for f in tr.glob("*") if f.is_file() and is_matrix(f.name)]
    for f in sources:
        try:
            txt = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r"\bREQ-(\d{3,})\b", txt):
            ids.add(f"REQ-{m.group(1)}")
    return ids


def build_reprefix_map(out: Path, feat_upper: str) -> dict[str, str]:
    """Map REQ-NNN → REQ-<FEAT>-NNN. TC ids are intentionally absent (not namespaced)."""
    return {rid: f"REQ-{feat_upper}-{rid.split('-', 1)[1]}" for rid in sorted(collect_req_ids(out))}


def reprefix_req(text: str, feat_upper: str) -> str:
    """Namespace bare REQ-NNN → REQ-<FEAT>-NNN. Already-namespaced ids are left alone.
    TC ids are never touched."""
    return re.sub(r"\bREQ-(\d{3,})\b", rf"REQ-{feat_upper}-\1", text)


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{1,}:?", c or "") for c in cells) and any(c for c in cells)


def rebuild_matrix(text: str, feature: str, feat_upper: str | None = None) -> tuple[str, bool]:
    """Rebuild a legacy 7-col matrix into the v2 8-col shape.

    Injects a leading `feature` column. Value = `shared` for rows whose req_id is
    REQ-SHARED-*, else the target `feature` slug. If REQ reprefix is requested
    (feat_upper given), bare REQ-NNN cells are also namespaced. Idempotent: a matrix
    already in 8-col shape is returned unchanged with rebuilt=False.

    Returns (new_text, rebuilt).
    """
    lines = text.splitlines()
    out_lines: list[str] = []
    rebuilt = False
    header_seen = False

    for line in lines:
        stripped = line.strip()
        is_table_row = stripped.startswith("|") and stripped.count("|") >= 2
        if not is_table_row:
            out_lines.append(line)
            continue

        cells = _split_row(line)

        if not header_seen:
            lowered = [c.lower() for c in cells]
            if lowered == V2_MATRIX_COLS:
                # Already v2 — nothing to rebuild for this table.
                out_lines.append(line)
                header_seen = True
                continue
            if lowered == LEGACY_MATRIX_COLS:
                out_lines.append("| " + " | ".join(V2_MATRIX_COLS) + " |")
                header_seen = True
                rebuilt = True
                continue
            # Unknown header — leave the whole text alone, treat as not-rebuilt.
            out_lines.append(line)
            continue

        # In-body rows (header already seen and it was legacy → rebuild=True).
        if _is_separator(cells):
            out_lines.append("|" + "|".join(["-------"] * len(V2_MATRIX_COLS)) + "|")
            continue

        # Optionally reprefix REQ in the row first.
        if feat_upper:
            cells = [reprefix_req(c, feat_upper) for c in cells]

        req_cell = cells[0] if cells else ""
        feat_val = "shared" if re.search(r"REQ-SHARED-", req_cell, re.IGNORECASE) else feature
        # Pad/trim legacy body to 7 data cols, then prepend feature.
        body = (cells + [""] * len(LEGACY_MATRIX_COLS))[:len(LEGACY_MATRIX_COLS)]
        out_lines.append("| " + " | ".join([feat_val] + body) + " |")

    new_text = "\n".join(out_lines)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, rebuilt


def matrix_needs_rebuild(out: Path) -> bool:
    """True if a legacy 7-col matrix is present in traceability/."""
    tr = out / "traceability"
    if not tr.is_dir():
        return False
    for f in tr.glob("*"):
        if not (f.is_file() and is_matrix(f.name)):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line in txt.splitlines():
            cells = [c.lower() for c in _split_row(line)]
            if cells == LEGACY_MATRIX_COLS:
                return True
            if cells == V2_MATRIX_COLS:
                return False
    return False


def detect_multi_feature(out: Path) -> bool:
    """Heuristic: legacy artifacts that clearly span multiple features.

    Out of scope to auto-split; we only warn. Signals:
      - multiple distinct D-02 files (e.g. D-02-auth, D-02-billing), or
      - already-namespaced REQ ids with >1 distinct <FEAT> token in legacy docs.
    """
    pa = out / "planning-artifacts"
    if pa.is_dir():
        d02 = [f for f in pa.glob("*") if f.is_file() and re.match(r"D-02\b", f.name)]
        if len(d02) > 1:
            return True
    feats: set[str] = set()
    sources: list[Path] = []
    if pa.is_dir():
        sources += [f for f in pa.glob("*") if f.is_file() and is_reprefix_target(f.name)]
    tr = out / "traceability"
    if tr.is_dir():
        sources += [f for f in tr.glob("*") if f.is_file() and is_matrix(f.name)]
    for f in sources:
        try:
            txt = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r"\bREQ-([A-Z][A-Z0-9]*)-\d{3,}\b", txt):
            tok = m.group(1)
            if tok != "SHARED":
                feats.add(tok)
    return len(feats) > 1


def worktree_dirty(out: Path) -> bool:
    """Best-effort uncommitted-changes guard over the output tree (and its repo)."""
    import subprocess
    try:
        repo = out.resolve()
        r = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True, text=True, encoding="utf-8",
        )
    except (OSError, ValueError):
        return False
    if r.returncode != 0:
        return False
    return bool(r.stdout.strip())


def archive_legacy(out: Path, timestamp: str) -> Path:
    """Copy the legacy tree to _bmad-output/.archive/migrate-<ts>/ before moving."""
    dest = out / ".archive" / f"migrate-{timestamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for sub in LEGACY_DIRS:
        src = out / sub
        if src.is_dir():
            shutil.copytree(src, dest / sub, dirs_exist_ok=True)
    return dest


def build_plan(out: Path, feature: str, reprefix: bool) -> dict:
    """Compute the deterministic plan (no writes)."""
    warnings: list[str] = []
    if not has_legacy_layout(out):
        return {
            "status": "nothing_to_migrate",
            "feature": feature,
            "moves": [],
            "reprefix": {},
            "matrix_rebuild": False,
            "warnings": warnings,
        }

    moves = plan_moves(out, feature)
    reprefix_map: dict[str, str] = {}
    if reprefix:
        reprefix_map = build_reprefix_map(out, feature.upper())

    if detect_multi_feature(out):
        warnings.append("multi_feature_suspected")

    return {
        "status": "ready",
        "feature": feature,
        "moves": [{"src": str(src), "dst": str(dst)} for src, dst in moves],
        "reprefix": reprefix_map,
        "matrix_rebuild": matrix_needs_rebuild(out),
        "warnings": warnings,
    }


def apply_migration(out: Path, feature: str, reprefix: bool, timestamp: str) -> dict:
    """Perform the move + reprefix + matrix rebuild. Returns the executed plan."""
    plan = build_plan(out, feature, reprefix)
    if plan["status"] != "ready":
        return plan

    feat_upper = feature.upper()
    feat_for_matrix = feat_upper if reprefix else None

    # 1. Backup the legacy tree first.
    archive_legacy(out, timestamp)

    # 2. Move files.
    for src, dst in plan_moves(out, feature):
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.move(str(src), str(dst))

    # 3. Reprefix REQ in moved D-02/D-26/D-27 (+ matrix), then rebuild matrix to 8 cols.
    feat_root = out / "features" / feature
    if reprefix:
        for f in feat_root.rglob("*"):
            if f.is_file() and is_reprefix_target(f.name):
                txt = f.read_text(encoding="utf-8")
                f.write_text(reprefix_req(txt, feat_upper), encoding="utf-8")

    tr = feat_root / "traceability"
    if tr.is_dir():
        for f in tr.glob("*"):
            if f.is_file() and is_matrix(f.name):
                txt = f.read_text(encoding="utf-8")
                new_txt, _ = rebuild_matrix(txt, feature, feat_for_matrix)
                f.write_text(new_txt, encoding="utf-8")

    plan["status"] = "migrated"
    plan["archive"] = str(out / ".archive" / f"migrate-{timestamp}")
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate legacy HBC output to per-feature layout.")
    ap.add_argument("--out", default="_bmad-output", help="Output folder root")
    ap.add_argument("--feature", default="default", help="Feature slug for legacy artifacts")
    ap.add_argument("--apply", action="store_true", help="Actually move (default: dry-run)")
    ap.add_argument("--reprefix", action="store_true",
                    help="Re-prefix REQ-NNN → REQ-<FEAT>-NNN in moved D-02/D-26/D-27 + matrix "
                         "(TC ids are left as-is)")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable plan JSON to stdout")
    ap.add_argument("--force", action="store_true", help="Apply even if the worktree is dirty")
    ap.add_argument("--timestamp", default=DEFAULT_TIMESTAMP,
                    help="Timestamp for the backup folder (Date.now is unavailable in some contexts)")
    args = ap.parse_args()

    out = Path(args.out)
    if not out.is_dir():
        if args.json:
            print(json.dumps({"status": "out_not_found", "feature": args.feature,
                              "moves": [], "reprefix": {}, "matrix_rebuild": False,
                              "warnings": [f"output folder not found: {out}"]}))
        else:
            print(f"Output folder not found: {out}")
        return 2

    # Dirty guard only matters for --apply.
    if args.apply and not args.force and worktree_dirty(out):
        plan = build_plan(out, args.feature, args.reprefix)
        plan["status"] = "dirty_worktree"
        plan["warnings"].append("uncommitted changes present — re-run with --force or commit first")
        if args.json:
            print(json.dumps(plan, ensure_ascii=False))
        else:
            print("Refusing to migrate: worktree has uncommitted changes. "
                  "Commit/stash them or pass --force.")
        return 3

    if args.apply:
        plan = apply_migration(out, args.feature, args.reprefix, args.timestamp)
    else:
        plan = build_plan(out, args.feature, args.reprefix)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False))
        return 0

    # Human-readable output.
    if plan["status"] == "nothing_to_migrate":
        print("No legacy project-level layout found — nothing to migrate (already v2 or empty).")
        return 0

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] feature='{args.feature}' · {len(plan['moves'])} item(s)")
    for mv in plan["moves"]:
        print(f"  {mv['src']}  ->  {mv['dst']}")

    if args.reprefix:
        n = len(plan["reprefix"])
        print(f"\n[reprefix] {n} REQ id(s) → REQ-{args.feature.upper()}-NNN "
              f"(TC ids unchanged){'' if args.apply else ' (dry-run)'}")
        for k, v in plan["reprefix"].items():
            print(f"  {k} -> {v}")

    if plan["matrix_rebuild"]:
        print(f"\n[matrix] legacy 7-col → v2 8-col (inject `feature`)"
              f"{'' if args.apply else ' (dry-run)'}")

    for w in plan["warnings"]:
        print(f"\n[warning] {w}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to perform the migration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
