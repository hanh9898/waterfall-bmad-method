---
title: "Đề xuất Cải tiến Framework HBC — qua elicitation (case: resource-plan-billable)"
doc_type: framework-improvement-proposal
audience: "HBC maintainer (chính bạn)"
method: ["Grounded-only (đọc source/doc/context)", "Interactive elicitation (option + suggest)", "Brainstorming lenses", "RCA"]
case_under_test: resource-plan-billable
date: "2026-06-20"
status: final
owner: "HanhNT2 (HBC maintainer)"
reviewer: "adversarial-subagent độc lập × 4 vòng (2026-06-20 → 06-21)"
next_action: "thẩm định độc lập từng item LỚN trước khi vào roadmap (xem §2 Kiểm soát)"
structure: "Sắp theo VÒNG ĐỜI (lifecycle) — không theo thứ tự elicitation. ID quyết định (A#/B#/E#/F#/UX#) giữ nguyên để truy vết chéo."
---

# Đề xuất Cải tiến Framework HBC

> **Cách làm tài liệu này (theo yêu cầu của maintainer):**
> - Em **chỉ khẳng định** điều thấy được qua **tài liệu / context / đọc source skill**. Phần còn lại **hỏi anh** bằng câu hỏi có option + gợi ý đáp án tốt nhất → tránh hallucination & một chiều.
> - Quá trình elicitation đi theo: **Tổng workflow** (10 câu, lăng kính brainstorming) → **từng skill** (mỗi skill 10 câu; đọc source trước khi hỏi). Trọng tâm: *skill đang tự-quyết quá nhiều → chỗ nào nên HỎI người dùng.*
> - Mỗi mục dưới đây = **quyết định của anh** đã chốt qua elicitation, kèm 1 dòng "thấy được ở đâu" (grounding).
> - **Bố cục đã sắp lại theo VÒNG ĐỜI** (Phase 0→4 + Cross-cutting) để đọc-hiểu, không còn theo thứ tự đã hỏi. Các mã quyết định (A1, B3-5, E-8, F-4, UX-1…) giữ nguyên để đối chiếu với nhật ký elicitation.

---

## 1. Tóm tắt điều hành (vấn đề · 5 nhóm lỗ hổng · CHỐT 🟢/🟡)

**Cấu phần tài liệu:** workflow tổng (Phần A, 10) · từng skill = **16 skill + 5 agent** (B.1–B.17: B.1–B.11 doc/core · B.12 api-spec = N/A · B.13 readiness · B.14 migrate · B.15 project-init · B.16 Phase-4 [test-execution+acceptance] · B.17 5 agent) · UX (Phần D) · khung chuẩn (Phần E) · kiểm soát (Phần F). **Tổng ~145 quyết định** — tất cả là **KHUYẾN NGHỊ qua 4 vòng adversarial-review độc lập**, KHÔNG phải spec để code thẳng.

**5 nhóm lỗ hổng lớn nhất của HBC (đã verify):**
1. **Thiếu kiểm chứng domain-model** — không có chốt Model-Spike/model-validation giữa P1–P2 → model chỉ bị nhận sai *sau khi build* (gốc của case).
2. **Thiếu engine re-baseline** — đổi model lõi / shared sau Phase-3 không có path gated; cascade dựa user nhớ.
3. **Thiếu tầng UX** — HBC bỏ qua D-14 + design-sync; mockup là ốc đảo không traceability.
4. **Thiếu tầng Architecture + Detailed-Design** (giữa V-Model) → quyết định kiến trúc/logic bị dồn vào code.
5. **Thiếu catalog/applicability control** — không có catalog deliverable canonical; chọn bộ tài liệu ad-hoc → sót/over-produce.

Để **thực thi de-ceremony (F-1) thật**, chia 2 rổ — chỉ rổ 🟢 được commit:

### 🟢 COMMIT NGAY — S/ready/ROI-cao, ceremony thấp (chủ yếu lint/check/sửa-tín-hiệu-giả, KHÔNG thêm tầng tài liệu)
| Item | Metric đo (F-6) |
|---|---|
| IMP-01 version-coherence validator | xref-version mismatch = 0 |
| IMP-02 spec-ref lint (code/test) | spec-ref leak 65→0 |
| IMP-03 gate-script robust + cấm silent manual-pass | gate-false-pass→0 |
| QW-4 số liệu gate do script tính (không LLM khai) | gate-false-pass→0 |
| QW-5/A9 + **B13-1** matrix parse-cột + REQ→row coverage | REQ-không-matrix (3→0); code_ref-giả bắt được |
| QW-6/A10 + **B5-1/B13-3** MODEL_DRIFT (code vs D-19 hiện hành) | code↔design drift bắt 100% |
| SE-1 gate STALE theo version-set + auto-revalidate | gate cũ không-tự-pass |
| **B14** migrate bug-fix (regex-scope, timestamp-unique, dirty-guard-warn, contract-sync, emit missing-row) | traceability không gãy sau migrate |

→ **Net ceremony commit ngay ≈ thấp**: phần lớn là *gỡ tín hiệu giả* + *bắt drift*, không phải thêm HALT/doc.

### 🟡 CẦN SPIKE/THIẾT KẾ RIÊNG — CHƯA commit (needs-design; mỗi cái 1 spike + 1 review độc lập theo F-3 trước khi vào chuẩn)
- **A1 Model-Spike** — `hypothesis` (F-4): pilot 1 feature, đo churn/false-pass; **chưa chứng minh ngăn được case** → KHÔNG commit tới khi pilot xác nhận.
- **A3 hbc-rebaseline** — engine MỚI (xác nhận B14-6), subsystem nhiều tuần.
- **A4 ADR/decision-gate · A7 maturity track · E-8 applicability-matrix** — kiểm soát, cần thiết kế.
- **E-1 Architecture · E-2 Detailed-design** — thêm tầng V-Model; cân cost/benefit cho module Odoo.
- **Phần D UX** — **conditional, phần lớn N/A cho back-office Odoo** (F-5: UI server-rendered view/wizard, cùng lý do D-21 N/A); chỉ bật khi feature UI-rich/dùng Claude Design.

> **Lỗ hổng đáng tin nhất (đã verify):** matrix id-presence-only + thiếu task/D-19/version ở seam-gate (B13), migrate bug (B14), spec-ref leak, gate-false-pass. Đây là rổ 🟢. Các "tầng mới" (UX/architecture/detailed-design/model-spike/rebaseline) là **giả thuyết cần thử**, không phải kết luận.

Xuyên suốt: **ASK-at-domain-decision · grounding thật · machine-verified · cascade-enforced · anti-false-green · review-by-independent-subagent**.

---

## 2. Nguyên tắc xuyên suốt + Kiểm soát (Phần F)

### Nguyên tắc xuyên suốt (áp cho MỌI skill)

