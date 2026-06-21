---
document_id: D-06
title: "OPMS Project Invoice — Lập kế hoạch nguồn lực & tạo Billable — Sơ đồ luồng nghiệp vụ"
version: "2.3"
status: draft
mode: migration
diagram_type: ["sequenceDiagram", "flowchart", "stateDiagram"]
inputDocuments:
  - "_bmad-output/features/resource-plan-billable/planning-artifacts/D-02-resource-plan-billable.md"
  - "_bmad-output/planning-artifacts/D-03-resource-plan-billable-glossary.md"
stage_2_actors: ["Delivery Manager", "Department Manager", "Invoice Manager", "QA", "Sales", "Kế hoạch nguồn lực", "Phân bổ nhân sự", "Billable (hóa đơn nội bộ theo tháng)", "Bảng tổng hợp nguồn lực", "Google Sheet (AS-IS)"]
stage_2_flows: ["AS-IS — Billable thủ công qua Google Sheet", "TO-BE — Lập kế hoạch nguồn lực, duyệt 2 cấp và tạo billable", "TO-BE chi tiết — Nhập kế hoạch và cập nhật phân bổ nhân sự + bảng tổng hợp", "TO-BE — Tạo billable & bảo vệ tháng đã chốt", "Vòng đời yêu cầu duyệt (2 cấp) + luồng billable sau khi tạo", "Nạp dữ liệu lần đầu cài đặt"]
stepsCompleted: ["stage-1", "stage-2", "stage-3", "stage-4", "stage-5"]
lastStep: "complete"
updated: "2026-06-19"
semanticReview:
  status: passed
  reviewedBy: llm
  date: "2026-06-18"
  openFacets: []
---

# D-06 Sơ đồ luồng nghiệp vụ — Lập kế hoạch nguồn lực & tạo Billable

> Phạm vi: quy trình **lập kế hoạch nguồn lực** trên OPMS và **tạo billable** (hóa đơn nội bộ theo tháng) từ kế hoạch. Bối cảnh: chuyển đổi từ cách làm cũ trên **Google Sheet (AS-IS)** sang làm trực tiếp trên **OPMS (TO-BE)**.
>
> **Điểm chính của quy trình mới:**
> - **Kế hoạch nguồn lực** sửa được bất kỳ lúc nào. Mỗi lần cần duyệt, Delivery Manager **trình một yêu cầu duyệt** kèm một **bản chốt số liệu** (không sửa được) tại thời điểm trình.
> - **Duyệt 2 cấp**: Department Manager duyệt cấp 1 → Invoice Manager duyệt cấp 2. Duyệt cấp 2 xong, hệ thống **tự tạo billable** từ bản chốt.
> - Billable theo tháng đi theo một **luồng duyệt riêng**: QA rà soát và trình, Delivery Manager / Quản trị / Invoice Manager duyệt cuối.
> - Các tháng **đã chốt** (đã duyệt / đã gửi / đã thanh toán / đã khóa) được **bảo vệ**, không bị ghi đè — hệ thống chỉ **báo chênh lệch**.
> - **Bảng tổng hợp nguồn lực** luôn cập nhật theo kế hoạch.
>
> **Vai trò người dùng (REQ-RESOURCE-PLAN-BILLABLE-020, 036, 038):**
> - **Delivery Manager** — lập kế hoạch nguồn lực và trình duyệt. Chỉ thấy/sửa kế hoạch của các dự án mình phụ trách (theo nhóm Delivery) (REQ-020).
> - **Department Manager** — duyệt cấp 1; chỉnh sửa các dòng nhân sự thuộc bộ phận mình.
> - **Invoice Manager** — duyệt cấp 2, duyệt billable cuối, toàn quyền chỉnh sửa/xóa billable.
> - **QA** — rà soát và trình billable **chưa chốt**; được **sửa nhưng không được xóa**; không lập kế hoạch nguồn lực, không tự duyệt cuối (REQ-036, REQ-038).

## 1. Luồng nghiệp vụ: Lập kế hoạch nguồn lực & tạo Billable

### AS-IS (Hiện tại)

Hiện tại các bộ phận nhập kế hoạch nguồn lực trên Google Sheet, tổng hợp và tạo billable thủ công.

