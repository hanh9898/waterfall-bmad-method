---
title: "HBC Implementation Plan — backlog đầy đủ, break thành task (có traceability tới process-review)"
status: ready-to-implement
date: 2026-06-21
owner: HanhNT2
purpose: "Gom toàn bộ quyết định trong process-review thành 1 plan task-hoá, mỗi task truy về tài liệu nguồn + decision-ID. Là backlog để chuẩn bị implement — KHÔNG phải spec code thẳng (mỗi item L/needs-design phải qua F-3 review độc lập trước)."
---

# HBC Implementation Plan

> Mỗi task có **Source** (tài liệu + decision-ID), **Target** (skill/file), **E·C** (Effort S/M/L · Confidence ready/needs-design — theo F-2), **Dep**, **DoD**. Trạng thái: ✅ xong · ⚠️ một phần · ❌ chưa.

## 0. Index tài liệu nguồn (process-review/)

| Tài liệu | Chứa gì | Namespace ID |
|---|---|---|
| `process-retrospective-rca-2026-06-20.md` | RCA case `resource-plan-billable`: nguyên nhân gốc, 8 gap, khuyến nghị, nợ-case | G1–G8 · R1–R5 · F1–F6 (case-debt) |
| `hbc-improvement-proposal-2026-06-20.md` | ~145 quyết định cho 16 skill + 5 agent; roadmap Đợt 1/2/3; kiểm soát F | A1–A10 · B1-…–B17-… · E1–E8 · UX1–8 · F-1–F-6 · QW/SE/ST |
| `hbc-improvement-elicitation-log.md` | **Câu trả lời nguyên văn** của maintainer (chỉ đạo lớn B1-2, B3-5, B4, UX-1; 4 vòng adversarial) | (đối chiếu A/B/E/UX) |
| `hbc-buildgraph-redesign-2026-06-21.md` | Mô hình 3 trục; **trục A = build-graph kernel**; §10 execution B0–B3; §11 decisions | (trục A kernel) |
| `hbc-improvement-spec-2026-06-21.md` | 19 IMP (phase/work-breakdown/role từ research) + 4 wave | IMP-01–IMP-19 |
| `technical-hbc-phase-workbreakdown-role-research-2026-06-21.md` | Nguồn học thuật cho IMP (Cooper/V-Model/SPIDR/INVEST/Shape Up/SoD…) | (sources) |
| `hbc-dcode-reconcile-2026-06-21.md` | ✅ reconcile D-08→D-09 / D-17→D-16 | (done) |
| `hbc-trucb-build-plan-2026-06-21.md` | ✅ build plan trục B | (done) |

