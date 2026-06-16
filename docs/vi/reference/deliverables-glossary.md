# Bảng tra deliverable (D-xx)

> 🌐 [English](../../en/reference/deliverables-glossary.md) · **Tiếng Việt**
>
> 📖 **Reference** — tra cứu nhanh mọi deliverable HBC sinh ra. Muốn hiểu *deliverable là gì / vì sao đánh mã*, xem [Khái niệm cốt lõi](../explanation/concepts.md).

Mã `D-xx` thuộc bộ tài liệu chuẩn của HBLAB. HBC hiện sinh **8 tài liệu D-xx** sau, cộng một số artifact không đánh mã D (task breakdown, báo cáo test, gate, ma trận traceability).

## Tài liệu D-xx

> Cột **Bắt buộc**: ✅ = bắt buộc (điều kiện qua Phase Gate) · `—` = tùy chọn.

| Mã | Tên | Phase | Skill | Bắt buộc | Nơi lưu |
| --- | --- | --- | --- | :---: | --- |
| **D-02** | Requirements Specification | 1 · Analysis | `REQ` | ✅ | `planning_artifacts` |
| **D-03** | Glossary | 1 · Analysis | `GLO` | — | `planning_artifacts` |
| **D-06** | Business Flow Diagram (AS-IS/TO-BE) | 1 · Analysis | `BFD` | — | `planning_artifacts` |
| **D-12** | Coding Standards | 2 · Design | `CS` | ✅ | `planning_artifacts` |
| **D-19** | Database Design / ER Diagram | 2 · Design | `ERD` | ✅ | `planning_artifacts` |
| **D-21** | API Specification | 2 · Design | `API` | — | `planning_artifacts` |
| **D-26** | Test Plan | 2 · Design | `TP` | ✅ | `planning_artifacts` |
| **D-27** | Test Specification | 2 · Design | `TS` | ✅ | `planning_artifacts` |

> 📌 Các mã bị "khuyết" (D-01, D-04, D-05…) thuộc bộ chuẩn HBLAB rộng hơn nhưng **không** do HBC sinh ra — đừng nhầm là thiếu sót.

## Chi tiết từng tài liệu

### D-02 — Requirements Specification ✅
Đặc tả yêu cầu với các **REQ-xxx ID** và ranh giới phạm vi. Là nền của mọi phase sau và là nguồn để khởi tạo traceability (`TRI`).

### D-03 — Glossary
Thuật ngữ miền nghiệp vụ thống nhất, tổng hợp từ tài liệu dự án và yêu cầu. Tùy chọn.

### D-06 — Business Flow Diagram
Sơ đồ luồng nghiệp vụ AS-IS / TO-BE bằng Mermaid, dựng từ PRD và planning artifacts. Tùy chọn.

### D-12 — Coding Standards ✅
Quy chuẩn code theo từng dự án — đặt tên, format, xử lý lỗi — điều chỉnh theo framework đang dùng.

### D-19 — Database Design / ER Diagram ✅
Tài liệu thiết kế CSDL kèm ER Diagram (Mermaid), suy ra từ yêu cầu và kiến trúc.

### D-21 — API Specification
Đặc tả API — endpoint và schema request/response. Tùy chọn.

### D-26 — Test Plan ✅
Kế hoạch test — chiến lược, phạm vi, lịch, tiêu chí vào/ra (entry/exit) và đánh giá rủi ro.

### D-27 — Test Specification ✅
Test case chi tiết với các **TC-xxx ID**, từng bước và kết quả mong đợi. Là nguồn để viết test trong TDD ở Phase 3.

## Artifact không đánh mã D-xx

| Artifact | Phase | Skill | Nơi lưu |
| --- | --- | --- | --- |
| Task Breakdown | 3 · Implementation | `TB` | `implementation_artifacts` |
| Code (TDD) | 3 · Implementation | `IM` | `implementation_artifacts` |
| Test Execution Report | 4 · Testing | `TE` | `implementation_artifacts` |
| Acceptance Report | 4 · Testing | `AC` | `implementation_artifacts` |
| Phase Gate Report | xuyên suốt | `PG` | `{output_folder}/gates` |
| Traceability Matrix | xuyên suốt | `TRI`/`TRU` | `{output_folder}/traceability` |

> Cột ma trận traceability: `design_ref` / `code_ref` / `test_ref` / `gate_status`.

## Liên quan

- 📖 Tra **khái niệm** (không phải mã): [Glossary khái niệm](concept-glossary.md).
- 📖 Danh sách skill đầy đủ kèm mô tả & thứ tự: [Catalog skill](skills-catalog.md).
- 🗺️ Xem deliverable nằm ở đâu trong quy trình: [Bản đồ quy trình](../tutorials/workflow-map.md).
