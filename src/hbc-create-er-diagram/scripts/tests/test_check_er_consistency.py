#!/usr/bin/env python3
"""Tests for check-er-consistency.py (B2-2 entity↔REQ / B2-3 ondelete / B2-5 REQ+D-06 / B2-7 drift / B2-9 churn)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-er-consistency.py")

# A D-19 with one erDiagram block that cites REQ-AUTH-001 in a comment, two tables,
# one FK with an ondelete behavior and one without, and a date-first revision row.
D19_CLEAN = """\
---
document_id: D-19
version: "1.0"
---

# D-19

## 2. ER Diagram
```mermaid
erDiagram
    %% account + session (REQ-AUTH-001)
    account {
        int id PK
        string email
    }
    session {
        int id PK
        int account_id FK
    }
    account ||--o{ session : "has"
```

## 3. Table Definitions
### 3.1 account
- **Physical name (Tên vật lý)**: `auth_account`
| name | phys | type | constraint | desc |
|---|---|---|---|---|
| account | account_id | INTEGER | FK -> auth_account, ON DELETE CASCADE | (REQ-AUTH-001) |
| email | email | VARCHAR | FK -> nothing | no ondelete here |

**Revision History**
| Date | Version | Changes | Author |
|---|---|---|---|
| 2026-06-20 | 1.0 | Initial creation | team |
"""

# D-02 source defining three REQs (D-19 only cites 001 → 002/003 uncovered).
D02 = """\
# D-02
- REQ-AUTH-001 Account
- REQ-AUTH-002 Session
- REQ-AUTH-003 Logout
"""

# Odoo model code declaring auth.account (matches design phys auth_account) but NOT
# auth.session — and code adds an undocumented auth.token model.
CODE_MODEL = """\
class Account(models.Model):
    _name = 'auth.account'

class Token(models.Model):
    _name = 'auth.token'
