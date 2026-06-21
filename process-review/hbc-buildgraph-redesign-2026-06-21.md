---
title: "Đề xuất Kiến trúc — HBC Build-Graph Redesign (mô hình 3 trục)"
doc_type: architecture-design-proposal
companion_of:
  - process-review/process-retrospective-rca-2026-06-20.md
  - process-review/hbc-improvement-proposal-2026-06-20.md
source:
  - "Brainstorming 1 — thiết kế 3 trục (First Principles → SCAMPER → Cross-Pollination)"
  - "Brainstorming 2 — chi tiết khung trục B (Morphological Analysis → Role Playing) + bmad-technical-research"
session_log:
  - _bmad-output/brainstorming/brainstorming-session-2026-06-21-010339.md
  - _bmad-output/brainstorming/brainstorming-session-2026-06-21-022343.md
  - _bmad-output/research/technical-d14-claude-design-ux-research-2026-06-21.md
date: "2026-06-21"
updated: "2026-06-21 (sau brainstorm 2 — khung trục B chi tiết + nguyên tắc nền)"
status: "draft — trục B (cấu trúc, §10) sẵn sàng code; trục A (enforcement) chưa kiểm chứng, cần spike (§8)"
owner: "HanhNT2 (HBC maintainer)"
relationship_to_proposal: "Tái cấu trúc proposal ~145 quyết định thành 1 kernel + 3 trục; phần lớn item co/gộp, không bỏ bằng chứng."
---

# Đề xuất Kiến trúc — HBC Build-Graph Redesign

> **Tài liệu này là gì:** kết quả hội tụ của **2 phiên brainstorming có kỷ luật** trên bộ `process-review` (brainstorm-1: thiết kế 3 trục; brainstorm-2: chi tiết khung trục B + bmad-technical-research). Nó KHÔNG thay thế proposal gốc — nó **tái cấu trúc** ~145 quyết định rời rạc đó thành *một ý lõi (build-graph kernel) + một mô hình trách nhiệm 3 trục*, và 2 nguyên tắc nền (§1b). Mọi quyết định đều truy về gốc RCA.
>
> **Trạng thái:** thiết kế đã tự-nhất-quán. **Ưu tiên thực thi: bổ sung khung (trục B) trước** (cấu trúc, không cần kernel — §10); **enforcement bằng máy (trục A) + spike kernel ở backlog** (§8). Kernel vẫn là *giả thuyết chưa kiểm chứng* (F-3/F-4) — không build phần enforcement trước khi spike.

---

## 1. Tóm tắt điều hành

**Một câu:** Cả 5 lỗ hổng lớn của HBC + phần lớn item trong proposal quy về **một thứ còn thiếu — một đồ thị phụ thuộc máy-đọc-được, có trạng thái built/stale/missing**. Có nó rồi thì drift, blast-radius, staleness, re-baseline, test-selection, status, acceptance đều là *truy vấn trên cùng một nền*, không phải các engine/gate rời.

**Mô hình trách nhiệm 3 trục** (giải đồng thời 2 bệnh của case: *rubber-stamp gate* và *hallucination*):

| Trục | Là gì | AI QUYẾT |
|---|---|---|
| **A — Consistency mechanics** | build-graph kernel (đồ thị + reconcile + gate) | **MÁY** quyết FACTS (deterministic, sàn cứng) |
| **B — Framework structure** | tầng/node/pha (V-Model) | (định nghĩa node-set per-feature) |
| **C — Elicitation discipline** | mọi bước sinh doc = câu hỏi+suggest | **USER** quyết JUDGMENT (quyết-định-miền) |

**LLM bị đẩy ra khỏi CẢ HAI chỗ nguy hiểm:** không tự-chấm gate (trục A chặn), không tự-quyết miền (trục C chặn). LLM chỉ *trình option + bằng chứng + làm việc cơ học + thực thi lựa chọn của user*.

**Hệ quả de-ceremony (ngược cảnh báo THÊM:BỎ 25:1 của proposal):** đây không phải thêm tầng — đây là thêm *một nền* để **xóa logic trùng lặp** rải rác trong task-breakdown / test-execution / acceptance / status.

---

## 1b. Hai nguyên tắc nền (steer maintainer — brainstorm 2)

