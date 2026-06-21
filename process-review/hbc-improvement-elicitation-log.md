---
title: "HBC Improvement — Nhật ký Elicitation (Q&A nguyên văn)"
doc_type: elicitation-log
companion_of: hbc-improvement-proposal-2026-06-20.md
purpose: "Lưu nguyên văn mọi câu hỏi đã đặt + câu trả lời của maintainer (gồm các câu trả lời tự-do/redirect bị nén mất trong bảng quyết định)."
date_started: "2026-06-20"
---

# Nhật ký Elicitation — HBC Improvement

> Đây là bản ghi **đầy đủ** quá trình hỏi-đáp tạo ra `hbc-improvement-proposal-2026-06-20.md`. Bảng quyết định trong proposal đã nén; file này giữ **câu trả lời gốc** (đặc biệt các chỉ đạo tự-do + các yêu cầu research-first). `(KN)` = chọn phương án Khuyến nghị.

## Quy ước & meta-quyết định của maintainer
- **Cách làm việc:** "Bạn chỉ nên phân tích các khía cạnh bạn thấy được qua tài liệu/context/**source skill (cần đọc nó)**. Còn lại **hỏi tôi** các câu hỏi để làm rõ càng nhiều càng tốt. Câu hỏi đều là tương tác có option và **suggest đáp án tốt nhất**."
- **Cấu trúc:** Tổng workflow (10 câu, dùng brainstorming lenses) → từng skill 10 câu. Trọng tâm: *skill đang tự-quyết quá nhiều → bị hallucination*.
- **Trước mỗi mảng cần chuẩn ngành:** dùng **bmad research** trước rồi mới hỏi (DB design, test-spec, task-breakdown TDD, business-flow, test-plan, khung V-Model).
- **Quyết định LỚN phải qua subagent độc lập review** (đã bắt được hallucination thật).
- **Mục đích tài liệu (chốt):** *backlog tổng-hợp-vấn-đề + suggest cải-tiến HBC* — KHÔNG sửa code ở repo này (repo chỉ là bản cài HBC). Deliverable = tài liệu.

---

## PHẦN A — Tổng workflow (10 câu)

