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
moved D-02 / D-06 / D-26 / D-27 / task-breakdown / gate / matrix. The reprefix is
ID-ONLY (B14-2): only the leading `REQ-NNN` token of a spec id is rewritten — bare
years, version numbers, or `TC-NNN` ids are never touched. TC ids stay TC-NNN
(numeric, per-feature). The traceability matrix is rebuilt from the legacy 7-col
shape to the v2 8-col shape (a leading `feature` column is injected).

D-CODE RECONCILE (T1.8, BREAKING): consumer projects that ran the pre-reconcile
HBC carry the OLD design D-codes D-08 (Architecture) and D-17 (Behavioral Design).
The canonical numbering is D-08→D-09 and D-17→D-16. Migration renames those
per-feature artifacts AND rewrites matrix `design_ref` cells. It is IDEMPOTENT:
an already-reconciled tree (has D-09/D-16, no D-08/D-17) is skipped, never renamed
twice; a MIXED tree (some old, some new) is reconciled to all-new but a same-target
filename COLLISION is flagged (warning `dcode_collision`) and left for the human.

Safety (--apply): refuses to move when the worktree/target has uncommitted changes
unless --force, and first copies the legacy tree into
`_bmad-output/.archive/migrate-<ts>/` (timestamp from --timestamp; default = a real
wall-clock stamp so re-runs never overwrite a prior backup, B14-4).

With --json, emits a machine-readable plan to stdout (always computed in dry-run).
The JSON shape is the SINGLE SOURCE OF TRUTH for the headless contract (B14-5):
    {status, applied, feature, moves:[{src,dst}], reprefix:{REQ-001:REQ-FEAT-001},
     reprefix_diff:[{file,before,after}], dcode_rename:[{from,to}],
     matrix:{from_cols,to_cols,rebuilt}, missing_from_matrix:[REQ-...],
     backup, decision_log, validation:{valid,gaps}, warnings:[...], reason}

NOTE: this is for CONSUMER projects upgrading from HBC v1. This repo itself has no
legacy D-02 to migrate, so it ships unused here.

Usage (engine ships with the skill; the skill invokes it via {skill-root}/scripts):
    python .claude/skills/hbc-migrate/scripts/migrate-to-feature-layout.py [--out _bmad-output]
        [--feature default] [--apply] [--reprefix] [--json]
        [--force] [--timestamp <ts>]
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Shared validation primitives (missing_from_matrix, req_num_map). Bootstrap relative
# to skill root: <skill>/scripts/x.py -> parents[2] is src/, then hbc-shared/lib.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import missing_from_matrix  # type: ignore
except Exception:  # pragma: no cover - shared lib always ships alongside
    missing_from_matrix = None  # type: ignore

# D-xx → shared subdir (deliverables that are project-global in v2).
SHARED = {"D-12": "coding-standards", "D-03": "glossary", "D-19": "erd", "D-21": "api"}

# Deliverables that carry REQ ids and thus get re-prefixed when moved.
# B14-3: implementation artifacts (task-breakdown) and gates reference REQ ids too,
# so they are matched by content (any moved per-feature .md), not just these D-docs.
REPREFIX_DOCS = ("D-02", "D-06", "D-26", "D-27")  # D-06 may reference REQ ids in flows

# D-code reconcile (T1.8): old design code -> canonical code. BREAKING for consumers.
DCODE_RECONCILE = {"D-08": "D-09", "D-17": "D-16"}

# Legacy 7-col matrix header (no leading `feature`).
LEGACY_MATRIX_COLS = ["req_id", "story_id", "design_ref", "code_ref",
                      "test_ref", "gate_status", "timestamp"]
# v2 8-col header (leading `feature` injected).
V2_MATRIX_COLS = ["feature"] + LEGACY_MATRIX_COLS

LEGACY_DIRS = ("planning-artifacts", "implementation-artifacts", "gates", "traceability")

# Per-feature subdirs whose .md files may embed REQ ids (B14-3: not just planning).
REPREFIX_SUBDIRS = ("planning-artifacts", "implementation-artifacts", "gates", "traceability")

