"""Tests for scan-project-init.py — invoked the way SKILL.md will (subprocess)."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scan-project-init.py"
CATALOG = (Path(__file__).resolve().parents[3]
           / "hbc-shared" / "references" / "deliverable-catalog.yaml")


def run(project_root, output_folder, **kw):
    cmd = [sys.executable, str(SCRIPT),
           "--project-root", str(project_root),
           "--output-folder", str(output_folder),
           "--catalog-path", str(CATALOG)]
    for k, v in kw.items():
        cmd += [f"--{k.replace('_', '-')}", str(v)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def write(p: Path, content="x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_greenfield_empty(tmp_path):
    out = tmp_path / "_bmad-output"
    out.mkdir()
    r = run(tmp_path, out)
    assert r["project_type"] == "greenfield"
    assert r["is_rerun"] is False
    assert set(r["missing"]) == {"D-12", "D-03", "D-19", "D-21", "constitution"}
    assert r["present"] == []
    assert r["legacy_v1_layout"] is False


def test_brownfield_detection(tmp_path):
    write(tmp_path / "src" / "app.py", "print('hi')")
    out = tmp_path / "_bmad-output"
    out.mkdir()
    r = run(tmp_path, out)
    assert r["project_type"] == "brownfield"


def test_tooling_dirs_are_not_source(tmp_path):
    # only tooling/output dirs -> still greenfield
    write(tmp_path / "_bmad" / "config.py", "x = 1")
    write(tmp_path / "docs" / "guide.md", "doc")
    out = tmp_path / "_bmad-output"
    out.mkdir()
    r = run(tmp_path, out)
    assert r["project_type"] == "greenfield"


def test_rerun_present_and_drift(tmp_path):
    out = tmp_path / "_bmad-output"
    # constitution present but incomplete -> drift signal
    write(out / "shared" / "constitution.md",
          "---\nversion: \"1.0\"\nlastStep: \"\"\n---\n# c")
    write(out / "shared" / "coding-standards" / "D-12-x.md",
          "---\nlastStep: complete\n---\n# d12")
    r = run(tmp_path, out)
    assert r["is_rerun"] is True
    assert "constitution" in r["present"]
    assert "D-12" in r["present"]
    signals = {d["deliverable"] for d in r["drift"]}
    assert "constitution" in signals  # incomplete constitution flagged


def test_legacy_v1_layout(tmp_path):
    out = tmp_path / "_bmad-output"
    write(out / "planning-artifacts" / "D-02-x.md", "old")
    r = run(tmp_path, out)
    assert r["legacy_v1_layout"] is True


def test_legacy_false_when_features_dir(tmp_path):
    out = tmp_path / "_bmad-output"
    write(out / "planning-artifacts" / "D-02-x.md", "old")
    (out / "features").mkdir(parents=True)
    r = run(tmp_path, out)
    assert r["legacy_v1_layout"] is False


def test_catalog_loaded(tmp_path):
    out = tmp_path / "_bmad-output"
    out.mkdir()
    r = run(tmp_path, out)
    cat = r["catalog"]
    assert cat["loaded"] is True
    ids = {d["id"] for d in cat["deliverables"]}
    # canonical Phase-0 + key per-feature ids present
    assert {"D-03", "D-12", "D-19", "D-21"}.issubset(ids)
    assert any(f.startswith("has-") for f in cat["facets"])


def test_project_context_present(tmp_path):
    write(tmp_path / "project-context.md", "# context")
    out = tmp_path / "_bmad-output"
    out.mkdir()
    r = run(tmp_path, out)
    assert r["project_context"] == "present"
    assert r["project_context_path"]


def test_documented_knowledge(tmp_path):
    write(tmp_path / "docs" / "index.md", "# index")
    out = tmp_path / "_bmad-output"
    out.mkdir()
    r = run(tmp_path, out, project_knowledge=str(tmp_path / "docs"))
    assert r["documented"] is True
