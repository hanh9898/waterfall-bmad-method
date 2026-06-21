---
title: "D-code reconcile — căn HBC theo numbering canonical HBLAB"
status: applied
date: 2026-06-21
trigger: "Đọc templates/ (bộ canonical HBLAB D-00→D-31) → phát hiện D-08/D-17 của trục B đụng nghĩa canonical."
---

# Reconcile mã D — HBC ↔ canonical HBLAB

## Vấn đề
`templates/` chứa bộ tài liệu **canonical HBLAB** (D-00→D-31, tiếng Nhật) — chính là "bộ chuẩn rộng hơn" docs HBC vẫn viện dẫn. Trục B (2026-06-21) gán mã **đụng** canonical:

| Mã | Canonical HBLAB (`templates/`) | HBC trục B (cũ) | Vấn đề |
|---|---|---|---|
| D-07 | 運用シナリオ (Operational Scenario) | — | (không trống — đừng tái dùng cho Discovery) |
| **D-08** | 基本設計書 (Basic Design) | Architecture Design | **đụng** |
| **D-09** | アーキテクチャ設計書 (Architecture, C4) | — | đây mới là Architecture |
| **D-17** | シーケンス図 (Sequence Diagram) | Behavioral Design | **đụng** |
| D-16 | 詳細設計書 (Detailed Design) | — | host hợp lý cho behavioral |
| D-14 | 画面仕様書 (Screen Spec) | UX/Screen Design | ✅ đã khớp |

Docs HBC tự tuyên bố "mã khuyết thuộc bộ chuẩn HBLAB rộng hơn" → HBC **có ý bám numbering HBLAB**, nên D-08/D-17 lệch là **lỗi gán mã**, không cố ý.

## Quyết định (USER: hướng A — reconcile theo canonical)
- **Architecture: D-08 → D-09** (= canonical アーキテクチャ設計書; HBC vốn dùng C4/ADR → khớp tuyệt đối).
- **Behavioral Design: D-17 → D-16** (host trong canonical 詳細設計書/Detailed Design; behavioral spec ST/DR/INV/SEQ là detailed-design động). Giải phóng **D-17** trả về nghĩa canonical **Sequence Diagram**.
- **D-14 UX/Screen, D-19 ER, D-21 API, D-02/03/06/12/26/27** đã khớp — giữ nguyên.
- **Discovery/Spike (IMP-10)**: **không nằm trong canonical** → để **non-mã-D** (`discovery-note`, kiểu readiness-report), tránh đẻ thêm lệch.

## Phạm vi đã sửa (sweep có ngữ cảnh)
Đổi `D-08→D-09`, `D-17→D-16` ở **artifact authoritative**: `src/` (hbc-create-architecture, hbc-create-behavioral-design, 4 agent, module-help.csv, deliverable-catalog.yaml — gồm rename 2 template asset `D-09_architecture-design_template.md` / `D-16_behavioral-design_template.md`), toàn bộ `docs/{vi,en}`, `README*`, `MAINTAINING.md`, và spec `hbc-improvement-spec-2026-06-21.md`.

**CỐ Ý KHÔNG đổi** (D-17 ở đây = canonical Sequence, đúng sau reconcile):
- `src/hbc-create-er-diagram/references/stage-guide.md` + `SKILL.md` — off-ramp "D-17 sequence / D-18 class" giữ nguyên.
- `discover-planning-artifacts.py` — bỏ glob `D-08*.md` thừa (Architecture giờ là `D-09*.md`, đã glob sẵn).

**KHÔNG đụng** (historical/generated): `templates/` (canonical — giữ nghĩa gốc), các doc lịch sử khác trong `process-review/`, `_bmad-output/` (dogfood/log/archive). Runtime `.claude/skills/hbc-*` stale → đồng bộ khi re-install.

## Việc còn lại / theo dõi
- Dogfood `_bmad-output/features/hbc-framework-augmentation/*` vẫn ghi D-08/D-17 (generated, sẽ tự đúng khi chạy lại).
- Cân nhắc: off-ramp ER-diagram "sequence/call-flow" có thể trỏ tới **D-16 behavioral** (vì SEQ nằm trong behavioral) thay vì D-17 thuần sequence — minor, để sau.
- Re-install module sau khi merge để runtime phản ánh mã mới.