```mermaid
sequenceDiagram
    actor Dept as Bộ phận
    participant Sheet as GoogleSheet
    actor IM as InvoiceManager
    participant OPMS as OPMS
    actor Sales as Sales

    Dept->>Sheet: Nhập kế hoạch nguồn lực thủ công
    Note over Sheet: Dữ liệu phân tán, nhiều bản, dễ sai lệch
    IM->>Sheet: Tổng hợp số liệu hàng tháng
    IM->>OPMS: Nhập / tạo billable thủ công theo từng tháng
    Sales->>OPMS: Cung cấp số liệu doanh thu
    IM->>OPMS: Đối soát billable với doanh thu thủ công
    OPMS-->>IM: Kết quả billable
```

**Vấn đề AS-IS:** thao tác thủ công, dữ liệu tách rời khỏi OPMS, khó truy vết khi kế hoạch thay đổi, rủi ro lệch giữa kế hoạch nguồn lực và phân bổ thực tế, không có quy trình duyệt chuẩn hóa.

### TO-BE (Mục tiêu) — Lập kế hoạch, duyệt 2 cấp và tạo billable

Nhập kế hoạch nguồn lực trực tiếp trên OPMS, cập nhật phân bổ nhân sự một chiều, **duyệt 2 cấp**, sau đó hệ thống **tự tạo billable**.

```mermaid
sequenceDiagram
    actor DelM as DeliveryManager
    actor DeptM as DepartmentManager
    actor IM as InvoiceManager
    actor QA as QA
    participant Plan as KeHoachNguonLuc
    participant Req as YeuCauDuyet va BanChot
    participant Bill as Billable
    participant Sum as BangTongHop

    DelM->>Plan: Lập/sửa kế hoạch nguồn lực bất kỳ lúc nào (REQ-042)
    Plan-->>DelM: Gợi ý sẵn từ phân bổ hiện có (cửa sổ 8 tháng), nhập MM và đơn giá (REQ-003/007/008/009/010)
    Note over Plan: Kế hoạch tự cập nhật phân bổ nhân sự (một chiều) (REQ-011/012/013)
    DelM->>Req: Trình duyệt (chỉ Delivery Manager) tạo yêu cầu kèm bản chốt số liệu (REQ-040)
    Note over Req: Mỗi kế hoạch chỉ 1 yêu cầu đang xử lý, sửa kế hoạch tiếp không đổi bản chốt
    DeptM->>Req: Duyệt cấp 1 — xem bản chốt (REQ-024)
    Note over DeptM,Req: Trả lại hoặc Thu hồi đều kết thúc yêu cầu, có thể tự duyệt
    IM->>Req: Duyệt cấp 2 — kiểm tra bản chốt còn nguyên vẹn (REQ-041)
    Req->>Bill: Tạo billable từ bản chốt, bỏ qua tháng đã chốt (REQ-014/016/022)
    Bill-->>IM: Billable nháp theo tháng (thành tiền = MM x đơn giá), báo tháng bỏ qua + chênh lệch (REQ-015/018/037)
    Req->>Sum: Cập nhật bảng tổng hợp từ bản chốt (REQ-029/041)
    QA->>Bill: Rà soát và trình billable chưa chốt (REQ-038)
    IM->>Bill: Duyệt billable cuối — Delivery Manager/Quản trị/Invoice Manager (REQ-038)
```

