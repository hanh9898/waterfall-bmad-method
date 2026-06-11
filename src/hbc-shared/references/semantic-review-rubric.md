# HBC Semantic Review Rubric (Lớp 1 — hợp đồng dùng chung)

> Nguyên tắc gốc: **máy lo cấu trúc · người/LLM lo ngữ nghĩa & đủ-nghĩa.**
> Validator (`hbc_validation`) đã kiểm cấu trúc và trả `verdict` với
> `semantic_review` ban đầu = `n/a`/`pending`. Bước review NGỮ NGHĨA dưới đây là
> phần con người/LLM phải làm, dùng chung cho mọi create-skill (A-2, C-2).

## Khi nào chạy

Sau khi validator cấu trúc xanh (`structure_ok = true`), create-skill chạy bước
**Semantic Review** trước khi đánh dấu tài liệu hoàn tất. Đây là Lớp 2 (nhúng
trong từng skill). Kết quả ghi vào frontmatter (A-3) và được phase-gate REVIEW
item kiểm (#5).

## Kỷ luật tách-facet (A-2)

Một REQ/chức năng thường có **nhiều mặt**. Đừng dừng ở "có ≥1 test/đề cập". Với
mỗi yêu cầu, soi qua ma trận facet và hỏi "mặt nào áp dụng, mặt đó đã được phủ
chưa?":

| Trục | Giá trị | Câu hỏi |
|---|---|---|
| Hành động | `read` / `write` | Có cả đọc lẫn ghi/biến đổi trạng thái không? Mỗi mặt đã đặc tả/test? |
| Bề mặt | `api` / `admin` / `ui` / `batch` | Logic lộ qua REST? Qua màn hình admin/back-office? Job nền? Mỗi bề mặt có chủ? |
| Vòng đời | `create` / `update` / `suspend` / `revoke` / `rotate` | Với tài nguyên có vòng đời (key, account, subscription), mỗi chuyển trạng thái đã phủ? |

Trục mở rộng được — thêm trục nếu domain cần. **Bài học seam:** khi D-21 cắt mặt
admin/write ra khỏi REST, mặt đó vẫn phải có chủ ở D-26/D-27 (test) hoặc được ghi
rõ là out-of-scope có chủ đích — không để rơi im lặng.

## Đầu ra: frontmatter `semanticReview` (A-3)

```yaml
semanticReview:
  status: passed          # pending (mặc định, chưa review) | passed | n/a
  reviewedBy: llm         # llm | human | <tên>
  date: "YYYY-MM-DD"
  openFacets: []          # facet/REQ chưa phủ; phải RỖNG thì status mới = passed
```

- `status` **chỉ** được đặt `passed` khi `openFacets` rỗng và reviewer đã thực sự
  soi đủ-nghĩa + facet. Còn nghi ngờ → để `pending` và liệt kê `openFacets`.
- `openFacets` ví dụ: `["REQ-013 mặt admin/write chưa có TC", "Màn hình duyệt key chưa có test area"]`.
- phase-gate item loại `REVIEW` đọc đúng `status` này và **chặn** nếu != `passed`.

## Phạm vi quyết định vị trí

- Ngữ nghĩa **trong 1 tài liệu** → review tại chỗ (skill này, dùng rubric này).
- Nhất quán **giữa nhiều tài liệu** (D-02 ↔ D-19/D-21/D-26/D-27/tasks) → KHÔNG
  thuộc skill đơn lẻ; để `hbc-check-implementation-readiness` (gate liên-doc, P-1)
  chạy bắt buộc trước `hbc-phase-gate` Phase 2.
