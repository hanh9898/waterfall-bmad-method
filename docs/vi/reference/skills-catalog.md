# Catalog skill HBC

> 🌐 [English](../../en/reference/skills-catalog.md) · **Tiếng Việt**
>
> 📖 **Reference** — danh sách đầy đủ mọi agent và skill. Mới dùng? Đừng học thuộc bảng này — bắt đầu từ [Bắt đầu với HBC](../tutorials/getting-started-hbc.md).

Gọi skill bằng **menu code** (vd `REQ`), **tên skill** (`hbc-create-requirements`), hoặc qua **agent**. Mỗi skill workflow hỗ trợ 3 chế độ **Create / Update / Validate**; phần lớn có `--headless` / `-H` để chạy không tương tác.

## Agent điều phối

| Code | Skill | Vai trò |
| --- | --- | --- |
| `BA` | `hbc-agent-ba` | Điều phối Phase 1 Analysis — dẫn dắt elicitation yêu cầu, tạo glossary, vẽ business flow. |
| `ARCH` | `hbc-agent-architect` | Điều phối Phase 2 Design — thiết kế DB, coding standards, API spec. |
| `QA` | `hbc-agent-qa` | Điều phối Phase 2 Test Design — tạo test plan và test case. |
| `DEV` | `hbc-agent-dev` | Điều phối Phase 3 Implementation — task breakdown và TDD. |
| `TST` | `hbc-agent-tester` | Điều phối Phase 4 Testing — chạy test, triage defect, quyết định nghiệm thu. |

## Phase 1 — Analysis

| Code | Skill | Mô tả | Deliverable | Bắt buộc |
| --- | --- | --- | --- | :---: |
| `REQ` | `hbc-create-requirements` | Sinh đặc tả yêu cầu với REQ-xxx ID và ranh giới phạm vi | D-02 | ✅ |
| `GLO` | `hbc-create-glossary` | Thuật ngữ miền thống nhất từ tài liệu dự án & yêu cầu | D-03 | — |
| `BFD` | `hbc-create-business-flow-diagram` | Sơ đồ luồng nghiệp vụ AS-IS/TO-BE (Mermaid) từ PRD | D-06 | — |

## Phase 2 — Design (ARCH) + Test Design (QA)

| Code | Skill | Mô tả | Deliverable | Bắt buộc |
| --- | --- | --- | --- | :---: |
| `ERD` | `hbc-create-er-diagram` | Thiết kế CSDL + ER Diagram (Mermaid) từ yêu cầu & kiến trúc | D-19 | ✅ |
| `CS` | `hbc-create-coding-standards` | Coding standards theo dự án, điều chỉnh theo framework | D-12 | ✅ |
| `API` | `hbc-create-api-spec` | Đặc tả API — endpoint và schema request/response | D-21 | — |
| `TP` | `hbc-create-test-plan` | Test plan — chiến lược, phạm vi, lịch, tiêu chí vào/ra, rủi ro | D-26 | ✅ |
| `TS` | `hbc-create-test-spec` | Test case chi tiết với TC-xxx ID, các bước & kết quả mong đợi | D-27 | ✅ |

## Phase 3 — Implementation

| Code | Skill | Mô tả | Args | Bắt buộc |
| --- | --- | --- | --- | :---: |
| `TB` | `hbc-task-breakdown` | Chia design thành task TDD nhỏ, sắp thứ tự phụ thuộc, gán test case | `create\|update\|validate -H` | ✅ |
| `IM` | `hbc-implement` | Lập trình theo chu trình TDD (RED-GREEN-REFACTOR) theo từng task | `task TASK-xxx \| all \| coverage -H` | ✅ |

## Phase 4 — Testing

| Code | Skill | Mô tả | Args | Bắt buộc |
| --- | --- | --- | --- | :---: |
| `TE` | `hbc-test-execution` | Chạy test suite, thu kết quả, phân loại lỗi, sinh báo cáo | `all \| unit \| integration \| e2e \| report -H` | ✅ |
| `AC` | `hbc-acceptance-check` | Đánh giá nghiệm thu cuối — ACCEPTED/REJECTED/DEFERRED/PENDING | `review \| status -H` | ✅ |

## Xuyên suốt — Phase Gate & Traceability

| Code | Skill | Mô tả | Args |
| --- | --- | --- | --- |
| `PG` | `hbc-phase-gate` | Validate hoàn thành phase (1–4) theo checklist — deterministic + LLM, báo PASSED/FAILED | `1\|2\|3\|4 -H` |
| `TRI` | `hbc-traceability` (init) | Tạo ma trận từ REQ ID của D-02. Chạy một lần sau khi chốt yêu cầu | `-H` |
| `TRU` | `hbc-traceability` (update) | Điền cột `design_ref`/`code_ref`/`test_ref`/`gate_status` khi mỗi phase xong | `-H` |
| `TRR` | `hbc-traceability` (report) | Báo cáo coverage — bao nhiêu REQ ID có chuỗi truy vết đầy đủ | `-H` |
| `TRA` | `hbc-traceability` (audit) | Phát hiện gap và phân loại mức nghiêm trọng cho link truy vết thiếu | `-H` |

## Thứ tự thực thi đề xuất

```
BA → REQ → (GLO, BFD) → TRI → PG 1
ARCH → ERD → CS → (API) ┐
QA   → TP  → TS         ┘ → TRU → PG 2
DEV  → TB  → IM         → TRU → PG 3
TST  → TE  → AC         → TRA → PG 4
```

> 💡 `bmad-help` luôn gợi ý bước tiếp theo dựa trên trạng thái dự án — không cần nhớ thứ tự này.

## Liên quan

- 📖 Tra mã & nội dung deliverable: [Bảng deliverable D-xx](deliverables-glossary.md).
- 🗺️ Toàn cảnh quy trình: [Bản đồ quy trình](../tutorials/workflow-map.md).
