---
title: "HBC — Chia phase, chia công việc & phân role: nên học theo mô hình nào là tối ưu"
research_type: technical
research_topic: "HBC phase-division + work-breakdown + role-assignment — mô hình tham chiếu tối ưu"
date: 2026-06-21
author: bmad-technical-research (Hanhnt2)
status: draft
confidence_policy: "Claim quan trọng đối chiếu ≥2 nguồn độc lập; gắn confidence high/med/low; ưu tiên tác giả gốc + nguồn chính thống."
---

# HBC — Chia phase / chia công việc / phân role: học theo gì cho tối ưu

> 📖 Tài liệu nghiên cứu (web, June 2026). Mục tiêu: đối chiếu cấu trúc hiện tại của HBC với các thực hành chuẩn (phase-gating, incremental delivery, work-breakdown, spec-driven AI-era, quality pairing, lean/flow, role division) → rút ra điều **nên adopt / nên tránh**, kèm **danh mục tài liệu nguồn** có trích dẫn.

## 0. Phạm vi đã chốt (7 trục)

| # | Trục | Nội dung |
|---|------|----------|
| 1 | Phase-gating | Stage-Gate (Cooper), V-Model, waterfall-with-gates, Agile-Stage-Gate |
| 2 | Incremental & iterative | Patton/Cockburn, vertical slice, walking skeleton, dual-track agile |
| 3 | Work-breakdown / story slicing | INVEST, SPIDR, Lawrence patterns, WBS 100%-rule, Canon TDD test-list |
| 4 | Spec-driven & AI-era (2024–26) | GitHub Spec Kit, Amazon Kiro, BMad Method, SDD-vs-waterfall |
| 5 | Quality pairing / shift-left | V-Model test levels, shift-left (4 loại), TDD/BDD/ATDD |
| 6 | Lean / flow | Shape Up (appetite/scopes/hill chart/circuit breaker), Reinertsen flow, Kanban WIP |
| 7 | Role / ownership | RACI, Scrum accountabilities, SoD/test-independence, feature-vs-component team, multi-agent persona |

---

## 1. Kết luận điều hành (đọc cái này trước)

**Phát hiện cốt lõi:** Cấu trúc HBC hiện tại **đã trùng khớp đáng kinh ngạc với điểm hội tụ của các mô hình chuẩn** — nó là một **Agile-Stage-Gate hợp lệ** (gate + per-feature incremental + TDD loop), một **V-Model phân mảnh nhỏ** (mỗi feature = một V nhỏ → đúng "incremental shift-left"), và khớp với điểm hội tụ **spec → design → tasks → implement** mà Spec Kit/Kiro/BMad đang quy về. Phần lớn cải tiến là **đặt tên/hình thức hoá cái đã có**, cộng vài bổ sung có đòn bẩy cao.

**6 việc có đòn bẩy cao nhất (chi tiết §6):**

1. **Gate hai-tầng + thêm outcome `Recycle`** (Cooper): must-meet (knock-out, một "No" là chặn) vs should-meet (scorecard = các facet semantic-review). Gate được phép **trả feature về phase trước**, không chỉ pass/fail.
2. **Hình thức hoá cặp V-Model trên `v_pair`** (catalog HBC đã có field này!): mỗi design-facet khai báo *test level nào kiểm chứng nó* → biến "V-pair" từ ý ngầm thành cạnh design↔test enforce được trong ma trận.
3. **Vertical-slice là quy tắc cắt task ở Phase 3** + nhúng catalog SPIDR/Lawrence vào `hbc-task-breakdown`. Đây là **lỗ hổng cụ thể nhất**: task-breakdown dễ âm thầm tái lập "cắt theo tầng" (model→API→UI) dù feature đã vertical.
4. **Risk-classifier per-feature ở gate Phase 1**: feature "known" → đường design-first hiện tại; feature "uncertain" → bắt buộc vòng **discovery/iterative** (walking skeleton/tracer bullet) trước. Đây là cách hoà giải dual-track mà không phá traceability.
5. **Appetite (ngân sách thời gian) + circuit breaker** cho mỗi feature, và **WIP-limit ở cấp portfolio** (giới hạn số feature đang dở giữa các phase). Khoảng trống flow lớn nhất của HBC: docs nói luồng *trong* một feature, im lặng về *bao nhiêu feature chạy song song*.
6. **Lớp `constitution.md`** (Spec Kit) ở Phase 0: nguyên tắc xuyên-phase bất biến (test-first, language policy, separation-of-duties, simplicity caps) — hợp đồng chung cho cả 5 persona.