**Khác biệt AS-IS → TO-BE:**
- Nguồn nhập chuyển từ Google Sheet sang kế hoạch nguồn lực trên OPMS (REQ-RESOURCE-PLAN-BILLABLE-001, REQ-RESOURCE-PLAN-BILLABLE-002).
- Bổ sung **vòng đời duyệt 2 cấp** (Delivery lập + trình → Department Manager duyệt cấp 1 → Invoice Manager duyệt cấp 2), có Trả lại và tự duyệt (REQ-RESOURCE-PLAN-BILLABLE-024) — không có ở AS-IS.
- Tổng hợp + tạo billable thủ công → hệ thống **tự tạo billable** sau khi duyệt cấp 2: tìm hoặc tạo billable nháp của tháng (mỗi dự án chỉ một billable mỗi tháng), thay các dòng chưa chốt bằng số liệu từ bản chốt (REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-015, REQ-RESOURCE-PLAN-BILLABLE-016, REQ-RESOURCE-PLAN-BILLABLE-022).
- Bổ sung **luồng duyệt riêng của billable** sau khi tạo: **QA rà soát và trình**, **Delivery Manager / Quản trị / Invoice Manager duyệt cuối** (REQ-RESOURCE-PLAN-BILLABLE-038).
- Bổ sung **cập nhật phân bổ nhân sự một chiều** từ kế hoạch (REQ-RESOURCE-PLAN-BILLABLE-011..REQ-RESOURCE-PLAN-BILLABLE-013, REQ-RESOURCE-PLAN-BILLABLE-023) và **bảng tổng hợp nguồn lực luôn cập nhật theo kế hoạch** (REQ-RESOURCE-PLAN-BILLABLE-028, REQ-RESOURCE-PLAN-BILLABLE-029) — không có ở AS-IS.
- Bổ sung **bảo vệ tháng đã chốt**, cơ chế ghi đè có xác nhận và **báo chênh lệch** khi kế hoạch lệch so với billable đã chốt (REQ-RESOURCE-PLAN-BILLABLE-016..REQ-RESOURCE-PLAN-BILLABLE-018, REQ-RESOURCE-PLAN-BILLABLE-033, REQ-RESOURCE-PLAN-BILLABLE-037, REQ-RESOURCE-PLAN-BILLABLE-039).

## 2. Luồng nghiệp vụ: Nhập kế hoạch & cập nhật phân bổ nhân sự (TO-BE chi tiết)

```mermaid
sequenceDiagram
    actor DM as DeliveryManager
    actor DeptM as DepartmentManager
    participant Plan as KeHoachNguonLuc
    participant Alloc as PhanBoNhanSu
    participant Sum as BangTongHop

    DM->>Plan: Mở kế hoạch dự án (mặc định 8 tháng, chỉ dự án mình phụ trách) (REQ-003, REQ-020, REQ-032)
    Plan->>Alloc: Lấy phân bổ hiện có trong khoảng thời gian
    Alloc-->>Plan: Phân bổ hiện có
    Plan-->>DM: Gợi ý sẵn các dòng — Bộ phận/Vai trò/Phân bổ/Đơn giá/Tiền tệ, HB/BU (REQ-006, REQ-007, REQ-010, REQ-030, REQ-031)
    DM->>Plan: Thêm dòng, chọn nhân viên đã duyệt (REQ-005), chọn đơn giá (REQ-008), nhập MM (REQ-009)
    alt Tháng đã có billable chốt
        Plan-->>DM: Chặn — "billable đã duyệt, cần mở lại billable trước" (REQ-033)
    else Tháng chưa chốt
        Plan->>Alloc: Tạo phân bổ tương ứng (REQ-011)
    end
    DM->>Plan: Sửa tỷ lệ phân bổ / khoảng thời gian của một dòng
    Plan->>Alloc: Cập nhật tỷ lệ phân bổ / khoảng thời gian (REQ-012)
    DeptM->>Plan: Xóa một dòng (chỉ dòng thuộc bộ phận mình) (REQ-020)
    Plan->>Alloc: Kết thúc phân bổ (giữ lịch sử, không xóa cứng) (REQ-013)
    Note over Plan,Sum: Bảng tổng hợp luôn cập nhật theo kế hoạch — thêm/sửa/xóa dòng phản ánh ngay (REQ-028, REQ-029)
    Note over Plan,Alloc: Sửa phân bổ ngoài kế hoạch KHÔNG đồng bộ ngược về kế hoạch (REQ-023)
    Note over Plan,Alloc: Chỉ cập nhật phân bổ khi người dùng có quyền (REQ-025)
    Plan-->>DM: Lưu kế hoạch — tránh hai người lưu đè lên nhau (REQ-027)
```

## 3. Luồng nghiệp vụ: Tạo Billable (có nhiều nhánh quyết định)

