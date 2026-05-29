#!/usr/bin/env python3
"""Tests for discover-planning-artifacts.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "discover-planning-artifacts.py")


def run_script(artifacts_dir: str, template_path: str, workspace: str | None = None) -> dict:
    cmd = [sys.executable, SCRIPT, artifacts_dir, "--template-path", template_path, "-o", "-"]
    if workspace:
        cmd.extend(["--workspace", workspace])
    result = subprocess.run(cmd, capture_output=True, text=True)
    for line in result.stdout.strip().split("\n"):
        if line.startswith("{"):
            return json.loads(line)
    return {}


def run_script_full(artifacts_dir: str, template_path: str, output_path: str, workspace: str | None = None) -> dict:
    cmd = [sys.executable, SCRIPT, artifacts_dir, "--template-path", template_path, "-o", output_path]
    if workspace:
        cmd.extend(["--workspace", workspace])
    subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(Path(output_path).read_text(encoding="utf-8"))


def test_empty_artifacts_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        tpl = Path(tmpdir) / "template.md"
        tpl.write_text("# Template\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(tpl), out)
        assert data["artifacts_dir_exists"] is True
        assert data["template_exists"] is True
        assert data["prd"] == []
        assert data["architecture"] == []


def test_template_missing_fatal():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(Path(tmpdir) / "nonexist.md"), out)
        assert data["fatal"] == "template_missing"
        assert data["template_exists"] is False


def test_discovers_prd_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        (arts / "prd-orders.md").write_text("# PRD\n", encoding="utf-8")
        (arts / "PRD-users.md").write_text("# PRD 2\n", encoding="utf-8")
        tpl = Path(tmpdir) / "template.md"
        tpl.write_text("# Template\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(tpl), out)
        assert len(data["prd"]) == 2


def test_discovers_architecture_docs():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        (arts / "architecture-v1.md").write_text("# Arch\n", encoding="utf-8")
        tpl = Path(tmpdir) / "template.md"
        tpl.write_text("# Template\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(tpl), out)
        assert len(data["architecture"]) == 1


def test_resume_state_fresh():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        ws = Path(tmpdir) / "workspace"
        ws.mkdir()
        tpl = Path(tmpdir) / "template.md"
        tpl.write_text("# Template\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(tpl), out, workspace=str(ws))
        assert data["resume_state"]["recommended_intent"] == "Fresh"
        assert data["resume_state"]["fresh_reason"] == "no_workspace"


def test_resume_state_update():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        ws = Path(tmpdir) / "workspace"
        ws.mkdir()
        primary = ws / "D-19-er-diagram.md"
        primary.write_text(
            '---\nstepsCompleted: ["stage-1", "stage-2", "stage-3", "stage-4", "stage-5"]\nlastStep: complete\nupdated: "2026-05-28"\n---\n# ER\n',
            encoding="utf-8",
        )
        tpl = Path(tmpdir) / "template.md"
        tpl.write_text("# Template\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(tpl), out, workspace=str(ws))
        assert data["resume_state"]["recommended_intent"] == "Update"


def test_resume_state_crashed():
    with tempfile.TemporaryDirectory() as tmpdir:
        arts = Path(tmpdir) / "artifacts"
        arts.mkdir()
        ws = Path(tmpdir) / "workspace"
        ws.mkdir()
        primary = ws / "D-19-er-diagram.md"
        primary.write_text(
            "---\nstepsCompleted: []\nlastStep: null\n---\n# ER\n",
            encoding="utf-8",
        )
        tpl = Path(tmpdir) / "template.md"
        tpl.write_text("# Template\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script_full(str(arts), str(tpl), out, workspace=str(ws))
        assert data["resume_state"]["recommended_intent"] == "Fresh"
        assert data["resume_state"]["fresh_reason"] == "crashed_no_progress"


if __name__ == "__main__":
    tests = [
        test_empty_artifacts_dir,
        test_template_missing_fatal,
        test_discovers_prd_files,
        test_discovers_architecture_docs,
        test_resume_state_fresh,
        test_resume_state_update,
        test_resume_state_crashed,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
