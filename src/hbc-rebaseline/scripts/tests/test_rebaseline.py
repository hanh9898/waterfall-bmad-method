#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for rebaseline.py (TA.7 cross-feature blast-radius engine).

Run: python -m pytest src/hbc-rebaseline -q

Covers: blast-radius rollup (shared model hits multiple features), no-false-positive
(feature-owned model hits only its feature), shared-candidate discovery (>=2 features),
downstream rollup ordering, code-drift flag, dry-run vs apply, idempotent apply,
None-safety / determinism, and the CLI contract (JSON shape, exit codes). Invokes the
engine via subprocess the way SKILL.md will, and imports it directly for unit cases.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "rebaseline.py"

# Import the engine directly for unit-level cases (kernel on path via the script's own
# bootstrap — replicate it here).
sys.path.insert(0, str(SCRIPT.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "hbc-shared" / "lib"))
import rebaseline as rb  # noqa: E402


# --- fixture builder: a tiny two-feature corpus with a shared core model ---------

def _feature(root: Path, name: str, model_name: str, *, shares: str | None,
             with_downstream=True):
    """Write one feature dir: code/models/<m>.py + D-19 + (optional) matrix/tb/gate."""
    fdir = root / name
    (fdir / "code" / "models").mkdir(parents=True, exist_ok=True)
    (fdir / "planning").mkdir(parents=True, exist_ok=True)
    rel = f"    parent_id = fields.Many2one('{shares}')\n" if shares else ""
    (fdir / "code" / "models" / f"{name}.py").write_text(
        "from odoo import fields, models\n\n\n"
        f"class M(models.Model):\n    _name = '{model_name}'\n{rel}",
        encoding="utf-8")
    phys = f"- **Physical name**: `{model_name}`\n"
    if shares:
        phys += f"- relates to `{shares}`\n"
    (fdir / "planning" / "D-02-x.md").write_text(
        f"---\nversion: \"1.0\"\n---\n# Req\nREQ-{name.upper()}-001: thing.\n", encoding="utf-8")
    (fdir / "planning" / "D-19-er.md").write_text(
        f"---\ndocument_id: D-19\nversion: \"1.0\"\n---\n# DB\n### {model_name}\n{phys}",
        encoding="utf-8")
    if with_downstream:
        (fdir / "traceability").mkdir(exist_ok=True)
        (fdir / "traceability" / "matrix.md").write_text(
            "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|---|---|---|---|---|---|---|---|\n"
            f"| {name} | REQ-{name.upper()}-001 |  | {model_name} | x.py | TC-001 | PASS | 2026-01-01 |\n",
            encoding="utf-8")
        (fdir / "implementation").mkdir(exist_ok=True)
        (fdir / "implementation" / "task-breakdown.md").write_text(
            f"---\nsources: D-02 v1.0\n---\n# Tasks\n- TASK-1\n", encoding="utf-8")
        (fdir / "gates").mkdir(exist_ok=True)
        (fdir / "gates" / "phase-3-gate.md").write_text(
            "# Gate\nEvaluated against D-02 v1.0.\nPASS\n", encoding="utf-8")


def _corpus(root: Path):
    """Two features sharing core model `project.project`; each also owns its own model."""
    _feature(root, "feature-a", "app.alpha", shares="project.project")
    _feature(root, "feature-b", "app.beta", shares="project.project")


def run_json(*args, expect_code=0):
    p = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == expect_code, f"exit {p.returncode}\nSTDOUT:{p.stdout}\nSTDERR:{p.stderr}"
    return json.loads(p.stdout) if p.stdout.strip() else {}


# --- blast-radius (the engine's core) --------------------------------------------

def test_shared_model_hits_all_referencing_features():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        out = run_json("--root", str(root), "--changed", "project.project", "--change-id", "bc1")
        assert out["affected_features"] == ["feature-a", "feature-b"]
        assert out["changed_node"] == "project.project"
        assert out["warnings"] == []  # genuinely cross-feature