Hai ràng buộc này chi phối MỌI quyết định bên dưới; vi phạm chúng là sai hướng:

1. **HBC = framework ĐẦY ĐỦ & TỔNG QUÁT.** Odoo (dự án OPMS / `resource-plan-billable`) **chỉ là dự án thực hành**, không phải đối tượng tối ưu. → Mọi skill phải chỉn chu mức tối thiểu (full anatomy). **KHÔNG cắt tầng/skill bằng lý do "Odoo không cần"**; per-feature trimming là việc của applicability-catalog, không hardcode trong thiết kế tầng.
2. **KHÔNG hardcode framework cụ thể vào core.** Mọi logic *phụ-thuộc-framework* = **adapter cắm được qua registry/config** (pattern `design_handoffs`/`creative_tools` của bmad-ux). Core agnostic, ship vài adapter tham chiếu; Odoo (hay Django/Prisma/…) là **entry override trong `_bmad/custom/`**, KHÔNG vào source HBC. Áp cho cả họ reconcile machine-floor (xem §3.2).

> ⚠️ Các phần viết trước brainstorm-2 (đặc biệt §4.1 cũ) có *thiên lệch Odoo* — đã sửa bên dưới theo 2 nguyên tắc này.

---

## 2. Bài toán (nhắc gốc RCA)

Nguyên nhân gốc (RCA `resource-plan-billable`): *domain model bị "gate PASSED" trước khi được kiểm chứng; khi model đổi (U-turn v2.0), thay đổi lan truyền bằng viết-lại-thủ-công thay vì cascade/freeze; code không tái sinh → doc/code/matrix/test phân kỳ.*

Biểu hiện cụ thể (regression fixture của mọi cải tiến):
- task-breakdown kẹt v1.8 trong khi D-19 đã v2.3 (không ai re-derive)
- matrix thiếu REQ-040/041/042, `code_ref` trống nhưng gate khai "39/39"
- code 100% model cũ (`resource.plan.state`), 0 dòng request/snapshot; 146 test khóa model cũ
- gate PASSED xuyên churn + manual-pass sau evaluator crash
- 65 spec-ref leak trong code/test

---

## 3. Trục A — Build-Graph Kernel (cơ chế nhất quán)

### 3.1 Ý lõi: HBC như một BUILD GRAPH (mô hình Make/Bazel)

- **Matrix-graph = dependency DAG.** Mỗi artifact (D-02→D-06→D-19→D-27→code→test) là một *target*; input = artifact thượng nguồn + ground-truth (code/DB thật).
- **Matrix = view dẫn-xuất**, KHÔNG file viết tay — scan các artifact để dựng lại mỗi lần. → *khuyết-matrix trở nên bất khả thi* (bịt trực tiếp gốc của case).
- **Edge = `sources:` frontmatter (nâng cấp cái đã có) + content-hash.** HBC đã có mầm (task-breakdown ghi `sources: D-02 v1.8 / D-19 v1.3`); chỉ cần thay version-string bằng hash + bắt mọi artifact khai.
- **Stale = input đổi hash kể từ lần "build" (validate/freeze) gần nhất.** → "frozen" hết là nhãn cảm tính, thành *ảnh chụp hash* kiểm được bằng máy.
- **Re-baseline = chạy `make`:** đổi 1 node → chỉ node phụ thuộc transitively bị dirty cần làm lại. **Blast-radius = dirty-set = miễn phí** → engine `hbc-rebaseline` riêng (🟡 ST-2 "nhiều tuần") **biến mất**.
- **Ground-truth (code/DB thật) = node hạng-nhất** trong DAG, có hash riêng; mọi artifact model có cạnh trỏ tới → grounding thành *topology*, không thể "quên".

> Giải nguyên văn case: "code không tái sinh" = *build chưa chạy lại sau khi D-19 đổi hash*. Make đánh code = STALE + rebuild đúng phần dirty thay vì viết-lại-thủ-công toàn bộ.

### 3.2 Reconcile-rule — ruột của kernel (tôn validator 3-tầng HBC)

`reconcile(artifact, ground_truth)` là MỘT nguyên thủy dùng lại ở mọi seam, gồm 2 lớp tách bạch:

