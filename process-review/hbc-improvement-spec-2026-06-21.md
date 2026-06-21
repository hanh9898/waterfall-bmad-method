---
title: "HBC Improvement Spec — chia phase / chia công việc / phân role (từ technical-research 2026-06-21)"
status: draft (chờ triển khai)
date: 2026-06-21
author: Hanhnt2 (qua bmad-technical-research → spec)
source_research: _bmad-output/planning-artifacts/research/technical-hbc-phase-workbreakdown-role-research-2026-06-21.md
related:
  - process-review/hbc-buildgraph-redesign-2026-06-21.md   # mô hình 3 trục (A=máy, B=khung, C=elicitation)
  - process-review/hbc-trucb-build-plan-2026-06-21.md       # trục B đã build (D-09/D-16/D-14 + catalog + folds)
  - process-review/hbc-improvement-proposal.md
---

# HBC Improvement Spec — Phase / Work-breakdown / Role

> Chuyển hóa các phát hiện của technical-research thành **spec cải tiến hành động được**. Mỗi item có ID `IMP-xx`, trục (A=enforcement-bằng-máy / B=khung-structure), nơi tác động, thay đổi cụ thể, applicability/maturity gating, DoD, phụ thuộc, rủi ro.

## 0. Quyết định đã confirm (2026-06-21)

| # | Câu hỏi | Quyết định |
|---|---------|-----------|
| Q1 | Mức enforce | **B + A đầy đủ** — gồm gate scoring engine, Recycle state-machine, machine-check coverage/V-pair. **Trục A gated bởi spike kernel** (xem §4 Wave 2). |
| Q2 | Dual-track | **Risk-classifier + discovery step** — gate Phase 1 phân loại known/uncertain; uncertain bắt buộc walking-skeleton/discovery loop trước design-first. |
| Q3 | Lean/flow | **Guidance + gate-question** — appetite chốt ở gate BA, circuit-breaker = outcome gate, hill-chart = cách report. **Không build tracking machine.** |
| Q4 | Gate model | **Recycle + 2 tầng criteria** — outcome Recycle (trả về phase trước) + must-meet (knock-out) / should-meet (scorecard semantic). |

**Nguyên tắc nền (giữ xuyên suốt):** HBC là framework **đầy đủ & tổng quát** — item không cắt vì "Odoo không cần", mà gate bằng **applicability-catalog + maturity**. Không hardcode framework (adapter). Handoff giữa persona **bắt buộc qua artifact D-xx có cấu trúc** (điều kiện MetaGPT/Anthropic) — không bao giờ bằng hội thoại tự do.

---

## 1. Tổng quan 19 item

| ID | Tên | Trục | Skill/nơi | Wave |
|----|-----|:----:|-----------|:----:|
| IMP-01 | Gate outcome: +Recycle, state-machine PASS/FAIL/RECYCLE | A | hbc-phase-gate | 2 |
| IMP-02 | Gate exit-criteria 2 tầng (must/should schema) | B→A | hbc-phase-gate/checklists | 1→2 |
| IMP-03 | Vertical-slice task-rule + catalog SPIDR/Lawrence | B | hbc-task-breakdown | 1 |
| IMP-04 | test-list = task-list (Canon TDD) | B | hbc-task-breakdown | 1 |
| IMP-05 | Invariant 100%-rule coverage (REQ↔task) | A | hbc-task-breakdown | 2 |
| IMP-06 | INVEST-check (feature) + SMART-check (task) | B | hbc-phase-gate P1, hbc-task-breakdown | 1 |
| IMP-07 | Surface + enforce `v_pair` (design↔test edge) | A+B | catalog, ma trận, hbc-traceability | 1→2 |
| IMP-08 | Đặt tên shift-left + EARS→ATDD + BDD facet | B | docs, hbc-create-behavioral-design, hbc-acceptance-check | 1 |
| IMP-09 | Risk-classifier known/uncertain ở gate P1 | B | hbc-agent-ba, hbc-create-requirements, P1 checklist | 1 |
| IMP-10 | Discovery/walking-skeleton step (uncertain) | B | **skill mới** hbc-discovery-spike | 1.5 |
| IMP-11 | Appetite/feature chốt ở gate BA | B | hbc-agent-ba, P1 checklist | 1 |
| IMP-12 | Circuit-breaker = outcome gate (re-slice/defer/kill) | B+A | hbc-phase-gate | 1→2 |
| IMP-13 | WIP-limit cấp portfolio (guidance) | B | docs (workflow-map/concepts) | 1 |
| IMP-14 | Hill-chart reporting (uphill/downhill) | B | hbc-phase-gate report, docs | 1 |
| IMP-15 | `constitution.md` — nguyên tắc xuyên-phase ở Phase 0 | B | hbc-project-init | 1 |
| IMP-16 | Quick-Plan fast-path + bugfix-lane (theo maturity) | B | hbc-project-init/maturity, agents | 1 |
| IMP-17 | Markers `[NEEDS CLARIFICATION]` trong template D-xx | B | tất cả hbc-create-* template | 1 |
| IMP-18 | Role doc: R/A, process-integrity owner, Party-Mode, Dev=Responsible | B | 5 agent SKILL, docs | 1 |
| IMP-19 | Cascade-sync = nguyên tắc load-bearing | B | docs, constitution | 1 |

