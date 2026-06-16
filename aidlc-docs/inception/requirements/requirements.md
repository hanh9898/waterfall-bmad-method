# Requirements Specification — hbc-sync (Cascade Document Synchronization)

## 1. Project Background

### Problem Statement
Workflow HBLAB BMad Custom hiện tại là one-way: tài liệu được generate theo thứ tự phase (D-02 → D-19 → D-27 → Task Breakdown → Code). Khi một tài liệu upstream thay đổi, KHÔNG có cơ chế tự động propagate thay đổi xuống các tài liệu downstream. Dẫn đến tài liệu lệch nhau, test spec không khớp requirements, code không khớp design.

### Solution
Skill **hbc-sync** — orchestrator cascade update. Khi user thay đổi bất kỳ tài liệu nào, hbc-sync phân tích dependency tree, suggest tài liệu bị ảnh hưởng, user confirm, rồi lần lượt gọi skill tương ứng ở mode `update` để đồng bộ toàn bộ chain.

### Stakeholders
- Developer team sử dụng HBC workflow
- QA team cần test spec luôn khớp requirements
- BA team cần đảm bảo requirements cascade đúng

## 2. Scope

### In-Scope
- REQ-001: Dependency tree analysis giữa các tài liệu HBC
- REQ-002: Impact analysis khi một tài liệu thay đổi
- REQ-003: User interaction — suggest + confirm affected documents
- REQ-004: Sequential cascade orchestration (gọi skill tương ứng)
- REQ-005: Triple trigger mechanism (auto-chained, manual, hybrid)
- REQ-006: Headless mode (non-interactive) cho CI/CD hoặc skill-to-skill call
- REQ-007: Intelligent stop/ask logic (cơ học → auto, ngữ nghĩa → hỏi)
- REQ-008: Code-level cascade handling (suggest strategy per case)
- REQ-009: Traceability integration (delegate cho hbc-traceability)

### Out-of-Scope
- Tự trực tiếp sửa nội dung tài liệu (delegate cho skill tương ứng)
- Tạo tài liệu mới (chỉ update existing)
- Phase gate validation (đó là hbc-phase-gate)
- Version control / git operations

## 3. User Roles

| Role | Description |
|------|-------------|
| Developer | Thay đổi design/code, cần sync lại tài liệu liên quan |
| BA | Thay đổi requirements, cần cascade xuống design + test |
| QA | Thay đổi test spec, cần sync lại task breakdown |
| Orchestrator Skill | Skill khác gọi hbc-sync ở headless mode sau khi update |

## 4. Functional Requirements

### REQ-001: Dependency Graph Analysis
- Maintain một dependency graph giữa các tài liệu HBC
- **Graph là DAG (Directed Acyclic Graph) with shared nodes** — KHÔNG phải tree thuần (xác nhận qua Reverse Engineering: D-27 và task-breakdown.md có nhiều parents)
- Graph structure (DAG):
  ```
  D-02 (Requirements) ─┬─> D-03 (Glossary)
                       ├─> D-06 (Business Flow) ──> D-26 (Test Plan) ─┐
                       ├─> D-19 (Database/ER) ─┬─> D-21 (API Spec)    │
                       │                       ├─> D-12 (Coding Std) ─┼─> Code
                       │                       └─> task-breakdown ────┤
                       ├─> D-21 (API Spec)                            │
                       ├─> D-26 (Test Plan)                           │
                       └─> D-27 (Test Spec) <────────────────────────┘
                              ▲ (parents: D-02, D-26)
                       D-27 ──> task-breakdown (parents: D-19, D-27) ──> Code
  ```
- **Shared nodes**: D-27 (parents: D-02, D-26), task-breakdown (parents: D-19, D-27), Code (parents: D-12, D-27, task-breakdown)
- Traversal phải dùng **topological sort** (không phải tree walk) để tránh xử lý trùng node và đảm bảo thứ tự đúng
- Graph configurable qua customize.toml + `assets/dependency-graph.yaml`

### REQ-002: Impact Analysis
- Khi user mô tả thay đổi, AI đọc:
  - Tài liệu nguồn (vừa bị thay đổi)
  - Dependency graph
  - Nội dung hiện tại của downstream documents
- Output: danh sách tài liệu bị ảnh hưởng + lý do + mức độ (high/medium/low impact)
- Full cascade — traverse toàn bộ tree từ điểm thay đổi xuống leaf nodes

### REQ-003: User Selection Interface
- Hiển thị kết quả impact analysis dạng bảng/tree
- User chọn tài liệu nào sẽ update (check/uncheck)
- Confirm trước khi bắt đầu cascade
- Cho phép thay đổi thứ tự cascade (nếu cần)

