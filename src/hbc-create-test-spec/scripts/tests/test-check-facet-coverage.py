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


D27_TODO = """\
# D-27

## Chi tiết test case (Detailed Test Cases)

### TC-001: Login
**REQ ID:** REQ-013
**Facets:** TODO

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Tóm tắt | Test Cases | Facets |
|--------|---------|------------|--------|
| REQ-013 | Key mgmt | TC-001 | TODO |
"""


def _w(body: str) -> str:
    d = tempfile.mkdtemp()
    p = Path(d) / "D-27.md"
    p.write_text(body, encoding="utf-8")
    return str(p)


def run(d27: str) -> tuple[dict, int]:
    r = subprocess.run([sys.executable, SCRIPT, "--d27", d27], capture_output=True, text=True, encoding="utf-8")
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
    # honest-verdict contract (S-3).
    assert data["structure_ok"] is True
    assert data["semantic_review"] == "n/a"
    assert data["passed"] is True
    assert code == 0


def test_no_declared_facets_is_vacuously_covered():
    data, code = run(_w(D27_NO_FACETS))
    assert data["reqs_with_declared_facets"] == 0
    assert data["facet_covered"] is True
    assert data["uncovered_facets"] == {}
    # #2: a vacuous green must be transparent so the P2-08 reviewer doesn't read
    # "nothing measured" as "all good".
    assert "note" in data
    assert "vacuous" in data["note"].lower()
    assert code == 0


def test_placeholder_todo_fails_loudly():
    # Bug F1: a "TODO" required facet and a "TODO" covered facet cancelled out and
    # the REQ reported full coverage. Placeholder facets must fail loudly.
    data, code = run(_w(D27_TODO))
    assert data["facet_covered"] is False
    assert data.get("placeholder_facets")
    assert code == 1


