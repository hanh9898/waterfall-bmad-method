# Application Design Plan — hbc-sync

## Plan Steps

- [ ] Define component structure and responsibilities
- [ ] Define dependency graph data model (assets/dependency-graph.yaml)
- [ ] Define component methods and interfaces
- [ ] Define service orchestration flow
- [ ] Define integration points with existing skills
- [ ] Define state management (resume/interrupted cascade)
- [ ] Generate design artifacts

## Design Questions (with AI Suggestions)

> **Lưu ý**: Mỗi câu có **[AI Suggestion]** kèm lý do. Bạn có thể đồng ý tất cả (trả lời "đồng ý"/"ok") hoặc override từng câu.

### Question 1: Dependency Graph Storage Format
Dependency graph giữa các tài liệu nên lưu ở format nào?

A) YAML file (dễ đọc, dễ edit cho user) — `assets/dependency-graph.yaml`
B) JSON file (dễ parse bằng script) — `assets/dependency-graph.json`
C) Embedded trong SKILL.md (hardcoded, không cần file riêng)
D) Python dict trong script (code-first approach)
X) Other

**[AI Suggestion]: A** — YAML khớp với pattern hiện có (skills dùng `assets/` cho template). User dễ đọc/sửa khi thêm document type mới (thỏa NFR-003 Extensibility). Script Python có thể parse YAML dễ dàng.

[Answer]: A

### Question 2: Cascade State Persistence
Khi cascade bị interrupted (skill fail giữa chừng), state lưu ở đâu?

A) File `.sync-state.json` trong `{project-root}/_bmad-output/sync/`
B) Frontmatter của mỗi tài liệu đã xử lý (distributed state)
C) Trong memory chỉ — nếu interrupt thì restart từ đầu
X) Other

**[AI Suggestion]: A** — Khớp chính xác pattern hiện có: `hbc-traceability` dùng `.trace-state.json`, `hbc-create-test-spec` dùng `.decision-log.md`. File state tập trung dễ resume (thỏa NFR-002 Reliability). Tránh option B vì làm bẩn frontmatter tài liệu.

[Answer]: A

### Question 3: Skill Invocation Mechanism
hbc-sync gọi skill downstream bằng cách nào?

A) LLM orchestration — sync's SKILL.md instruct AI gọi skill tiếp theo bằng tên
B) Python script dispatch — script generate command
C) Hybrid — AI reads dependency graph + state (qua script), quyết định thứ tự, rồi instruct gọi từng skill ở mode update
X) Other

**[AI Suggestion]: C** — Đây là pattern chuẩn của BMad: script lo phần deterministic (parse graph, detect phase, tính thứ tự cascade), AI lo phần orchestration + judgment (quyết định stop/ask, gọi skill). Giống cách `hbc-task-breakdown` dùng script detect + LLM judgment.

[Answer]: C

### Question 4: Impact Analysis Output Format
Kết quả impact analysis (danh sách tài liệu bị ảnh hưởng) hiển thị dạng nào?

A) Markdown table (document, impact level, reason, skill to invoke)
B) Tree view (highlight affected nodes)
C) Cả hai — tree view tổng quan + table chi tiết
X) Other

**[AI Suggestion]: C** — Tree view giúp user thấy vị trí trong dependency chain, table cho chi tiết để chọn. UX tốt nhất cho bước user selection (REQ-003). Validate ASCII tree theo content-validation rules.

[Answer]: C

### Question 5: Modification to Existing Skills
Để support triple trigger (auto-chain + manual + hybrid), existing skills cần sửa gì?

A) Thêm 1 dòng ở Stage cuối (handoff): "Suggest: chạy hbc-sync"
B) Thêm config option trong customize.toml: `auto_sync_after_update`
C) Cả A và B — suggest (hybrid mode) + configurable auto behavior
X) Other

**[AI Suggestion]: C** — Thỏa REQ-005 (cả 3 trigger mode). Dòng suggest ở handoff = hybrid mode (gợi ý). Config flag = auto-chained mode (tự động). Manual mode không cần sửa gì (user gọi trực tiếp). Thay đổi tối thiểu, không phá existing skills.

[Answer]: C

### Question 6: Change Description Input
User mô tả thay đổi bằng cách nào khi gọi sync?

A) Free-text description khi gọi
B) Auto-detect bằng diff (compare frontmatter.updated timestamp)
C) Kết hợp: auto-detect changes + user supplement thêm context
X) Other

**[AI Suggestion]: C** — Thỏa câu trả lời Round 2 Q4 của bạn ("user đưa thông tin thay đổi, AI đọc source tự suggest"). Auto-detect tài liệu nào vừa đổi (timestamp), user mô tả thêm ngữ nghĩa thay đổi để AI hiểu impact chính xác.

[Answer]: C