**Về phân role (trục 7) — câu trả lời quan trọng:** mô hình "một persona / một phase·gate" của HBC **được lý thuyết bảo chứng** (Separation-of-Duties + V-Model authorship + RACI single-Accountable). NHƯNG nó chỉ đúng **vì các handoff là tài liệu D-xx có cấu trúc + ma trận traceability** — đúng điều kiện MetaGPT/Anthropic. **Nếu HBC để các persona bàn giao bằng hội thoại tự do thay vì artifact, thiết kế sẽ vỡ** (cascading hallucination). Hai rủi ro phải canh: (a) Dev *phủi* trách nhiệm chất lượng ("QA sẽ bắt"), (b) "waterfall-gravity" do quá nhiều gate tuần tự.

---

## 2. Trục 1 — Phase-gating

**Stage-Gate (Cooper, 1988).** Stage (làm việc) ⟷ Gate (quyết định **Go/Kill/Hold/Recycle**, *cấp phát nguồn lực* cho stage sau). Gate là **quyết định nhìn-tới**, không phải review-trạng-thái-nhìn-lui. *Confidence: high.*

**Thực hành đáng mượn:**
- **Exit-criteria 2 tầng:** must-meet (binary, một "No" = Kill/Hold) vs should-meet (scorecard có trọng số phân biệt "mạnh" với "vừa đủ").
- Gate là **decision có hệ quả thật** (gồm cả *Recycle* = trả về phase trước). Gate chỉ-bao-giờ-"Go" = sân khấu (theater).
- Criteria **hiển thị trước** để team tự đánh giá. Gate **evidence-based, nhẹ**, không nặng giấy tờ.
- **Agile-Stage-Gate / Triple-A** (Cooper 2016): chạy sprint *trong* stage, gate **Adaptive/Agile/Accelerated** (Honeywell, LEGO, P&G, Tetra Pak).

**V-Model & waterfall-with-gates:** xem trục 5. Phân biệt then chốt: gate "completeness" (đã xong giấy chưa?) vs gate "investment" (có đáng đi tiếp không?) — đây là ranh giới giữa gate giá-trị và gate-quan-liêu.

**Ánh xạ HBC:** Gate HBC hiện đọc như **completeness-check pass/fail** → **ADOPT** outcome `Recycle` + chia must/should (validator+traceability+model-validation = knock-out; facet semantic-review = scorecard, `openFacets` rỗng = ngưỡng đậu). **AVOID:** đừng để số gate/feature thành nghi-lễ tuân-thủ (đã có facet-conditionality + N/A waiver làm van WIP); đừng nhập gate tài-chính của Cooper (HBC là gate technical-readiness, không phải gate đầu-tư).

---

## 3. Trục 2 — Incremental & iterative

**Incremental ≠ Iterative (Cockburn 2008 / Patton — analogy Mona Lisa):**
- **Incremental** = dựng từng mảnh *đã hoàn thiện* (giả định đã biết tổng thể; chiến lược *staging*).
- **Iterative** = dựng bản thô cả-bức rồi *tinh chỉnh qua nhiều lượt* (chiến lược *learning/rework*).
- **Cảnh báo Cockburn:** chỉ làm một trong hai là gặp rắc rối. Incremental-only = dựng xong mới phát hiện sai (không có vòng validate). *Confidence: high.*