```
reconcile(A, B):
  ① MACHINE FLOOR (Python, deterministic): parse A, parse B, set-diff
        → facts {missing_in_B, missing_in_A, mismatched}        ← sàn cứng của gate
  ② SEMANTIC CEILING (LLM, adversarial): "đối ứng này CÓ Ý NGHĨA không?"
        BẮT BUỘC trích facts ở ① làm bằng chứng (ID/count) — B6-1/B6-2
  OUTPUT: green | red(machine fail) | contested(LLM bất đồng)
```

**Machine floor — các seam** (phần "đọc framework thật" qua **extraction-adapter**, không hardcode — xem nguyên tắc 2):

| Seam | Machine floor | Adapter (framework-specific) | Semantic ceiling |
|---|---|---|---|
| D-19 ↔ DB/code | entity/field/relation set-diff | **entity-extraction** (Odoo `_name`/fields · Django models · Prisma schema…) | tên-khác-cùng-concept? denorm cố ý? |
| code ↔ D-19 | code không chứa field D-19 đã bỏ; field D-19 phải có trong code | (cùng entity-extraction adapter) | hành vi field đúng intent? |
| behavioral ↔ code | (xem §4.2 — biến thành structural qua test) | (test-runner/coverage adapter) | — |
| token ↔ code-style | token-value set-diff | **style-target** (Tailwind · SCSS-var · CSS-var) | — |
| UI ↔ mockup | structural/visual diff | **component-extraction + visual-harness** | — |

> **NGUYÊN TẮC ADAPTER (từ brainstorm-2):** tầng machine-floor *phải* biết "đọc framework thật thế nào" — toàn bộ phần đó là **một họ adapter cùng pattern registry**, core ship reference adapter (vd CSS-vars), framework khác là override. Đây là cách giữ kernel framework-agnostic.

> **META-NGUYÊN-TẮC (áp cho MỌI reconcile-rule):** *Ưu tiên biến seam semantic → structural bằng test/artifact sinh-ra; chỉ rơi về LLM-adversarial + CONTESTED ở chỗ KHÔNG thể chuyển được.* Đây là cách HBC giữ "machine-verified, không LLM tự chấm" mà vẫn chạm tầng ý nghĩa.

### 3.3 Gate = `/verify` — `make` 2 tầng

```
/verify (gate phase N):
  ① scan → dựng matrix → dirty-set → reconcile mọi required-node của phase
  ② node verdict: built-fresh-green | stale | missing | red(machine) | contested(LLM)
  ③ COMPOSITE (two-stage AND):
     TẦNG MÁY  (trục A, deterministic, KHÔNG human-override):
        mọi required-node green-fresh; red/missing/stale → FAILED; tool crash → BLOCKED
     TẦNG NGƯỜI (trục C, design-phase P1/P2):
        máy-green RỒI → user sign-off quyết-định-miền
  PASSED = máy-green AND (user-sign-off nếu design-phase)
```

Ba quyết định chốt:
1. **Two-stage AND** — máy gác *facts*, người gác *judgment*, không bên nào override bên kia. Máy-red thì sign-off không cứu (chống lenient/manual-pass); máy-green nhưng design-phase vẫn cần người (chống "gate tự tuyên done"). Gate-report tách 2 mục → dấu vết kiểm sạch, diệt G5.
2. **crash / judgment-vắng / CONTESTED → BLOCKED, không bao giờ auto-pass.** Headless design-phase chỉ đạt "judgment-pending". CONTESTED → hỏi user (interactive) / BLOCKED (headless). Diệt manual-pass-sau-crash của case.
3. **Số liệu do máy tính** (QW-4/B6-2) — LLM chỉ narrate, không khai count.

---

## 4. Trục B — Framework Structure (khung/tầng)

> Build-graph (trục A) giữ artifact nhất quán nhưng KHÔNG trả lời "HBC đáng lẽ có tầng gì". Đây là câu hỏi độc lập.

### 4.1 Tiêu chí lọc tầng

**Một tầng thiết kế chỉ "đáng có" nếu nó bắt được một QUYẾT ĐỊNH mà nếu thiếu nó, quyết định đó vẫn bị ra — ngầm, trong lúc code.** Tiêu chí này lọc Phần E gốc.

