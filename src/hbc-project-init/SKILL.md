---
name: hbc-project-init
description: "Phase 0 — khởi tạo dự án + tạo các deliverable dùng chung (shared) một lần trước khi làm feature. Use when user says 'project init', 'khởi tạo dự án', 'phase 0', 'tạo shared', or agent menu [PI]."
---

# Project Init (Phase 0)

## Overview

Phase 0 chạy **một lần, bắt buộc, TRƯỚC** mọi tính năng (hoặc chạy lại để update trực tiếp). Nó làm hai việc: **(1) hiểu dự án** (đặc biệt khi cài vào codebase có sẵn — brownfield), rồi **(2) tạo các deliverable dùng chung** (shared) làm nền cho mọi feature.

| Deliverable | Bắt buộc | Vị trí |
| --- | --- | --- |
| **D-12 Coding Standards** | ✅ | `{output_folder}/shared/coding-standards/` |
| **D-03 Glossary** | ✅ | `{output_folder}/shared/glossary/` |
| **D-19 ERD (baseline)** | tùy chọn | `{output_folder}/shared/erd/` |
| **D-21 API (baseline)** | tùy chọn | `{output_folder}/shared/api/` |

Idempotent: deliverable shared đã tồn tại thì **bỏ qua** (không ghi đè), chỉ tạo phần còn thiếu. Chạy lại để update trực tiếp khi cần.

**Args:** `create` (default — hiểu dự án + tạo phần còn thiếu), `status` (chỉ liệt kê shared + project-context đã có/chưa). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> Phase 0 **không nhận `feature`** — nó tạo artifact shared toàn dự án. Per-feature override D-19/D-21 được tạo sau bằng `hbc-create-er-diagram`/`hbc-create-api-spec` với `feature=<slug>`.

## Headless Mode

`-H` / `--headless` runs `create` / `status` non-interactively (full I/O contract — input args, return schema, blocked reasons: `references/headless-contract.md`). Detects brownfield vs greenfield deterministically (codebase presence), uses any existing project documentation as source, then writes shared deliverables under `_bmad-output/shared/...`. Idempotent — existing deliverables are skipped. No `feature` arg.

Blocked reasons (closed set):

- `missing_sources` — a mandatory shared deliverable is still missing and there are insufficient sources (no project-context, no codebase, no PRD/brief) to generate it.

## Stages

### Stage 1: Status

Quét trạng thái nền của dự án:
- **Project context:** `project-context.md` (BMad AI rules/context) đã có chưa? Tài liệu dự án `{project_knowledge}/index.md` (output của `bmad-document-project`) đã có chưa?
- **Shared deliverables:** D-12 `{output_folder}/shared/coding-standards/D-12-*` · D-03 `{output_folder}/shared/glossary/D-03-*` · D-19 baseline `{output_folder}/shared/erd/D-19-*` · D-21 baseline `{output_folder}/shared/api/D-21-*`.

Trình bảng "đã có / còn thiếu". Nếu `status` arg → dừng ở đây.

**Phát hiện layout LEGACY (v1).** Cũng quét dấu hiệu output HBC v1 (layout phẳng): tồn tại `_bmad-output/planning-artifacts/D-*`, hoặc `_bmad-output/traceability/matrix*` mà KHÔNG có thư mục `_bmad-output/features/`. Nếu phát hiện → **khuyến nghị chạy `hbc-migrate` ([MIG]) TRƯỚC** khi tạo bất kỳ shared deliverable nào: migrate sẽ di chuyển các artifact phẳng sang `shared/` + `features/<feature>/` và re-prefix REQ/TC. Tạo shared ngay bây giờ sẽ gây **trùng lặp** (double-creation) với những gì migrate sắp dựng. Báo cảnh báo này rồi dừng (để user chạy [MIG] xong mới quay lại PI cho phần shared còn thiếu).

### Stage 2: Hiểu dự án (brownfield-aware)

Xác định loại dự án rồi đảm bảo có đủ **context** để seed shared deliverables — thay vì tạo từ con số 0:

1. **Phân loại brownfield vs greenfield.** Brownfield = đã có codebase (mã nguồn ngoài `_bmad/`, `docs/`, `_bmad-output/`). Greenfield = dự án mới, chưa có code.
2. **Đảm bảo `project-context.md`.** Nếu chưa có, điều phối `bmad-generate-project-context` để tạo (AI rules + bối cảnh dự án). Đây là persistent fact mọi skill HBC dựa vào.
3. **Brownfield — document dự án trước.** Nếu là brownfield và chưa có tài liệu dự án (`{project_knowledge}/index.md`), điều phối **`bmad-document-project`** để quét codebase (kiến trúc, schema DB, endpoint, convention code) → tài liệu context. Đây là **nguồn** để rút ra shared deliverables: convention code → D-12, schema → baseline D-19, endpoint → baseline D-21.
4. **Greenfield — lấy context từ nguồn khác.** Dùng PRD/brief/`project-context.md` nếu có; nếu không, hỏi user ngắn gọn về stack + domain.

Headless: phân loại tự động; nếu brownfield mà thiếu tài liệu dự án, vẫn tiếp tục nhưng ghi chú nguồn hạn chế; thiếu hẳn mọi nguồn cho deliverable bắt buộc → `blocked` (`missing_sources`).

### Stage 3: Create missing (idempotent)

Với mỗi deliverable shared **còn thiếu**, điều phối create-skill tương ứng, **truyền context từ Stage 2** (brownfield: rút từ codebase/tài liệu dự án; greenfield: từ PRD/brief/lựa chọn):
- D-12 → `hbc-create-coding-standards` (bắt buộc) — brownfield: trích convention từ code hiện có.
- D-03 → `hbc-create-glossary` (bắt buộc) — từ domain/tài liệu dự án.
- D-19 baseline → `hbc-create-er-diagram` (tùy chọn) — brownfield: reverse từ schema DB hiện có.
- D-21 baseline → `hbc-create-api-spec` (tùy chọn) — brownfield: từ endpoint hiện có.

**Không ghi đè** deliverable đã tồn tại. Headless: tạo deliverable bắt buộc còn thiếu nếu đủ nguồn, ngược lại `blocked` (`missing_sources`).

### Stage 4: Handoff

_"Phase 0 xong — dự án đã có project-context + shared deliverables. Bắt đầu feature đầu tiên: mở `hbc-agent-ba` ([BA]) với một feature slug, rồi `hbc-create-requirements` (feature=<slug>)."_

Headless: trả JSON `{status, project_type, project_context, documented, created, skipped, missing}`.
