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

### Đợt 0 — Nền móng (mở khóa mọi thứ)
- [ ] **C-1** Tạo thư viện chung `hbc_validation` (`parse_table`, `extract_column`, `section_labels(config)`, `verdict(...)`).
- [ ] **S-3** Schema phán-quyết-trung-thực: `{ structure_ok, semantic_review: pending|passed|n/a, checked[], not_checked[] }`; `passed` tổng = `structure_ok && semantic_review != pending`.
- [ ] **C-2** Hợp đồng rubric review (Lớp 1) + kỷ luật tách-facet.
- **Đo thành công:** requirements + glossary chạy trên lib, output có `structure_ok/semantic_review`, test xanh (TDD: test lib trước).

### Đợt 1 — Quick wins (cắm vào nền, đóng defect rẻ)
- [ ] **S-1** Nhãn section: English canonical + `document_output_language` (bỏ JP cứng) → đóng glossary-JP, requirements-VN, yêu cầu bỏ Nhật.
- [ ] **S-4** Chỉ quét trong ô cột bảng (bỏ `entity.lower() in content`, `REQ-\d+` toàn file) → đóng REQ-over-count, entity-substring.
- [ ] **E-2** Xóa đường fail im lặng (thiếu `project-context.md` → cảnh báo rõ "bỏ qua infra").
- [ ] **E-1** Strip tiếng Nhật khỏi template gốc BMad mà skill phát ra.
- [ ] **C-4** Artifact resolver dir-aware tra theo tiền tố D-ID → đóng discover-bỏ-D02, D06-folder-glob, P1-05-khó-hiểu.

### Đợt 2 — Tầng ngữ nghĩa (giá trị thật)
- [ ] **A-1** Nâng cơ chế `QUALITY → PENDING_LLM` của phase-gate thành primitive chung.
- [ ] **A-2** Rubric facet tái dùng `{read|write} × {api|admin}` (mở rộng được).
- [ ] **Lớp-2 embed** Thêm Stage review ngữ nghĩa vào các create-skill.
- [ ] **A-3** Frontmatter `semanticReview: {status, reviewedBy, date, openFacets}`.
- [ ] **M-1** Metric coverage facet-aware (đếm theo ô facet, không theo REQ).
- [ ] **R-2** Taxonomy task mở — suy loại task từ artifact có mặt (đóng taxonomy-thiếu-loại + entity=CRUD).

### Đợt 3 — Bộ răng + gate liên-doc
- [ ] **R-1** Mặc định "chưa review = CHƯA pass" (đảo gánh nặng chứng minh).
- [ ] **#5** phase-gate thêm item loại `REVIEW`, chặn nếu `semanticReview.status != passed`; liệt kê `openFacets`.
- [ ] **P-1** `hbc-check-implementation-readiness` = gate bắt buộc trước phase-gate 2.
- [ ] **A-4** Traceability ↔ D-02 sync (mượn covered/uncovered/phantom của check-fr-coverage).

### Track song song
- [ ] **S-2** `validate-mermaid.py`: regex → parser thật (`mmdc` render thử); actor-coverage làm lớp phụ. Cô lập, làm bất cứ lúc nào sau Đợt 0.

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
