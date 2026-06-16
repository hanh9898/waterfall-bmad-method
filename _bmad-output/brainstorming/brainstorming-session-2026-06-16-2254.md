---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'Đập đi xây lại hbc-sync như một phần hài hòa của bộ skill HBC — trọng tâm: hợp đồng đồng bộ chung cho cả suite'
session_goals: 'Một concept/kiến trúc mới neo trên hợp đồng chung (bao gồm mô hình phụ thuộc), đủ rõ để viết spec. SR boundary mở để xét lại; bất biến cứng = đồng bộ không bao giờ âm thầm làm lệch nội dung.'
selected_approach: 'progressive-flow'
techniques_used: ['First Principles Thinking', 'Mind Mapping', 'Morphological Analysis']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Hanhnt2
**Date:** 2026-06-16 22:54

## Session Overview

**Topic:** Đập đi xây lại `hbc-sync` để hòa hợp với cả bộ skill HBC — trọng tâm là **hợp đồng đồng bộ chung cho cả suite** (thay vì một orchestrator đứng ngoài áp lên 10 skill).

**Goals:** Rời phiên với một concept/kiến trúc mới, neo trên hợp đồng chung (bao gồm mô hình phụ thuộc derivation-vs-consumption và doc-vs-code), đủ rõ để viết spec.

### Session Setup

- **Ràng buộc:** Ranh giới single-responsibility (sync chỉ điều phối) **mở để xét lại**.
- **Bất biến cứng:** Đồng bộ không bao giờ *âm thầm làm hỏng/lệch* nội dung.
- **Bối cảnh đầu vào:** Báo cáo analyze hbc-sync (grade good, 6 high) + đánh giá concept (graph trộn derivation/consumption; D-21 API spec & D-03 glossary là lá; phụ thuộc hợp đồng update chưa tồn tại của 10 skill; verify thực thi ≠ verify lan truyền).

## Technique Selection

**Approach:** Progressive Technique Flow (rộng → hẹp dần)
**Journey Design:** Đi từ bóc-giả-định-tận-gốc tới chọn kiến trúc và lộ trình xây.

**Progressive Techniques (đề xuất):**

- **Phase 1 — Expansive Exploration:** First Principles Thinking — bóc mọi giả định, hỏi "nếu xây lại từ đầu, đồng bộ thực chất là gì".
- **Phase 2 — Pattern Recognition:** Mind Mapping — gom ý tưởng Phase 1 thành các "trụ cột" nền của bản xây lại.
- **Phase 3 — Idea Development:** Morphological Analysis — với mỗi trụ cột, liệt kê tham số & lựa chọn, ghép thành các ứng viên kiến trúc.
- **Phase 4 — Action Planning:** Decision Tree Mapping — chọn ứng viên kiến trúc và vạch lộ trình xây + bước kế.

**Journey Rationale:** Chủ đề là "đập đi xây lại từ nền", nên hành trình bắt đầu bằng First Principles (đúng tinh thần), rồi tụ dần về một kiến trúc khả thi và lộ trình hành động.

## Technique Execution Results

### Phase 1 — First Principles Thinking

**Chân lý nền đã bóc ra:**