> **⚠️ SỬA bias Odoo (brainstorm-2):** bảng cũ demote Architecture→"sketch nhẹ" và UX→"N/A" *vì Odoo*. Sai theo nguyên tắc 1 (framework đầy đủ). Đã sửa: **Architecture (D-08) và UX (D-14) là skill ĐẦY ĐỦ**; applicability-catalog quyết áp-dụng/độ-sâu per-feature (một feature Odoo có thể đánh optional qua catalog) — KHÔNG hardcode N/A.

| Tầng ứng viên | Verdict | Lý do |
|---|---|---|
| **Behavioral-Design (D-17)** | 🆕 **Skill mới (conditional theo facet)** | Gốc RCA: logic phi-CRUD (sync-timing/hash/in-flight) bị quyết lúc code. D-19(data)+D-27(test) kẹp 2 bên, giữa trống. |
| **Architecture (D-08)** | 🆕 **Skill mới ĐẦY ĐỦ** *(sửa: không còn "sketch vì Odoo")* | Bắt quyết định component/layer/integration/NFR. Áp-dụng/độ-sâu do catalog quyết per-feature, không hardcode. |
| **UX (D-14)** | 🆕 **Skill mới ĐẦY ĐỦ** *(sửa: không còn "N/A vì Odoo")* | Bắt quyết định screen/component/state/visual. Tích hợp Claude Design (xem §4.6). Applicability theo facet `has-ui`. |
| Use-case (D-04/05) | 🔗 gộp D-06 | D-06 đã phủ actor/main/alt/exception nếu làm path-coverage đúng. |
| D-01 overview | 🔗 header D-02 | goal/scope/context neo feasibility, không cần doc riêng. |

### 4.2 Hai "tầng mới" đều tan vào kernel

- **Model-validation checkpoint (P1)** = `reconcile(model-conceptual-draft, ground-truth)` chạy *sớm*, ở P1, trên bản nháp. Cùng primitive, khác thời điểm. Là "điểm bắt sai rẻ nhất" của gap #1. **Greenfield-adaptive (brainstorm-2):** brownfield → reconcile vs code/DB thật; **greenfield (chưa có code) → ground-truth tạm = D-06 flow + example-mapping với stakeholder** (kiểm model vs nghiệp vụ thật). Hình dạng: gate-item P1 + bước trong `hbc-agent-ba`; reconcile-máy gắn sau (backlog).
- **Behavioral-Design (D-17)** = SINH test → test là máy-kiểm. Mỗi element đẻ ≥1 test; reconcile(behavioral↔code) = mọi element-ID có test xanh + sanity. Đóng V-pairing behavioral↔unit; *tự biện minh* (nguồn sinh test); feed thẳng D-27.
  - **4 content-block (conditional theo facet):** state-transition table · decision-table · invariant list · **sequence/interaction block** (timing/ordering liên-entity — đúng chỗ allocation case chết). KHÔNG pseudocode.
  - **element-ID ổn định** (ST-01/DR-03/INV-02/SEQ-04) → D-27 test-case tham chiếu ID → coverage. Đây là link machine behavioral→test→code.
  - **Granularity:** 1 doc/feature, section per complex-REQ. **D-27 dẫn xuất per-REQ, union theo nguồn** (xem §11.2): behavioral-test từ D-17 (nếu complex) + data-test từ D-19 (EP/BVA) + flow-test từ D-06. Behavioral đặt sau D-19, trước D-27.
  - **Trigger:** KHÔNG tự-phán — skill HỎI user (facet phi-CRUD: state/invariant/timing/algorithm/concurrency làm *gợi ý*, trục C).

> Kết luận: HBC không cần engine rời nào. Chỉ cần *primitive reconcile + áp ở đúng các seam/thời-điểm* + định nghĩa node-set.

### 4.3 Lifecycle tái thiết (1 workflow hoàn thiện)

