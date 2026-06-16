# Testable Properties — hbc-sync (PBT)

> PBT Extension: **Partial mode** — enforce PBT-02, PBT-03, PBT-07, PBT-08, PBT-09. PBT-01 (identification) advisory but performed below. Framework: **Hypothesis** (Python, PBT-09).

## Identified Properties

### P-1: DAG Validity Invariant (PBT-03)
- **Component**: C-01 DependencyGraphLoader.validate_graph
- **Category**: Invariant
- **Property**: Với mọi graph hợp lệ được load, không tồn tại cycle. Validator phải reject mọi graph có cycle.
- **Generator**: random graph generator (cả DAG hợp lệ lẫn graph có cycle) — PBT-07

### P-2: Downstream Closure Invariant (PBT-03)
- **Component**: C-03 ImpactAnalyzer.traverse_downstream
- **Category**: Invariant
- **Property**: Affected set đóng dưới quan hệ con — nếu node X trong affected set và Y là con của X, thì Y cũng trong affected set (trừ khi bị blocked-branch loại).
- **Generator**: random DAG + random changed-node subset

### P-3: Topological Order Invariant (PBT-03)
- **Component**: C-03 / cascade order
- **Category**: Invariant
- **Property**: Trong order trả về, mọi node xuất hiện SAU tất cả parents của nó (trong affected set). `index(parent) < index(child)` luôn đúng.
- **Generator**: random DAG

### P-4: State Round-Trip (PBT-02)
- **Component**: C-06 StateManager
- **Category**: Round-trip
- **Property**: `load_state(save_state(s)) == s` cho mọi SyncState hợp lệ. Serialize → deserialize bảo toàn toàn bộ thông tin.
- **Generator**: random SyncState generator (node_status, blocked, results)

### P-5: Cascade Idempotence Invariant (PBT-03, Q6=C)
- **Component**: S-01 SyncOrchestrationService + C-02 ChangeDetector
- **Category**: Invariant (idempotence-as-invariant để nằm trong scope Partial)
- **Property**: Khi mọi doc hash khớp `.sync-manifest.json` (không có thay đổi từ lần sync cuối), affected set = ∅ → cascade là no-op (không tạo skill invocation nào).
- **Generator**: random graph + manifest đồng bộ (mọi doc hash = manifest hash)

### P-7: Selection Gap Closure Invariant (PBT-03, BR-14)
- **Component**: C-05 resolve_selection_gaps
- **Category**: Invariant
- **Property**: Sau khi resolve, KHÔNG tồn tại node được chọn (selected) mà có parent trong affected set bị bỏ chọn và chưa được auto-include. Tức selection đã đóng dưới quan hệ parent trong affected set (mọi gap được auto-include hoặc explicitly accepted).
- **Generator**: random DAG + random affected set + random selection subset (có gap)

### P-6: Shared Node Single Visit Invariant (PBT-03)
- **Component**: C-03 dedupe_shared_nodes
- **Category**: Invariant
- **Property**: Trong order, mỗi node xuất hiện đúng MỘT lần, kể cả node có nhiều parents.
- **Generator**: random DAG with shared nodes (multiple parents)

## Generator Quality (PBT-07)
Custom Hypothesis strategies cần xây:
- `dag_strategy()` — sinh DAG hợp lệ (random nodes + acyclic edges)
- `graph_with_cycle_strategy()` — sinh graph có cycle (để test reject)
- `sync_state_strategy()` — sinh SyncState với node_status/blocked/results hợp lệ
- `sync_manifest_strategy()` — sinh SyncManifest với doc_hashes hợp lệ
- `changed_nodes_strategy(graph)` — sinh subset node từ một graph cho trước
- `selection_with_gap_strategy(graph, affected)` — sinh selection subset có gap (P-7)

Không dùng raw primitives cho domain types (node id phải là valid pattern, status phải trong enum).

## Shrinking & Reproducibility (PBT-08)
- Hypothesis tự shrink (mặc định) — không disable
- Log seed khi fail; CI log seed mỗi run
- Include PBT trong CI pipeline

## Framework (PBT-09)
- **Hypothesis** cho Python — hỗ trợ custom strategies, shrinking, seed reproducibility
- Thêm vào `requirements.txt` / dev dependencies của module

## PBT-01 Compliance Note (Partial mode)
PBT-01 là advisory ở Partial mode nhưng đã thực hiện identification ở trên. Components không có PBT property: C-04 SelectionPresenter (pure I/O rendering), C-08 TraceabilitySyncTrigger (pure delegation) → marked "No PBT properties identified — I/O only".