1. **ASK tại "quyết định miền" (A5)** — skill phân biệt quyết-định-cơ-học (tự làm) vs miền/nghiệp-vụ/kiến-trúc (HỎI); thiếu dữ kiện → dừng hỏi, không bịa default. *(Mối lo gốc của maintainer.)*
2. **Grounding bắt buộc** — feasibility/reality-check/AS-IS/test-data/code đều bám **source code · DB schema · business-flow · stakeholder thật**, không "trên không".
3. **Machine-verified, không LLM tự chấm** — số liệu gate + semantic-review chạy bằng script/lens đối-kháng + sign-off; cấm tự khai con số / rubber-stamp.
4. **Anti-false-green** — test/implement phải có sanity chứng minh fixture thực sự exercise nhánh.
5. **Staleness + cascade enforced** — version-set theo dõi, đổi → STALE + auto-revalidate; cascade là bắt buộc, không dựa user nhớ.
6. **Chuẩn ngành per-artifact** (research-backed): DB 3-tier · test specification-based · TDD vertical-slice (INVEST/SPIDR) · BPMN swimlane + path-coverage · **ISO/IEC/IEEE 29119** (không phải 829 đã withdrawn) · DDD ubiquitous-language.

### Kiểm soát (Phần F — sau adversarial review)

Các quyết định vá đúng những finding chí mạng còn lại của review độc lập:

#### F-1 · Quy tắc DE-CEREMONY (chống THÊM:BỎ 25:1 + gate-fatigue)
- **Mỗi đề xuất thêm gate/doc/check PHẢI kèm 1 đề xuất bỏ/gộp/làm-nhẹ** (net-ceremony budget). Review lại toàn bộ A–E theo lăng kính này trước khi commit.
- **Default-light theo maturity (A7):** feature `exploratory` → tắt phần lớn gate mới; chỉ feature `stable`/critical mới bật full. Tránh nhân HALT → override/bypass.

#### F-2 · Sizing mỗi roadmap item (Effort · Confidence · Dependency · ROI)
Legend: **Effort** S/M/L · **Confidence** `ready` (script/đặc tả rõ) / `needs-design` (thiết kế lớn chưa đặc tả) · **ROI** cao/TB/thấp.

| Item tiêu biểu | Effort | Confidence | Dep | ROI |
|---|---|---|---|---|
| QW-1 version-coherence · QW-2 spec-ref lint · QW-3 gate-robust · QW-4 machine-numbers | **S** | ready | — | **cao** |
| QW-5 matrix/REQ coverage | S | ready | cần SE-3 | cao |
| QW-6 MODEL_DRIFT | M | ready | cần D-19 chuẩn | cao |
| SE-1 STALE+revalidate · SE-3 matrix auto-write · SE-4 cascade-enforced | M | ready | — | cao |
| SE-2 ADR/decision-gate | M | needs-design | — | TB-cao |
| A1 **Model-Spike** | M | **needs-design + HYPOTHESIS** (F-4) | A4 | TB (chưa chứng minh) |
| A3 **hbc-rebaseline engine** | **L** | **needs-design** (subsystem chưa tồn tại) | migrate, matrix | cao nhưng rủi ro |
| A7 maturity track | M | needs-design | — | cao (giảm tải) |
| E-1 Architecture · E-2 Detailed-design · Part D UX | **L** | needs-design | E-8 | TB (xem F-5/F-6) |
| E-8 applicability matrix | M | ready | catalog-def | cao (kiểm soát phạm vi) |

→ **Ưu tiên thực: các "S/ready/cao" (QW-*, SE-1/3/4)** làm trước; **mọi "needs-design"** phải qua F-3 trước khi commit.

#### F-3 · Quyết định LỚN qua review độc lập (chống rubber-stamp)
~145 quyết định trong doc = **khuyến nghị được phê chuẩn, KHÔNG độc lập**. Nguyên tắc: **item Effort=L hoặc Confidence=needs-design phải qua 1 vòng adversarial-subagent** (như vòng vừa rồi đã bắt được hallucination catalog) **trước khi vào roadmap chính thức**. Khớp B6-1 (lens độc lập + sign-off).

#### F-4 · Fix chưa-chứng-minh = HYPOTHESIS + pilot
**Model-Spike (A1)** và mọi fix có claim nhân-quả chưa trace (ngăn được case) **đánh dấu `hypothesis`**: chạy **pilot trên 1 feature thật, đo bằng metric F-6**, rồi mới đưa vào chuẩn. RCA cho thấy model chỉ bị nhận sai *sau khi build* → spike có thể không bắt được; phải thử nghiệm, không giả định.

#### F-5 · Part D (UX) = conditional + cost/benefit
Part D **chỉ bật khi**: feature UI-rich HOẶC dùng Claude Design. Back-office Odoo (view/wizard server-rendered) → **D-14 nhẹ hoặc N/A** (cùng lý do D-21 N/A). Đưa qua **applicability matrix (E-8)** với cost/benefit, không áp mặc định.

#### F-6 · Success metrics + baseline (đo hiệu quả cải tiến)
| Metric | Baseline (từ case) | Mục tiêu |
|---|---|---|
| Churn — # version/doc tới khi frozen | D-02 = **13** | ≤ 3–4 |
| Re-cascade lặp (số vòng full-cascade) | **4+** (v2.0→2.3) | 1 |
| Gate-false-pass (PASS trên model/struct sai) | 3 gate (P1/P2/P3) | 0 |
| Spec-ref leak trong code | **65** | 0 |
| REQ không-task/không-matrix | 3 (040-042) | 0 |
| Code↔design drift phát hiện | 0 (không bắt) | 100% bắt |

→ Cải tiến nào không cải thiện được metric tương ứng trên pilot → **loại/revise**.

---

## 3. Cải tiến theo VÒNG ĐỜI (lifecycle)