**Vertical slice > horizontal layer** (đồng thuận cao nhất trong literature). **Walking skeleton / tracer bullet** (Cockburn; Pragmatic Programmer): lát end-to-end mỏng nhất, dựng *trước* để khử rủi-ro tích-hợp. **Dual-track agile** (Patton/Cagan): hai track *song song liên tục* — Discovery (đáng làm không?) feed Delivery.

**Ánh xạ HBC:** HBC = "incremental across slices, design-first within slice" → ánh xạ sạch vào trục *incremental* của Cockburn ở cấp dự án.
- **Hợp** khi: yêu cầu rõ/ít mơ hồ (ERP/back-office, regulated, integration-heavy), feature thực sự độc lập & shippable, có nhu cầu audit/traceability.
- **Rủi ro** khi: feature có **discovery-risk cao** (nhu cầu chưa rõ, UX mới). Design-first-per-slice **xung đột dual-track**: nếu yêu cầu *sai*, pipeline-gated trung thành xây sai — đúng failure-mode "incremental không kèm iterative".
- **ADOPT (gated):** risk-classifier ở gate BA → "uncertain" bắt buộc discovery loop / walking-skeleton trước khi đóng Phase 1; "known" giữ đường design-first. **KEEP** sequential-within-slice làm *default* (đúng domain ERP, là cái làm traceability mạch lạc). **AVOID** biến cả framework thành dual-track liên tục (sẽ hoà tan gate + traceability — chính là differentiator).

---

## 4. Trục 3 — Work-breakdown / story slicing

**INVEST (Bill Wake 2003)** cho *story/value-unit* + **SMART** cho *task*. Hierarchy: Epic → Story (đơn vị INVEST) → Task (đơn vị SMART). "V" = Valuable **(or Vertical)".

**SPIDR (Cohn):** Spike / Path / Interface / Data / Rules. **Lawrence — 9 patterns + flowchart:** Workflow Steps, Operations(CRUD), Business-Rule Variations, Data Variations, Data-Entry Methods, Major Effort, Simple/Complex, Defer Performance, Spike. **Quy tắc load-bearing (cả hai đồng thuận):** *cắt dọc xuyên tầng để giao giá trị quan sát được, KHÔNG cắt ngang theo tầng.*

**WBS + quy tắc 100%** (PMI): decomposition hướng-deliverable; con = 100% cha, **không dư scope ngoài**. **Canon TDD (Kent Beck):** bắt đầu bằng **test list** (liệt kê biến thể hành vi + edge case), chọn **1 test/lần**, RED→GREEN→REFACTOR; **không** viết hết test đầu cơ trước.

**Ánh xạ HBC (đòn bẩy cao):**
- **ADOPT vertical-slice làm quy tắc cắt task Phase 3.** Mỗi TDD-task = lát dọc mỏng đẩy 1–vài test-case RED→GREEN→REFACTOR — *không* phải task "dựng model" → "dựng API" → "dựng UI". **AVOID** cắt theo tầng dù D-19/D-21 là deliverable theo-tầng (deliverable là *design artifact*; task vẫn phải cắt dọc xuyên chúng).
- **ADOPT INVEST cho *feature* (gate Phase 1)** + **SMART cho *task* (Phase 3)**. Feature fail "Small" → tách thành feature anh-em *trước khi* vào lifecycle (không tách thành task).
- **ADOPT "test-list = task-list"** (Canon TDD): output `hbc-task-breakdown` chính là test-list per-feature, mỗi task ≈ 1 biến thể hành vi, sắp đơn-giản-trước. SPIDR/Lawrence "Rules/Data" = chính các "what-if" trên test-list của Beck → một catalog dùng cho cả hai.
- **ADOPT quy tắc-100% như invariant coverage máy-kiểm-được:** breakdown hoàn chỉnh ⟺ (a) mọi REQ-ID phủ bởi ≥1 task **và** (b) mọi task map ≥1 REQ-ID (nửa sau = chống gold-plating). Khớp triết lý "structure ở Python, meaning ở LLM" của HBC.
- Hoà giải caveat anti-đầu-cơ của Beck với traceability: coi test-list trong ma trận là **living artifact** (HBC đã có cascade-sync + DF-9 drift `test_ref` ↔ D-27).

