---
name: hbc-migrate
description: "Migrate (di chuyển output) một dự án HBC v1 (layout flat) sang layout v2 per-feature + shared. dry-run plan → confirm → apply; idempotent. Use when user says 'migrate', 'migrate v1', 'di chuyển output', 'nâng cấp layout', or agent menu [MIG]."
---

# Migrate v1 → v2 (Phase 0)

## Overview

Chuyển dự án đã chạy **HBC v1** (output flat: `_bmad-output/{planning-artifacts,implementation-artifacts,gates,traceability}/`, id `REQ-NNN`, matrix 7 cột) sang **v2**: per-feature `_bmad-output/features/<feature>/{…}/` + shared `_bmad-output/shared/{coding-standards,glossary,erd,api}/`, id `REQ-<FEAT>-NNN`, matrix 8 cột. Một lần, **destructive** (di chuyển file) → mặc định **dry-run**, chỉ `apply` mới ghi.

**Args:** `plan` (default — dry-run preview, không ghi), `apply` (thực thi). Optional: `feature=<slug>`, `--apply`, `--force`, `-H` / `--headless`.

Orchestrate engine: `{project-root}/_bmad/scripts/migrate-to-feature-layout.py` (dry-run default, `--apply`, `--feature`, `--reprefix`, `--json`, `--timestamp`, `--force`). Determinism (move/re-prefix/rebuild matrix/backup) sống trong script; phán đoán (feature nào? shared hay per-feature? tách multi-feature?) sống ở skill.

## Conventions

- Bare paths resolve from the skill root. `{skill-root}` = installed dir. `{project-root}`-prefixed from project. `{skill-name}` = basename. Output viết bằng `{document_output_language}`, giao tiếp bằng `{communication_language}`.

## On Activation

Resolve customization, load persistent facts + config per standard BMad activation.

> Không namespacing `feature` ở output — skill **rewrite `_bmad-output/` tại chỗ**. `feature=<slug>` chỉ dùng để gán prefix REQ/TC + route per-feature.

## Headless Mode

`-H` runs `plan` (default) / `apply` non-interactively. Full I/O contract — args, return schema, blocked reasons: `references/headless-contract.md`. `apply` headless cần `feature=<slug>` + `--apply`; mặc định headless = plan JSON (`--json`). Idempotent.

Blocked reasons (closed set): `feature_required` · `multi_feature_ambiguous` · `nothing_to_migrate` · `dirty_worktree`.

## Stages

### Stage 1: Detect & Classify

Chạy engine ở chế độ scan (dry-run, `--json`). Phát hiện layout flat hợp lệ: `planning-artifacts/D-*`, flat `implementation-artifacts/`, `gates/`, `traceability/matrix*` (7 cột), id `REQ-NNN`. Classify mỗi artifact → **shared** vs **per-feature**.

**Idempotent:** nếu đã v2 (hoặc không có gì legacy) → report "nothing to migrate" và **dừng** (headless: `blocked: nothing_to_migrate`).

### Stage 2: Plan (judgment)

Route:
- **shared/** → D-12 (coding-standards), D-03 (glossary), baseline D-19 (erd), D-21 (api).
- **features/<feature>/** → D-02, D-06, D-26, D-27, task-breakdown, gates, matrix.

**Resolve feature:** single-project flat docs → hỏi user / dùng `feature=<slug>` (headless thiếu → `blocked: feature_required`). **Multi-feature** flat docs (REQ của nhiều feature trong một D-02) → **cảnh báo** + offer tách: v1 yêu cầu một `--feature` mỗi lần chạy (hoặc tách thủ công); headless không tự suy luận được → `blocked: multi_feature_ambiguous`.

Không double-create: nếu `shared/` đã có (PI đã chạy) → giữ nguyên, không ghi đè.

### Stage 3: Dry-run preview (default)

Với action `plan`: gọi engine `--json` (không `--apply`) → in **toàn bộ plan**: từng `src → dst`, bản đồ re-prefix `REQ-NNN → REQ-<FEAT>-NNN` **và** `TC-NNN`, plan rebuild matrix 7→8 cột (chèn cột `feature`). **Không ghi.** User review rồi xác nhận để sang `apply`.

### Stage 4: Apply (`apply` / `--apply`)

Chỉ chạy khi action `apply` (hoặc `--apply`). Engine:
1. **Dirty-guard:** worktree git có thay đổi chưa commit → từ chối (headless: `blocked: dirty_worktree`), trừ khi `--force`.
2. **Backup** trước khi move (`.archive/<ts>/`, `--timestamp`).
3. Move file theo plan; **re-prefix REQ và TC** trong D-02/D-26/D-27/matrix đã move (`--reprefix`).
4. **Rebuild matrix 8 cột** (chèn cột `feature`).
5. Ghi **decision-log** mọi thay đổi.

Idempotent: artifact đã v2 → skip.

### Stage 5: Verify & Handoff

Chạy validators trên artifact đã migrate + `trace-report.py --d02` (d02-sync) + readiness `[IR]` (`hbc-check-implementation-readiness`). Report pass/gaps. Handoff:

_"Migrate xong → layout v2. Nếu shared còn thiếu, chạy `[PI]` (`hbc-project-init`). Sau đó tiếp tục per-feature: `[BA]` / `hbc-create-requirements` với `feature=<slug>`."_

Headless: trả JSON theo `references/headless-contract.md` (`status`, `moves`, `reprefix`, `matrix`, `validation`, hoặc `blocked` + `reason`).