```
NỀN (trục A, luôn bật): sources:+hash · matrix=view scan · reconcile mọi seam ·
   gate=/verify(build đỏ/xanh) · stale theo hash · blast-radius=traversal · node-set=applicability catalog

P0 Project-Init (shared): D-12 · D-03(seed) · 🆕 integration-map (inventory ground-truth read-only, KHÁC D-08 — xem §11.3) · 🆕 applicability-catalog

P1 Analysis (BA): Feasibility(đọc source+fw) → D-02(🔗header=overview) → D-06(✏️BPMN swimlane+path-ID;🔗use-case)
   → D-03 → 🆕★ Model-validation checkpoint (brownfield: reconcile vs code/DB thật · greenfield: vs D-06+example-mapping)
   Gate P1: +adversarial+edge-case(D-02,D-06); item "model đã kiểm chứng"

P2 Design: 🆕 Architecture D-08(skill đầy đủ) → D-19(✏️3-tier ASK-gate; reconcile vs DB)
   → 🆕 Behavioral-Design D-17(điều kiện phi-CRUD, TRƯỚC code) → 🆕 UX D-14(facet has-ui; Claude Design optional §4.6)
   → D-26(✏️technique-per-scope) → D-27(✏️spec-based, derive từ D-17, ground D-19, sanity) → IR(✏️matrix-complete+MODEL_DRIFT+behavioral)
   Gate P2: user sign-off; reconcile clean

P3 Impl (DEV): Task-breakdown(✏️vertical-slice+INVEST/SPIDR; input D-06 path+AC+behavioral+code-reality; derive từ dirty-set)
   → Implement TDD(✏️reconcile code↔D-19↔behavioral; no spec-ref; sanity)  Gate P3: reconcile clean; coverage cần-không-đủ

P4 Test (TST): Test-exec(🆕test-impact: chỉ test dirty) → Acceptance(✏️đọc graph-state, không tin chuỗi matrix)

V-pairing: requirement↔acceptance · architecture↔integration-test · behavioral↔unit · D-27↔code
Cờ điều kiện: maturity(exploratory|stable) · facet→node-set (has-* ) · facet phi-CRUD→behavioral-design
```

### 4.4 Maturity sống ở trục B, KHÔNG ở trục A

`maturity=exploratory` **nới REQUIRED-NODE-SET** (ít node bắt buộc hơn + dung thứ downstream-stale) qua applicability-catalog — NHƯNG luật verdict (reconcile-red → FAIL) **bất biến**. Vì cấu trúc vậy, maturity *không có đường chạm sàn correctness* → không thể đẻ false-green. Giải A7 (over-gate model động) mà không mở lại cửa hậu lenient.

**Maturity còn nới ASK-volume (brainstorm-2, chống elicitation-fatigue):** exploratory → chỉ ASK quyết-định-miền cốt lõi + default phần còn lại; stable → ASK đầy đủ. Cộng batch câu hỏi theo lô. Đây là van chống đúng rủi ro *gate-fatigue → bypass* mà trục C (mọi-bước-đều-HỎI) có thể tạo ra nếu không tiết chế.

### 4.5 Applicability-catalog — hình dạng chi tiết (brainstorm-2)

Catalog *là* "khung": nó định nghĩa bộ node + per-feature node-set, và là *schema* để build-graph tính missing/dirty.

| Trục | Chốt |
|---|---|
| **Form** | YAML canonical `hbc-shared/references/deliverable-catalog.yaml` + instance per-feature |
| **Entry** | `id · name · scope(shared/per-feature/dual) · phase · owner-skill · default-applicability · applicability-rule · reconcile-seam + ground-truth · v-pair` (hook trục A/V-pair khai sẵn dù chưa enforce) |
| **Chọn node-set** | suy default từ rule+facet → **USER xác nhận/override** (trục C) |
| **Giá trị** | required / optional / N-A (conditional resolve về 1 trong 3; maturity = modifier) |
| **Taxonomy** | **facet-based** (`has-state-machine? has-cross-entity-sync? has-invariant? has-integration? has-ui? has-migration?`) — **cùng bộ facet vừa lái applicability-rule vừa LÀ trigger Behavioral-Design** |
| **Hook** | (1) selection lúc feature-start (cần ngay) · (2) gate-enforce (backlog, khai hook sẵn) |

### 4.6 UX (D-14) + tích hợp Claude Design (brainstorm-2, sau bmad-technical-research)