---

## 5. Trục 4 — Spec-driven & AI-era (2024–2026)

**GitHub Spec Kit (9/2025):** `/specify → /plan → /tasks → /implement`, mỗi phase ra 1 Markdown feed phase sau. Đáng mượn: **`constitution.md`** (nguyên tắc bất biến cấp dự án, gồm "test-first là hiến pháp"); **"Phase -1 Gates"** (Simplicity/Anti-Abstraction/Integration-First); **`[NEEDS CLARIFICATION]`** markers (van xác định, buộc model nêu bất định thay vì đoán thầm).

**Amazon Kiro (2025):** **Requirements → Design → Tasks** (`requirements.md`/`design.md`/`tasks.md`). Đáng mượn: **EARS notation** (HBC *đã dùng* → validated); **approval-gate giữa phase** + **"Quick Plan" escape-hatch** (bỏ gate cho việc đã-rõ); **Bugfix spec** (khác Feature spec); **dependency-graph "waves"** (chạy task độc lập song song — cộng hưởng hướng "build-graph kernel" trong memory HBC).

**BMad Method (cha của HBC):** 7 agent, gate ở mọi stage-transition, "Party Mode" (đa-persona tranh luận 1 session). **HBC tách QA thành persona độc lập** thay vì nhúng trong Dev như BMad → **tăng cường separation-of-duties** (xem trục 7) — hợp lý.

**SDD có "mới" không?** (Thoughtworks, cân bằng): *không mới về hình dạng* — nó là hình waterfall — nhưng *hoàn cảnh khác*: spec là Markdown versioned cập-nhật-lặp, **regenerate downstream khi spec đổi** → vòng phản hồi ngắn. **Bẫy được ghi nhận:** thiếu "rails" cưỡng-chế incremental, "trọng lực kéo team về specify-mọi-thứ-trước-khi-build" = thoái về waterfall.

**Ánh xạ HBC:** **per-feature incremental + cascade-sync của HBC chính là thuốc giải bẫy SDD-waterfall** → nên nâng thành **nguyên tắc thiết kế load-bearing tuyên bố rõ**. **ADOPT** `constitution.md`-analogue ở Phase 0; markers `[NEEDS CLARIFICATION]` trong template D-xx; **Quick Plan fast-path + bugfix lane** (giảm overhead 4-gate/feature cho việc nhỏ). HBC **đã vượt** Spec Kit/BMad về gating + traceability — giữ.

---

## 6. Trục 5 — Quality pairing / shift-left

**Cặp V-Model:** Requirements↔**Acceptance** (validation), System↔System-test, Architecture↔**Integration**, Detailed/Unit↔**Unit** (verification). **Shift-left (Larry Smith 2001) — 4 loại:** Traditional / Incremental (chẻ 1 V lớn thành nhiều V nhỏ) / Agile-DevOps / **Model-based** (test *bản thân* requirement/architecture/design *trước khi có code*). **TDD vs BDD vs ATDD:** TDD=dev/unit ("build it right"); ATDD=dev+tester+PO/acceptance ("right product", viết acceptance *trước*); BDD=Given-When-Then/behavior, cầu nối kỹ-thuật↔nghiệp-vụ.

**Ánh xạ HBC (phần lớn đã khớp — hãy đặt tên):**
- HBC **đã là "model-based shift-left"** (validator + semantic-review test artifact D-xx *trước code*) — dạng shift-left mạnh & hiện đại nhất → nêu rõ như differentiator.
- HBC **đã là "incremental shift-left"** (per-feature = nhiều V nhỏ) — đúng khuyến nghị của Smith.
- **ADOPT** map EARS-requirement → ATDD-acceptance (D-02 → `hbc-acceptance-check`); **BDD cho facet behavioral-design** ↔ test hành vi (cầu BA↔Tester); TDD giữ làm engine Phase 3.
- **AVOID** độ-cứng V-Model: thuốc giải của HBC là **cascade-sync/drift** (tái-lan-truyền REQ→design→test) — đầu tư tiếp; đó là cái giữ HBC khỏi thành "waterfall-thêm-bước". **Đừng** ép cả TDD+BDD+ATDD lên mọi feature (dùng facet-conditionality). **Đừng** mã-hoá meaning-check vào Python (giữ luật 3-lớp).

