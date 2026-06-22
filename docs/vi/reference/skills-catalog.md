# Catalog skill HBC

> 🌐 [English](../../en/reference/skills-catalog.md) · **Tiếng Việt**
>
> 📖 **Reference** — danh sách đầy đủ mọi agent và skill. Mới dùng? Đừng học thuộc bảng này — bắt đầu từ [Bắt đầu với HBC](../tutorials/getting-started-hbc.md).

Gọi skill bằng **menu code** (vd `REQ`), **tên skill** (`hbc-create-requirements`), hoặc qua **agent**. Mỗi skill workflow hỗ trợ 3 chế độ **Create / Update / Validate**; phần lớn có `--headless` / `-H` để chạy không tương tác.

HBC giao **tăng dần theo từng tính năng** (incremental per-feature delivery): mỗi tính năng đi qua 4 phase có cổng kiểm soát + TDD rồi ship độc lập. Trước đó **Phase 0 là bắt buộc và chạy đầu tiên** một lần cho toàn dự án (hoặc chạy lại để cập nhật trực tiếp). Mỗi skill có **phạm vi** (scope):

- **per-feature** — chạy cho từng tính năng, output vào `_bmad-output/features/<feature>/...`; ở chế độ headless bắt buộc truyền `feature=<slug>` (thiếu sẽ bị chặn `feature_required`).
- **shared** — tài liệu dùng chung toàn dự án, output vào `_bmad-output/shared/...`; không cần `feature`.
- **dual** — có bản baseline dùng chung ở `shared/...` và có thể ghi đè per-feature ở `features/<feature>/...`; **bản ghi đè thắng nếu tồn tại** (path-existence precedence). Headless: `feature` không bắt buộc.

## Agent điều phối

| Code | Skill | Vai trò |
| --- | --- | --- |
| `BA` | `hbc-agent-ba` | Điều phối Phase 1 Analysis — dẫn dắt elicitation yêu cầu, tạo glossary, vẽ business flow. |
| `ARCH` | `hbc-agent-architect` | Điều phối Phase 2 Design — kiến trúc (D-09), thiết kế DB (D-19), coding standards, API spec, thiết kế hành vi (D-16), UX (D-14). |
| `QA` | `hbc-agent-qa` | Điều phối Phase 2 Test Design — tạo test plan và test case. |
| `DEV` | `hbc-agent-dev` | Điều phối Phase 3 Implementation — task breakdown và TDD. |
| `TST` | `hbc-agent-tester` | Điều phối Phase 4 Testing — chạy test, triage defect, quyết định nghiệm thu. |

## Phase 0 — Project Init

**Bắt buộc và chạy đầu tiên**, một lần cho toàn dự án, **trước mọi tính năng** (hoặc chạy lại để cập nhật trực tiếp các deliverable dùng chung). Không có `feature` arg. `PI` **nhận biết brownfield**: với codebase đã có, nó tài liệu hoá code trước (`bmad-document-project` + `project-context.md`) rồi suy ra các deliverable dùng chung từ đó; với greenfield thì suy ra từ PRD/lựa chọn. **D-12 Coding Standards và D-03 Glossary là deliverable dùng chung (shared) sinh ở Phase 0.**

| Code | Skill | Mô tả | Deliverable | Phạm vi |
| --- | --- | --- | --- | --- |
| `PI` | `hbc-project-init` | Bắt buộc, chạy đầu tiên. Brownfield: tài liệu hoá code (`bmad-document-project` + `project-context.md`) rồi suy ra deliverable dùng chung; greenfield: suy ra từ PRD/lựa chọn. Tạo các shared deliverable: D-12 Coding Standards, D-03 Glossary, và baseline D-19 ERD / D-21 API | D-12, D-03, baseline D-19/D-21 | shared |
| `MIG` | `hbc-migrate` | Đưa dự án **HBC v1 (layout phẳng)** lên v2 (per-feature + shared): dịch chuyển file, đổi tiền tố REQ/TC, dựng lại ma trận 8 cột. `MIG plan` = dry-run xem trước → `MIG apply feature=<slug>`. Xem [Migrate từ v1 lên v2](../how-to/migrate-from-v1.md) | layout v2 + ma trận 8 cột | v1→v2 migration, chạy một lần |

Output: `_bmad-output/shared/{coding-standards, glossary, erd, api}/`.

## Phase 1 — Analysis

