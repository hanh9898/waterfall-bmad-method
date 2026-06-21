---
title: "Hồi cứu Quy trình & Phân tích Nguyên nhân gốc — Workflow HBC (OPMS)"
doc_type: process-retrospective-rca
scope: ["tài liệu HBC generate", "quá trình làm việc", "đối chiếu định nghĩa skill HBC"]
feature_in_focus: resource-plan-billable
techniques: ["Value Stream Mapping", "Lean 8 Wastes (knowledge-work)", "Root Cause Analysis (Fishbone + 5 Whys)", "Gap Analysis (as-is vs HBC-intent)"]
date: "2026-06-20"
author: "Architect + 3 luồng điều tra read-only"
status: draft
---

# Hồi cứu Quy trình & Phân tích Nguyên nhân gốc

> **Mục đích:** trả lời câu hỏi của anh — *"vì sao tôi phải viết tài liệu rồi viết lại nhiều lần; tài liệu chưa hoàn thiện; code/test generate ra chưa đúng"* — bằng phương pháp Lean/RCA, đối chiếu với chính định nghĩa của các skill HBC.
> **Phạm vi:** tài liệu HBC generate (D-02/06/19/26/27, matrix, gates, task-breakdown) + quá trình làm việc thực tế + định nghĩa skill HBC.

---

## 0. Tóm tắt điều hành (Executive Summary)

Ba triệu chứng anh nêu là **thật và có bằng chứng định lượng**:

| Triệu chứng | Bằng chứng |
|---|---|
| **Viết lại nhiều lần** | D-02 **13 phiên bản**, D-19 7, D-06 6, D-26 6, D-27 ~8 — tất cả dồn trong **8 ngày** (06-11→06-19). Riêng thiết kế Summary **lật ≥3 lần**. |
| **Tài liệu chưa hoàn thiện** | "Complete"/gate PASSED nhưng còn `TBD` (timeline D-02 §1.3, toàn bộ assignee D-26 §8), `E2E PENDING DESIGN`, mâu thuẫn nội bộ (D-02 §6.2 "per-month" vs NFR-005 "all-or-nothing"), cross-ref lệch version (D-26/D-27 ghi "D-02 v2.2" trong khi D-02 đã v2.3). |
| **Code/test sai** | Code **100% là model CŨ** (lifecycle-on-plan); model v2.3 (Request+Snapshot) **chưa implement dòng nào**. 146 test khóa chặt hành vi cũ. **REQ-040/041/042 không có task, không có dòng matrix.** |

**Một câu chẩn đoán:** *Mô hình miền (domain model) bị coi là đã chốt và được "gate PASSED" **trước khi nó thực sự được kiểm chứng**; khi nó đổi (U-turn ở v2.0), thay đổi được lan truyền bằng **viết-lại-tại-chỗ thủ công toàn bộ tài liệu** thay vì cơ chế cascade/freeze của chính HBC — còn code thì không được tái sinh, khiến tài liệu / code / matrix / test phân kỳ.*

Quan trọng: **công sức không vô ích** — thiết kế v2.3 hiện đã rõ và đã qua adversarial. Vấn đề là **thứ tự (sequencing)**, không phải bản thân việc làm.

---

## 1. Bản đồ dòng giá trị hiện trạng (Current-State VSM)

Dòng artifact HBC và **các vòng rework** đã thực sự xảy ra:

```
Phase 1        Phase 2                         Phase 3                Phase 4
D-02 ──► D-06 ──► D-19 ──► D-26 ──► D-27 ──► task-breakdown ──► CODE+TEST ──► (gates)
 │                                                  │              │
 │   ◄──────────── VÒNG REWORK #1..N ──────────────┘              │
 │   (model lõi đổi v1.x→2.0→2.1→2.2→2.3 → cascade lại TẤT CẢ)    │
 │                                                                 │
 └─ U-TURN v2.0 (sau khi đã code xong 87 test) ───────────────────┘
                                                   ▲
                          CODE đứng yên ở model CŨ │ (không tái sinh)
                                                   └── matrix đứng ở REQ-039 (thiếu 040-042)
```

**Phân loại hoạt động (VA / NNVA / NVA):**

| Hoạt động | Loại | Ghi chú |
|---|---|---|
| Viết D-02..D-27 lần đầu (model cũ) | **NVA (đã vứt)** | Toàn bộ bị đảo ở v2.0 |
| Code + 87 test model cũ + 3 gate PASSED | **NVA (đã vứt)** | Code vẫn là model cũ, sẽ phải viết lại |
| Cascade v2.0→2.1→2.2→2.3 (4+ vòng, ~7 doc/vòng) | **NNVA → NVA** | Cần để chốt model, nhưng lặp lại nhiều lần là lãng phí |
| party-mode + adversarial ×2 | **VA** (chốt được model đúng) | Nhưng đáng lẽ làm **trước** khi sản xuất artifact |
| Update Claude Design (mockup ×N) | **NNVA** | Cũng chạy theo từng vòng — cùng bệnh |
| **Thiết kế v2.3 cuối cùng** | **VA** | Sản phẩm có giá trị còn lại |