> **Tạo billable diễn ra tự động khi yêu cầu được duyệt cấp 2** (không phải nút bấm riêng): hệ thống kiểm tra bản chốt còn nguyên vẹn, **khóa kế hoạch** để tránh hai lần duyệt song song, rồi với mỗi tháng trong bản chốt — tìm hoặc tạo billable của tháng (mỗi dự án chỉ một billable mỗi tháng), thay các dòng chưa chốt bằng số liệu từ bản chốt. Tháng **đã chốt** bị bỏ qua kèm **báo chênh lệch**; tháng chưa chốt nhưng đã có dữ liệu cần **xác nhận ghi đè**. Chạy lại nhiều lần vẫn an toàn (không nhân đôi).

```mermaid
flowchart TD
    Start(["Duyệt cấp 2 — kích hoạt tạo billable — REQ-041"]) --> Hash{"Bản chốt còn nguyên vẹn? — REQ-041"}
    Hash -- "Không" --> Err["Báo lỗi, dừng"]
    Hash -- "Có" --> Lock["Khóa kế hoạch chống duyệt song song + ghi nhận bản duyệt hiện hành — REQ-041"]
    Lock --> V{"Bản chốt hợp lệ? — REQ-021"}
    V -- "Không" --> Err
    V -- "Có" --> FOC["Mỗi tháng trong bản chốt: tìm hoặc tạo billable của tháng (mỗi dự án 1 billable/tháng) — REQ-014"]
    FOC --> State{"Trạng thái billable của tháng? — REQ-016, REQ-018, REQ-037"}
    State -- "Đã duyệt / đã gửi / đã thanh toán" --> SkipHave["Bỏ qua + báo đã có"]
    State -- "Đã khóa" --> SkipLock["Bỏ qua + báo đã khóa"]
    State -- "Mới tạo (chưa có dòng)" --> Gen
    State -- "Nháp / rà soát / đã trình (đã có dòng)" --> Confirm{"Xác nhận ghi đè? — REQ-017"}
    Confirm -- "Hủy" --> Keep["Giữ nguyên tháng này"]
    Confirm -- "Đồng ý" --> Unlink["Bỏ các dòng chưa chốt của tháng (kể cả người đã rời kế hoạch) — REQ-016, REQ-026"]
    Unlink --> Gen["Tạo lại dòng billable theo số liệu bản chốt (MM, đơn giá, tỷ lệ) — REQ-014, REQ-022"]
    Gen --> Amt["Tính thành tiền = MM x đơn giá (theo bản chốt) — REQ-015"]
    Amt --> Next{"Còn tháng kế tiếp?"}
    SkipHave --> Next
    SkipLock --> Next
    Keep --> Next
    Next -- "Có" --> State
    Next -- "Không" --> Done(["Báo cáo kết quả: tháng đã tạo / bỏ qua"])
    Done --> Period["Billable ở trạng thái Nháp đi vào luồng duyệt riêng: QA trình, Invoice Manager duyệt cuối — REQ-038"]
```

## 4. Vòng đời yêu cầu duyệt (2 cấp) + luồng billable sau khi tạo

> **Kế hoạch nguồn lực không có trạng thái duyệt** — Delivery Manager sửa bất kỳ lúc nào (REQ-042). Vòng đời duyệt 2 cấp nằm ở **yêu cầu duyệt** (mỗi lần trình là một yêu cầu kèm bản chốt không đổi). Yêu cầu được **duyệt cấp 2 mới nhất** là nguồn dữ liệu cho billable và bảng tổng hợp (REQ-024/040/041).