REQ_TOKEN_RE = re.compile(r"\bREQ-(\d{3,})\b")
DCODE_TOKEN_RE = re.compile(r"\bD-(08|17)\b")


def _now_stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def plan_moves(out: Path, feature: str) -> list[tuple[Path, Path]]:
    """Plan src->dst moves, applying D-code reconcile to the destination filename."""
    moves: list[tuple[Path, Path]] = []
    feat = out / "features" / feature
    pa = out / "planning-artifacts"
    if pa.is_dir():
        for f in sorted(pa.glob("*")):
            m = re.match(r"(D-\d{2})", f.name)
            if f.is_file() and m and m.group(1) in SHARED:
                moves.append((f, out / "shared" / SHARED[m.group(1)] / f.name))
            else:
                moves.append((f, feat / "planning-artifacts" / reconcile_filename(f.name)))
    for sub in ("implementation-artifacts", "gates", "traceability"):
        d = out / sub
        if d.is_dir():
            for f in sorted(d.glob("*")):
                moves.append((f, feat / sub / reconcile_filename(f.name)))
    return moves


def reconcile_filename(name: str) -> str:
    """Rename a leading D-08/D-17 prefix to its canonical D-09/D-16 (id-only)."""
    m = re.match(r"(D-\d{2})", name)
    if m and m.group(1) in DCODE_RECONCILE:
        return DCODE_RECONCILE[m.group(1)] + name[len(m.group(1)):]
    return name


def plan_dcode_renames(out: Path) -> tuple[list[dict], list[str]]:
    """Detect per-feature artifacts (in the flat planning-artifacts) carrying an old
    design D-code. Returns (renames, warnings). Idempotent: already-canonical files
    (D-09/D-16) are not in the list. MIXED tree → a target-name collision is warned.
    """
    renames: list[dict] = []
    warnings: list[str] = []
    pa = out / "planning-artifacts"
    if not pa.is_dir():
        return renames, warnings
    names = {f.name for f in pa.glob("*") if f.is_file()}
    for f in sorted(pa.glob("*")):
        if not f.is_file():
            continue
        new = reconcile_filename(f.name)
        if new != f.name:
            collision = new in names
            renames.append({"from": f.name, "to": new, "collision": collision})
            if collision:
                warnings.append(f"dcode_collision:{f.name}->{new}")
    return renames, warnings


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
    if m and m.group(1) in REPREFIX_DOCS:
        return True
    # B14-3: task-breakdown / implementation / gate files carry REQ refs but no D-code.
    return is_matrix(name) or bool(
        re.search(r"(task-breakdown|implementation|gate|phase-\d)", name, re.IGNORECASE)
    )


def is_matrix(name: str) -> bool:
    return bool(re.match(r"matrix.*\.md$", name))


def _collect_req_ids_from_text(txt: str) -> set[str]:
    return {f"REQ-{m.group(1)}" for m in REQ_TOKEN_RE.finditer(txt)}


