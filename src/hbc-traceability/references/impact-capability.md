# Impact Capability — Cascade Document Sync

Operational detail for the **Impact** capability (the 5th, beside Initialize/Update/Report/Audit). SKILL.md holds the concise flow; this file holds the per-stage rules. Contract of record: `_bmad-output/specs/spec-traceability-impact/SPEC.md`.

**Core principle:** Impact only ĐỌC các nguồn sự thật đã có (matrix, task-breakdown status, phase-gate, git), suy tác động, ĐỀ XUẤT — **không bao giờ tự sửa nội dung**. Mọi sửa đổi đi qua owning-skill ở `update` mode. Con người quyết, hệ thống đề xuất.

Lifecycle: **DECLARE → IMPACT → FREEZE-CHECK → SUGGEST → (validate-plan) → APPLY → RECONCILE → ADVISORY (non-REQ)**.

Mọi lệnh `impact.py` truyền các giá trị `{workflow.*}` đã cấu hình trong `customize.toml` (baseline git, flood-threshold, gate-reports-glob, task-breakdown, reconcile-max-retries) — không hardcode.

## Stage 1 — DECLARE (CAP-1)

User khai REQ/artifact vừa đổi. Đối chiếu git và chuẩn hóa về REQ:

```
python3 scripts/impact.py detect --matrix {workflow.matrix_path} \
  --declared "<REQ-xxx,...>" --since {workflow.impact_git_baseline} --project-root {project-root}
```

- Baseline git mặc định `{workflow.impact_git_baseline}` (working tree vs HEAD); thay bằng ref khác khi user chỉ định runtime.
- Thay đổi non-REQ (code/test/design) được map ngược về REQ qua matrix (`code_ref`/`test_ref`/`design_ref` → `req_id`).
- Trình `changed-set` cho user **xác nhận** trước khi sang IMPACT.
- Biên (matrix chưa init, thay đổi chưa-trace, REQ id sai, changed-set rỗng → no-op, `--since` sai): xem `references/edge-handling.md`.

## Stage 2 — IMPACT (CAP-2)

Đọc matrix theo **cả cột** để tìm mọi REQ/artifact bị ảnh hưởng:

```
python3 scripts/impact.py analyze --matrix {workflow.matrix_path} \
  --changed "<REQ-xxx,...>" --flood-threshold {workflow.impact_flood_threshold} --project-root {project-root}
```

Script trả hai diện, đã khử trùng artifact dùng chung:
- **lan DỌC (apply)** — hạ nguồn của chính REQ vừa đổi.
- **lan NGANG (verify)** — REQ khác có ref trỏ tới cùng artifact (chỉ cần review, tự nó không đổi).

LLM judgment trên kết quả script: xác nhận nhãn apply/verify, đánh impact_level, lọc nhiễu. Biên (REQ bị xóa → conflict mồ côi; flood artifact dùng chung; ref còn rỗng): xem `references/edge-handling.md`.

## Stage 2b — FREEZE-CHECK (CAP-3)

Phân loại mỗi **REQ** bị ảnh hưởng là updatable hay frozen:

```
python3 scripts/impact.py freeze --matrix {workflow.matrix_path} \
  --reqs "<REQ-xxx,...>" --task-breakdown {workflow.task_breakdown_path} \
  --gate-reports-glob {workflow.gate_reports_glob} --project-root {project-root}
```

Gộp 3 nguồn; khi bất đồng, **ưu tiên: task status > phase-gate > matrix `gate_status`**. Artifact frozen (done/PASSED) → **không sửa tại chỗ**, định tuyến sang gợi ý "tạo task mới". Thiếu task-breakdown → fallback gate+matrix.

## Stage 3 — SUGGEST (CAP-4)

Trình impact cho user, dùng `{workflow.ref_skill_map}` map mỗi ref → owning-skill, xếp theo thứ tự waterfall (design→test→code; apply trước verify). Trình bảng đề xuất rồi dừng — mọi áp dụng chờ user hành động (Stage APPLY). Ref không map được skill → flag thủ công, không bỏ qua im lặng. Output là một bảng đề xuất "chạy skill nào, thứ tự nào" + danh sách "tạo task mới" cho phần frozen.

