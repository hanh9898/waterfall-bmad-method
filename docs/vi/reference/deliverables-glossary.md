# Bảng tra deliverable (D-xx)

> 🌐 [English](../../en/reference/deliverables-glossary.md) · **Tiếng Việt**
>
> 📖 **Reference** — tra cứu nhanh mọi deliverable HBC sinh ra. Muốn hiểu *deliverable là gì / vì sao đánh mã*, xem [Khái niệm cốt lõi](../explanation/concepts.md).

Mã `D-xx` thuộc bộ tài liệu chuẩn của HBLAB. HBC hiện sinh **8 tài liệu D-xx** sau, cộng một số artifact không đánh mã D (task breakdown, báo cáo test, gate, ma trận traceability).

HBC giao **tăng dần theo từng tính năng (incremental per-feature)**: mỗi tính năng đi qua Phase 1→4 rồi ship độc lập. Vì thế mỗi deliverable có một **phạm vi (scope)**:

- **per-feature** — sinh riêng cho từng tính năng, lưu dưới `features/<feature>/…`.
- **shared** — dùng chung toàn dự án, lưu dưới `shared/…`, sinh **một lần** ở Phase 0 (`hbc-project-init`).
- **dual** — có bản baseline dùng chung ở `shared/…`, kèm tùy chọn **bản ghi đè per-feature**; ưu tiên theo path-existence (bản override thắng nếu tồn tại).

> 📌 **Phase 0 — Project Init** (`PI`): **bắt buộc và chạy đầu tiên**, một lần cho toàn dự án (hoặc chạy lại để cập nhật trực tiếp). **Nhận biết brownfield** — với codebase đã có, tài liệu hoá code trước (`bmad-document-project` + `project-context.md`) rồi suy ra deliverable dùng chung; greenfield suy ra từ PRD/lựa chọn. Tạo các deliverable dùng chung — **D-12 Coding Standards, D-03 Glossary** — và baseline D-19 ERD / D-21 API. Không cần tham số `feature`.

## Tài liệu D-xx

> Cột **Bắt buộc**: ✅ = bắt buộc (điều kiện qua Phase Gate) · `—` = tùy chọn.
> Cột **Phạm vi**: per-feature · shared · dual.

| Mã | Tên | Phase | Skill | Bắt buộc | Phạm vi | Nơi lưu |
| --- | --- | --- | --- | :---: | --- | --- |
| **D-02** | Requirements Specification | 1 · Analysis | `REQ` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-03** | Glossary | 1 · Analysis | `GLO` | — | shared | `shared/glossary/` |
| **D-06** | Business Flow Diagram (AS-IS/TO-BE) | 1 · Analysis | `BFD` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-12** | Coding Standards | 2 · Design | `CS` | ✅ | shared | `shared/coding-standards/` |
| **D-19** | Database Design / ER Diagram | 2 · Design | `ERD` | ✅ | dual | `shared/erd/` (+ ghi đè per-feature) |
| **D-21** | API Specification | 2 · Design | `API` | — | dual | `shared/api/` (+ ghi đè per-feature) |
| **D-26** | Test Plan | 2 · Design | `TP` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |
| **D-27** | Test Specification | 2 · Design | `TS` | ✅ | per-feature | `features/<feature>/planning-artifacts/` |

> 📌 Các mã bị "khuyết" (D-01, D-04, D-05…) thuộc bộ chuẩn HBLAB rộng hơn nhưng **không** do HBC sinh ra — đừng nhầm là thiếu sót.

## Chi tiết từng tài liệu

### D-02 — Requirements Specification ✅
Đặc tả yêu cầu với các **REQ ID** và ranh giới phạm vi. ID theo dạng **`REQ-<FEAT>-NNN`** (ví dụ `REQ-AUTH-001`) cho yêu cầu của từng tính năng, cộng **`REQ-SHARED-NNN`** cho yêu cầu dùng chung (dạng cũ `REQ-NNN` vẫn parse được). Là nền của mọi phase sau và là nguồn để khởi tạo traceability (`TRI`). Phạm vi: per-feature → `features/<feature>/planning-artifacts/`.

