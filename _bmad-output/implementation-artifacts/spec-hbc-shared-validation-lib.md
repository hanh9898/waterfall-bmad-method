---
title: 'HBC shared validation lib + honest verdict (Đợt 0)'
type: 'refactor'
created: '2026-06-02'
status: 'done'
baseline_commit: '537fde08cec40cabb19722ec3754c1bcbd5be02a'
context:
  - '{project-root}/_bmad-output/hbc-refactor-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Mỗi validator HBC tự viết lại parse bảng / kiểm section / in JSON, và phát ngôn `valid:true` như thể đã kiểm ngữ nghĩa — gây lệch nhau giữa skill, false-positive (đếm `REQ-\d+` toàn file), và hardcode nhãn tiếng Nhật. Đây là Đợt 0 (nền móng) của `hbc-refactor-plan.md`.

**Approach:** Tạo một thư viện chung `hbc_validation` (C-1) cung cấp parse-bảng, trích-cột, nhận-diện-section theo config (English + `document_output_language`, S-1), và hàm dựng **phán quyết trung thực** (S-3: `structure_ok / semantic_review / checked / not_checked`). Rút 2 validator (requirements, glossary) về dùng lib làm bằng chứng — giữ hành vi cũ, chỉ thay đổi đúng các bug đã định (REQ over-count, nhãn JP-only).

## Boundaries & Constraints

**Always:**
- Lib sống tại `.claude/skills/hbc-shared/lib/hbc_validation.py`; validator import qua sys.path bootstrap tính theo `parents[2]/"hbc-shared"/"lib"`.
- TDD: viết test lib TRƯỚC khi viết lib; test phải đỏ rồi mới xanh.
- Migration **behavior-preserving** trừ 2 thay đổi cố ý: (1) nhận section theo English+`document_output_language` thay vì JP-only; (2) đếm REQ ID chỉ trong cột ID của bảng functional, không quét toàn file (S-4).
- Section recognition KHÔNG hardcode tiếng Nhật.

**Ask First:**
- Nếu phải đổi *shape* output đang được SKILL.md/phase-gate tiêu thụ (xóa key `valid`/`issues`/counts) → HALT hỏi. Mặc định: **additive** (giữ key cũ, THÊM trường verdict mới).
- Nếu lộ ra cần sửa file ngoài 6 file trong Code Map → HALT hỏi.

**Never:**
- KHÔNG wiring LLM semantic review ở Đợt 0 (đó là Đợt 2) → `semantic_review` mặc định `"n/a"` cho validator cấu trúc; KHÔNG để `passed` hoá false hàng loạt.
- KHÔNG đụng các validator/skill khác (chỉ requirements + glossary).
- KHÔNG cài package vào venv / phá mô hình uv-run standalone.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| verdict structural-only | `structure_ok=True, semantic_review="n/a"` | `passed=True`, gồm `checked[]`/`not_checked[]` | N/A |
| verdict chưa review | `semantic_review="pending"` | `passed=False` dù `structure_ok=True` | N/A |
| section nhận theo config | doc dùng nhãn tiếng Việt, `document_output_language=vi` | section được tìm thấy (không cần nhãn JP) | N/A |
| REQ ID trong prose | `REQ-001` xuất hiện ở User Roles + cột ID bảng | đếm 1 lần (chỉ cột bảng) → không báo DUPLICATE giả | N/A |
| bảng rỗng / không có | section không có bảng | `parse_table` trả `[]` | không raise |
| cột vượt chỉ số | `extract_column(rows, 9)` | bỏ qua ô thiếu, trả phần có | không raise |

</frozen-after-approval>

## Code Map

- `.claude/skills/hbc-shared/lib/hbc_validation.py` — **MỚI** lib chung: `parse_table`, `extract_column`, `find_section`/`section_labels`, `verdict`.
- `.claude/skills/hbc-shared/lib/tests/test_hbc_validation.py` — **MỚI** pytest cho lib (viết trước).
- `.claude/skills/hbc-create-requirements/scripts/validate-requirements.py` — rút về lib; REQ ID đếm theo cột bảng; section theo config; output qua `verdict`.
- `.claude/skills/hbc-create-glossary/scripts/validate-glossary.py` — rút về lib; section theo config (bỏ JP-only); table qua `parse_table`; output qua `verdict`.
- `.claude/skills/hbc-create-requirements/scripts/tests/test_validate_requirements.py` — cập nhật kỳ vọng (additive keys, hết false DUPLICATE).
- `.claude/skills/hbc-create-glossary/scripts/tests/test_validate_glossary.py` — cập nhật kỳ vọng (section VN/EN, additive keys).

## Tasks & Acceptance

**Execution:**
- [x] `.claude/skills/hbc-shared/lib/tests/test_hbc_validation.py` -- viết test cho 4 hàm + I/O matrix -- TDD đỏ trước
- [x] `.claude/skills/hbc-shared/lib/hbc_validation.py` -- implement 4 hàm tới khi test xanh -- nền dùng chung
- [x] `.claude/skills/hbc-create-requirements/scripts/validate-requirements.py` -- thêm bootstrap + rút check section/REQ-column/verdict về lib -- đóng REQ over-count + nhãn config
- [x] `.claude/skills/hbc-create-glossary/scripts/validate-glossary.py` -- bootstrap + rút section/table/verdict về lib -- bỏ JP hardcode
- [x] `.claude/skills/hbc-create-requirements/scripts/tests/test_validate_requirements.py` -- cập nhật kỳ vọng -- xác nhận hết false-positive
- [x] `.claude/skills/hbc-create-glossary/scripts/tests/test_validate_glossary.py` -- cập nhật kỳ vọng -- xác nhận section đa-ngôn-ngữ

