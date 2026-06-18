---
id: SPEC-traceability-impact
companions:
  - architecture-diagrams.md
  - ref-skill-map.md
  - edge-handling.md
  - ../../../src/hbc-shared/references/semantic-review-rubric.md
sources:
  - ../../brainstorming/brainstorming-session-2026-06-16-2254.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Capability "impact" — Đồng bộ tài liệu cascade trong hbc-traceability

## Why

Trong vòng đời tuần tự theo phase của HBC, khi một tài liệu đổi (vd đổi REQ), các artifact hạ nguồn (design, test, code) và các artifact dùng chung có thể lệch — ai đó sẽ xây/kiểm thử sai thứ. Đây là **pain cần giải**. Bản orchestrator cũ `src/hbc-sync` tự nuôi một mô hình trạng thái song song (DAG tĩnh + hash manifest) nên (a) **âm thầm bỏ sót** artifact bị ảnh hưởng — API spec/glossary thành "lá" không cascade tới đâu, (b) xác minh "skill đã chạy" chứ không xác minh "thay đổi đã nhập", và (c) phải bảo trì một nguồn-sự-thật thứ hai chắc chắn lệch với thực tế. Bộ skill HBC **đã có sẵn** nguồn sự thật chính xác hơn: traceability matrix (REQ↔artifact theo từng REQ), `task-breakdown` status, `hbc-phase-gate`, và git. Việc cần làm là dựng lại "đồng bộ" thành một **capability `impact` nhúng trong hbc-traceability** — chỉ ĐỌC các nguồn đã có, suy tác động chính xác, ĐỀ XUẤT, để con người quyết, và không bao giờ tự sửa nội dung.

## Capabilities

- id: CAP-1
  intent: User khai REQ/artifact mình vừa đổi (changed-set), hệ thống đối chiếu git để gợi ý bổ sung và chuẩn hóa changed-set về REQ id, làm điểm xuất phát cho phân tích tác động.
  success: Với một khai báo của user cộng các thay đổi git chưa commit (baseline = working tree vs HEAD; override `--since <ref>`), capability trình ra changed-set cho user xác nhận; thay đổi non-REQ (code/test/design) được map ngược về REQ qua matrix (`code_ref`/`test_ref`/`design_ref` → `req_id`); không đọc/ghi `.sync-manifest.json`. Biên đầu vào (matrix chưa init, không trace được, REQ id sai, changed-set rỗng, `--since` sai): xem `edge-handling.md`.

- id: CAP-2
  intent: Hệ thống đọc traceability matrix theo CẢ CỘT để tìm mọi REQ/artifact bị ảnh hưởng bởi changed-set, phân biệt "lan dọc" (hạ nguồn của REQ vừa đổi → apply) với "lan ngang" (REQ khác dùng chung artifact → verify).
  success: Khi đổi một thực thể dùng chung (vd `Customer.credit_limit`), danh sách tác động chứa cả hạ nguồn của REQ đổi LẪN mọi REQ khác có `design_ref`/`code_ref`/`test_ref` trỏ tới thực thể đó, mỗi mục gắn nhãn apply hoặc verify. Biên (REQ bị xóa, flood artifact dùng chung, ref còn rỗng): xem `edge-handling.md`.

- id: CAP-3
  intent: Hệ thống phân loại mỗi artifact bị ảnh hưởng là updatable (live frontier) hay frozen (done) bằng cách đọc matrix `gate_status` + `task-breakdown` status + `hbc-phase-gate`, và định tuyến phần frozen sang "tạo task mới" thay vì sửa tại chỗ.
  success: Một artifact bị ảnh hưởng nhưng task của nó đã DONE (hoặc phase gate đã PASSED) không bao giờ bị đề xuất sửa tại chỗ — nó được nêu dưới dạng gợi ý "tạo task mới". Biên (3 nguồn bất đồng → ưu tiên task > phase-gate > matrix; thiếu task-breakdown → fallback gate+matrix): xem `edge-handling.md`.

- id: CAP-4
  intent: Hệ thống trình impact kèm trình tự owning-skill nên chạy theo thứ tự phase cố định, đã khử trùng artifact dùng chung, mà không tự sửa bất kỳ nội dung nào.
  success: Output nêu, cho mỗi artifact bị ảnh hưởng (đã khử trùng nếu nhiều REQ dùng chung), owning-skill và thứ tự (phase cố định design→test→code; apply trước verify); không có gì được áp cho tới khi user hành động. Biên (ref không map được skill): xem `edge-handling.md`.

- id: CAP-5
  intent: Khi user hành động, hệ thống gọi owning-skill của từng artifact ở update mode một cách an toàn, để một update bị kích hoạt không thể tái kích hoạt sync.
  success: Mọi lệnh gọi ủy quyền đều mang `--invoked-by-sync`; không xảy ra vòng lặp update→sync→update; capability không tự sửa nội dung tài liệu nào. Biên (thiếu update contract → `skill_no_update_contract`; lỗi runtime → branch-stop giữ trạng thái; user áp tập con): xem `edge-handling.md`.

- id: CAP-6
  intent: Sau khi áp, hệ thống xác minh thay đổi đã thật sự nhập đúng qua hai trụ chính — validator deterministic và LLM semantic review — kèm độ-tươi ô matrix làm đối chiếu phụ.
  success: Một lần áp chỉ được báo "đã lan đúng" khi validator của artifact pass VÀ semantic review xác nhận thay đổi cụ thể đã hiện diện (ô matrix tươi chỉ là đối chiếu phụ, không tự nó chứng minh nội dung đổi); ca "skill chạy xong nhưng nội dung chưa nhập" bị báo chưa-lan-đúng và đẩy lại thành đề xuất ở bước SUGGEST — không clear state, không rollback. Biên (thiếu validator cho loại artifact; giới hạn vòng re-suggest mặc định 2): xem `edge-handling.md`.