def collect_req_ids(out: Path) -> set[str]:
    """Find legacy REQ-NNN ids (un-namespaced) across moved per-feature docs + matrix.

    Scans the *source* (pre-move) locations so the map can be previewed in dry-run.
    A REQ id already shaped REQ-<WORD>-NNN is left alone by the id-only regex.
    """
    ids: set[str] = set()
    for f in _reprefix_sources_flat(out):
        try:
            ids |= _collect_req_ids_from_text(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return ids


def _reprefix_sources_flat(out: Path) -> list[Path]:
    """Flat (pre-move) files that carry REQ ids: planning D-docs, impl, gates, matrix."""
    sources: list[Path] = []
    for sub in ("planning-artifacts", "implementation-artifacts", "gates", "traceability"):
        d = out / sub
        if not d.is_dir():
            continue
        for f in d.glob("*"):
            if f.is_file() and is_reprefix_target(f.name):
                sources.append(f)
    return sources


def build_reprefix_map(out: Path, feat_upper: str) -> dict[str, str]:
    """Map REQ-NNN → REQ-<FEAT>-NNN. TC ids are intentionally absent (not namespaced)."""
    return {rid: f"REQ-{feat_upper}-{rid.split('-', 1)[1]}" for rid in sorted(collect_req_ids(out))}


def reprefix_req(text: str, feat_upper: str) -> str:
    """Namespace bare REQ-NNN → REQ-<FEAT>-NNN (ID-ONLY, B14-2). Already-namespaced
    ids are left alone (the \\b...\\d-only token never matches REQ-WORD-NNN). TC ids
    and plain numbers are never touched."""
    return REQ_TOKEN_RE.sub(rf"REQ-{feat_upper}-\1", text)


def reprefix_diff(out: Path, feat_upper: str) -> list[dict]:
    """B14-2 dry-run diff: per flat source file, the before→after REQ-id changes."""
    diff: list[dict] = []
    for f in _reprefix_sources_flat(out):
        try:
            txt = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        before = sorted(_collect_req_ids_from_text(txt))
        if not before:
            continue
        after = [f"REQ-{feat_upper}-{rid.split('-', 1)[1]}" for rid in before]
        diff.append({"file": f.name, "before": before, "after": after})
    return diff


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{1,}:?", c or "") for c in cells) and any(c for c in cells)


def reconcile_dcode_text(text: str) -> str:
    """Rewrite D-08→D-09 / D-17→D-16 tokens inside a doc (e.g. matrix design_ref)."""
    return DCODE_TOKEN_RE.sub(lambda m: DCODE_RECONCILE["D-" + m.group(1)], text)


def rebuild_matrix(text: str, feature: str, feat_upper: str | None = None) -> tuple[str, bool]:
    """Rebuild a legacy 7-col matrix into the v2 8-col shape.

    Injects a leading `feature` column. Value = `shared` for rows whose req_id is
    REQ-SHARED-*, else the target `feature` slug. If REQ reprefix is requested
    (feat_upper given), bare REQ-NNN cells are also namespaced. `design_ref` cells
    carrying an old D-08/D-17 are reconciled to D-09/D-16 (T1.8). Idempotent: a
    matrix already in 8-col shape is returned with rebuilt=False (but D-code
    reconcile still applied so a re-run on a half-reconciled matrix self-heals).

    Returns (new_text, rebuilt).
    """
    lines = text.splitlines()
    out_lines: list[str] = []
    rebuilt = False
    header_seen = False
    already_v2 = False

    for line in lines:
        stripped = line.strip()
        is_table_row = stripped.startswith("|") and stripped.count("|") >= 2
        if not is_table_row:
            out_lines.append(reconcile_dcode_text(line))
            continue

        cells = _split_row(line)

        if not header_seen:
            lowered = [c.lower() for c in cells]
            if lowered == V2_MATRIX_COLS:
                already_v2 = True
                out_lines.append(line)
                header_seen = True
                continue
            if lowered == LEGACY_MATRIX_COLS:
                out_lines.append("| " + " | ".join(V2_MATRIX_COLS) + " |")
                header_seen = True
                rebuilt = True
                continue
            # Unknown header — leave the whole text alone, treat as not-rebuilt.
            out_lines.append(reconcile_dcode_text(line))
            continue

        if _is_separator(cells):
            if already_v2:
                out_lines.append(line)
            else:
                out_lines.append("|" + "|".join(["-------"] * len(V2_MATRIX_COLS)) + "|")
            continue

        # Reprefix REQ + reconcile D-codes in the row.
        if feat_upper:
            cells = [reprefix_req(c, feat_upper) for c in cells]
        cells = [reconcile_dcode_text(c) for c in cells]

        if already_v2:
            # Already 8-col — keep shape, only the in-cell rewrites applied above.
            out_lines.append("| " + " | ".join(cells) + " |")
            continue

        req_cell = cells[0] if cells else ""
        feat_val = "shared" if re.search(r"REQ-SHARED-", req_cell, re.IGNORECASE) else feature
        body = (cells + [""] * len(LEGACY_MATRIX_COLS))[:len(LEGACY_MATRIX_COLS)]
        out_lines.append("| " + " | ".join([feat_val] + body) + " |")

    new_text = "\n".join(out_lines)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, rebuilt


def _matrix_files(tr: Path) -> list[Path]:
    if not tr.is_dir():
        return []
    return [f for f in tr.glob("*") if f.is_file() and is_matrix(f.name)]


def matrix_cols(out: Path, sub: str = "traceability") -> int | None:
    """Detect the column count of the legacy matrix (7 / 8 / None if absent)."""
    for f in _matrix_files(out / sub):
        try:
            txt = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line in txt.splitlines():
            cells = [c.lower() for c in _split_row(line)]
            if cells == LEGACY_MATRIX_COLS:
                return 7
            if cells == V2_MATRIX_COLS:
                return 8
    return None


def matrix_needs_rebuild(out: Path) -> bool:
    return matrix_cols(out) == 7


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
    for f in _reprefix_sources_flat(out):
        try:
            txt = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r"\bREQ-([A-Z][A-Z0-9]*)-\d{3,}\b", txt):
            tok = m.group(1)
            if tok != "SHARED":
                feats.add(tok)
    return len(feats) > 1