def test_d27_unreadable_exit_2():
    # GAP-5: missing/unreadable D-27 → JSON error + exit 2.
    r = subprocess.run([sys.executable, SCRIPT, "--d27", "/nope/D-27.md"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2
    data = json.loads(r.stdout)
    assert "error" in data
    assert data["facet_covered"] is False


# --- P2: pipe-separated facets in a TC block parse correctly ---
D27_PIPE = """\
# D-27

## Chi tiết test case

### TC-001: Read
**REQ ID:** REQ-013
**Facets:** read | api

### TC-002: Write
**REQ ID:** REQ-013
**Facets:** write | admin

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Tóm tắt | Test Cases | Facets |
|--------|---------|------------|--------|
| REQ-013 | Key mgmt | TC-001, TC-002 | read, write, admin |
"""


def test_pipe_separated_facets_parse():
    data, code = run(_w(D27_PIPE))
    # covered = {read, api, write, admin} ⊇ required {read, write, admin}
    assert data["facet_covered"] is True
    assert data["uncovered_facets"] == {}  # no raw "read | api" garbage token left
    assert code == 0


# --- D3: one TC covering multiple REQ ids credits its facets to each ---
D27_MULTI_REQ = """\
# D-27

## Chi tiết test case

### TC-001: Shared
**REQ ID:** REQ-001, REQ-002
**Facets:** read, write

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Tóm tắt | Test Cases | Facets |
|--------|---------|------------|--------|
| REQ-001 | A | TC-001 | read, write |
| REQ-002 | B | TC-001 | read, write |
"""


def test_multi_req_tc_credits_all_reqs():
    data, code = run(_w(D27_MULTI_REQ))
    assert data["facet_covered"] is True
    assert data["uncovered_facets"] == {}
    assert code == 0


# --- D1: required facets are UNIONED across D-02 and D-27 (no source shadows) ---
D02_PARTIAL_FACETS = """\
# D-02

## Yêu cầu chức năng

| REQ ID | Mô tả | Facets |
|--------|-------|--------|
| REQ-001 | A | admin |
| REQ-002 | B |  |
"""

D27_FOR_UNION = """\
# D-27

## Chi tiết test case

### TC-001: A read
**REQ ID:** REQ-001
**Facets:** read

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Tóm tắt | Test Cases | Facets |
|--------|---------|------------|--------|
| REQ-001 | A | TC-001 | read |
"""


def test_union_d02_does_not_shadow_d27():
    # D-02 declares only REQ-001:admin; D-27 matrix declares REQ-001:read.
    # Union → required REQ-001 = {admin, read}; covered = {read} → admin missing.
    # (Old "first source wins" would have dropped D-27's 'read' entirely.)
    d = tempfile.mkdtemp()
    d02 = Path(d) / "D-02.md"; d02.write_text(D02_PARTIAL_FACETS, encoding="utf-8")
    d27 = Path(d) / "D-27.md"; d27.write_text(D27_FOR_UNION, encoding="utf-8")
    r = subprocess.run([sys.executable, SCRIPT, "--d27", str(d27), "--d02", str(d02)],
                       capture_output=True, text=True, encoding="utf-8")
    data = json.loads(r.stdout)
    assert data["uncovered_facets"]["REQ-001"] == ["admin"]
    assert data["facet_covered"] is False
    assert r.returncode == 1


# --- GAP-11: union symmetric direction — D-27 matrix declares the uncovered facet ---
D02_NO_FACET_COL = """\
# D-02

## Yêu cầu chức năng

| REQ ID | Mô tả |
|--------|-------|
| REQ-001 | Login |
"""

D27_MATRIX_UNIQUE_FACET = """\
# D-27

## Chi tiết test case

### TC-001: A read
**REQ ID:** REQ-001
**Facets:** read

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Test Cases | Facets |
|--------|------------|--------|
| REQ-001 | TC-001 | read, write |
"""


def test_union_d27_matrix_contributes_uncovered_facet():
    # D-02 has no Facets column; D-27 matrix uniquely declares write → uncovered.
    d = tempfile.mkdtemp()
    d02 = Path(d) / "D-02.md"; d02.write_text(D02_NO_FACET_COL, encoding="utf-8")
    d27 = Path(d) / "D-27.md"; d27.write_text(D27_MATRIX_UNIQUE_FACET, encoding="utf-8")
    r = subprocess.run([sys.executable, SCRIPT, "--d27", str(d27), "--d02", str(d02)],
                       capture_output=True, text=True, encoding="utf-8")
    data = json.loads(r.stdout)
    assert data["uncovered_facets"]["REQ-001"] == ["write"]
    assert r.returncode == 1


# --- P4: REQ column resolves correctly even when "Requirement" column comes first ---
D27_REORDERED_HEADER = """\
# D-27

## Chi tiết test case

### TC-001: A
**REQ ID:** REQ-001
**Facets:** read

## Ma trận bao phủ (Coverage Matrix)

| Requirement Summary | REQ ID | Test Cases | Facets |
|---------------------|--------|------------|--------|
| Login flow | REQ-001 | TC-001 | read, write |
"""


def test_col_index_prefers_req_id_over_requirement_summary():
    # P4: "Requirement Summary" precedes "REQ ID"; word-boundary match must pick
    # the REQ ID column, so REQ-001 is found and 'write' shows as uncovered.
    data, code = run(_w(D27_REORDERED_HEADER))
    assert data["uncovered_facets"] == {"REQ-001": ["write"]}
    assert code == 1


# --- P4 regression: a noisy column with a bounded "req." token must NOT win ---
D27_NOISY_REQ_HEADER = """\
# D-27

## Chi tiết test case

### TC-001: A
**REQ ID:** REQ-001
**Facets:** read

## Ma trận bao phủ (Coverage Matrix)

| Notes about req. | REQ ID | Test Cases | Facets |
|------------------|--------|------------|--------|
| see ticket | REQ-001 | TC-001 | read, write |
"""


def test_col_index_ignores_noisy_bounded_req_token():
    # Old first-boundary-match picked the "Notes about req." column (index 0) and
    # silently dropped the REQ → false green. Scoring must pick the real REQ ID col.
    data, code = run(_w(D27_NOISY_REQ_HEADER))
    assert data["uncovered_facets"] == {"REQ-001": ["write"]}
    assert code == 1


# --- BUG1: score-1 TIE must be broken by data (which column holds REQ ids) ---
D27_TIE_REQ_HEADER = """\
# D-27

## Chi tiết test case

### TC-001: A
**REQ ID:** REQ-005
**Facets:** read

## Ma trận bao phủ (Coverage Matrix)

| Acceptance Requirement | Requirements | Facets |
|------------------------|--------------|--------|
| n/a | REQ-005 | read, write, api |
"""


def test_req_col_tie_broken_by_data():
    # Both "Acceptance Requirement" and "Requirements" score 1 (substring) for
    # "req". First-wins would pick the "n/a" column → REQ-005 dropped → false green.
    # Data-aware tie-break must pick the column actually holding REQ-005.
    data, code = run(_w(D27_TIE_REQ_HEADER))
    assert data["reqs_with_declared_facets"] == 1
    assert sorted(data["uncovered_facets"]["REQ-005"]) == ["api", "write"]
    assert code == 1


# --- BUG2: a combined "REQ Facets" header must not map req and facet to one col ---
D27_COMBINED_HEADER = """\
# D-27

## Ma trận bao phủ (Coverage Matrix)

| REQ Facets | Test Cases |
|------------|------------|
| REQ-001 read, write | TC-001 |
"""


def test_combined_req_facets_header_no_fabricated_facets():
    # ci_fac claims the "REQ Facets" column; ci_req is then resolved excluding it →
    # None → source skipped, rather than fabricating facets like "req-001 read".
    data, code = run(_w(D27_COMBINED_HEADER))
    assert data["reqs_with_declared_facets"] == 0
    assert data["uncovered_facets"] == {}  # no fabricated facet tokens at all
    assert code == 0


# --- HTML comment in a MATRIX cell must not leak into required facets (P2, required side) ---
D27_MATRIX_COMMENT = """\
# D-27

## Chi tiết test case

### TC-001: A
**REQ ID:** REQ-001
**Facets:** read

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Test Cases | Facets |
|--------|------------|--------|
| REQ-001 | TC-001 | read <!-- confirm w/ BA --> |
"""


def test_matrix_cell_html_comment_not_leaked_as_facet():
    # The reviewer note must be stripped so required facets = {read}, fully covered.
    # Before the fix it leaked tokens like "read <!-- confirm w" / "ba -->" → false RED.
    data, code = run(_w(D27_MATRIX_COMMENT))
    assert data["facet_covered"] is True
    assert data["uncovered_facets"] == {}
    assert code == 0


# --- #7: #### TC heading + fenced example handled in covered_facets ---
D27_H4_AND_FENCE = """\
# D-27

## Chi tiết test case

```
### TC-000: example (must be ignored)
**REQ ID:** REQ-013
**Facets:** read, write, admin
```

#### TC-001: read
**REQ ID:** REQ-013
**Facets:** read, write, admin

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Test Cases | Facets |
|--------|------------|--------|
| REQ-013 | TC-001 | read, write, admin |
"""


def test_h4_tc_counted_and_fenced_tc_ignored():
    # The real #### TC covers read/write/admin; the fenced example is NOT a source
    # of coverage on its own but must not crash or double-count.
    data, code = run(_w(D27_H4_AND_FENCE))
    assert data["facet_covered"] is True
    assert data["uncovered_facets"] == {}
    assert code == 0


# --- #6: a half-tagged TC (Facets but no REQ ID) is surfaced, not silently dropped ---
D27_HALF_TAGGED = """\
# D-27

## Chi tiết test case

### TC-001: tagged
**REQ ID:** REQ-013
**Facets:** read

### TC-002: half
**Facets:** write

## Ma trận bao phủ (Coverage Matrix)

| REQ ID | Test Cases | Facets |
|--------|------------|--------|
| REQ-013 | TC-001 | read |
"""


def test_half_tagged_tc_surfaced():
    data, code = run(_w(D27_HALF_TAGGED))
    assert data["malformed_tc"] == 1  # TC-002 has Facets but no REQ ID
    assert data["facet_covered"] is True  # REQ-013's declared 'read' is covered


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