> **Research:** *Claude Design* là sản phẩm thật (Anthropic 04/2026; update 06/2026 có `/design-sync` 2 chiều design↔code + import design-system từ repo) nhưng **chỉ chạy React/Next — KHÔNG Odoo (QWeb server-rendered)**. *DESIGN.md* (Google Labs, open) = token-contract portable. *bmad-ux* đã có spines DESIGN.md/EXPERIENCE.md + `design_handoffs` registry.

**Ràng buộc cốt lõi: D-14 ↔ Claude Design phải ĐỒNG BỘ (mockup không thành ốc-đảo).** Hình dạng chốt (12 câu):

- **Cấu trúc:** D-14 ≈ EXPERIENCE.md (how-works: screens/components/states/flows, trace REQ+D-06) **+ trỏ DESIGN.md token** (how-looks) bằng `{path.to.token}`. Skill **HBC-native theo concept tài liệu HBLAB (D-xx)**, chỉ *tham chiếu* mô hình bmad-ux — KHÔNG wrap (xem §11.1).
- **Nguồn sự thật:** **D-14 + DESIGN.md = spec-of-record**; Claude Design mockup = realization, THUA khi xung đột ("spines win").
- **3 trụ neo (đừng phát minh lại):** DESIGN.md token-contract (portable) · Claude Design generator + `/design-sync` push/pull (qua Claude Code) · bmad-ux spines. **Claude Design = một entry trong `design_handoffs`**, OPTIONAL (skill ASK "có dùng không?").
- **Đồng bộ:** token↔code-style drift (máy, qua style-target adapter) · UI↔mockup visual-regression(baseline=mockup)+structural · **cascade 2 chiều** (forward: spec đổi→push→re-gen; backward: sửa canvas→pull→D-14 stale→USER cập nhật, spec thắng, không silent).
- **Node:** D-14+DESIGN.md = node đầy đủ; mockup = node downstream (commit vào repo path chuẩn `_bmad-output/features/<f>/ux/`, ref relative-path+id → build-graph thấy).
- **Matrix mở rộng:** REQ→screen→component→token→code→test (giải E2E-PENDING-DESIGN của case).
- **Framework:** spec↔design sync chạy mọi framework (design-system, không phải app-code); design↔code-gen tự động chỉ React/Next → Odoo dùng reconcile HBC. Đúng nguyên tắc 2.
- **Identity:** skill mới `hbc-create-ux`, D-14, menu UX, phase 2-design.

---

## 5. Trục C — Elicitation Discipline (cột sống chống-hallucination)

**Mọi bước sinh tài liệu = một (hoặc nhiều) câu hỏi cho user chọn, kèm đáp án gợi ý. Skill KHÔNG tự-quyết quyết-định-miền.** (Mối lo gốc A5, xuyên suốt proposal.)

Phân vai hoàn chỉnh:
- **MÁY** = facts (đối ứng cấu trúc, count, diff) — deterministic, sàn cứng.
- **USER** = quyết-định-miền (model nào đúng? cần behavioral? denorm cố ý?) qua option+suggest.
- **LLM** = *không quyết, không tự-chấm* — chỉ trình option + bằng chứng + làm việc cơ học + thực thi lựa chọn của user.

---

## 6. Quyết định thiết kế đã chốt — `code_ref` (giải tension cuối)

**Lối (b): `code_ref` dẫn xuất qua `REQ →[D-27 map]→ test-case →[coverage]→ code`.**

- **Code + test SẠCH spec-ref hoàn toàn** — REQ-id chỉ sống ở D-02 (định nghĩa) + D-27 (map REQ→test-case) + matrix dẫn-xuất. Tôn IMP-02 trọn vẹn (xóa cả 29 prod + 36 test leak của case).
- **code_ref KHÔNG THỂ GIẢ** — là code thật sự bị test chạm (coverage), không phải chuỗi gõ tay → diệt "39/39 code_ref giả".
- **REQ thiếu code_ref = tín hiệu thật** (chưa implement / chưa test) → REQ-040/041/042 tự lòi là missing.
- **Dùng lại CÙNG test cho 2 việc:** reconcile(behavioral↔code) + derive code_ref đều chạy trên test+coverage.
- **Contract nhỏ:** D-27 phải ghi test-case-id → test-function/path.
- **Đánh đổi:** matrix-derivation có phần động (chạy test+coverage), không thuần static — nhưng test-impact selection làm incremental; coverage vốn đã cần cho anti-false-green.