---

## 7. Trục 6 — Lean / flow

**Shape Up (Basecamp/Ryan Singer):** **Appetite** ("bao nhiêu *xứng đáng* để chi", không phải estimate) → **fixed-time/variable-scope** (cắt scope để giữ deadline); **Shaping**; **Betting table** (không backlog); **Scopes** (mảnh build-integrate-finish độc lập); **Hill chart** (uphill=còn unknown / downhill=chỉ-còn-thực-thi); **Circuit breaker** (không xong 1 cycle → xét lại, *không* auto-gia-hạn); **Cool-down**. **Reinertsen (flow):** queue ẩn = gốc rễ kém; **giảm batch-size giảm cycle-time**. **Kanban/Little's Law:** `CycleTime = WIP / Throughput` → giảm WIP (giữ throughput) để rút cycle-time.

**Ánh xạ HBC:**
- **ADOPT (thận trọng) appetite/feature** = van batch-size tự nhiên. **Tension:** fixed-time/variable-scope cắt scope giữa-chừng sẽ phá ma trận (REQ bị bỏ). **Khuyến nghị:** appetite cap *kích thước slice ở gate BA* (chốt must-have vs defer-sang-feature-sau *từ đầu*), REQ defer thành *feature kế*, không thành dòng-ma-trận mồ-côi.
- **ADOPT circuit-breaker như một outcome gate** (blow appetite → re-slice/defer/kill, không im-lặng gia-hạn) — khớp máy gate sẵn có.
- **ADOPT WIP-limit ở cấp portfolio** (giới hạn số feature đang giữa Phase 1–4 đồng thời). Trong 1 feature đã WIP=1/phase; WIP-limit chủ yếu là vấn đề *cross-feature* — **khoảng trống flow HBC chưa nói tới**.
- **ADOPT hill-chart cho report gate** (Phase 1–2 = uphill, 3–4 = downhill — trung thực hơn %-complete). **Cool-down** tùy chọn giữa feature (tech-debt + reconcile ma trận + "bet" feature kế).
- **AVOID** "no-backlog / shape-loosely" của Shape Up (mâu thuẫn triết lý design-first + spec có cấu trúc của HBC). **AVOID** giáo-điều cycle-6-tuần (mượn *fixed-time/variable-scope*, không mượn nhịp lịch).

---

## 8. Trục 7 — Role / ownership

