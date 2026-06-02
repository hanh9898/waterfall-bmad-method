---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Refactor bộ skill HBC dựa trên các vấn đề validator/convention/seam đã phát hiện'
session_goals: 'Sinh ý tưởng giải pháp kỹ thuật VÀ ưu tiên/lộ trình triển khai'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'SCAMPER Method', 'Solution Matrix']
ideas_generated: 21
context_file: ''
technique_execution_complete: true
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Hanhnt2
**Date:** 2026-06-02

## Session Overview

**Topic:** Refactor bộ skill HBC dựa trên các vấn đề đã phát hiện trong phiên review trước.

**Goals:** Vừa sinh ý tưởng giải pháp kỹ thuật (cách fix/refactor), vừa rút ra ưu tiên/lộ trình (fix gì trước).

### Session Setup

Các "hạt giống vấn đề" làm nhiên liệu ideation:

- **Validator false-positive / false-safety:** requirements đếm REQ-token toàn file + không nhận header tiếng Việt; glossary hardcode nhãn Nhật không fallback; validate-mermaid không phải parser thật (valid nhưng không render).
- **Discovery / convention:** discover chỉ nhận "PRD" bỏ D-02; D-06 output folder vs glob `D-06-*`; phase-gate P1-05 báo "1 file(s)" gây hiểu nhầm khi glob trúng thư mục.
- **task-breakdown:** taxonomy thiếu UI/admin + service/behavior; infra phụ thuộc cứng project-context.md fail im lặng; validator chỉ cấu trúc (không REQ→task, không ngữ nghĩa); đóng khung "entity = CRUD".
- **Xuyên suốt:** seam đa-facet REQ (mặt admin/write không ai test); bỏ tiếng Nhật → English + ngôn ngữ cấu hình BMad.

## Technique Execution Results

### Pha 1 — First Principles Thinking (hoàn tất)

Lột giả định gốc *"validator passed:true ⟹ tài liệu đúng"*. Rút ra 5 nền móng cho kiến trúc refactor:

