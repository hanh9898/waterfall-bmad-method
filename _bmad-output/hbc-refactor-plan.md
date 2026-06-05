---
title: "HBC Skills Refactor Plan"
status: draft
created: 2026-06-02
source: "_bmad-output/brainstorming/brainstorming-session-2026-06-02-1255.md"
related:
  - "_bmad-output/brainstorming/brainstorming-session-2026-06-02-1255.md"
---

# HBC Skills — Refactor Plan & Roadmap

> Nguồn: phiên brainstorming 2026-06-02 (First Principles → SCAMPER → Solution Matrix).
> Mục tiêu: loại false-positive/false-safety của validator, thống nhất convention, đóng seam liên-tài-liệu, bỏ tiếng Nhật cứng.

## Nguyên tắc gốc

**Máy lo cấu trúc · người/LLM lo ngữ nghĩa & đủ-nghĩa.**
Gốc của gần như mọi defect: validator **nhầm vai** — kiểm cấu trúc nhưng phát ngôn `passed:true` như đã kiểm ngữ nghĩa.

Hệ quả nguyên tắc:
- **Phạm vi quyết định vị trí:** ngữ nghĩa trong 1 doc → review nhúng skill; nhất quán giữa nhiều doc → gate dùng chung.
- **Hợp đồng review = thư viện, không phải gác cổng:** chuẩn format/rubric ở một nơi, ai cũng vay.
- **"Chưa review" phải thấy-được & chặn-được:** ràng buộc dữ liệu, không dựa trí nhớ người chạy.

## Kiến trúc 3 lớp

| Lớp | Vai trò | Hiện vật |
|---|---|---|
| **Lớp 1** | Hợp đồng review (thư viện) | format phán-quyết-trung-thực, rubric, kỷ luật tách-facet |
| **Lớp 2** | Review nội-tài-liệu | mỗi create-skill thêm Stage "LLM semantic review" nạp rubric domain |
| **Lớp 3** | Gate liên-tài-liệu | `hbc-check-implementation-readiness` bắt buộc trước `hbc-phase-gate` Phase 2 |

## Lộ trình 4 đợt

### Đợt 0 — Nền móng (mở khóa mọi thứ) ✅ commit 188614a (2026-06-02)
- [x] **C-1** Thư viện chung `hbc_validation` (`parse_table`, `extract_column`, `find_section`, `section_body`, `verdict`).
- [x] **S-3** Schema phán-quyết-trung-thực `{ structure_ok, semantic_review, checked[], not_checked[], passed }`; `passed = structure_ok && semantic_review != pending`.
- [x] **C-2** Hợp đồng review (Lớp 1): format verdict (lib) + rubric/kỷ luật tách-facet (`semantic-review-rubric.md`). Hoàn tất qua A-2.
- **Đo thành công:** ✅ requirements + glossary chạy trên lib; output có structure_ok/semantic_review; lib 16 + validators 44 test xanh.

### Đợt 1 — Quick wins (cắm vào nền, đóng defect rẻ)
- [x] **S-1** Nhãn section EN + `document_output_language` (bỏ JP cứng) qua lib `check_required_sections`. ✅ 9 validator: requirements, glossary, task-breakdown, coding-standards, api-spec, test-spec, test-plan, test-execution, acceptance-check.
- [x] **S-4** Chỉ quét ô cột bảng. ✅ requirements (REQ column), task-breakdown (entity coverage theo design_ref).
- [x] **E-2** Cảnh báo khi thiếu `project-context.md` (task-breakdown SKILL.md Stage 2).
- [x] **E-1** Strip JP khỏi 7 template skill phát ra (assets/): D-02,D-03,D-12,D-19,D-21,D-26,D-27 — headings EN+VI, rename file JP (D-03/D-19), update customize.toml. (Root `templates/` 31 file JP là legacy, KHÔNG skill nào dùng → để deferred.)
- [x] **C-4** Dir-aware: phase-gate glob trúng thư mục → lặn vào lấy .md (đóng D06-folder-glob + P1-05); discover nhận D-02 làm nguồn yêu cầu (+EN/VI globs).

