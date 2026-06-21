#!/usr/bin/env python3
"""Tests for validate-coding-standards.py (D-12)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-coding-standards.py")

VALID_DOC = """\
---
document_id: D-12
version: "1.0"
status: draft
---

# Demo — Coding Standards

## 1. Overview
Chuẩn code cho dự án demo.

## 2. Naming Conventions
snake_case cho biến, PascalCase cho class.

```python
order_total = 0
class OrderService: ...
```

## 3. Formatting
Thụt lề 4 khoảng trắng.

```python
def f():
    return 1
```

## 4. Comments
Docstring cho mọi public function.

```python
def g():
    \"\"\"Trả về g.\"\"\"
    return 2
```

## 5. Imports
Nhóm stdlib / third-party / local.

## 6. Error Handling
Raise lỗi rõ ràng, không nuốt exception.

## 7. Security
Không nhúng secret; validate input.

## 8. Testing
pytest; mỗi script có test.

## 9. Framework-Specific
Tuân theo convention của framework đang dùng.

## 10. Git Conventions
Conventional commits; PR review bắt buộc.
"""


def run_script(doc_content: str, extra: list[str] | None = None) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-12-demo.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path)] + (extra or [])
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True


def test_missing_section():
    doc = VALID_DOC.replace("## 7. Security", "## 7. Removed")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "SECTION_MISSING" for i in result["issues"])


def test_few_examples():
    # strip all fenced code blocks → fewer than 3 examples
    import re
    doc = re.sub(r"```python\n.*?```", "(example removed)", VALID_DOC, flags=re.DOTALL)
    result, code = run_script(doc)
    assert any(i["type"] == "FEW_EXAMPLES" for i in result["issues"])


def test_vietnamese_sections():
    doc = (VALID_DOC
           .replace("## 1. Overview", "## 1. Tổng quan")
           .replace("## 2. Naming Conventions", "## 2. Quy ước đặt tên")
           .replace("## 3. Formatting", "## 3. Định dạng")
           .replace("## 4. Comments", "## 4. Chú thích")
           .replace("## 5. Imports", "## 5. Import")
           .replace("## 6. Error Handling", "## 6. Xử lý lỗi")
           .replace("## 7. Security", "## 7. Bảo mật")
           .replace("## 8. Testing", "## 8. Kiểm thử")
           .replace("## 9. Framework-Specific", "## 9. Đặc thù framework")
           .replace("## 10. Git Conventions", "## 10. Quy ước Git"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-12.md"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1


if __name__ == "__main__":
    tests = [test_valid_document, test_missing_section, test_few_examples,
             test_vietnamese_sections, test_missing_document]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