→ **Phần lớn thời gian rơi vào NVA/rework**: vẽ-rồi-xóa một stack hoàn chỉnh vì model lõi chưa đứng yên.

---

## 2. Phân tích lãng phí (Lean 8 Wastes — bản knowledge-work)

| Lãng phí | Biểu hiện trong dự án | Mức |
|---|---|---|
| **Defects / Rework** | 13 phiên bản D-02; cascade chạy lại ≥4 vòng (~7 doc mỗi vòng ≈ 28+ lượt sửa); Summary lật ≥3 lần. **Lãng phí chủ đạo.** | 🔴 Rất cao |
| **Overproduction** | Sản xuất **đầy đủ + versioned + gated + push Claude Design + 87 test** cho model rồi bị đảo. D-27 chi tiết tới 107 TC, mockup React 54KB — đánh bóng trước khi đóng băng. | 🔴 Cao |
| **Relearning (học lại)** | Cùng quyết định bị tái-tranh-luận: v1.9 chốt "plan read-only sau Submit / L2 không reject" → v2.0 đảo "plan stateless" → v2.2 vá lại. Summary 3 vòng. | 🔴 Cao |
| **Waiting / Handoff loops** | Nhiều vòng review (party-mode, adversarial ×2), mỗi vòng đẻ thêm finding → thêm edit. | 🟠 Trung bình |
| **Over-processing** | Nghi lễ traceability/gate/versioning áp lên artifact đang biến động; **65 chú thích spec-ref nhúng trong code** (vi phạm rule). | 🟠 Trung bình |
| **Partially-done work (tồn kho WIP)** | Doc ở v2.3 nhưng code ở model cũ; task-breakdown đứng ở v1.8; matrix thiếu 040-042 + trống `code_ref`. Nhiều thứ dở dang không hội tụ. | 🔴 Cao |
| **Task-switching** | Nhảy doc↔doc↔mockup↔code↔DB-discussion liên tục. | 🟡 Thấp-TB |
| **Không tận dụng đúng công cụ** | **Bỏ qua engine cascade `hbc-traceability impact`** của chính HBC, làm tay thay vì để hệ thống lan truyền. | 🟠 Trung bình |

---

## 3. Phân tích nguyên nhân gốc (RCA)

### 3.1 Fishbone (Ishikawa) — nhóm nguyên nhân

```
                 Method/Quy trình            Tooling (HBC skills)
                 ───────────────             ────────────────────
   Sản xuất artifact trước khi      Gate validate CẤU TRÚC/traceability,
   đóng băng model lõi          \   KHÔNG validate tính-đúng-của-model
   Đánh bóng/versioning sớm      \  Gate "PASSED xuyên churn" → tín hiệu giả
   Không spike/prototype model    \ Evaluator crash → manual pass
                                   \  HBC KHÔNG có gate cho "đổi model lõi
                                    \ sau Phase 3"; shared D-19 chỉ ADVISORY
        ────────────────────────────●────────────────────────────►  "Làm việc
                                    /   KHÔNG hiệu quả"
   Requirement/business-flow      /  Matrix đứng ở model cũ (thiếu 040-042)
   ban đầu SAI về gốc            /   Code/test không tái sinh → phân kỳ
   Phát hiện muộn (sau code)    /    Doc cross-ref lệch version
                               /     Spec-ref nhúng trong code
                 Inputs/Yêu cầu             Artifacts/Outputs
```

### 3.2 Năm-Tại-Sao (5 Whys) — cho triệu chứng "phải viết tài liệu nhiều lần"

1. **Vì sao viết lại nhiều lần?** → Vì model lõi đổi (v2.0 Request+Snapshot đảo "lifecycle-on-plan").
2. **Vì sao model đổi muộn?** → Vì requirement/business-flow gốc sai, nhưng chỉ phát hiện **sau khi đã code + 87 test + 3 gate PASSED**.
3. **Vì sao phát hiện muộn?** → Vì model **chưa từng được kiểm chứng rẻ** (spike/prototype/review miền) trước khi sản xuất cả stack tài liệu + gate.
4. **Vì sao sản xuất cả stack trước?** → Vì đi tuần tự theo HBC phase-by-phase và **gate báo "PASSED" tạo cảm giác đã chốt** (niềm tin sai).
5. **Vì sao gate tạo niềm tin sai?** → Vì gate kiểm **cấu trúc/sự hiện diện traceability, không kiểm tính-đúng-của-domain-model**; lại còn **manual-pass sau khi script crash** và **không chạy lại** sau U-turn v2.0.

