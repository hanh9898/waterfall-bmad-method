#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for migrate-to-feature-layout.py.

Run: python -m pytest src/hbc-migrate -q
Covers: dry-run plan JSON (contract shape), shared-vs-per-feature routing, REQ reprefix
(id-only, TC untouched), reprefix diff, 8-col matrix rebuild, idempotency (already-v2),
backup + dirty guard, impl/gate reprefix (B14-3), unique-timestamp backup (B14-4),
missing_from_matrix emit (B14-1), D-code reconcile D-08→D-09 / D-17→D-16 + idempotent
+ mixed tree (T1.8), and contract↔engine JSON-shape sync (B14-5).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "migrate-to-feature-layout.py"

LEGACY_MATRIX = (
    "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
    "|--------|----------|------------|----------|----------|-------------|-----------|\n"
    "| REQ-001 |  | D-08 | foo.py | TC-001 | PASSED | 2026-01-01 |\n"
    "| REQ-SHARED-009 |  | D-17 | bar.py | TC-009 |  | 2026-01-01 |\n"
)

D02 = (
    "# Requirements\n\n"
    "REQ-001: user can log in (verified by TC-001).\n"
    "REQ-002: user can log out (TC-002).\n"
)

D26 = "# Test Plan\nScope covers REQ-001 and REQ-002 via TC-001/TC-002.\n"
D27 = "# Test Spec\n## TC-001 for REQ-001\n## TC-002 for REQ-002\n"


def run(out: Path, *args, expect_code=0):
    p = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out), *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert p.returncode == expect_code, (
        f"exit {p.returncode} != {expect_code}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
    )
    return p


def run_json(out: Path, *args, expect_code=0):
    p = run(out, "--json", *args, expect_code=expect_code)
    return json.loads(p.stdout)


def make_v1(root: Path) -> Path:
    """Build a v1 (flat) output tree under root/_bmad-output (old D-codes D-08/D-17)."""
    out = root / "_bmad-output"
    pa = out / "planning-artifacts"
    pa.mkdir(parents=True)
    (pa / "D-02-requirements.md").write_text(D02, encoding="utf-8")
    (pa / "D-26-test-plan.md").write_text(D26, encoding="utf-8")
    (pa / "D-27-test-spec.md").write_text(D27, encoding="utf-8")
    (pa / "D-12-coding-standards.md").write_text("# Coding Standards\n", encoding="utf-8")
    (pa / "D-03-glossary.md").write_text("# Glossary\n", encoding="utf-8")
    (pa / "D-19-erd.md").write_text("# ERD\n", encoding="utf-8")
    (pa / "D-06-business-flow.md").write_text(
        "# Business Flow\nFlow covers REQ-001 (login) then REQ-002 (logout).\n", encoding="utf-8")
    # OLD design D-codes (pre-reconcile consumer).
    (pa / "D-08-architecture.md").write_text(
        "# Architecture\nServes REQ-001.\n", encoding="utf-8")
    (pa / "D-17-behavioral.md").write_text(
        "# Behavioral Design\nSequence for REQ-002.\n", encoding="utf-8")
    impl = out / "implementation-artifacts"
    impl.mkdir(parents=True)
    (impl / "task-breakdown.md").write_text(
        "# Tasks\n- T1 implements REQ-001\n- T2 implements REQ-002\n", encoding="utf-8")
    gates = out / "gates"
    gates.mkdir(parents=True)
    (gates / "phase-1-gate.md").write_text("# Gate\nChecks REQ-001 coverage.\n", encoding="utf-8")
    tr = out / "traceability"
    tr.mkdir(parents=True)
    (tr / "matrix.md").write_text(LEGACY_MATRIX, encoding="utf-8")
    return out


def test_dryrun_plan_json():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--reprefix")
        assert plan["status"] == "ready", plan
        assert plan["applied"] is False, plan
        assert plan["feature"] == "auth"
        assert plan["matrix"]["from_cols"] == 7, plan
        assert plan["matrix"]["rebuilt"] is False, plan  # planned only in dry-run
        assert plan["moves"], "expected moves"
        # Full contract shape present (B14-5).
        for required in ("status", "applied", "feature", "moves", "reprefix", "reprefix_diff",
                         "dcode_rename", "matrix", "missing_from_matrix", "backup",
                         "decision_log", "validation", "warnings", "reason"):
            assert required in plan, f"missing contract key {required}"
        assert plan["backup"] is None and plan["decision_log"] is None
        # dry-run must not write — source files still present.
        assert (out / "planning-artifacts" / "D-02-requirements.md").exists()
        assert not (out / "features").exists()