**[Nền móng #1] Lằn ranh Cấu trúc ↔ Ngữ nghĩa** — Máy lo cấu trúc (đếm được, định dạng, thứ tự, trùng lặp); người/LLM lo ngữ nghĩa & đủ-nghĩa. Validator hiện lấn sân phán "đúng" trong khi chỉ đủ tư cách phán "đúng cấu trúc".

**[Nền móng #2] Validator 2 tầng** — (1) script kiểm cấu trúc + đánh dấu phần "chưa kiểm được"; (2) bước LLM review ngữ nghĩa bắt buộc. phase-gate đã có mầm (QUALITY → PENDING_LLM) nhưng chưa nhân rộng.

**[Nền móng #3] Phạm vi quyết định vị trí** — Ngữ nghĩa trong 1 doc → review tại chỗ (nhúng skill). Nhất quán giữa nhiều doc → gate dùng chung (check-implementation-readiness).

**[Nền móng #4] Hợp đồng review = thư viện, không phải gác cổng** — Lớp chung chỉ cấp format output trung thực + rubric + kỷ luật tách-facet; A (local) và B (gate) đều vay nó. Sửa chuẩn 1 chỗ, áp mọi nơi.

**[Nền móng #5] "Chưa review" là trạng thái thấy-được & chặn-được** — frontmatter `semanticReview: {status, reviewedBy, date, openFacets}`; phase-gate thêm item loại REVIEW, chặn nếu `status != passed`. Biến lỗ hổng quy trình thành ràng buộc dữ liệu cứng.

**Kiến trúc tổng hợp:** 3 lớp — Lớp 1 hợp đồng review (thư viện) · Lớp 2 review nội-tài-liệu (nhúng từng create-skill) · Lớp 3 gate liên-tài-liệu (check-implementation-readiness, bắt buộc trước phase-gate 2).

### Pha 2 — SCAMPER (hoàn tất)

**S — Substitute**
- **[S-1]** Nhãn section: English canonical + `document_output_language` (bỏ JP cứng) → đóng glossary-JP + requirements-VN + yêu cầu bỏ Nhật.
- **[S-2]** `validate-mermaid.py`: regex → parser thật (`mmdc` render thử); actor-coverage làm lớp phụ.
- **[S-3]** `passed: true` → phán quyết trung thực `{structure_ok, semantic_review: pending|passed|n/a, checked[], not_checked[]}`; passed tổng = structure_ok && semantic_review != pending.
- **[S-4]** Bỏ so khớp lỏng (`entity.lower() in content`, `REQ-\d+` toàn file) → chỉ quét trong **ô cột bảng**.

**C — Combine**
- **[C-1]** Gộp khung validator lặp → thư viện `hbc_validation` (parse bảng, nhãn-config, phán-quyết-trung-thực, trích-ô-bảng).
- **[C-2]** Gộp review ngữ nghĩa rải rác → 1 hợp đồng rubric chung + kỷ luật tách-facet; Lớp 2 & 3 cùng dùng.
- **[C-4]** Gộp tìm tài liệu → 1 "artifact resolver" tra theo tiền tố D-ID, trả đúng file `.md` (dir-aware) → đóng discover-bỏ-D02 + D06-folder-glob + P1-05-khó-hiểu.

**A — Adapt**
- **[A-1]** Bê cơ chế `QUALITY → PENDING_LLM` của phase-gate thành primitive "máy giao việc LLM" dùng chung.
- **[A-2]** Bê "ma trận facet" từ vụ seam thành rubric tái dùng `{read|write} × {api|admin}`.
- **[A-3]** Bê pattern frontmatter `stepsCompleted` (business-flow) cho `semanticReview` state.
- **[A-4]** Bê logic covered/uncovered/phantom (check-fr-coverage) cho traceability matrix ↔ D-02.

**M / P / E / R**
- **[M-1]** Metric coverage facet-aware (đếm theo ô facet, không theo REQ).
- **[P-1]** hbc-check-implementation-readiness = gate ngữ nghĩa liên-doc bắt buộc trước phase-gate 2 (Lớp 3).
- **[E-1]** Xóa tiếng Nhật tại template gốc. **[E-2]** Xóa đường fail im lặng (thiếu project-context.md → cảnh báo rõ).
- **[R-1]** Mặc định "chưa review = CHƯA pass" (đảo gánh nặng chứng minh). **[R-2]** Taxonomy task mở, suy từ artifact có mặt (đóng taxonomy-thiếu-loại + entity=CRUD).

### Pha 3 — Solution Matrix (hoàn tất)

**Lưới Impact × Effort**

| | Effort thấp | Effort cao |
|---|---|---|
| Impact cao | S-1, S-4, E-2, C-4, E-1 | C-1, C-2, S-2, A-1, A-2, M-1 |
| Impact vừa | A-3, P-1, S-3 | R-1, A-4, R-2, Lớp-2-embed |

**Phụ thuộc mấu chốt:** C-1 (thư viện chung) + S-3 (phán quyết trung thực) + C-2 (hợp đồng rubric) là nền — mọi ý khác cắm vào, phải làm trước.

**Lộ trình 4 đợt:**
- **Đợt 0 — Nền móng:** C-1 thư viện `hbc_validation` · S-3 format trung thực · C-2 hợp đồng rubric (Lớp 1).
- **Đợt 1 — Quick wins:** S-1, S-4, E-2, E-1, C-4 → đóng glossary-JP, requirements-VN, REQ-over-count, entity-substring, discover-bỏ-D02, D06-glob, P1-05.
- **Đợt 2 — Tầng ngữ nghĩa:** A-1, A-2, Lớp-2 embed, A-3, M-1, R-2 → "máy lo cấu trúc, LLM lo ngữ nghĩa" + đóng seam đa-facet.
- **Đợt 3 — Bộ răng + gate liên-doc:** R-1, #5 phase-gate item REVIEW, P-1 readiness-gate bắt buộc, A-4 traceability↔D-02.
- **Track song song:** S-2 parser Mermaid thật (cần `mmdc`, cô lập, làm bất cứ lúc nào sau Đợt 0).

**Nguyên tắc xếp ưu tiên:** nền trước → quick-win đóng defect rẻ → tầng ngữ nghĩa → bộ răng ép tuân thủ.

## Idea Organization and Prioritization

**Tổ chức theo chủ đề (6 cụm):**
1. **Hợp đồng trung thực** — S-3, R-1, #5, A-1 → máy không được nói dối bằng `passed:true`.
2. **Nền chung / DRY** — C-1, C-2, C-4 → sửa 1 nơi, hết lệch giữa các skill.
3. **Bỏ ngôn ngữ cứng** — S-1, E-1 → English + `document_output_language`.
4. **Ngữ nghĩa & facet** — A-2, M-1, Lớp-2 embed, R-2 → đóng seam đa-facet + taxonomy thiếu loại.
5. **Lưới an toàn liên-doc** — P-1, A-4, A-3.
6. **Diệt false-positive cấu trúc** — S-4, E-2, S-2.

**Kết quả ưu tiên:**
- **Top impact, làm trước:** Đợt 0 nền móng (C-1, S-3, C-2).
- **Quick wins:** S-1, S-4, E-2, E-1, C-4.
- **Breakthrough dài hạn:** tầng ngữ nghĩa (Đợt 2) + bộ răng ép tuân thủ (Đợt 3).

**Kế hoạch hành động — Đợt 0 (mắt xích mở khóa):**
1. Tạo `scripts/lib/hbc_validation.py` chung: `parse_table`, `extract_column`, `section_labels(config)`, `verdict(...)`.
2. Định nghĩa schema phán-quyết-trung-thực (S-3) + schema rubric review (C-2) — viết spec + ví dụ trước khi refactor.
3. TDD: test lib trước, rồi rút từng `validate-*.py` về dùng lib.
- **Cần:** thống nhất chỗ đặt lib chung + quy ước import.
- **Đo thành công:** requirements + glossary chạy trên lib, output có `structure_ok/semantic_review`, test xanh.

## Session Summary and Insights

**Thành tựu chính:**
- 21 ý tưởng (5 nền móng + 16 giải pháp) → một kiến trúc refactor mạch lạc, không phải danh sách vá rời rạc.
- Lộ trình 4 đợt có thứ tự phụ thuộc rõ + track song song cho Mermaid parser.

**Insight đột phá:**
- Gốc của gần như mọi defect = validator **nhầm vai**: kiểm cấu trúc nhưng phát ngôn như đã kiểm ngữ nghĩa. Lằn ranh "máy lo cấu trúc · người/LLM lo ngữ nghĩa" là kim chỉ nam cho toàn bộ refactor.
- "Phạm vi quyết định vị trí": intra-doc → nhúng skill; inter-doc → gate dùng chung. Giải tỏa tranh luận A-vs-B.
- Bộ răng (frontmatter + phase-gate chặn) là thứ biến mọi cải tiến thành bắt-buộc, chống tái diễn vụ "quên chạy readiness-check".

**Reflections:** Phiên đi từ phát tán (First Principles) → hệ thống (SCAMPER) → hội tụ (Solution Matrix) đúng 2 vế mục tiêu: vừa ra ý tưởng, vừa ra lộ trình.