def test_feature_owned_model_hits_only_its_feature():
    """No false positive: a model only one feature touches does not flag the other."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        out = run_json("--root", str(root), "--changed", "app.alpha", "--change-id", "bc2")
        assert out["affected_features"] == ["feature-a"]
        assert out["owners"] == ["feature-a"]
        assert "not_cross_feature_shared" in out["warnings"]


def test_unreferenced_model_yields_empty_radius():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        out = run_json("--root", str(root), "--changed", "does.not.exist", "--change-id", "bc3")
        assert out["affected_features"] == []
        assert "empty_blast_radius" in out["warnings"]


def test_rollup_downstream_artifacts_in_order():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        out = run_json("--root", str(root), "--changed", "project.project", "--change-id", "bc4")
        row = next(r for r in out["blast_radius"] if r["feature"] == "feature-a")
        assert row["stale_artifacts"] == ["D-19", "matrix", "task-breakdown", "gate"]
        assert row["verdict"] == "rebaseline"
        assert row["code_references_changed"] is True


def test_feature_without_downstream_rolls_up_only_present_nodes():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _feature(root, "feature-a", "app.alpha", shares="project.project")
        _feature(root, "feature-b", "app.beta", shares="project.project", with_downstream=False)
        out = run_json("--root", str(root), "--changed", "project.project", "--change-id", "bc5")
        row = next(r for r in out["blast_radius"] if r["feature"] == "feature-b")
        assert row["stale_artifacts"] == ["D-19"]  # no matrix/tb/gate authored yet


# --- shared-candidate discovery ---------------------------------------------------

def test_discovery_lists_shared_candidates():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        out = run_json("--root", str(root))  # no --changed
        assert "project.project" in out["shared_candidates"]
        assert out["shared_candidates"]["project.project"] == ["feature-a", "feature-b"]
        # feature-owned models are NOT shared candidates (only one referencer)
        assert "app.alpha" not in out["shared_candidates"]


# --- dry-run vs apply + idempotency ----------------------------------------------

def test_dry_run_writes_nothing():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        out = run_json("--root", str(root), "--changed", "project.project", "--change-id", "bc6")
        assert out["applied"] is False
        assert not (root.parent / "baseline-change").exists()


def test_apply_writes_envelope_then_idempotent():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "features"
        root.mkdir()
        _corpus(root)
        outdir = Path(d) / "out"
        first = run_json("--root", str(root), "--changed", "project.project",
                         "--change-id", "bc7", "--apply", "--out-root", str(outdir))
        assert first["applied"] is True and first["skipped"] is False
        env = outdir / "baseline-change" / "bc7"
        assert (env / "rebaseline-plan.json").is_file()
        assert (env / ".decision-log.md").is_file()
        # re-apply identical plan → skipped, not written twice
        second = run_json("--root", str(root), "--changed", "project.project",
                          "--change-id", "bc7", "--apply", "--out-root", str(outdir))
        assert second["applied"] is True and second["skipped"] is True


def test_apply_rewrites_when_plan_changed():
    """Idempotency is plan-aware: a DIFFERENT plan under the same change-id is written,
    not skipped (e.g. the affected set changed since the envelope was first recorded)."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "features"
        root.mkdir()
        _corpus(root)
        outdir = Path(d) / "out"
        run_json("--root", str(root), "--changed", "project.project",
                 "--change-id", "bc9", "--apply", "--out-root", str(outdir))
        # different changed_node under same id → not the same plan → must write
        second = run_json("--root", str(root), "--changed", "app.alpha",
                          "--change-id", "bc9", "--apply", "--out-root", str(outdir))
        assert second["skipped"] is False
        recorded = json.loads((outdir / "baseline-change" / "bc9" / "rebaseline-plan.json")
                              .read_text(encoding="utf-8"))
        assert recorded["changed_node"] == "app.alpha"


def test_determinism_identical_input_identical_output():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        _corpus(root)
        a = run_json("--root", str(root), "--changed", "project.project", "--change-id", "bc8")
        b = run_json("--root", str(root), "--changed", "project.project", "--change-id", "bc8")
        assert a == b


# --- CLI contract / error handling -----------------------------------------------

def test_missing_root_exits_2():
    run_json("--root", "/no/such/dir", "--changed", "x.y", expect_code=2)


def test_empty_root_exits_2():
    with tempfile.TemporaryDirectory() as d:
        run_json("--root", d, "--changed", "x.y", expect_code=2)


# --- unit-level None-safety -------------------------------------------------------

def test_model_tokens_none_safe_on_empty_graph():
    from hbc_buildgraph import BuildGraph
    g = BuildGraph()
    assert rb.model_tokens(g) == set()
    assert rb.owned_tokens(g) == set()


def test_proves_blast_radius_on_clean_corpus():
    """End-to-end proof on the committed clean corpus (read-only; never mutated)."""
    corpus = Path(__file__).resolve().parents[4] / "process-review" / "spikes" / "ta0" / "corpus-clean"
    if not corpus.is_dir():
        import pytest
        pytest.skip("clean corpus not present")
    out = run_json("--root", str(corpus), "--changed", "project.project", "--change-id", "bc-clean")
    assert out["affected_features"] == ["project-tag-filter", "resource-plan-billable"]