| Code | Skill | Mô tả | Deliverable | Phạm vi | Bắt buộc |
| --- | --- | --- | --- | --- | :---: |
| `REQ` | `hbc-create-requirements` | Sinh đặc tả yêu cầu với REQ-<FEAT>-NNN ID và ranh giới phạm vi | D-02 | per-feature | ✅ |
| `GLO` | `hbc-create-glossary` | Duy trì **D-03 dùng chung** (đã khởi tạo ở Phase 0) — thuật ngữ miền thống nhất từ tài liệu dự án & yêu cầu | D-03 | shared | — |
| `BFD` | `hbc-create-business-flow-diagram` | Sơ đồ luồng nghiệp vụ AS-IS/TO-BE (Mermaid) từ PRD | D-06 | per-feature | ✅ |
| `DSC` | `hbc-discovery-spike` | Kiểm chứng rẻ giả định model rủi ro nhất so với ground-truth TRƯỚC khi thiết kế — verdict VALIDATED/RESHAPE/KILL kèm USER sign-off | discovery-note | per-feature | ◑ |

> ◑ **`DSC` theo điều kiện:** chỉ chạy khi D-02 có `discovery_risk: uncertain` (model/giả định chưa chứng). Khi đó gate Phase 1 (**P1-11**) đòi một discovery-note **VALIDATED đã ký**. `known`/vắng → N/A. Là remediation cho lỗi gốc RCA "model gate PASSED trước khi kiểm chứng".

Output per-feature: `_bmad-output/features/<feature>/planning-artifacts/`. Output shared: `_bmad-output/shared/glossary/`.

## Phase 2 — Design (ARCH) + Test Design (QA)

> Cột **Bắt buộc**: ✅ = luôn bắt buộc · ◑ = **bắt buộc theo facet** (applicability-catalog quyết định per-feature) · `—` = tùy chọn.

| Code | Skill | Mô tả | Deliverable | Phạm vi | Bắt buộc |
| --- | --- | --- | --- | --- | :---: |
| `AD` | `hbc-create-architecture` | Thiết kế kiến trúc / giải pháp + ADR (quyết định kèm lý do) | D-09 | per-feature | ◑ |
| `ERD` | `hbc-create-er-diagram` | Thiết kế CSDL + ER Diagram (Mermaid) từ yêu cầu & kiến trúc | D-19 | dual | ✅ |
| `CS` | `hbc-create-coding-standards` | Duy trì **D-12 dùng chung** (đã khởi tạo ở Phase 0) — coding standards theo dự án, điều chỉnh theo framework | D-12 | shared | ✅ |
| `API` | `hbc-create-api-spec` | Đặc tả API — endpoint và schema request/response | D-21 | dual | — |
| `BD` | `hbc-create-behavioral-design` | Đặc tả hành vi phi-CRUD: state-machine (ST), decision-rule (DR), invariant (INV), sequence (SEQ) | D-16 | per-feature | ◑ |
| `UX` | `hbc-create-ux` | Thiết kế UX/màn hình (SCR/CMP); tùy chọn token Claude Design (`DESIGN.md`) | D-14 | per-feature | ◑ |
| `TP` | `hbc-create-test-plan` | Test plan — chiến lược, phạm vi, lịch, tiêu chí vào/ra, rủi ro | D-26 | per-feature | ✅ |
| `TS` | `hbc-create-test-spec` | Test case chi tiết với TC-xxx ID, các bước & kết quả mong đợi | D-27 | per-feature | ✅ |
| `IR` | `hbc-check-implementation-readiness` | Cổng kiểm tra sẵn sàng (readiness seam gate) — đối chiếu D-02 ↔ D-21/D-26/D-27 + ma trận truy vết trước khi đóng Phase 2 | readiness-report | per-feature | ✅ |

> ◑ **Theo facet:** D-09 required nếu `has-integration`/`has-algorithm`; D-16 required nếu facet phi-CRUD (state-machine/cross-entity-sync/invariant/algorithm/concurrency); D-14 required nếu `has-ui`. Ngoài ra → optional/N-A, không chặn gate. Nguồn: `src/hbc-shared/references/deliverable-catalog.yaml`.

Output per-feature (AD/BD/UX/TP/TS/IR): `features/<feature>/planning-artifacts/`. Output dual (ERD/API): baseline `shared/erd|api/` + ghi đè tuỳ chọn `features/<feature>/planning-artifacts/`. Output shared (CS): `shared/coding-standards/`.

## Phase 3 — Implementation

TDD mềm: `IM` chạy RED→GREEN→REFACTOR; phải ghi nhận **bằng chứng RED** (test fail trước khi viết code) — cổng Phase 3 kiểm tra bằng chứng RED.