def compute_missing_from_matrix(out: Path, feat_upper: str | None) -> list[str]:
    """B14-1: REQ ids in D-02 but absent from the matrix (post-migrate gap surface).

    Computed on the *source* tree so it can be previewed in dry-run. When reprefix
    is on, both sides are namespaced first so identity (trailing number) is sound.
    """
    if missing_from_matrix is None:
        return []
    pa = out / "planning-artifacts"
    tr = out / "traceability"
    d02s = []
    if pa.is_dir():
        d02s = [f for f in pa.glob("*") if f.is_file() and re.match(r"D-02\b", f.name)]
    if not d02s:
        return []
    d02_text = "\n".join(_safe_read(f) for f in d02s)
    matrix_text = "\n".join(_safe_read(f) for f in _matrix_files(tr))
    if feat_upper:
        d02_text = reprefix_req(d02_text, feat_upper)
        matrix_text = reprefix_req(matrix_text, feat_upper)
    try:
        return missing_from_matrix(d02_text, matrix_text)
    except Exception:
        return []


def _safe_read(f: Path) -> str:
    try:
        return f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


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
    """Copy the legacy tree to _bmad-output/.archive/migrate-<ts>/ before moving.

    B14-4: the timestamp is wall-clock-unique by default, so a re-run never overwrites
    a prior backup. If the (unlikely) exact dir already exists, suffix a counter.
    """
    base = out / ".archive" / f"migrate-{timestamp}"
    dest = base
    n = 1
    while dest.exists() and any(dest.iterdir()):
        dest = out / ".archive" / f"migrate-{timestamp}-{n}"
        n += 1
    dest.mkdir(parents=True, exist_ok=True)
    for sub in LEGACY_DIRS:
        src = out / sub
        if src.is_dir():
            shutil.copytree(src, dest / sub, dirs_exist_ok=True)
    return dest


def build_plan(out: Path, feature: str, reprefix: bool) -> dict:
    """Compute the deterministic plan (no writes). Matches the headless JSON contract."""
    warnings: list[str] = []
    feat_upper = feature.upper() if reprefix else None
    if not has_legacy_layout(out):
        return {
            "status": "nothing_to_migrate",
            "applied": False,
            "feature": feature,
            "moves": [],
            "reprefix": {},
            "reprefix_diff": [],
            "dcode_rename": [],
            "matrix": {"from_cols": matrix_cols(out), "to_cols": matrix_cols(out), "rebuilt": False},
            "missing_from_matrix": [],
            "backup": None,
            "decision_log": None,
            "validation": {"valid": None, "gaps": []},
            "warnings": warnings,
            "reason": "nothing_to_migrate",
        }

    moves = plan_moves(out, feature)
    reprefix_map: dict[str, str] = {}
    diff: list[dict] = []
    if reprefix:
        reprefix_map = build_reprefix_map(out, feat_upper)
        diff = reprefix_diff(out, feat_upper)

    dcode_rename, dcode_warn = plan_dcode_renames(out)
    warnings += dcode_warn

    if detect_multi_feature(out):
        warnings.append("multi_feature_suspected")

    from_cols = matrix_cols(out)
    will_rebuild = from_cols == 7

    return {
        "status": "ready",
        "applied": False,
        "feature": feature,
        "moves": [{"src": str(src), "dst": str(dst)} for src, dst in moves],
        "reprefix": reprefix_map,
        "reprefix_diff": diff,
        "dcode_rename": dcode_rename,
        "matrix": {"from_cols": from_cols,
                   "to_cols": 8 if from_cols else from_cols,
                   "rebuilt": False},
        "missing_from_matrix": compute_missing_from_matrix(out, feat_upper),
        "backup": None,
        "decision_log": None,
        "validation": {"valid": None, "gaps": []},
        "warnings": warnings,
        "reason": None,
    }


