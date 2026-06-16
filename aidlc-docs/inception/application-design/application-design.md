# Application Design — hbc-sync (Consolidated)

## 1. Design Overview

hbc-sync là một **orchestrator skill** thực hiện cascade document synchronization cho HBC workflow. Nguyên tắc thiết kế cốt lõi: **single responsibility** — skill chỉ điều phối, không tự sửa nội dung tài liệu; mỗi skill downstream tự update phần của mình.

> **Điều chỉnh sau Reverse Engineering**: Dependency giữa documents là **DAG with shared nodes** (không phải tree). D-27 có parents [D-02, D-26]; task-breakdown có parents [D-19, D-27]; Code có parents [D-12, D-27, task-breakdown]. Traversal dùng **topological sort**, shared node chỉ update một lần sau khi mọi parent đã xử lý.

### Design Decisions (từ application-design-plan.md)
| # | Decision | Choice |
|---|----------|--------|
| Q1 | Dependency graph format | YAML (`assets/dependency-graph.yaml`) |
| Q2 | Cascade state persistence | `.sync-state.json` |
| Q3 | Skill invocation | Hybrid (script parse + LLM orchestration) |
| Q4 | Impact output format | Tree view + table |
| Q5 | Existing skill modification | Handoff suggest + config flag |
| Q6 | Change description input | Auto-detect + user context |

## 2. Components (chi tiết: components.md)

| ID | Component | Role |
|----|-----------|------|
| C-01 | DependencyGraphLoader | Load/validate dependency graph |
| C-02 | ChangeDetector | Xác định tài liệu vừa đổi |
| C-03 | ImpactAnalyzer | Full cascade traversal + impact level |
| C-04 | SelectionPresenter | Tree + table, thu thập user selection |
| C-05 | CascadeOrchestrator | Điều phối gọi skill theo thứ tự |
| C-06 | StateManager | Resume state qua `.sync-state.json` |
| C-07 | CodeCascadeStrategist | Strategy khi cascade chạm code |
| C-08 | TraceabilitySyncTrigger | Gọi hbc-traceability update |
| C-09 | HeadlessContract | Non-interactive mode + JSON |

## 3. Service Layer (chi tiết: services.md)
- **S-01 SyncOrchestrationService** — service chính điều phối flow tuyến tính: detect → analyze → select → cascade → traceability.

## 4. Dependencies (chi tiết: component-dependency.md)
- Internal: DAG component dependencies, no cycles
- External: delegation tới 11 skill nodes qua graph config (loose coupling)

## 5. Skill Structure (theo BMad convention)
```
src/hbc-sync/
├── SKILL.md                       # Main skill definition (5-stage workflow)
├── customize.toml                 # Config: graph path, skill mappings, trigger defaults
├── assets/
│   └── dependency-graph.yaml      # Default document dependency tree
├── scripts/
│   ├── load-graph.py              # Parse + validate graph (no cycles)
│   ├── analyze-impact.py          # Topological traversal → affected set
│   └── sync-state.py              # State save/load/clear
└── references/
    └── headless-contract.md       # Headless input args + JSON return schema
```

## 6. Testable Properties (PBT-01, Partial mode preview)

Theo PBT extension (Partial mode — enforce PBT-02, 03, 07, 08, 09), các property sau được xác định cho Functional Design:

| Component | Property | Category | PBT Rule |
|-----------|----------|----------|----------|
| C-01 graph validation | Graph hợp lệ luôn là DAG (no cycle) | Invariant | PBT-03 |
| C-03 ImpactAnalyzer | Affected set đóng dưới quan hệ dependency (downstream closure) | Invariant | PBT-03 |
| C-03 traversal | Topological order: parent luôn đứng trước child | Invariant | PBT-03 |
| C-06 StateManager | save→load state = identity (round-trip JSON) | Round-trip | PBT-02 |
| Generators | Random valid graph (DAG) generator cho test | Generator quality | PBT-07 |

Chi tiết sẽ hoàn thiện trong Functional Design.

## 7. Out of Scope (xác nhận lại)
- Tự sửa nội dung tài liệu (delegate cho skill tương ứng)
- Tạo tài liệu mới
- Phase gate validation
- Git/version control operations