**[Nền #1]: Không ai được hành động trên thông tin đã cũ**
_Concept:_ Đồng bộ tồn tại để bảo vệ **tính hợp lệ của công việc hạ nguồn**, không phải để "cập nhật tài liệu". Lệch = ai đó đang xây/test sai thứ.
_Novelty:_ Đặt mục tiêu vào "trạng thái hợp lệ", không vào "động tác cập nhật".

**[Nền #2]: Mô hình PUSH, bị chặn bởi vòng đời waterfall**
_Concept:_ Luôn đẩy cái mới xuống, nhưng chỉ trong phạm vi task chưa xong. Artifact của task đã done thì đóng băng.
_Novelty:_ Sync chỉ chạy trên **live frontier** (đang-làm), không trên toàn bộ tài liệu.

**[Nền #3]: Thay đổi sau khi done = TASK MỚI**
_Concept:_ Đổi sau done không sửa ngược artifact cũ — sinh task mới.
_Novelty:_ Cascade dừng tự nhiên ở biên "done" → không cần rollback/transactionality toàn cục.

**[Nền #4]: Hệ thống SUGGEST, con người DECIDE**
_Concept:_ Sync đề xuất "nên làm gì", user bấm nút.
_Novelty:_ Củng cố bất biến cứng — không bao giờ âm thầm đổi nội dung.

**[Nền #5]: Đừng tạo nguồn-sự-thật thứ hai**
_Concept:_ hbc-sync cũ tự nuôi `.sync-manifest.json` + DAG tĩnh — bản sao nghèo của thứ matrix + task-status + phase-gate đã biết chính xác hơn.
_Novelty:_ Bản xây lại không sở hữu state — chỉ đọc từ ba nguồn đã có.

**[Nền #6]: Đồ thị tác động là theo REQ, không theo tài liệu**
_Concept:_ "Đổi REQ-010 ảnh hưởng gì" = đọc hàng REQ-010 trong matrix (design_ref/code_ref/test_ref của riêng nó).
_Novelty:_ Tác động chính xác từng artifact; hết regenerate cả tài liệu vì một dòng.

**Phát hiện từ source — ba tầng sự thật đã tồn tại:**
- Phase: `hbc-phase-gate` (PASSED/FAILED) — mặt-tiền waterfall.
- Task: `task-breakdown.md` cột `status` (TODO/IN_PROGRESS/DONE).
- Requirement: traceability matrix (7 cột: req_id, story_id, design_ref, code_ref, test_ref, gate_status, timestamp) — "single source of truth for which requirement is covered where".

**🎯 Quyết định kiến trúc (lựa chọn B):** Sync KHÔNG còn là skill riêng. Nó trở thành **một capability nhúng trong `hbc-traceability`** (vì traceability đã sở hữu matrix). Sync = một capability đọc-matrix + suggest, đứng cạnh Initialize/Update/Report/Audit.

**[Nền #7]: Cascade order = chuỗi phase waterfall, không phải đồ thị**
_Concept:_ Với mỗi REQ đổi, đi theo design→test→code theo thứ tự lifecycle, bỏ qua phần done. Không topological sort.
_Novelty:_ Xóa toàn bộ load-graph/analyze-impact/dependency-graph.yaml — thay bằng bảng ref-type→skill + freeze-check.

**[Nền #8]: Impact là artifact-centric + có HAI loại lan**
_Concept:_ Đổi REQ-010 → đổi `Customer` → mọi REQ trỏ tới `Customer` đều vào diện ảnh hưởng. Sync đọc CẢ CỘT (bipartite REQ↔artifact).
_Novelty:_ Matrix CHÍNH LÀ consumption graph (suy từ dữ liệu thật). Hai loại lan: DỌC (apply, hạ nguồn REQ đổi) vs NGANG (verify, REQ dùng chung artifact).

### Phase 3 — Morphological Analysis (RỖNG-B, RỖNG-C)

**RỖNG-B — thay đổi không gắn REQ (glossary D-03, coding-standard D-12): CA BIÊN.**
- Đổi định nghĩa *độc lập* (không do REQ) là **hiếm** → không phải đường chính.
- Xử lý: **advisory nhẹ** — reverse-text-scan tìm thuật ngữ/quy tắc đổi trong artifact chưa-đóng-băng, gắn confidence, gợi ý review. Không index phải bảo trì, không tự sửa.
- Giải luôn nghịch lý "D-03 thành lá" của bản cũ: glossary cascade bằng quét-tham-chiếu lúc cần, không bằng cạnh khai báo.

**RỖNG-C — verify "đã lan ĐÚNG": 3 lớp.**
1. Deterministic: validator sẵn có pass (`validate-implementation.py`, facet coverage).
2. Matrix tươi: ô REQ→artifact có timestamp mới.
3. **LLM semantic review** (user thêm): đọc thay-đổi-gốc + artifact-đã-cập-nhật, phán "đã nhập đúng nghĩa chưa". Cũng xử lý lan-ngang-verify (REQ-022). Đồng bộ với `semantic-review-rubric.md` của suite.

### Phase 4 — Kiến trúc hội tụ + lộ trình

**Capability "impact" trong hbc-traceability:** ĐỌC sự thật → SUY tác động → SUGGEST → (user apply) → RECONCILE.
- ĐỌC (không sở hữu state): matrix · task-breakdown.status · phase-gate.
- SUY (artifact-centric, quét cả cột): lan DỌC (apply) + lan NGANG (verify), lọc qua freeze-check (done → flag "tạo task mới").
- SUGGEST: trình impact + "chạy skill nào, thứ tự waterfall nào"; không tự sửa.
- RECONCILE: verify 3 lớp.

**Với hbc-sync cũ:**
- VỨT: dependency-graph.yaml, load-graph.py, analyze-impact.py, .sync-manifest.json, topological sort.
- GIỮ & chuyển vào traceability: cờ `--invoked-by-sync` (BR-13), headless contract, decision log.
- LÀM MỚI (nhỏ): bảng ref-type→skill, freeze-check, reverse-text-scan (B), reconcile (validator + Audit + LLM review).

**RỖNG-A — Trigger/Detection: USER-DECLARED là chính.**
- User khai "tôi đổi REQ-010" = changed-set chính thức.
- Git `git diff` chạy phụ trợ: gợi ý nhẹ nếu thấy artifact đổi mà user chưa khai; user quyết.
- KHÔNG hash manifest. Git lo bootstrapping + drift + out-of-band edits (đóng 3 lỗ hổng concept ban đầu).

## Blueprint cuối — "impact" capability trong hbc-traceability

**Vòng đời 5 nhịp:** DECLARE → IMPACT → SUGGEST → APPLY (user) → RECONCILE

1. **DECLARE (trigger):** user khai REQ/artifact đổi; git diff đối chiếu, đề xuất bổ sung; user confirm changed-set.
2. **IMPACT (suy, artifact-centric):** đọc matrix theo CẢ CỘT →
   - lan DỌC: hạ nguồn của REQ đổi (design→test→code theo thứ tự waterfall).
   - lan NGANG: REQ khác dùng chung artifact → diện "verify".
   - lọc FREEZE-CHECK (matrix gate_status + task-breakdown status + phase-gate): cái đã done → KHÔNG sửa, flag "tạo task mới".
   - nhánh-B (hiếm): glossary/coding-standard đổi → reverse-text-scan → advisory review list.
3. **SUGGEST:** trình impact (dọc/ngang/đóng-băng) + "chạy skill nào, thứ tự nào"; KHÔNG tự sửa.
4. **APPLY:** user bấm; sync gọi owning skill ở update mode (cờ `--invoked-by-sync` chống loop).
5. **RECONCILE (verify 3 lớp):** validator pass + matrix tươi + LLM semantic review (đã nhập đúng nghĩa? lan-ngang còn đúng?).

**Nguồn sự thật (chỉ ĐỌC, không sở hữu):** traceability matrix · task-breakdown.status · hbc-phase-gate · git.

**Vứt khỏi bản cũ:** DAG tĩnh + dependency-graph.yaml + load-graph.py + analyze-impact.py + .sync-manifest.json + topological sort.

## Next Steps (Action Plan)

1. Viết spec cho capability "impact" trong hbc-traceability (dùng `bmad-spec` hoặc workflow-builder Edit) — input chính là blueprint trên.
2. Định nghĩa cụ thể: bảng `ref-type → owning-skill`; hợp đồng freeze-check (đọc 3 nguồn); rubric cho LLM semantic-review của reconcile.
3. Xác nhận hợp đồng `update --invoked-by-sync` ở 10 skill (tiền đề; degrade graceful nếu thiếu).
4. Lên kế hoạch gỡ/deprecate `src/hbc-sync` cũ sau khi capability mới chạy được.

## Cập nhật sau phiên — 2026-06-17 (đồng bộ với spec)

**✅ Đã viết spec:** `_bmad-output/specs/spec-traceability-impact/` (SPEC.md + 4 companion). Action Plan #1 hoàn tất; #2 đã chốt trong companion (`ref-skill-map.md`, `edge-handling.md` + rubric adopted). #3, #4 vẫn là việc triển khai về sau (đã thành Assumption/Non-goal trong spec).

Spec đã qua **3 vòng review** sau blueprint. Vài chỗ spec **tiến hóa vượt blueprint** — ghi lại để nguồn không lệch contract:

- **RECONCILE (đổi so với blueprint):** blueprint ghi "verify 3 lớp (validator + matrix tươi + LLM)"; spec **hạ "matrix tươi" xuống đối chiếu phụ** → **2 trụ chính = validator + LLM semantic review** (review G4: matrix-tươi chỉ chứng minh "Update đã chạy", không chứng minh nội dung đổi).
- **DECLARE (bổ sung):** thêm chuẩn-hóa changed-set về REQ qua reverse-map (`code_ref`/`test_ref`/`design_ref`→`req_id`) cho thay đổi non-REQ; baseline git = working tree vs HEAD, override `--since <ref>`.
- **4 Open Question đã giải:** baseline git (working-tree vs HEAD); bảng ref→skill ở `customize.toml` của hbc-traceability; fallback skill thiếu contract = flag/`skill_no_update_contract`; deprecate hbc-sync hai nhịp.
- **17 edge-case** (từ edge-case-hunter) đã xử lý, dồn vào companion `edge-handling.md` — gồm: matrix chưa init, thay đổi chưa-trace, REQ id sai, no-op rỗng, `--since` sai, REQ bị xóa, flood artifact dùng chung, 3 nguồn freeze bất đồng, thiếu task-breakdown, ref không map skill, apply tập con, skill lỗi runtime, thiếu validator, re-suggest vô hạn, thuật ngữ phổ biến, concurrency.
- **Lưu ý granularity** (Assumption mới): độ chính xác apply/verify của lan-ngang bị chặn bởi độ mịn `design_ref` trong matrix — chấp nhận over-flag hơn bỏ sót.

Tham chiếu chi tiết quyết định: `_bmad-output/specs/spec-traceability-impact/.decision-log.md`.
