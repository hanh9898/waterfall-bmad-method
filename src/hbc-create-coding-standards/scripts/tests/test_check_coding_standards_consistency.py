#!/usr/bin/env python3
"""Tests for check-coding-standards-consistency.py (B10-1 deviation / B10-2 spec-ref-leak)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-coding-standards-consistency.py")

# D-12 stating 4-space + snake_case (matches the SPACES_SNAKE code below).
D12_SPACES_SNAKE = """\
---
document_id: D-12
version: "1.0"
---

# Coding Standards

## Formatting
Thụt lề bằng 4 spaces, không dùng tabs.

## Naming Conventions
snake_case cho hàm và biến; PascalCase cho class.

## Machine-checkable Rules (Lint)
- Không nhúng spec id (REQ-/TC-/NFR-) vào code/test.
"""

# D-12 that states tabs + only camelCase — deviates from the SPACES_SNAKE code.
D12_TABS_CAMEL = """\
---
document_id: D-12
---

# Coding Standards

## Formatting
Indent with tabs.

## Naming Conventions
camelCase for functions.
"""

SPACES_SNAKE_CODE = """\
def compute_total(self):
    value = 0
    return value

def sync_period_line(self):
    other_value = 1
    return other_value

def _private_helper(self):
    inner = 2
    return inner

def reset_to_draft(self):
    flag = True
    return flag

def build_window(self):
    months = []
    return months
"""

# Code with REQ-/TC- spec ids embedded (B10-2).
LEAKY_CODE = """\
def handle(self):
    # implements REQ-016 and TC-005
    return 1

def other(self):
    \"\"\"covers NFR-002\"\"\"
    return 2
"""


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_clean_when_standards_match_code():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        code = tmp / "models"
        code.mkdir()
        write(code, "m.py", SPACES_SNAKE_CODE)
        result, rc = run([str(doc), "--code-dir", str(code)])
        assert result["deviations"] == [], result["deviations"]
        assert result["indent_actual"] == "spaces"
        assert result["naming_case_actual"] == "snake_case"
        assert result["grounded"] is True
        assert rc == 0


def test_indentation_deviation_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_TABS_CAMEL)  # states tabs
        code = tmp / "models"
        code.mkdir()
        write(code, "m.py", SPACES_SNAKE_CODE)  # actually spaces
        result, rc = run([str(doc), "--code-dir", str(code)])
        aspects = {dv["aspect"] for dv in result["deviations"]}
        assert "indentation" in aspects, result["deviations"]
        assert rc == 1
        assert any(i["type"] == "DEVIATION" for i in result["issues"])


def test_naming_case_deviation_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_TABS_CAMEL)  # names only camelCase
        code = tmp / "models"
        code.mkdir()
        write(code, "m.py", SPACES_SNAKE_CODE)  # snake_case funcs
        result, rc = run([str(doc), "--code-dir", str(code)])
        aspects = {dv["aspect"] for dv in result["deviations"]}
        assert "naming_case" in aspects, result["deviations"]


def test_spec_ref_leaks_reported():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        code = tmp / "models"
        code.mkdir()
        write(code, "leaky.py", LEAKY_CODE)
        result, rc = run([str(doc), "--code-dir", str(code)])
        refs = result["spec_ref_leaks"]
        assert "REQ-016" in refs and "TC-005" in refs and "NFR-002" in refs, refs
        assert result["spec_ref_leak_count"] >= 3
        assert rc == 1
        assert any(i["type"] == "SPEC_REF_LEAK" for i in result["issues"])


def test_advisory_when_no_code_dir():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        result, rc = run([str(doc)])
        assert rc == 0
        assert result["grounded"] is False
        assert result["deviations"] == []
        assert result["spec_ref_leaks"] == []
        assert result["valid"] is True


def test_honest_verdict_fields():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        code = tmp / "models"
        code.mkdir()
        write(code, "m.py", SPACES_SNAKE_CODE)
        result, _ = run([str(doc), "--code-dir", str(code)])
        assert result["semantic_review"] == "n/a"
        assert "structure_ok" in result
        assert result["not_checked"]


def test_code_under_skipped_ancestor_still_sampled():
    # Regression (CRITICAL, mirrors glossary): the skip set must be RELATIVE to
    # --code-dir, not the absolute path. A project under a 'build'/'migrations'
    # ANCESTOR must still be sampled — else deviation/leak checks false-green.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        models = tmp / "build" / "proj" / "models"  # 'build' is an ANCESTOR of code-dir
        models.mkdir(parents=True)
        write(models, "leaky.py", LEAKY_CODE)
        result, rc = run([str(doc), "--code-dir", str(models)])
        assert "REQ-016" in result["spec_ref_leaks"], result["spec_ref_leaks"]
        assert rc == 1


def test_vendored_subdir_under_code_dir_skipped():
    # node_modules/vendor UNDER code-dir must still be skipped (relative-parts match).
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        code = tmp / "code"
        (code / "node_modules").mkdir(parents=True)
        write(code / "node_modules", "vendored.py", LEAKY_CODE)
        result, rc = run([str(doc), "--code-dir", str(code)])
        assert result["spec_ref_leaks"] == [], result["spec_ref_leaks"]
        assert rc == 0


def test_nonexistent_code_dir_is_loud_error():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_SPACES_SNAKE)
        result, rc = run([str(doc), "--code-dir", str(tmp / "nope")])
        assert rc == 2
        assert "error" in result


def test_too_little_indent_signal_no_false_deviation():
    # Below the 5-line sample floor → style undecidable → no deviation asserted.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = write(tmp, "D-12.md", D12_TABS_CAMEL)
        code = tmp / "models"
        code.mkdir()
        write(code, "tiny.py", "x = 1\n")  # no indented lines
        result, rc = run([str(doc), "--code-dir", str(code)])
        indent_devs = [dv for dv in result["deviations"] if dv["aspect"] == "indentation"]
        assert indent_devs == [], indent_devs


def test_project_root_resolves_relative_paths():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write(tmp, "D-12.md", D12_SPACES_SNAKE)
        code = tmp / "models"
        code.mkdir()
        write(code, "m.py", SPACES_SNAKE_CODE)
        result, rc = run(["D-12.md", "--project-root", str(tmp), "--code-dir", "models"])
        assert result["grounded"] is True
        assert "error" not in result


def test_missing_document():
    result, rc = run(["/nonexistent/D-12.md"])
    assert rc == 2
    assert "error" in result


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
