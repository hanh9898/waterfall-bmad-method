# Establish Active Feature (B)

Canonical procedure for resolving the **active feature** at the start of an HBC
agent session. HBC giao tăng dần **theo từng tính năng** — xác lập active feature
một lần đầu phiên rồi giữ suốt phiên.

## Resolve

1. **Source order:** arg `feature=<slug>` → session value (đã xác lập trước đó) →
   hỏi user (kebab-case, vd `change-password`).
2. **Validate** slug against `^[a-z0-9][a-z0-9-]*$`. Reject and re-ask if invalid.
3. **Headless** (`-H` / `--headless` / `{agent.headless_default}`): feature là
   **bắt buộc** — không có nguồn nào cung cấp → return `status: blocked`,
   `reason: feature_required`. Không được hỏi tương tác ở headless.

## Carry forward

- **Truyền `feature=<slug>`** cho MỌI per-feature skill bạn dispatch
  (REQ/BFD/ERD/API/TP/TS/TB/IM/TE/AC/PG/TR…) — kèm cùng context capsule.
- Giữ active feature ổn định suốt phiên; nếu mất context (sau compaction),
  khôi phục lại trước khi dispatch tiếp.

## Path layout

- Artifact per-feature: `{output_folder}/features/{feature}/…`
- Deliverable **shared** (D-12 Coding Standards, D-03 Glossary; baseline D-19/D-21):
  `{output_folder}/shared/…` — KHÔNG truyền `feature` cho các skill shared
  (GLO, CS; ERD/API khi ghi baseline).

## Phase 0 reminder

Nếu `shared/coding-standards/D-12-*` hoặc `shared/glossary/D-03-*` chưa có, gợi ý
chạy `hbc-project-init` ([PI]) tạo shared deliverables trước khi bắt đầu feature đầu tiên.