def write_decision_log(out: Path, plan: dict, timestamp: str) -> Path:
    """Append a human-readable record of every change to .decision-log.md."""
    log = out / ".decision-log.md"
    lines = [f"\n## Migrate v1→v2 — {timestamp}", "",
             f"- feature: `{plan['feature']}`",
             f"- moves: {len(plan['moves'])}",
             f"- reprefix: {len(plan['reprefix'])} REQ id(s)",
             f"- d-code rename: {len(plan['dcode_rename'])}",
             f"- matrix: {plan['matrix']['from_cols']}→{plan['matrix']['to_cols']} cols "
             f"(rebuilt={plan['matrix']['rebuilt']})",
             f"- backup: `{plan.get('backup')}`"]
    if plan.get("missing_from_matrix"):
        lines.append(f"- ⚠ missing_from_matrix: {plan['missing_from_matrix']}")
    for w in plan.get("warnings", []):
        lines.append(f"- ⚠ warning: {w}")
    with log.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return log


def apply_migration(out: Path, feature: str, reprefix: bool, timestamp: str) -> dict:
    """Perform the move + reprefix + D-code reconcile + matrix rebuild. Returns the plan."""
    plan = build_plan(out, feature, reprefix)
    if plan["status"] != "ready":
        return plan

    feat_upper = feature.upper()
    feat_for_matrix = feat_upper if reprefix else None

    # 1. Backup the legacy tree first.
    backup = archive_legacy(out, timestamp)
    plan["backup"] = str(backup)

    # 2. Move files (destinations already carry reconciled D-code filenames).
    for src, dst in plan_moves(out, feature):
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            if dst.exists():
                # MIXED-tree collision: keep the existing canonical file, archive the
                # incoming under a suffix so nothing is silently overwritten (B14-4).
                shutil.move(str(src), str(dst.with_name(dst.stem + f".incoming-{timestamp}" + dst.suffix)))
            else:
                shutil.move(str(src), str(dst))

    # 3. Reprefix REQ (id-only) + reconcile D-codes in moved per-feature files.
    feat_root = out / "features" / feature
    for sub in REPREFIX_SUBDIRS:
        d = feat_root / sub
        if not d.is_dir():
            continue
        for f in d.rglob("*"):
            if not (f.is_file() and is_reprefix_target(f.name)):
                continue
            txt = _safe_read(f)
            if reprefix:
                txt = reprefix_req(txt, feat_upper)
            txt = reconcile_dcode_text(txt)
            f.write_text(txt, encoding="utf-8")

    # 4. Rebuild matrix to 8 cols (and reconcile design_ref D-codes).
    rebuilt_any = False
    for f in _matrix_files(feat_root / "traceability"):
        txt = _safe_read(f)
        new_txt, rebuilt = rebuild_matrix(txt, feature, feat_for_matrix)
        f.write_text(new_txt, encoding="utf-8")
        rebuilt_any = rebuilt_any or rebuilt
    plan["matrix"]["rebuilt"] = rebuilt_any

    # 5. Recompute missing_from_matrix on the MIGRATED tree (faithful surface, B14-1).
    plan["missing_from_matrix"] = _missing_after(feat_root)

    # 6. Decision log.
    plan["decision_log"] = str(write_decision_log(out, plan, timestamp))

    plan["status"] = "migrated"
    plan["applied"] = True
    return plan


