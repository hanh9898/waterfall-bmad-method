#!/usr/bin/env python3
"""Tests for check-readiness.py (P-1)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-readiness.py")

D02 = """\
# D-02

## Yêu cầu chức năng

| REQ ID | Mô tả |
|--------|-------|
| REQ-001 | Login |
| REQ-002 | Order |
"""


def _w(d: Path, name: str, body: str) -> str:
    p = d / name
    p.write_text(body, encoding="utf-8")
    return str(p)


def run(args: list[str]) -> tuple[dict, int]:
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return json.loads(r.stdout), r.returncode


def test_ready_all_covered():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", "TC-001 covers REQ-001\nTC-002 covers REQ-002\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["ready"] is True
        assert data["uncovered_by_test"] == []
        assert data["passed"] is True
        assert code == 0


def test_uncovered_by_test():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", "TC-001 covers REQ-001\n")  # REQ-002 missing
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["ready"] is False
        assert data["uncovered_by_test"] == ["REQ-002"]
        assert code == 1


def test_orphan_downstream():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", "REQ-001 REQ-002 REQ-099\n")  # REQ-099 not in D-02
        data, code = run(["--d02", d02, "--d27", d27])
        assert "REQ-099" in data["orphan_reqs_downstream"]
        assert data["ready"] is False


def test_matrix_missing_req():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        matrix = _w(d, "matrix.md", "| req_id |\n|---|\n| REQ-001 |\n")  # REQ-002 missing
        data, code = run(["--d02", d02, "--matrix", matrix])
        assert data["missing_from_matrix"] == ["REQ-002"]
        assert data["ready"] is False


def test_prose_req_in_d02_not_counted_as_defined():
    # D-02 prose mentions REQ-900 outside the functional table → not "defined"
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", "## Giả định\nREQ-900 sau.\n\n" + D02)
        d27 = _w(d, "D-27.md", "REQ-001 REQ-002\n")  # does NOT cover REQ-900
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["d02_req_count"] == 2  # only REQ-001, REQ-002
        assert data["ready"] is True       # REQ-900 was never "defined"


def test_d02_missing_file_exit_2():
    r = subprocess.run([sys.executable, SCRIPT, "--d02", "/nope/D-02.md"], capture_output=True, text=True)
    assert r.returncode == 2
    assert "error" in json.loads(r.stdout)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
