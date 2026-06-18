# Khởi động nhanh (10 phút)

> 🌐 [English](../../en/tutorials/quickstart.md) · **Tiếng Việt**
>
> 📘 **Tutorial** — đi từ con số 0 đến chiến thắng đầu tiên: thấy agent chào bạn và tạo ra tài liệu D-02 đầu tiên cho tính năng đầu tiên của bạn. Khoảng 10 phút.
>
> 📖 **Gặp từ lạ?** (deliverable, D-02, phase gate, traceability, scope per-feature/shared/dual…) → [Glossary khái niệm](../reference/concept-glossary.md).

## Bạn sẽ đạt được gì

Cuối bài này bạn sẽ: cài xong HBC, chạy **Phase 0 bắt buộc** (`PI`) — bước **đầu tiên** giúp HBC hiểu dự án và tạo các deliverable dùng chung, xác nhận agent chạy, rồi tạo **D-02 Requirements đầu tiên cho một tính năng cụ thể** — đủ để biết "à, mình dùng được HBC rồi". Muốn đi trọn 4 phase cho một tính năng? Sang [Bắt đầu với HBC (walkthrough)](getting-started-hbc.md) sau khi xong bài này.

> ℹ️ **Mô hình giao hàng:** HBC giao **tăng dần theo từng tính năng** (incremental per-feature). Mỗi tính năng đi qua 4 phase + TDD rồi ship độc lập. Bên trong một tính năng, HBC giữ **kỷ luật tuần tự, thiết kế-trước** (thiết kế trước, gate từng mốc) — đó là cách làm việc bên trong một feature, không phải mô hình giao hàng của cả module.

## Bước 0 — Chuẩn bị

| Cần có | Kiểm tra |
| --- | --- |
| **AI coding agent** (Claude Code, Cursor, hoặc tương đương) | Đây là nơi bạn sẽ "gõ" các lệnh `PI`, `BA`, `REQ`… — **không phải** terminal thường |
| **Node.js** (để chạy `npx`) | `node -v` |
| **Python 3.10+** (cho script kiểm tra của HBC) | `python --version` |
| **2 module BMad đi kèm** — `core` + `bmm` (bắt buộc) | Có thư mục `_bmad/core/` và `_bmad/bmm/` trong dự án |
| **Quyền truy cập repo HBC** | Clone thử / `ssh -T git@git.hblab.vn` |

## Bước 1 — Cài đặt

HBC là module tùy chỉnh, cài qua trình cài đặt tương tác của BMad. Bạn cần **quyền truy cập repo HBC** — Git URL qua SSH (`git@git.hblab.vn:...`) hoặc HTTPS, hoặc một bản local.

Trong terminal, tại thư mục gốc dự án:

```bash
npx bmad-method install
```

Trình cài đặt hỏi từng bước. Đi qua như sau (dòng dưới mỗi câu hỏi là lựa chọn bạn chọn/nhập):

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│
◇  Installation directory:
│  C:\Users\HanhNT2\stc-erp-bmad-custom
│
o  Install to this directory?
│  Yes
│
o  How would you like to proceed?
│  Modify BMAD Installation
│
│  Found existing modules: core, bmm, bmb
│
o  Select official modules to install:
│    • BMad Core Module
│    • BMad Method
│    • BMad Builder
│
*  Do you want to install custom or community modules (Git URL or local path)?
│  > Yes
│
◇  Git URL hoặc đường dẫn local:
│  git@git.hblab.vn:stc/erp/stc-erp-bmad-custom.git
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ở bước *Select official modules*, đảm bảo **BMad Core Module** (`core`) và **BMad Method** (`bmm`) được chọn — HBC cần cả hai (BMad Builder tùy chọn). Khi danh sách module custom hiện ra, chọn **"HBLAB BMad Custom"**, rồi nhập cấu hình (tên, ngôn ngữ…).

> ⚠️ **Cài không tương tác (CI/script) — cẩn thận mất module!** Chạy `--custom-source` mà thiếu `--modules` sẽ khiến trình cài chỉ giữ `core` + module custom và **gỡ** `bmm`/`bmb`. Luôn liệt kê đầy đủ module cần giữ (`core` luôn kèm; `--tools` bắt buộc với `--yes` khi cài mới):
>
> ```bash
> npx bmad-method install --directory . --modules bmm,bmb \
>   --custom-source git@git.hblab.vn:stc/erp/stc-erp-bmad-custom.git \
>   --tools claude-code --yes
> ```
>
> Để **cập nhật về sau** mà giữ nguyên cấu hình & module: `npx bmad-method install --action quick-update --custom-source <URL>`.
>
> ⚠️ **Báo lỗi quyền/clone?** Bạn chưa có quyền vào repo. Kiểm tra SSH key bằng `ssh -T git@git.hblab.vn`, hoặc dùng URL HTTPS, hoặc xin quyền từ team.

