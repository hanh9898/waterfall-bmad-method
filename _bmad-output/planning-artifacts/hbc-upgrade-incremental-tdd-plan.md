---
title: Kế hoạch nâng cấp HBC — Incremental per-feature + TDD (test-coupled)
module: HBLAB BMad Custom (hbc)
type: module-upgrade-plan
status: ready-to-build
created: 2026-06-17
updated: 2026-06-17
revision: 3 (đã đóng 6 điểm để ngỏ a–f)
---

# Kế hoạch nâng cấp HBC: Incremental per-feature + kỷ luật TDD

> Nguồn: review `src/` (party-mode) + adversarial review của chính plan. Bản này
> đã đóng 15 finding adversarial theo lựa chọn của user.

## Quyết định thiết kế (đã chốt)

| # | Quyết định | Chọn |
|---|-----------|------|
| ① | Cơ chế feature | **Hybrid**: per-feature folder cho D-xx per-feature; **matrix per-feature + report roll-up** |
| ② | REQ ID | `REQ-<FEAT>-NNN` + namespace **`SHARED`** (`REQ-SHARED-NNN`) cho yêu cầu dùng chung |
| ③ | TDD | **Test-coupled + RED-attested (soft)** — lưu RED-evidence + structural check; **KHÔNG** tuyên bố "guaranteed" (evidence tự khai). Docs mô tả trung thực |
| A | Yêu cầu | Viết theo **EARS** — **keyword tiếng Anh** (`WHEN`/`THE SYSTEM SHALL`), **nội dung theo `document_output_language`** (Tiếng Việt); validator **cảnh báo** (không block) + ví dụ |
| B | Active feature | **Không file global**; agent giữ feature trong phiên; headless **bắt buộc** arg `feature=<slug>` |
| C | Map TDD | Gate đối chiếu RED-evidence với cặp `code_ref↔test_ref` của matrix (soft cross-check) |

## Phân loại D-xx theo scope (quan trọng)

| Scope | Deliverable | Vị trí |
|-------|-------------|--------|
| **Per-feature** | D-02 Requirements · D-06 Business Flow · D-26 Test Plan · D-27 Test Spec · task-breakdown · code · tdd-evidence · test-execution · acceptance | `features/<feature>/…` |
| **Shared (toàn dự án)** | D-12 Coding Standards · D-03 Glossary | `shared/…` |
| **Cả hai** | D-19 ERD · D-21 API Spec | `shared/…` làm baseline **+** `features/<feature>/…` override khi dự án chia nhiều module/framework. Feature mặc định kế thừa shared; có override thì dùng override |

- **Phase 0 — Project Init (a):** deliverable **shared** (D-12, D-03, và baseline D-19/D-21) được tạo **một lần** qua bước project-init (mở rộng `hbc-setup` thành `hbc-project-init`/Phase 0) **trước** khi làm feature. Feature sau kế thừa.
- **Override resolution (b):** với D-19/D-21 — nếu tồn tại file `features/<feature>/…` thì dùng nó; không thì fallback `shared/…` (**path-existence precedence**, ẩn, không cần khai báo).

## Mô hình "feature" (first-class)

- **feature slug**: kebab-case, validate format (`^[a-z0-9][a-z0-9-]*$`), không trùng `shared`/`default`.
- **Active feature (B)**: agent xác lập feature ở đầu chu trình & giữ trong phiên hội thoại. **Không** file `.active` toàn cục. Headless/script: arg `feature=<slug>` bắt buộc.
- **Đường dẫn:**
  - Per-feature: `{output_folder}/features/<feature>/{planning-artifacts,implementation-artifacts,gates}/…`
  - Shared: `{output_folder}/shared/{coding-standards,glossary,erd,api}/…`
  - Matrix per-feature: `{output_folder}/features/<feature>/traceability/matrix.md`
  - Report roll-up: `{output_folder}/traceability/coverage-rollup.md` (TRR đọc mọi matrix)
- **Gate & Acceptance theo feature**: đọc artifact + matrix của feature đang xử lý → feature dở không chặn feature đã xong.

## EPIC 1 — Per-feature increment