```mermaid
stateDiagram-v2
    state "Đã trình" as Submitted
    state "Đã duyệt cấp 1" as L1
    state "Đã duyệt cấp 2" as L2
    state "Bị trả lại" as Rejected
    state "Đã thu hồi" as Cancelled

    [*] --> Submitted: Delivery Manager trình (tạo yêu cầu + bản chốt) (REQ-040)
    Submitted --> L1: Department Manager duyệt cấp 1 (REQ-024)
    L1 --> L2: Invoice Manager duyệt cấp 2 — kiểm tra bản chốt + tạo billable (REQ-041)
    Submitted --> Rejected: Trả lại — Department/Invoice Manager/Quản trị (REQ-024)
    L1 --> Rejected: Trả lại — Invoice Manager/Quản trị (REQ-024)
    Submitted --> Cancelled: Delivery Manager thu hồi (REQ-040)
    L1 --> Cancelled: Delivery Manager thu hồi (REQ-040)
    L2 --> [*]
    Rejected --> [*]
    Cancelled --> [*]
    note right of L2
        Duyệt cấp 2 là bước kết thúc: ghi nhận bản duyệt hiện hành,
        tạo billable từ bản chốt (bỏ qua tháng đã chốt + báo),
        cập nhật bảng tổng hợp (REQ-041). Không trả lại được.
        Kế hoạch vẫn sửa được; sửa sau đó sẽ "lệch (chưa trình)";
        muốn cập nhật billable thì trình một yêu cầu MỚI.
        Trả lại / Thu hồi là kết thúc; trình lại là yêu cầu mới (REQ-024).
        Mỗi kế hoạch tối đa 1 yêu cầu đang xử lý.
    end note
```

Luồng **billable theo tháng** sau khi tạo đi theo vòng đời riêng (độc lập với kế hoạch): **QA rà soát và trình** billable chưa chốt, **Delivery Manager / Quản trị / Invoice Manager duyệt cuối** (REQ-RESOURCE-PLAN-BILLABLE-038):

```mermaid
stateDiagram-v2
    state "Nháp" as draft
    state "Rà soát" as review
    state "Đã trình" as submitted
    state "Đã duyệt" as approved
    state "Đã gửi" as sent
    state "Đã thanh toán" as paid
    state "Đã khóa" as locked

    [*] --> draft: Tạo billable khi yêu cầu duyệt cấp 2 (từ bản chốt) (REQ-014, REQ-038)
    draft --> review: QA rà soát (REQ-038)
    review --> submitted: QA trình (REQ-038)
    submitted --> approved: Delivery Manager/Quản trị/Invoice Manager duyệt cuối (REQ-038)
    approved --> sent
    sent --> paid
    paid --> locked
    note right of draft
        Nháp / rà soát / đã trình = chưa chốt: QA sửa được (không xóa), tạo billable lại được (có xác nhận ghi đè).
        Đã duyệt / đã gửi / đã thanh toán / đã khóa = đã chốt: chỉ Invoice Manager; tạo billable bỏ qua + báo lệch; kế hoạch vẫn sửa được (không đè tháng đã chốt).
        QA không tự duyệt cuối (chỉ Delivery Manager / Quản trị / Invoice Manager).
    end note
```

## 5. Nạp dữ liệu lần đầu cài đặt (billable hiện có → kế hoạch nguồn lực)

> Lần cài đặt đầu tiên, hệ thống nạp dữ liệu **billable hiện có** thành **kế hoạch nguồn lực**. **Chạy lại nhiều lần vẫn an toàn**: mỗi dòng kế hoạch nhận diện theo (dự án, nhân viên, vai trò, tháng). Với mỗi kế hoạch, tạo sẵn một yêu cầu **đã duyệt cấp 2** kèm bản chốt (sao chép **giá trị lịch sử** từ billable nguồn — MM / đơn giá / thành tiền, không lấy đơn giá hiện hành) để bảng tổng hợp có nguồn; **không tạo lại billable** (giữ nguyên billable đã có). Cuối cùng đối chiếu số dòng và tổng tiền (REQ-RESOURCE-PLAN-BILLABLE-034/040/041).

```mermaid
flowchart TD
    Start(["Chạy nạp dữ liệu lần đầu"]) --> Scan["Quét billable hiện có"]
    Scan --> Loop{"Mỗi dòng (dự án, nhân viên, tháng, đơn giá)"}
    Loop --> Key{"Đã có dòng kế hoạch tương ứng?"}
    Key -- "Chưa có" --> Create["Tạo dòng kế hoạch (gộp vào kế hoạch duy nhất của dự án)"]
    Key -- "Đã có" --> WD{"Người dùng đã chỉnh sau lần nạp trước?"}
    WD -- "Có" --> Skip["Bỏ qua — không ghi đè dòng người dùng đã sửa"]
    WD -- "Không" --> Upsert["Cập nhật lại (lần chạy lại không tạo trùng)"]
    Create --> Chot{"Tháng đã có billable chốt?"}
    Upsert --> Chot
    Chot -- "Có" --> RO["Nạp ở chế độ chỉ đọc"]
    Chot -- "Không" --> RW["Nạp bình thường"]
    RO --> NextItem{"Còn dòng?"}
    RW --> NextItem
    Skip --> NextItem
    NextItem -- "Có" --> Loop
    NextItem -- "Không" --> Report(["Đối chiếu tổng tiền và số dòng kế hoạch so với billable nguồn"])
```

