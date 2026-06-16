# Edge / Boundary Handling — capability "impact"

Companion của `SPEC.md`. Kho **duy nhất** các quy tắc biên: mỗi dòng = một boundary → hành vi bắt buộc. Downstream phải tuân; kernel `SPEC.md` chỉ giữ tiêu chí chính của mỗi capability rồi trỏ về đây. Bất biến xuyên suốt: **không âm thầm bỏ sót, không âm thầm làm lệch.**

## CAP-1 — DECLARE / Detection

| Biên | Hành vi bắt buộc |
|---|---|
| Matrix chưa init (traceability chưa chạy) | Dừng, gợi ý chạy traceability `init`, không phân tích. |
| Reverse-map không ra REQ nào cho một thay đổi | Flag "thay đổi chưa được trace", hỏi user — không bỏ qua. |
| User khai REQ id không tồn tại trong matrix | Báo lỗi rõ id sai, không phân tích. |
| Changed-set rỗng (git sạch + user không khai) | Báo no-op "đã đồng bộ", dừng (idempotence). |
| `--since <ref>` sai / không tồn tại | Báo lỗi, KHÔNG lặng lẽ lùi về HEAD. |

## CAP-2 — IMPACT

| Biên | Hành vi bắt buộc |
|---|---|
| REQ bị XÓA (req_id biến mất) thay vì sửa | Cảnh báo conflict: downstream mồ côi, đề xuất dọn — không coi như "không tác động". |
| Artifact dùng chung bởi nhiều REQ vượt ngưỡng N | Nhóm/tóm tắt danh sách verify + cảnh báo scale, không xổ phẳng vô hạn. |
| Hàng REQ có `design/code/test_ref` còn rỗng (phase sớm) | Phân biệt "chưa có hạ nguồn" vs "matrix dở dang"; nêu rõ, không báo "không tác động" sai. |
| (Granularity `design_ref` thô — mức thực thể) | Chấp nhận over-flag (an toàn) hơn bỏ sót — xem Assumptions trong SPEC. |

## CAP-3 — FREEZE-CHECK

| Biên | Hành vi bắt buộc |
|---|---|
| 3 nguồn bất đồng (gate PASSED vs task IN_PROGRESS…) | Ưu tiên **task status > phase-gate > matrix `gate_status`**. |
| Thiếu `task-breakdown.md` (trước Phase 3) | Lùi về gate + matrix; không coi mọi thứ updatable một cách mặc nhiên. |

## CAP-4 — SUGGEST

| Biên | Hành vi bắt buộc |
|---|---|
| `design_ref` không khớp mục nào trong `ref_skill_map` | Flag thủ công cho user, KHÔNG bỏ artifact khỏi kế hoạch một cách im lặng. |

## CAP-5 — APPLY

| Biên | Hành vi bắt buộc |
|---|---|
| Owning-skill thiếu update contract | Interactive: flag cập nhật thủ công + gợi ý cài hợp đồng. Headless: `blocked` reason `skill_no_update_contract`. |
| Owning-skill lỗi runtime giữa chừng | Branch-stop nhánh đó, giữ trạng thái đã áp, báo rõ artifact đã/chưa xong, tiếp các nhánh độc lập. |
| User áp TẬP CON các đề xuất | Hỗ trợ subset; giữ thứ tự waterfall; cảnh báo phần bỏ lại có thể gây lệch. |

## CAP-6 — RECONCILE

| Biên | Hành vi bắt buộc |
|---|---|
| Thiếu validator deterministic cho loại artifact | Dựa lớp LLM semantic review + ghi rõ "không có validator"; KHÔNG coi là pass mặc nhiên. |
| Reconcile fail → re-suggest → fail lặp | Giới hạn số vòng re-suggest (mặc định 2); vượt ngưỡng → block + báo human. |

## CAP-7 — ADVISORY (non-REQ)

| Biên | Hành vi bắt buộc |
|---|---|
| Thuật ngữ glossary là từ phổ biến (vd "Order") | Lọc theo ranh giới từ/ngữ cảnh, hạ confidence; tránh ngập rác advisory. |
| Coding-standard đổi nhưng chưa có code task (trước Phase 3) | Nêu rõ "chưa có code task để flag", không im lặng coi như xong. |

## Cross-cutting

| Biên | Hành vi bắt buộc |
|---|---|
| Hai lần chạy `impact` đồng thời chạm cùng artifact | Nối tiếp/khóa theo artifact — xem Constraint concurrency trong SPEC. |