| # | File | Thay đổi |
|---|---|---|
| 1.0 | `hbc-setup` → **Phase 0 / project-init** (a) | Tạo deliverable **shared** 1 lần (D-12 Coding Standards, D-03 Glossary, baseline D-19/D-21) ở `shared/` trước khi làm feature |
| 1.1 | `hbc-traceability/assets/matrix-template.md` | Ma trận **per-feature**; `feature` là nhóm chính (tính coverage); `story_id` giữ làm link BMM tùy chọn |
| 1.2 | `hbc-traceability/SKILL.md` + `customize.toml` | TRI/TRU theo feature (path per-feature); **TRR đọc nhiều matrix → report roll-up** cross-feature; TRA theo feature |
| 1.3 | `hbc-create-requirements/SKILL.md` | Nhận `feature`; REQ ID `REQ-<FEAT>-NNN` + `REQ-SHARED-NNN`; cho tham chiếu chéo feature/shared; viết REQ **EARS (A)** |
| 1.4 | `…/scripts/validate-requirements.py` | Chấp nhận `REQ-<FEAT>-NNN`/`REQ-SHARED-NNN` (+ `_v2`); tuần tự **theo từng namespace**; **cảnh báo** REQ không-EARS (không block) |
| 1.5 | `…/assets/D-02_requirements_template.md` | Trường `Feature`; **mẫu EARS** (keyword Anh, nội dung Việt) + ví dụ |
| 1.6 | `hbc-create-er-diagram`, `hbc-create-api-spec` | Hỗ trợ **cả shared lẫn per-feature** (baseline shared + override per-feature) |
| 1.7 | `hbc-create-coding-standards`, `hbc-create-glossary` | Output **shared/** (toàn dự án) |
| 1.8 | `hbc-create-business-flow-diagram`, `hbc-create-test-plan`, `hbc-create-test-spec` | Per-feature path; nhận `feature` |
| 1.9 | `hbc-task-breakdown`, `hbc-implement` | Path `features/<feature>/`; tham chiếu REQ/TC theo feature (+ shared) |
| 1.10 | `hbc-test-execution`, `hbc-acceptance-check` | Scope theo feature; AC ship 1 feature độc lập |
| 1.11 | `hbc-phase-gate/SKILL.md` + `assets/phase-*-gate-checklist.md` + customize | Nhận `feature`; đọc artifact + matrix của feature ("every REQ **of this feature**", gồm SHARED được feature tham chiếu) |
| 1.12 | 5 agent (`hbc-agent-*`) | Hỏi/giữ feature trong phiên (B); mang xuyên suốt; không ghi file global |

## EPIC 2 — Kỷ luật TDD (test-coupled + RED-attested, soft)

| # | File | Thay đổi |
|---|---|---|
| 2.1 | `hbc-implement/SKILL.md` | HALT quy trình: mỗi task viết test → CHẠY → lưu **RED-evidence** (log fail) vào `tdd-evidence/<TASK>.md` → rồi code. *(Lưu ý: evidence do agent tự khai — kỷ luật, không phải bằng chứng mật mã.)* |
| 2.2 | `…/scripts/validate-implementation.py` | Mỗi task DONE phải có `tdd-evidence/<TASK>.md` chứa lần chạy FAIL |
| 2.3 | `hbc-phase-gate/assets/phase-3-gate-checklist.md` | Item: "Mọi task DONE có RED-evidence"; gate chạy validator 2.2 |
| 2.4 | `hbc-phase-gate` + validator | Soft cross-check RED-evidence ↔ `code_ref/test_ref` (C) |

> 🔖 **Trung thực hóa nhãn:** vì RED-evidence tự khai (cụm 1 = soft), docs gọi là *"kỷ luật TDD (test-first, có RED-evidence)"*, **không** dùng "cưỡng chế/guaranteed". (Cập nhật README/why-incremental-tdd cho khớp.)

## Transition, version & quy trình (cụm 3, 6, 10)

- **Nhánh riêng** `feat/hbc-incremental-tdd`; **bump version** `src/module.yaml` (major, vd 1.x → 2.0).
- **Di trú (3):** script chuyển artifact cũ `_bmad-output/planning-artifacts/*` → `features/default/…`; REQ cũ → `REQ-DEFAULT-NNN`. Sửa lại mọi câu "tương thích ngược" thành "có bước migrate" + fallback `feature=default`.
  - **(d) Repo NÀY:** **bỏ qua chạy migration** (chưa có D-02 thật) — chỉ ship script cho *consumer projects*.
- **Regenerate (c):** sau khi sửa `src/`, đồng bộ bản cài bằng `npx bmad-method install --action quick-update`; **xác minh lệnh thật sự regenerate** ở Bước 7, nếu không phủ hết thì viết script sync + CI drift-check.
- **Nguồn chân lý (6):** `src/` là canonical; thêm bước/script regenerate `_bmad/hbc/*` + `_bmad/_config/*` từ `src/` (hoặc qua installer); thêm CI check chống drift (mở rộng `check_doc_links`/thêm script so khớp).

## Build Roadmap

> Phạm vi (f): **làm trọn 1 đợt** theo thứ tự dưới, validate ở cuối bằng kịch bản nghiệm thu.

0. **Phase 0 / project-init** — 1.0 (tạo shared D-12/D-03 + baseline D-19/D-21).
1. **Nền tảng** — 1.1 + 1.2 (matrix per-feature + roll-up).
2. **REQ + EARS + SHARED** — 1.3 + 1.4 + 1.5.
3. **TDD soft** — 2.1 + 2.2 + 2.3 + 2.4.
4. **Phân scope D-xx** — 1.6 + 1.7 + 1.8 + 1.9 + 1.10.
5. **Gate theo feature** — 1.11.
6. **Agent giữ feature** — 1.12.
7. **Di trú + version bump + regenerate bản cài + VM + dry-run 2 feature**.

## Tiêu chí nghiệm thu (kịch bản cụ thể — cụm 10)

1. **Dry-run 2 feature** (`auth`, `report`): chạy `auth` trọn 4 phase → ship; thêm `report` → feature `auth` KHÔNG bị đè/chặn; mỗi feature có matrix riêng; `coverage-rollup` thấy cả hai.
2. **Shared dùng chung**: cả `auth` & `report` dùng cùng D-12/D-03; D-19 có baseline shared + (tùy chọn) override per-feature.
3. **TDD**: task có `tdd-evidence` FAIL → gate PASS; task thiếu RED-evidence → gate **FAIL**.
4. **EARS**: REQ không-EARS → validator **cảnh báo** (không chặn).
5. **Cross-ref**: feature tham chiếu `REQ-SHARED-NNN` → matrix/gate tính đúng.
6. `validate-module` (VM) pass; `npm run check:docs` xanh; **regenerate** không gây drift `src/` ↔ `_bmad/hbc/`.

## Đã đóng finding adversarial (truy vết)

| Finding | Xử lý |
|---|---|
| RED ngụy tạo / acceptance vòng tròn / C aspirational | Cụm 1=C: chấp nhận soft + **trung thực hóa nhãn** (không "guaranteed") |
| D-xx global ép per-feature | Cụm 2=A+: phân scope per-feature/shared/both (D-19,D-21 cả hai) |
| "Tương thích ngược" sai + không di trú | Cụm 3=A: bump version + script migrate + sửa claim |
| `.active` global footgun | Cụm 4=A: bỏ file global, giữ trong phiên |
| Matrix trung tâm xung đột merge | Cụm 5=A: matrix per-feature + roll-up |
| 3 bản drift | Cụm 6=A: src canonical + regenerate + CI |
| EARS chỉ cảnh báo + lẫn ngôn ngữ | Cụm 7=A: EARS keyword Anh + nội dung Việt, cảnh báo + ví dụ |
| REQ cross-feature/shared | Cụm 8=A: namespace SHARED + tham chiếu chéo |
| story_id vs feature | Cụm 9=A: feature nhóm chính, story_id link tùy chọn |
| Module sống, không version/branch; VM yếu | Cụm 10=A: branch + version + dry-run có kịch bản |
