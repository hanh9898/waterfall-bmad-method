# Ref → Owning-Skill Map & Waterfall Order

Companion của `SPEC.md`. Là tri thức tĩnh nhỏ thay thế cho `dependency-graph.yaml` cũ: capability `impact` cần biết (a) cột matrix nào → owning-skill nào, và (b) thứ tự waterfall cố định để xếp cascade (CAP-4). Không còn DAG, không topological sort.

## Cột matrix → owning-skill

| Cột matrix / loại ref | Artifact | Owning-skill (update mode) |
|---|---|---|
| `req_id` (tài liệu nguồn) | D-02 requirements | hbc-create-requirements |
| `design_ref` (thực thể/bảng) | D-19 ER/database | hbc-create-er-diagram |
| `design_ref` (endpoint) | D-21 API spec | hbc-create-api-spec |
| `test_ref` (TC-xxx) | D-27 test spec | hbc-create-test-spec |
| `test_ref` (kế hoạch test) | D-26 test plan | hbc-create-test-plan |
| `code_ref` (file:function) | source code | hbc-implement |
| (tác vụ) | task-breakdown.md | hbc-task-breakdown |
| (ma trận, self) | matrix | hbc-traceability |

> `design_ref` có thể trỏ tới D-19 *hoặc* D-21 — phân biệt bằng LLM judgment trên nội dung ref (thực thể/bảng → ER; endpoint/route → API). Bảng này sống trong `customize.toml` của hbc-traceability (`[workflow] ref_skill_map`), override được mà không sửa skill.

## Artifact không gắn REQ (CAP-7, ca biên)

| Artifact | Owning-skill | Cách lan |
|---|---|---|
| D-03 glossary | hbc-create-glossary | reverse-text-scan (advisory) |
| D-12 coding-standards | hbc-create-coding-standards | reverse-text-scan (advisory) |
| D-06 business-flow | hbc-create-business-flow-diagram | theo REQ (qua D-26) |

## Thứ tự waterfall cố định (thay topological sort)

Cascade cho một REQ đi theo đúng chuỗi phase lifecycle, bỏ qua phần đã done:

```
requirements (D-02)
  → [glossary D-03 · business-flow D-06 · ER D-19]        (Phase design sớm)
  → [coding-standards D-12 · api-spec D-21 · test-plan D-26]
  → test-spec (D-27)
  → task-breakdown
  → code
  → matrix (hbc-traceability, luôn cuối)
```

Quy tắc: với mỗi REQ bị ảnh hưởng, áp owning-skill theo thứ tự trên, chỉ trên artifact chưa-đóng-băng. `matrix` luôn chạy cuối để phản ánh cascade (kể cả khi cascade chỉ một phần).

## Freeze-check (CAP-3) — ghép 3 nguồn

Một artifact là **frozen** (→ tạo task mới, không sửa) nếu BẤT KỲ điều nào đúng:
- `task-breakdown` status của task tương ứng = `DONE`, HOẶC
- `hbc-phase-gate` của phase chứa artifact = `PASSED` (phase đã đóng), HOẶC
- ô matrix tương ứng có `gate_status` đã chốt cho phase đó.

Ngược lại là **updatable** (live frontier) → đề xuất cập nhật qua owning-skill.
