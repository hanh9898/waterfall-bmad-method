# TDD Evidence — TASK-001 (scaffold, gộp vào TASK-002)

TASK-001 (scaffold thuần: wiring `models/__init__.py` + manifest) được **gộp vào TASK-002** theo quyết định (scaffold không có hành vi riêng để test). RED/GREEN chung với TASK-002 (model `resource.plan`). Xem chi tiết: `TASK-002.md`.

## RED — 2026-06-19 (chung TASK-002)
```
ERROR ...test_resource_plan: self.env['resource.plan'].create(...) -> KeyError: 'resource.plan'
Ran 3 tests ... FAILED (errors=3)
```
→ scaffold + model chưa tồn tại.

## GREEN — 2026-06-19
Scaffold: `project_invoice/models/__init__.py` (`from . import resource_plan`), `project_invoice/__manifest__.py`. Model `resource.plan` (TASK-002). Test `tests/test_resource_plan.py` OK.
