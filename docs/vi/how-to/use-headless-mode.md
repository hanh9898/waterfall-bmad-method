# Cách dùng chế độ Headless

> 🌐 [English](../../en/how-to/use-headless-mode.md) · **Tiếng Việt**
>
> 🔧 **How-to** — chạy skill HBC không cần hỏi-đáp tương tác.

## Mục tiêu

Chạy một skill ở chế độ tự động (không dừng lại hỏi bạn), phù hợp cho script, CI, hoặc khi đầu vào đã đủ rõ.

## Cú pháp

Thêm cờ `--headless` hoặc viết tắt `-H` vào cuối lệnh:

```
REQ create -H
PG 2 -H
TRU -H
```

Hầu hết skill workflow đều hỗ trợ `-H` (xem cột Args trong [Catalog skill](../reference/skills-catalog.md)).

## Khi nào nên dùng

| Tình huống | Vì sao headless hợp |
| --- | --- |
| Chạy trong CI/CD pipeline | Không có người trả lời prompt |
| Đầu vào đã đầy đủ, rõ ràng | Không cần agent hỏi thêm |
| Chạy lại hàng loạt (batch) | Tránh dừng giữa chừng |
| Tự động hóa qua script | Thực thi liền mạch |

## Khi nào **không** nên dùng

- Lần đầu tạo deliverable cần bàn bạc (vd `REQ` lần đầu) — chế độ tương tác giúp elicitation tốt hơn.
- Khi yêu cầu còn mơ hồ — để agent hỏi sẽ ra kết quả chất lượng hơn.

> 💡 Quy tắc đơn giản: **tương tác khi sáng tạo nội dung lần đầu; headless khi validate, cập nhật, hoặc chạy tự động.**

## Kết hợp với chế độ

`-H` đi kèm chế độ/đối số của skill. Ví dụ với traceability và gate:

```
TRI -H
TRU -H
PG 1 -H
```

Hoặc validate hàng loạt cuối dự án:

```
REQ validate -H
TS validate -H
```

## Liên quan

- 📖 Cột Args từng skill: [Catalog skill](../reference/skills-catalog.md)
- 🔗 [Chạy Phase Gate](run-a-phase-gate.md)