### D-03 — Glossary
Thuật ngữ miền nghiệp vụ thống nhất, tổng hợp từ tài liệu dự án và yêu cầu. Tùy chọn. Phạm vi: shared → `shared/glossary/`, **sinh ở Phase 0 (`PI`)**; `GLO` duy trì về sau.

### D-06 — Business Flow Diagram ✅
Sơ đồ luồng nghiệp vụ AS-IS / TO-BE bằng Mermaid, dựng từ PRD và planning artifacts. Bắt buộc — là điều kiện qua Phase Gate 1. Phạm vi: per-feature → `features/<feature>/planning-artifacts/`.

### D-12 — Coding Standards ✅
Quy chuẩn code theo từng dự án — đặt tên, format, xử lý lỗi — điều chỉnh theo framework đang dùng. Phạm vi: shared → `shared/coding-standards/`, **sinh ở Phase 0 (`PI`)**; `CS` duy trì về sau.

### D-19 — Database Design / ER Diagram ✅
Tài liệu thiết kế CSDL kèm ER Diagram (Mermaid), suy ra từ yêu cầu và kiến trúc. Phạm vi: dual — baseline ở `shared/erd/`, có thể ghi đè per-feature tại `features/<feature>/planning-artifacts/` (bản override thắng nếu tồn tại).

### D-21 — API Specification
Đặc tả API — endpoint và schema request/response. Tùy chọn. Phạm vi: dual — baseline ở `shared/api/`, có thể ghi đè per-feature tại `features/<feature>/planning-artifacts/` (bản override thắng nếu tồn tại).

### D-26 — Test Plan ✅
Kế hoạch test — chiến lược, phạm vi, lịch, tiêu chí vào/ra (entry/exit) và đánh giá rủi ro. Phạm vi: per-feature → `features/<feature>/planning-artifacts/`.

### D-27 — Test Specification ✅
Test case chi tiết với các **`TC-NNN` ID** (đánh số tuần tự **trong từng tính năng**), từng bước và kết quả mong đợi. Là nguồn để viết test trong TDD ở Phase 3. Phạm vi: per-feature → `features/<feature>/planning-artifacts/`.

## Artifact không đánh mã D-xx

| Artifact | Phase | Skill | Nơi lưu |
| --- | --- | --- | --- |
| Task Breakdown | 3 · Implementation | `TB` | `features/<feature>/implementation-artifacts/` |
| Code (TDD) | 3 · Implementation | `IM` | `features/<feature>/implementation-artifacts/` |
| Test Execution Report | 4 · Testing | `TE` | `features/<feature>/implementation-artifacts/` |
| Acceptance Report | 4 · Testing | `AC` | `features/<feature>/implementation-artifacts/` |
| Phase Gate Report | xuyên suốt | `PG` | `features/<feature>/gates/` |
| Traceability Matrix | xuyên suốt | `TRI`/`TRU` | `features/<feature>/traceability/` |

> Cột ma trận traceability — nay **8 cột**: `feature` / `req_id` / `story_id` / `design_ref` / `code_ref` / `test_ref` / `gate_status` / `timestamp`. Coverage tính theo `design_ref` / `code_ref` / `test_ref`. Ma trận theo từng tính năng; `TRR` có thể roll-up đa tính năng (hàng shared chỉ tính một lần).

## Liên quan

- 📖 Tra **khái niệm** (không phải mã): [Glossary khái niệm](concept-glossary.md).
- 📖 Danh sách skill đầy đủ kèm mô tả & thứ tự: [Catalog skill](skills-catalog.md).
- 🗺️ Xem deliverable nằm ở đâu trong quy trình: [Bản đồ quy trình](../tutorials/workflow-map.md).
