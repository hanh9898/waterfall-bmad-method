# Component Dependency — hbc-sync

## Dependency Matrix

| Component | Depends On | Communication |
|-----------|-----------|---------------|
| S-01 SyncOrchestrationService | C-01..C-09 | Direct method calls |
| C-01 DependencyGraphLoader | (none) | Reads YAML file |
| C-02 ChangeDetector | C-01 (graph) | Reads document frontmatter |
| C-03 ImpactAnalyzer | C-01, C-02 | In-memory graph traversal |
| C-04 SelectionPresenter | C-03 | Renders report, reads user input |
| C-05 CascadeOrchestrator | C-04, C-06, C-07 | Invokes external skills |
| C-06 StateManager | (none) | Reads/writes `.sync-state.json` |
| C-07 CodeCascadeStrategist | C-02 (change context) | Delegates to hbc-implement/task-breakdown |
| C-08 TraceabilitySyncTrigger | (none) | Invokes hbc-traceability |
| C-09 HeadlessContract | S-01 | Wraps orchestration for non-interactive |

## Data Flow Diagram

```
+------------------+     +------------------+     +------------------+
|  ChangeDetector  | --> |  ImpactAnalyzer  | --> | SelectionPresent |
|  (C-02)          |     |  (C-03)          |     | (C-04)           |
+------------------+     +------------------+     +------------------+
        ^                        ^                         |
        |                        |                         v
+------------------+     +------------------+     +------------------+
| DependencyGraph  |     |  YAML graph file |     | CascadeOrchestr  |
| Loader (C-01)    | <-- |  (assets/)       |     | (C-05)           |
+------------------+     +------------------+     +------------------+
                                                          |
                          +-------------------------------+
                          |               |               |
                          v               v               v
                  +-------------+ +-------------+ +-------------+
                  | StateManager| | CodeCascade | | external    |
                  | (C-06)      | | Strategist  | | skills      |
                  | sync-state  | | (C-07)      | | (update)    |
                  +-------------+ +-------------+ +-------------+
                                                          |
                                                          v
                                                  +-------------+
                                                  |Traceability |
                                                  |SyncTrigger  |
                                                  | (C-08)      |
                                                  +-------------+
```

## External Skill Dependencies (Delegation Targets)

hbc-sync KHÔNG phụ thuộc code các skill này — chỉ invoke chúng qua LLM orchestration:

| Document Node | Delegated Skill | Mode |
|---------------|-----------------|------|
| D-02 | hbc-create-requirements | update |
| D-03 | hbc-create-glossary | update |
| D-06 | hbc-create-business-flow-diagram | update |
| D-19 | hbc-create-er-diagram | update |
| D-21 | hbc-create-api-spec | update |
| D-12 | hbc-create-coding-standards | update |
| D-26 | hbc-create-test-plan | update |
| D-27 | hbc-create-test-spec | update |
| task-breakdown.md | hbc-task-breakdown | update |
| Code | hbc-implement | task/all |
| Matrix | hbc-traceability | update |

## Coupling Concerns

- **Loose coupling with skills**: hbc-sync chỉ biết tên skill + mode (qua graph config), không import code → dễ thêm skill mới (NFR-003)
- **No circular dependency**: graph validation đảm bảo DAG (directed acyclic graph)
- **State isolation**: StateManager là component độc lập, không phụ thuộc logic khác
