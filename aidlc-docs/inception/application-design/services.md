# Services — hbc-sync

hbc-sync chỉ có một service layer chính (orchestration), vì đây là một skill đơn nhiệm. Service điều phối các component theo flow tuyến tính.

## S-01: SyncOrchestrationService

**Purpose**: Service chính điều phối toàn bộ cascade flow từ change detection đến traceability sync.

**Responsibilities**:
- Khởi tạo và phối hợp các component (C-01 → C-08)
- Quản lý flow tổng thể + error handling
- Định tuyến giữa interactive và headless mode

**Orchestration Flow (Interactive)**:
```
1. StateManager.is_interrupted()
   ├── Yes → offer resume (load_state) / restart
   └── No  → fresh start
2. DependencyGraphLoader.load_graph() + validate
3. ChangeDetector.detect_changes(graph, user_input)
4. ImpactAnalyzer.analyze(graph, changeset)
5. SelectionPresenter.present(impact_report) → user selects
6. CascadeOrchestrator.orchestrate(selection, changeset):
   for each doc in topological order:
     a. save_state (resume point)
     b. classify_change → mechanical | semantic
     c. if semantic → ask user; if mechanical → auto
     d. invoke_skill(skill, "update", context)
     e. if doc == Code → CodeCascadeStrategist.suggest_code_strategy()
     f. accumulate result into context
7. TraceabilitySyncTrigger.sync_traceability() (if selected)
8. StateManager.clear_state()
9. Report cascade summary
```

**Orchestration Flow (Headless)**:
```
1. HeadlessContract.parse_args() → config (--changed doc)
2. load_graph + validate
3. detect_changes (changed doc from args)
4. analyze → auto-select ALL affected
5. orchestrate:
   - mechanical changes → auto-apply
   - semantic changes → return blocked + reason (no human available)
6. sync_traceability (headless)
7. build_result → return JSON
```

## Service Interaction Patterns

| Pattern | Description |
|---------|-------------|
| Sequential orchestration | Components gọi tuần tự theo flow, không parallel |
| Delegation | Skill invocation delegate hoàn toàn cho skill tương ứng (không tự sửa) |
| State checkpoint | Lưu state trước mỗi skill call để resume |
| Fail-stop | Nếu một skill fail → dừng cascade, giữ state, báo user |

## Trigger Integration (REQ-005)

| Trigger Mode | Entry Point |
|--------------|-------------|
| Manual | User gọi `hbc-sync` / menu [SYNC] → SyncOrchestrationService (interactive) |
| Hybrid | Existing skill handoff suggest → user xác nhận → SyncOrchestrationService |
| Auto-chained | Existing skill (config `auto_sync_after_update=true`) → headless call |
