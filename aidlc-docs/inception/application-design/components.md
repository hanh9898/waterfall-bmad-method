# Components — hbc-sync

## Overview
hbc-sync gồm các component logic phối hợp để thực hiện cascade document synchronization. Skill tuân theo orchestrator pattern: KHÔNG tự sửa nội dung tài liệu, mà điều phối gọi skill tương ứng.

## Component List

### C-01: DependencyGraphLoader
- **Purpose**: Load và parse dependency graph từ `assets/dependency-graph.yaml`
- **Responsibilities**:
  - Đọc graph definition (nodes = documents, edges = dependencies)
  - Validate graph (no cycles, valid skill mappings)
  - Resolve config overrides từ customize.toml
- **Interface**: `load_graph(path) -> Graph`

### C-02: ChangeDetector
- **Purpose**: Xác định tài liệu nào vừa thay đổi (điểm bắt đầu cascade)
- **Responsibilities**:
  - Auto-detect: so sánh frontmatter `updated` timestamp / hash
  - Nhận user-provided change description (free-text context)
  - Kết hợp cả hai (REQ-006, Q6=C)
- **Interface**: `detect_changes(graph, user_input) -> ChangeSet`

### C-03: ImpactAnalyzer
- **Purpose**: Phân tích tác động — traverse DAG từ changed nodes xuống descendants
- **Responsibilities**:
  - **Topological traversal** trên DAG (không phải tree walk) — toàn bộ downstream (full cascade)
  - Xử lý shared nodes đúng cách: một node có nhiều parents chỉ update MỘT lần, sau khi TẤT CẢ parents đã xử lý
  - Gán impact level (high/medium/low) cho mỗi affected document
  - Tạo rationale cho mỗi impact
- **Interface**: `analyze(graph, changeset) -> ImpactReport`

### C-04: SelectionPresenter
- **Purpose**: Hiển thị impact report và thu thập lựa chọn user
- **Responsibilities**:
  - Render tree view (highlight affected nodes) + table chi tiết (Q4=C)
  - Thu thập user selection (tài liệu nào update)
  - Interactive mode only — headless tự select all
- **Interface**: `present(impact_report) -> SelectionResult`

### C-05: CascadeOrchestrator
- **Purpose**: Điều phối gọi skill tương ứng theo thứ tự dependency
- **Responsibilities**:
  - Sắp xếp affected documents theo topological order
  - Gọi skill tương ứng ở mode `update` (LLM-orchestrated, Q3=C)
  - Truyền context: original change + kết quả update trước đó
  - Stop/ask logic: cơ học → auto, ngữ nghĩa → hỏi user (REQ-007)
- **Interface**: `orchestrate(selection, changeset) -> CascadeResult`

### C-06: StateManager
- **Purpose**: Quản lý cascade state để resume khi interrupted
- **Responsibilities**:
  - Ghi `.sync-state.json` (Q2=A) trước mỗi skill invocation
  - Detect interrupted cascade khi khởi động lại
  - Clear state khi cascade hoàn thành
- **Interface**: `save_state(state)`, `load_state() -> State|None`, `clear_state()`

### C-07: CodeCascadeStrategist
- **Purpose**: Quyết định strategy khi cascade chạm code level (REQ-008)
- **Responsibilities**:
  - Phân loại scope thay đổi (nhỏ/trung bình/lớn)
  - Suggest strategy: flag task / tạo task mới / re-run breakdown
  - Delegate cho hbc-implement hoặc hbc-task-breakdown
- **Interface**: `suggest_code_strategy(change_scope) -> CodeStrategy`

### C-08: TraceabilitySyncTrigger
- **Purpose**: Gọi hbc-traceability update sau khi cascade xong (REQ-009)
- **Responsibilities**:
  - Trigger `hbc-traceability update` nếu user chọn
  - Delegate hoàn toàn (single responsibility)
- **Interface**: `sync_traceability() -> TraceResult`

### C-09: HeadlessContract
- **Purpose**: Xử lý headless mode (REQ-006)
- **Responsibilities**:
  - Parse `--headless` / `--changed` args
  - Skip user interaction, auto-select all
  - Return JSON result schema
  - Return `blocked` khi semantic change cần human judgment
- **Interface**: `run_headless(args) -> JSON`
