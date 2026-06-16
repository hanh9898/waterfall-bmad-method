# Impact — Edge / Boundary Handling

Quy tắc biên cho capability **Impact**. Mỗi dòng = boundary → hành vi bắt buộc. Bất biến: **không âm thầm bỏ sót, không âm thầm làm lệch.** Đồng bộ với `_bmad-output/specs/spec-traceability-impact/edge-handling.md`.

## DECLARE (Stage 1)

| Biên | Hành vi |
|---|---|
| Matrix chưa init | Dừng, gợi ý `traceability init`, không phân tích. |
| Reverse-map không ra REQ cho một thay đổi | Flag "thay đổi chưa được trace", hỏi user — không bỏ qua. |
| User khai REQ id không có trong matrix | Báo lỗi id sai, không phân tích. |
| Changed-set rỗng (git sạch + không khai) | Báo no-op "đã đồng bộ", dừng. |
| `--since <ref>` sai/không tồn tại | Báo lỗi, KHÔNG lặng lẽ lùi HEAD. |

## IMPACT (Stage 2)

| Biên | Hành vi |
|---|---|
| REQ bị XÓA (req_id biến mất) | Cảnh báo conflict: downstream mồ côi, đề xuất dọn — không coi "không tác động". |
| Artifact dùng chung vượt ngưỡng N REQ | Nhóm/tóm tắt danh sách verify + cảnh báo scale. |
| Hàng REQ có ref còn rỗng (phase sớm) | Phân biệt "chưa có hạ nguồn" vs "matrix dở dang"; nêu rõ. |
| Granularity `design_ref` thô (mức thực thể) | Chấp nhận over-flag (an toàn) hơn bỏ sót. |

## FREEZE-CHECK (Stage 2b)

| Biên | Hành vi |
|---|---|
| 3 nguồn bất đồng | Ưu tiên **task status > phase-gate > matrix `gate_status`**. |
| Thiếu `task-breakdown.md` (trước Phase 3) | Fallback gate + matrix; không mặc nhiên coi updatable. |

## SUGGEST (Stage 3)

| Biên | Hành vi |
|---|---|
| `design_ref` không khớp `ref_skill_map` | Flag thủ công, KHÔNG bỏ artifact im lặng. |

## APPLY (Stage 4)

| Biên | Hành vi |
|---|---|
| Owning-skill thiếu update contract | Interactive: flag cập nhật thủ công. Headless: `blocked` reason `skill_no_update_contract`. |
| Owning-skill lỗi runtime giữa chừng | Branch-stop, giữ trạng thái, báo rõ đã/chưa xong, tiếp nhánh độc lập. |
| User áp tập con | Hỗ trợ subset; giữ thứ tự; cảnh báo phần bỏ lại có thể lệch. |

## RECONCILE (Stage 5)

| Biên | Hành vi |
|---|---|
| Thiếu validator cho loại artifact | Dựa LLM semantic review + ghi rõ "không validator"; không pass mặc nhiên. |
| Reconcile fail lặp | Giới hạn re-suggest (mặc định 2) → block + báo human. |

## ADVISORY non-REQ (CAP-7)

| Biên | Hành vi |
|---|---|
| Thuật ngữ glossary là từ phổ biến | Lọc theo ranh giới từ/ngữ cảnh, hạ confidence. |
| Coding-standard đổi nhưng chưa có code task | Nêu rõ "chưa có code task để flag", không im lặng. |

## Cross-cutting

| Biên | Hành vi |
|---|---|
| Hai lần chạy impact chạm cùng artifact | Nối tiếp/khóa theo artifact, không ghi đè đồng thời. |
