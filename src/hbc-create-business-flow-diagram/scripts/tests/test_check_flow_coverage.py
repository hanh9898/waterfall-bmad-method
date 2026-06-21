#!/usr/bin/env python3
"""Tests for check-flow-coverage.py (B8-2 all-paths / B8-5 phantom+REQ-facet / B8-6 path-ID)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-flow-coverage.py")

# A D-06 with: block0 = single-path AS-IS (no branch, no REQ → single + phantom);
# block1 = TO-BE flowchart WITH a decision + REQ + PATH-01 (clean).
D06_MIXED = """\
---
document_id: D-06
---

# D-06

## 1. AS-IS
```mermaid
sequenceDiagram
    actor U as User
    participant S as System
    U->>S: do thing
    S-->>U: result
```

## 2. TO-BE (REQ-AUTH-001)
%% PATH-01 happy, PATH-02 reject
```mermaid
flowchart TD
    Start(["submit REQ-AUTH-001"]) --> D{"valid?"}
    D -- "yes" --> OK["accept"]
    D -- "no" --> Err["reject"]
```
"""

D02 = """\
# D-02
- REQ-AUTH-001 Login
- REQ-AUTH-002 Logout
- REQ-AUTH-003 Reset
"""


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_single_path_flow_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, rc = run([str(g)])
        # block 0 (AS-IS, no alt) is single-path; block 1 (flowchart w/ decision) is not.
        assert result["single_path_flows"] == [0], result["single_path_flows"]
        assert rc == 1


def test_phantom_flow_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, rc = run([str(g)])
        # block 0 cites no REQ → phantom; block 1 cites REQ-AUTH-001 → not.
        assert result["phantom_flows"] == [0], result["phantom_flows"]
        assert any(i["type"] == "PHANTOM_FLOW" for i in result["issues"])


def test_path_id_well_formed_collected():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, _ = run([str(g)])
        assert result["path_ids"] == ["PATH-01", "PATH-02"], result["path_ids"]
        assert result["malformed_path_ids"] == []


def test_malformed_path_id_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # PATH-1 (one digit) and PATH-A do not match PATH-\d{2,}
        doc = D06_MIXED.replace("%% PATH-01 happy, PATH-02 reject", "%% PATH-1 happy, PATH-A reject")
        g = write(tmp, "D-06.md", doc)
        result, rc = run([str(g)])
        assert set(result["malformed_path_ids"]) == {"PATH-1", "PATH-A"}, result["malformed_path_ids"]
        assert any(i["type"] == "MALFORMED_PATH_ID" for i in result["issues"])
        assert rc == 1


def test_uncovered_reqs_flagged_against_source():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)  # only references REQ-AUTH-001
        src = write(tmp, "D-02.md", D02)  # defines 001/002/003
        result, rc = run([str(g), "--sources", str(src)])
        assert result["grounded"] is True
        assert "REQ-AUTH-002" in result["uncovered_reqs"]
        assert "REQ-AUTH-003" in result["uncovered_reqs"]
        assert "REQ-AUTH-001" not in result["uncovered_reqs"]
        assert rc == 1


def test_bare_and_canonical_req_reconcile():
    # D-06 cites bare REQ-002; source defines canonical REQ-AUTH-002 → same trailing
    # number, must reconcile (not falsely uncovered).
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = D06_MIXED.replace("REQ-AUTH-001", "REQ-001").replace(
            'OK["accept"]', 'OK["accept REQ-002 REQ-003"]')
        g = write(tmp, "D-06.md", doc)
        src = write(tmp, "D-02.md", D02)
        result, _ = run([str(g), "--sources", str(src)])
        assert result["uncovered_reqs"] == [], result["uncovered_reqs"]


def test_statediagram_is_not_single_path():
    # A stateDiagram is exempt from B8-2 (its transitions are the branches).
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = """\
# D-06
```mermaid
stateDiagram-v2
    [*] --> A: start (REQ-001)
    A --> B
    B --> [*]
```
"""
        g = write(tmp, "D-06.md", doc)
        result, _ = run([str(g)])
        assert result["single_path_flows"] == [], result["single_path_flows"]


def test_clean_document_passes():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = """\
# D-06
## TO-BE (REQ-001)
%% PATH-01 happy, PATH-02 exception
```mermaid
flowchart TD
    S(["start REQ-001"]) --> D{"ok?"}
    D -- "yes" --> Y["done"]
    D -- "no" --> N["error"]
```
"""
        g = write(tmp, "D-06.md", doc)
        result, rc = run([str(g)])
        assert result["valid"] is True, result["issues"]
        assert rc == 0


def test_advisory_when_no_sources():
    # No --sources → uncovered_reqs not computed (grounded False), but path/phantom
    # checks still run on the doc itself.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, _ = run([str(g)])
        assert result["grounded"] is False
        assert result["uncovered_reqs"] == []


def test_honest_verdict_fields():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, _ = run([str(g)])
        assert "structure_ok" in result
        assert result["semantic_review"] == "n/a"
        assert result["not_checked"]
        assert "block_count" in result


def test_missing_source_is_loud_error():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, rc = run([str(g), "--sources", str(tmp / "nope.md")])
        assert rc == 2
        assert "error" in result


def test_custom_path_id_pattern():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = D06_MIXED.replace("%% PATH-01 happy, PATH-02 reject", "%% P1 happy")
        g = write(tmp, "D-06.md", doc)
        # accept the project's own scheme; PATH tokens absent → no malformed
        result, _ = run([str(g), "--path-id-pattern", r"P\d+"])
        assert result["path_ids"] == ["P1"], result["path_ids"]
        assert result["malformed_path_ids"] == []


def test_custom_pattern_with_capture_group_not_corrupted():
    # A --path-id-pattern carrying a capture group must still collect the WHOLE
    # match (not just the group) and must not flag unrelated PATH- text as malformed.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        doc = D06_MIXED.replace("%% PATH-01 happy, PATH-02 reject", "%% UC-1 happy")
        g = write(tmp, "D-06.md", doc)
        result, _ = run([str(g), "--path-id-pattern", r"(UC)-\d+"])
        assert result["path_ids"] == ["UC-1"], result["path_ids"]
        assert result["malformed_path_ids"] == []  # PATH- scheme not in use → no noise


def test_bad_path_id_pattern_exit_2():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-06.md", D06_MIXED)
        result, rc = run([str(g), "--path-id-pattern", "PATH-[", "-o", str(tmp / "o.json")])
        assert rc == 2
        assert "error" in result


def test_missing_d06_file():
    result, rc = run(["/nonexistent/D-06.md"])
    assert rc == 2
    assert "error" in result


def test_project_root_resolves_relative_paths():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write(tmp, "D-06.md", D06_MIXED)
        write(tmp, "D-02.md", D02)
        result, _ = run(["D-06.md", "--project-root", str(tmp), "--sources", "D-02.md"])
        assert result["grounded"] is True
        assert "error" not in result


def test_real_fixture_d06_behaves_sensibly():
    # Eval on the TD.0 fixture: the v2.3 D-06 covers all 42 REQs (no uncovered),
    # but uses no PATH-NN scheme yet (B8-6 incomplete) and has happy-only AS-IS.
    fixture = (Path(__file__).resolve().parents[4]
               / "process-review" / "fixtures" / "resource-plan-billable"
               / "artifacts" / "planning-artifacts" / "D-06-opms"
               / "D-06-business-flow-diagram.md")
    if not fixture.exists():
        return  # fixture not checked out — skip rather than fail
    src = (fixture.parents[1] / "D-02-resource-plan-billable.md")
    result, _ = run([str(fixture), "--sources", str(src)])
    assert result["uncovered_reqs"] == [], result["uncovered_reqs"]  # all REQs covered
    assert result["path_ids"] == []  # no PATH-NN scheme yet → B8-6 work remains
    assert result["block_count"] == 7


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
