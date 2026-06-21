# Glossary khái niệm

> 🌐 [English](../../en/reference/concept-glossary.md) · **Tiếng Việt**
>
> 📖 **Reference** — gặp một từ lạ trong tài liệu HBC? Tra ở đây. Mỗi mục là một câu định nghĩa ngắn (answer-first) kèm link đọc sâu.
>
> ℹ️ Đây là glossary của **khái niệm HBC**. Nếu bạn tìm bảng tra **mã deliverable** (D-02, D-19…), xem [Bảng deliverable D-xx](deliverables-glossary.md); tra **skill/agent** xem [Catalog skill](skills-catalog.md). Đừng nhầm với *D-03 Glossary* — đó là glossary thuật ngữ **nghiệp vụ của dự án bạn**, do bạn sinh ra, không phải giải thích HBC.

## Mô hình giao hàng & vòng đời

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **Incremental (giao tăng dần)** | **Mô hình triển khai của HBC**: giao **từng tính năng** một, mỗi feature là một chu trình có cổng + TDD, ship độc lập với các feature khác. | [Vì sao Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **Feature (tính năng)** | Đơn vị giao hàng của HBC: một lát cắt phạm vi đi qua trọn 4 phase + TDD rồi ship riêng. Mỗi feature có một `<slug>` (vd `auth`) làm khóa cho thư mục và ID. | [Vì sao Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **Phase** | Một trong 4 chặng có thứ tự của HBC: Analysis → Design → Implementation → Testing. | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Phase 0 (Project Init)** | Bước chạy **một lần, cho cả dự án** trước mọi feature (skill `PI` / hbc-project-init): sinh các deliverable **dùng chung** (D-12, D-03) + baseline D-19/D-21. Idempotent (bỏ qua cái đã có), không cần arg `feature`. | [Catalog skill (PI)](skills-catalog.md) |
| **Phase Gate** | Chốt kiểm soát ở ranh giới mỗi phase — phải "pass" mới được sang phase sau (lệnh `PG <n>`, mang `feature=`). | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Entry/Exit criteria** | Điều kiện *vào* và *ra* của một phase — tiêu chí để bắt đầu và để được coi là hoàn thành. | [Bảng deliverable (D-26)](deliverables-glossary.md) |

## Phạm vi & deliverable

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **Scope (phạm vi)** | Một deliverable thuộc một trong ba phạm vi: **per-feature** (riêng từng feature), **shared** (dùng chung cả dự án), hoặc **dual** (có baseline shared + tùy chọn ghi đè per-feature). | [Bảng deliverable D-xx](deliverables-glossary.md) |
| **Shared deliverable (deliverable dùng chung)** | Tài liệu sinh **một lần cho cả dự án**, dùng lại cho mọi feature: D-03 Glossary, D-12 Coding Standards. Lưu ở `_bmad-output/shared/…`. | [Bảng deliverable (D-12)](deliverables-glossary.md) |
| **Per-feature override (bản ghi đè per-feature)** | Với deliverable **dual** (D-19 ERD, D-21 API): nếu feature cần bản riêng, đặt file trong `features/<feature>/planning-artifacts/` để **đè** baseline shared. | [Bảng deliverable (D-19)](deliverables-glossary.md) |
| **Path-existence precedence (ưu tiên theo sự tồn tại của path)** | Quy tắc chọn bản dual: **nếu file override per-feature tồn tại thì nó thắng**, nếu không thì dùng baseline shared. Không cần cấu hình — chỉ dựa vào đường dẫn nào có thật. | [Bảng deliverable D-xx](deliverables-glossary.md) |
| **Applicability-catalog** | Nguồn chuẩn (`src/hbc-shared/references/deliverable-catalog.yaml`) khai báo HBC định nghĩa những deliverable nào và quy tắc **required / optional / N-A** per-feature theo facet. Tính năng tối giản chỉ cần D-02 + D-06. | [Bảng deliverable D-xx](deliverables-glossary.md) |
| **Facet** | Thuộc tính boolean của một tính năng (vd `has-ui`, `has-integration`, `has-state-machine`) — đầu vào để applicability-catalog quyết định deliverable nào áp dụng, đồng thời là trigger cho Behavioral Design (D-16). | [Bảng deliverable D-xx](deliverables-glossary.md) |
| **Maturity (exploratory / stable)** | Bộ chỉnh mức chín của tính năng: `exploratory` nới required-set (hạ một số required→optional) và giảm số câu hỏi elicitation; **không bao giờ** đụng sàn đúng đắn (correctness floor). | [Bảng deliverable D-xx](deliverables-glossary.md) |

## Truy vết (Traceability)

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **Traceability** | Việc nối mỗi yêu cầu tới thiết kế, code và test của nó — để không bỏ sót yêu cầu nào. | [Khái niệm cốt lõi](../explanation/concepts.md) |
| **Traceability matrix (8 cột)** | Bảng truy vết per-feature, **8 cột**: `feature \| req_id \| story_id \| design_ref \| code_ref \| test_ref \| gate_status \| timestamp`. Coverage đếm theo `design_ref`/`code_ref`/`test_ref`. | [Quản lý Traceability](../how-to/manage-traceability.md) |
| **Rollup (TRR — gộp chéo feature)** | Skill `TRR` gộp ma trận của nhiều feature thành một bảng tổng; dòng **shared** chỉ đếm một lần. | [Quản lý Traceability](../how-to/manage-traceability.md) |
| **REQ-\<FEAT\>-NNN** | Namespace ID yêu cầu **theo từng feature** (vd `REQ-AUTH-001`), sinh ở D-02. Yêu cầu dùng chung dùng **`REQ-SHARED-NNN`**. Legacy `REQ-NNN` vẫn parse được. | [D-02 Requirements](deliverables-glossary.md) |
| **TC-NNN** | Mã định danh test case, đánh số **tuần tự trong D-27 của từng feature** (vd `TC-001`). | [D-27 Test Spec](deliverables-glossary.md) |
| **Coverage (độ phủ)** | Tỉ lệ yêu cầu đã có đủ chuỗi truy vết (thiết kế + code + test). | [Quản lý Traceability](../how-to/manage-traceability.md) |
| **Cascade Sync (SYNC — đồng bộ lan truyền)** | Khi một tài liệu nguồn đổi, skill `SYNC` phân tích impact và **đề xuất cập nhật lan truyền** xuống các tài liệu/test/code phụ thuộc bên dưới. | [Quản lý Traceability](../how-to/manage-traceability.md) |

## Lập trình & kiểm thử

| Thuật ngữ | Định nghĩa ngắn | Đọc sâu |
| --- | --- | --- |
| **TDD** | Test-Driven Development: **viết test trước**, rồi mới viết code cho test đó pass. | [Vì sao Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **RED → GREEN → REFACTOR** | Chu trình TDD: 🔴 viết test thấy fail → 🟢 viết code tối thiểu cho pass → ♻️ dọn code, test vẫn xanh. | [Vì sao Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **RED evidence (bằng chứng RED) — soft TDD** | **Cưỡng chế mềm**: trước khi viết code phải ghi lại bằng chứng test đang fail (🔴); cổng Phase 3 kiểm tra có bằng chứng RED hay không (tự khai, không phải bằng chứng mã hóa). Tinh thần: "test-first có bằng chứng RED", không chỉ "có test". | [Vì sao Incremental + TDD](../explanation/why-incremental-tdd.md) |
| **EARS** | Cú pháp viết yêu cầu rõ-ràng-có-điều-kiện; từ khóa giữ nguyên tiếng Anh (`WHEN … THE SYSTEM SHALL …`), phần văn xuôi theo `{document_output_language}`. | [D-02 Requirements](deliverables-glossary.md) |
| **Readiness check (IR — kiểm tra sẵn sàng)** | **Cổng "đường nối" của Phase 2** (skill `IR` / hbc-check-implementation-readiness): đối soát D-02 ↔ D-21/D-26/D-27 + ma trận trước khi sang Phase 3, để bắt khoảng hở giữa thiết kế và thực thi. | [Catalog skill (IR)](skills-catalog.md) |
| **ERD (ER Diagram)** | Sơ đồ quan hệ thực thể — mô tả các bảng dữ liệu và liên kết giữa chúng (deliverable D-19). | [D-19 Database Design](deliverables-glossary.md) |
| **Architecture Design (D-09)** | Thiết kế kiến trúc/giải pháp + **ADR** (quyết định kèm lý do); áp dụng khi tính năng có tích hợp hoặc thuật toán. | [D-09 Architecture](deliverables-glossary.md) |
| **Behavioral Design (D-16)** | Đặc tả hành vi phi-CRUD bằng 4 khối có ID: **ST** (state-machine), **DR** (decision-rule), **INV** (invariant), **SEQ** (sequence). | [D-16 Behavioral Design](deliverables-glossary.md) |
| **UX / Screen Design (D-14)** | Thiết kế màn hình & trải nghiệm (SCR/CMP, trạng thái, điều hướng); tùy chọn token **Claude Design** (`DESIGN.md`). Áp dụng khi tính năng có UI. | [D-14 UX/Screen Design](deliverables-glossary.md) |
| **Model-validation (P1-09)** | Mục cổng Phase 1: USER ký xác nhận **domain model đã được kiểm chứng** trước khi đóng Analysis (tự điều chỉnh cho greenfield) — chặn lỗi "model sai được PASSED". | [Cách chạy Phase Gate](../how-to/run-a-phase-gate.md) |
| **discovery_risk (known / uncertain)** | Cờ ở frontmatter D-02 (BA phân loại, USER chốt): `uncertain` = model/giả định chưa chứng → bắt buộc kiểm chứng rẻ trước thiết kế. | [D-02 Requirements](deliverables-glossary.md) |
| **Discovery Spike (DSC — discovery-note)** | Skill `hbc-discovery-spike`: với feature `uncertain`, kiểm chứng giả định model rủi ro nhất so với **ground-truth** rồi ra verdict **VALIDATED/RESHAPE/KILL** kèm USER sign-off; chặn xây cả stack trên model sai. Cổng **P1-11** đòi VALIDATED. | [Cách chạy Phase Gate](../how-to/run-a-phase-gate.md) |
| **Triage (lỗi)** | Phân loại và xếp ưu tiên các lỗi tìm được, để xử lý cái quan trọng trước. | [Bảng deliverable](deliverables-glossary.md) |
| **Deterministic** | "Cho kết quả cố định" — kiểm tra tự động bằng quy tắc cứng (có/không), không phụ thuộc đánh giá chủ quan. | [Khái niệm cốt lõi](../explanation/concepts.md) |

## Nghiệm thu (Acceptance)

| Thuật ngữ | Định nghĩa ngắn |
| --- | --- |
| **Acceptance** | Đánh giá cuối: tính năng có đạt yêu cầu để bàn giao không (lệnh `AC review`) — ship từng feature độc lập. |
| **ACCEPTED** | Đạt — chấp nhận bàn giao. |
| **REJECTED** | Không đạt — có lỗi/thiếu sót phải sửa rồi đánh giá lại. |
| **DEFERRED** | Tạm hoãn — chấp nhận có điều kiện, phần còn thiếu để lại xử lý sau (đã thống nhất). |
| **PENDING** | Chưa quyết — còn chờ thông tin/kết quả để ra quyết định. |

## Liên quan

- 💡 Hiểu sâu 4 khái niệm nền tảng: [Khái niệm cốt lõi](../explanation/concepts.md).
- 📖 Tra mã deliverable: [Bảng deliverable D-xx](deliverables-glossary.md).
- 📖 Tra skill: [Catalog skill](skills-catalog.md).
- ❓ Không biết làm gì tiếp? Gọi **`bmad-help`** — trợ lý "bước tiếp theo" luôn sẵn sàng.
