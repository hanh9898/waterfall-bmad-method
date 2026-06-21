# TDD Evidence — TASK-008 Đồng bộ 1 chiều plan→allocation

REQ-011 (thêm dòng→tạo member), REQ-012 (sửa→cập nhật), REQ-013 (xóa→end_at), REQ-023 (1 chiều), REQ-025 (no-sudo). Test: `tests/test_resource_plan_alloc_sync.py` (7 test). TC-026 (snapshot generate_lines) chuyển sang TASK-011.

## RED — 2026-06-19
```
FAIL ...alloc_sync: "Them dong phai tao/lien ket allocation" / "0.0 != 0.8" / create_uid sudo / end_at ...
Ran 7 tests ... FAILED (failures=5)
```

## GREEN — 2026-06-19
Code `resource_plan_line.py`: `_sync_allocation_create` (link member có sẵn hoặc tạo mới, no sudo), `_sync_allocation_write` (effort→member.effort_ratio), `_sync_allocation_unlink` (set end_at, không xóa cứng); tích hợp vào create/write/unlink. Một chiều (không có member→line).
```
...test_resource_plan_alloc_sync: Ran 7 tests — OK   (7 suite resource_plan OK)
```
REFACTOR: không cần.
