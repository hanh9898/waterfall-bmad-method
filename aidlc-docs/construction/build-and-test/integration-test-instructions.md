# Integration Test Instructions — hbc-sync

## Purpose
Test các script phối hợp end-to-end và tích hợp với existing skills (qua headless contract).

## Scenario 1: load-graph → analyze-impact (cascade computation)
- **Description**: Graph load + impact analysis trên thay đổi D-02
- **Setup**: dùng `src/hbc-sync/assets/dependency-graph.yaml`
- **Steps**:
  ```bash
  python src/hbc-sync/scripts/analyze-impact.py \
    --graph src/hbc-sync/assets/dependency-graph.yaml \
    --project-root . --changed D-02 --selected task-breakdown D-27 --auto-close-gaps
  ```
- **Expected**:
  - `affected` chứa toàn bộ downstream của D-02
  - `selection_gaps` phát hiện task-breakdown→D-19, D-27→D-26
  - `auto_included` = [D-06, D-19, D-26]
  - `selected_resolved` theo topological order, gap-free
- **Verified**: ✅ (chạy khi code generation)

## Scenario 2: analyze-impact → sync-state (resume cycle)
- **Steps**:
  ```bash
  python src/hbc-sync/scripts/sync-state.py --action save --state-path tmp.json --payload "{\"node\":\"D-19\",\"status\":\"done\"}"
  python src/hbc-sync/scripts/sync-state.py --action load --state-path tmp.json
  python src/hbc-sync/scripts/sync-state.py --action clear --state-path tmp.json
  ```
- **Expected**: save ok → load trả về `node:D-19, status:done, sync_in_progress:true` → clear `removed:true`
- **Verified**: ✅

## Scenario 3: Skill delegation contract (manual / LLM-orchestrated)
- **Description**: hbc-sync gọi skill downstream ở mode update với `--invoked-by-sync`
- **Setup**: cần một project có D-xx documents thực tế trong `_bmad-output/planning-artifacts/`
- **Steps** (manual verification):
  1. Sửa D-02 (thêm REQ mới)
  2. Chạy `hbc-sync` (interactive) hoặc `hbc-sync --headless --changed D-02`
  3. Quan sát sync đề xuất affected docs, gọi `hbc-create-test-spec update --invoked-by-sync`, v.v.
- **Expected**:
  - Mỗi skill được gọi với `--invoked-by-sync` (không re-trigger sync — BR-13)
  - Cascade theo topological order
  - matrix chạy cuối cùng
- **Note**: cần documents thực + skills đã install; verify trong môi trường tích hợp đầy đủ

## Scenario 4: Idempotence (BR-12)
- **Steps**: chạy sync 2 lần liên tiếp không sửa gì giữa 2 lần
- **Expected**: lần 2 trả `is_noop: true`, không gọi skill nào
- **Verified**: ✅ (P-5 trong PBT suite)

## Cleanup
```bash
Remove-Item tmp.json -ErrorAction SilentlyContinue
```