> Đọc theo dòng chảy phát triển: **bức tranh lớn (workflow + khung chuẩn)** → **Phase 0 → 1 → 2 → 3 → 4** → **các skill cross-cutting**. Mỗi skill: thiếu gì / sai gì / cần bổ sung gì, trọng tâm A5 (chống tự-quyết/hallucination). ID quyết định giữ nguyên (A#/B#/E#/UX#) để đối chiếu nhật ký elicitation.

### 3.0 Bức tranh lớn — Workflow tổng (Phần A) + Khung chuẩn (Phần E)

#### Phần A — Tổng workflow: SAI gì / THIẾU gì (10 quyết định)

| # | Lăng kính | Vấn đề (grounded) | Quyết định của anh | Gắn vào HBC |
|---|---|---|---|---|
| **A1** | Pre-mortem | Workflow đi thẳng REQ→design→code, **không có chốt kiểm chứng domain-model** (thấy qua: thứ tự phase trong các SKILL + churn case) | **Thêm bước Model-Spike giữa P1–P2** + gate P1 item "model đã kiểm chứng" | `hbc-phase-gate` (P1 checklist) + skill spike/`hbc-agent-architect` |
| **A2** | Reversal | Gate **giữ PASSED dù artifact đổi version** (thấy qua: phase-2-gate-log "giữ PASSED xuyên v1.3→v1.8") | **Gate tự chuyển STALE khi version-set đổi**; entry-gate đọc STALE như chưa-pass | `hbc-phase-gate` engine |
| **A3** | Gap | Đổi model lõi / **baseline shared chỉ ADVISORY**, Impact key REQ-id per-feature (thấy qua: `impact-capability.md` CAP-7 + `hbc-project-init` "never overwrite") | **Engine re-baseline cross-feature** (`hbc-rebaseline` + Impact declare-shared, blast radius từ rollup) | `hbc-traceability` + skill mới |
| **A4** | What's missing | Quyết định mở (TBD, A1/A2/A3 "decision-needed") **rò vào doc "complete"** (thấy qua: D-02 §1.3, D-26 §8, consistency-audit) | **ADR first-class + decision-gate** (chặn `complete`/qua-phase khi còn TBD/ADR-open) | deliverable mới + gate item |
| **A5** | Autonomy ⭐ | Skill **tự-quyết quá nhiều khi ambiguity → hallucination** (mối lo chính của anh) | **Mặc định HỎI tại "quyết định miền"** (phân biệt cơ-học vs miền/nghiệp-vụ/kiến-trúc; thiếu dữ kiện → dừng hỏi) | Áp cho MỌI skill (Phần B đào từng cái) |
| **A6** | First-principles | Đơn vị thay đổi = feature; **thay đổi xuyên-feature không có chỗ đứng** | **Thêm cấp "baseline/epic change"** trên feature (gắn A3) | layout + `hbc-rebaseline` |
| **A7** | Edge (greenfield bất định) | Một mức nghi lễ cho mọi feature → overproduction khi model biến động | **Cờ `maturity: exploratory \| stable`** — nới gate tới khi model frozen | config + create-skills |
| **A8** | Analogy (CI) | Gate chạy **thủ công 1 lần** → dễ cũ | **Re-validate tự động khi artifact đổi** ("CI cho tài liệu") | `hbc-phase-gate` + hook update |
| **A9** | Integrity | **Matrix khuyết mà gate vẫn pass** (thiếu REQ-040/041/042; code_ref trống dù khai 39/39) | **Gate diff D-02 vs matrix bắt buộc** + verify code_ref non-empty + flag REQ mới | `hbc-traceability` + P2-13/P3-07 |
| **A10** | Verification | P3 reconcile theo task-breakdown cũ → **không bắt code-on-old-model** | **Drift-detector code vs D-19 hiện hành** (`MODEL_DRIFT`) | `validate-implementation.py` + readiness |

> **Chủ đề xuyên suốt (A5):** nhiều cải tiến quy về cùng một nguyên tắc — *skill phải biết khi nào DỪNG & HỎI thay vì bịa default*. Phần B chỉ ra với **từng skill** đâu là "quyết định miền" cần hỏi.

#### Phần E — Lỗ hổng khung chuẩn (HBC vs V-Model + catalog tự khai)

> **Bộ khung chuẩn HBC** = V-Model/phased SDLC (verification: req→design→code · validation: các cấp test), doc-driven, gói incremental+TDD.
> **⚠️ ĐÍNH CHÍNH (adversarial-subagent):** **KHÔNG có file catalog D-NN nào** — `hbc_validation.py` chỉ là parser bảng/TC, **0 literal `D-0x`** (claim cũ "hbc_validation khai catalog D-01…D-27" là **sai/nhiễu grep .pyc**). Thực tế các D-NN nằm **rải rác** ở glob của `discover-planning-artifacts.py`/`scan-sources.py` + `module-help.csv` + prose SKILL; **chỉ ~8 có skill**, phần còn lại chỉ tồn tại như **pattern input-glob**. **Tên** các D-NN dưới đây đã được subagent verify ĐÚNG qua source (module-help.csv + glob), nhưng **không có "catalog khai báo" chính thức** — đây là một **lỗ hổng phụ: HBC thiếu một catalog deliverable canonical**.
> Lỗ hổng chính: **tầng Architecture + Detailed Design** (giữa requirement và code) trống → quyết định kiến trúc/logic bị dồn vào code (đúng case). (Research: V-Model "architecture design" + "module/detailed design" là phase riêng.)

| # | Lỗ hổng (vs chuẩn) | Quyết định |
|---|---|---|
| E-1 | **Không có Architecture Design** (D-08/09) — nhảy req→DB | **Thêm D-08/09 Architecture Design đầu Phase 2** (components/layers/integration/NFR-driven/tech-decisions), trước D-19/detailed-design |
| E-2 | **Không có Detailed Design** (D-17 sequence/D-18 class/logic) — ER→code | **Thêm Detailed Design (sequence/logic) cho REQ phức tạp (phi-CRUD) TRƯỚC code** (chống thiết-kế-logic-trong-lúc-code) |
| E-3 | Use-case (D-04/05) chưa có | **Gộp use-case (actor-goal + main/alt/exception scenarios) vào D-06** |
| E-4 | Table-def (D-20) | **Inline trong D-19; tách D-20 chỉ khi cần DDL/migration chi tiết** |
| E-5 | D-01 overview thiếu | **Thêm D-01 feature-overview nhẹ đầu Phase 1** (mục tiêu/scope/stakeholder/context → neo feasibility B1) |
| E-6 | Không có thiết kế phi-chức-năng | **Deliverable optional: security / deployment / data-migration design — bật khi feature chạm tới** (vd migration REQ-034) |
| E-7 | V-pairing chỉ D-27↔code | **Mỗi cấp design có cấp test tương ứng**: requirement↔acceptance/system · **architecture↔integration-test** · detailed↔unit |
| E-8 | Catalog chọn ad-hoc → sót/over-produce | **Applicability matrix per-feature**: mỗi D-NN = required/optional/N-A + lý do (theo loại feature + maturity A7) + gate kiểm đúng bộ đã chọn |

**Bổ sung Roadmap:** E-8 (applicability matrix) + E-3/E-4/E-5 → **Đợt 1–2**; E-1/E-2/E-6/E-7 (architecture + detailed-design + NFR-design + V-pairing = deliverable/skill mới) → **Đợt 3**. → Cùng Phần D (UX), đây là phần **mở rộng catalog deliverable** lớn nhất của HBC.

---

### 3.1 Phase 0 — Khởi tạo dự án

#### B.15 — `hbc-project-init` (Phase 0) (đã chốt)

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B15-1 | Idempotent 'never overwrite' → stale khi shared tiến hóa | **Re-run detect drift + offer update (không chỉ create-missing)** (A3/B10-4) |
| B15-2 | Chỉ D-12/D-03 (+optional D-19/D-21) | **Thêm baseline Architecture (E-1) + thiết lập applicability-catalog (E-8) ở Phase 0** |
| B15-3 | Baseline D-19/D-21 optional | **Brownfield → bắt derive baseline D-19 (+D-21 nếu có API) từ hệ thống thật** |
| B15-4 | Tự classify brownfield + orchestrate | **Confirm classify + stack/domain/conventions với user** (A5) |

---

### 3.2 Phase 1 — Phân tích

#### B.1 — `hbc-create-requirements` (đã chốt 10/10)

> **Chỉ đạo lớn của maintainer — tái thiết luồng intake Phase 1:**
> **Ý tưởng → Đánh giá khả thi** (đọc source code + framework + bản thân ý tưởng → "khả thi/không + ràng buộc/rủi ro") **→ Quick Discovery** (luôn chạy, cho cả 2 nhánh) **→ HỎI có cần Brainstorming sâu** (optional; task đơn giản → bỏ) **→ [Brainstorming]** với **2 câu hỏi suggest lần lượt: chủ đề + output mong muốn** **→ Discovery bổ sung bắt buộc** (kể cả sau brainstorming) **→ Sinh D-02 → BẮT BUỘC `bmad-review-adversarial-general` rồi `bmad-review-edge-case-hunter`** (tuần tự) **→ Phase-1 gate.** Mọi bước **tham chiếu source code hiện tại**.

| # | Vấn đề (grounded từ SKILL.md) | Quyết định |
|---|---|---|
| B1-1 | Stage 2→3 soft-gate rồi LLM tự sinh REQ-list → bịa REQ | **Bắt user duyệt REQ-list trước Generation** |
| B1-2 | (Tái khung) intake bắt đầu từ ý tưởng, chưa thẩm định khả thi | **Pipeline intake mới** (xem hộp trên) |
| B1-3 | NFR "measurable" → LLM tự bịa ngưỡng | **HỎI số; không có → đánh dấu ASSUMPTION (vào ADR), KHÔNG bịa** |
| B1-4 | Validate cấu trúc, không kiểm model-đúng | **Thêm reality-check + nối Model-Spike (A1)** |
| B1-5 | Không thẩm định khả thi ý tưởng | **Bước Feasibility bắt buộc, đọc source+framework** |
| B1-6 | Brainstorming hiện là quyết định nhị phân | **Quick Discovery luôn; rồi HỎI có cần brainstorming sâu** |
| B1-7 | bmad-brainstorming cần topic + desired-output | **2 câu hỏi suggest lần lượt (topic → output)** |
| B1-8 | Sau brainstorm dễ nhảy thẳng sinh doc | **Discovery bổ sung bắt buộc sau brainstorming** |
| B1-9 | Không có review bắt buộc sau D-02 | **Bắt buộc `bmad-review-adversarial-general` → `bmad-review-edge-case-hunter` (tuần tự) trước Phase-1 gate** |
| B1-10 | Grounding chỉ ở brownfield | **Bắt buộc đọc source/framework ở feasibility + reality-check + brownfield** |
| (chung) | Skill tự-quyết khi ambiguity (A5) | Mọi "quyết định miền" ở các bước trên → **HỎI**, không tự quyết |

#### B.11 — `hbc-create-glossary` (D-03, SHARED) (đã chốt)

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B11-1 | Definition LLM viết → generic/sai | **Definition ground source + user xác nhận khi suy ra** |
| B11-2 | Chỉ cross-ref D-02 | **Consistency check cross-doc: term dùng ở D-02/D-06/D-19 thiếu glossary → flag; glossary orphan → flag** |
| B11-3 | Glossary tách rời code | **Glossary = ubiquitous language (DDD), đối chiếu entity/field D-19 + code** |
| (inherited) | recurring | semantic · churn · autonomy A5 · grounding |

#### B.8 — `hbc-create-business-flow-diagram` (D-06) (đã chốt)

> **Khung chuẩn (research):** BPMN swimlane (Pool/Lane) + gateway · path coverage happy/alternate/exception · AS-IS/TO-BE · confirm-with-participants. D-06 là **nguồn cho reality-check (B2-5) + vertical-slice (B4) + test nghiệp vụ (B3)** nên chất lượng tối quan trọng.

| # | Vấn đề (grounded + research) | Quyết định |
|---|---|---|
| B8-1 | mermaid tự do, không lộ swimlane/handoff | **Ép swimlane theo actor + gateway (BPMN-style), 3–7 lane** |
| B8-2 | Dễ chỉ happy path → sót slice/test | **Bắt buộc đủ happy + alternate + exception path; thiếu → flag** (đánh dấu happy) |
| B8-3 | AS-IS đọc PRD | **AS-IS ground vào hệ thống thật (code/hành vi hiện có)** |
| B8-4 | LLM quyết flow rồi mới soft-gate | **Confirm danh sách flow/actor/path với user TRƯỚC generate** (best-practice confirm-with-participants) |
| B8-5 | Chỉ FR-coverage PRD→D06 | **REQ flow-facet → phải có flow; flow phantom (không-REQ) → flag** |
| B8-6 | Path không có ID | **Gán ID/nhãn mỗi path → task-breakdown (B4) + test (B3) tham chiếu path-ID** (D-06 = nguồn slicing) |
| B8-7 | D-06 review chỉ optional | **D-06 vào bộ review bắt buộc cùng D-02 (adversarial + edge-case) trước Phase-1 gate** |
| (inherited) | recurring patterns | semantic-review lens-độc-lập+sign-off · churn gộp-theo-phiên+cảnh-báo · autonomy A5 (flow mơ hồ→HỎI) · grounding source |

---

### 3.3 Phase 2 — Thiết kế

#### B.2 — `hbc-create-er-diagram` (đã chốt 10/10)

> **Khung chủ đạo:** áp dụng **quy trình thiết kế DB 3 cấp** (Conceptual → Logical → Physical), mỗi cấp **dừng HỎI đúng lớp quyết định của nó** (research: AWS/Visual Paradigm/ER-Studio).

| # | Vấn đề (grounded từ SKILL.md) | Quyết định |
|---|---|---|
| B2-1 | LLM tự thiết kế toàn bộ schema | **Áp dụng 3 cấp + ASK-gate mỗi cấp**: conceptual=entity/quan hệ/cardinality khớp REQ; logical=normalization/denorm(snapshot)/PK/constraint; physical=index/ondelete/kiểu |
| B2-2 | Validator chỉ PRD→D19 | **Check mỗi entity/field/constraint truy về ≥1 REQ** (chặn schema gold-plating) |
| B2-3 | Không nhắc ondelete/FK | **Bắt buộc HỎI ondelete cho mỗi FK quan trọng + rationale** (physical) |
| B2-4 | LLM tự thêm index | **Index = ĐỀ XUẤT cần xác nhận + lý do truy vấn** (physical) |
| B2-5 | Reality-check thiếu | **Conceptual đối chiếu REQ + D-06 business-flow** (không chỉ PRD) |
| B2-6 | Model lõi cụ thể hóa ở D-19 | **Bản nháp logical D-19 là đối tượng Model-Spike (A1) trước cascade** |
| B2-7 | Grounding chỉ khi brownfield-detect | **Bắt buộc đọc DB schema + models/migration thật làm ground-truth, log mọi lệch** |
| B2-8 | semanticReview tự chấm | **Lens độc lập (skeptic) + user sign-off khi passed** |
| B2-9 | auto version-bump → churn | **Gộp theo phiên + cảnh báo churn cao → gợi ý model chưa frozen (A7)** |
| B2-10 | Quyết định DB rời rạc | **Ghi quyết định (denorm/ondelete/index/constraint) vào Decision Record (A4) + rationale + REQ** |

#### B.10 — `hbc-create-coding-standards` (D-12, SHARED) (đã chốt)

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B10-1 | Dễ default generic thay vì code thật | **Bắt buộc derive từ code thật khi có codebase; deviation → flag/hỏi** |
| B10-2 | D-12 chỉ tài liệu, không enforce (65 leak) | **Rule máy-kiểm-được → lint + gate P3 enforce** (nối IMP-02) |
| B10-3 | Preference có thể tự-default | **Preference KHÔNG tự-default im lặng; trình để user xác nhận** (A5) |
| B10-4 | 'never overwritten' → stale | **Thêm cơ chế update D-12 khi convention đổi + cascade advisory** (A3 shared) |
| (inherited) | recurring | semantic · churn · autonomy A5 · grounding |

#### B.3 — `hbc-create-test-spec` (đã chốt 10/10)

> **Khung chủ đạo:** D-27 hiện **test nghiệp vụ yếu, không bám business/db/requirement** (LLM sinh TC tự do). Áp dụng **kỹ thuật thiết kế test specification-based, map kỹ-thuật↔nguồn theo loại REQ** (research: decision-table/state-transition/EP-BVA/use-case/example-mapping).

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B3-1 | LLM tự sinh TC + expected → "xanh giả" (case này gặp) | **Bắt buộc sanity-check cho TC nhạy cảm** (chứng minh fixture kích hoạt nhánh; assert giá trị có cấu trúc, không parse chuỗi) |
| B3-2 | test-data "realistic" do LLM bịa | **Ground test-data vào D-19 entity/constraint thật** |
| B3-3 | D-27 nặng nhất, sinh trước khi frozen = lãng phí | **Gate độ-sâu theo maturity (A7)**: exploratory → khung/critical; full khi stable |
| B3-4 | LLM tự quyết độ phủ rồi mới "any additional?" | **Chốt facet + edge in/out-scope per-REQ TRƯỚC generate** |
| B3-5 | TC không bám business/db/flow | **Bắt buộc map kỹ-thuật↔nguồn**: Decision-Table←business-rule(REQ/D-06); State-Transition←lifecycle(D-19/D-06, phủ cả transition sai); EP+BVA←D-19 constraint; Use-Case←D-06; Example-Mapping = elicitation đầu |
| B3-6 | LLM tự gán severity | **LLM đề xuất; critical-path phải user xác nhận** |
| B3-7 | D-27 không đối chiếu hành vi code | **Khi có code → đối chiếu TC vs hành vi thật + cảnh báo giả định sai** |
| B3-8 | semanticReview tự chấm | **Lens độc lập + user sign-off khi passed** |
| B3-9 | Review chỉ optional (parallel-lens) | **Bắt buộc `bmad-review-edge-case-hunter` + adversarial trước Phase-2 gate** |
| B3-10 | auto version-bump → ~8 ver | **Gộp theo phiên + cảnh báo churn cao (A7)** |

#### B.9 — `hbc-create-test-plan` (D-26) (đã chốt)

> **Chuẩn (research): ISO/IEC/IEEE 29119-3** (test documentation hiện hành) — ⚠️ **đính chính:** IEEE 829 (16 clause) **đã withdrawn 2013, bị 29119-3 thay thế**; tham khảo 829 cho cấu trúc cơ bản nhưng chuẩn hiện hành là 29119. D-26 đã khá khớp; điểm yếu = LLM bịa schedule/risk/scope + approach chung chung rời D-27.

| # | Vấn đề (grounded + research) | Quyết định |
|---|---|---|
| B9-1 | LLM bịa schedule/Gantt (case: ngày bất khả thi) | **Schedule do user cung cấp / để placeholder, KHÔNG bịa ngày** |
| B9-2 | LLM tự gán risk + likelihood/impact | **Risk derive từ REQ/D-06/complexity thật + likelihood/impact user xác nhận** (risk-based testing) |
| B9-3 | LLM tự quyết in/out-scope | **Chốt in/out-scope với user trước generate** (out-of-scope quan trọng ngang in-scope) |
| B9-4 | Approach chung chung, rời D-27 | **D-26 approach chỉ định kỹ thuật test per scope-area** (decision-table/state-transition/EP-BVA/use-case) → D-27 (B3-5) bám theo (liên kết WHAT→HOW) |
| (inherited) | recurring | semantic lens+sign-off · churn · autonomy A5 · grounding · review |

#### B.12 — `hbc-create-api-spec` (D-21) — **N/A** (Odoo module nội bộ không expose API; ghi N/A, review khi sau này có API/integration)

#### Phần D — Lỗ hổng UX/UI (Phase 2; conditional theo F-5)

> **Vấn đề:** HBC đi requirements→DB→test→code, **bỏ qua hẳn tầng UX/UI**. D-14 chỉ nhắc 2 lần, không có skill tạo; mockup Claude Design là **ốc đảo không traceability** → sản phẩm cuối (code/test/UX) **không map mockup**, E2E treo "PENDING DESIGN". (Research: UX artifacts, component-driven + visual-regression, design tokens, ATDD.)

| # | Vấn đề (grounded + research) | Quyết định |
|---|---|---|
| UX-1 | Không có deliverable UX | **Thêm D-14 UX/Screen Design (Phase 2)**: Screens→Components→Interactions→States→Dev-Notes, trace REQ + D-06 path + mockup. **Claude Design = tool OPTIONAL → HỎI user có dùng không**; nếu dùng → **D-14 ↔ Claude Design phải link** (để sát thực tế) |
| UX-2 | Mockup ad-hoc, không vào HBC | **Bước design-sync chính thức: mockup ↔ D-14 ↔ matrix + cascade** (khi dùng Claude Design) |
| UX-3 | Component mockup không ánh xạ code | **Shared design-system map: component mockup ↔ code component ↔ token** (tận dụng Claude Design có sẵn) |
| UX-4 | Matrix không có UX | **Mở rộng matrix: REQ → screen → component → code → test** |
| UX-5 | E2E treo 'pending design' | **UI-acceptance (ATDD/BDD) per-screen dẫn xuất E2E từ D-14 + visual-regression (baseline = mockup khi dùng Claude Design)** |
| UX-6 | Token design/code tách rời | **Design tokens 1 nguồn (Claude Design tokens ↔ code styles) khi dùng Claude Design** |
| UX-7 | UX rời nhịp TDD | **D-14 ở Phase 2; outside-in ATDD: screen-spec → acceptance test → UI code** |
| UX-8 | Mockup churn (viết lại mỗi cascade) | **Maturity-gate UX: wireframe low-fi sớm; high-fi mockup chỉ khi model/flow frozen** (A7) |

**Bổ sung Roadmap:** UX-2/UX-3 (design-sync + component-map) → **Đợt 2 (Seams)**; UX-5/UX-6 (UI-testing + tokens) → **Đợt 2–3**; UX-1/UX-4/UX-7 (D-14 + matrix-ext + outside-in) + UX-8 (maturity) → **Đợt 3 (Cấu trúc)**. Verify trên `resource-plan-billable`: mockup request/snapshot đã làm phải trace được REQ→screen→component→E2E.

---

### 3.4 Phase 3 — Triển khai

#### B.4 — `hbc-task-breakdown` (đã chốt)

> **Phát hiện gốc:** validator ĐỦ sức bắt thiếu task (entity/TC coverage) nhưng **không ai chạy lại với D-19/D-27 v2.3** → task-breakdown kẹt v1.8, **sót hẳn model request/snapshot**. Sâu hơn (research): **chia NGANG theo category** (entity/api/ui) sai chuẩn — phải chia **DỌC vertical-slice**; và **thiếu input** để cắt slice.

| # | Vấn đề (grounded + research) | Quyết định |
|---|---|---|
| B4-1 | Chia ngang theo category → task không giao giá trị, dễ sót slice | **Chuẩn: vertical-slice + INVEST + SPIDR + Kent Beck test-list** (mỗi task = slice test-được, AC rõ) |
| B4-2 | Thiếu input để cắt slice | **+Input: D-06 business-flow (paths) · Acceptance Criteria per-REQ tường minh · Spike cho unknown (nối A1) · ADR + hiện trạng code (NEW/CHANGE/đã-có)** |
| B4-3 | Không re-run khi nguồn đổi → kẹt v1.8 | **Lưu version-set nguồn → STALE + auto re-validate** (kế thừa A2/A8) |
| B4-4 | Override HALT dễ dãi | **Mặc định KHÔNG override; override phải ghi lý do + cảnh báo rủi ro** |
| B4-5 | Chỉ confirm dependency graph | **Duyệt bảng 'path/REQ-facet/entity → slice nào' trước generate** (bắt sót slice) |
| B4-6 | Validator không kiểm REQ→task (case: 040-042 không task) | **Thêm validate mọi REQ D-02 hiện hành có ≥1 task** (nối A9) |
| B4-7 | LLM tự suy dependency/priority/granularity | **Ranh giới mơ hồ → HỎI; assumption ghi ADR** (A5) |
| B4-8 | Model lõi đổi → task không re-derive | **Kế thừa A3 (hbc-rebaseline): model đổi → task-breakdown STALE + fork task mới** |

#### B.5 — `hbc-implement` (đã chốt 10/10)

> **Grounded-good:** TDD RED→GREEN→REFACTOR, RED-evidence bắt buộc, validate-implementation, cập nhật matrix code_ref, trình test review. **Gốc lỗi:** reconcile vs task-breakdown/matrix (KHÔNG vs D-19 hiện hành) → code model-cũ vẫn pass; RED-evidence soft; copy spec-ref vào code.

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B5-1 | Không kiểm code vs D-19 hiện hành | **Thêm MODEL_DRIFT: entity/field D-19 hiện hành phải có trong code** (A10) |
| B5-2 | Copy REQ/TC vào code (65 leak) | **KHÔNG nhúng spec-ref vào code/test + lint chặn** (IMP-02) |
| B5-3 | RED-evidence soft, chỉ kiểm tồn tại | **Giữ soft NHƯNG test phải FAIL đúng nhánh nghiệp vụ + sanity chống xanh-giả** |
| B5-4 | Implement theo spec stale | **Spec/task STALE → chặn implement, bắt re-derive trước** (A2) |
| B5-5 | Batch auto → sai quy mô lớn | **Batch vẫn dừng checkpoint ở quyết-định-miền + khi test PASS ngay (dấu hiệu sai)** |
| B5-6 | GREEN bịa field/API | **GREEN chỉ dùng entity/field có trong D-19 hiện hành; cần field mới → cập nhật D-19 trước** |
| B5-7 | coverage cao trên model sai | **Coverage là điều kiện CẦN không đủ (+ MODEL_DRIFT clean + sanity)** |
| B5-8 | Brownfield không đối chiếu code | **Đọc code hiện có, phân biệt sửa-vs-tạo, không trùng lặp** |
| B5-9 | DONE = test tồn tại (≠ có ý nghĩa) | **DONE cần test có sanity chống xanh-giả** (B3-1) |
| B5-10 | Batch/headless tự quyết | **Quyết định miền phát sinh khi code → DỪNG hỏi (cả batch); headless → blocked** (A5) |

---

### 3.5 Phase 4 — Kiểm thử & nghiệm thu

#### B.16 — Phase 4: `hbc-test-execution` + `hbc-acceptance-check` (đã chốt)

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B16-1 | acceptance 'traced' tin matrix-cell present-string → false-pass | **Verify ref THẬT non-empty + MODEL_DRIFT clean** (B13-1/A10) |
| B16-2 | acceptance dựa green+coverage → ACCEPT model-sai (87 green/93%) | **Bổ sung model-match + sanity; coverage CẦN-không-đủ** (B5-7/9) |
| B16-3 | test-execution map vào D-27 có thể stale | **Check D-27 STALE (version) trước khi map; stale → cảnh báo/blocked** (A2) |
| B16-4 | acceptance không kiểm UX↔mockup | **Khi Part D áp dụng → acceptance thêm tiêu chí UX↔mockup (visual/E2E)** (conditional, F-5) |
| (inherited) | phase-entry override logging (B4-5) · autonomy (human-decision đã có) | |

---

### 3.6 Cross-cutting — Gate · Traceability · Readiness · Migrate · Agents

#### B.6 — `hbc-phase-gate` (đã chốt)

> **Kế thừa Phần A vào gate engine:** A1 (item model-spike ở P1) · A2 (STALE theo version-set) · A4 (decision-gate chặn TBD/ADR-open) · A8 (auto-revalidate) · A9 (matrix-completeness) · IMP-03 (crash→BLOCKED, no silent manual-pass). Dưới đây là quyết định **riêng của gate**:

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B6-1 | QUALITY item LLM tự chấm → rubber-stamp (passed trên model sai) | **Adversarial (skeptic+acceptance) bắt buộc + bằng chứng định lượng (ID/count), bất đồng → CONTESTED** |
| B6-2 | Số liệu 'X/Y' do LLM khai (case: 39/39 code_ref khi matrix trống) | **Mọi METRIC/count do script tính trên artifact thật, LLM không tự khai** |
| B6-3 | lenient hạ mọi FAILED→WARNING | ⚠️ **ĐÃ CÓ SẴN** (entry-gate không bị lenient hạ — `hbc-phase-gate/SKILL.md:71` + test `test_entry_gate_failure_not_downgraded_by_lenient`). Chỉ cần **MỞ RỘNG** cho item correctness/model (đã đúng cho entry-gate). *(Lỗi review: đề xuất thứ đã tồn tại — đọc source kỹ hơn.)* |
| B6-4 | na_deliverables waiver dễ lạm dụng | **Waiver cần rationale + KHÔNG được miễn item tính-đúng** |
| B6-5 | Gate tự tuyên 'done' | **PASS phase thiết kế (1/2) cần user sign-off** |
| B6-6 | Bằng chứng mơ hồ → tự pass | **Mơ hồ → CONTESTED/hỏi (interactive) / blocked (headless), không auto-pass** (A5) |

#### B.7 — `hbc-traceability` (Impact engine) (đã chốt)

> **Case bỏ qua hoàn toàn engine này** (viết tay thay vì cascade). Kế thừa A3 (rebaseline), A9 (matrix-completeness). Quyết định riêng:

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B7-1 | Cascade chỉ 'suggest, user tự chạy' → dễ skip | **Đổi doc có downstream → cascade BẮT BUỘC: block 'complete'/phase tới khi Impact đã chạy** (Impact vẫn READ-only, nhưng việc chạy là bắt buộc) |
| B7-2 | Matrix khuyết → under-propagate | **Skill tự ghi matrix ở phase của mình (design_ref/test_ref/code_ref) + gate verify đầy đủ** (A9) |
| B7-3 | Không phát hiện 'đổi mà chưa cascade' | **Drift-watch: so version-set, artifact đổi mà downstream chưa cascade → cảnh báo/STALE** (A8) |
| B7-4 | RECONCILE LLM tự chấm | **RECONCILE cần adversarial + bằng chứng deterministic, không tự chấm** |
| B7-5 | Đổi phá-cấu-trúc vẫn fork-task | **Thay đổi phá-cấu-trúc frozen → route sang `hbc-rebaseline` (A3), KHÔNG fork-task additive** |
| B7-6 | Cascade trên matrix khuyết | **Cascade yêu cầu matrix đầy đủ trước khi chạy (khuyết → blocked untraced_change + backfill)** |

#### B.13 — `hbc-check-implementation-readiness` (seam-gate) — review độc lập (subagent)

> **Đây là seam-gate mà case lỗi.** Verdict thì script-verified/trung thực, nhưng **phạm vi quá hẹp** → nửa thất bại lọt qua.

| # | Lỗ hổng (grounded file:line) | Quyết định |
|---|---|---|
| B13-1 | Matrix kiểm **REQ-id-có-mặt, không parse cột** → "39/39 code_ref" giả vô hình (check-readiness.py:99-105,193-201) | **Parse cột matrix**: verify code_ref/test_ref/design_ref non-empty per REQ (nối A9/B7-2) |
| B13-2 | **Không reconcile task-breakdown** (no `--tasks`) | **Thêm input task-breakdown + reconcile REQ↔TASK↔current-design** (nối B4-6) |
| B13-3 | **Không kiểm D-19 currency** (D-19 không phải input) | **Thêm D-19 vào seam + MODEL_DRIFT** (nối A10/B5-1) |
| B13-4 | **Không version-drift** giữa docs | **Version-coherence ở seam** (nối IMP-01/A2) |
| B13-5 | "covered" mức-nhắc-tên cho matrix/D-26/D-21 → **paste-appendix loophole** | **Scope-hoá như D-27** (TC/row-level), không findall toàn file |
| B13-6 | headless-contract schema sai (`reason` script không emit) | **Sửa contract khớp engine** |
| (giữ) | `missing_from_matrix` ĐÃ CÓ — bắt 040-042 nếu chạy đúng nguồn | Giữ + **gọi readiness bắt buộc** (B7-1 cascade-enforced) |

#### B.14 — `hbc-migrate` — review độc lập (subagent)

> Faithful (không bịa row — tốt), nhưng nhiều bug + over-promise; **xác nhận rebaseline (A3) cần engine MỚI, không extend migrate**.

| # | Lỗ hổng (grounded) | Quyết định |
|---|---|---|
| B14-1 | Phát hiện missing-row chỉ ở prose, engine không emit (build_plan:300-328) | **Engine emit `missing_from_matrix` (D-02 vs matrix diff)** trong plan JSON |
| B14-2 | Re-prefix **regex global** dễ hỏng code-ref/prose `REQ-001` (lines 141-144,351-355); no dry-run diff | **Scope re-prefix vào cột id; dry-run diff thực vị trí thay** |
| B14-3 | Scope lệch: task-breakdown/gates **không re-prefix** → traceability gãy ngầm (REPREFIX_DOCS:58) | **Mở rộng re-prefix sang implementation-artifacts/gates HOẶC cảnh báo rõ** |
| B14-4 | dirty-guard **tắt im lặng ngoài git** (273-286); timestamp default cố định → **backup đè** (68,289-297) | **Cảnh báo khi guard off + timestamp bắt buộc/unique (no silent overwrite)** |
| B14-5 | headless/decision-log/validation **hứa trong contract nhưng engine không có** (331-367) | **Đồng bộ contract↔engine** (implement hoặc bỏ khỏi contract) |
| B14-6 | Strictly one-time v1→v2; `has_legacy_layout` từ chối tree đã-v2 (90-100) | **Xác nhận A3 `hbc-rebaseline` = engine MỚI** (cross-feature/đã-v2/D-19-diff), KHÔNG extend migrate |

#### B.17 — 5 agent (`ba/architect/qa/dev/tester`) (đã chốt)

> Agent = **bề mặt autonomy** (nơi 'tự-quyết' lo nhất) + nơi điều phối các bước mới.

| # | Vấn đề (grounded) | Quyết định |
|---|---|---|
| B17-1 | Persona 'quyết & làm tiếp' | **Persona mọi agent: ưu tiên ELICIT > auto-proceed ở quyết-định-miền** (A5) |
| B17-2 | Menu cũ không điều phối bước mới | **Cập nhật mỗi agent điều phối bước mới**: BA (pipeline B1) · Architect (model-spike+DB-3-tier+architecture) · QA (technique-map+edge-review) · Dev (MODEL_DRIFT+no-spec-ref+sanity) · Tester (model-match acceptance) |
| B17-3 | Phase-entry không nhất quán — **verify: CẢ 5 agent chỉ "warn"** (architect:72/dev:68/tester:62), HALT thật chỉ ở tầng skill (task-breakdown:35, test-execution:35) | **Mọi agent HALT-on-unclosed-predecessor nhất quán + log override** (kéo teeth từ skill lên agent) |
| B17-4 | Self-review | **Agent gọi subagent độc lập cho review/semantic (không tự chấm)** (B6-1 + meta-lesson) |

> **Coverage HOÀN TẤT:** 16 skill + 5 agent đã review (B.1–B.17; B.12 api-spec = N/A). Không còn skill bị defer.

---

## 4. Roadmap triển khai HBC (ưu tiên theo đợt — Phần C)

### Đợt 1 — Quick wins (rẻ, script/lint, làm trước)

| Item | Nội dung | Nguồn |
|---|---|---|
| QW-1 | Validator **version-coherence** cross-doc | IMP-01 |
| QW-2 | **Lint spec-ref** trong code/test (D-12 rule máy-kiểm) | IMP-02, B5-2, B10-2 |
| QW-3 | Gate-script **robust + cấm silent manual-pass** (crash→BLOCKED) | IMP-03 |
| QW-4 | **Số liệu gate do script tính**, không LLM khai | B6-2 |
| QW-5 | Coverage checks: **REQ↔matrix↔task↔TC** (REQ→task, matrix completeness) | A9, B4-6 |
| QW-6 | **MODEL_DRIFT**: code vs D-19 hiện hành | A10, B5-1 |

### Đợt 2 — Seams (hành vi gate / cascade / review)

| Item | Nội dung | Nguồn |
|---|---|---|
| SE-1 | Gate **STALE theo version-set** + **auto-revalidate** + **drift-watch** | A2, A8, B7-3 |
| SE-2 | **ADR / decision-gate** (chặn complete khi còn TBD/ADR-open) | A4, B2-10 |
| SE-3 | **Matrix completeness gate** + skill **tự ghi matrix** ở phase | A9, B7-2 |
| SE-4 | **Cascade enforced** (block complete tới khi Impact chạy) | B7-1 |
| SE-5 | **QUALITY/semantic adversarial + sign-off** (gate + mọi create-skill); reconcile adversarial | B6-1, B7-4, semantic-inherited |
| SE-6 | **Lenient/waiver/sign-off** siết: không miễn correctness; PASS phase 1/2 cần user | B6-3,4,5,6 |
| SE-7 | **Review bắt buộc**: D-02+D-06 (adversarial+edge-case); D-27 (edge-case) | B1-9, B8-7, B3-9 |
| SE-8 | **Anti-false-green sanity** discipline (test-spec + implement) | B3-1, B5-3, B5-9 |
| SE-9 | **A5 autonomy** wiring: ASK-at-domain-decision + grounding cho mọi create/implement skill | A5, toàn B |

### Đợt 3 — Cấu trúc (capability mới, lớn)

| Item | Nội dung | Nguồn |
|---|---|---|
| ST-1 | **Model-Spike** giữa P1–P2 + P1 gate item; D-19 logical là đối tượng spike — ⚠️ **HYPOTHESIS, CHƯA commit** (F-4: pilot trước; nhân-quả chưa chứng minh) | A1, B2-6 |
| ST-2 | **`hbc-rebaseline` engine** + cấp 'baseline/epic-change' + Impact declare-shared + route structural-change | A3, A6, B7-5 |
| ST-3 | **Maturity `exploratory\|stable`** (gate ceremony + depth-gating test-spec) | A7, B3-3 |
| ST-4 | **Nâng chuẩn per-skill** (research-backed): | |
| | · D-19: **3-tier ASK-gates** (conceptual/logical/physical) + ondelete/index/constraint hỏi | B2-1..4 |
| | · D-27: **technique-map** (decision-table/state-transition/EP-BVA/use-case) + test-data ground D-19 | B3-2,5 |
| | · task-breakdown: **vertical-slice + INVEST + SPIDR + test-list** + input D-06/AC/Spike/code-reality | B4-1,2 |
| | · D-06: **BPMN swimlane + gateway** + path-coverage (happy/alt/exception) + **path-IDs** | B8-1,2,6 |
| | · D-26: **technique-per-scope-area** (link D-27) + risk grounded + no-fabricated-schedule | B9-1,2,4 |
| | · D-02: intake pipeline **feasibility→quick-discovery→[brainstorm]→discovery→review** | B1 |
| | · D-03: ubiquitous-language + cross-doc consistency | B11-2,3 |

> **Phần D (UX) bổ sung Roadmap:** UX-2/UX-3 → Đợt 2; UX-5/UX-6 → Đợt 2–3; UX-1/UX-4/UX-7/UX-8 → Đợt 3. **Phần E (khung chuẩn) bổ sung Roadmap:** E-8 + E-3/E-4/E-5 → Đợt 1–2; E-1/E-2/E-6/E-7 → Đợt 3.

### Cách verify các cải tiến
Dùng chính **`resource-plan-billable`** (đang dở giữa model cũ↔v2.3) làm **regression fixture**: nếu các item hoạt động, chúng phải bắt được — gate STALE sau v2.0, matrix thiếu REQ-040/041/042, code MODEL_DRIFT, task-breakdown sót slice request/snapshot, D-27 xanh-giả, và đáng lẽ đã chặn cascade ở model chưa-kiểm-chứng.

---

## 5. Giới hạn & cảnh báo phương pháp + Phụ lục

### ⚠️ Giới hạn & cảnh báo phương pháp (sau review của adversarial-subagent độc lập)

Đọc tài liệu này KÈM các cảnh báo sau — chúng là rủi ro thật của chính tài liệu/quá trình:

1. **Quyết định = khuyến nghị của tác giả được phê chuẩn, KHÔNG độc lập.** ~145 quyết định phần lớn là phương án "(Khuyến nghị)" xếp đầu + maintainer đồng ý → **leading-question + rubber-stamp** (đúng anti-pattern A5/B6-1 mà doc chê). Coi đây là **đề xuất cần thẩm định lại độc lập**, không phải chân lý.
2. **Cân bằng THÊM:BỎ ≈ 25:1.** Đề xuất chủ yếu **cộng dồn** (~9-10 doc mới · ~12 engine · ~35-40 gate/review) trong khi than phiền gốc là *quá nhiều nghi lễ/rework*. **Thiếu hẳn mục "giảm tải/bỏ bớt".** Rủi ro: HBC nặng hơn → **gate-fatigue → override/bypass** (lẻn autonomy cửa sau, headless→blocked hàng loạt). *(F-1 de-ceremony vá hướng này.)*
3. **Nhân-quả chưa chứng minh.** Các fix (đặc biệt Model-Spike) **chưa được trace là sẽ ngăn case**: RCA cho thấy model chỉ bị nhận ra sai *sau khi build*, và v2.3 vẫn chưa frozen → spike có thể đẻ ra cùng model sai. Coi là **giả thuyết cần thử nghiệm**, không phải đảm bảo. *(F-4 hypothesis+pilot vá.)*
4. **Thiếu actionability:** không size **effort/cost/ROI**, không **sequence dependency** (có Đợt-1 phụ thuộc Đợt-3), không **success-metric** đo hiệu quả sau cải tiến, và **trộn "đã chốt" với "thiết kế lớn chưa đặc tả"** (vd `hbc-rebaseline` = subsystem nhiều tuần, chưa tồn tại) cùng format. *(F-2 sizing + F-6 metrics vá.)*
5. **Một số "phát hiện" đã có sẵn / lỗi nguồn:** B6-3 đã tồn tại trong gate; "catalog hbc_validation" là bịa (xem đính chính Phần E §3.0); IEEE 829 đã withdrawn. → **confirmation-bias cộng dồn**, ít kết luận "đủ rồi, giữ nguyên".
6. **Coverage** *(✅ ĐÃ GIẢI QUYẾT — B.13–B.17 đã review hết; không còn skill defer)*: trước đây defer 6 skill + 5 agent — đặc biệt `hbc-check-implementation-readiness` (seam-gate case lỗi) + `hbc-migrate` (nền A6) → nay đã soi (B.13/B.14/B.15/B.16/B.17).
7. **Phần D (UX) phần lớn điều kiện theo Claude Design** — một tool N/A-tiềm-năng cho Odoo back-office (UI = server-rendered view/wizard, cùng lý do D-21 N/A); cost/benefit chưa xét. *(F-5 conditional vá.)*
8. **Hygiene:** ✅ đã vá — frontmatter có `owner`/`reviewer`/`status`. (Cảnh báo này giữ lại để truy vết, không còn live.)

**Hệ quả:** dùng tài liệu như **backlog ý tưởng có cấu trúc để THẨM ĐỊNH + ưu tiên**, không phải spec để code thẳng. Việc tiếp theo nên là: thẩm định độc lập từng item, thêm effort/ROI/dependency/metrics (đã có ở Phần F), và một vòng "cái gì BỎ/giữ-nguyên".

### Phụ lục — nguồn & kỹ thuật

- **Bằng chứng case (grounded):** Revision History D-02(13)/D-19(7)/D-06(6)/D-26(6)/D-27(~8); matrix thiếu REQ-040/041/042 + code_ref trống; code có `resource.plan.state` + manual sync wizard, **không** có `resource.plan.request`; 146 test model cũ; 65 spec-ref leak; P1/P2/P3 gate PASSED trên model cũ + manual-pass sau evaluator crash.
- **HBC intent (đọc source):** entry-gate B2; task-breakdown HALT; Impact = READ+SUGGEST + FREEZE-CHECK; matrix = đồ thị tác động; shared D-19/D-03/D-12 đổi chỉ ADVISORY; không có path gated cho đổi-model-lõi-sau-Phase-3.
- **Kỹ thuật:** Lean 7–8 wastes (Lean Enterprise Institute; Boldare) · RCA 5-Whys + Fishbone (PRIZ Guru) · Gap analysis (Hyperproof) · DB 3-tier (AWS/Visual Paradigm/ER-Studio) · test specification-based (decision-table/state-transition/EP-BVA/use-case/example-mapping) · TDD vertical-slice (INVEST/SPIDR/Kent Beck test-list) · BPMN swimlane + path-coverage · ISO/IEC/IEEE 29119-3 (thay IEEE 829 withdrawn) · DDD ubiquitous-language · UX component-driven/visual-regression/design-tokens/ATDD.

<!-- END -->