**Validate-plan (trước APPLY):** trước khi mutate bất cứ thứ gì, xác nhận lại plan với nguồn-sự-thật — mỗi ref còn resolve được owning-skill, phần frozen định tuyến sang new-task (không sửa tại chỗ), nhãn apply/verify nhất quán. Trình plan-đã-validate cho user; chỉ sang APPLY khi user đồng ý (headless: validate xong tiếp). Đây là chốt cuối trước thao tác không-hồi.

## Stage 4 — APPLY (CAP-5)

Chỉ khi user hành động. Với mỗi mục đã chọn (hỗ trợ **tập con**), gọi owning-skill ở `update` mode **luôn kèm `--invoked-by-sync`** (chống loop):

```
<owning-skill> update --invoked-by-sync [--headless]
```

- Thiếu update contract → interactive flag thủ công; headless `blocked` reason `skill_no_update_contract`.
- Owning-skill lỗi runtime → branch-stop nhánh đó, giữ trạng thái, tiếp nhánh độc lập.
- `code` node: theo chiến lược của `hbc-implement` (task-level), không regenerate mù.
- **Resume state:** trước mỗi node, ghi tiến độ cascade vào `{output_folder}/traceability/.cascade-state.json` — **file riêng, KHÁC `.trace-state.json` của Update** (tránh va chạm schema). Nội dung `{cascade_in_progress, applied:[], pending:[], dispositions:{node→reconciled|deferred|frozen_task|blocked}, started}`; clear khi hoàn tất. Khi activation thấy state còn → offer **Resume** (tiếp từ `pending` đầu) hoặc **Restart**; headless resume im lặng.

## Stage 5 — RECONCILE (CAP-6)

Xác minh "đã lan đúng" — **2 trụ chính + 1 phụ**:
1. **Validator deterministic** pass (vd `hbc-implement/scripts/validate-implementation.py`, facet coverage của D-27). Thiếu validator cho loại artifact → dựa trụ 2, ghi rõ "không validator".
2. **LLM semantic review** (rubric: `src/hbc-shared/references/semantic-review-rubric.md`) — đọc thay-đổi-gốc + artifact-đã-cập-nhật, phán thay đổi cụ thể đã hiện diện; xử lý luôn lan-ngang-verify.
3. (phụ) ô matrix tươi — chỉ đối chiếu, không tự chứng minh nội dung đổi.

Chưa-lan-đúng → đẩy lại SUGGEST (không clear, không rollback). Vòng re-suggest giới hạn `{workflow.impact_reconcile_max_retries}` → block + báo human. Sau cùng chạy `hbc-traceability update` cho REQ liên quan để matrix phản ánh cascade.

**Completeness check (đóng cascade):** chạy
```
python3 scripts/impact.py complete --state {output_folder}/traceability/.cascade-state.json --changed "<REQ-xxx,...>"
```
Script trả `missing` = node trong changed-set chưa có disposition cuối trong `dispositions` (reconciled / deferred-by-user (subset) / frozen→task / branch-stopped-blocked). Còn `missing` → báo rõ thay vì kết thúc im lặng.

## Stage 6 — ADVISORY non-REQ (CAP-7)

Khi changed-set chứa artifact **không-gắn-REQ** (glossary D-03, coding-standard D-12) — ca hiếm, luôn **advisory, không bao giờ tự áp**:
- **glossary** — reverse-scan các artifact chưa-đóng-băng tìm tham chiếu thuật ngữ đổi; trình danh sách "nên review" kèm confidence. Lọc theo ranh giới từ/ngữ cảnh để tránh flood khi thuật ngữ phổ biến (xem `references/edge-handling.md`).
- **coding-standard** — flag mọi code task chưa-đóng-băng để re-check theo chuẩn mới; nếu chưa có code task, nêu rõ "chưa có để flag", không im lặng.

## Trigger modes

- **Manual** — user gọi `hbc-traceability impact` / menu [SYNC].
- **Hybrid** (mặc định) — một create-* skill sau `update` gợi ý chạy impact; user xác nhận.
- **Auto-chained** — skill có `auto_sync_after_update=true` gọi impact trực tiếp; cascade vẫn gọi owning-skill kèm `--invoked-by-sync` như APPLY, nên không loop.