→ **NGUYÊN NHÂN GỐC:** *Domain model được "đóng dấu PASSED" trước khi được kiểm chứng; cơ chế lan truyền thay đổi của HBC (Impact cascade + FREEZE-CHECK) không được dùng — thay bằng viết-lại-tại-chỗ thủ công; và code không được tái sinh từ model mới.*

---

## 4. Adversarial review + Gap Analysis (process-as-done vs HBC-intent)

Đối chiếu **cách HBC thiết kế để vận hành** với **cách dự án thực sự chạy**:

| # | HBC intent (to-be) | Thực tế (as-is) | Gap / Hệ quả |
|---|---|---|---|
| G1 | **Design-first**: chốt thiết kế trước, gate chặn đi tiếp khi predecessor chưa đóng (B2 entry-gate, task-breakdown HALT) | Model lõi sai được gate PASSED qua nhiều version; gate **không bắt** sai model, chỉ bắt cấu trúc | 🔴 Xây cả stack trên nền chưa kiểm chứng |
| G2 | Thay đổi yêu cầu → **cascade qua `hbc-traceability impact`** (READ + SUGGEST, owning-skill `update`, freeze-check) | Lan truyền bằng **viết-lại-tại-chỗ thủ công** toàn bộ doc, **không dùng Impact**; matrix không cập nhật | 🔴 N lượt rewrite tay = rework; bỏ phí engine có sẵn |
| G3 | **FREEZE-CHECK**: artifact done/PASSED → **fork task mới**, không sửa tại chỗ | Code Phase 3 (frozen) để nguyên model cũ; doc lại sửa tại chỗ | 🔴 Doc ↔ code phân kỳ; "done" code sai model |
| G4 | **Matrix = đồ thị tác động sống**, nguồn sự thật | Matrix đứng ở model cũ (REQ-024→`resource_plan.state`), **thiếu REQ-040/041/042**, `code_ref` trống | 🔴 Impact engine không chạy được vì đồ thị khuyết |
| G5 | Gate PASSES **chỉ khi mọi required item pass**; re-validate khi thay đổi | Gate "giữ PASSED xuyên churn"; P2 trích "39 REQ/82 TC", P3 "39/39 code_ref"; **manual-pass sau evaluator crash**; không chạy lại cho v2.x | 🔴 Tín hiệu "done" giả |
| G6 | Test design ở Phase 2 + TDD RED→GREEN; mỗi REQ-facet có TC | 146 test viết cho model cũ, khóa hành vi cũ; **0 test cho request/snapshot** | 🔴 Bộ test neo vào model sai |
| G7 | **Không spec-ref trong code** (rule dự án) | **65 leak** (29 production, 36 test): REQ-/TC-/NFR- | 🟠 Vi phạm rule + nhiễu khi tái sinh |
| G8 | Phase 0: **baseline domain model ổn định** trước mọi feature; shared D-19 "không overwrite" | Model lõi (= bản chất baseline) sai & đổi sau Phase 3 — **HBC không có path gated cho tình huống này** (shared D-19 chỉ ADVISORY) | 🔴 Đây là lỗ hổng method-fit lớn nhất |

> **Phát hiện method-fit then chốt (từ điều tra skill HBC):** HBC tối ưu cho **thay đổi nhỏ, REQ-shaped, trên một baseline ổn định**. Nó **không có cơ chế gate/cascade cho việc đổi domain model lõi sau Phase 3** — đúng kịch bản đã xảy ra. Một phần "kém hiệu quả" là **dùng method tối-ưu-cho-cascade vào tình huống nền-móng-biến-động**.

---

## 5. Tổng hợp nguyên nhân (ưu tiên)

1. **(Gốc) Đóng băng & gate model trước khi kiểm chứng** → mọi rework downstream. *(G1, 5-Whys)*
2. **Không dùng cơ chế thay đổi của HBC** (Impact cascade + FREEZE-CHECK + matrix sống) → lan truyền thủ công, doc/code/matrix phân kỳ. *(G2,G3,G4)*
3. **Gate là tín hiệu "done" giả** (kiểm cấu trúc, manual-pass, không re-validate). *(G5)*
4. **Method-fit gap**: HBC không gate cho đổi-model-lõi-sau-Phase-3. *(G8)*
5. **Đánh bóng sớm** (versioning/test chi tiết/push design) trên artifact biến động = overproduction. *(Waste)*
6. **Vệ sinh artifact**: cross-ref lệch version, mâu thuẫn nội bộ, TBD tồn đọng, spec-ref leak. *(G7 + §0)*

---

## 6. Khuyến nghị + Kế hoạch hành động

### 6.1 Đổi cách làm (phòng tái diễn)

