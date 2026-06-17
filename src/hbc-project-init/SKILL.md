---
name: hbc-project-init
description: "Phase 0 — tạo các deliverable dùng chung (shared) một lần trước khi làm feature. Use when user says 'project init', 'khởi tạo dự án', 'phase 0', 'tạo shared', or agent menu [PI]."
---

# Project Init (Phase 0)

## Overview

Khởi tạo **một lần** các deliverable **dùng chung toàn dự án** (shared) trước khi bắt đầu chu trình per-feature. HBC giao tăng dần theo từng tính năng; nhưng vài thứ là chung cho mọi feature và phải có sẵn từ đầu:

| Deliverable | Bắt buộc | Vị trí |
| --- | --- | --- |
| **D-12 Coding Standards** | ✅ | `{output_folder}/shared/coding-standards/` |
| **D-03 Glossary** | ✅ | `{output_folder}/shared/glossary/` |
| **D-19 ERD (baseline)** | tùy chọn | `{output_folder}/shared/erd/` |
| **D-21 API (baseline)** | tùy chọn | `{output_folder}/shared/api/` |

Idempotent: nếu deliverable shared đã tồn tại, **bỏ qua** (không ghi đè), chỉ tạo phần còn thiếu.

**Args:** `create` (default — tạo phần còn thiếu), `status` (liệt kê shared đã có/chưa). Optional: `--headless` / `-H`.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename.

## On Activation

Resolve customization, load persistent facts and config per standard BMad activation. Output in `{document_output_language}`, communicate in `{communication_language}`.

> Phase 0 **không nhận `feature`** — nó tạo artifact shared toàn dự án. Per-feature override D-19/D-21 được tạo sau bằng `hbc-create-er-diagram`/`hbc-create-api-spec` với `feature=<slug>`.

## Headless Mode

`-H` / `--headless` runs `create` / `status` non-interactively. Writes shared deliverables under `_bmad-output/shared/...` (D-12 `shared/coding-standards/`, D-03 `shared/glossary/`, D-19 baseline `shared/erd/`, D-21 baseline `shared/api/`). Idempotent — existing deliverables are skipped, never overwritten. No `feature` arg: Phase 0 is project-wide, not per-feature.

Blocked reasons (closed set):

- `missing_sources` — a mandatory shared deliverable is still missing and insufficient sources exist to generate it.

## Stages

### Stage 1: Status

Quét `{workflow.shared_dir}` xem deliverable shared nào đã có:
- D-12: `{output_folder}/shared/coding-standards/D-12-*`
- D-03: `{output_folder}/shared/glossary/D-03-*`
- D-19 baseline: `{output_folder}/shared/erd/D-19-*`
- D-21 baseline: `{output_folder}/shared/api/D-21-*`

Trình bảng "đã có / còn thiếu". Nếu `status` arg → dừng ở đây.

### Stage 2: Create missing (idempotent)

Với mỗi deliverable shared **còn thiếu**, mời/điều phối tạo qua create-skill tương ứng (chúng đã ghi vào `shared/`):
- D-12 → `hbc-create-coding-standards` (bắt buộc)
- D-03 → `hbc-create-glossary` (bắt buộc)
- D-19 baseline → `hbc-create-er-diagram` (tùy chọn — bỏ qua nếu chưa cần)
- D-21 baseline → `hbc-create-api-spec` (tùy chọn)

**Không ghi đè** deliverable đã tồn tại. Trong headless: tạo các deliverable bắt buộc còn thiếu nếu đủ nguồn, ngược lại trả `blocked` (`missing_sources`).

### Stage 3: Handoff

_"Phase 0 xong — shared deliverables sẵn sàng. Bắt đầu feature đầu tiên: mở `hbc-agent-ba` ([BA]) với một feature slug, rồi `hbc-create-requirements` (feature=<slug>)."_

Headless: trả JSON `{status, created, skipped, missing}`.