- **A1 [Pre-mortem]** Workflow đi thẳng REQ→design→code, không có chốt kiểm chứng domain-model → **Thêm Model-Spike giữa P1–P2 + gate P1 "model đã kiểm chứng"** (KN). *(Sau bị adversarial hạ xuống HYPOTHESIS — F-4.)*
- **A2 [Reversal]** Gate giữ PASSED dù artifact đổi version → **Gate tự STALE khi version-set đổi** (KN).
- **A3 [Gap]** Đổi model lõi/shared chỉ ADVISORY, Impact key REQ-id per-feature → **Engine re-baseline cross-feature (hbc-rebaseline + Impact declare-shared)** (KN).
- **A4 [What's missing]** Quyết định mở (TBD) rò vào doc "complete" → **ADR first-class + decision-gate** (KN).
- **A5 [Autonomy ⭐]** Skill tự-quyết quá nhiều → **Mặc định HỎI tại "quyết định miền"** (phân biệt cơ-học vs miền) (KN).
- **A6 [First-principles]** Đơn vị thay đổi = feature → **Thêm cấp "baseline/epic change"** (KN).
- **A7 [Edge]** Một mức nghi lễ cho mọi feature → **Cờ maturity exploratory|stable** (KN).
- **A8 [Analogy CI]** Gate chạy thủ công 1 lần → **Re-validate tự động khi artifact đổi** (KN).
- **A9 [Integrity]** Matrix khuyết mà gate vẫn pass → **Gate diff D-02 vs matrix bắt buộc + verify code_ref** (KN).
- **A10 [Verification]** P3 reconcile theo task-breakdown cũ → **Drift-detector code vs D-19 hiện hành (MODEL_DRIFT)** (KN).

---

## PHẦN B — Từng skill

### B.1 — hbc-create-requirements
- B1-1 Stale soft-gate → LLM bịa REQ → **Bắt user duyệt REQ-list trước Generation** (KN).
- **B1-2 [chỉ đạo lớn, nguyên văn]:** *"Brainstorming không phải bị hallucination mà vấn đề đang gặp phải là khách hàng khi đưa ra requirement thường chỉ là 1 ý tưởng. Thứ nhất chưa biết được ý tưởng đấy có khả thi không (cần đánh giá dựa trên những cái hiện có: source code hiện tại, framework, bản thân ý tưởng đó, ...). Sau khi đánh giá ý tưởng đó khả thi nhưng thường khách hàng cũng chưa hình dung được cụ thể họ muốn gì nên cần brainstorming với họ. Hiện tại brainstorming của bmad khá hay nhưng bmad brainstorming cần 2 cái input là: chủ đề và mong muốn ra cái gì. 2 cái này sẽ cần có 2 câu hỏi lần lượt để suggest cho họ... Nhưng thực ra brainstorming đôi lúc cũng là optional do đôi khi task yêu cầu thực sự là 1 task đơn giản. Vậy nên nên có 1 option discovery nhanh (bước này thực ra là cần với cả 2). Kể cả sau khi brainstorming xong vẫn nên có các câu hỏi discovery để khám phá thêm góc nhìn. Rồi khi ra được tài liệu requirement cần có các bước review lại bao gồm review adversarial, review edge case (cả 2 đều là của bmad và bắt buộc user phải làm). Các quy trình bên trên cũng nên có tham khảo từ source code hiện tại."*
  → Pipeline intake: **Ý tưởng → Feasibility (đọc source+framework) → Quick Discovery (cả 2 nhánh) → HỎI có brainstorming sâu (optional) → Brainstorming (2 câu suggest: chủ đề + output) → Discovery bổ sung bắt buộc → Sinh D-02 → bắt buộc adversarial + edge-case review → gate.**
- B1-3 NFR LLM bịa ngưỡng → **HỎI số; không có → đánh dấu ASSUMPTION (vào ADR), KHÔNG bịa** (KN).
- B1-4 Validate cấu trúc, không kiểm model-đúng → **Thêm reality-check + nối Model-Spike A1** (KN).
- B1-5 → **Bước Feasibility bắt buộc, đọc source+framework** (KN).
- B1-6 → **Quick Discovery luôn; rồi HỎI có cần brainstorming sâu** (KN).
- B1-7 → **2 câu hỏi suggest lần lượt (topic → output)** (KN).
- B1-8 → **Discovery bổ sung bắt buộc sau brainstorming** (KN).
- **B1-9 [nguyên văn]:** *"gọi lần lượt là bmad-review-adversarial-general, bmad-review-edge-case-hunter và là bắt buộc."*
- B1-10 → **Bắt buộc đọc source/framework ở feasibility + reality-check + brownfield** (KN).

### B.2 — hbc-create-er-diagram
- **B2-Q1 [redirect, nguyên văn]:** *"Dùng bmad research để tìm hiểu các quy trình thiết kế 1 database đi. sau đó giải thích các quy trình đấy cho tôi để tôi lựa chọn."* → Research ra **quy trình DB 3 cấp (Conceptual/Logical/Physical)**. Chốt: **Áp dụng 3-cấp, ASK-gate mỗi cấp** (conceptual=entity/quan hệ/cardinality khớp REQ; logical=normalization/denorm/PK/constraint; physical=index/ondelete/kiểu) (KN).
- B2-2 → **Check mỗi entity/field/constraint truy về ≥1 REQ** (chống gold-plating) (KN).
- B2-3 → **Bắt buộc HỎI ondelete cho mỗi FK quan trọng + rationale** (KN).
- B2-4 → **Index = ĐỀ XUẤT cần xác nhận + lý do truy vấn** (KN).
- B2-5 → **Conceptual đối chiếu REQ + D-06 business-flow** (KN).
- B2-6 → **Bản nháp logical D-19 là đối tượng Model-Spike (A1) trước cascade** (KN).
- B2-7 → **Bắt buộc đọc DB schema + models/migration thật làm ground-truth, log mọi lệch** (KN).
- B2-8 → **Semantic review: lens độc lập (skeptic) + user sign-off khi passed** (KN).
- B2-9 → **Gộp version-bump theo phiên + cảnh báo churn cao** (KN).
- B2-10 → **Ghi quyết định DB (denorm/ondelete/index/constraint) vào Decision Record + rationale + REQ** (KN).

### B.3 — hbc-create-test-spec
- B3-1 LLM tự sinh TC → "xanh giả" → **Bắt buộc sanity-check cho TC nhạy cảm** (KN).
- B3-2 test-data bịa → **Ground test-data vào D-19 entity/constraint thật** (KN).
- B3-3 D-27 nặng nhất, sinh trước khi frozen → **Gate độ-sâu theo maturity (A7)** (KN).
- B3-4 → **Chốt facet + edge in/out-scope per-REQ TRƯỚC generate** (KN).
- **B3-5 [redirect, nguyên văn]:** *"Đầu tiên bạn cần dùng bmad research để biết cách viết d27 tốt nhất. Tôi thấy nó viết đang ko sát với business, db, requirement, ... Test nghiệp vụ cực yếu."* → Research ra **kỹ thuật specification-based**. Chốt: **Bắt buộc map kỹ-thuật↔nguồn theo loại REQ** (Decision-Table←business-rule; State-Transition←lifecycle phủ cả transition sai; EP+BVA←D-19 constraint; Use-Case←D-06; Example-Mapping = elicitation đầu) (KN).
- B3-6 → **LLM đề xuất severity; critical-path phải user xác nhận** (KN).
- B3-7 → **Khi có code → đối chiếu TC vs hành vi thật + cảnh báo giả định sai** (KN).
- B3-8 → **Semantic review lens độc lập + user sign-off** (KN).
- B3-9 → **Bắt buộc bmad-review-edge-case-hunter + adversarial trên D-27 trước Phase-2 gate** (KN).
- B3-10 → **Gộp churn theo phiên + cảnh báo** (KN).

### B.4 — hbc-task-breakdown
- **B4-Q1..4 [redirect/nghi ngờ, nguyên văn]:** *"Lại dùng bmad research tìm kiếm xem input hiện tại đã đủ để viết task breakdown chưa. Với bình thường trong quy trình tdd thì người ta sẽ chia task như thế nào dùng chuẩn gì"* + *"Tôi đang nghi ngờ chưa đủ input để break task."* → Research ra **Kent Beck test-list + INVEST + SPIDR + vertical-slice**. Chốt:
  - **Chuẩn: vertical-slice + INVEST + SPIDR + Kent Beck test-list** (bỏ chia ngang theo category) (KN).
  - **+Input: D-06 business-flow (paths) · Acceptance Criteria per-REQ tường minh · Spike cho unknown (nối A1) · ADR + hiện trạng code (NEW/CHANGE/đã-có)** (multi-select, chọn cả 4).
- B4-5 Phase-entry → **Mặc định KHÔNG override; override phải ghi lý do + cảnh báo** (KN).
- B4-6 Completeness → **Duyệt bảng 'path/REQ-facet/entity → slice nào' trước generate** (KN).
- B4-7 REQ coverage → **Thêm validate mọi REQ D-02 có ≥1 task** (KN).
- B4-8 Autonomy → **Ranh giới mơ hồ → HỎI; assumption ghi ADR** (KN).
- (kế thừa) staleness A2/A8; rebaseline A3.

### B.5 — hbc-implement
- B5-1 → **Thêm MODEL_DRIFT: entity/field D-19 hiện hành phải có trong code (A10)** (KN).
- B5-2 → **KHÔNG nhúng spec-ref vào code/test + lint chặn (IMP-02)** (KN).
- B5-3 → **RED-evidence soft NHƯNG test phải FAIL đúng nhánh + sanity chống xanh-giả** (KN).
- B5-4 → **Spec/task STALE → chặn implement, bắt re-derive trước (A2)** (KN).
- B5-5 → **Batch vẫn dừng checkpoint ở quyết-định-miền + khi test PASS ngay (dấu hiệu sai)** (KN).
- B5-6 → **GREEN chỉ dùng entity/field có trong D-19 hiện hành** (KN).
- B5-7 → **Coverage là điều kiện CẦN không đủ (+MODEL_DRIFT + sanity)** (KN).
- B5-8 → **Brownfield: đọc code hiện có, phân biệt sửa-vs-tạo, không trùng lặp** (KN).
- B5-9 → **DONE cần test có sanity chống xanh-giả (B3-1)** (KN).
- B5-10 → **Quyết định miền phát sinh khi code → DỪNG hỏi (cả batch); headless → blocked (A5)** (KN).

### B.6 — hbc-phase-gate
- B6-1 → **QUALITY adversarial (skeptic+acceptance) bắt buộc + bằng chứng định lượng; bất đồng → CONTESTED** (KN).
- B6-2 → **Số liệu gate do script tính, không LLM khai** (KN).
- B6-3 → ⚠️ **ĐÃ CÓ SẴN** (entry-gate không bị lenient hạ — gate:71 + test); chỉ MỞ RỘNG cho item correctness/model. *(Lỗi review: đề xuất thứ đã tồn tại.)*
- B6-4 → **Waiver cần rationale + KHÔNG miễn item tính-đúng** (KN).
- B6-5 → **PASS phase thiết kế (1/2) cần user sign-off** (KN).
- B6-6 → **Bằng chứng mơ hồ → CONTESTED/hỏi, không auto-pass (A5)** (KN).
- (kế thừa) A1/A2/A4/A8/A9/IMP-03 cắm vào gate.

### B.7 — hbc-traceability (Impact engine)
- B7-1 → **Đổi doc có downstream → cascade BẮT BUỘC (block complete tới khi Impact chạy)** (KN).
- B7-2 → **Skill tự ghi matrix ở phase + gate verify đầy đủ (A9)** (KN).
- B7-3 → **Drift-watch: artifact đổi version chưa cascade → cảnh báo/STALE (A8)** (KN).
- B7-4 → **RECONCILE adversarial + bằng chứng, không tự chấm** (KN).
- B7-5 → **Thay đổi phá-cấu-trúc → route sang hbc-rebaseline (A3), KHÔNG fork-task** (KN).
- B7-6 → **Cascade yêu cầu matrix đầy đủ trước khi chạy (khuyết → blocked)** (KN).

### B.8 — hbc-create-business-flow-diagram (D-06)
- Research trước: **BPMN swimlane + path-coverage + AS-IS/TO-BE + confirm-with-participants.**
- B8-1 → **Ép swimlane theo actor + gateway (BPMN-style), 3–7 lane** (KN).
- B8-2 → **Bắt buộc đủ happy + alternate + exception path; thiếu → flag** (KN).
- B8-3 → **AS-IS ground vào hệ thống thật (code/hành vi hiện có)** (KN).
- B8-4 → **Confirm danh sách flow/actor/path với user TRƯỚC generate** (KN).
- B8-5 → **REQ flow-facet → phải có flow; flow phantom → flag** (KN).
- B8-6 → **Gán ID/nhãn mỗi path → task-breakdown + test tham chiếu** (KN).
- B8-7 → **D-06 vào bộ review bắt buộc cùng D-02 (adversarial + edge-case)** (KN).
- (inherited) semantic/churn/autonomy/grounding.

### B.9 — hbc-create-test-plan (D-26)
- Research: **IEEE 829 (⚠️ đã withdrawn → ISO/IEC/IEEE 29119-3 là chuẩn hiện hành).**
- B9-1 → **Schedule do user cung cấp / placeholder, KHÔNG bịa ngày** (KN).
- B9-2 → **Risk derive từ REQ/D-06/complexity thật + likelihood/impact user xác nhận** (KN).
- B9-3 → **Chốt in/out-scope với user trước generate** (KN).
- B9-4 → **D-26 approach chỉ định kỹ thuật test per scope-area → D-27 (B3-5) bám theo** (KN).

### B.10 — hbc-create-coding-standards (D-12, SHARED)
- B10-1 → **Bắt buộc derive từ code thật khi có codebase; deviation → flag/hỏi** (KN).
- B10-2 → **Rule máy-kiểm-được → lint + gate P3 enforce (IMP-02)** (KN).
- B10-3 → **Preference KHÔNG tự-default im lặng; trình để user xác nhận** (KN).
- B10-4 → **Thêm cơ chế update D-12 khi convention đổi + cascade advisory (A3)** (KN).

### B.11 — hbc-create-glossary (D-03, SHARED)
- B11-1 → **Definition ground source + user xác nhận khi suy ra** (KN).
- B11-2 → **Consistency check cross-doc (term D-02/D-06/D-19 thiếu glossary → flag; orphan → flag)** (KN).
- B11-3 → **Glossary = ubiquitous language (DDD), đối chiếu entity/field D-19 + code** (KN).

### B.12 — hbc-create-api-spec (D-21) — **N/A** (Odoo module nội bộ không expose API).

### B.13 — hbc-check-implementation-readiness (review độc lập subagent)
- B13-1 → **Parse cột matrix: verify code_ref/test_ref non-empty per REQ (A9/B7-2)** *(case: "39/39 code_ref" giả vô hình)*.
- B13-2 → **Thêm input task-breakdown + reconcile REQ↔TASK↔current-design (B4-6)**.
- B13-3 → **Thêm D-19 vào seam + MODEL_DRIFT (A10/B5-1)**.
- B13-4 → **Version-coherence ở seam (IMP-01/A2)**.
- B13-5 → **Scope-hoá như D-27 (TC/row-level), không findall toàn file (chống paste-appendix)**.
- B13-6 → **Sửa headless-contract khớp engine (`reason`)**.
- (giữ) `missing_from_matrix` đã có — bắt 040-042 nếu chạy đúng nguồn.

### B.14 — hbc-migrate (review độc lập subagent)
- B14-1 → **Engine emit `missing_from_matrix` (D-02 vs matrix diff)**.
- B14-2 → **Scope re-prefix vào cột id; dry-run diff thực** *(regex global dễ hỏng code-ref)*.
- B14-3 → **Mở rộng re-prefix sang implementation-artifacts/gates HOẶC cảnh báo** *(traceability gãy ngầm)*.
- B14-4 → **Cảnh báo khi dirty-guard off + timestamp unique (no backup overwrite)**.
- B14-5 → **Đồng bộ contract↔engine (headless/decision-log/validation)**.
- B14-6 → **Xác nhận A3 hbc-rebaseline = engine MỚI, KHÔNG extend migrate**.

### B.15 — hbc-project-init (Phase 0)
- B15-1 → **Re-run detect drift + offer update (không chỉ create-missing)** (KN).
- B15-2 → **Thêm baseline Architecture (E-1) + applicability-catalog (E-8) ở Phase 0** (KN).
- B15-3 → **Brownfield → bắt derive baseline D-19 (+D-21 nếu có API) từ hệ thống thật** (KN).
- B15-4 → **Confirm classify + stack/domain/conventions với user** (KN).

### B.16 — Phase 4 (test-execution + acceptance-check)
- B16-1 → **Verify ref THẬT non-empty + MODEL_DRIFT clean, không tin matrix-string** (KN).
- B16-2 → **Bổ sung model-match + sanity; coverage CẦN-không-đủ** (KN).
- B16-3 → **Check D-27 STALE (version) trước khi map; stale → cảnh báo/blocked** (KN).
- B16-4 → **Khi Part D áp dụng → acceptance thêm tiêu chí UX↔mockup** (KN).

### B.17 — 5 agent (ba/architect/qa/dev/tester)
- B17-1 → **Persona mọi agent: ưu tiên ELICIT > auto-proceed ở quyết-định-miền** (KN).
- B17-2 → **Cập nhật mỗi agent điều phối bước mới của phase mình** (BA pipeline / Architect model-spike+DB-3-tier+architecture / QA technique-map+edge-review / Dev MODEL_DRIFT+no-spec-ref+sanity / Tester model-match) (KN).
- B17-3 → **Mọi agent HALT-on-unclosed-predecessor nhất quán + log override** (KN).
- B17-4 → **Agent gọi subagent độc lập cho review/semantic (không tự chấm)** (KN).

> **COVERAGE HOÀN TẤT** — 16 skill + 5 agent (B.1–B.17; B.12 N/A). Không còn skill defer.

---

## PHẦN D — Lỗ hổng UX/UI
- Research: UX artifacts · component-driven + visual-regression · design tokens · ATDD.
- **UX-1 [nguyên văn nuance]:** *"D14 nhưng vẫn cần claude design nhé. claude design là 1 tool optional mà cần hỏi người dùng xem họ có dùng ko. Nếu có dùng thì sẽ cần thiết kế để d14 và claude design link được với nhau nó mới sát được thực tế."* → **Thêm D-14 (Phase 2); Claude Design OPTIONAL (hỏi user); nếu dùng → D-14 ↔ Claude Design link.**
- UX-2 → **Bước design-sync chính thức: mockup ↔ D-14 ↔ matrix + cascade** (KN).
- UX-3 → **Shared design-system map: component mockup ↔ code ↔ token** (KN).
- UX-4 → **Mở rộng matrix: REQ → screen → component → code → test** (KN).
- UX-5 → **UI-acceptance (ATDD/BDD) per-screen + visual-regression (khi dùng Claude Design)** (KN).
- UX-6 → **Design tokens 1 nguồn (khi dùng Claude Design)** (KN).
- UX-7 → **D-14 ở Phase 2; outside-in ATDD: screen-spec → acceptance test → UI code** (KN).
- UX-8 → **Maturity-gate UX: wireframe low-fi sớm; high-fi mockup chỉ khi model/flow frozen (A7)** (KN).
- *(F-5 sau: Part D conditional — phần lớn N/A cho Odoo back-office.)*

---

## PHẦN E — Lỗ hổng khung chuẩn (V-Model + catalog)
- **[nguyên văn]:** *"research bộ khung phát triển chuẩn của hbc"* → HBC = **V-Model phân pha + catalog tài liệu**.
- ⚠️ **Đính chính (subagent):** KHÔNG có file catalog D-NN; `hbc_validation.py` 0 literal `D-0x`. D-NN nằm rải rác glob + module-help.csv + prose; **tên** đã verify đúng nhưng **không có catalog canonical** (= lỗ hổng phụ).
- E-1 → **Thêm D-08/09 Architecture Design đầu Phase 2** (KN).
- E-2 → **Thêm Detailed Design (sequence/logic) cho REQ phức tạp TRƯỚC code** (KN).
- E-3 → **Gộp use-case (actor-goal + scenarios) vào D-06** (KN).
- E-4 → **Inline table-def trong D-19; tách D-20 chỉ khi cần** (KN).
- E-5 → **Thêm D-01 feature-overview nhẹ đầu Phase 1** (KN).
- E-6 → **Deliverable optional: security/deployment/data-migration design — bật khi feature chạm** (KN).
- E-7 → **V-pairing: architecture↔integration-test · detailed↔unit** (KN).
- E-8 → **Applicability matrix per-feature (required/optional/N-A + lý do) + gate** (KN).

---

## ADVERSARIAL REVIEWS (subagent độc lập) + hiệu chỉnh

### Vòng 1 (toàn doc)
- Bắt: **provenance Phần E bịa** (catalog), **B6-3 đã-có-sẵn**, **IEEE 829 withdrawn**; xác nhận rubber-stamp / 25:1 / nhân-quả chưa chứng minh. → Sửa factual + thêm Phần F.

### Vòng 2 (readiness + migrate) → B.13/B.14 (ở trên).

### Vòng 3 (re-review sau vá) → execute-consolidation
- Bắt: tally cũ "11 skill/~90" sai; F-1/F-2/F-6 là "paper-fix"; mâu thuẫn A1(commit vs hypothesis), Part-D(N/A vs top-gap); warning #8 cũ; recursion F-3.
- **[nguyên văn]:** *"Execute-consolidation: sửa tại chỗ cho hết mâu thuẫn"* + *"Chỉ nhóm S/ready/ROI-cao làm ngay; còn lại = backlog 'cần-spike'."*
- → CHỐT: rổ 🟢 COMMIT NGAY (8 item) vs 🟡 CẦN SPIKE; reconcile tally; A1=hypothesis; Part D=conditional.

## PHẦN F — Kiểm soát (sau adversarial)
- F-1 De-ceremony (mỗi ADD kèm 1 BỎ; default-light theo maturity) · F-2 Sizing Effort/Confidence/Dep/ROI · F-3 Quyết-định-LỚN qua subagent độc lập · F-4 fix-chưa-chứng-minh = hypothesis+pilot · F-5 Part-D conditional · F-6 success-metrics + baseline.

---
### Vòng 4 (scoped, CUỐI) — verify B.15-17 + quét nhất quán
- B.15/B.16/B.17 đều **SOUND** (mọi claim truy được source, không sai). Bonus: B17-3 nói nhẹ — **cả 5 agent đều chỉ "warn"**, HALT thật ở tầng skill (đã cập nhật).
- Tally **16 skill + 5 agent / ~145** nhất quán; 0 leftover; cross-ref resolve; trích B6-3 chính xác.
- Cosmetic dòng-32 "defer" → đã đánh dấu ✅-đã-giải-quyết.
- **Verdict độc lập: STOP — finalize, không lỗi blocking.**

---
**TRẠNG THÁI: CHỐT (finalized 2026-06-21).** Coverage hoàn tất (16 skill + 5 agent), 4 vòng adversarial độc lập, tally nhất quán. Dừng đánh bóng — bước tiếp là triển khai (rổ 🟢) / pilot (🟡), không phải sửa tài liệu.
