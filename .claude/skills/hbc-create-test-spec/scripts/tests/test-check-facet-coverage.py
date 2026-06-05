#!/usr/bin/env python3
"""Tests for check-facet-coverage.py (M-1)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-facet-coverage.py")

D27_PARTIAL = """\
# D-27

## Chi tiết test case (Detailed Test Cases)

### TC-001: Login via API
**REQ ID:** REQ-013
**Facets:** read, api

### TC-002: Issue key
**REQ ID:** REQ-013
**Facets:** write

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Tóm tắt | Test Cases | Facets |
|--------|---------|------------|--------|
| REQ-013 | Key mgmt | TC-001, TC-002 | read, write, admin |
"""

D27_FULL = D27_PARTIAL.replace(
    "### TC-002: Issue key\n**REQ ID:** REQ-013\n**Facets:** write",
    "### TC-002: Issue key\n**REQ ID:** REQ-013\n**Facets:** write\n\n"
    "### TC-003: Admin revoke\n**REQ ID:** REQ-013\n**Facets:** admin",
)

D27_NO_FACETS = """\
# D-27

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Tóm tắt | Test Cases |
|--------|---------|------------|
| REQ-001 | Login | TC-001 |
"""


def _w(body: str) -> str:
    d = tempfile.mkdtemp()
    p = Path(d) / "D-27.md"
    p.write_text(body, encoding="utf-8")
    return str(p)


def run(d27: str) -> tuple[dict, int]:
    r = subprocess.run([sys.executable, SCRIPT, "--d27", d27], capture_output=True, text=True)
    return json.loads(r.stdout), r.returncode


def test_uncovered_facet_detected():
    data, code = run(_w(D27_PARTIAL))
    # required {read,write,admin}; covered {read,api,write} → admin missing
    assert data["facet_covered"] is False
    assert data["uncovered_facets"]["REQ-013"] == ["admin"]
    assert code == 1


def test_all_facets_covered():
    data, code = run(_w(D27_FULL))
    assert data["facet_covered"] is True
    assert data["uncovered_facets"] == {}
    assert code == 0


def test_no_declared_facets_is_vacuously_covered():
    data, code = run(_w(D27_NO_FACETS))
    assert data["reqs_with_declared_facets"] == 0
    assert data["facet_covered"] is True
    assert code == 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
