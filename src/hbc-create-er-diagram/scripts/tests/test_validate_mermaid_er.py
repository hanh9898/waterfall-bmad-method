#!/usr/bin/env python3
"""Tests for validate-mermaid-er.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-mermaid-er.py")


def run_script(d19_content: str, expected_entities: str | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(d19_content, encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        cmd = [sys.executable, SCRIPT, str(d19), "-o", out]
        if expected_entities:
            cmd.extend(["--expected-entities", expected_entities])
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(Path(out).read_text(encoding="utf-8"))


def test_valid_diagram():
    content = """# ER Diagram

```mermaid
erDiagram
  Users {
    int id PK
    string name
  }
  Orders {
    int id PK
    int status
  }
  Users ||--o{ Orders : places
```
"""
    data = run_script(content)
    assert data["passed"] is True
    assert len(data["issues"]) == 0


def test_orphan_entity():
    content = """# ER Diagram

```mermaid
erDiagram
  Users {
    int id PK
  }
  Orphan {
    int id PK
  }
  Orders {
    int id PK
  }
  Users ||--o{ Orders : places
```
"""
    data = run_script(content)
    orphan_issues = [i for i in data["issues"] if i.get("kind") == "orphan_entity" and i.get("name") == "Orphan"]
    assert len(orphan_issues) == 1


def test_missing_expected_entity():
    content = """# ER Diagram

```mermaid
erDiagram
  Users {
    int id PK
  }
```
"""
    data = run_script(content, expected_entities="Users,Orders")
    assert data["passed"] is False
    missing = [i for i in data["issues"] if i.get("kind") == "missing_expected_entity" and i.get("name") == "Orders"]
    assert len(missing) == 1


def test_no_mermaid_blocks():
    content = "# ER Diagram\n\nNo mermaid blocks here.\n"
    data = run_script(content)
    assert data["passed"] is False
    no_block = [i for i in data["issues"] if i.get("kind") == "no_er_blocks"]
    assert len(no_block) == 1


def test_empty_file():
    data = run_script("")
    assert data["passed"] is False


def test_auto_fixable_flag_present():
    content = """# ER Diagram

```mermaid
erDiagram
  Users {
    int id PK
  }
  Orphan {
    int id PK
  }
  Users ||--o{ Users : self
```
"""
    data = run_script(content)
    for issue in data["issues"]:
        assert "auto_fixable" in issue


def test_undeclared_entity_in_relationship():
    content = """# ER Diagram

```mermaid
erDiagram
  Users {
    int id PK
  }
  Users ||--o{ Orders : places
```
"""
    data = run_script(content)
    undeclared = [i for i in data["issues"] if i.get("kind") == "undeclared_entity" and i.get("name") == "Orders"]
    assert len(undeclared) == 1
    assert undeclared[0]["auto_fixable"] is True


if __name__ == "__main__":
    tests = [
        test_valid_diagram,
        test_orphan_entity,
        test_missing_expected_entity,
        test_no_mermaid_blocks,
        test_empty_file,
        test_auto_fixable_flag_present,
        test_undeclared_entity_in_relationship,
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