---

## 2. Chi tiết item

### Nhóm A — Phase-gating (Cooper Stage-Gate)

#### IMP-01 — Gate outcome model: +Recycle + state-machine `[Trục A · Wave 2]`
- **Vì sao:** Cooper — gate là *decision* (Go/Kill/Hold/**Recycle**), không phải completeness-check pass/fail. Gate chỉ-bao-giờ-"Go" = theater.
- **Thay đổi:** `hbc-phase-gate` trả 3 outcome: `PASSED` / `FAILED` (sửa tại chỗ rồi chạy lại) / **`RECYCLE→phase-(n-k)`** (trả feature về phase trước khi lỗi thuộc tầng trước — vd readiness gate bounce design về Analysis). Gate ghi `recycle_to` + lý do vào `gates/phase-n-gate.md` và cập nhật `gate_status` ma trận.
- **Phụ thuộc:** build-graph kernel (trục A) để mô hình hoá "trả về" + dirty-set re-propagation. **Spike-gated.**
- **DoD:** state-machine 3-outcome có test; ma trận phản ánh recycle; doc gate cập nhật.
- **Rủi ro:** loop vô hạn recycle → cap số lần + escalate USER.

#### IMP-02 — Exit-criteria 2 tầng `[Trục B→A · Wave 1→2]`
- **Vì sao:** Cooper must-meet (knock-out) vs should-meet (scorecard).
- **Thay đổi (Wave 1, data):** mỗi dòng checklist gắn `tier: must|should`. **must** = structural-validator pass + traceability-complete + model-validation (P1-09) → một "No" là FAIL. **should** = facet semantic-review rubric (read/write·api/admin·lifecycle) → scorecard, ngưỡng đậu = `openFacets` rỗng.
- **Thay đổi (Wave 2, engine):** gate-evaluation script đọc tier, tính verdict 2 tầng.
- **DoD:** checklist có cột tier; engine phân biệt knock-out vs scorecard.

### Nhóm B — Work-breakdown

#### IMP-03 — Vertical-slice task-rule + catalog `[Trục B · Wave 1]`
- **Vì sao:** Lawrence/Cohn đồng thuận cao nhất: cắt DỌC xuyên tầng, không cắt NGANG theo tầng. **Lỗ hổng cụ thể nhất của HBC:** task-breakdown dễ âm thầm tái lập "model→API→UI" dù feature đã vertical (vì D-19/D-21 là deliverable theo-tầng).
- **Thay đổi:** thêm `src/hbc-task-breakdown/references/splitting-patterns.md` (catalog SPIDR + 9 pattern Lawrence) + quy tắc trong SKILL: "mỗi task = lát dọc đẩy 1–vài test-case RED→GREEN→REFACTOR; cấm task thuần-một-tầng". Mỗi task nêu pattern dùng để justify slice.
- **DoD:** reference + guidance inline; ví dụ vertical vs horizontal.

#### IMP-04 — test-list = task-list (Canon TDD) `[Trục B · Wave 1]`
- **Vì sao:** Kent Beck — task breakdown CHÍNH LÀ test-list (biến thể hành vi + edge-case), 1 test/lần, sắp đơn-giản-trước; SPIDR "Rules/Data" = "what-if" trên test-list.
- **Thay đổi:** output `hbc-task-breakdown` = test-list per-feature, mỗi task ≈ 1 biến thể hành vi, có thứ tự. Caveat anti-đầu-cơ của Beck hoà giải bằng coi test-list là **living artifact** (đã có cascade-sync + DF-9 drift).
- **DoD:** template task-breakdown phản ánh test-list-shape.

#### IMP-05 — Invariant 100%-rule coverage `[Trục A · Wave 2]`
- **Vì sao:** WBS quy-tắc-100% (đủ + không dư) ánh xạ qua traceability.
- **Thay đổi:** script structure-only trong `hbc-task-breakdown`: breakdown hợp lệ ⟺ (a) mọi REQ-ID phủ ≥1 task **và** (b) mọi task map ≥1 REQ-ID (chống gold-plating). JSON-stdout, verdict honest.
- **Phụ thuộc:** ma trận traceability ổn định (đã có).
- **DoD:** script + pytest; gate Phase 3 đọc verdict.

#### IMP-06 — INVEST(feature) + SMART(task) `[Trục B · Wave 1]`
- **Vì sao:** INVEST cho value-unit, SMART cho task — khác tầng, khác tiêu chí.
- **Thay đổi:** gate Phase 1 thêm item `P1-10` INVEST-check cho *feature* (fail "Small" → tách thành feature anh-em *trước khi* vào lifecycle, KHÔNG tách thành task); guidance SMART cho task trong hbc-task-breakdown. KHÔNG đòi task "Independent/Valuable" (category-error đẩy về cắt-tầng).
- **DoD:** P1-10 trong checklist; guidance SMART.

### Nhóm C — V-Model / quality pairing

#### IMP-07 — Surface + enforce `v_pair` `[Trục A+B · Wave 1→2]`
- **Vì sao:** V-Model — level *viết* spec sở hữu test-gate khớp nó; catalog HBC **đã có field `v_pair`** (ngầm).
- **Thay đổi (Wave 1):** surface `v_pair` trong docs + template mỗi design-facet ("test level kiểm chứng: D-09↔integration, D-16↔unit, D-14↔e2e, D-02↔acceptance, D-21↔integration"). **Thay đổi (Wave 2):** ma trận + `hbc-traceability` enforce cạnh design↔test theo v_pair (thiếu cạnh = gap có severity).
- **DoD:** v_pair hiển thị; audit traceability bắt thiếu cạnh v_pair.

#### IMP-08 — Đặt tên shift-left + EARS→ATDD + BDD facet `[Trục B · Wave 1]`
- **Vì sao:** HBC *đã là* model-based + incremental shift-left (validator/semantic-review trước code; per-feature = nhiều V nhỏ) — dạng mạnh nhất; nêu rõ làm differentiator.
- **Thay đổi:** docs concepts/why-incremental nêu "model-based + incremental shift-left"; map EARS-requirement (D-02) → ATDD-acceptance (`hbc-acceptance-check`); BDD Given-When-Then cho facet behavioral-design (D-16) ↔ test hành vi. Dùng facet-conditionality (không ép BDD/ATDD lên feature CRUD).
- **DoD:** doc + ghi chú trong 2 skill liên quan.

### Nhóm D — Incremental/iterative (dual-track) — Q2

#### IMP-09 — Risk-classifier known/uncertain `[Trục B · Wave 1]`
- **Vì sao:** Cockburn — incremental-only = xây xong mới biết sai; cần iterative khi discovery-risk cao.
- **Thay đổi:** elicitation BA + item gate `P1-11`: phân loại feature **known** (yêu cầu rõ, ít mơ hồ) vs **uncertain** (nhu cầu/UX chưa rõ, giả định chưa chứng). Lưu vào D-02 frontmatter (cạnh `maturity`/`facets`). known → đường design-first; uncertain → bắt buộc IMP-10.
- **DoD:** frontmatter field `discovery_risk`; P1-11 checklist.

#### IMP-10 — Discovery / walking-skeleton step `[Trục B · Wave 1.5 · skill mới]`
- **Vì sao:** dual-track (Patton/Cagan) + walking-skeleton/tracer-bullet (Cockburn/Pragmatic): lát end-to-end mỏng nhất *trước* để validate + khử rủi-ro tích-hợp.
- **Thay đổi:** skill mới `hbc-discovery-spike` (full anatomy) — chỉ chạy khi `discovery_risk=uncertain` (applicability-gated). Output: walking-skeleton/prototype + validation-note có thể **kill/reshape** feature *trước* design→test→build. Chạy sau REQ nháp, trước khi đóng Phase 1.
- **Đăng ký:** marketplace.json + module.yaml + module-help.csv (menu-code `DSC`).
- **DoD:** skill + validator structure-only + test + headless-contract; gate P1 cho phép "uncertain chưa có discovery → FAIL".
- **Rủi ro:** đừng biến mọi feature thành dual-track (chỉ uncertain); giữ design-first làm default.

### Nhóm E — Lean/flow (Q3: guidance + gate-question, KHÔNG build machine)

#### IMP-11 — Appetite/feature chốt ở gate BA `[Trục B · Wave 1]`
- **Vì sao:** Shape Up — appetite (ngân sách, không phải estimate); fixed-time/variable-scope.
- **Thay đổi:** elicitation BA chốt **appetite** + tách must-have vs **defer-to-next-feature** *từ đầu* (tránh cắt scope giữa-chừng phá ma trận; REQ defer thành *feature kế*, không thành dòng mồ-côi). Ghi `appetite` D-02 frontmatter. Item gate `P1-12`.
- **DoD:** field appetite + guidance "defer → feature kế".

#### IMP-12 — Circuit-breaker = outcome gate `[Trục B+A · Wave 1→2]`
- **Vì sao:** Shape Up — không xong trong appetite → xét lại, KHÔNG auto-gia-hạn.
- **Thay đổi (Wave 1):** guidance: feature blow appetite → gate decision re-slice/defer/kill. **Wave 2:** nối vào outcome Recycle (IMP-01) như một nhánh.
- **DoD:** guidance + (Wave 2) nhánh trong state-machine.

#### IMP-13 — WIP-limit portfolio (guidance) `[Trục B · Wave 1]`
- **Vì sao:** Little's Law — quá nhiều feature dở → queue ẩn giữa gate, cycle-time phình. Khoảng trống: docs im lặng về số feature song song.
- **Thay đổi:** thêm mục guidance trong docs (workflow-map/concepts): "giới hạn số feature đang giữa Phase 1–4 đồng thời"; trong-feature đã WIP=1/phase nên đây là vấn đề cross-feature.
- **DoD:** đoạn doc + ghi chú.

#### IMP-14 — Hill-chart reporting `[Trục B · Wave 1]`
- **Vì sao:** Shape Up — uphill (còn unknown) / downhill (chỉ-còn-thực-thi) trung thực hơn %-complete.
- **Thay đổi:** report gate khung uphill (Phase 1–2) / downhill (Phase 3–4); doc nêu cách đọc.
- **DoD:** guidance report.

### Nhóm F — Spec-driven / AI-era

#### IMP-15 — `constitution.md` Phase 0 `[Trục B · Wave 1]`
- **Vì sao:** Spec Kit — lớp nguyên tắc bất biến cấp dự án (test-first, language-policy, SoD, simplicity-caps) trên mọi deliverable; HBC hiện rải rác trong prose/customize.toml.
- **Thay đổi:** `hbc-project-init` sinh shared deliverable `constitution.md` (nguyên tắc xuyên-phase, regeneration-stable). 5 persona tham chiếu như hợp đồng chung.
- **DoD:** template + bước trong PI + ghi vào deliverable-catalog (scope shared, Phase 0).

#### IMP-16 — Quick-Plan fast-path + bugfix-lane `[Trục B · Wave 1]`
- **Vì sao:** Kiro — escape-hatch cho việc đã-rõ; Bugfix spec ≠ Feature spec. Giảm overhead 4-gate/feature.
- **Thay đổi:** gắn vào `maturity` đã có: `exploratory`/trivial → fast-path (gộp/bỏ một số gate-question). Thêm **bugfix-lane** (lighter deliverable-set: D-02-mini + test + acceptance) qua applicability-catalog.
- **DoD:** maturity-driven fast-path; bugfix applicability-profile trong catalog.

#### IMP-17 — `[NEEDS CLARIFICATION]` markers `[Trục B · Wave 1]`
- **Vì sao:** Spec Kit — van xác định, buộc model nêu bất định thay vì đoán thầm (hợp trục C elicitation + MÁY/USER/LLM).
- **Thay đổi:** template D-xx có quy ước marker `[NEEDS CLARIFICATION: ...]`; semantic-review + gate coi marker còn sót = `pending`, không `passed`.
- **DoD:** marker trong template + check ở gate/semantic-review.

### Nhóm G — Roles (Q7)

#### IMP-18 — Role doc clarifications `[Trục B · Wave 1]`
- **Vì sao:** SoD + V-Model + RACI bảo chứng "1 persona/phase·gate"; nhưng phải tách R/A, đặt tên process-owner, chống abdication, và **handoff phải qua artifact** (MetaGPT/Anthropic — coding HBC tuần tự+coupled, multi-agent chỉ đáng vì handoff có cấu trúc).
- **Thay đổi:**
  - Mỗi gate khai báo **R** (persona làm) vs **A** (persona chịu trách nhiệm gate) — tránh "tự chấm bài mình".
  - Đặt tên **process-integrity owner** = engine `hbc-phase-gate`+traceability (vai ≈ Scrum-Master, hiện ẩn).
  - **Giữ Dev *Responsible* cho chất lượng** (TDD) dù QA/Tester *Accountable* gate — chống abdication "QA sẽ bắt".
  - **Party-Mode** (đa-persona tranh-luận) tại readiness gate Phase 2 (Architect+QA reconcile D-21 vs D-26).
  - Ghi nguyên tắc bất biến: **persona handoff chỉ qua D-xx + ma trận, cấm hội thoại tự do** (vào constitution.md / IMP-15).
- **DoD:** cập nhật 5 agent SKILL + docs role; ghi vào constitution.

#### IMP-19 — Cascade-sync = nguyên tắc load-bearing `[Trục B · Wave 1]`
- **Vì sao:** Thoughtworks — bẫy SDD-waterfall ("trọng lực kéo về specify-hết-trước"); thuốc giải = regenerate-downstream-on-change. Cũng là thuốc giải độ-cứng V-Model.
- **Thay đổi:** nâng cascade-sync (`SYNC` + DF-9 drift) thành **nguyên tắc thiết kế tuyên bố rõ** trong docs + constitution: "đổi spec ⇒ tái-lan-truyền downstream; đây là cái giữ HBC khỏi thành waterfall".
- **DoD:** đoạn nguyên tắc trong concepts + constitution.

---

## 3. Đã khớp sẵn (không cần làm, chỉ ghi nhận)
- **EARS** (Kiro/Rolls-Royce) — D-02 đã dùng ✅
- **Tách QA khỏi Dev** — HBC đã mạnh hơn BMad (SoD) ✅
- **Per-feature = incremental shift-left** — đã có ✅ (IMP-08 chỉ đặt tên)
- **Phase set khớp hội tụ spec→design→tasks→implement** ✅

---

## 4. Sequencing (waves)

**Wave 0 — Spike kernel (prereq trục A):** spike build-graph trên `resource-plan-billable` (đã chốt hướng trong buildgraph-redesign). Mở khoá IMP-01, IMP-05, IMP-07(enforce), IMP-12(outcome).

**Wave 1 — Trục B (làm ngay, không cần spike):** IMP-02(data), 03, 04, 06, 07(surface), 08, 09, 11, 13, 14, 15, 16, 17, 18, 19. → phần lớn giá trị, rủi ro thấp.

**Wave 1.5 — Skill mới:** IMP-10 `hbc-discovery-spike` (đăng ký 3 nơi + test). Phụ thuộc IMP-09 (risk-classifier).

**Wave 2 — Trục A (sau spike):** IMP-01 (Recycle+engine), IMP-05 (coverage check), IMP-07 (enforce v_pair edges), IMP-12 (circuit-breaker outcome), IMP-02 (engine 2 tầng).

---

## 5. Rủi ro & guard tổng
- **Quá nhiều gate-question** (IMP-06/09/11/12 đều thêm item P1) → dùng maturity fast-path (IMP-16) + facet-conditionality để không thành nghi-lễ.
- **Dual-track lan rộng** (IMP-10) → chỉ uncertain; design-first là default.
- **Recycle loop** (IMP-01) → cap + escalate.
- **Abdication chất lượng** (IMP-18) → Dev giữ Responsible.
- **Handoff vỡ thành hội thoại** → constitution cấm rõ; chỉ artifact.
- Trục A phụ thuộc spike chưa chứng minh → Wave 2 KHÔNG khởi động trước khi spike PASS.

---

## 6. Bước tiếp theo đề xuất
1. Chốt spec này (USER review §2).
2. Khởi động **Wave 1** ngay (trục B) — phần lớn là `references/` + `template` + checklist + docs + 5 agent + constitution.
3. Lên lịch **spike kernel** (Wave 0) để mở Wave 2.
4. IMP-10 (skill mới) chạy qua `bmad-workflow-builder` như các hbc-create-* khác.

*Hết spec. Truy vết nguồn: xem reading-list §10 của research doc.*