> 🔁 **Revision 2026-06-21b** — vá sau `bmad-review-adversarial-general` (15 finding): + track REMOVE/de-ceremony (§6.5) · + regression-fixture cho metrics (TF.3/TD.0) · + D-code migrate consumer (T1.8) · + bar GO/NO-GO spike định lượng (TA.0) · phân rã T3.13 · exit-criteria + sizing per-đợt (§8) · residual cho mục ⚠️ · env-note + RACI + skill-DoD chung (§0.1).
> 🔁 **Revision 2026-06-21g** — **+§9 Per-skill Implementation Dossier** (checklist ~95 ô B-ID xuyên 21 skill/agent + nền) làm hợp-đồng chống-sót-spec cho implementation per-skill.
> 🔁 **Revision 2026-06-21f** — vá sau **F-3 review độc lập 5 subagent** (đối chiếu từng B-decision ↔ plan): đóng **10 MISSING** (B4-6 mapping-trước-generate · B3-4 scope-confirm · B3-7 code-reconcile · B5-8 brownfield-implement [+T3.18] · B8-3 AS-IS-ground-code · B9-3 in/out-scope-confirm · B11-1 definition-confirm · B16-4 UX-acceptance · B17-2 agent-orchestration · UX-1 hỏi-Claude-Design) + ~14 LỆCH (B5-4/B7-3/B7-5/B7-6 NO-GO-fallback đích-danh · B15-3 khôi-phục-API · B6-3 đã-có · B2-10/B4-2/B9-2/B10-3/B10-4/B11-3/B13-2/E-6…) + **nguyên-tắc "ASK-trước-generate + grounding-code tường-minh-per-skill"** (§0.1).
> 🔁 **Revision 2026-06-21e** — sửa LỆCH ở `hbc-create-requirements` (B1-2): tách lại 3 khái niệm anh chốt — **(1) Feasibility = bước-1 BẮT BUỘC** mọi ý tưởng (early-kill, đọc source+framework) vào T3.1 · **(2) Quick Discovery LUÔN** (chỉ brainstorming optional) · **(3) DSC = Model-Spike → REPOSITION sang đầu Phase 2, soi bản nháp D-19** (B2-6); `discovery_risk` chỉ quyết **độ sâu** spike, KHÔNG quyết có-feasibility-hay-không → **+T3.17 reposition DSC** (rework có kiểm soát vì DSC đã ship). DSC trong §1 chuyển ✅→⚠️.
> 🔁 **Revision 2026-06-21d** — bám lại **câu trả lời elicitation (B-ID)**: + **T2.11 anti-churn (B2-9/B3-10)** [vá RCA #1 "13 version"] · + **T2.12 semantic-review wiring (B2-8/B3-8/B8/B11)** · T2.2 +reconcile-adversarial (B7-4) · T3.3 +severity-confirm (B3-6). Cột **Source** giờ ưu tiên **B-ID** (quyết-định-của-USER) làm nguồn gốc.
> 🔁 **Revision 2026-06-21c** — vá sau `bmad-review-edge-case-hunter` (14 edge-case): **TD.0 kéo lên `T0` prereq (hết deadlock)** · TD.0 snapshot từ **git-ref RCA** · RM pool-exhaustion rule + RM.1 breaking + RM.6 superset-check · TA.0 false-positive corpus + **NO-GO fallback** · T1.8 idempotent · token đo bằng **tiktoken** · headless **assumptions-mode** (không block câu đầu) · bundling liệt-kê skill-không-T3 · exit-criteria định lượng · T2.4 interim (kernel thay) · **+T-REINSTALL** runtime version-check.

---

## 0.1 Quy ước chung (áp cho MỌI task — không lặp lại per-task)

**RACI / driver:** owner = HanhNT2 (Accountable mọi gate-decision). Driver thực thi theo loại:
- *Skill mới / sửa SKILL.md, validator, template* → qua `bmad-workflow-builder` (Build/Edit).
- *Script-only (lint/check/validator)* → trực tiếp + `bmad-workflow-builder` Analyze để soi.
- *Gate/cascade/traceability* → sửa source + chạy `bmad-module-builder` VM.
- *Item Effort=L / needs-design* → **bắt buộc qua F-3 (subagent độc lập)** trước khi merge (TF.4).
- Mỗi PR phải xanh: `pytest` toàn repo · `npm run check:docs` · `validate-module.py src` (0 finding).

**Skill-creation DoD chuẩn (áp cho mọi task "skill mới" — TA.7, và bất kỳ skill phát sinh):** SKILL.md (frontmatter name+description, ≤3000 token) + customize.toml (nếu cần `{workflow.*}`) + assets/template + `scripts/validate-*.py` (structure-only + `hbc_validation` bootstrap + honest verdict + JSON-stdout) + `scripts/tests/test_*.py` (pytest subprocess) + `references/headless-contract.md` + **đăng ký 3 nơi** (marketplace.json · module.yaml · module-help.csv) + **docs song ngữ** (skills-catalog/deliverables-glossary/workflow-map vi+en). *(Bài học phiên này: quên đăng ký = installer drop skill.)*

**Token-budget rule (áp cho mọi task sửa SKILL.md, đặc biệt Effort=L):** SKILL.md ≤ ~3000 token (target ~2000). `hbc-create-requirements` đã chạm trần — các task **T3.1/T3.2/T3.3 (L)** PHẢI carve phần dài sang `references/` (giữ routing-map ở SKILL.md), không nhồi inline. **Đo bằng tiktoken (cl100k) — KHÔNG ước lượng chars×0.24** (tỉ lệ suy từ 1 điểm dữ liệu, không tin được): T-ENV cài `tiktoken` vào dev-deps; DoD mỗi task L = token thật ≤ 3000.

**De-ceremony rule (F-1, bắt buộc):** mỗi task ADD gate/doc/check phải **kèm 1 mục §6.5 REMOVE** (net-ceremony ≤ 0 mỗi đợt). PR thêm ceremony mà không có dòng BỎ tương ứng → reject.

**Env gotcha (Windows, đã cắn phiên này):** `python3` alias **vỡ** → dùng `python` khi chạy local (SKILL.md vẫn ghi `python3` cho consumer Linux/Mac — xem T-ENV); CRLF warnings vô hại (git lưu LF); `tiktoken` không cài → đo token ước lượng. SSH `git.hblab.vn:22` cần VPN.

**Bundling rule (tránh sửa-2-lần):** **T2.1 (A5 autonomy) GỘP VÀO** mỗi lượt rewrite per-skill T3.1–T3.10 — không edit cùng SKILL.md hai lượt (tránh churn token + rework). **Skill KHÔNG có task T3.x → T2.1 áp standalone** (tập tường minh để autonomy không mồ-côi): `hbc-implement` · `hbc-traceability` · `hbc-phase-gate` · `hbc-migrate` · `hbc-check-implementation-readiness` · `hbc-discovery-spike`. Mỗi skill này phải có nhánh ASK-at-domain-decision riêng.

**Tường-minh-per-skill rule (sửa pattern lệch hệ thống từ F-3 review):** hai loại vế sau **KHÔNG được ẩn vào T2.1/T2.8 phủ-chung** — phải là **DoD tường minh trong từng skill**: (1) **"ASK/confirm/elicit TRƯỚC generate"** ở quyết-định-miền cụ thể (chốt scope/facet/flow/path/preference/definition/L-I trước khi sinh artifact); (2) **"grounding vào CODE/DB/hành-vi thật"** cho AS-IS/reality-check (không chỉ PRD/elicit). Lý do: F-3 review thấy các vế này bị "nén mất" khi đóng gói task gộp — đúng mẫu lỗi requirements (Feasibility-bắt-buộc bị gộp thành DSC).

---

## 1. ĐÃ XONG (không task lại — để truy vết)

| Hạng mục | Source | Ghi chú |
|---|---|---|
| ⚠️ ST-1 / A1 Model-Spike = skill `hbc-discovery-spike` (built đầy đủ) | spec IMP-10 · A1 | + validator + 9 test + đăng ký — **NHƯNG đặt LỆCH (Phase-1/conditional/assumptions); reposition → T3.17** (soi D-19, P1→P2) |
| ⚠️ IMP-09 risk-classifier `discovery_risk` + gate **P1-11** | spec IMP-09 | wire D-02/requirements/gate/BA — **NHƯNG `discovery_risk` đang quyết có-chạy-DSC-không (lệch); đổi thành quyết ĐỘ-SÂU + Feasibility-bắt-buộc thay vai gate-sớm → T3.1/T3.17** |
| P1-09 model-validation (gate Phase 1) | A1 · B6-5 | đã có từ trục B |
| E-1 Architecture = **D-09** · E-3 use-case→D-06 · E-5 D-01→D-02 (fold) | E-1/E-3/E-5 | trục B — *(E-5: chốt **fold** D-01 vào header D-02 thay "deliverable D-01 riêng" của proposal; là quyết-định-có-chủ-đích đã review+merge ở trục B, vẫn neo feasibility trong D-02 §Overview)* |
| ⚠️ E-2 Detailed-Design = **D-16 Behavioral** (một phần) · E-8 applicability-**catalog** | E-2/E-8 | catalog có; **residual → T3.12 (E-2 hoàn tất), T3.15 (E-8 per-feature instance + gate-enforce)** |
| ⚠️ D-14 UX skill (Part D phần khung) | UX-1 | design-sync/visual-regression chưa → **residual T3.14** |
| ⚠️ A7/ST-3 maturity flag (frontmatter + catalog) | A7 | gate-ceremony-gating chưa → **residual T3.16** |
| ⚠️ B.8 D-06 BPMN swimlane + path-ID + use-case | B8-1/6 · E-3 | stage-guide đã thêm → **residual T3.11** (đủ all-paths/phantom-flag) |
| D-code reconcile + docs song ngữ | reconcile doc | ✅ |

---

## 2. ĐỢT 1 — Quick Wins (anti-false-green) · ROI cao · KHÔNG cần spike · **ưu tiên #1**
> Vá trực tiếp triệu chứng RCA (gate PASSED model sai · 65 spec-ref · code↔design drift · số liệu giả). Rổ 🟢 "COMMIT NGAY" maintainer đã chốt (proposal §1).

| ID | Task | Source | Target (skill/file) | E·C | Dep | DoD |
|----|------|--------|---------------------|-----|-----|-----|
| **T1.1** | **MODEL_DRIFT** — entity/field trong D-19/D-16 hiện hành phải có trong code; cờ drift | QW-6 · A10 · B5-1/7 | `hbc-implement/scripts/validate-implementation.py` (+ readiness) | M·ready | D-19/D-16 chuẩn | script phát hiện code dùng field không-có-trong-design & ngược lại; pytest; gate P3 đọc verdict |
| **T1.2** | **spec-ref lint** — cấm `REQ-/TC-/NFR-` nhúng code/test | QW-2 · B5-2 · B10-2 | `hbc-implement/scripts/` + `hbc-create-coding-standards` rule | S·ready | — | script đếm leak (mục tiêu 65→0); gate P3 chặn; pytest |
| **T1.3** | **version-coherence** — xref version giữa D-02↔D-06/D-19/D-26/D-27 | QW-1 · A2 · B13-4 | `hbc-shared/lib` + `hbc-phase-gate` | S·ready | — | bắt "D-26 cite D-02 v2.2 khi D-02=v2.3"; JSON-stdout; pytest |
| **T1.4** | **Gate numbers do script tính** (không LLM khai) | QW-4 · B6-2 | `hbc-phase-gate/scripts` | S·ready | T1.5 | mọi metric "X/Y" do script tính trên artifact thật |
| **T1.5** | **Matrix REQ→row coverage** — parse cột, verify `code_ref/test_ref/design_ref` non-empty per REQ + mọi REQ có ≥1 task | QW-5 · A9 · B4-7 · B13-1 | `hbc-traceability` + `hbc-check-implementation-readiness/check-readiness.py` | S·ready | — | "39/39 giả" bị bắt; REQ thiếu row → fail; pytest |
| **T1.6** | **Gate-robust** — evaluator crash→BLOCKED; cấm silent manual-pass; mơ hồ→CONTESTED | QW-3 · B6-6 | `hbc-phase-gate` | S·ready | — | crash không thành PASS; test |
| **T1.7** | **Migrate bug-fix** (5): regex-scope id-only + dry-run diff · re-prefix impl/gates · dirty-guard warn + timestamp-unique · contract↔engine sync · emit `missing_from_matrix` | B14-1..5 | `hbc-migrate` | M·ready | — | từng bug có test; traceability không gãy sau migrate |
| **T1.8** | **D-code migrate cho consumer hiện hữu** — reconcile D-08→D-09/D-17→D-16 là **BREAKING**: artifact/matrix dự án đã-dùng-HBC mang mã cũ. Renumber per-feature artifact + matrix `design_ref`. **IDEMPOTENT**: detect cây đã-reconcile (có D-09/D-16) → skip + cảnh báo, KHÔNG rename hai-lần (tránh lỗi one-time B14-6); xử lý cây MIXED (vừa cũ vừa mới). + Changelog/breaking-note `module.yaml`/README (semver) | reconcile doc · B14-6 | `hbc-migrate` (hoặc one-shot script) + module.yaml | M·ready | — | dry-run diff; **chạy lại an toàn (idempotent)** + xử lý mixed; matrix không gãy; CHANGELOG breaking |
| **T-ENV** | **Chuẩn-hoá script invocation** — SKILL.md ghi `python3 {project-root}/...` (consumer Linux/Mac đúng); thêm note dev Windows dùng `python`; cấm bare `_bmad` path (path-standards); **+ cài `tiktoken` dev-deps** (đo token thật) | env gotcha (§0.1) | tất cả SKILL.md + CONTRIBUTING + package/dev-deps | S·ready | — | path-standards scan clean; tiktoken đo được; note env trong docs/MAINTAINING |
| **T-REINSTALL** | **Runtime version-check** — consumer pull `main` mới nhưng KHÔNG re-install → `.claude/skills/` chạy skill CŨ với mã D mới ở docs → mismatch âm thầm. Thêm check version `module.yaml` (src) vs runtime ở activation; lệch → cảnh báo "re-install" | env gotcha · reconcile | `hbc-setup`/`hbc-shared` activation + docs/MAINTAINING | S·ready | — | runtime cảnh báo khi version src≠installed; hướng dẫn re-install |

> **Exit-criteria Đợt 1 (định lượng, đo trên fixture TD.0 — KHÔNG dùng "cải thiện" mơ hồ):** MODEL_DRIFT bắt **4/4** lỗi-model đã-biết · matrix REQ-không-row = **0** (bắt đủ 040-042) · spec-ref-leak = **0** (từ 65) · gate-false-pass = **0** (từ 3) · version-coherence bắt **100%** xref-lệch đã-biết. Thiếu BẤT KỲ ngưỡng nào → Đợt 1 chưa done.

---

## 3. ĐỢT 2 — Seams (gate/cascade/review/autonomy) · phần lớn cần thiết kế nhẹ

| ID | Task | Source | Target | E·C | Dep | DoD |
|----|------|--------|--------|-----|-----|-----|
| **T2.1** | **A5 autonomy wiring** ⭐ — mọi create/implement skill: phân biệt quyết-định-cơ-học vs miền; quyết-định-miền → HỎI; thiếu dữ kiện → KHÔNG bịa default. **Headless: 2 chế độ** — (a) `--strict` → blocked ở quyết-định-miền đầu tiên; (b) `--assumptions-allowed` (mặc định cho CI) → suy giả-định + **log vào ADR** + tiếp, KHÔNG block câu đầu (tránh CI feature phức tạp đứng ngay) | SE-9 · A5 · B17-1 | tất cả `hbc-create-*` + `hbc-implement` + 5 agent | M·ready | — | mỗi skill có "ASK-at-domain-decision"; headless 2-mode (strict-block / assumptions-log); CI complex không deadlock |
| **T2.2** | **Cascade ENFORCED** — đổi doc có downstream → block "complete"/qua-phase tới khi `hbc-traceability impact` chạy (Impact vẫn READ-only). **+ RECONCILE adversarial** (B7-4): khi reconcile, dùng bằng-chứng-deterministic + lens-độc-lập, KHÔNG tự chấm | **B7-1 · B7-4** · SE-4 | `hbc-traceability` + các create-skill | M·ready | — | không cascade → blocked `untraced_change`; reconcile không tự-chấm |
| **T2.3** | **Matrix completeness + skill tự-ghi-matrix** ở phase mình (design_ref/test_ref/code_ref) + gate verify | SE-3 · A9 · B7-2 | create/implement skills + `hbc-phase-gate` | M·ready | T1.5 | mỗi phase ghi cột của mình; gate bắt khuyết |
| **T2.4** | **STALE version-set + auto-revalidate + drift-watch** ⚠️ **INTERIM** — làm bản version-set nhẹ; **dirty-set thật sẽ do TA.1 (build-graph kernel) thay**. Giữ phạm vi tối thiểu để không rework lớn; nếu spike GO sớm có thể hoãn T2.4 chờ TA.1 | SE-1 · A2/A8 · B7-3 | `hbc-phase-gate` + `hbc-traceability` | M·ready | — | STALE version-set tối thiểu (⚠️ một phần đã có); ghi rõ "sẽ được TA.1 thay" để tránh đầu-tư trùng |
| **T2.5** | **ADR first-class + decision-gate** — chặn "complete"/qua-phase khi còn TBD/ADR-open | SE-2 · A4 · B2-10 | deliverable ADR mới + `hbc-phase-gate` | M·needs-design | — | quyết-định-mở không lọt vào doc "complete" |
| **T2.6** | **QUALITY adversarial + design-phase sign-off** — gate QUALITY = skeptic+acceptance + bằng chứng định lượng; bất đồng→CONTESTED; PASS phase 1/2 cần user-sign-off | SE-5 · B6-1/5 | `hbc-phase-gate` + 5 agent (B17-4) | M·ready | — | gate QUALITY không tự-chấm; sign-off bắt buộc |
| **T2.7** | **Siết waiver/lenient** — waiver cần rationale + KHÔNG miễn item tính-đúng. ⚠️ **B6-3 ĐÃ TỒN TẠI** (entry-gate không bị lenient hạ — `hbc-phase-gate/SKILL.md:71` + test `test_entry_gate_failure_not_downgraded_by_lenient`); task này **CHỈ MỞ RỘNG sang item correctness/model, KHÔNG build lại** lenient-downgrade | SE-6 · **B6-3 (đã-có)** · B6-4 | `hbc-phase-gate` | S·ready | — | waiver không miễn correctness; KHÔNG re-implement phần đã có |
| **T2.8** | **Review BẮT BUỘC** — `bmad-review-adversarial-general` + `bmad-review-edge-case-hunter` trên D-02+D-06 (và D-27) trước gate. **+ availability-check**: 2 skill này thuộc bmm/core; nếu consumer không cài → **fallback**: áp lăng-kính review trực tiếp (như B6 parallel-lens) + ghi rõ "ran inline", KHÔNG block cứng | SE-7 · B1-9 · B8-7 · B3-9 · B6 | `hbc-create-requirements/business-flow/test-spec` + gate | M·ready | — | gate đòi bằng chứng 2 review đã chạy; thiếu skill → fallback có ghi nhận, không gãy |
| **T2.9** | **Anti-false-green sanity** — TC nhạy cảm chứng minh fixture kích hoạt nhánh; assert có cấu trúc. **+ B5-3: RED-evidence VẪN SOFT** (chỉ thêm điều kiện test FAIL-đúng-nhánh-nghiệp-vụ + sanity, KHÔNG biến thành hard-gate). **+ B5-5: batch DỪNG checkpoint khi test PASS-ngay** (xanh-không-qua-RED = dấu hiệu sai) | SE-8 · B3-1 · B5-3 · B5-5 · B5-9 | `hbc-create-test-spec` + `hbc-implement` | M·ready | — | DONE cần sanity; RED-soft giữ nguyên (chỉ FAIL-đúng-nhánh); batch dừng khi xanh-ngay |
| **T2.10** | **Readiness-gate overhaul (B.13 — cổng đã LỖI trong case)** — parse cột matrix · +input task-breakdown · +D-19/MODEL_DRIFT · version-coherence · scope-hoá TC/row chống paste-appendix · fix headless-contract. **+ B13-2: reconcile 3-CHIỀU REQ↔TASK↔current-design** (phát hiện task mồ-côi / REQ-thiếu-task / task-breakdown stale-vs-REQ — đúng nửa-thất-bại của case) | B13-1..6 (**B13-2**) | `hbc-check-implementation-readiness` | M·ready | T1.1/T1.3/T1.5 | seam-gate bắt nửa-thất-bại; reconcile 3-chiều không để task-breakdown lỗi-thời "xanh"; test |
| **T2.11** | **Anti-churn (vá RCA #1 "13 version")** — version-bump **gộp theo PHIÊN** (không bump mỗi sửa nhỏ); đếm churn, **cảnh báo churn-cao → gợi ý "model chưa frozen → cân nhắc maturity=exploratory / chạy [DSC]"**. Recurring ở mọi create-skill | **B2-9 · B3-10** (+ inherited B-x) | `hbc-shared/lib` + tất cả `hbc-create-*` | M·ready | — | bump gộp theo phiên; cảnh-báo khi churn vượt ngưỡng; **giảm metric churn F-6 (13→≤4)**. *(Tính de-ceremony — đối trọng ADD, F-1.)* |
| **T2.12** | **Semantic-review WIRE vào từng skill** (không chỉ gộp reference RM.2) — mỗi create-skill chạy review **lens-độc-lập (skeptic) + USER sign-off khi passed**; record `semanticReview` frontmatter | **B2-8 · B3-8 · B8 · B11** (recurring) | tất cả `hbc-create-*` + `hbc-shared/references/semantic-review-rubric.md` | M·ready | RM.2 | mỗi skill gọi semantic-review chung; `passed` chỉ khi `openFacets` rỗng + sign-off |

> **Exit-criteria Đợt 2:** trên fixture (TD.0): readiness-gate (T2.10) chặn được "nửa-thất-bại" của case; cascade-enforced bắt untraced-change; A5-autonomy: mọi create/implement skill có nhánh ASK-at-domain-decision + headless blocked-reason (audit thủ công 1 lượt). Net-ceremony Đợt 2 ≤ 0 (đối chiếu §6.5).

---

## 4. ĐỢT 3 — Nâng chuẩn per-skill (research-backed) + capability lớn

| ID | Task | Source | Target | E·C | Dep | DoD |
|----|------|--------|--------|-----|-----|-----|
| **T3.1** | **D-02 intake pipeline** (đúng B1-2): **① Feasibility — bước-1 BẮT BUỘC mọi ý tưởng** (đọc source+framework, đánh giá khả thi, **kill sớm** ý tưởng bất khả thi TRƯỚC khi tốn công) → **② Quick Discovery LUÔN** (cả 2 nhánh) → **③ HỎI brainstorming sâu (OPTIONAL)** → Brainstorming (2 câu suggest: chủ đề+output) → **④ Discovery bổ sung bắt buộc** → D-02 → review (T2.8) → gate; + duyệt REQ-list trước generate; + NFR hỏi-số→ASSUMPTION/ADR | **B1-2 (nguyên văn) · B1-1 · B1-5 (Feasibility bắt-buộc) · B1-6 (Quick-Discovery luôn) · B1-3 · B1-10** | `hbc-create-requirements` | L·ready | T2.8 | Feasibility **bắt buộc + sớm + mọi feature** (KHÔNG lẫn/thay bằng DSC); Quick-Discovery luôn; chỉ brainstorming optional; token ≤3000 (carve references) |
| **T3.2** | **D-19 DB 3-tier + ASK-gate mỗi cấp** (Conceptual/Logical/Physical) + ondelete-ask + index-as-proposal + decision-records + ground real schema. **+ B2-5: conceptual đối chiếu REQ + D-06 business-flow** (không chỉ PRD). **+ B2-7: đọc DB-schema/models/migration thật làm ground-truth + LOG MỌI LỆCH**. **+ B2-10: decision-record DB nối ADR-gate** (Dep→T2.5, không để trôi nổi) | B2-1..10 (**B2-Q1 · B2-5 · B2-7 · B2-10**) | `hbc-create-er-diagram` | L·ready | T2.5 | 3 cấp ASK-gate; mỗi entity/field ≥1 REQ; conceptual↔D-06; log-lệch-schema-thật; decision↔ADR |
| **T3.3** | **D-27 technique-map specification-based** — Decision-Table←rule · State-Transition←lifecycle (phủ transition-sai) · EP-BVA←D-19 · Use-Case←D-06 · Example-Mapping; ground test-data vào D-19; **severity critical-path do USER xác nhận (B3-6)**; **+ B3-4: chốt facet + edge in/out-scope per-REQ với user TRƯỚC generate**; **+ B3-7: khi có code → đối chiếu TC vs hành-vi-thật + cảnh báo giả-định-sai** | B3-1..10 (**B3-4 · B3-5 · B3-6 · B3-7**) | `hbc-create-test-spec` | L·ready | — | TC map đúng kỹ-thuật↔nguồn; scope chốt-trước-generate; severity có sign-off; reconcile-vs-code khi có |
| **T3.4** | **task-breakdown vertical-slice + INVEST + SPIDR + Kent Beck test-list** + input (D-06 paths · AC per-REQ · **ADR** · code-reality **phân-loại NEW/CHANGE/đã-có** — B4-2 giữ đủ chiều) + **gate input-đủ trước generate** ("nghi ngờ chưa đủ input"); catalog `references/splitting-patterns.md`; 100%-rule coverage. **+ B4-6: duyệt bảng path/REQ-facet/entity → slice nào TRƯỚC generate** (chống sót slice — đúng lỗi gốc case). **+ B4-5: no-default-override + log lý do tại CHÍNH skill** (không chỉ ở agent T3.8) | B4 (=IMP-03/04/06) **· B4-2 · B4-5 · B4-6** | `hbc-task-breakdown` | M·ready | T1.5 | task = slice dọc; **review bảng-mapping TRƯỚC generate**; input-đủ-check; override-HALT tại skill; mọi REQ↔≥1 task |
| **T3.5** | **D-26 technique-per-scope-area** (link D-27) + risk grounded + no-fabricated-schedule. **+ B9-2: likelihood/impact do USER xác nhận** (LLM chỉ đề xuất). **+ B9-3: chốt in/out-scope với user TRƯỚC generate** (out-of-scope quan trọng ngang in-scope) | B9-1..4 (**B9-2 · B9-3**) | `hbc-create-test-plan` | M·ready | T3.3 | approach kỹ-thuật per scope; không bịa ngày; L/I có confirm; in/out-scope chốt-trước-generate |
| **T3.6** | **D-12 derive-from-real-code + machine-rule→lint** + update-on-convention-change. **+ B10-3: preference KHÔNG tự-default im lặng → trình user xác nhận**. **+ B10-4: D-12 shared đổi → cascade ADVISORY xuống feature đang chạy** (nối T2.2) | B10-1..4 (**B10-3 · B10-4**) | `hbc-create-coding-standards` | M·ready | T1.2 · T2.2 | rule máy-kiểm; deviation flag; preference-confirm; cascade-advisory khi convention đổi |
| **T3.7** | **D-03 DDD ubiquitous-language + cross-doc consistency** (term D-02/D-06/D-19 thiếu glossary→flag; orphan→flag). **+ B11-1: definition ground-source; khi suy-ra → user xác nhận** (chống bịa định-nghĩa). **+ B11-3: đối chiếu cả CODE** (không chỉ D-19) | B11-1..3 (**B11-1 · B11-3**) | `hbc-create-glossary` | M·ready | — | consistency cross-doc; definition-confirm; đối chiếu entity/field **+ code** |
| **T3.8** | **5-agent: ELICIT>auto persona + HALT thật (không chỉ warn) + log override + gọi subagent độc lập review. + B17-2: mỗi agent ĐIỀU PHỐI đúng bước-mới của phase mình** (BA pipeline · Architect spike+DB-3-tier+architecture · QA technique-map+edge-review · Dev MODEL_DRIFT+no-spec-ref+sanity · Tester model-match) — cập nhật MENU/sequence, không để agent chạy luồng cũ khi skill đã nâng cấp | B17-1..4 (**B17-2**) | `hbc-agent-{ba,architect,qa,dev,tester}` | M·ready | T2.1 · (T3.1–T3.4/T3.10/T3.17) | mọi agent HALT-on-unclosed-predecessor; **menu/điều-phối khớp bước mới**; không tự-chấm |
| **T3.9** | **project-init: re-run drift+update + nạp/khởi applicability-catalog + baseline Architecture; confirm classify**. **+ B15-3: brownfield derive baseline D-19 + D-21 (KHI CÓ API)** — N/A do **catalog** quyết, KHÔNG cắt-tầng-sẵn-trong-DoD (nguyên-tắc framework-đầy-đủ). **+ B15-4: confirm cả stack/domain/conventions** (không chỉ classify) | B15-1..4 · E-8 | `hbc-project-init` | M·ready | — | PI dùng catalog; derive D-19 (+D-21 khi có API); confirm stack/domain/conventions |
| **T3.10** | **Phase-4: verify ref thật + MODEL_DRIFT clean + D-27 STALE check** (không tin matrix-string). **+ B16-2: model-match + sanity (anti-false-green) + coverage CẦN-không-đủ** (nối T2.9). **+ B16-4: khi catalog bật Part-D → acceptance THÊM tiêu chí UX↔mockup** (visual/E2E) — `hbc-acceptance-check` sở hữu, dep T3.14/T3.15 | B16-1..4 (**B16-2 · B16-4**) | `hbc-test-execution` + `hbc-acceptance-check` | M·ready | T1.1/T1.5 · T2.9 · (T3.14) | acceptance không ACCEPT model-sai; coverage-không-đủ + sanity; UX↔mockup khi Part-D |
| **T3.11** | **Hoàn tất D-06** — đủ all-paths (happy/alt/exception) + flag phantom-flow + path-ID chuẩn. **+ B8-3: AS-IS phải ground vào CODE/hành-vi-thật** (không chỉ PRD/elicit) + log lệch. **+ B8-4: confirm flow/actor/path với user TRƯỚC generate là gate cứng** (hiện chỉ soft) | B8-2/3/4/5/6 (**B8-3 · B8-4**) | `hbc-create-business-flow-diagram` | S·ready | — | gate bắt thiếu path/ID; AS-IS-ground-code; confirm-trước-generate cứng (⚠️ một phần đã có) |
| **T3.12** | **V-Model gaps còn lại** — E-2 detailed-design hoàn tất · E-4 table-def inline/D-20 · **E-6 deliverable optional cụ thể: security · deployment · data-migration design** (bật khi feature chạm — KHÔNG gói chung "NFR-design") · E-7 v-pair (surface trong template/docs) | E-2/4/6/7 | catalog + create-skills + docs | M·needs-design | — | mỗi design-level khai test-level; 3 nhóm design optional rõ |
| **T3.13a** | **`constitution.md`** — lớp nguyên tắc xuyên-phase bất biến (test-first · language-policy · SoD · handoff-qua-artifact · simplicity-caps) ở Phase 0 | IMP-15 | `hbc-project-init` + catalog | M·ready | T3.9 | shared deliverable; 5 persona tham chiếu |
| **T3.13b** | **Quick-Plan fast-path + bugfix-lane** (theo maturity) — feature trivial/`exploratory` gộp/bỏ gate-question; bugfix-profile deliverable-set nhẹ | IMP-16 | catalog + agents | M·ready | T3.16 | maturity-driven fast-path; bugfix applicability-profile |
| **T3.13c** | **Markers `[NEEDS CLARIFICATION]`** trong template D-xx — van xác định, gate coi marker sót = `pending` | IMP-17 | tất cả `hbc-create-*` template + gate | S·ready | — | marker trong template; gate/semantic-review đọc |
| **T3.13d** | **Đặt-tên shift-left + EARS→ATDD + BDD facet** — docs nêu model-based/incremental shift-left; map EARS→acceptance; BDD cho D-16 | IMP-08 · research | docs + `hbc-acceptance-check`/`hbc-create-behavioral-design` | S·ready | — | doc + ghi-chú 2 skill |
| **T3.13e** | **Cascade-sync = nguyên-tắc load-bearing** — nâng trong docs/constitution: "đổi spec ⇒ regenerate downstream" = thuốc giải SDD-waterfall | IMP-19 | docs + constitution (T3.13a) | S·ready | T3.13a | đoạn nguyên-tắc trong concepts + constitution |
| **T3.13f** | **Lean-flow GUIDANCE** (không build machine) — appetite chốt ở gate BA · circuit-breaker = outcome gate · WIP-limit portfolio · hill-chart reporting | IMP-11/12/13/14 · research | docs + gate-question | M·ready | — | guidance + gate-question; KHÔNG tracking-engine (circuit-breaker outcome thực = TA.8) |
| **T3.14** | **Part D UX — tầng đầy đủ của framework** (KHÔNG hạ vì "Odoo back-office") — design-sync mockup↔D-14↔matrix · component-map↔code↔token · matrix REQ→screen→component→test · UI-acceptance/visual-regression · outside-in ATDD · maturity-gate UX. **+ UX-1 (nguyên văn): HỎI user có dùng Claude Design không (OPTIONAL); nếu CÓ → enforce link D-14↔Claude Design; nếu KHÔNG → D-14 standalone**. **+ UX-6: design-token 1-nguồn (single source) khi dùng Claude Design**. **Applicability per-project qua catalog** (feature không-UI → N/A *bằng catalog*, không phải cắt-tầng — nguyên tắc "framework đầy đủ & tổng quát") | UX-1..8 · nguyên-tắc-nền | `hbc-create-ux` + `hbc-traceability` | L·needs-design | spike UX · T3.15 | đủ tầng UX; **hỏi-user Claude-Design optional + link có-điều-kiện**; token single-source; N/A do catalog |
| **T3.15** | **(residual E-8) Applicability per-feature INSTANCE + gate-enforce** — catalog mới có schema; cần: ghi instance (required/optional/N-A + lý do) ở feature-start + gate kiểm đúng-bộ-đã-chọn | E-8 | catalog + `hbc-project-init`/`hbc-phase-gate` | M·ready | T3.9 | mỗi feature có instance; gate enforce bộ deliverable |
| **T3.16** | **(residual A7/ST-3) Maturity ceremony-gating** — `exploratory` thực-sự nới gate/ASK-volume (không chỉ là flag); correctness-floor INVARIANT | A7 · ST-3 · F-1 | `hbc-phase-gate` + create-skills | M·ready | — | exploratory hạ required→optional + giảm ASK; floor không đổi |
| **T3.17** | **REPOSITION DSC → Model-Spike soi bản nháp D-19** (sửa LỆCH B1-2/B2-6; DSC đã ship → rework có kiểm soát). DSC chuyển từ "Phase-1, sau REQ+BFD, soi assumptions" → **đầu Phase 2, soi bản-nháp-logical-D-19** (đối tượng spike đúng B2-6). **`discovery_risk` đổi vai: quyết ĐỘ SÂU spike, KHÔNG quyết có-chạy-hay-không** (Feasibility ở T3.1 mới là gate sớm bắt-buộc). **Di P1-11 → gate đầu-Phase-2 / readiness** (model-validation trên D-19 trước khi cascade design). Cập nhật: DSC SKILL + applicability + skills-catalog/workflow-map/gate + docs + ranh-giới 3-khái-niệm (Feasibility≠QuickDiscovery≠Model-Spike) | **A1 · B1-4 · B2-6** · reconcile | `hbc-discovery-spike` + `hbc-create-er-diagram` (D-19 draft = spike object) + `hbc-phase-gate` (P1-11→P2-entry) + `hbc-agent-architect` + docs | M·needs-design | T3.1 · T3.2 | DSC soi D-19-draft ở P1→P2 seam; discovery_risk=độ-sâu; P1-11 chuyển đúng chỗ; **breaking → qua T1.8 + CHANGELOG** (DSC/discovery_risk đã ship) |
| **T3.18** | **(MISSING B5-8) Brownfield trong `hbc-implement`** — đọc code hiện có, **phân biệt sửa-vs-tạo (NEW/CHANGE)**, không trùng lặp; GREEN cần field mới → cập nhật D-19 trước (B5-6) | **B5-8 · B5-6** | `hbc-implement` | M·ready | T1.1 | implement brownfield không tạo trùng; phân loại NEW/CHANGE rõ |

> ⚠️ **Ranh giới 3 khái niệm (chống tái-gộp như lỗi cũ):** **Feasibility** (T3.1 · ý-tưởng vs source · BẮT BUỘC · sớm · mọi feature) ≠ **Quick Discovery** (T3.1 · elicit nhu-cầu · LUÔN) ≠ **Model-Spike/DSC** (T3.17 · soi bản-nháp-D-19 vs ground-truth · P1→P2 seam · độ-sâu theo discovery_risk).

---

## 5. TRỤC A — Enforcement bằng máy (build-graph kernel) · **GATED bởi spike**
> Nguồn: `hbc-buildgraph-redesign-2026-06-21.md` (§3 kernel, §10 B0–B3) + spec IMP-01/02/05/07/12. KHÔNG khởi động khi spike chưa PASS (F-4).

| ID | Task | Source | Target | E·C | Dep | DoD |
|----|------|--------|--------|-----|-----|-----|
| **TA.0** | **Spike kernel trên `resource-plan-billable`** (fixture TD.0) — chứng minh build-graph bắt được các lỗi-đã-biết của case | buildgraph §10 · F-4 | spike (throwaway) | M·needs-design | TD.0 | **Bar GO định lượng (chống rubber-stamp):** bắt **≥4/4** lỗi-đã-biết — (1) gate-STALE sau U-turn v2.0, (2) matrix thiếu REQ-040/041/042, (3) MODEL_DRIFT code↔v2.3, (4) slice request/snapshot sót — **VÀ 0 false-positive trên corpus artifact-ĐÚNG** (= ≥1 feature lành mạnh đã merge, vd phiên-bản v2.3-clean của chính case + 1 feature khác; corpus rỗng → bar vô hiệu, KHÔNG được GO). Bắt <4/4 hoặc corpus rỗng → **NO-GO**. Pilot report ghi số. |
| **TA.1** | **Build-graph kernel** — matrix-as-view · edges `sources:`+content-hash · dirty-set · ground-truth node | buildgraph §3 | `hbc-shared` + `hbc-traceability` | L·needs-design | TA.0 | đồ thị sống; dirty propagate |
| **TA.2** | **Reconcile primitive** — machine-floor + semantic-ceiling | buildgraph §3.2 | `hbc-shared/lib` | L·needs-design | TA.1 | reconcile red→FAIL (invariant) |
| **TA.3** | **Gate=/verify two-stage + outcome RECYCLE** (state-machine PASS/FAIL/RECYCLE→phase-n-k) | IMP-01 · buildgraph | `hbc-phase-gate` | L·needs-design | TA.1 | gate trả về phase trước; cap loop |
| **TA.4** | **Gate exit-criteria 2 tầng engine** (must-knockout / should-scorecard) | IMP-02 | `hbc-phase-gate` | M·ready | TA.3 · T2.x | tier-aware verdict |
| **TA.5** | **100%-rule coverage check** (REQ↔task) bằng máy | IMP-05 | `hbc-task-breakdown` | M·ready | TA.1 · T3.4 | máy-kiểm hai chiều |
| **TA.6** | **Enforce v_pair edges** (design↔test) trong ma trận | IMP-07 · E-7 | `hbc-traceability` | M·needs-design | TA.1 · T3.12 | thiếu cạnh v_pair → gap severity |
| **TA.7** | **`hbc-rebaseline` engine** — re-baseline cross-feature khi đổi model lõi/shared sau Phase-3; Impact declare-shared; route structural-change. **+ A6: thêm cấp "baseline/epic-change" TRÊN feature ở layout** (đơn-vị-thay-đổi xuyên-feature, không chỉ engine) — DoD tường minh | A3 · A6 · B7-5 · B14-6 · ST-2 | **skill mới** `hbc-rebaseline` + layout | L·needs-design | TA.1 | engine MỚI (không extend migrate); **cấp epic/baseline-change ở layout**; blast-radius từ rollup; **+ skill-creation DoD §0.1** |
| **TA.8** | **Circuit-breaker outcome** (blow appetite → re-slice/defer/kill) | IMP-12 | `hbc-phase-gate` | S·ready | TA.3 | nối nhánh Recycle |

> ⚠️ **NO-GO fallback (nếu TA.0 trượt bar):** KHÔNG bỏ trống nửa-enforcement của remediation RCA. Đường-B = giữ enforcement bằng **script Đợt-1/2** (T1.1 MODEL_DRIFT · T1.5 matrix-coverage · T2.2 cascade-enforced · T2.4 STALE · T2.10 readiness) làm lớp máy "đủ tốt", và **Recycle/2-tier (TA.3/TA.4) hạ xuống làm guidance gate** (USER-driven) thay vì engine. Tức trục A → "enforcement nhẹ không-kernel", không phải dừng hẳn.
>
> ⚠️ **Các quyết-định-BẮT-BUỘC của maintainer KHÔNG được giam hết trong kernel** (sửa pattern #3): các bản **tối-thiểu không-kernel PHẢI ship ở Đợt 2 bất kể spike** — **B5-4** STALE→**block-implement** (tường minh ở `hbc-implement`, không chỉ T2.4 "interim") · **B7-3** drift-watch (ship tối-thiểu ở T2.4, không hoãn chờ TA.1) · **B7-5** structural-change→**route cảnh-báo/rebaseline** (touchpoint nhẹ ở `hbc-traceability`, độc lập kernel) · **B7-6** cascade pre-check: **matrix-khuyết → blocked `untraced_change` + backfill** (thêm vào T2.2). Kernel TA.x chỉ NÂNG CẤP các bản này, không phải là điều-kiện-tồn-tại của chúng.

---

## 6. KỶ LUẬT XUYÊN SUỐT (F — bắt buộc kèm khi triển khai)

| ID | Task | Source | DoD |
|----|------|--------|-----|
| **TF.1** | **De-ceremony budget** — mỗi gate/doc/check THÊM phải kèm 1 BỎ/gộp/làm-nhẹ; default-light theo maturity | F-1 | net-ceremony ≤ 0 mỗi đợt; rà THÊM:BỎ |
| **TF.2** | **Pilot discovery-spike** trên 1 feature uncertain THẬT + đo (model-spike là hypothesis) | F-4 | pilot report: có ngăn được "model sai trước build" không |
| **TF.3** | **F-6 metrics harness** — baseline + target: churn D-02 13→≤4 · re-cascade 4+→1 · gate-false-pass 3→0 · spec-ref 65→0 · REQ-không-matrix 3→0 · code↔design-drift 0→100% bắt. **Substrate = fixture TD.0** (snapshot case `resource-plan-billable`); metric vô nghĩa nếu không có input cố định để đo lại | F-6 | script đo chạy trên fixture TD.0, xuất số trước-sau mỗi đợt; **không có TD.0 thì TF.3 không khởi động được** |
| **TF.4** | **Independent-subagent review** cho mọi item Effort=L / needs-design trước khi vào roadmap chính | F-3 | mỗi L-item có 1 vòng adversarial độc lập |
| **TF.5** | **Lưu substrate research per-skill** — chuẩn B2 (DB 3-tier)/B3-5 (technique-map)/B4 (TDD-slice)/B9 (29119) chạy `bmad research` inline, CHƯA lưu doc nguồn → traceability đứt. Tái-chạy + lưu vào `process-review/research/` | elicitation B2/B3/B4/B9 | mỗi chuẩn per-skill có doc research nguồn có trích dẫn (như research phase/work-breakdown/role) |

## 6.5 REMOVE / de-ceremony track (F-1 — đối trọng cho ~36 task ADD)
> Plan trên gần như chỉ THÊM. Để giữ net-ceremony ≤ 0 (F-1), MỖI đợt phải kèm các BỎ/gộp dưới. Đây là **ứng viên REMOVE cụ thể** — không còn là khẩu hiệu.

| ID | REMOVE / gộp / làm-nhẹ | Vì sao | Bù cho |
|----|------------------------|--------|--------|
| **RM.1** | **Gộp P1-09 + P1-11 thành 1 touchpoint model-validation** (uncertain → đường discovery-note; known → sign-off nhẹ) — không bắt user ký 2 lần. ⚠️ **P1-09/P1-11 ĐÃ ship lên main** → đây là **breaking-change**: phải đi qua T1.8 migrate + CHANGELOG breaking, không sửa lén | tránh gate-fatigue 2 mục chồng nghĩa | T1.8 · T2.6 |
| **RM.2** | **Rút "semantic review lens + sign-off" lặp ở ~10 skill về 1 reference dùng chung** (`hbc-shared`), skill chỉ trỏ tới | đang lặp prose mỗi skill → token + churn | T3.1–T3.10 |
| **RM.3** | **maturity `exploratory` TẮT** các gate Đợt-2 mới (review bắt buộc, ADR-gate, P1-11) cho feature thăm-dò | F-1 default-light; tránh nhân HALT | T2.5–T2.8 · T3.16 |
| **RM.4** | **Bỏ na_deliverables verbosity** — thay bằng applicability-instance (T3.15) tự suy N/A | catalog instance thay waiver thủ công | T3.15 |
| **RM.5** | **Xoá `process-review/MR-trucb-framework.md`** (đã bị MR gộp thay) + dọn `_bmad/hbc/module-help.csv.bak` | rác/superseded | (housekeeping) |
| **RM.6** | **Retire check cũ bị MODEL_DRIFT/coverage (T1.1/T1.5) bao trùm** — CHỈ retire sau khi **chứng minh new-check ⊇ old-check** (diff coverage trên fixture TD.0); bao-trùm một-phần → giữ cả hai | tránh 2 check cùng việc; chống coverage-gap ngầm | T1.1/T1.5 · TD.0 |
| **RM.7** | **Quick-Plan fast-path (T3.13b) BỎ bớt gate-question** cho feature trivial/bugfix | đối trọng trực tiếp cho mọi ADD gate | T2.x |

> **Quy tắc:** mỗi PR Đợt-2/3 thêm gate phải dẫn ≥1 RM.x tương ứng; reviewer reject nếu net-ceremony > 0.
> ⚠️ **Pool-exhaustion (edge-case):** Đợt 3 có ~21 ADD nhưng pool RM chỉ 7 → KHÔNG đủ 1-đổi-1. Quy tắc thực tế: **(a) đa số ADD per-skill là *thay-thế guidance cũ* (net ~0 tự thân), không phải HALT mới — chỉ HALT/gate/doc mới mới cần RM;** (b) khi pool cạn, cho phép **net > 0 kèm rationale USER ký** (ngân-sách ngoại lệ), không chặn cứng. Đo net-ceremony = số *HALT/gate* ròng, không phải số dòng.

---

## 7. NỢ DỰ ÁN — `resource-plan-billable` (TÁCH khỏi framework; RCA §6.2)
> Dọn-nợ-case (TD.1–TD.6), không phải cải-tiến-framework — làm khi quay lại feature đó.
> ⚠️ **NGOẠI LỆ — TD.0 KHÔNG parked:** TD.0 là **`T0` — prereq của cả plan** (TF.3 metrics + TA.0 spike phụ thuộc nó). Phải làm **TRƯỚC Đợt 1**, không hoãn cùng TD.1–6. (Đây là deadlock mà edge-case #1 chỉ ra: exit-criteria các đợt đo trên TD.0 nên TD.0 không thể nằm trong track-hoãn.)

| ID | Task | Source | DoD |
|----|------|--------|-----|
| **TD.0** = **`T0`** | **Snapshot case `resource-plan-billable` (trạng-thái-lỗi) làm REGRESSION FIXTURE** — đóng băng artifact + matrix + code mang lỗi-đã-biết (gate-STALE, thiếu 040-042, MODEL_DRIFT, slice sót, 65 spec-ref) làm input cố định cho TF.3 + TA.0. **Nguồn = git-ref/tag TẠI thời điểm RCA (2026-06-20), KHÔNG dùng HEAD** (case có thể đã đổi → trạng-thái-lỗi không dựng lại được từ HEAD). **Prereq toàn plan — làm TRƯỚC Đợt 1** | RCA §0/§7 · F-6 | fixture bất biến (vd `process-review/fixtures/` từ git-ref RCA) + checklist lỗi-đã-biết; metric đo lại được |
| TD.1 | Sửa matrix: +REQ-040/041/042, repoint REQ-024, điền code_ref thật | F1 | matrix khớp v2.3 |
| TD.2 | Re-derive task-breakdown từ v2.3 (đang v1.8) | F2 | có task request/snapshot/hash/in-flight |
| TD.3 | Re-implement code theo v2.3 + viết lại 146 test | F3 | code = model v2.3 (khối lớn nhất) |
| TD.4 | Chạy lại gate 1/2/3 thật trên v2.3 (không manual-pass) | F4 | gate xanh thật |
| TD.5 | Vá mâu thuẫn/cross-ref (D-02 §6.2 vs NFR-005; cite đúng v2.3; bỏ TBD) | F5 | 0 mâu thuẫn |
| TD.6 | Gỡ 65 spec-ref khỏi code/test | F6 | spec-ref leak 0 |

---

## 8. Sequencing đề xuất (đường tới hành động)

```
ĐỢT 1 (T1.1–T1.7) ─ rẻ, độc lập, vá gốc false-green ─┐
                                                      ├─► ĐỢT 2 (T2.1 A5 ⭐ → T2.10 readiness)
T2.10 readiness cần T1.1/T1.3/T1.5 ───────────────────┘
                                                      │
ĐỢT 3 per-skill (T3.x) ─ song song, mỗi skill 1 nhánh ─┤  (T3.4 cần T1.5; T3.x cần T2.1 autonomy)
                                                      │
TA.0 SPIKE ─(GO)─► TRỤC A (TA.1…TA.8) + hbc-rebaseline ┘
                                                      │
TF.3 metrics dựng TRƯỚC Đợt 1 (để đo) · TF.1 de-ceremony áp MỖI đợt · TF.2 pilot sau khi có feature uncertain · TF.4 gate cho mọi L-item
```

**Khuyến nghị bắt đầu (sửa sau review — fixture TRƯỚC):** `TD.0` (snapshot fixture — prereq đo) → `TF.3` (metrics harness) → **Đợt 1** (T1.1 MODEL_DRIFT · T1.2 spec-ref lint · T1.5 matrix-coverage) → `T2.10` readiness → `T2.1` autonomy → `TA.0` spike (bar ≥4/4 → GO) → trục A.

### Sizing rollup (chỉ-báo, KHÔNG phải cam kết — F-2; mọi L qua F-3 trước)
| Nhóm | #task | Effort thô | Cần spike/needs-design? |
|---|---|---|---|
| Đợt 1 (T1.x + T-ENV) | 9 | hầu hết **S/M·ready** | không |
| Đợt 2 (T2.x) | 12 | **M·ready** (T2.5 needs-design); T2.11 anti-churn vá RCA #1 | không |
| Đợt 3 (T3.x + 3.13a–f) | ~23 | M nhiều · **3 task L** (T3.1/3.2/3.3) + T3.12/3.14/**T3.17** needs-design; +T3.18 brownfield-implement | không (trừ UX spike) |
| Trục A (TA.x) | 9 | **L·needs-design** chủ đạo | **CÓ — gated bởi TA.0** |
| Kỷ luật F (TF.x) | 5 | S/M | — |
| REMOVE (RM.x) | 7 | S | — |
| Nợ-case (TD.x) | 7 | M/L | — |

> Critical path: `TD.0 → TF.3 → Đợt1 → T2.10 → TA.0(GO) → TA.1→TA.7`. Trục A là khối rủi-ro-cao dài nhất; mọi thứ trước nó **không phụ thuộc spike** nên có thể chạy ngay.

### Exit-criteria tổng (khi nào coi 1 đợt "done")
- **Đợt 1/2:** xem dòng *Exit-criteria* cuối mỗi §; cộng: pytest+doc-check+VM xanh · net-ceremony ≤ 0 (≥1 RM.x/đợt) · F-6 metric cải thiện trên TD.0.
- **Trục A:** chỉ "done" khi TA.0 đạt bar ≥4/4 (NO-GO → dừng, không sunk-cost).
- **Toàn plan:** F-6 đạt target (false-pass 0 · spec-ref 0 · drift bắt 100% · churn ≤4) **đo trên fixture**, không phải tự-khai.

> ⚠️ Nhắc lại (elicitation §meta): tài liệu này là **backlog để chuẩn bị implement**, mỗi item L/needs-design phải qua **F-3 review độc lập** trước khi code; và **F-1 de-ceremony** áp mỗi đợt để HBC không phình thành gate-fatigue.

---

## 9. Per-skill Implementation Dossier (hợp-đồng chống-sót-spec)

> **Cách dùng:** implement **TRỌN VẸN từng skill** (không rời theo wave). Mỗi skill = 1 phiên `bmad-workflow-builder` (Edit). **Tick từng `[ ]` B-ID**; skill chỉ KHOÁ khi **mọi ô ✅ + AR + ECH (F-3) + VM 0 + pytest/doc-check xanh + metric đo trên TD.0**. Bundling: gộp T2.1(autonomy)+T2.12(semantic-review)+T2.11(anti-churn) vào chính lượt rewrite (đừng sửa 2 lần). `(✅done)` = đã có, chỉ verify lại; `(spike)` = gated TA.0.

### Prereq nền (làm TRƯỚC mọi skill — là THƯ VIỆN per-skill gọi tới)
- [x] **T0/TD.0** fixture `resource-plan-billable` (git-ref RCA) ✅ U0 · [x] **TF.3** metrics harness ✅ U0 — `process-review/fixtures/resource-plan-billable/` (hash-pinned, 6 metric, baseline 13/44/3/2/5/≥4)
- [x] T1.5 matrix-coverage-lib ✅ U1 · [x] T1.3 version-coherence-lib ✅ U1 · [x] T1.1 MODEL_DRIFT ✅ U1 · [x] T1.2 spec-ref-lint ✅ U1 · [x] T2.12/RM.2 semantic-review-reference ✅ U1 · [ ] T2.1 autonomy-pattern · [x] T2.11 anti-churn-lib ✅ U1 · [ ] T-ENV (tiktoken/python/path) · [ ] T-REINSTALL
  - **U1 done (2026-06-22):** primitives in `hbc-shared/lib/hbc_validation.py` (`missing_from_matrix`/`matrix_coverage_gaps`/`reqs_without_task`, `version_coherence`, `model_drift`, `spec_ref_leaks`, `churn_assessment`, `semantic_review_status`) + runnable scripts (`hbc-implement/validate-implementation.py --code-dir/--design`, `hbc-traceability/check-matrix-coverage.py`, `hbc-phase-gate/check-version-coherence.py`). 85 unit/fixture tests; all re-derive the TD.0 baseline (3 missing-rows, 13 churn, v2.2-stale, 2 model-drift, 44 spec-ref). F-3 (adversarial+edge-case) closed: dotted-substring masking, quoted/absent/blank-line `openFacets`, spaced matrix headers, multi-line `_name`, None-safety. *(T2.1 autonomy / T-ENV / T-REINSTALL are separate nền units, not in U1's scope.)*

### Phase 1
**`hbc-create-requirements` [REQ]** — DoD: 10/10 B + review + VM
- [ ] B1-1 duyệt REQ-list trước generate (T3.1) · [ ] B1-2 intake pipeline (T3.1) · [ ] B1-3 NFR→ASSUMPTION/ADR (T3.1) · [ ] B1-4 reality-check + nối Model-Spike (T3.1·T3.17) · [ ] B1-5 **Feasibility bắt-buộc** đọc source+framework (T3.1) · [ ] B1-6 Quick-Discovery luôn (T3.1) · [ ] B1-7 2-câu-suggest topic→output (T3.1) · [ ] B1-8 Discovery-bổ-sung sau brainstorm (T3.1) · [ ] B1-9 adversarial+edge-case bắt buộc (T2.8) · [ ] B1-10 grounding đọc source (T3.1) · [ ] A5 autonomy (T2.1) · [ ] discovery_risk classify `(✅done, reposition T3.17)`

**`hbc-create-glossary` [GLO]** — DoD: 3/3
- [ ] B11-1 definition ground-source + user-confirm-khi-suy-ra (T3.7) · [ ] B11-2 cross-doc consistency + orphan-flag (T3.7) · [ ] B11-3 DDD ubiquitous-language + đối chiếu D-19 **+ code** (T3.7) · [ ] A5 autonomy (T2.1)

**`hbc-create-business-flow-diagram` [BFD]** — DoD: 7/7
- [ ] B8-1 swimlane+gateway 3–7 lane `(✅ stage-guide)` · [ ] B8-2 all-paths happy/alt/exception (T3.11) · [ ] B8-3 **AS-IS ground vào CODE** + log lệch (T3.11) · [ ] B8-4 confirm flow/actor/path TRƯỚC generate (cứng) (T3.11) · [ ] B8-5 REQ-flow-facet + phantom-flag (T3.11) · [ ] B8-6 path-ID chuẩn `(✅ partial)` · [ ] B8-7 D-06 vào review bắt buộc (T2.8)

**`hbc-discovery-spike` [DSC]** — DoD: reposition trọn vẹn
- [ ] A1/B1-4/B2-6 reposition → Model-Spike soi **D-19 draft** ở P1→P2 (T3.17) · [ ] discovery_risk = ĐỘ-SÂU (không quyết có-chạy) (T3.17) · [ ] P1-11 → gate đầu-Phase-2 (T3.17) · [ ] breaking → T1.8+CHANGELOG · [ ] A5 autonomy standalone (T2.1)

### Phase 2 — Design
**`hbc-create-architecture` [AD]** — DoD: verify + autonomy
- [ ] E-1 Architecture = D-09 `(✅ reconcile)` · [ ] E-7 v-pair surface (T3.12) · [ ] A5 autonomy (T2.1)

**`hbc-create-er-diagram` [ERD]** — DoD: 10/10
- [ ] B2-1 3-tier ASK-gate (T3.2) · [ ] B2-2 entity/field↔≥1 REQ (T3.2) · [ ] B2-3 ondelete-ask + rationale (T3.2) · [ ] B2-4 index-proposal (T3.2) · [ ] B2-5 conceptual↔REQ+D-06 (T3.2) · [ ] B2-6 logical-D-19 = Model-Spike object (T3.17) · [ ] B2-7 ground real schema + **log mọi lệch** (T3.2) · [ ] B2-8 semantic lens+signoff (T2.12) · [ ] B2-9 anti-churn (T2.11) · [ ] B2-10 decision-record→ADR (T3.2·dep T2.5)

**`hbc-create-behavioral-design` [BD]** — DoD: complete E-2 + BDD
- [ ] E-2 detailed-design (ST/DR/INV/SEQ) `(D-16 ✅ partial → T3.12 hoàn tất)` · [ ] B3-?BDD-Given-When-Then facet (T3.13d) · [ ] B2-8 semantic (T2.12) · [ ] anti-churn (T2.11) · [ ] A5 (T2.1)

**`hbc-create-ux` [UX]** — DoD: 8/8 (conditional Part-D)
- [ ] UX-1 **HỎI user Claude-Design optional + link có-điều-kiện** (T3.14) · [ ] UX-2 design-sync mockup↔D-14↔matrix (T3.14) · [ ] UX-3 component-map↔code↔token (T3.14) · [ ] UX-4 matrix REQ→screen→component→test (T3.14) · [ ] UX-5 UI-acceptance/visual-regression (T3.14) · [ ] UX-6 token single-source (T3.14) · [ ] UX-7 outside-in ATDD (T3.14) · [ ] UX-8 maturity-gate UX (T3.14·T3.16)

**`hbc-create-coding-standards` [CS]** — DoD: 4/4
- [ ] B10-1 derive-from-real-code + deviation-flag (T3.6) · [ ] B10-2 machine-rule→lint + gate-P3 (T1.2·T3.6) · [ ] B10-3 preference KHÔNG tự-default → confirm (T3.6) · [ ] B10-4 update + **cascade-advisory** (D-12 shared) (T3.6·T2.2)

**`hbc-create-api-spec` [API]** — DoD: N/A-by-catalog (không cắt sẵn)
- [ ] B12 = N/A cho Odoo nhưng **giữ tầng** (N/A do catalog quyết per-feature, T3.15) · [ ] E-7 v-pair API↔integration-test (T3.12)

### Phase 2 — Test Design
**`hbc-create-test-plan` [TP]** — DoD: 4/4
- [ ] B9-1 no-fabricated-schedule (T3.5) · [ ] B9-2 risk-grounded + **L/I user-confirm** (T3.5) · [ ] B9-3 **chốt in/out-scope TRƯỚC generate** (T3.5) · [ ] B9-4 technique-per-scope→D-27 (T3.5)

**`hbc-create-test-spec` [TS]** — DoD: 10/10
- [ ] B3-1 sanity TC-nhạy-cảm (T2.9) · [ ] B3-2 ground test-data D-19 (T3.3) · [ ] B3-3 depth theo maturity (T3.3·T3.16) · [ ] B3-4 **chốt facet/scope per-REQ TRƯỚC generate** (T3.3) · [ ] B3-5 technique-map 5-kỹ-thuật (T3.3) · [ ] B3-6 severity user-confirm (T3.3) · [ ] B3-7 **reconcile TC↔code thật** (T3.3) · [ ] B3-8 semantic lens+signoff (T2.12) · [ ] B3-9 edge+adversarial trước P2-gate (T2.8) · [ ] B3-10 anti-churn (T2.11)

**`hbc-check-implementation-readiness` [IR]** — DoD: 6/6 (cổng đã LỖI)
- [ ] B13-1 parse-cột-matrix non-empty (T2.10·T1.5) · [ ] B13-2 **reconcile 3-chiều REQ↔TASK↔design** (T2.10) · [ ] B13-3 +D-19/MODEL_DRIFT (T2.10·T1.1) · [ ] B13-4 version-coherence ở seam (T2.10·T1.3) · [ ] B13-5 scope-hoá TC/row chống paste-appendix (T2.10) · [ ] B13-6 fix headless-contract (T2.10)

### Phase 3
**`hbc-task-breakdown` [TB]** — DoD: trọn vẹn
- [ ] B4-1 vertical-slice+INVEST+SPIDR+test-list (T3.4) · [ ] B4-2 input D-06/AC/spike/**ADR**/code-NEW-CHANGE + gate-input-đủ (T3.4) · [ ] B4-5 no-default-override tại skill (T3.4) · [ ] B4-6 **duyệt bảng path/facet/entity→slice TRƯỚC generate** (T3.4) · [ ] B4-7 mọi REQ↔≥1 task (T3.4·T1.5) · [ ] B4-8 autonomy (T2.1) · [ ] B4-3 STALE re-derive (T2.4) · [ ] 100%-rule coverage máy `(spike TA.5)`

**`hbc-implement` [IM]** — DoD: 10/10
- [ ] B5-1 MODEL_DRIFT (T1.1) · [ ] B5-2 no-spec-ref-lint (T1.2) · [ ] B5-3 RED-soft + FAIL-đúng-nhánh + sanity (T2.9) · [ ] B5-4 **STALE→block-implement** (tường minh, §5+T2.4) · [ ] B5-5 batch dừng khi test-PASS-ngay (T2.9) · [ ] B5-6 GREEN-only-D19 (T1.1·T3.18) · [ ] B5-7 coverage CẦN-không-đủ (T1.1·T2.9) · [ ] B5-8 **brownfield phân biệt sửa-vs-tạo** (T3.18) · [ ] B5-9 DONE-sanity (T2.9) · [ ] B5-10 batch-domain-stop / headless-blocked (T2.1)

### Phase 4
**`hbc-test-execution` + `hbc-acceptance-check` [TE/AC]** — DoD: 4/4
- [ ] B16-1 verify-ref-thật + MODEL_DRIFT clean (T3.10·T1.1/T1.5) · [ ] B16-2 model-match + sanity + coverage-không-đủ (T3.10·T2.9) · [ ] B16-3 D-27-STALE check (T3.10·T1.3) · [ ] B16-4 **UX↔mockup acceptance khi Part-D** (T3.10·dep T3.14)

### Cross-cutting
**`hbc-phase-gate` [PG]** — DoD: B6 + kế-thừa-A
- [ ] B6-1 QUALITY adversarial + định-lượng + CONTESTED (T2.6) · [ ] B6-2 machine-numbers (T1.4) · [ ] B6-3 **ĐÃ-CÓ — chỉ mở rộng correctness, không re-build** (T2.7) · [ ] B6-4 waiver-no-correctness (T2.7) · [ ] B6-5 design-phase user-sign-off (T2.6) · [ ] B6-6 ambiguous→CONTESTED (T1.6) · [ ] A2/A8 STALE+auto-revalidate `(interim T2.4 → spike TA.x)` · [ ] A4 ADR-gate (T2.5) · [ ] A9 matrix-completeness (T1.5·T2.3) · [ ] maturity-gating (T3.16) · [ ] Recycle/2-tier/circuit-breaker `(spike TA.3/4/8)`

**`hbc-traceability` [TRI/TRU/TRR/TRA/SYNC]** — DoD: B7 + matrix-engine
- [ ] B7-1 cascade-ENFORCED block-complete (T2.2) · [ ] B7-2 skill-tự-ghi-matrix (T2.3) · [ ] B7-3 drift-watch (tối-thiểu Đợt-2, §5) · [ ] B7-4 reconcile-adversarial (T2.2) · [ ] B7-5 structural→rebaseline route (touchpoint nhẹ §5 → engine TA.7) · [ ] B7-6 cascade-precheck matrix-khuyết→blocked (T2.2) · [ ] matrix-as-view / v_pair-edges `(spike TA.1/TA.6)`

**`hbc-migrate` [MIG]** — DoD: 6/6
- [ ] B14-1 emit missing_from_matrix (T1.7) · [ ] B14-2 scope-regex-id + dry-run (T1.7) · [ ] B14-3 re-prefix impl/gates (T1.7) · [ ] B14-4 dirty-guard-warn + timestamp-unique (T1.7) · [ ] B14-5 contract↔engine sync (T1.7) · [ ] B14-6 rebaseline = engine MỚI (TA.7) · [ ] T1.8 D-code migrate **idempotent + mixed** (T1.8)

**`hbc-project-init` [PI]** — DoD: 4/4 + constitution
- [ ] B15-1 re-run drift+update (T3.9) · [ ] B15-2 baseline-Architecture + nạp-catalog Phase-0 (T3.9·T3.15) · [ ] B15-3 brownfield derive D-19 **(+D-21 khi có API)** (T3.9) · [ ] B15-4 confirm classify + **stack/domain/conventions** (T3.9) · [ ] constitution.md (T3.13a)

**5 agent `hbc-agent-{ba,architect,qa,dev,tester}`** — DoD: 4/4 mỗi agent
- [ ] B17-1 ELICIT>auto persona (T3.8) · [ ] B17-2 **mỗi agent điều phối bước-mới của phase mình** (T3.8) · [ ] B17-3 HALT-thật (không chỉ warn) + log-override (T3.8) · [ ] B17-4 gọi subagent độc-lập review (T3.8·T2.6)

**`hbc-rebaseline` [MỚI]** — DoD: skill-creation §0.1 `(spike)`
- [ ] A3 re-baseline cross-feature · [ ] A6 cấp epic/baseline-change ở layout · [ ] B7-5 route structural-change · [ ] B14-6 engine-mới-không-extend-migrate · [ ] đăng-ký-3-nơi + test + headless-contract + docs (TA.7)

> **Tổng cờ spec:** ~95 ô B-ID/decision xuyên 21 skill/agent + nền. Skill "done" = mọi ô của nó ✅. Khi cả §9 ✅ + F-6 đạt target trên fixture ⇒ plan hoàn tất.

---

## 10. Implementation Runbook (auto-next — để KHÔNG phải nhớ thứ tự)

> **Quy tắc chọn bước tiếp theo:** đơn-vị kế = **đơn-vị ĐẦU TIÊN trong bảng dưới mà chưa-done (ô §9 chưa 100% ✅) VÀ mọi `prereq` của nó đã done.** Cứ thế tới hết. Mỗi đơn-vị = 1 session.

| # | Đơn vị | BMad skill để gọi | Prereq | Done khi |
|---|--------|-------------------|--------|----------|
| U0 ✅ | TD.0 fixture + TF.3 metrics | (script tay, không builder) | — | **DONE** — fixture hash-pinned + harness 6 metric, baseline đo được + F-3 sạch |
| U1 ✅ | Primitives (T1.1/1.2/1.3/1.5 · T2.11/T2.12) | (script-only → direct + F-3 review per §0.1 RACI) | U0 | **DONE** — libs+scripts+85 tests; bắt đủ lỗi fixture TD.0; F-3 sạch high/critical |
| U2 | `hbc-create-glossary` | `bmad-workflow-builder` Edit | U1 | §9 GLO 100% + AR+ECH+VM |
| U3 | `hbc-create-coding-standards` | `bmad-workflow-builder` Edit | U1 | §9 CS 100% |
| U4 | `hbc-create-business-flow-diagram` | `bmad-workflow-builder` Edit | U1 | §9 BFD 100% |
| U5 | `hbc-create-test-plan` | `bmad-workflow-builder` Edit | U1 | §9 TP 100% |
| U6 | `hbc-create-requirements` [L] | `bmad-workflow-builder` Edit | U1 | §9 REQ 100% |
| U7 | `hbc-create-er-diagram` [L] | `bmad-workflow-builder` Edit | U1 | §9 ERD 100% |
| U8 | `hbc-create-test-spec` [L] | `bmad-workflow-builder` Edit | U1·U7 | §9 TS 100% |
| U9 | `hbc-task-breakdown` [L] | `bmad-workflow-builder` Edit | U1 | §9 TB 100% |
| U10 | `hbc-implement` (+T3.18 brownfield) | `bmad-workflow-builder` Edit | U1 | §9 IM 100% |
| U11 | `hbc-check-implementation-readiness` | `bmad-workflow-builder` Edit | U1 | §9 IR 100% |
| U12 | `hbc-project-init` (+constitution) | `bmad-workflow-builder` Edit | U1 | §9 PI 100% |
| U13 | `hbc-migrate` (+T1.8 D-code) | `bmad-workflow-builder` Edit | U1 | §9 MIG 100% |
| U14 | Phase-4 (test-execution + acceptance) | `bmad-workflow-builder` Edit | U7·U10 | §9 TE/AC 100% |
| U15 | `hbc-create-behavioral-design` + `hbc-create-ux` | `bmad-workflow-builder` Edit | U1 | §9 BD/UX 100% (UX conditional) |
| U16 | `hbc-phase-gate` (B6 + kế-thừa) | `bmad-workflow-builder` Edit | U1·(phần lớn skill trên) | §9 PG 100% (trừ ô spike) |
| U17 | `hbc-traceability` (B7) | `bmad-workflow-builder` Edit | U1·U16 | §9 TR 100% (trừ ô spike) |
| U18 | 5 agent (B17) | `bmad-agent-builder` | skill của phase tương ứng | §9 agents 100% |
| U19 | **VM toàn module** (checkpoint) | `bmad-module-builder` VM | sau mỗi ~4 U | 0 finding |
| U20 | **Spike TA.0** (cổng trục A) | (spike tay) | U0 | bar ≥4/4 → GO, else NO-GO+fallback §5 |
| U21 | Trục A (TA.1–TA.8) + `hbc-rebaseline` | `bmad-workflow-builder` Build/Edit | **U20 GO** | §9 ô (spike) ✅ |
| U22 | Nợ-case TD.1–TD.6 | (tay, feature resource-plan-billable) | — | RCA §6.2 |

**Per-session loop (driver tự làm):** xác định U kế → mở đúng BMad skill → implement theo §9 dossier của nó (bundling T2.1/T2.12/T2.11) → eval input thật → AR+ECH → VM/pytest/doc-check → **tick ô §9 + cập nhật bảng này** → `git commit` → báo "đã xong Ux, kế tiếp Uy".
