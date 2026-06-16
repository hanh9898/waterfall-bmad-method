# Business Rules — hbc-sync

## BR-01: Single Responsibility (Orchestrator)
hbc-sync KHÔNG bao giờ tự sửa nội dung tài liệu. Mọi thay đổi nội dung phải qua skill tương ứng ở mode `update`. Vi phạm rule này = bug.

## BR-02: Topological Order Guarantee
Một node chỉ được invoke sau khi TẤT CẢ parents của nó (trong affected set) đã được xử lý (done hoặc blocked). Thực thi qua Kahn's algorithm (in-degree = 0).

## BR-03: Shared Node Single Update (Q3=A)
Một node có nhiều parents chỉ được update MỘT lần duy nhất, gom context từ tất cả parents. Không update lặp theo từng parent.

## BR-04: Branch-Stop on Blocked (Q2=C)
Khi một skill return `status: blocked`:
- Node đó + toàn bộ descendants của nó (qua mọi đường) bị đánh dấu blocked, không xử lý
- Các nhánh độc lập (không phụ thuộc node blocked) tiếp tục bình thường
- State được lưu để resume sau khi user fix nguyên nhân blocked
- **Ngoại lệ (BR-09)**: node `matrix` (traceability) KHÔNG bị branch-stop — vẫn chạy trên partial results để ghi nhận tiến độ một phần

## BR-05: Stop-and-Ask Rule (Q1=C)
- **Mechanical change** → auto-invoke skill, không hỏi user
- **Semantic change** → trong interactive mode: dừng, hỏi user cách xử lý; trong headless: return `blocked` reason `semantic_change_needs_human`
- LLM ra quyết định cuối dựa trên script heuristic + nội dung

## BR-06: Change Detection via Baseline Manifest (Q6 Round2=C)
- **Baseline**: `.sync-manifest.json` lưu hash (sha256 của body, bỏ frontmatter) của mỗi document tại lần sync thành công cuối cùng
- **Detect**: ChangeDetector tính hash hiện tại của mỗi doc, so với manifest:
  - Hash khác → doc đã thay đổi (changed)
  - Hash giống → không đổi
  - Doc không có trong manifest → treat as new/changed
- **Ưu tiên override**: doc user chỉ định qua `--changed` luôn được coi là changed (bỏ qua hash check)
- **User free-text context** bổ sung ngữ nghĩa cho LLM, không thay thế hash detection
- Manifest được cập nhật (ghi hash mới) chỉ khi cascade hoàn thành thành công cho node đó
- **Lý do không dùng timestamp**: timestamp parent vs child không đáng tin (child có thể update sau vì lý do khác; user sửa tay không bump timestamp). Hash là nguồn sự thật.

## BR-07: Impact Level Assignment (Q5=C)
Impact level là **LLM qualitative estimate** (KHÔNG phải con số chính xác). LLM đánh giá dựa trên 2 yếu tố:
- **Loại thay đổi**: semantic (đổi ý nghĩa) vs mechanical (đổi cơ học)
- **Mức phụ thuộc**: phần downstream phụ thuộc vào phần upstream bị đổi là nhiều hay ít (qualitative: nhiều/vừa/ít)

```
impact_level (LLM judgment):
  HIGH   — semantic change VÀ downstream phụ thuộc nhiều vào phần đổi
  MEDIUM — semantic + phụ thuộc ít, HOẶC mechanical + phụ thuộc nhiều
  LOW    — mechanical change VÀ downstream phụ thuộc ít
```
Không có ngưỡng % cứng — đây là ước lượng định tính để hỗ trợ user selection, ghi kèm rationale.

## BR-08: Code Cascade Strategy (REQ-008, C-07)
```
change_scope:
  SMALL  (field rename, thêm validation rõ ràng)
    → flag affected tasks trong task-breakdown + suggest quick fix; KHÔNG tự sửa code
  MEDIUM (logic change)
    → tạo task mới trong task-breakdown (qua hbc-task-breakdown update),
      delegate hbc-implement cho task mới
  LARGE  (architecture / nhiều entity đổi)
    → flag toàn bộ affected tasks, recommend re-run hbc-task-breakdown đầy đủ
```
AI suggest scope, user confirm trước khi thực thi (interactive). Headless: SMALL auto-flag, MEDIUM/LARGE return blocked.

## BR-09: Traceability Always Terminal (REQ-009)
Node `matrix` luôn là bước cuối cùng, delegate hoàn toàn cho `hbc-traceability update`. Nếu user bỏ chọn matrix → skip nhưng warn "traceability có thể lệch".

## BR-10: State Persistence Before Each Invocation (NFR-002)
Trước khi gọi mỗi skill, ghi `.sync-state.json` với node hiện tại = `in_progress`. Đảm bảo resume chính xác khi interrupt.

## BR-11: DAG Validity (PBT-03 invariant)
Dependency graph load lên PHẢI là DAG. Nếu phát hiện cycle → HALT (interactive) hoặc return blocked `reason: graph_has_cycle` (headless). Không bao giờ cascade trên graph có cycle.

## BR-12: Idempotence (Q6=C, PBT-03 invariant)
Chạy cascade hai lần liên tiếp khi không có thay đổi mới giữa hai lần → lần thứ hai không tạo bất kỳ thay đổi nội dung nào (no-op). Khi mọi doc hash khớp manifest (BR-06), affected set = ∅.

## BR-13: Circular Trigger Guard (REQ-005, CRITICAL)
Auto-chained trigger có thể tạo vòng lặp: skill update xong → trigger sync → sync gọi skill update → skill lại trigger sync → ∞.
- Khi hbc-sync invoke bất kỳ skill nào, PHẢI truyền flag suppress: `--invoked-by-sync` (hoặc context `invoked_by_sync=true`)
- Skill nhận flag này MUST KHÔNG kích hoạt auto_sync_after_update (bỏ qua trigger)
- Manual và hybrid trigger không bị ảnh hưởng (user chủ động gọi)
- Đây là teeth chống infinite loop — bắt buộc thực thi ở cả sync và các skill được modify (REQ-004 skill modification)

## BR-14: Selection Gap Handling (REQ-003)
User có thể chọn subset tùy ý. Nếu selection bỏ qua node trung gian nhưng giữ descendant của nó (vd bỏ D-27 nhưng giữ task-breakdown — task-breakdown depends_on D-27):
- Sync PHẢI phát hiện "gap" trong selection (node được chọn có parent affected nhưng không được chọn)
- **Interactive**: cảnh báo user, đề nghị 2 lựa chọn: (a) auto-include node trung gian, (b) giữ nguyên nhưng chấp nhận rủi ro không nhất quán
- **Headless**: auto-include node trung gian (an toàn mặc định), log cảnh báo
- Không bao giờ silently update node mà parent affected của nó bị skip

## BR-15: Conflict Detection (REQ-002)
Trong quá trình classify_change, nếu phát hiện downstream document có nội dung **mâu thuẫn** với thay đổi upstream (vd D-27 test một REQ vừa bị xóa khỏi D-02):
- Đánh dấu là semantic change + conflict flag
- **Interactive**: surface conflict cho user, hỏi cách xử lý trước khi gọi skill
- **Headless**: return `blocked` reason `downstream_conflict`
- Conflict là tập con của semantic change (luôn cần human judgment)
