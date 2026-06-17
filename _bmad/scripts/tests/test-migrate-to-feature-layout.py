#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for migrate-to-feature-layout.py.

Run: PYTHONUTF8=1 python _bmad/scripts/tests/test-migrate-to-feature-layout.py
Covers: dry-run plan JSON, shared-vs-per-feature routing, REQ reprefix (TC untouched),
8-col matrix rebuild, idempotency (already-v2 → nothing to migrate), backup + dirty guard.
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
    "| REQ-001 |  | Foo | foo.py | TC-001 | PASSED | 2026-01-01 |\n"
    "| REQ-SHARED-009 |  | Bar | bar.py | TC-009 |  | 2026-01-01 |\n"
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
    """Build a v1 (flat) output tree under root/_bmad-output."""
    out = root / "_bmad-output"
    pa = out / "planning-artifacts"
    pa.mkdir(parents=True)
    (pa / "D-02-requirements.md").write_text(D02, encoding="utf-8")
    (pa / "D-26-test-plan.md").write_text(D26, encoding="utf-8")
    (pa / "D-27-test-spec.md").write_text(D27, encoding="utf-8")
    (pa / "D-12-coding-standards.md").write_text("# Coding Standards\n", encoding="utf-8")
    (pa / "D-03-glossary.md").write_text("# Glossary\n", encoding="utf-8")
    (pa / "D-19-erd.md").write_text("# ERD\n", encoding="utf-8")
    impl = out / "implementation-artifacts"
    impl.mkdir(parents=True)
    (impl / "task-breakdown.md").write_text("# Tasks\n", encoding="utf-8")
    gates = out / "gates"
    gates.mkdir(parents=True)
    (gates / "phase-1-gate.md").write_text("# Gate\n", encoding="utf-8")
    tr = out / "traceability"
    tr.mkdir(parents=True)
    (tr / "matrix.md").write_text(LEGACY_MATRIX, encoding="utf-8")
    return out


def test_dryrun_plan_json():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--reprefix")
        assert plan["status"] == "ready", plan
        assert plan["feature"] == "auth"
        assert plan["matrix_rebuild"] is True, plan
        assert plan["moves"], "expected moves"
        keys = set(k for k in plan.keys())
        for required in ("status", "feature", "moves", "reprefix", "matrix_rebuild", "warnings"):
            assert required in keys, f"missing {required}"
        # dry-run must not write — source files still present.
        assert (out / "planning-artifacts" / "D-02-requirements.md").exists()
        assert not (out / "features").exists()
        print("ok: dry-run plan JSON + no writes")


def test_shared_vs_perfeature_routing():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth")
        dsts = {Path(m["dst"]).as_posix() for m in plan["moves"]}
        # shared deliverables → shared/
        assert any("shared/coding-standards/D-12" in x for x in dsts), dsts
        assert any("shared/glossary/D-03" in x for x in dsts), dsts
        assert any("shared/erd/D-19" in x for x in dsts), dsts
        # per-feature deliverables → features/auth/
        assert any("features/auth/planning-artifacts/D-02" in x for x in dsts), dsts
        assert any("features/auth/planning-artifacts/D-26" in x for x in dsts), dsts
        assert any("features/auth/traceability/matrix.md" in x for x in dsts), dsts
        assert any("features/auth/implementation-artifacts/task-breakdown" in x for x in dsts), dsts
        assert any("features/auth/gates/phase-1-gate" in x for x in dsts), dsts
        print("ok: shared vs per-feature routing")