**Acceptance Criteria:**
- Given tài liệu D-02 tham chiếu `REQ-001` trong prose và bảng, when chạy validate-requirements, then KHÔNG có issue `REQ_ID_DUPLICATE`/`REQ_ID_ORDER` giả.
- Given glossary dùng nhãn section tiếng Việt và `document_output_language=Tiếng Việt`, when validate-glossary, then không có `SECTION_MISSING`.
- Given validator cấu trúc chạy ở Đợt 0, when in JSON, then có cả key cũ (`valid`/`issues`) lẫn trường mới (`structure_ok`,`semantic_review="n/a"`,`checked`,`not_checked`); các doc đang hợp lệ vẫn `valid:true`.
- Given cả 3 bộ test (lib + 2 validator), when chạy pytest, then tất cả xanh.

## Spec Change Log

## Design Notes

`verdict(structure_ok, *, semantic_review="n/a", checked, not_checked)` → `{"structure_ok", "semantic_review", "checked", "not_checked", "passed": structure_ok and semantic_review != "pending"}`. Đợt 0 truyền `semantic_review="n/a"` (chưa có lớp ngữ nghĩa); Đợt 2/3 sẽ đổi sang `pending`/`passed` + bật gate R-1.

Bootstrap import (mỗi validator, đầu file sau std imports):
```python
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
from hbc_validation import parse_table, extract_column, find_section, verdict
```

## Verification

**Commands:**
- `cd .claude/skills/hbc-shared/lib && python3 -m pytest tests/ -q` -- expected: all pass
- `python3 -m pytest .claude/skills/hbc-create-requirements/scripts/tests .claude/skills/hbc-create-glossary/scripts/tests -q` -- expected: all pass
- `python3 .claude/skills/hbc-create-glossary/scripts/validate-glossary.py <glossary-VN.md> --project-root .` -- expected: không SECTION_MISSING giả; JSON có trường verdict mới

## Suggested Review Order

**Hợp đồng trung thực (S-3) — đọc trước để hiểu ý đồ**

- Phán quyết trung thực: `passed` chỉ true khi structure_ok và semantic_review != pending
  [`hbc_validation.py:111`](../../.claude/skills/hbc-shared/lib/hbc_validation.py#L111)
- Ba trạng thái semantic (n/a · pending · passed) — Đợt 0 dùng n/a
  [`hbc_validation.py:24`](../../.claude/skills/hbc-shared/lib/hbc_validation.py#L24)

**Primitive dùng chung (C-1) + các fix từ review**

- find_section: chỉ match heading cấp 1–2, không dính subsection `###` (fix review)
  [`hbc_validation.py:29`](../../.claude/skills/hbc-shared/lib/hbc_validation.py#L29)
- section_body: cắt theo cấp heading bằng-hoặc-cao-hơn (fix review)
  [`hbc_validation.py:57`](../../.claude/skills/hbc-shared/lib/hbc_validation.py#L57)
- parse_table: dừng ở bảng đầu, không rò bảng thứ 2; chịu hàng thiếu `|` cuối (fix review)
  [`hbc_validation.py:71`](../../.claude/skills/hbc-shared/lib/hbc_validation.py#L71)

**Rút validator về lib**

- REQ ID lấy theo hàng bảng (bỏ giả định cột 0) — đóng S-4 over-count
  [`validate-requirements.py:58`](../../.claude/skills/hbc-create-requirements/scripts/validate-requirements.py#L58)
- Section nhận English + tiếng Việt, bỏ JP cứng (S-1); output additive + verdict
  [`validate-requirements.py:178`](../../.claude/skills/hbc-create-requirements/scripts/validate-requirements.py#L178)
- Glossary: nhãn section EN+VI thay 3 nhãn JP hardcode
  [`validate-glossary.py:38`](../../.claude/skills/hbc-create-glossary/scripts/validate-glossary.py#L38)
- Import guard: thiếu lib → JSON error, không traceback (fix review)
  [`validate-glossary.py:20`](../../.claude/skills/hbc-create-glossary/scripts/validate-glossary.py#L20)

**Tests (đọc cuối)**

- Lib unit tests (16) gồm các ca regression từ review
  [`test_hbc_validation.py:1`](../../.claude/skills/hbc-shared/lib/tests/test_hbc_validation.py#L1)
- Requirements: test prose-REQ không bị tính trùng (S-4)
  [`test_validate_requirements.py:116`](../../.claude/skills/hbc-create-requirements/scripts/tests/test_validate_requirements.py#L116)
- Glossary: test nhận section tiếng Việt
  [`test_validate_glossary.py:133`](../../.claude/skills/hbc-create-glossary/scripts/tests/test_validate_glossary.py#L133)