| Mô hình | Lõi | Hệ quả cho HBC |
|---|---|---|
| **RACI** | đúng **1 Accountable**/task; tách "làm" khỏi "chịu trách nhiệm" | "1 persona/phase·gate" = mô hình single-A → **hợp lệ**. Nhưng phải tách R vs A: ai *Accountable* cho gate Phase 3? Nếu vẫn là Dev → mùi "tự chấm bài mình". |
| **Scrum** | 3 accountability: PO(what/why) · SM(how/process) · Devs(build) | HBC **không có** analogue PO/SM — 5 persona đều là role *delivery*. Vai "process-integrity" (≈SM) **bị encode thành tooling** (`hbc-phase-gate`+traceability) thay vì persona → hợp lý cho AI-era, nhưng **nên đặt tên rõ**. |
| **SoD / test-independence** (COSO/SOX, NIST AC-5, ISTQB) | người làm không phải gate duy nhất xét đúng-sai; độc lập tìm "nhiều, khác" lỗi | **Đây là lý thuyết bảo chứng nguyên tắc "một người gác hai cổng thì hở".** Tách QA(test-design) ≠ Dev(impl) ≠ Tester(exec) = SoD sách-giáo-khoa, **mạnh hơn BMad** (nhúng QA trong Dev). Rủi ro: **abdication** ("QA sẽ bắt") → giữ Dev *Responsible* cho chất lượng. |
| **Feature vs Component team** (LeSS/Larman) | component-team = nhiều queue + handoff → củng cố waterfall | 5 persona ≈ **component-team theo trục lifecycle** → mỗi ranh giới persona = 1 handoff/queue. Giữa AI-agent: rẻ để gọi nhưng dễ **mất context / "tam-sao-thất-bản"**. **Ma trận traceability + cascade-sync chính là cơ chế nội-bộ-hoá các handoff này** — giữ & tăng cường. |
| **V-Model** | level *viết* spec **sở hữu** test-gate khớp nó | **Bảo chứng QA-persona thiết-kế-test ở Phase 2** (cùng lúc Architect design), không phải sau code. Nêu đây là rationale. |
| **Multi-agent persona** (Anthropic/MetaGPT/CrewAI) | đa-agent đáng giá khi **song song / vượt context**; *không* đáng khi **chung context + nhiều phụ thuộc**; multi-agent ≈ **15× token** | Việc coding HBC **phần lớn tuần tự + coupled context** → đáng-lẽ multi-agent *thêm phí*, **TRỪ KHI handoff có cấu trúc** → "cứu cánh của HBC là handoff = tài liệu D-xx + ma trận" (đúng điều kiện MetaGPT chống cascading-hallucination). **Song song chỉ ở trục *per-feature* (độc lập); chuỗi *trong-feature* thì đừng multi-agent cho-có.** |

**Tổng hợp tradeoff:** tách-ownership **tăng chất lượng** khi (1) author-bias là rủi ro chính [SoD — case mạnh nhất cho QA/Tester≠Dev], (2) việc song-song-được/tách-context-được [đúng trục per-feature], (3) accountability dễ loãng [RACI/Scrum single-A], (4) **handoff là hợp-đồng-tài-liệu một-chủ** [đúng D-xx]. Tách **thêm phí ròng** khi: bước chung context/coupled chặt [chuỗi trong-feature], overhead token/điều-phối > giá-trị (~15×), hoặc tách đẻ ra abdication.

**ADOPT thêm:** "Party Mode" (đa-persona tranh-luận) tại gate readiness Phase 2 (Architect+QA reconcile D-21 vs D-26) — bắt xung-đột mà handoff tuần tự bỏ sót.

---

## 9. Bảng ánh xạ tổng — HBC đang ở đâu

