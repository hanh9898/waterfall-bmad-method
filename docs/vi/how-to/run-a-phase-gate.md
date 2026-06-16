# Cách chạy Phase Gate

> 🌐 [English](../../en/how-to/run-a-phase-gate.md) · **Tiếng Việt**
>
> 🔧 **How-to** — hướng dẫn làm một việc cụ thể: chạy và xử lý kết quả Phase Gate. Muốn hiểu *Gate là gì*, xem [Khái niệm cốt lõi](../explanation/concepts.md#3-phase-gate--chốt-kiểm-soát-giữa-các-phase).

## Mục tiêu

Kiểm tra một phase đã hoàn thành đủ chuẩn để sang phase sau chưa.

## Chạy gate

Luôn **truyền số phase** (1–4) kèm theo lệnh:

```
PG 2
```

hoặc chạy không tương tác:

```
PG 2 -H
```

Tham số **bắt buộc**: `1` | `2` | `3` | `4` (số phase); thêm `-H` để chạy headless.

## Đọc kết quả

Gate chạy hai lớp — **kiểm tra tự động** (deliverable bắt buộc có chưa, định dạng đúng chưa) + **đánh giá LLM** (nội dung rõ, đủ, nhất quán chưa) — rồi trả báo cáo **PASSED** hoặc **FAILED**.

Báo cáo lưu ở `{output_folder}/gates` (mặc định `_bmad-output/gates`), tên dạng `phase-<n>-gate*`.

## Khi FAILED

1. Mở báo cáo gate, đọc phần liệt kê mục chưa đạt.
2. Sửa đúng deliverable được nêu (vd: D-02 thiếu tiêu chí chấp nhận → mở `REQ` chế độ `update`).
3. Chạy lại `PG <n>`.
4. Lặp đến khi **PASSED** mới sang phase sau.

> 💡 Gate "FAILED" không phải lỗi của bạn — nó đang chặn lỗi trôi xuống phase sau (nơi sửa đắt hơn nhiều).

## Mẹo

- Chạy gate **trước mỗi lần chuyển phase**, đừng để dồn đến cuối.
- Trước khi chạy `PG`, nên `TRU` để cập nhật traceability — gate cũng soi `gate_status` trong ma trận.
- Dùng `-H` khi chạy trong CI/script tự động.

## Liên quan

- 🔗 [Quản lý Traceability](manage-traceability.md)
- 🗺️ [Bản đồ quy trình](../tutorials/workflow-map.md)