## 6. Ánh xạ REQ ↔ luồng (Coverage note)

| Nhóm REQ | Phủ trong luồng |
|---|---|
| REQ-RESOURCE-PLAN-BILLABLE-001, REQ-RESOURCE-PLAN-BILLABLE-002, REQ-RESOURCE-PLAN-BILLABLE-010 | Mục 1 TO-BE, Mục 2 (mở/tạo kế hoạch duy nhất của dự án, gợi ý sẵn) |
| REQ-RESOURCE-PLAN-BILLABLE-003, REQ-RESOURCE-PLAN-BILLABLE-032 | Mục 2 (cửa sổ mặc định 8 tháng) |
| REQ-RESOURCE-PLAN-BILLABLE-004, REQ-RESOURCE-PLAN-BILLABLE-005, REQ-RESOURCE-PLAN-BILLABLE-006, REQ-RESOURCE-PLAN-BILLABLE-007, REQ-RESOURCE-PLAN-BILLABLE-009 | Mục 2 (nhập dòng, nhân viên đã duyệt, Bộ phận/Vai trò/Phân bổ, MM) |
| REQ-RESOURCE-PLAN-BILLABLE-008, REQ-RESOURCE-PLAN-BILLABLE-030 | Mục 1 & 2 (chọn đơn giá, tiền tệ theo đơn giá) |
| REQ-RESOURCE-PLAN-BILLABLE-031 | Mục 2 (hiển thị Department HB + OB Delivery BU) |
| REQ-RESOURCE-PLAN-BILLABLE-011, REQ-RESOURCE-PLAN-BILLABLE-012, REQ-RESOURCE-PLAN-BILLABLE-013, REQ-RESOURCE-PLAN-BILLABLE-023, REQ-RESOURCE-PLAN-BILLABLE-025 | Mục 2 (cập nhật phân bổ nhân sự một chiều từ kế hoạch; có kiểm tra quyền; không đồng bộ ngược) |
| REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-022 | Mục 1 TO-BE, Mục 3 (tự tạo billable sau duyệt cấp 2: tìm hoặc tạo billable của tháng, mỗi dự án 1 billable/tháng, thay dòng chưa chốt bằng số liệu bản chốt) |
| REQ-RESOURCE-PLAN-BILLABLE-015 | Mục 1 TO-BE & Mục 3 (thành tiền = MM × đơn giá) |
| REQ-RESOURCE-PLAN-BILLABLE-016, REQ-RESOURCE-PLAN-BILLABLE-017, REQ-RESOURCE-PLAN-BILLABLE-026 | Mục 3 (ghi đè tháng chưa chốt + xác nhận ghi đè; kế hoạch là nguồn dữ liệu chính) |
| REQ-RESOURCE-PLAN-BILLABLE-018, REQ-RESOURCE-PLAN-BILLABLE-037 | Mục 3 & Mục 4 (bỏ qua tháng đã chốt: "đã có" / "đã khóa") |
| REQ-RESOURCE-PLAN-BILLABLE-019 | Mục 3 & Mục 4 (hiển thị trạng thái tháng — đề cập, giao diện) |
| REQ-RESOURCE-PLAN-BILLABLE-020 | Vai trò người dùng + Mục 1/2/3 (Delivery/Department/Invoice Manager theo quy trình; dòng theo bộ phận) |
| REQ-RESOURCE-PLAN-BILLABLE-021 | Mục 3 (chặn tạo billable khi kế hoạch không hợp lệ) |
| REQ-RESOURCE-PLAN-BILLABLE-020 (phạm vi) | Vai trò người dùng + Mục 1/2 (Delivery chỉ thấy dự án mình phụ trách) |
| REQ-RESOURCE-PLAN-BILLABLE-024 | Mục 1 TO-BE & Mục 4 (vòng đời duyệt 2 cấp; Trả lại; tự duyệt; Trả lại vẫn giữ tháng đã chốt) |
| REQ-RESOURCE-PLAN-BILLABLE-027 | Mục 2 (lưu kế hoạch tránh hai người lưu đè nhau) |
| REQ-RESOURCE-PLAN-BILLABLE-028, REQ-RESOURCE-PLAN-BILLABLE-029 | Mục 1 TO-BE & Mục 2 (bảng tổng hợp nguồn lực luôn cập nhật theo kế hoạch) |
| REQ-RESOURCE-PLAN-BILLABLE-033 | Mục 2 & Mục 4 (chặn sửa kế hoạch của tháng đã chốt) |
| REQ-RESOURCE-PLAN-BILLABLE-034 | Mục 5 (nạp dữ liệu lần đầu, chạy lại an toàn, tháng đã chốt nạp chỉ đọc) |
| REQ-RESOURCE-PLAN-BILLABLE-035 | Mục 2 (thêm tháng mới trên biểu mẫu, gộp vào kế hoạch duy nhất) |
| REQ-RESOURCE-PLAN-BILLABLE-036 | Vai trò người dùng + Mục 4 (Invoice Manager toàn quyền; QA sửa billable chưa chốt, KHÔNG xóa; nhóm khác chỉ xem) |
| REQ-RESOURCE-PLAN-BILLABLE-038 | Mục 1 TO-BE, Mục 3 & Mục 4 (billable sau khi tạo: QA trình, Invoice Manager duyệt cuối; luồng riêng) |
| REQ-RESOURCE-PLAN-BILLABLE-039 | Mục 1/3/4 (báo chênh lệch hai chiều: kế hoạch ↔ bản chốt + bản chốt ↔ billable thực) |
| REQ-RESOURCE-PLAN-BILLABLE-040 | Mục 1/4 (Delivery Manager trình → yêu cầu + bản chốt không đổi theo (nhân viên, vai trò, tháng); 1 yêu cầu đang xử lý; Thu hồi) |
| REQ-RESOURCE-PLAN-BILLABLE-041 | Mục 1/3 (khi duyệt cấp 2: kiểm tra bản chốt + khóa + ghi nhận bản duyệt hiện hành + tạo billable + cập nhật bảng tổng hợp) |
| REQ-RESOURCE-PLAN-BILLABLE-042 | Mục 1/4 (kế hoạch không có trạng thái duyệt, luôn sửa được; vòng đời ở yêu cầu duyệt; bản duyệt hiện hành) |