def test_req_reprefix_tc_untouched():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        plan = run_json(out, "--feature", "auth", "--reprefix")
        # plan map: REQ namespaced, TC absent.
        assert plan["reprefix"].get("REQ-001") == "REQ-AUTH-001", plan["reprefix"]
        assert plan["reprefix"].get("REQ-002") == "REQ-AUTH-002", plan["reprefix"]
        assert all(not k.startswith("TC-") for k in plan["reprefix"]), plan["reprefix"]
        # apply and check actual file content.
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        d02 = (out / "features" / "auth" / "planning-artifacts" / "D-02-requirements.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in d02 and "REQ-AUTH-002" in d02, d02
        assert "REQ-001:" not in d02, "bare REQ should be gone"
        # TC ids must be untouched.
        assert "TC-001" in d02 and "TC-AUTH-001" not in d02, d02
        d27 = (out / "features" / "auth" / "planning-artifacts" / "D-27-test-spec.md").read_text(encoding="utf-8")
        assert "REQ-AUTH-001" in d27, d27
        assert "TC-001" in d27 and "TC-AUTH-001" not in d27, d27
        print("ok: REQ reprefix across D-02/D-26/D-27, TC untouched")


def test_matrix_rebuild_8col():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        mx = (out / "features" / "auth" / "traceability" / "matrix.md").read_text(encoding="utf-8")
        lines = [l for l in mx.splitlines() if l.strip().startswith("|")]
        header = [c.strip().lower() for c in lines[0].strip("|").split("|")]
        assert header == ["feature", "req_id", "story_id", "design_ref", "code_ref",
                          "test_ref", "gate_status", "timestamp"], header
        # data rows have 8 cells; REQ-SHARED row → feature=shared, normal → feature slug.
        body = [l for l in lines[2:]]
        cells0 = [c.strip() for c in body[0].strip("|").split("|")]
        assert len(cells0) == 8, cells0
        assert cells0[0] == "auth", cells0
        assert cells0[1] == "REQ-AUTH-001", cells0
        shared_row = [l for l in body if "SHARED" in l][0]
        scells = [c.strip() for c in shared_row.strip("|").split("|")]
        assert scells[0] == "shared", scells
        print("ok: matrix rebuilt to 8-col with feature/shared routing")


def test_idempotent_already_v2():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        run(out, "--feature", "auth", "--reprefix", "--apply", "--force")
        # Re-run on the now-migrated tree (no flat dirs left) → nothing_to_migrate.
        plan = run_json(out, "--feature", "auth", "--reprefix")
        assert plan["status"] == "nothing_to_migrate", plan
        assert plan["moves"] == [], plan
        # And a fresh empty output dir.
        with tempfile.TemporaryDirectory() as d2:
            empty = Path(d2) / "_bmad-output"
            empty.mkdir()
            plan2 = run_json(empty)
            assert plan2["status"] == "nothing_to_migrate", plan2
        print("ok: idempotent — already-v2 / empty → nothing_to_migrate")


def test_backup_created():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        run(out, "--feature", "auth", "--apply", "--force", "--timestamp", "20260617-101010")
        archive = out / ".archive" / "migrate-20260617-101010"
        assert archive.is_dir(), "archive folder must exist"
        assert (archive / "planning-artifacts" / "D-02-requirements.md").exists(), "legacy backed up"
        assert (archive / "traceability" / "matrix.md").exists()
        print("ok: backup copied to .archive/migrate-<ts>/")


def test_dirty_guard():
    # Make a git repo with an uncommitted change, then refuse without --force.
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        out = make_v1(root)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
        # Uncommitted files present → dirty.
        plan = run_json(out, "--feature", "auth", "--apply", expect_code=3)
        assert plan["status"] == "dirty_worktree", plan
        # files NOT moved.
        assert (out / "planning-artifacts" / "D-02-requirements.md").exists()
        assert not (out / "features").exists()
        # --force overrides.
        run(out, "--feature", "auth", "--apply", "--force")
        assert (out / "features" / "auth" / "planning-artifacts" / "D-02-requirements.md").exists()
        print("ok: dirty guard refuses without --force, proceeds with --force")


def test_multi_feature_warning():
    with tempfile.TemporaryDirectory() as d:
        out = make_v1(Path(d))
        # Add a second D-02 → multi-feature heuristic.
        (out / "planning-artifacts" / "D-02-billing.md").write_text(
            "REQ-101: billing\n", encoding="utf-8")
        plan = run_json(out, "--feature", "auth")
        assert "multi_feature_suspected" in plan["warnings"], plan
        assert plan["status"] == "ready", plan  # still proceeds with single --feature
        print("ok: multi_feature_suspected warning, still proceeds")


def main():
    test_dryrun_plan_json()
    test_shared_vs_perfeature_routing()
    test_req_reprefix_tc_untouched()
    test_matrix_rebuild_8col()
    test_idempotent_already_v2()
    test_backup_created()
    test_dirty_guard()
    test_multi_feature_warning()
    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
