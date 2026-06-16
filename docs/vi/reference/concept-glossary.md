# Glossary khái niệm

> 🌐 [English](../../en/reference/concept-glossary.md) · **Tiếng Việt**
>
> 📖 **Reference** — gặp một từ lạ trong tài liệu HBC? Tra ở đây. Mỗi mục là một câu định nghĩa ngắn (answer-first) kèm link đọc sâu.
>
> ℹ️ Đây là glossary của **khái niệm HBC**. Nếu bạn tìm bảng tra **mã deliverable** (D-02, D-19…), xem [Bảng deliverable D-xx](deliverables-glossary.md). Đừng nhầm với *D-03 Glossary* — đó là glossary thuật ngữ **nghiệp vụ của dự án bạn**, do bạn sinh ra, không phải giải thích HBC.

## Quy trình & vòng đời

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **Waterfall** | Mô hình làm tuần tự: xong phase này mới sang phase kế, không nhảy cóc. | [Vì sao Waterfall + TDD](../explanation/why-waterfall-tdd.md) |
| **Phase** | Một trong 4 chặng có thứ tự của HBC: Analysis → Design → Implementation → Testing. | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Deliverable** | Sản phẩm bàn giao được của một phase (tài liệu hoặc code), thường đánh mã `D-xx`. | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Phase Gate** | Chốt kiểm soát ở ranh giới mỗi phase — phải "pass" mới được sang phase sau (lệnh `PG <n>`). | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Entry/Exit criteria** | Điều kiện *vào* và *ra* của một phase — tiêu chí để bắt đầu và để được coi là hoàn thành. | [Bảng deliverable (D-26)](deliverables-glossary.md) |

## Truy vết (Traceability)

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **Traceability** | Việc nối mỗi yêu cầu tới thiết kế, code và test của nó — để không bỏ sót yêu cầu nào. | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Traceability matrix** | Bảng thực hiện việc truy vết đó: mỗi dòng một yêu cầu, các cột là design/code/test. | [Quản lý Traceability](../how-to/manage-traceability.md) |
| **REQ ID** | Mã định danh một yêu cầu (vd `REQ-001`), sinh ở D-02, dùng làm "neo" cho mọi truy vết. | [D-02 Requirements](deliverables-glossary.md) |
| **TC ID** | Mã định danh một test case (vd `TC-001`), sinh ở D-27. | [D-27 Test Spec](deliverables-glossary.md) |
| **Coverage (độ phủ)** | Tỉ lệ yêu cầu đã có đủ chuỗi truy vết (thiết kế + code + test). | [Quản lý Traceability](../how-to/manage-traceability.md) |

## Lập trình & kiểm thử

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **TDD** | Test-Driven Development: **viết test trước**, rồi mới viết code cho test đó pass. | [Vì sao Waterfall + TDD](../explanation/why-waterfall-tdd.md) |
| **RED → GREEN → REFACTOR** | Chu trình TDD: 🔴 viết test thấy fail → 🟢 viết code tối thiểu cho pass → ♻️ dọn code, test vẫn xanh. | [Vì sao Waterfall + TDD](../explanation/why-waterfall-tdd.md) |
| **ERD (ER Diagram)** | Sơ đồ quan hệ thực thể — mô tả các bảng dữ liệu và liên kết giữa chúng (deliverable D-19). | [D-19 Database Design](deliverables-glossary.md) |
| **Triage (lỗi)** | Phân loại và xếp ưu tiên các lỗi tìm được, để xử lý cái quan trọng trước. | [Bảng deliverable](deliverables-glossary.md) |
| **Deterministic** | "Cho kết quả cố định" — kiểm tra tự động bằng quy tắc cứng (có/không), không phụ thuộc đánh giá chủ quan. | [Khái niệm cốt lõi](../explanation/concepts.md) |

## Nghiệm thu (Acceptance)

| Thuật ngữ | Định nghĩa ngắn |
| --- | --- |
| **Acceptance** | Đánh giá cuối: tính năng có đạt yêu cầu để bàn giao không (lệnh `AC review`). |
| **ACCEPTED** | Đạt — chấp nhận bàn giao. |
| **REJECTED** | Không đạt — có lỗi/thiếu sót phải sửa rồi đánh giá lại. |
| **DEFERRED** | Tạm hoãn — chấp nhận có điều kiện, phần còn thiếu để lại xử lý sau (đã thống nhất). |
| **PENDING** | Chưa quyết — còn chờ thông tin/kết quả để ra quyết định. |

## Liên quan

- 💡 Hiểu sâu 4 khái niệm nền tảng: [Khái niệm cốt lõi](../explanation/concepts.md).
- 📖 Tra mã deliverable: [Bảng deliverable D-xx](deliverables-glossary.md).
- 📖 Tra skill: [Catalog skill](skills-catalog.md).