---

## 7. Tái cấu trúc proposal gốc (cái gì co/gộp/giữ)

| Item proposal | Số phận dưới mô hình mới |
|---|---|
| 🟡 ST-2 `hbc-rebaseline` engine ("nhiều tuần") | **CO vào kernel** = traversal trên DAG |
| 🟡 ST-1 Model-Spike | **= reconcile chạy sớm ở P1** (không phải engine) |
| 🟢 QW-5/QW-6/B13-1 (matrix/MODEL_DRIFT) | **= reconcile-rule của node**, không phải script rời |
| 🟢 SE-1 (STALE), SE-3 (skill tự ghi matrix), drift-watch | **gộp vào** dirty-set + matrix-as-view |
| 🟢 QW-4 (machine-numbers), IMP-03 (crash=BLOCKED) | **= luật gate `/verify`** |
| Phần E (V-Model) | **2 skill mới** (Architecture D-08 · Behavioral-Design D-17) + **Model-validation = gate-item** (không skill) + **2 fold** (D-01→D-02, use-case→D-06). *(Sửa: Architecture là skill đầy đủ, không "sketch".)* |
| Phần D (UX) | **UX D-14 = skill đầy đủ** + tích hợp Claude Design (§4.6). *(Sửa: không còn "N/A vì Odoo" — applicability theo facet has-ui.)* |
| IMP-02 (no spec-ref) | giải qua `code_ref` lối (b) |
| A5 (ASK-at-domain) | **nâng thành trục C** (thuộc tính phổ quát) + maturity nới ASK-volume |
| (mới) framework-coupling | **nguyên tắc adapter** — không hardcode framework, adapter cắm được (§1b, §3.2) |

→ Net: phần lớn proposal **co/gộp về 1 kernel + 3 trục**, KHÔNG mất bằng chứng. Đây là de-ceremony thật.

---

## 8. BACKLOG — Kiểm chứng kernel (spike)

> **Quyết định sắp xếp (2026-06-21):** ưu tiên **bổ sung khung HBC (trục B)** trước; **spike kernel (trục A) đưa vào backlog**. Lý do: thêm tầng/catalog/fold là cấu trúc, KHÔNG phụ thuộc kernel đã kiểm chứng. Chỉ phần *enforcement bằng máy* (matrix-as-view, gate two-stage, reconcile, code_ref-via-coverage) mới cần kernel → chờ spike này.

**Kỷ luật F-3/F-4: kernel là GIẢ THUYẾT. Spike TRƯỚC khi build phần enforcement.**

**Spike throwaway** (~1 buổi, KHÔNG đụng source HBC production) trên `resource-plan-billable` (repo OPMS):
1. Dựng DAG từ `sources:` frontmatter
2. Tính dirty-set theo version/hash
3. reconcile machine-floor 2 seam dễ (matrix-completeness, MODEL_DRIFT code↔D-19)
4. In report STALE + drift

**Tiêu chí THÀNH CÔNG — spike phải tự động bắt 5/5:**
1. task-breakdown STALE (sources D-19 v1.3 < hiện hành v2.3)
2. matrix thiếu REQ-040/041/042
3. matrix `code_ref` trống
4. MODEL_DRIFT: code thiếu request/snapshot, thừa `resource.plan.state`
5. version-incoherence: D-26/D-27 cite "D-02 v2.2" khi D-02 đã v2.3

→ **5/5 bằng máy = giả thuyết xác nhận.** <5 hoặc phải nhờ LLM phán = kernel chưa đủ, revise trước khi build.

**Câu hỏi rủi-ro-nhất spike trả lời:** `sources:`/matrix/code thật có ĐỦ tín hiệu máy-parse-được để dựng dirty-set + drift mà KHÔNG cần đọc tay không?

**Open items:** (chỉ logistics) path repo OPMS cho spike đã có (`C:\Users\HanhNT2\opms`).

---

## 9. Truy vết về RCA (mỗi quyết định vá lỗ nào)

