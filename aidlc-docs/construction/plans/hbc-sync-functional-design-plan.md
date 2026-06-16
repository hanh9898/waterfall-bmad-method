# Functional Design Plan — hbc-sync

## Plan Steps
- [ ] Design dependency-graph.yaml schema
- [ ] Design cascade algorithm (topological traversal on DAG)
- [ ] Design state machine + .sync-state.json schema
- [ ] Design stop/ask classification logic (mechanical vs semantic)
- [ ] Design code cascade strategy decision rules
- [ ] Design headless JSON contract
- [ ] Generate functional design artifacts

## Design Questions (with AI Suggestions)

### Question 1: Stop/Ask Classification — ai quyết định mechanical vs semantic?
Quy tắc phân loại thay đổi để biết auto hay hỏi user nằm ở đâu?

A) LLM judgment thuần — AI đọc change context + downstream doc, tự quyết
B) Rule-based thuần — bảng quy tắc cứng trong script (ví dụ: ID rename = mechanical)
C) Hybrid — script đưa signal sơ bộ (heuristics), LLM ra quyết định cuối
X) Other

**[AI Suggestion]: C** — Khớp pattern toàn module (script lo deterministic, LLM lo judgment). Script flag heuristic (vd: chỉ đổi frontmatter timestamp = mechanical; section bị xóa = semantic), LLM xác nhận. Tránh A (thiếu reproducibility) và B (không bắt được nuance ngữ nghĩa).

[Answer]: C

### Question 2: Cascade fail — khi một skill trả về `blocked`, làm gì?
Khi skill downstream return `{status: blocked, reason}`:

A) Dừng toàn bộ cascade ngay, lưu state, báo user (fail-stop)
B) Skip node đó + descendants của nó, tiếp tục các nhánh độc lập khác, báo cuối
C) Dừng nhánh chứa node blocked, tiếp tục nhánh song song độc lập, lưu state
X) Other

**[AI Suggestion]: C** — Cân bằng nhất. Nếu D-19 blocked thì nhánh D-19→task-breakdown→code dừng, nhưng nhánh D-03 (Glossary) độc lập vẫn chạy được. Node blocked + descendants được lưu vào state để resume. Phù hợp DAG (có nhánh song song). NFR-002 Reliability.

[Answer]: C

### Question 3: Shared node — khi nào update?
D-27 có parents [D-02, D-26]. Nếu cả D-02 và D-26 đều thay đổi, D-27 update thế nào?

A) Update D-27 một lần duy nhất, sau khi CẢ D-02 và D-26 đã xử lý xong (gom context)
B) Update D-27 hai lần, mỗi lần một parent
C) Update D-27 ngay khi parent đầu tiên xong, parent sau bị bỏ qua
X) Other

**[AI Suggestion]: A** — Topological sort đảm bảo D-27 chỉ được visit sau khi tất cả parents (in-degree = 0). Gom context từ mọi parent thành một lần gọi `hbc-create-test-spec update` → hiệu quả, tránh update thừa, tránh conflict. Đây là lý do dùng topological sort thay vì tree walk.

[Answer]: A

### Question 4: Change context truyền cho skill — format nào?
Khi gọi skill downstream update, truyền thông tin thay đổi thế nào?

A) Free-text summary (AI mô tả thay đổi upstream bằng prose)
B) Structured JSON (changed_doc, change_type, affected_sections, upstream_results)
C) Cả hai — structured JSON + human-readable summary
X) Other

**[AI Suggestion]: C** — JSON cho skill parse (headless), summary cho LLM hiểu ngữ cảnh. Khớp pattern headless contract của module. Skill nhận biết chính xác cái gì đổi để update đúng phần.

[Answer]: C

### Question 5: Impact level — tiêu chí gán high/medium/low?
Cơ sở nào để gán impact level cho mỗi affected document?

A) Khoảng cách trong graph (parent trực tiếp = high, càng xa = càng thấp)
B) Loại thay đổi (semantic = high, mechanical = low) + có content thực sự đổi không
C) Kết hợp: loại thay đổi + độ phủ (bao nhiêu % nội dung downstream phụ thuộc phần đổi)
X) Other

**[AI Suggestion]: C** — Impact level hữu ích cho user selection (REQ-003). Chỉ dùng khoảng cách (A) không chính xác — node xa vẫn có thể bị ảnh hưởng nặng. Kết hợp loại thay đổi + độ phủ phản ánh đúng tác động thực.

[Answer]: C

### Question 6: PBT properties — xác nhận scope (Partial mode)
PBT Partial mode enforce PBT-02, 03, 07, 08, 09. Các property cần test:

A) Theo đúng bảng đã xác định ở Application Design (DAG invariant, downstream closure, topological order, state round-trip, graph generator)
B) Chỉ state round-trip (tối thiểu)
C) Mở rộng thêm: idempotence của cascade (chạy sync 2 lần = 1 lần nếu không có thay đổi mới)
X) Other

**[AI Suggestion]: C** — A đã tốt, nhưng thêm idempotence (PBT-04 không bắt buộc ở Partial, nhưng cascade idempotence là invariant quan trọng — chạy lại sync khi đã đồng bộ không được tạo thay đổi). Sẽ test như invariant (PBT-03) thay vì PBT-04 để nằm trong scope Partial.

[Answer]: C

