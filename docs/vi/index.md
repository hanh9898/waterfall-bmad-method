# Tài liệu HBC

> 🌐 [English](../en/index.md) · **Tiếng Việt** · [⬅ Chọn ngôn ngữ](../index.md)

Tài liệu **HBLAB BMad Custom (HBC)** tổ chức theo mô hình [Divio](https://docs.divio.com/documentation-system/) — chọn theo nhu cầu của bạn.

HBC giao **tăng dần theo từng tính năng** (incremental per-feature delivery): mỗi tính năng đi trọn 4 phase + TDD rồi ship độc lập. Trước tiên chạy **Phase 0 — Project Init** một lần cho cả dự án (`hbc-project-init`) để dựng các deliverable dùng chung.

> 💡 Mới hoàn toàn? Bắt đầu từ [Khởi động nhanh 10 phút](tutorials/quickstart.md). Bí lúc nào thì gõ `bmad-help`.

## 📘 Tutorials — học qua làm

Dành cho người mới, muốn được dắt tay từng bước.

- [Khởi động nhanh (10 phút)](tutorials/quickstart.md) — **bắt đầu ở đây**: cài đặt → xác nhận chạy → tạo D-02 đầu tiên.
- [Bắt đầu với HBC (walkthrough)](tutorials/getting-started-hbc.md) — chạy Phase 0 một lần, rồi đưa một tính năng đi trọn 4 phase.
- [Bản đồ quy trình](tutorials/workflow-map.md) — toàn cảnh Phase 0 + 4 phase per-feature, agent, skill, deliverable trong một trang *(nên đọc sau khi đã chạy thử lần đầu)*.

## 💡 Explanation — hiểu vì sao

Dành cho người muốn nắm tư duy đằng sau.

- [Khái niệm cốt lõi](explanation/concepts.md) — Phase 0, Phase Gate, Deliverable D-xx, phạm vi (per-feature·shared·dual), Traceability.
- [Vì sao Incremental + TDD](explanation/why-incremental-tdd.md) — lựa chọn nền tảng của HBC: giao tăng dần per-feature, test-first với bằng chứng RED.

## 🔧 How-to — giải quyết một việc cụ thể

Dành cho người đã chạy được, cần làm một tác vụ.

- [Chạy Phase Gate](how-to/run-a-phase-gate.md)
- [Quản lý Traceability](how-to/manage-traceability.md)
- [Dùng chế độ Headless](how-to/use-headless-mode.md)
- [Tùy chỉnh cấu hình](how-to/customize-config.md)

## 📖 Reference — tra cứu nhanh

Dành cho lúc cần tra mã/cú pháp.

- [Glossary khái niệm](reference/concept-glossary.md) — gặp từ lạ (deliverable, phase gate, traceability, TDD…)? tra ở đây.
- [Catalog skill](reference/skills-catalog.md) — mọi agent & skill kèm chế độ chạy.
- [Bảng deliverable D-xx](reference/deliverables-glossary.md) — mọi tài liệu HBC sinh ra.

---

[⬆ README dự án](../../README.md)