| Quyết định thiết kế | Vá gap RCA |
|---|---|
| Matrix-as-view (scan) | G4 (matrix khuyết → Impact không chạy) |
| reconcile D-19↔reality ở P1 | G1/G8 (model gate trước khi kiểm chứng) |
| dirty-set + STALE theo hash | G2/G3 (không cascade, code không tái sinh) |
| Gate two-stage + crash=BLOCKED | G5 (tín hiệu done giả, manual-pass) |
| Behavioral-Design sinh test | G6 (test neo model sai) + gốc logic-quyết-lúc-code |
| code_ref qua coverage | G7 (spec-ref leak) + "39/39 giả" |
| Trục C (ASK-at-domain) | mối lo autonomy/hallucination |

---

## 10. Bản đồ thực thi trục B (brainstorm-2) — cấu trúc, KHÔNG cần kernel

> Ưu tiên hiện tại: **bổ sung khung (trục B) trước**, enforcement bằng máy (trục A) ở backlog cùng spike. Phần *cấu trúc/format/ASK-discipline* làm được ngay.

- **B0 — Nền (mọi thứ phụ thuộc):** applicability-catalog (`hbc-shared/references/deliverable-catalog.yaml` + instance per-feature + selection-hook ở project-init/BA) · adapter-registry scaffolding (token→style · entity-extraction · component-extraction; ship reference CSS-vars).
- **B1 — Folds (rẻ, sửa skill có sẵn):** D-01→D-02 header (`hbc-create-requirements`) · use-case+BPMN swimlane+path-ID→D-06 (`hbc-create-business-flow-diagram`).
- **B2 — Skill mới (full anatomy + đăng ký marketplace.json/module-help.csv + catalog entry):** `hbc-create-architecture` (D-08, AR) · `hbc-create-behavioral-design` (D-17, BD) · `hbc-create-ux` (D-14, UX).
- **B3 — Tích hợp:** model-validation checkpoint (`hbc-phase-gate` P1-item + `hbc-agent-ba`, greenfield-adaptive) · maturity gate node-set+ASK-volume · cập nhật 5 agent · D-27-derive-từ-D-17.
- **BACKLOG (trục A, cần spike):** reconcile machine-floor (qua adapter) · matrix-as-view · gate two-stage · code_ref-coverage · visual-regression harness · `/design-sync` wiring.

**Nguyên tắc khi code:** mọi skill full-anatomy · source tiếng Anh (VI chỉ trigger+output) · mọi bước sinh-doc HỎI user (nới theo maturity) · không hardcode framework (adapter cắm được).

---

## 11. Quyết định đã chốt (3 điểm impl, chốt 2026-06-21)

1. **`hbc-create-ux` = skill HBC-native, KHÔNG wrap bmad-ux.** D-14 viết theo **concept tài liệu HBLAB (D-xx convention)** — là một deliverable D-xx nhất quán với phần còn lại của catalog. Chỉ *tham chiếu mô hình* bmad-ux (ý niệm DESIGN.md token-contract + EXPERIENCE-structure + design_handoffs), không gọi lại bmad-ux. → toàn quyền tích hợp build-graph node / trace REQ-D-06 / trục-C / Claude Design theo cách HBC.
2. **D-27 sourcing = per-REQ, union theo nguồn (routing theo facet / D-17-presence).** Mỗi REQ: có D-17 (complex) → behavioral-test từ element D-17 (ST/DR/INV/SEQ); **+ LUÔN** data-test từ D-19 constraint (EP/BVA) + flow-test từ D-06 path. Union, không loại trừ. Rule tường minh trong `hbc-create-test-spec`.
3. **P0 integration-map vs D-08 = tách rõ.** integration-map (P0, shared) = *inventory/registry ground-truth read-only* (model/module hệ thống ĐANG CÓ; project-init refresh). D-08 (P2, per-feature) = *quyết định kiến trúc* + khai "feature chạm model/module nào" = **cạnh trỏ vào integration-map**. Inventory (factual) vs design (decisions) — không trùng nội dung.

> Cả 3 là chi-tiết-triển-khai, không phải mâu thuẫn thiết kế. Trục A/B/C tự-nhất-quán.

<!-- END -->