| Code | Skill | Mô tả | Args | Phạm vi | Bắt buộc |
| --- | --- | --- | --- | --- | :---: |
| `TB` | `hbc-task-breakdown` | Chia design thành task TDD nhỏ, sắp thứ tự phụ thuộc, gán test case | `create\|update\|validate -H` | per-feature | ✅ |
| `IM` | `hbc-implement` | Lập trình theo chu trình TDD (RED-GREEN-REFACTOR) theo từng task | `task TASK-xxx \| all \| coverage -H` | per-feature | ✅ |

Output: `_bmad-output/features/<feature>/implementation-artifacts/`.

## Phase 4 — Testing

| Code | Skill | Mô tả | Args | Phạm vi | Bắt buộc |
| --- | --- | --- | --- | --- | :---: |
| `TE` | `hbc-test-execution` | Chạy test suite, thu kết quả, phân loại lỗi, sinh báo cáo | `all \| unit \| integration \| e2e \| report -H` | per-feature | ✅ |
| `AC` | `hbc-acceptance-check` | Đánh giá nghiệm thu cuối — ship một tính năng độc lập; ACCEPTED/REJECTED/DEFERRED/PENDING | `review \| status -H` | per-feature | ✅ |

Output: `_bmad-output/features/<feature>/implementation-artifacts/`.

## Xuyên suốt — Phase Gate & Traceability

| Code | Skill | Mô tả | Args | Phạm vi |
| --- | --- | --- | --- | --- |
| `PG` | `hbc-phase-gate` | Validate hoàn thành phase (1–4) theo checklist — deterministic + LLM, báo PASSED/FAILED; mang theo `feature=` | `1\|2\|3\|4 -H` | per-feature |
| `TRI` | `hbc-traceability` (init) | Tạo ma trận 8 cột từ REQ-<FEAT>-NNN ID của D-02. Chạy một lần sau khi chốt yêu cầu | `-H` | per-feature |
| `TRU` | `hbc-traceability` (update) | Điền cột `design_ref`/`code_ref`/`test_ref`/`gate_status` khi mỗi phase xong | `-H` | per-feature |
| `TRR` | `hbc-traceability` (report) | Báo cáo coverage — bao nhiêu REQ ID có chuỗi truy vết đầy đủ; có thể roll up xuyên feature | `-H` | per-feature + rollup |
| `TRA` | `hbc-traceability` (audit) | Phát hiện gap và phân loại mức nghiêm trọng cho link truy vết thiếu | `-H` | per-feature |
| `SYNC` | `hbc-traceability` (impact) | **Đồng bộ lan truyền (Cascade Sync)** — phân tích tác động khi một tài liệu nguồn thay đổi, đề xuất cập nhật lan truyền xuống docs/test/code downstream (read-only) | `<change> \| --since <ref> -H` | per-feature |
| `RBL` | `hbc-rebaseline` | **Re-baseline xuyên feature** — khi một model lõi/shared đổi sau Phase 3, tính **blast-radius** (feature/artifact nào stale) bằng build-graph rollup, lập kế hoạch re-baseline per-feature, ghi nhận **epic/baseline-change** ở cấp TRÊN feature; dry-run → apply, idempotent. Engine RIÊNG, không phải mở rộng `MIG` | `plan \| apply changed=<model.token> -H` | cross-feature (baseline-change) |

Ma trận truy vết 8 cột: `feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp`. Coverage đếm `design_ref`/`code_ref`/`test_ref`. Output: `_bmad-output/features/<feature>/traceability/`; gate: `features/<feature>/gates/`.

## Thứ tự thực thi đề xuất

```
PI                                      (một lần, đầu tiên — shared D-12/D-03 + baseline D-19/D-21)
BA → REQ → GLO → BFD → (DSC) → TRI → PG 1   (DSC chỉ khi discovery_risk=uncertain; GLO dùng chung từ Phase 0)
ARCH → (AD) → ERD → CS → (API) → (BD) → (UX) ┐   (AD/BD/UX/API theo facet — bỏ qua nếu N/A)
QA   → TP   → TS                             ┘ → IR → TRU → PG 2
DEV  → TB  → IM         → TRU → PG 3
TST  → TE  → AC         → TRA → PG 4
```

> 💡 `bmad-help` luôn gợi ý bước tiếp theo dựa trên trạng thái dự án — không cần nhớ thứ tự này.

## Liên quan

- 📖 Tra mã & nội dung deliverable: [Bảng deliverable D-xx](deliverables-glossary.md).
- 🗺️ Toàn cảnh quy trình: [Bản đồ quy trình](../tutorials/workflow-map.md).