"""


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_clean_doc_no_sources_no_code_passes():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        result, rc = run([str(g)])
        # No phantom (block cites REQ-AUTH-001); no sources/code → those checks skipped.
        assert result["valid"] is True, result["issues"]
        assert result["phantom_entity_blocks"] == []
        assert result["grounded_reqs"] is False
        assert result["grounded_code"] is False
        assert rc == 0


def test_phantom_entity_block_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = D19_CLEAN.replace("%% account + session (REQ-AUTH-001)", "%% account + session").replace(
            "| (REQ-AUTH-001) |", "| (none) |")
        g = write(tmp, "D-19.md", doc)
        result, rc = run([str(g)])
        assert result["phantom_entity_blocks"] == [0], result["phantom_entity_blocks"]
        assert any(i["type"] == "PHANTOM_ENTITY_BLOCK" for i in result["issues"])
        assert rc == 1


def test_uncovered_reqs_flagged_against_sources():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        src = write(tmp, "D-02.md", D02)
        result, rc = run([str(g), "--sources", str(src)])
        assert result["grounded_reqs"] is True
        assert "REQ-AUTH-002" in result["uncovered_reqs"]
        assert "REQ-AUTH-003" in result["uncovered_reqs"]
        assert "REQ-AUTH-001" not in result["uncovered_reqs"]
        assert rc == 1


def test_bare_and_canonical_req_reconcile():
    # D-19 cites bare REQ-001 (+ adds 002/003); source defines canonical REQ-AUTH-00N.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = D19_CLEAN.replace("REQ-AUTH-001", "REQ-001 REQ-002 REQ-003")
        g = write(tmp, "D-19.md", doc)
        src = write(tmp, "D-02.md", D02)
        result, _ = run([str(g), "--sources", str(src)])
        assert result["uncovered_reqs"] == [], result["uncovered_reqs"]


def test_schema_drift_design_only_and_code_only():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        write(tmp, "models/account.py", CODE_MODEL)
        result, rc = run([str(g), "--code-dir", str(tmp / "models")])
        assert result["grounded_code"] is True
        # auth_account in design matches code auth.account → NOT design_only.
        # auth_session is NOT in this minimal D19 phys-name set (no phys line), so the
        # drift here is driven by code: auth.token is code_only (undocumented model).
        assert "auth.token" in result["schema_drift"]["code_only"], result["schema_drift"]
        assert any(i["type"] == "SCHEMA_DRIFT_CODE_ONLY" for i in result["issues"])
        assert rc == 1


def test_design_only_drift_when_design_declares_unbuilt_model():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # Design declares a physical name the code never defines.
        doc = D19_CLEAN.replace(
            "- **Physical name (Tên vật lý)**: `auth_account`",
            "- **Physical name (Tên vật lý)**: `auth_account`\n- **Physical name (Tên vật lý)**: `auth.session.request`")
        g = write(tmp, "D-19.md", doc)
        write(tmp, "models/account.py", "class A(models.Model):\n    _name = 'auth.account'\n")
        result, rc = run([str(g), "--code-dir", str(tmp / "models")])
        assert "auth.session.request" in result["schema_drift"]["design_only"], result["schema_drift"]
        assert any(i["type"] == "SCHEMA_DRIFT_DESIGN_ONLY" for i in result["issues"])
        assert rc == 1


def test_ondelete_signal_counts():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        result, _ = run([str(g)])
        # Mermaid block stripped → 2 FK lines from the two table rows; 1 has ON DELETE CASCADE.
        assert result["ondelete"]["fk_lines"] == 2, result["ondelete"]
        assert result["ondelete"]["fk_with_ondelete"] == 1
        assert result["ondelete"]["fk_without_ondelete"] == 1


def test_churn_order_robust_high_churn():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # Append 4 more date-first revision rows → 5 total > threshold 4.
        extra = "\n".join(f"| 2026-06-2{i} | 1.{i} | x | t |" for i in range(1, 5))
        doc = D19_CLEAN + "\n" + extra
        g = write(tmp, "D-19.md", doc)
        result, _ = run([str(g)])
        assert result["churn"]["revisions"] == 5, result["churn"]
        assert result["churn"]["high_churn"] is True


def test_churn_threshold_override():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        result, _ = run([str(g), "--churn-threshold", "0"])
        # 1 revision row > threshold 0 → high churn.
        assert result["churn"]["high_churn"] is True


def test_honest_verdict_fields():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        result, _ = run([str(g)])
        assert "structure_ok" in result
        assert result["semantic_review"] == "n/a"
        assert result["not_checked"]
        assert "er_block_count" in result


def test_missing_source_is_loud_error():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        result, rc = run([str(g), "--sources", str(tmp / "nope.md")])
        assert rc == 2
        assert "error" in result


def test_missing_code_dir_is_loud_error():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        result, rc = run([str(g), "--code-dir", str(tmp / "nope")])
        assert rc == 2
        assert "error" in result


def test_missing_d19_file():
    result, rc = run(["/nonexistent/D-19.md"])
    assert rc == 2
    assert "error" in result


def test_project_root_resolves_relative_paths():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write(tmp, "D-19.md", D19_CLEAN)
        write(tmp, "D-02.md", D02)
        result, _ = run(["D-19.md", "--project-root", str(tmp), "--sources", "D-02.md"])
        assert result["grounded_reqs"] is True
        assert "error" not in result


def test_code_dir_excludes_tests_relative():
    # A model under a tests/ subdir must be excluded (relative-path exclusion) so it
    # is not read as a code model the design must declare.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        write(tmp, "models/account.py", "class A(models.Model):\n    _name = 'auth.account'\n")
        write(tmp, "models/tests/test_x.py", "class T(models.Model):\n    _name = 'auth.testonly'\n")
        result, _ = run([str(g), "--code-dir", str(tmp / "models")])
        assert "auth.testonly" not in result["schema_drift"]["code_only"], result["schema_drift"]


def test_multi_feature_sources_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-19.md", D19_CLEAN)
        multi = "# D-02\n- REQ-AUTH-001 x\n- REQ-BILLING-001 y\n"
        src = write(tmp, "D-02.md", multi)
        result, _ = run([str(g), "--sources", str(src)])
        assert result["multi_feature_sources"] is True
        assert set(result["source_feature_slugs"]) == {"REQ-AUTH", "REQ-BILLING"}


def test_real_fixture_d19_surfaces_drift_and_churn():
    # Eval on the TD.0 fixture: the v2.x D-19 declares resource.plan.request +
    # .request.line as physical names the code never defines (the RCA drift), and its
    # revision history is long (high churn). Surfaced, not green.
    fixture = (Path(__file__).resolve().parents[4]
               / "process-review" / "fixtures" / "resource-plan-billable")
    d19 = fixture / "artifacts" / "planning-artifacts" / "D-19-opms" / "D-19-er-diagram.md"
    code = fixture / "code"
    if not d19.exists() or not code.is_dir():
        return  # fixture not checked out — skip rather than fail
    result, rc = run([str(d19), "--code-dir", str(code)])
    assert "resource.plan.request" in result["schema_drift"]["design_only"], result["schema_drift"]
    assert "resource.plan.request.line" in result["schema_drift"]["design_only"]
    assert result["churn"]["high_churn"] is True, result["churn"]
    assert rc == 1


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
