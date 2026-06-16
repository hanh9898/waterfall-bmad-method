# Clarification Questions — hbc-sync Skill (Round 2)

Một vài điểm cần làm rõ thêm trước khi chốt requirements.

## Question 1 (giải thích lại Q5 — Trigger mechanism)

"Trigger" = cơ chế nào khởi động hbc-sync. Ba mô hình:

**Mô hình A — Auto-chained (tự động nối tiếp):**
Khi user chạy `hbc-create-requirements update` và hoàn thành, skill đó tự động gọi `hbc-sync` ở cuối. User không cần làm gì thêm. Cascade chạy ngay.
- Ưu: liền mạch, không quên sync.
- Nhược: skill create-requirements phải "biết" về hbc-sync (coupling).

**Mô hình B — Manual (thủ công):**
User update tài liệu xong, rồi tự gõ lệnh `hbc-sync` (hoặc menu code [SYNC]) để bắt đầu cascade.
- Ưu: tách biệt rõ ràng, user kiểm soát thời điểm.
- Nhược: user có thể quên sync → tài liệu lệch nhau.

**Mô hình C — Hybrid (kết hợp):**
Sau khi update xong, skill gợi ý "Tài liệu đã đổi, chạy hbc-sync để đồng bộ downstream? [Y/N]". User cũng có thể gọi `hbc-sync` độc lập bất kỳ lúc nào.
- Ưu: vừa nhắc nhở, vừa cho user quyền kiểm soát.

Bạn chọn mô hình nào?

A) Mô hình A — Auto-chained
B) Mô hình B — Manual
C) Mô hình C — Hybrid (gợi ý + cho phép gọi độc lập)
X) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 2 (xác nhận Q7 — vai trò orchestrator)

hbc-sync hoạt động như orchestrator, KHÔNG tự sửa nội dung tài liệu, mà gọi skill tương ứng (ở mode update) để mỗi skill tự lo phần của mình. Đúng không?

A) Đúng — hbc-sync chỉ điều phối, mỗi skill tự update phần của nó (single responsibility)
B) Sai — hbc-sync nên tự sửa trực tiếp các tài liệu downstream
C) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 3 (Q3 — "tùy trường hợp" cho code)

Bạn trả lời xử lý code "tùy trường hợp". Khi cascade chạm tới code, hbc-sync nên:

A) Luôn delegate cho `hbc-implement` quyết định (sync chỉ truyền danh sách task bị ảnh hưởng, implement tự xử lý theo TDD)
B) sync tự phân loại: thay đổi nhỏ → flag task; thay đổi lớn → tạo task mới trong task-breakdown
C) Luôn chỉ flag task cần re-implement, không bao giờ tự động sửa code
D) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 4 (Điểm bắt đầu cascade)

hbc-sync cần biết tài liệu nào vừa bị thay đổi để xác định điểm bắt đầu cascade. Cơ chế nào?

A) sync tự detect bằng cách so sánh timestamp/hash các tài liệu (phát hiện cái nào mới đổi)
B) Skill update truyền tên tài liệu đã đổi cho sync (ví dụ `hbc-sync --changed D-02`)
C) User chỉ định thủ công khi gọi sync
D) Kết hợp: ưu tiên tham số truyền vào, fallback sang auto-detect
E) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 5 (Khi nào dừng để hỏi user)

Bạn nói "1 số bước tự động, 1 số cần làm rõ, review ngữ nghĩa cần đặt câu hỏi". Xác nhận quy tắc dừng:

A) Dừng hỏi user khi: thay đổi mang tính ngữ nghĩa (semantic) hoặc ambiguous; tự động khi: thay đổi cơ học (ID rename, thêm field rõ ràng)
B) Luôn dừng hỏi trước MỖI tài liệu trong cascade
C) Chỉ dừng một lần đầu (confirm toàn bộ plan), sau đó chạy hết
D) Other (please describe after [Answer]: tag below)

[Answer]: 