> Các yêu cầu cấp chi tiết chỉ **đề cập** trong D-06 mà không vẽ thành bước riêng: REQ-RESOURCE-PLAN-BILLABLE-004 (ràng buộc khi lưu dòng), REQ-RESOURCE-PLAN-BILLABLE-019 (hiển thị trạng thái tháng — giao diện), REQ-RESOURCE-PLAN-BILLABLE-022 (cách tạo dòng billable từ bản chốt), và toàn bộ NFR-001..008. Các yêu cầu này được đặc tả ở D-02 và sẽ truy vết qua test (D-26/D-27).

---

**Revision History**

| Date | Version | Changes | Author |
|---|---|---|---|
| 2026-06-11 | 1.0 | Initial version | OPMS team |
| 2026-06-18 | 1.1 | Cập nhật theo D-02 v1.6: tách actor theo vai (Delivery/Dept Manager/IM/QA); vòng đời plan 2 cấp với state machine riêng + sơ đồ state (Mục 4); đổi Generate → Đồng bộ (action mới, chỉ IM, sau Approved L2, action_generate_lines + overlay MM/rate); thêm bỏ qua tháng đã-chốt ("đã có"/"đã khóa") + blocking confirm; luồng period sau đồng bộ (QA/IM, REQ-038); allocation một chiều + live-sync Summary (Mục 2); migration lần đầu (Mục 5); cập nhật ánh xạ REQ (028–038). | OPMS team |
| 2026-06-19 | 1.2 | Cập nhật theo D-02 v1.7 (cascade từ sync, không lan truyền tiếp). Luồng period sau đồng bộ map method thật: **QA đẩy tới `submitted`**, **IM duyệt cuối → `approved`** (`action_approve_delivery`→`_try_set_approved`); bỏ `dept_approved`; sửa state machine period (Mục 1/3/4). Đồng bộ: thêm **unlink member chưa-chốt** trước generate_lines, **find-or-create** + UNIQUE(project,month), **serialize/lock**, overlay cả `effort_ratio` (Mục 1/3, REQ-014/016/022). Quyền QA: edit period chưa-chốt, **không delete** (header + Mục 4, REQ-036). Scope Delivery theo field **`delivery_team_id.manager_id.user_id`** trên project (header + Mục 1/2, REQ-020). Thêm **REQ-039** chỉ báo lệch plan↔period (Mục 1/4). Summary đổi từ live-sync sang **model stored + refresh qua hook** (read_group/SQL view) (Mục 1/2, REQ-028/029). Migration key thêm `rate_id` + report assert số dòng (Mục 5, REQ-034). | OPMS team |
| 2026-06-19 | 1.3 | Cập nhật theo D-02 v1.8 (tuần tự in-session, sau verify-code). **Summary quay lại model stored + ACL + pivot + hook** (Odoo 11 pivot cần model backing — V6/REQ-028/029, đảo lại "view" của v1.2). Scope Delivery dùng **`delivery_team_id.manager_id.user_id`** sẵn có, KHÔNG field mới (V1/REQ-020). Period approve cuối **DM/Admin/IM** (không chỉ IM), cần `delivery_manager_user_id` raise nếu thiếu (V2/REQ-038). Đồng bộ ở `submitted` **re-sync downstream** billable/summary/customer-invoice/confirm (V5/REQ-014/016). UNIQUE `uniq_project_month` đã có (V4). Đơn giá `rate.price`/currency `rate.price_currency_id` (V3). | OPMS team |
| 2026-06-19 | 2.2 | **Tái cấu trúc theo D-02 v2.1/v2.2 (Request + Snapshot, sau party-mode + adversarial).** Vòng đời chuyển từ plan → **`resource.plan.request`** (state machine §4 = Submitted→ApprovedL1→ApprovedL2, Rejected/Cancelled terminal); **plan stateless luôn editable** (§1/§4). Submit (chỉ DelM) tạo **snapshot bất biến** grain (emp,role,month) giá trị-copy + hash; 1 in-flight/plan; DelM Withdraw. **Đồng bộ = sự kiện khi Approved L2** từ snapshot (§1/§3): verify hash + lock + set active_request_id + bỏ qua tháng đã-chốt + báo lệch; **rebuild Summary từ snapshot active** (bỏ refresh-live). Lệch 2 chiều (plan↔snapshot, snapshot↔invoice — REQ-039). Migration tạo request approved_l2 + snapshot copy từ invoice nguồn (§5). Tách DelM/DeptM. Coverage +REQ-040/041/042. | OPMS team |
| 2026-06-19 | 2.3 | **Viết lại theo hướng nghiệp vụ — loại bỏ thuật ngữ kỹ thuật triển khai.** Thay tên model/field/method và chi tiết kỹ thuật (vd. `resource.plan`, `project.invoice.period`, `active_request_id`, `snapshot_hash`, `SELECT FOR UPDATE`, `action_generate_lines`, `write_date`, `delivery_team_id.manager_id.user_id`, `idempotent`, `optimistic lock`, `pivot`, `hook`) bằng thuật ngữ nghiệp vụ tương đương (kế hoạch nguồn lực, billable theo tháng, bản chốt số liệu, khóa chống duyệt song song, chạy lại an toàn, bảng tổng hợp...). Nhãn trạng thái trong sơ đồ chuyển sang tiếng Việt. **Giữ nguyên logic nghiệp vụ, cấu trúc 6 mục, và ánh xạ REQ (truy vết).** | OPMS team |