def test_shared_vs_perfeature_routing():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth")
        dsts = {Path(m["dst"]).as_posix() for m in plan["moves"]}
        assert any("shared/coding-standards/D-12" in x for x in dsts), dsts
        assert any("shared/glossary/D-03" in x for x in dsts), dsts
        assert any("shared/erd/D-19" in x for x in dsts), dsts
        assert any("features/auth/planning-artifacts/D-02" in x for x in dsts), dsts
        assert any("features/auth/planning-artifacts/D-26" in x for x in dsts), dsts
        assert any("features/auth/traceability/matrix.md" in x for x in dsts), dsts
        assert any("features/auth/implementation-artifacts/task-breakdown" in x for x in dsts), dsts
        assert any("features/auth/gates/phase-1-gate" in x for x in dsts), dsts


def test_req_reprefix_idonly_tc_untouched():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--reprefix")
        assert plan["reprefix"].get("REQ-001") == "REQ-AUTH-001", plan["reprefix"]
        assert plan["reprefix"].get("REQ-002") == "REQ-AUTH-002", plan["reprefix"]
        assert all(not k.startswith("TC-") for k in plan["reprefix"]), plan["reprefix"]
        # reprefix diff present and per-file (B14-2).
        assert plan["reprefix_diff"], plan
        files = {d2["file"] for d2 in plan["reprefix_diff"]}
        assert "D-02-requirements.md" in files, files
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        d02 = (out / "features" / "auth" / "planning-artifacts" / "D-02-requirements.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in d02 and "REQ-AUTH-002" in d02, d02
        assert "REQ-001:" not in d02, "bare REQ should be gone"
        assert "TC-001" in d02 and "TC-AUTH-001" not in d02, d02


def test_reprefix_idonly_no_overmatch():
    # B14-2: id-only — years / version numbers / TC ids must NOT be rewritten.
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        (out / "planning-artifacts" / "D-02-requirements.md").write_text(
            "REQ-001 in 2026 v1.2.0 with TC-001 and id 12345.\n", encoding="utf-8")
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        txt = (out / "features" / "auth" / "planning-artifacts" / "D-02-requirements.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in txt
        assert "2026" in txt and "v1.2.0" in txt and "12345" in txt, txt
        assert "TC-001" in txt and "TC-AUTH-001" not in txt, txt


def test_impl_and_gate_reprefixed():
    # B14-3: task-breakdown + gate files reference REQ ids → must be reprefixed.
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        tb = (out / "features" / "auth" / "implementation-artifacts" / "task-breakdown.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in tb and "REQ-001" not in tb, tb
        gate = (out / "features" / "auth" / "gates" / "phase-1-gate.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in gate and "REQ-001" not in gate, gate


def test_matrix_rebuild_8col():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        assert plan["matrix"]["rebuilt"] is True, plan
        mx = (out / "features" / "auth" / "traceability" / "matrix.md").read_text(encoding="utf-8")
        lines = [l for l in mx.splitlines() if l.strip().startswith("|")]
        header = [c.strip().lower() for c in lines[0].strip("|").split("|")]
        assert header == ["feature", "req_id", "story_id", "design_ref", "code_ref",
                          "test_ref", "gate_status", "timestamp"], header
        body = [l for l in lines[2:]]
        cells0 = [c.strip() for c in body[0].strip("|").split("|")]
        assert len(cells0) == 8, cells0
        assert cells0[0] == "auth", cells0
        assert cells0[1] == "REQ-AUTH-001", cells0
        shared_row = [l for l in body if "SHARED" in l][0]
        scells = [c.strip() for c in shared_row.strip("|").split("|")]
        assert scells[0] == "shared", scells


def test_dcode_reconcile_filenames_and_matrix():
    # T1.8: D-08→D-09, D-17→D-16 on filenames AND matrix design_ref.
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--reprefix")
        renames = {(r["from"], r["to"]) for r in plan["dcode_rename"]}
        assert ("D-08-architecture.md", "D-09-architecture.md") in renames, renames
        assert ("D-17-behavioral.md", "D-16-behavioral.md") in renames, renames
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        pa = out / "features" / "auth" / "planning-artifacts"
        assert (pa / "D-09-architecture.md").exists(), "D-08 should be renamed to D-09"
        assert (pa / "D-16-behavioral.md").exists(), "D-17 should be renamed to D-16"
        assert not (pa / "D-08-architecture.md").exists()
        assert not (pa / "D-17-behavioral.md").exists()
        mx = (out / "features" / "auth" / "traceability" / "matrix.md").read_text(encoding="utf-8")
        assert "D-09" in mx and "D-16" in mx, mx
        assert "| D-08 " not in mx and "| D-17 " not in mx, mx


def test_dcode_reconcile_idempotent():
    # T1.8: a tree already reconciled (D-09/D-16) → no rename, no double-rename.
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        # Pre-reconcile: rename the source files to canonical already.
        pa = out / "planning-artifacts"
        (pa / "D-08-architecture.md").rename(pa / "D-09-architecture.md")
        (pa / "D-17-behavioral.md").rename(pa / "D-16-behavioral.md")
        plan = run_json(out, "--feature", "auth")
        assert plan["dcode_rename"] == [], plan["dcode_rename"]
        run(out, "--feature", "auth", "--apply", "--force")
        dst = out / "features" / "auth" / "planning-artifacts"
        assert (dst / "D-09-architecture.md").exists()
        assert (dst / "D-16-behavioral.md").exists()
        # No stray double-renamed files.
        names = {f.name for f in dst.glob("*")}
        assert not any(n.startswith("D-10") or n.startswith("D-15") for n in names), names


def test_dcode_mixed_tree_collision_warned():
    # T1.8 MIXED: both D-08-x.md and D-09-x.md present → target collision warned,
    # incoming file preserved (not silently overwritten).
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        pa = out / "planning-artifacts"
        (pa / "D-09-architecture.md").write_text("# Already canonical arch\n", encoding="utf-8")
        plan = run_json(out, "--feature", "auth")
        assert any(w.startswith("dcode_collision:") for w in plan["warnings"]), plan["warnings"]
        run(out, "--feature", "auth", "--apply", "--force")
        dst = out / "features" / "auth" / "planning-artifacts"
        assert (dst / "D-09-architecture.md").exists()
        incoming = [f for f in dst.glob("*incoming*")]
        assert incoming, "collided incoming file must be preserved, not overwritten"


def test_missing_from_matrix_emitted():
    # B14-1: a REQ in D-02 with no matrix row surfaces in the plan.
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        # D-02 has REQ-001 and REQ-002; matrix only has REQ-001 → 002 missing.
        plan = run_json(out, "--feature", "auth", "--reprefix")
        assert "REQ-AUTH-002" in plan["missing_from_matrix"], plan["missing_from_matrix"]
        # After apply, still faithfully surfaced (no fabrication).
        plan2 = run_json(out, "--feature", "auth", "--reprefix")  # idempotent re-run path
        # apply then check
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        ap = run_json(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        assert "REQ-AUTH-002" in ap["missing_from_matrix"], ap["missing_from_matrix"]


def test_idempotent_already_v2():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        plan = run_json(out, "--feature", "auth", "--reprefix")
        assert plan["status"] == "nothing_to_migrate", plan
        assert plan["moves"] == [], plan
        with tempfile.TemporaryDirectory() as d2:
            empty = Path(d2) / "_bmad-output"
            empty.mkdir()
            plan2 = run_json(empty)
            assert plan2["status"] == "nothing_to_migrate", plan2


def test_backup_created_and_unique():
    # B14-4: backup folder created; default timestamp is unique (no overwrite collision).
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--apply", "--force",
                        "--timestamp", "20260617-101010")
        archive = out / ".archive" / "migrate-20260617-101010"
        assert archive.is_dir(), "archive folder must exist"
        assert (archive / "planning-artifacts" / "D-02-requirements.md").exists()
        assert plan["backup"] and "20260617-101010" in plan["backup"], plan
    # Default (no --timestamp) uses wall-clock; not the old fixed 00000000 sentinel.
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--apply", "--force")
        assert plan["backup"], plan
        assert "migrate-00000000-000000" not in plan["backup"], plan


def test_dirty_guard():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        out = make_v1(root)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
        plan = run_json(out, "--feature", "auth", "--apply", expect_code=3)
        assert plan["status"] == "dirty_worktree", plan
        assert plan["reason"] == "dirty_worktree", plan
        assert (out / "planning-artifacts" / "D-02-requirements.md").exists()
        assert not (out / "features").exists()
        run(out, "--feature", "auth", "--apply", "--force")
        assert (out / "features" / "auth" / "planning-artifacts" / "D-02-requirements.md").exists()


def test_multi_feature_warning():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        (out / "planning-artifacts" / "D-02-billing.md").write_text(
            "REQ-101: billing\n", encoding="utf-8")
        plan = run_json(out, "--feature", "auth")
        assert "multi_feature_suspected" in plan["warnings"], plan
        assert plan["status"] == "ready", plan


def test_d06_reprefixed():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        d06 = (out / "features" / "auth" / "planning-artifacts" / "D-06-business-flow.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in d06 and "REQ-AUTH-002" in d06, d06
        assert "REQ-001" not in d06, "bare REQ-001 in D-06 should be re-prefixed"


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok: {name}")
    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