### REQ-004: Sequential Cascade Orchestration
- Gọi skill tương ứng ở mode `update` cho từng tài liệu đã chọn
- Thứ tự: theo dependency order (parent trước, child sau)
- Truyền context: thông tin thay đổi gốc + kết quả update trước đó
- Mỗi skill chỉ đảm nhận nhiệm vụ update phần của mình (single responsibility)
- Skill mapping:
  | Document | Skill gọi |
  |----------|-----------|
  | D-02 | hbc-create-requirements update |
  | D-03 | hbc-create-glossary update |
  | D-06 | hbc-create-business-flow-diagram update |
  | D-19 | hbc-create-er-diagram update |
  | D-21 | hbc-create-api-spec update |
  | D-12 | hbc-create-coding-standards update |
  | D-27 | hbc-create-test-spec update |
  | D-26 | hbc-create-test-plan update |
  | task-breakdown.md | hbc-task-breakdown update |
  | Code | hbc-implement (strategy varies) |
  | Traceability | hbc-traceability update |

### REQ-005: Triple Trigger Mechanism
- **Auto-chained**: Sau khi skill khác hoàn thành mode `update`, tự động gọi hbc-sync
- **Manual**: User gọi `hbc-sync` hoặc menu code [SYNC] bất kỳ lúc nào
- **Hybrid**: Skill gợi ý chạy sync sau update, user confirm Y/N
- Tất cả 3 mode cùng tồn tại, configurable mặc định qua customize.toml

### REQ-006: Headless Mode
- Support `--headless` / `-H` flag
- Non-interactive: skip user confirmation, auto-select all affected documents
- Return JSON: `{status, cascade_result[], affected_documents[], skipped[]}`
- Cho phép skill khác gọi headless: `hbc-sync --headless --changed D-02`
- Blocked reasons: khi semantic change requires human judgment → return blocked + reason

### REQ-007: Intelligent Stop/Ask Logic
- **Tự động (không hỏi)**: Thay đổi cơ học
  - ID rename/renumber
  - Field mới được thêm rõ ràng (có đủ thông tin)
  - Structural reorganization không đổi semantics
- **Dừng hỏi user**: Thay đổi ngữ nghĩa
  - Requirements bị xóa hoặc đổi ý nghĩa → hỏi user cách xử lý downstream
  - Ambiguous impact — nhiều cách interpret
  - Conflict detection — downstream document có nội dung contradict với thay đổi
  - Business logic changes cần human judgment

### REQ-008: Code-Level Cascade Strategy
- hbc-sync suggest strategy cho phần code dựa trên loại thay đổi:
  - **Thay đổi nhỏ** (field rename, thêm validation): flag task + suggest quick fix
  - **Thay đổi trung bình** (logic change): tạo task mới trong task-breakdown, delegate cho hbc-implement
  - **Thay đổi lớn** (architecture change): flag toàn bộ affected tasks, recommend re-run task-breakdown
- AI suggest, user confirm strategy trước khi thực hiện

### REQ-009: Traceability Integration
- Sau khi cascade hoàn thành, gọi `hbc-traceability update` để đồng bộ matrix
- Delegate hoàn toàn cho hbc-traceability (single responsibility)
- Nếu user không chọn traceability update → skip, nhưng warn

## 5. Non-Functional Requirements

### NFR-001: Performance
- Impact analysis hoàn thành trong < 30 giây cho project < 50 requirements

### NFR-002: Reliability
- Nếu một skill trong cascade fail, dừng cascade tại điểm đó
- Lưu state (resume point) để có thể tiếp tục sau khi fix
- Không bao giờ corrupt tài liệu đang có

### NFR-003: Extensibility
- Dependency graph configurable — thêm document type mới dễ dàng
- Skill mapping configurable qua customize.toml
- Plugin-friendly: custom skills có thể register vào graph

### NFR-004: Usability
- Communication language: theo `{communication_language}` config
- Output language: theo `{document_output_language}` config
- Progress indicator trong cascade (đang xử lý tài liệu nào, bao nhiêu %)

## 6. Constraints and Assumptions

### Constraints
- Python 3.10+ required (cho scripts)
- Requires BMM installed (BMad Method Module)
- Skill downstream phải support mode `update` (hiện tại tất cả skill đã có)
- Skill downstream phải support `--headless` khi cascade chạy auto

### Assumptions
- Tài liệu output nằm trong `{project-root}/_bmad-output/` (standard HBC layout)
- Mỗi tài liệu có frontmatter với metadata (version, updated timestamp)
- Dependency graph ít thay đổi (mostly static, cấu hình 1 lần)