| # | Hành động | Giải lãng phí | Ưu tiên |
|---|---|---|---|
| R1 | **Đóng băng model lõi TRƯỚC trong 1 ADR duy nhất**, kiểm chứng bằng **spike/prototype mỏng** (hoặc 1 vòng review miền), KHÔNG sản xuất 7 doc gated trước | Overproduction, Defects | 🔴 Cao |
| R2 | **Không đánh bóng/gate/push-design khi model chưa đứng yên**; giảm nghi lễ trên artifact biến động | Overproduction, Over-processing | 🔴 Cao |
| R3 | Khi đã đóng băng → **cascade MỘT lần** qua `hbc-traceability impact` (đúng cơ chế HBC), không viết-lại-tại-chỗ | Rework | 🔴 Cao |
| R4 | **Gate phải re-validate sau mỗi version-bump lớn**; sửa evaluator crash, **cấm manual-pass im lặng** | Tín hiệu giả | 🟠 TB |
| R5 | Nhận diện **method-fit**: với thay đổi nền-móng → coi là **re-baseline có chủ đích**, không ép vào cascade incremental | Method-fit | 🟠 TB |

### 6.2 Dọn nợ hiện tại của `resource-plan-billable` (đưa về nhất quán)

| # | Hành động | Ưu tiên |
|---|---|---|
| F1 | **Sửa matrix**: thêm REQ-040/041/042, repoint REQ-024 (bỏ `resource_plan.state`), điền `code_ref` thật | 🔴 Cao |
| F2 | **Re-derive task-breakdown từ v2.3** (hiện đứng ở v1.8; thiếu task cho request/snapshot/hash/in-flight) | 🔴 Cao |
| F3 | **Re-implement code theo v2.3** = rewrite cấu trúc (2 model mới + plan stateless + sync-khi-L2 + immutability/hash + partial-unique); **viết lại 146 test** | 🔴 Cao (khối lớn nhất) |
| F4 | **Chạy lại gate 1/2/3 thật** trên v2.3 (không manual-pass) | 🟠 TB |
| F5 | Vá mâu thuẫn/cross-ref: D-02 §6.2 vs NFR-005; D-26/D-27 ghi đúng "D-02 v2.3"; bỏ TBD timeline/assignee hoặc defer có ngày | 🟠 TB |
| F6 | **Gỡ 65 spec-ref** khỏi code/test (29 prod + 36 test) | 🟡 Thấp |

> **Lưu ý sắp xếp:** làm **R1 (đóng băng ADR) trước F2/F3**. Buổi thảo luận DB hôm nay đã lòi thêm quyết định mở (lazy-create, archive policy, hash, **allocation sync timing/risk còn dang dở**) — nghĩa là **model v2.3 CHƯA thực sự đóng băng**. Nếu re-implement bây giờ sẽ lại sinh rework. → Chốt nốt các quyết định mở vào ADR rồi mới F2→F3.

---

## 7. Bài học rút ra (1 dòng)

> **Đóng băng domain model bằng kiểm chứng rẻ (spike/ADR) trước; chỉ cascade MỘT lần qua cơ chế HBC sau; đừng để gate "PASSED" thay cho việc model đã đúng; đừng generate code/test khi spec còn động.**

---

## Phụ lục — Nguồn bằng chứng

- **Churn tài liệu:** Revision History của D-02 (13 ver), D-19 (7), D-06 (6), D-26 (6), D-27 (~8); revision rows lệch thứ tự thời gian.
- **Mâu thuẫn/stale:** D-02 §6.2 vs NFR-005; D-26/D-27 body cite "D-02 v2.2" (frontmatter v2.3); matrix thiếu REQ-040/041/042 & `code_ref` trống; task-breakdown `sources: D-02 v1.8 / D-19 v1.3 / D-27 v1.5`.
- **Gate:** P1 gated 24 REQ khi D-02 mới v1.1; P2 "39 REQ/82 TC"; P3 "18/18 task, 39/39 code_ref, 87 test" — đều trên model cũ; evaluator crash → manual pass.
- **Code vs v2.3:** `resource.plan` có `state` + lifecycle methods + manual sync wizard; KHÔNG có `resource.plan.request`/`request.line`/`active_request_id`/`snapshot_hash`; 146 test khóa model cũ; 0 test model mới; 65 spec-ref leak.
- **HBC intent:** design-first + entry-gate B2 + task-breakdown HALT; Impact = READ+SUGGEST + FREEZE-CHECK (frozen→new task); matrix = đồ thị tác động; **không có path gated cho đổi-model-lõi-sau-Phase-3** (shared D-19 chỉ ADVISORY).
- **Kỹ thuật phân tích (web research):** Lean 7–8 wastes (Lean Enterprise Institute, Boldare); RCA 5-Whys + Fishbone (PRIZ Guru); Gap analysis structure (Hyperproof).