### Đợt 2 — Tầng ngữ nghĩa (giá trị thật)
- [x] **A-1** Primitive review-ngữ-nghĩa dùng chung: verdict `semantic_review` (n/a|pending|passed) + phase-gate REVIEW + rubric Lớp 1 — máy giao việc LLM một cách chuẩn hóa.
- [x] **A-2** Rubric facet (read/write × api/admin/ui/batch × lifecycle, mở rộng) tại `hbc-shared/references/semantic-review-rubric.md` — cũng là phần rubric của C-2.
- [x] **Lớp-2 embed** Stage "Semantic Review (Lớp 2)" + ghi `semanticReview` frontmatter, trỏ rubric chung, vào 6 create-skill: requirements, glossary, coding-standards, api-spec, test-spec, test-plan.
- [x] **A-3** Schema `semanticReview:{status,reviewedBy,date,openFacets}` + reader trong phase-gate (`_semantic_review_status`).
- [x] **M-1** Engine `check-facet-coverage.py`: required-facets (cột Facets D-02/Coverage Matrix) vs covered-facets (**Facets:** tag mỗi TC) → uncovered_facets per REQ. Convention thêm vào template D-27; wire test-spec Stage 4b + gate P2-08. Tests 13 (3 gốc + 10 hardening post-review: union D1, multi-REQ D3, pipe split, column scoring, comment-leak, exit-2, verdict-contract).
- [x] **R-2** task-breakdown Stage 2: taxonomy mở (checklist, không đóng kín) + thêm UI/Screen & Behavior/Service category; entity gồm cả business-logic (không chỉ CRUD); thêm taxonomy-completeness check.

### Đợt 3 — Bộ răng + gate liên-doc
- [x] **R-1** "chưa review = CHƯA pass": verdict (passed cần semantic_review != pending) + phase-gate REVIEW item P2-12 (D-27) active + Lớp-2 embed ghi status. Gánh nặng chứng minh đã đảo.
- [x] **#5** phase-gate `evaluate_review` + nhánh REVIEW: đọc frontmatter `semanticReview.status`, FAIL nếu != passed (block/inline YAML). A-3 schema `semanticReview:{status,reviewedBy,date,openFacets}`. Chưa thêm REVIEW row vào checklist (bật sau embed).
- [x] **P-1** Skill `hbc-check-implementation-readiness` ([IR]): engine `check-readiness.py` reconcile D-02 ↔ D-21/D-26/D-27 + matrix (uncovered/orphan/missing, verdict S-3); SKILL.md; đăng ký bmad-help.csv; wire gate P2-11 (required). Tests 15 (6 gốc + 9 hardening post-review: D-21 informational, D4 vắng-section=lỗi, P6 gated-any, D-26 path, orphan-via-D21, matrix happy, --output, verdict-contract).
- [x] **A-4** `trace-report.py --d02`: so matrix REQ ids ↔ D-02 → orphan_in_matrix / missing_from_matrix; --strict & --validate fail nếu lệch. Tests +2.

### Track song song
- [x] **S-2** `validate-mermaid.py` render thật qua `mmdc` (fail→FAIL); khi vắng mmdc báo `render_check: skipped` trung thực (hết false-safety). Actor-coverage giữ làm lớp cấu trúc.

## Bản đồ defect → giải pháp

| Defect (từ review) | Giải pháp |
|---|---|
| requirements đếm REQ-token toàn file | S-4 |
| requirements không nhận header tiếng Việt | S-1 |
| glossary hardcode nhãn Nhật | S-1, E-1 |
| validate-mermaid không phải parser thật | S-2 |
| discover bỏ D-02 | C-4 |
| D-06 folder vs glob `D-06-*` | C-4 |
| phase-gate P1-05 báo "1 file(s)" khó hiểu | C-4 |
| task-breakdown taxonomy thiếu UI/admin/service | R-2 |
| task-breakdown infra fail im lặng | E-2 |
| task-breakdown validator chỉ cấu trúc | C-1, C-2, Lớp-2 embed, A-4 |
| task-breakdown entity=CRUD | R-2 |
| seam đa-facet REQ | A-2, M-1, P-1 |
| `passed:true` đọc nhầm = đúng | S-3, R-1, #5 |
| 2 validator xử lý ngôn ngữ khác nhau | C-1, C-2 |