- id: CAP-7
  intent: Khi một artifact không-gắn-REQ đổi, hệ thống trình một danh sách review advisory — glossary qua reverse-scan tham chiếu thuật ngữ; coding-standard qua flag các code task chưa-đóng-băng để re-check theo chuẩn mới.
  success: Đổi một thuật ngữ glossary cho ra danh sách artifact chưa-đóng-băng có tham chiếu thuật ngữ đó, kèm confidence; đổi coding-standard flag mọi code task chưa-đóng-băng cần re-check. Cả hai đều advisory — không bao giờ tự áp. Biên (thuật ngữ phổ biến gây flood; chưa có code task): xem `edge-handling.md`.

## Constraints

- Capability **không sở hữu state bền vững nào**; chỉ ĐỌC từ traceability matrix, `task-breakdown` status, `hbc-phase-gate`, và git. (Loại bỏ manifest + DAG tĩnh.)
- **Không bao giờ tự sửa nội dung tài liệu/code**; mọi sửa đổi đi qua owning-skill (bất biến single-responsibility).
- **Không áp gì khi chưa có hành động tường minh của user** (suggest-not-decide).
- Detection **user-declared là chính**; git chỉ đối chiếu/gợi ý, không phải nguồn quyết định.
- Tác động và thứ tự suy ra từ matrix + chuỗi phase cố định — **không DAG tĩnh, không topological sort**.
- Artifact đã frozen (done) **không bao giờ bị sửa tại chỗ**; thay đổi với chúng trở thành task mới.
- Sống như một **capability bên trong hbc-traceability**, không phải skill độc lập (đứng cạnh Initialize/Update/Report/Audit).
- Mọi lệnh gọi owning-skill ủy quyền phải mang `--invoked-by-sync` (an toàn chống loop).
- Đối chiếu git dùng baseline **working tree vs HEAD** (thay đổi chưa commit), hỗ trợ override `--since <ref>`.
- Bảng `ref-type → owning-skill` sống trong `customize.toml` của **hbc-traceability** (vd `[workflow] ref_skill_map`) — override được mà không sửa skill.
- Một artifact dùng chung bị nhiều mục trong changed-set chạm chỉ được xử lý **một lần**; trong cùng artifact, **apply (lan dọc) đi trước verify (lan ngang)**.
- Hai lần chạy `impact` chạm cùng artifact phải **nối tiếp/khóa theo artifact**, không chạy đồng thời ghi đè.

## Non-goals

- **Không phải watcher tự động/nền:** không poll, không tự cascade khi chưa có hành động của user.
- **Không** duy trì manifest phát-hiện-thay-đổi riêng hay đồ thị phụ thuộc tĩnh.
- **Không** tự chỉnh sửa nội dung tài liệu/code.
- **Không** lan ngược lên thượng nguồn — sửa một artifact con không viết lại cha (việc đó thành task mới / ngoài phạm vi).
- **Không** đảm bảo idempotence vượt quá mức mà các owning-skill được ủy quyền tự cung cấp.
- **Không** thay thế phase gate hay validator; nó tái dùng chúng.
- **Không** vận hành song song lâu dài với `src/hbc-sync` cũ: skill cũ đánh dấu DEPRECATED ngay (trỏ sang capability này), gỡ hẳn (thư mục skill + entry `[SYNC]` agent menu + tham chiếu `module.yaml`) sau khi `impact` pass validation.

## Success signal

Đổi REQ-010 (credit_limit → theo chi nhánh) làm lộ ra, trong **một lượt**, mọi artifact bị ảnh hưởng — bao gồm `order.py`/TC-220 của REQ-022 vốn dùng chung thực thể `Customer` — chia đúng thành apply vs verify, với phần done/frozen được định tuyến sang "tạo task mới"; user áp, và reconcile chỉ báo hoàn tất sau khi validator pass, timestamp matrix tươi lên, và LLM semantic review xác nhận luật-theo-chi-nhánh đã thật sự xuất hiện trong D-27. Không tồn tại bất kỳ `.sync-manifest.json` hay DAG tĩnh nào trong toàn bộ giải pháp.

## Assumptions

- 10 skill tạo-tài-liệu hỗ trợ `update` mode gọi được với `--invoked-by-sync` (đề xuất ở `src/hbc-sync/references/skill-integration.md`); coi là tiền đề, degrade graceful nếu một skill thiếu (CAP-5: flag/`skill_no_update_contract`).
- Thay đổi ở D-02 (requirements) map về REQ id qua cấu trúc theo-REQ của tài liệu; thay đổi ở code/test/design (không mang REQ id) map ngược về REQ qua matrix (`code_ref`/`test_ref`/`design_ref` → `req_id`).
- Độ chính xác phân tách apply/verify của CAP-2 bị chặn bởi granularity của `design_ref` trong matrix: nếu matrix chỉ ghi mức thực thể (`Customer`) chứ không field (`credit_limit`), thay đổi cấp field sẽ over-flag mọi REQ chạm thực thể đó. Chấp nhận over-flag (an toàn, advisory) hơn là bỏ sót.
- Rubric semantic-review dùng lại được tại `src/hbc-shared/references/semantic-review-rubric.md` để chống lưng lớp LLM của CAP-6.
- Project là git repo (detection của CAP-1 dựa vào git).