## Bước 2 — Xác nhận cài đặt thành công ✅

Đừng vội nhảy vào dùng. Mở **AI coding agent** (vd Claude Code) **trong thư mục dự án**, rồi gõ:

```
bmad-help
```

`bmad-help` (skill của BMad **core**, không thuộc riêng HBC) sẽ xem trạng thái dự án và tư vấn bước tiếp theo — **ví dụ minh họa** (câu chữ thực tế tùy phiên bản):

```text
BMad Help — đã xem dự án của bạn.
Trạng thái: chưa có deliverable nào trong _bmad-output/ → bạn chưa khởi tạo dự án.
Gợi ý: chạy hbc-project-init (gõ PI) MỘT LẦN để tạo deliverable dùng chung, rồi bắt đầu tính năng đầu tiên.
```

> ℹ️ Nếu bản cài của bạn không có `bmad-help`, cứ bỏ qua bước này và gõ thẳng `PI` ở dưới — nó là phép thử đủ để xác nhận HBC đã sẵn sàng.

## Bước 3 — Phase 0 BẮT BUỘC, chạy ĐẦU TIÊN (`PI`)

Phase 0 (`hbc-project-init`) là bước **bắt buộc** và phải **hoàn tất trước** mọi công việc tính năng. Chạy **một lần** cho cả dự án; về sau muốn cập nhật thì **chạy lại để sửa trực tiếp** (không phải "bỏ qua thứ đã có"). Bước này **không cần** tham số `feature`.

Phase 0 làm **hai việc**:

1. **Hiểu dự án.**
   - *Brownfield* (đã có codebase): lập tài liệu code trước bằng `bmad-document-project`, rồi đảm bảo có `project-context.md` (qua `bmad-generate-project-context`).
   - *Greenfield* (dự án mới): lấy bối cảnh từ PRD/brief, hoặc agent sẽ hỏi bạn.
2. **Tạo các deliverable dùng chung (shared) TỪ bối cảnh đó:** D-12 Coding Standards (brownfield: rút ra từ quy ước code sẵn có), D-03 Glossary (từ domain), bản nền (baseline) D-19 ERD (brownfield: từ schema DB sẵn có), bản nền D-21 API (brownfield: từ các endpoint sẵn có).

> ℹ️ D-12 và D-03 là deliverable **dùng chung của Phase 0** — không phải "bước tùy chọn" của Phase 1/2.

Vẫn trong agent, gõ:

```
PI
```

**Kết quả mong đợi** — các file dùng chung xuất hiện dưới `_bmad-output/shared/` (**ví dụ minh họa**):

```text
hbc-project-init — đã tạo deliverable dùng chung:
  _bmad-output/shared/coding-standards/  (D-12)
  _bmad-output/shared/glossary/          (D-03)
  _bmad-output/shared/erd/               (D-19 baseline)
  _bmad-output/shared/api/               (D-21 baseline)
```

> ℹ️ Đây là phần móng chung cho **mọi** tính năng, dựng **từ** bối cảnh dự án ở việc (1). Làm một lần là xong — các tính năng sau sẽ dùng lại (và có thể ghi đè per-feature khi cần); muốn cập nhật thì chạy lại `PI` để sửa trực tiếp.

## Bước 4 — Gặp agent Phase 1 🎉

Bây giờ mới mở agent của tính năng đầu tiên. Gõ:

```
BA
```

**Kết quả mong đợi** — agent Business Analyst chào và hiện menu Phase 1 (**ví dụ minh họa**, câu chữ thực tế có thể khác):

```text
Business Analyst — điều phối Phase 1 Analysis.
Bạn có thể: REQ (tạo yêu cầu D-02), GLO (glossary), BFD (business flow)...
```

> 🎉 **Chiến thắng đầu tiên!** Thấy agent chào nghĩa là bạn vừa chạm vào HBC thành công — phần khó nhất (làm nó "sống") đã xong.

### Nếu `BA` không phản hồi 🔧

Đây là chỗ người mới hay vấp. Thử lần lượt:

1. **Bạn có đang ở trong AI coding agent không?** `BA` là lệnh của agent, không chạy trong terminal thường.
2. **Đúng thư mục dự án chưa?** Agent cần thấy thư mục `_bmad/hbc/`.
3. **Cài đặt xong chưa?** Chạy lại Bước 1; kiểm tra có thư mục `_bmad/hbc/` và file `_bmad/hbc/config.yaml`.
4. **Vẫn kẹt?** Gõ `bmad-help` và mô tả vấn đề — nó sẽ chẩn đoán giúp.

## Bước 5 — Tạo tài liệu đầu tiên (D-02) cho tính năng đầu tiên

D-02 là deliverable **per-feature** — nó luôn thuộc về một tính năng cụ thể. Vì vậy bạn cần đặt tên tính năng (`feature`) dạng **kebab-case**, ví dụ `change-password`.

Vẫn trong agent, gõ:

```
REQ
```

Agent sẽ hỏi tên tính năng và phỏng vấn bạn về một yêu cầu. Cứ trả lời ngắn gọn, ví dụ:

> **feature:** `change-password`
>
> Người dùng đã đăng nhập có thể đổi mật khẩu: nhập mật khẩu cũ + mật khẩu mới, hệ thống kiểm tra mật khẩu cũ đúng và mật khẩu mới ≥ 8 ký tự.

> 💡 **Chưa chắc câu trả lời?** Không sao — trả lời sơ bộ cũng được. Sau này chạy lại `REQ` ở chế độ `update` để bổ sung. Mục tiêu lúc này chỉ là tạo ra file D-02 đầu tiên.

**Kết quả mong đợi** — một file **D-02 Requirements Specification** xuất hiện trong `_bmad-output/features/change-password/planning-artifacts/`, chứa các yêu cầu đánh mã theo tính năng: `REQ-CHANGE-PASSWORD-001`, `REQ-CHANGE-PASSWORD-002`… (mẫu chung là `REQ-<FEAT>-NNN`). Mở file đó ra xem: đó chính là deliverable đầu tiên của bạn.

> ℹ️ **Bố cục output:** mỗi tính năng có thư mục riêng dưới `_bmad-output/features/<feature>/` (gồm `planning-artifacts`, `implementation-artifacts`, `gates`, `traceability`); deliverable dùng chung nằm ở `_bmad-output/shared/`. Không còn thư mục phẳng `_bmad-output/planning-artifacts/` như bản cũ.

> 🎉 **Bạn đã hoàn thành Quickstart!** Bạn vừa: cài HBC → khởi tạo dự án (`PI`) → xác nhận chạy → tạo D-02 cho tính năng đầu tiên. Đây là một mốc **dừng được** — bạn đã biết cách dùng HBC ở mức cơ bản.
>
> ℹ️ **Lưu ý về `PG 1`:** D-02 chưa đủ để qua phase gate Phase 1. Để pass `PG 1` còn cần **D-03 (từ Phase 0, dùng chung)** và **D-06 (BFD — sơ đồ luồng nghiệp vụ, per-feature, bắt buộc)**. Luồng Phase 1 đầy đủ nằm trong [Bắt đầu với HBC](getting-started-hbc.md).

## Bước tiếp theo

- ▶️ **Đi trọn vòng đời:** [Bắt đầu với HBC (walkthrough 4 phase)](getting-started-hbc.md) — từ D-02 đến nghiệm thu, ship một tính năng độc lập.
- 🗺️ Xem toàn cảnh: [Bản đồ quy trình](workflow-map.md).
- 💡 Hiểu khái niệm: [Khái niệm cốt lõi](../explanation/concepts.md) · [Vì sao giao tăng dần + TDD](../explanation/why-incremental-tdd.md).
- 🔧 Việc cụ thể: [Chạy Phase Gate](../how-to/run-a-phase-gate.md) · [Quản lý Traceability](../how-to/manage-traceability.md) · [Chế độ Headless](../how-to/use-headless-mode.md) · [Tùy chỉnh cấu hình](../how-to/customize-config.md).

> 💡 Bất cứ lúc nào không biết làm gì tiếp — gõ `bmad-help`.
>
> 🔧 **Một skill báo lỗi hoặc sinh file rỗng?** Chạy lại nó ở chế độ `validate` (kiểm tra) hoặc `update` (bổ sung), hoặc gõ `bmad-help` để được chẩn đoán.