def _missing_after(feat_root: Path) -> list[str]:
    if missing_from_matrix is None:
        return []
    pa = feat_root / "planning-artifacts"
    tr = feat_root / "traceability"
    d02s = [f for f in pa.glob("*") if f.is_file() and re.match(r"D-02\b", f.name)] if pa.is_dir() else []
    if not d02s:
        return []
    d02_text = "\n".join(_safe_read(f) for f in d02s)
    matrix_text = "\n".join(_safe_read(f) for f in _matrix_files(tr))
    try:
        return missing_from_matrix(d02_text, matrix_text)
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate legacy HBC output to per-feature layout.")
    ap.add_argument("--out", default="_bmad-output", help="Output folder root")
    ap.add_argument("--feature", default="default", help="Feature slug for legacy artifacts")
    ap.add_argument("--apply", action="store_true", help="Actually move (default: dry-run)")
    ap.add_argument("--reprefix", action="store_true",
                    help="Re-prefix REQ-NNN → REQ-<FEAT>-NNN (id-only) in moved per-feature "
                         "docs + matrix (TC ids are left as-is)")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable plan JSON to stdout")
    ap.add_argument("--force", action="store_true", help="Apply even if the worktree is dirty")
    ap.add_argument("--timestamp", default=None,
                    help="Timestamp for the backup folder (default: wall-clock, unique per run)")
    args = ap.parse_args()

    timestamp = args.timestamp or _now_stamp()
    out = Path(args.out)
    if not out.is_dir():
        payload = {"status": "out_not_found", "applied": False, "feature": args.feature,
                   "moves": [], "reprefix": {}, "reprefix_diff": [], "dcode_rename": [],
                   "matrix": {"from_cols": None, "to_cols": None, "rebuilt": False},
                   "missing_from_matrix": [], "backup": None, "decision_log": None,
                   "validation": {"valid": None, "gaps": []},
                   "warnings": [f"output folder not found: {out}"], "reason": "out_not_found"}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"Output folder not found: {out}")
        return 2

    # Dirty guard only matters for --apply.
    if args.apply and not args.force and worktree_dirty(out):
        plan = build_plan(out, args.feature, args.reprefix)
        plan["status"] = "dirty_worktree"
        plan["reason"] = "dirty_worktree"
        plan["warnings"].append("uncommitted changes present — re-run with --force or commit first")
        if args.json:
            print(json.dumps(plan, ensure_ascii=False))
        else:
            print("Refusing to migrate: worktree has uncommitted changes. "
                  "Commit/stash them or pass --force.")
        return 3

    if args.apply:
        plan = apply_migration(out, args.feature, args.reprefix, timestamp)
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

    if plan["dcode_rename"]:
        print(f"\n[d-code reconcile] {len(plan['dcode_rename'])} file(s) D-08→D-09 / D-17→D-16")
        for r in plan["dcode_rename"]:
            flag = "  ⚠ COLLISION (target exists)" if r.get("collision") else ""
            print(f"  {r['from']} -> {r['to']}{flag}")

    if args.reprefix:
        n = len(plan["reprefix"])
        print(f"\n[reprefix] {n} REQ id(s) → REQ-{args.feature.upper()}-NNN "
              f"(id-only; TC ids unchanged){'' if args.apply else ' (dry-run)'}")
        for d in plan["reprefix_diff"]:
            print(f"  {d['file']}: {', '.join(d['before'])} -> {', '.join(d['after'])}")

    if plan["matrix"]["from_cols"] == 7:
        print(f"\n[matrix] legacy 7-col → v2 8-col (inject `feature`)"
              f"{'' if args.apply else ' (dry-run)'}")

    if plan.get("missing_from_matrix"):
        print(f"\n[traceability gap] REQ in D-02 but NOT in matrix: {plan['missing_from_matrix']}")
        print("  → run [TRU] (hbc-traceability update) to backfill so it matches D-02.")

    for w in plan["warnings"]:
        print(f"\n[warning] {w}")

    if plan.get("backup"):
        print(f"\n[backup] {plan['backup']}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to perform the migration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
