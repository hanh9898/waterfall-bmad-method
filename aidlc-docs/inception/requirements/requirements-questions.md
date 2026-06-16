# Requirements Clarification Questions — hbc-sync Skill

Vui lòng trả lời các câu hỏi sau bằng cách điền chữ cái lựa chọn vào sau tag `[Answer]:`.

## Question 1
Khi cascade update, nếu một tài liệu downstream có thay đổi lớn (ví dụ update D-02 dẫn đến 50% test case trong D-27 cần viết lại), skill nên xử lý thế nào?

A) Tự động update tất cả — không hỏi user (full automation)
B) Hiển thị impact analysis trước, user confirm từng tài liệu trước khi update
C) Hiển thị impact analysis, user confirm một lần cho toàn bộ cascade
D) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 2
Phạm vi cascade — khi update một tài liệu, mức độ lan truyền tối đa là gì?

A) Chỉ tài liệu trực tiếp phụ thuộc (1 level) — ví dụ update D-02 → chỉ update D-27
B) Toàn bộ chain downstream (full cascade) — D-02 → D-27 → Task Breakdown → Code
C) Configurable — user chọn depth mỗi lần
D) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 3
Với code (implementation) — khi cascade đến code level, skill nên làm gì?

A) Chỉ đánh dấu task nào cần re-implement (flag only, không sửa code)
B) Tự động regenerate code cho các task bị ảnh hưởng (full auto)
C) Tạo diff/patch suggestion — user review và apply thủ công
D) Tạo new tasks trong task-breakdown cho phần cần thay đổi
E) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 4
Dependency graph giữa các tài liệu — cấu trúc phụ thuộc nào đúng với workflow hiện tại?

A) Linear chain: D-02 → D-19/D-21 → D-27 → Task Breakdown → Code
B) Tree: D-02 là root, branch ra D-19, D-21, D-06, rồi converge vào D-27 → TB → Code
C) Cả hai, tùy thuộc vào loại thay đổi (structural change vs content change)
D) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 5
Khi nào hbc-sync được trigger?

A) Tự động — mỗi khi bất kỳ skill nào hoàn thành mode `update`, tự động gọi sync
B) Thủ công — user phải gọi `hbc-sync` explicitly sau khi update xong
C) Cả hai — auto-trigger sau update, nhưng user cũng có thể gọi manually bất kỳ lúc nào
D) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 6
Headless mode — skill này có cần hỗ trợ headless (non-interactive) không?

A) Có — cần headless mode để có thể chain trong CI/CD hoặc gọi từ skill khác
B) Không — chỉ cần interactive mode vì luôn cần human review
C) Other (please describe after [Answer]: tag below)

[Answer]: 

## Question 7
Traceability matrix — hbc-sync có nên tự động update traceability matrix khi cascade xong không?

A) Có — tự động gọi `hbc-traceability update` sau mỗi cascade
B) Không — traceability update riêng, do user trigger
C) Có, nhưng chỉ flag entries cần review, không tự sửa mapping
D) Other (please describe after [Answer]: tag below)

[Answer]: 

