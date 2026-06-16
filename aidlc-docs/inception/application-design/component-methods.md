# Component Methods — hbc-sync

> Note: Detailed business rules sẽ được định nghĩa trong Functional Design (CONSTRUCTION phase).

## C-01: DependencyGraphLoader

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `load_graph(path)` | yaml path | Graph object | Parse YAML graph definition |
| `validate_graph(graph)` | Graph | ValidationResult | Check no cycles, valid skill mappings |
| `resolve_skill(doc_id)` | document id | skill name | Map document → skill (e.g. D-27 → hbc-create-test-spec) |

## C-02: ChangeDetector

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `detect_by_timestamp(graph)` | Graph | list[doc_id] | Tài liệu có `updated` mới hơn downstream |
| `parse_user_change(text)` | free-text | ChangeContext | Trích thông tin ngữ nghĩa từ mô tả user |
| `detect_changes(graph, input)` | Graph, input | ChangeSet | Kết hợp auto-detect + user context |

## C-03: ImpactAnalyzer

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `traverse_downstream(graph, roots)` | Graph, changed nodes | list[doc_id] | DAG topological traversal (descendants) |
| `assess_impact_level(doc, change)` | doc, change | high/med/low | Đánh giá mức tác động |
| `dedupe_shared_nodes(nodes)` | list[doc_id] | ordered list | Shared node update 1 lần, sau khi mọi parent xong |
| `analyze(graph, changeset)` | Graph, ChangeSet | ImpactReport | Tổng hợp impact report + rationale |

## C-04: SelectionPresenter

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `render_tree(impact_report)` | ImpactReport | ascii tree | Tree view highlight affected nodes |
| `render_table(impact_report)` | ImpactReport | md table | Bảng chi tiết (doc, level, reason, skill) |
| `collect_selection(report)` | ImpactReport | SelectionResult | Thu thập lựa chọn user (check/uncheck) |

## C-05: CascadeOrchestrator

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `order_by_dependency(selection)` | SelectionResult | ordered list | Sắp xếp theo topological order |
| `invoke_skill(skill, mode, context)` | skill, mode, ctx | SkillResult | Gọi skill ở mode update với context |
| `classify_change(doc, change)` | doc, change | mechanical/semantic | Quyết định auto hay stop-ask |
| `orchestrate(selection, changeset)` | selection, changeset | CascadeResult | Vòng lặp cascade chính |

## C-06: StateManager

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `save_state(state)` | State | void | Ghi `.sync-state.json` |
| `load_state()` | - | State \| None | Đọc state nếu interrupted |
| `clear_state()` | - | void | Xóa state khi hoàn thành |
| `is_interrupted()` | - | bool | Check có cascade dở dang không |

## C-07: CodeCascadeStrategist

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `classify_scope(change)` | ChangeContext | small/medium/large | Phân loại độ lớn thay đổi |
| `suggest_code_strategy(scope)` | scope | CodeStrategy | flag / new-task / re-breakdown |

## C-08: TraceabilitySyncTrigger

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `sync_traceability()` | - | TraceResult | Gọi hbc-traceability update |

## C-09: HeadlessContract

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `parse_args(argv)` | cli args | HeadlessConfig | Parse --headless, --changed |
| `run_headless(config)` | HeadlessConfig | JSON | Chạy non-interactive, return JSON |
| `build_result(cascade)` | CascadeResult | JSON | Build result schema |