| Khía cạnh | Mô hình chuẩn | HBC hiện tại | Khoảng trống / Hành động |
|---|---|---|---|
| Gate | Stage-Gate Go/Kill/**Recycle**, must/should | pass/fail completeness | **+Recycle, +2-tầng criteria** |
| Design↔Test | V-Model pairing | có field `v_pair` trong catalog (ngầm) | **Hình thức hoá: facet khai báo test-level, enforce trong ma trận** |
| Shift-left | model-based + incremental | **đã làm** (validator/semantic-review + per-feature) | **Đặt tên làm differentiator** |
| Cắt task | vertical slice (SPIDR/Lawrence) + Canon-TDD test-list | nguy cơ cắt-theo-tầng âm thầm | **Quy tắc vertical-slice + catalog pattern + test-list=task-list** |
| Coverage | WBS quy-tắc-100% | ma trận REQ→…→test | **Invariant: mọi REQ↔≥1 task & mọi task↔≥1 REQ** |
| Bất định | dual-track / walking skeleton | design-first cứng/feature | **Risk-classifier ở gate BA → uncertain ⇒ discovery loop** |
| Batch/flow | appetite + circuit-breaker + WIP | im lặng về cross-feature WIP | **Appetite/feature, circuit-breaker outcome, WIP-limit portfolio, hill-chart** |
| Nguyên tắc | constitution.md (Spec Kit) | rải rác trong prose/customize.toml | **Lớp constitution ở Phase 0** |
| Ceremony | Quick Plan / Bugfix lane (Kiro) | mọi thứ = full feature 4-gate | **Fast-path việc nhỏ + lane bugfix** |
| Role | SoD + V-Model + RACI + MetaGPT | 5 persona, handoff = D-xx | **Hợp lệ; +tách R/A ở gate, +đặt tên process-owner, +Party Mode, giữ Dev Responsible** |
| Chống waterfall | regenerate-on-change | cascade-sync (DF-9) | **Nâng thành nguyên tắc load-bearing** |
| EARS | Kiro/Rolls-Royce | **đã dùng** | đã khớp ✅ |

---

## 10. Reading list (tài liệu nguồn — phân theo ưu tiên)

### ⭐ Phải đọc (đòn bẩy cao nhất cho HBC)
- **Cooper — The Stage-Gate Model: An Overview** — https://www.stage-gate.com/blog/the-stage-gate-model-an-overview/ — gate outcomes, must/should, "forward-looking". `high`
- **Cooper — The Agile–Stage-Gate Hybrid (JPIM 2016)** — https://onlinelibrary.wiley.com/doi/abs/10.1111/jpim.12314 — template cho chính hình dạng HBC. `high`
- **Richard Lawrence — Guide to Splitting User Stories** — https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/ — 9 pattern + quy tắc "cắt dọc không cắt tầng". `high`
  - Flowchart PDF — https://www.humanizingwork.com/wp-content/uploads/2020/10/HW-Story-Splitting-Flowchart.pdf
- **Mike Cohn — SPIDR** — https://www.mountaingoatsoftware.com/blog/five-simple-but-powerful-ways-to-split-user-stories — 5 kỹ thuật cắt story. `high`
- **Kent Beck — Canon TDD** — https://newsletter.kentbeck.com/p/canon-tdd — test-list = task-list, 1-test/lần, anti-đầu-cơ. `high`
- **GitHub Spec Kit — Spec-Driven Development** — https://github.com/github/spec-kit/blob/main/spec-driven.md — constitution.md, Phase-1 gates, [NEEDS CLARIFICATION]. `high`
- **Kiro — Feature Specs / EARS** — https://kiro.dev/docs/specs/feature-specs/ — EARS, approval gates, Quick Plan, bugfix spec. `high`
- **Anthropic — Building a multi-agent research system** — https://www.anthropic.com/engineering/built-multi-agent-research-system — khi nào đa-agent đáng/không đáng (15× token). `high`
- **MetaGPT (arXiv 2308.00352, ICLR 2024)** — https://arxiv.org/html/2308.00352v7 — role + **handoff phải là structured output** chống cascading-hallucination. `high`

### 📘 Nên đọc (bối cảnh + bảo chứng thiết kế)
- **Shift-left testing (Wikipedia)** — https://en.wikipedia.org/wiki/Shift-left_testing — 4 loại, gồm model-based. `high`
- **TDD vs BDD vs ATDD (BrowserStack)** — https://www.browserstack.com/guide/tdd-vs-bdd-vs-atdd — ai-viết/level/khi-nào. `high`
- **V-Model & testing (Code Intelligence)** — https://www.code-intelligence.com/blog/everything-about-v-model-and-testing-embedded-software — pairing + traceability + chỉ-trích độ-cứng. `high`
- **Patton — Iterative vs Incremental (Mona Lisa)** — https://itsadeliverything.com/revisiting-the-iterative-incremental-mona-lisa — phân biệt nền tảng. `high`
- **Cockburn — Using Both Incremental and Iterative Development** — https://www.se.rit.edu/~swen-256/resources/UsingBothIncrementalandIterativeDevelopment-AlistairCockburn.pdf — paper gốc. `high (qua đối chiếu)`
- **SVPG (Cagan) — Dual-Track Agile** — https://www.svpg.com/dual-track-agile/ — discovery ∥ delivery. `high`
- **Basecamp — Shape Up** — https://basecamp.com/shapeup — appetite/scopes/hill-chart/circuit-breaker. `high`
  - Ch.9 Place Your Bets — https://basecamp.com/shapeup/2.3-chapter-09
- **Reinertsen — Principles of Product Development Flow (review)** — https://xp123.com/the-principles-of-product-development-flow-reinertsen/ — batch-size/queue. `high`
- **INVEST (Agile Alliance)** — https://agilealliance.org/glossary/invest/ — định nghĩa + "Valuable (or vertical)". `high`
- **WBS (Wikipedia)** — https://en.wikipedia.org/wiki/Work_breakdown_structure — quy-tắc-100%, deliverable-oriented. `high`
- **Thoughtworks — Unpacking SDD (2025)** — https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices — SDD vs waterfall, drift risk. `high`
- **LeSS — Feature Teams** — https://less.works/less/structure/feature-teams — handoff/queue critique. `high`
- **2020 Scrum Guide** — https://scrumguides.org/scrum-guide.html — 3 accountability PO/SM/Dev. `high`
- **NIST SP 800-53 AC-5 (SoD)** — https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-5/ — separation-of-duties "without collusion". `high`
- **BMad Method — Agents reference** — https://docs.bmad-method.org/reference/agents/ — mô hình agent cha của HBC. `high`

### 📑 Tham khảo / phụ
- Toolshero — Stage-Gate — https://www.toolshero.com/innovation/stage-gate-process/ `high`
- IBM — Shift-left testing — https://www.ibm.com/think/topics/shift-left-testing `high`
- Walking skeleton — https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html `high`
- Productboard — Dual-Track Agile — https://www.productboard.com/glossary/dual-track-agile/ `high`
- Kiro Specs (overview + waves) — https://kiro.dev/docs/specs/ `high`
- GitHub Blog — SDD with AI — https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/ `high`
- marmelab — "SDD: Waterfall Strikes Back" (2025) — https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html `med`
- sudoish — "SDD isn't Waterfall but keeps ending up there" — https://sudoish.com/spec-driven-development-waterfall-trap/ `med`
- RACI (Wikipedia) — https://en.wikipedia.org/wiki/Responsibility_assignment_matrix `high`
- Independent testing benefits/risks (ISTQB) — https://tryqa.com/what-is-independent-testing-its-benefits-and-risks/ `med`
- Kanban flow physics (Little's Law) — https://theburndown.com/flow-physics-cycle-time-throughput-and-wip/ `high`
- CrewAI docs — https://docs.crewai.com/en/introduction `high`
- Martin Fowler — TestDrivenDevelopment (bliki) — https://www.martinfowler.com/bliki/TestDrivenDevelopment.html `high`

---

## 11. Caveats về độ tin cậy

- Định nghĩa chính xác trong PDF gốc của Cockburn: verify qua abstract + nguồn thứ cấp + framing của Patton (substance `high`, không đọc nguyên-văn in-paper).
- "~40% throughput từ WIP-limit": 1 nguồn thứ cấp → minh hoạ, không phải established (`low`).
- Nhãn 2 tầng giữa của V-Model (system vs architectural): tên khác nhau giữa nguồn; *nguyên tắc* (mỗi design-level có test-level kiểm chứng) là `high`.
- Tương đương SPIDR↔Lawrence và "phút/chu-kỳ RED-GREEN" là *synthesis của researcher*, không phải claim của tác giả gốc (`med`).
- "PO/SM phải tách": không có cấm-đoán nguyên-văn trong Scrum Guide — là *hệ quả* của accountability đối nghịch (cấu trúc `high`, rationale `med`).

---

*Hết tài liệu nghiên cứu. Bước gợi ý tiếp theo: chọn 2–3 mục ⭐ ưu tiên (đề xuất: #1 gate 2-tầng+Recycle, #3 vertical-slice task + catalog, #4 risk-classifier dual-track) để đưa vào `process-review/` như đề xuất cải tiến trục B/A kế tiếp.*
