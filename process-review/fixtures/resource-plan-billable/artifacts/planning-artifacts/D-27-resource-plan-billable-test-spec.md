---
document_id: D-27
title: "OPMS Resource Plan & Billable Generation — Đặc tả kiểm thử"
version: "2.3"
status: draft
tc_count: 107
coverage: 100
stepsCompleted: ["prerequisites", "discovery", "generation", "validation", "semantic-review", "complete"]
lastStep: "complete"
updated: "2026-06-19"
semanticReview:
  status: passed
  reviewedBy: llm
  date: "2026-06-19"
  openFacets: []
---

# OPMS Resource Plan & Billable Generation — Đặc tả kiểm thử (Test Specification)

## 1. Tổng quan (Overview)

### 1.1 Mục đích (Purpose)

Đặc tả chi tiết test case cho feature Resource Plan & Billable Generation (module project invoice, Odoo 11). Mỗi REQ-xxx của D-02 (**v2.2, 42 REQ**) có ≥1 test case. Bám chiến lược D-26 (unit/integration: Odoo test framework; E2E: Playwright).

> ⚠️ **THAY ĐỔI MÔ HÌNH (v2.2 — Request + Snapshot).** Vòng đời KHÔNG còn trên plan. **Plan stateless, luôn editable.** Để cập nhật invoice: **DelM Submit** → tạo `resource.plan.request` (state submitted) + **snapshot bất biến** (`resource.plan.request.line`, grain (employee,role,month), **giá-trị-copy** + **hash**, immutable-on-create, 1-in-flight/plan, DelM Withdraw được). **DeptM duyệt L1, IM duyệt L2.** **Đồng bộ = sự kiện một lần khi Approved L2, dữ liệu lấy từ SNAPSHOT** (verify hash → lock FOR UPDATE → set `active_request_id` → find-or-create period (project,month) → unlink member chưa-chốt → generate_lines → overlay effort_mm/rate_id/effort_ratio từ **snapshot**; idempotent; serialize 2×L2; bỏ tháng đã-chốt + báo). **Resource Plan Summary đọc từ snapshot active** (request L2 mới nhất), rebuild khi L2 — KHÔNG refresh-live theo plan. **Reject terminal** (DeptM@submitted, IM@approved_l1; KHÔNG reject ở approved_l2). Lệch **2 chiều**: plan↔snapshot + snapshot↔invoice (REQ-039). Migration tạo request `approved_l2` + snapshot copy từ invoice nguồn, **KHÔNG re-sync** (REQ-034). **Bản đồ TC bị ảnh hưởng** (model cũ → v2.2) ở §2.1.

### 1.2 Tài liệu tham chiếu (Reference Documents)

| Document | ID | Description |
|----------|----|-------------|
| Đặc tả yêu cầu | D-02 | 42 REQ (**v2.2**) — nguồn truy vết |
| Kế hoạch kiểm thử | D-26 | Chiến lược, phạm vi, cấp độ (v2.2) |
| Sơ đồ luồng | D-06 | Kịch bản integration/E2E (v2.2) |
| Thiết kế CSDL | D-19 | resource_plan + request + request_line snapshot (v2.2) |

### 1.3 Quy ước mã test case (Test Case ID Format)

Format: `TC-xxx` (tuần tự từ TC-001). Mỗi TC gắn ≥1 REQ-xxx. Trường **Facets** khai báo mặt mà TC thực thi (read/write · api/admin/ui/batch · lifecycle).

## 2. Danh sách test case (Test Case Summary)

| TC ID | Category | REQ ID | Description | Severity | Status |
|-------|----------|--------|-------------|----------|--------|
| TC-001 | Functional | REQ-RESOURCE-PLAN-BILLABLE-001 | Menu Resource Plan hiển thị cho 3 nhóm quyền | Medium | Draft |
| TC-002 | Functional | REQ-RESOURCE-PLAN-BILLABLE-002 | Tạo resource plan gắn 1 dự án | High | Draft |
| TC-003 | Functional | REQ-RESOURCE-PLAN-BILLABLE-002 | Mở lại plan đã lưu giữ nguyên dữ liệu | Medium | Draft |
| TC-004 | Functional | REQ-RESOURCE-PLAN-BILLABLE-003 | Cửa sổ mặc định 8 tháng (current−2…current+5) | High | Draft |
| TC-005 | Functional | REQ-RESOURCE-PLAN-BILLABLE-003 | from > to bị từ chối | Medium | Draft |
| TC-006 | Functional | REQ-RESOURCE-PLAN-BILLABLE-004 | Lưu dòng thiếu employee/rate bị chặn | High | Draft |
| TC-007 | Functional | REQ-RESOURCE-PLAN-BILLABLE-005 | Chỉ chọn được nhân viên approved | Medium | Draft |
| TC-008 | Functional | REQ-RESOURCE-PLAN-BILLABLE-006 | Dept/Role tự hiển thị read-only theo nhân viên | Medium | Draft |
| TC-009 | Functional | REQ-RESOURCE-PLAN-BILLABLE-007 | Allocation % khớp project.member | Medium | Draft |
| TC-010 | Functional | REQ-RESOURCE-PLAN-BILLABLE-008 | Đơn giá chỉ chọn từ bảng rate | High | Draft |
| TC-011 | Functional | REQ-RESOURCE-PLAN-BILLABLE-009 | Nhập MM=0.5 lưu đúng | High | Draft |
| TC-012 | Functional | REQ-RESOURCE-PLAN-BILLABLE-009 | MM âm / không phải số bị từ chối | High | Draft |
| TC-013 | Functional | REQ-RESOURCE-PLAN-BILLABLE-010 | Pre-fill dòng từ allocation hiện có | High | Draft |
| TC-014 | Integration | REQ-RESOURCE-PLAN-BILLABLE-011 | Thêm dòng tay → tạo allocation mới | High | Draft |
| TC-015 | Integration | REQ-RESOURCE-PLAN-BILLABLE-012 | Sửa allocation % → cập nhật project.member | High | Draft |
| TC-016 | Integration | REQ-RESOURCE-PLAN-BILLABLE-013 | Xóa dòng → set end_at (không xóa cứng) | High | Draft |
| TC-017 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014 | Khi L2: đồng bộ từ snapshot tạo đủ period(draft) + member (overlay MM/rate từ snapshot) | Critical | Draft |
| TC-018 | Functional | REQ-RESOURCE-PLAN-BILLABLE-015 | amount = MM × đơn giá | Critical | Draft |
| TC-019 | Integration | REQ-RESOURCE-PLAN-BILLABLE-016 | Đồng bộ lại replace member lines tháng chưa-chốt | High | Draft |
| TC-020 | Functional | REQ-RESOURCE-PLAN-BILLABLE-017 | Blocking confirm trước khi ghi đè (chỉ khi đã có lines) | High | Draft |
| TC-021 | Integration | REQ-RESOURCE-PLAN-BILLABLE-018 | Đồng bộ bỏ qua tháng locked + báo "đã khóa" | Critical | Draft |
| TC-022 | Integration | REQ-RESOURCE-PLAN-BILLABLE-018 | Không sửa được member ở period locked | High | Draft |
| TC-023 | Functional | REQ-RESOURCE-PLAN-BILLABLE-019 | Hiển thị trạng thái từng cột tháng | Medium | Draft |
| TC-024 | Security | REQ-RESOURCE-PLAN-BILLABLE-020 | Phân quyền request theo workflow (DelM submit / DeptM L1 / IM L2); plan ai-cũng-sửa; đồng bộ tự động khi L2 | High | Draft |
| TC-025 | Functional | REQ-RESOURCE-PLAN-BILLABLE-021 | Chặn Đồng bộ khi plan không hợp lệ | High | Draft |
| TC-026 | Integration | REQ-RESOURCE-PLAN-BILLABLE-022 | Member line khớp khung generate_lines; MM/rate/effort_ratio overlay từ snapshot | Medium | Draft |
| TC-027 | Integration | REQ-RESOURCE-PLAN-BILLABLE-023 | Sửa allocation ngoài plan không đổi plan đã lưu | Medium | Draft |
| TC-028 | Integration | REQ-RESOURCE-PLAN-BILLABLE-024, REQ-RESOURCE-PLAN-BILLABLE-040 | DelM Submit → tạo request(submitted) + snapshot bất biến | High | Draft |
| TC-029 | Integration | REQ-RESOURCE-PLAN-BILLABLE-024 | DeptM duyệt L1 → IM duyệt L2 → đồng bộ tự động từ snapshot | High | Draft |
| TC-030 | Integration | REQ-RESOURCE-PLAN-BILLABLE-024 | Reject terminal → request rejected; active_request_id giữ nguyên; resubmit = request mới | High | Draft |
| TC-031 | Security | REQ-RESOURCE-PLAN-BILLABLE-024 | Non-DeptM/non-IM không duyệt được cấp tương ứng | High | Draft |
| TC-032 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014 | Đồng bộ lỗi giữa chừng → rollback nguyên tử tháng đó | High | Draft |
| TC-033 | Integration | REQ-RESOURCE-PLAN-BILLABLE-019 | Lưới frozen-pane: cột định danh + header đứng yên khi scroll | Medium | Draft |
| TC-034 | Functional | REQ-RESOURCE-PLAN-BILLABLE-009 | Accessibility: tab-traversal ô + aria-invalid khi MM lỗi | Medium | Draft |
| TC-035 | Functional | REQ-RESOURCE-PLAN-BILLABLE-017 | Accessibility: dialog Đồng bộ focus trap + Esc hủy | Medium | Draft |
| TC-036 | Security | REQ-RESOURCE-PLAN-BILLABLE-020 | Row-level: Delivery Manager không mở được plan dự án không phụ trách | High | Draft |
| TC-037 | Security | REQ-RESOURCE-PLAN-BILLABLE-020 | Department Manager chỉ sửa dòng bộ phận mình; dòng bộ phận khác read-only | High | Draft |
| TC-038 | Functional | REQ-RESOURCE-PLAN-BILLABLE-024 | Reject terminal kèm lý do (DeptM@submitted / IM@approved_l1); resubmit = request mới | High | Draft |
| TC-039 | Security | REQ-RESOURCE-PLAN-BILLABLE-024 | Tự duyệt request L1+L2 cho phép (self-approval không bị chặn) | Medium | Draft |
| TC-040 | Security | REQ-RESOURCE-PLAN-BILLABLE-025 | Sync thiếu quyền project.member → bị từ chối | High | Draft |
| TC-041 | Integration | REQ-RESOURCE-PLAN-BILLABLE-026 | Đồng bộ (L2) ghi đè cả sửa tay trên period (snapshot là nguồn sự thật) | High | Draft |
| TC-042 | Integration | REQ-RESOURCE-PLAN-BILLABLE-027 | Sửa đồng thời: 2 user khác dòng → user B lưu sau bị từ chối | High | Draft |
| TC-043 | Functional | REQ-RESOURCE-PLAN-BILLABLE-027 | Đồng bộ khi còn thay đổi chưa lưu → cảnh báo, chạy trên dữ liệu đã lưu | Medium | Draft |
| TC-044 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014 | Đồng bộ xảy ra đúng khi request đạt approved_l2 (không ở submitted/approved_l1) | High | Draft |
| TC-045 | Functional | REQ-RESOURCE-PLAN-BILLABLE-017 | Submit khi snapshot rỗng / tháng chưa có lines → xử lý đúng (không blocking thừa) | Medium | Draft |
| TC-046 | Integration | REQ-RESOURCE-PLAN-BILLABLE-028 | Summary pivot Department→Project→Member từ snapshot active; default filter chưa closed + năm hiện tại | High | Draft |
| TC-047 | Integration | REQ-RESOURCE-PLAN-BILLABLE-029 | Summary đọc snapshot active: sửa plan sau snapshot KHÔNG đổi Summary; rebuild khi L2 ("xanh giả" sanity) | High | Draft |
| TC-048 | Integration | REQ-RESOURCE-PLAN-BILLABLE-028, REQ-RESOURCE-PLAN-BILLABLE-029 | Summary pivot đa-currency tách theo currency (không cộng lẫn) | High | Draft |
| TC-049 | Functional | REQ-RESOURCE-PLAN-BILLABLE-030 | Cột Đơn vị tiền tệ liền sau Đơn giá; ăn theo rate.price_currency_id | Medium | Draft |
| TC-050 | Functional | REQ-RESOURCE-PLAN-BILLABLE-031 | Hiển thị Department (HB) và OB Delivery (BU) | Low | Draft |
| TC-051 | Functional | REQ-RESOURCE-PLAN-BILLABLE-032 | Cửa sổ 8 tháng theo tz server (freeze current); thêm tháng ngoài cửa sổ | High | Draft |
| TC-052 | Integration | REQ-RESOURCE-PLAN-BILLABLE-033 | Tháng period đã-chốt: billable bị guard (plan vẫn editable) → chặn ghi member + đúng thông báo | High | Draft |
| TC-053 | Integration | REQ-RESOURCE-PLAN-BILLABLE-034 | Migrate lần 1 tạo request(approved_l2) + snapshot copy từ invoice nguồn; KHÔNG re-sync; report khớp invoice cũ | High | Draft |
| TC-054 | Integration | REQ-RESOURCE-PLAN-BILLABLE-034 | Migrate idempotent: rerun → created=0, không dup request/snapshot | High | Draft |
| TC-055 | Functional | REQ-RESOURCE-PLAN-BILLABLE-035 | Thêm tháng mới trên form → cộng dồn vào plan duy nhất | Medium | Draft |
| TC-056 | Security | REQ-RESOURCE-PLAN-BILLABLE-036 | Invoice: IM edit/delete; QA edit period chưa-chốt KHÔNG delete; QA delete approved bị chặn; nhóm cũ view | High | Draft |
| TC-057 | Integration | REQ-RESOURCE-PLAN-BILLABLE-037 | Đồng bộ khoảng có tháng đã-chốt → bỏ qua + "đã có" | High | Draft |
| TC-058 | Integration | REQ-RESOURCE-PLAN-BILLABLE-038 | Period sau Đồng bộ: QA đẩy tới submitted, IM duyệt cuối → approved; QA không tự approve | High | Draft |
| TC-059 | Functional | REQ-RESOURCE-PLAN-BILLABLE-018 | Bảng chân trị: predicate month_has_committed_invoice + committed_reason (assert enum) | High | Draft |
| TC-060 | Performance | NFR-001, NFR-002, NFR-008 | Đo p95 render/đồng bộ/pivot theo điều kiện đo (dataset, warm, 20 runs) | Medium | Draft |
| TC-061 | Functional | REQ-RESOURCE-PLAN-BILLABLE-039 | Chỉ báo lệch chiều (a) plan↔snapshot (plan live ≠ snapshot active) | Medium | Draft |
| TC-062 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-037 | Race/TOCTOU: period reset committed→draft giữa lúc đồng bộ L2 (re-check dưới lock) | High | Draft |
| TC-063 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-041 | Race: 2×L2 song song → serialize/lock, 1 thắng, active=mới nhất, không nhân đôi | High | Draft |
| TC-064 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014 | find-or-create dựa UNIQUE(project, month) — không tạo period trùng | High | Draft |
| TC-065 | Functional | REQ-RESOURCE-PLAN-BILLABLE-003, REQ-RESOURCE-PLAN-BILLABLE-032 | Cửa sổ 8 tháng vắt qua năm (current=2026-11 → 2027-04) | High | Draft |
| TC-066 | Functional | REQ-RESOURCE-PLAN-BILLABLE-032 | "current" theo tz server (freeze time, không tz user) | Medium | Draft |
| TC-067 | Integration | REQ-RESOURCE-PLAN-BILLABLE-034 | Migration dữ liệu bẩn: employee non-approved/đã nghỉ → ghi snapshot + report, không crash | Medium | Draft |
| TC-068 | Integration | REQ-RESOURCE-PLAN-BILLABLE-034 | Migration: rate nguồn không map ntq.project.billable.rate → report, không crash | Medium | Draft |
| TC-069 | Integration | REQ-RESOURCE-PLAN-BILLABLE-034 | Migration: >1 member cùng (project,employee,month,role) ở nguồn → report | Medium | Draft |
| TC-070 | Functional | REQ-RESOURCE-PLAN-BILLABLE-004 | Negative: thêm dòng employee trùng (UNIQUE plan,employee,role) | High | Draft |
| TC-071 | Functional | REQ-RESOURCE-PLAN-BILLABLE-002 | Negative: tạo plan thứ 2 cho cùng project (UNIQUE project) bị chặn | High | Draft |
| TC-072 | Integration | REQ-RESOURCE-PLAN-BILLABLE-013 | Allocation edge: xóa dòng member_id=False (không raise) | Medium | Draft |
| TC-073 | Integration | REQ-RESOURCE-PLAN-BILLABLE-011 | Allocation edge: thêm dòng employee đã có allocation (không dup) | Medium | Draft |
| TC-074 | Functional | REQ-RESOURCE-PLAN-BILLABLE-012 | Allocation edge: effort_ratio biên 0% / >100% | Medium | Draft |
| TC-075 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-021 | Đồng bộ edge: dòng MM=0 mọi tháng → không sinh member | Medium | Draft |
| TC-076 | Integration | REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-022 | Đồng bộ edge: tháng MM=0 chủ đích vs 0-mặc-định generate_lines | Medium | Draft |
| TC-077 | Integration | REQ-RESOURCE-PLAN-BILLABLE-018, REQ-RESOURCE-PLAN-BILLABLE-037 | Đồng bộ edge: khoảng toàn tháng đã-chốt (0 period) | Medium | Draft |
| TC-078 | Security | REQ-RESOURCE-PLAN-BILLABLE-020 | Multi-department: Dept Manager A sửa dòng bộ phận B → chặn | High | Draft |
| TC-079 | Integration | REQ-RESOURCE-PLAN-BILLABLE-020, REQ-RESOURCE-PLAN-BILLABLE-024 | Multi-department: Dept Manager duyệt L1 toàn plan | Medium | Draft |
| TC-080 | Security | REQ-RESOURCE-PLAN-BILLABLE-024 | Self-approval: 1 IM tự duyệt L1+L2 → cho phép (IM⊇Dept) | Medium | Draft |
| TC-081 | Security | NFR-004 | Audit/log thao tác Đồng bộ (người/thời điểm/tháng bỏ qua) | Medium | Draft |
| TC-082 | Functional | REQ-RESOURCE-PLAN-BILLABLE-009, REQ-RESOURCE-PLAN-BILLABLE-005 | Tách tầng: type-coercion (UI) vs CHECK (DB) cho MM; approved-employee cần @api.constrains | Medium | Draft |
| TC-083 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | Submit tạo snapshot grain (employee,role,month) giá-trị-copy đầy đủ field + hash | Critical | Draft |
| TC-084 | Security | REQ-RESOURCE-PLAN-BILLABLE-040 | Chỉ DelM được Submit; DeptM/IM/người khác Submit → bị chặn | High | Draft |
| TC-085 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | 1-in-flight: Submit khi đang có request {submitted, approved_l1} → bị chặn | High | Draft |
| TC-086 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | DelM Withdraw request in-flight → cancelled; cho Submit request mới | High | Draft |
| TC-087 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | Submit KHÔNG sinh allocation/period (chỉ tạo request + snapshot) | Medium | Draft |
| TC-088 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | Snapshot immutable: sửa plan/đổi rate/xóa employee sau Submit → snapshot + hash KHÔNG đổi | Critical | Draft |
| TC-089 | Security | REQ-RESOURCE-PLAN-BILLABLE-040 | request.line immutable: write/unlink sau tạo → bị chặn (mọi state, mọi role) | High | Draft |
| TC-090 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | Snapshot grain UNIQUE(request, employee, role, month) — không trùng dòng | Medium | Draft |
| TC-091 | Integration | REQ-RESOURCE-PLAN-BILLABLE-041 | Verify hash trước L2: snapshot bị tamper → L2 raise | High | Draft |
| TC-092 | Integration | REQ-RESOURCE-PLAN-BILLABLE-041 | Đồng bộ overlay từ SNAPSHOT (không plan live): đổi plan giữa Submit và L2 → invoice khớp snapshot | Critical | Draft |
| TC-093 | Integration | REQ-RESOURCE-PLAN-BILLABLE-041 | Đồng bộ idempotent: re-run sync trên cùng request không nhân đôi member/period | High | Draft |
| TC-094 | Integration | REQ-RESOURCE-PLAN-BILLABLE-041 | Set active_request_id = request L2 mới nhất; nhiều chu kỳ L2 → trỏ request cuối | High | Draft |
| TC-095 | Functional | REQ-RESOURCE-PLAN-BILLABLE-042 | Plan stateless: sửa plan khi có request pending / sau L2 → cho phép | High | Draft |
| TC-096 | Functional | REQ-RESOURCE-PLAN-BILLABLE-042 | Plan không có field state; không có action submit/approve trên plan | Medium | Draft |
| TC-097 | Integration | REQ-RESOURCE-PLAN-BILLABLE-024 | Không reject ở approved_l2 (terminal) → bị chặn | High | Draft |
| TC-098 | Integration | REQ-RESOURCE-PLAN-BILLABLE-024 | State machine request: submitted→approved_l1→approved_l2; nhảy cấp sai → chặn | High | Draft |
| TC-099 | Integration | REQ-RESOURCE-PLAN-BILLABLE-039 | Chỉ báo lệch chiều (b) snapshot↔invoice (tháng đã-chốt bị bỏ qua / period thu hẹp) | Medium | Draft |
| TC-100 | Integration | REQ-RESOURCE-PLAN-BILLABLE-028, REQ-RESOURCE-PLAN-BILLABLE-029 | Summary "xanh giả" sanity: đổi plan sau snapshot RỒI mới assert Summary đọc snapshot | High | Draft |
| TC-101 | Integration | REQ-RESOURCE-PLAN-BILLABLE-016, REQ-RESOURCE-PLAN-BILLABLE-041 | Đồng bộ: unlink member chưa-chốt rồi sinh lại từ snapshot → employee đã xóa khỏi snapshot biến mất | High | Draft |
| TC-102 | Integration | REQ-RESOURCE-PLAN-BILLABLE-034 | Migration: tổng amount snapshot = invoice cũ; KHÔNG re-sync (invoice không đổi); Summary khớp invoice cũ | High | Draft |
| TC-103 | Security | REQ-RESOURCE-PLAN-BILLABLE-040 | Row-level request: DelM chỉ request dự án mình; DeptM chỉ duyệt request bộ phận mình | High | Draft |
| TC-104 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | active_request_id ondelete SET NULL: xóa request L2 → plan.active_request_id = NULL (không crash) | Medium | Draft |
| TC-105 | Functional | REQ-RESOURCE-PLAN-BILLABLE-041 | "Xanh giả" sanity đồng bộ: đổi plan sau snapshot trước khi assert invoice == snapshot | High | Draft |
| TC-106 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | Reject/Cancelled là terminal: không transition tiếp; resubmit tạo request mới (1-in-flight lại mở) | Medium | Draft |
| TC-107 | Integration | REQ-RESOURCE-PLAN-BILLABLE-040 | Race 2 DelM Submit đồng thời cùng plan → partial UNIQUE chặn, chỉ 1 request in-flight | High | Draft |

### 2.1 Bản đồ TC bị ảnh hưởng bởi v2.2 (model cũ → Request+Snapshot)

Các TC cũ dưới đây **đã đổi ngữ nghĩa** sang model Request+Snapshot (chi tiết §3 đã cập nhật cho các TC trọng yếu):

| TC | Model cũ (v1.x) | v2.2 |
|---|---|---|
| TC-017, TC-026, TC-101 | overlay member từ **plan** khi Đồng bộ thủ công | overlay từ **snapshot** khi **L2** |
| TC-024, TC-031, TC-036, TC-037, TC-078, TC-079, TC-103 | phân quyền **plan** + nút Đồng bộ | phân quyền **request**; plan ai-cũng-sửa; đồng bộ tự động khi L2 |
| TC-028, TC-029, TC-030, TC-038, TC-039, TC-080, TC-097, TC-098, TC-106 | lifecycle **trên plan** (Draft→…→Approved L2; Reject→Draft) | lifecycle **trên request** (Submitted→ApprovedL1→ApprovedL2; **Reject terminal**) |
| TC-041, TC-044 | Đồng bộ thủ công khi plan Approved L2; plan = nguồn | Đồng bộ **sự kiện khi L2**; **snapshot** = nguồn |
| TC-046, TC-047, TC-100 | Summary refresh-live theo plan | Summary đọc **snapshot active**, rebuild khi L2 |
| TC-052 | chặn **sửa plan** tháng đã-chốt | plan editable; **billable** bị guard |
| TC-053, TC-054, TC-067, TC-068, TC-069, TC-102 | migration tạo **plan(draft)** | migration tạo **request approved_l2 + snapshot** từ invoice nguồn, KHÔNG re-sync |
| TC-061, TC-099 | lệch plan↔period 1 chiều | lệch **2 chiều** plan↔snapshot + snapshot↔invoice |
| TC-062, TC-063 | race 2 IM Đồng bộ thủ công | race **2×L2** |

## 3. Chi tiết test case (Detailed Test Cases)

### TC-001: Menu Resource Plan hiển thị theo quyền

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-001
**Facets:** read, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- User thuộc nhóm Invoice Manager / Department Manager / Delivery Manager.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đăng nhập, mở module Project Invoice | Thấy menu "Resource Plans" |
| 2 | Mở menu | Hiển thị danh sách plan + nút Tạo plan |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user_group | group_project_invoice_manager | |

**Postconditions:** Không thay đổi dữ liệu.

### TC-002: Tạo resource plan gắn 1 dự án

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-002
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Tồn tại dự án HBU_123.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Tạo plan, chọn dự án HBU_123 | Plan lưu với project_id = HBU_123 |
| 2 | Bỏ trống dự án rồi lưu | Bị chặn (project_id NOT NULL) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| project | HBU_123 | |

**Postconditions:** 1 bản ghi resource_plan tồn tại.

### TC-003: Mở lại plan đã lưu

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-002
**Facets:** read
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Plan HBU_123 đã có 3 dòng.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đóng và mở lại plan | Hiển thị đúng dự án + 3 dòng đã nhập |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan | HBU_123 (3 dòng) | |

**Postconditions:** Không đổi dữ liệu.

### TC-004: Cửa sổ mặc định 8 tháng (current−2…current+5)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-003
**Facets:** read, ui
**Category:** Functional
**Severity:** High
**Preconditions:**

- Plan mới; "current" tháng được **freeze = 2026-06** trong test (tránh flakiness do thời gian chạy).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở plan với current=2026-06 | Lưới hiển thị đúng 8 cột: 2026-04 … 2026-11 (current−2 → current+5) |
| 2 | Kiểm tháng trống | Tháng không có MM vẫn hiển thị cột (không bị ẩn) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| current (freeze) | 2026-06 | Cố định thời gian để test ổn định |

**Postconditions:** Không đổi dữ liệu.

### TC-005: from > to bị từ chối

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-003
**Facets:** write
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Plan mới.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chọn from=2026-03, to=2026-01 | Báo lỗi khoảng tháng; không lưu |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| from / to | 2026-03 / 2026-01 | Negative |

**Postconditions:** Không tạo plan.

### TC-006: Lưu dòng thiếu employee/rate bị chặn

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-004
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Plan draft.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Thêm dòng không chọn nhân viên, lưu | Bị chặn (employee NOT NULL) |
| 2 | Chọn nhân viên, bỏ trống rate, lưu | Bị chặn (rate NOT NULL) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee / rate | (trống) | Negative |

**Postconditions:** Dòng không được lưu.

### TC-007: Chỉ chọn nhân viên approved

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-005
**Facets:** read, write
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Có nhân viên approved và non-approved.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở dropdown nhân viên | Chỉ liệt kê process_state='approved' |
| 2 | Thử gán nhân viên non-approved qua API | Bị từ chối |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee.process_state | approved / draft | |

**Postconditions:** Không đổi dữ liệu.

### TC-008: Dept/Role tự hiển thị read-only

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-006
**Facets:** read, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Nhân viên HuanTV thuộc HBU, role Tech Lead.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chọn nhân viên HuanTV | Cột Bộ phận=HBU, Role=Tech Lead tự hiện |
| 2 | Thử sửa trực tiếp cột Bộ phận/Role | Read-only, không sửa được |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee | HuanTV | |

**Postconditions:** Không đổi dữ liệu.

### TC-009: Allocation % khớp project.member

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-007
**Facets:** read
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Allocation HuanTV effort_ratio=50%.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Pre-fill dòng HuanTV | Cột Allocation hiển thị 50% |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| project_member.effort_ratio | 0.5 | |

**Postconditions:** Không đổi dữ liệu.

### TC-010: Đơn giá chỉ chọn từ bảng rate

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-008
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Bảng rate có rate 350,000.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chọn rate 350,000 | Lưu rate_id hợp lệ |
| 2 | Thử gán rate_id không tồn tại qua API | Bị từ chối (FK) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| rate | 350,000 | |

**Postconditions:** Dòng có rate_id hợp lệ.

### TC-011: Nhập MM=0.5 lưu đúng

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-009
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Dòng HuanTV, cột tháng 06/2026.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Nhập MM=0.5 cho 06/2026 | resource_plan_line_month.effort_mm = 0.5 |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| effort_mm | 0.5 | Boundary (nửa tháng) |

**Postconditions:** Ô MM lưu 0.5.

### TC-012: MM âm / không phải số bị từ chối

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-009
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Dòng bất kỳ.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Nhập MM = -1 | Bị từ chối (CHECK effort_mm >= 0) |
| 2 | Nhập "abc" | Bị từ chối (không phải số) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| effort_mm | -1 / "abc" | Negative |

**Postconditions:** Giá trị không hợp lệ không được lưu.

### TC-013: Pre-fill từ allocation

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-010
**Facets:** read
**Category:** Integration
**Severity:** High
**Preconditions:**

- Dự án có 2 allocation giao với khoảng plan.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở plan cho dự án + khoảng | Lưới pre-fill đúng 2 dòng với employee/role/allocation tương ứng |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| allocations | 2 (HuanTV, NamNV) | |

**Postconditions:** Không tạo allocation mới (chỉ đọc).

### TC-014: Thêm dòng tay → tạo allocation

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-011
**Facets:** write
**Category:** Integration
**Severity:** High
**Preconditions:**

- Plan draft; nhân viên LanTT chưa có allocation ở dự án.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Thêm dòng LanTT, nhập allocation% + rate, lưu | Tồn tại project.member mới cho (dự án, LanTT) khớp allocation% + khoảng |
| 2 | Kiểm tra line.member_id | Trỏ tới allocation vừa tạo |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee | LanTT | |

**Postconditions:** 1 project.member mới + line.member_id set.

### TC-015: Sửa allocation % → cập nhật project.member

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-012
**Facets:** write
**Category:** Integration
**Severity:** High
**Preconditions:**

- Dòng có member_id.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa allocation% dòng từ 50%→80% | project.member.effort_ratio = 0.8 |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| effort_ratio | 0.5 → 0.8 | |

**Postconditions:** Allocation đồng bộ giá trị mới.

### TC-016: Xóa dòng → set end_at (không xóa cứng)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-013
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Dòng có member_id, allocation đang hiệu lực.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Xóa dòng trong plan | project.member KHÔNG bị xóa; end_at set về cuối khoảng plan |
| 2 | Mở lại plan | Dòng không còn pre-fill cho khoảng sau end_at |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan range | 04–06/2026 | end_at = 2026-06-30 |

**Postconditions:** Allocation giữ lịch sử, hết hiệu lực sau end_at.

### TC-017: Đồng bộ khoảng 3 tháng tạo đủ period(draft) + member (overlay MM/rate)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014
**Facets:** write, batch, lifecycle
**Category:** Integration
**Severity:** Critical
**Preconditions:**

- DelM đã Submit request (snapshot có dòng MM>0 ở cả 3 tháng), DeptM đã duyệt L1; user = Invoice Manager sắp duyệt L2; không tháng nào đã-chốt.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 0 | **Sanity (anti-false-green):** xác nhận giá trị snapshot (MM/price/effort_ratio) **khác** mặc định generate_lines (0/False/weighted) | Nếu trùng mặc định thì bước 3 vô nghĩa → fixture phải dùng giá trị phi-mặc-định |
| 1 | IM duyệt **L2** request (khoảng snapshot 04–06/2026) | Đồng bộ chạy **trong transaction L2**: verify hash OK → set `active_request_id` → **find-or-create** 3 `project.invoice.period` theo (project, tháng), mỗi period `draft`; không tạo period trùng |
| 2 | Kiểm member line mỗi period | Mỗi dòng snapshot MM>0 → 1 member với employee/dept/role khớp khung `action_generate_lines` |
| 3 | Kiểm `effort_mm`, `rate_id`, `effort_ratio` mỗi member | **effort_mm/rate_id/effort_ratio = giá trị từ SNAPSHOT** (không phải plan live, không phải `0`/`False`/weighted mặc định generate_lines) |
| 4 | Kiểm `amount` | amount = MM × price (từ snapshot, ≠ 0) |
| 5 | Re-run đồng bộ trên cùng request | **Idempotent** — vẫn đúng 3 period, không nhân đôi member (xem TC-093) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| snapshot range | 04–06/2026 | |
| request.state khi đồng bộ | approved_l2 | Đồng bộ là sự kiện ở L2 (xem TC-044) |
| MM / price / effort_ratio (snapshot) | 1.0 / 350,000 / 0.5 | amount kỳ vọng 350,000 (≠ 0) |

**Postconditions:** 3 period(draft) + member overlay từ snapshot; `active_request_id` = request vừa L2; find-or-create không tạo period trùng.

### TC-018: amount = MM × đơn giá

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-015
**Facets:** write
**Category:** Functional
**Severity:** Critical
**Preconditions:**

- Dòng rate=350,000.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | MM=1.0 → Generate | member.amount = 350,000 |
| 2 | MM=0.5 → Generate | member.amount = 175,000 |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| rate / MM | 350,000 / {1.0, 0.5} | Boundary |

**Postconditions:** Amount đúng công thức.

### TC-019: Đồng bộ lại replace member lines tháng chưa-chốt

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-016
**Facets:** write, batch
**Category:** Integration
**Severity:** High
**Preconditions:**

- Tháng 05/2026 đã đồng bộ lần 1 với 2 nhân viên A + B (period chưa-chốt: state ∈ {draft, review, submitted}); sau đó **xóa B khỏi plan** và đổi 1 MM của A.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đồng bộ lại 05/2026, xác nhận | **Unlink toàn bộ member cũ rồi sinh lại** từ plan hiện tại |
| 2 | Kiểm member B | Member B **biến mất** (nhờ unlink) — không còn dòng thừa của nhân viên đã xóa khỏi plan |
| 3 | Kiểm member A | Còn đúng 1 dòng A với MM mới |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| month | 05/2026 | |
| plan | lần 1: A+B; sau: bỏ B | Assert B biến mất sau Đồng bộ lại |

**Postconditions:** Member lines = ảnh chiếu plan hiện tại (chỉ A); B đã bị unlink.

### TC-020: Blocking confirm khi IM duyệt L2 mà snapshot sẽ ghi đè billable đã có

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-017
**Facets:** write, ui, lifecycle
**Category:** Functional
**Severity:** High
**Preconditions:**

- request ở approved_l1, snapshot bao tháng 05/2026; period 05/2026 chưa-chốt **đã có member lines** (từ chu kỳ trước).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM bấm **Duyệt L2** | Hiện **hộp xác nhận chặn (blocking confirm)** "dữ liệu billable hiện có (tháng chưa-chốt) sẽ bị ghi đè từ snapshot" |
| 2 | Bấm Hủy | **Request CHƯA L2** (vẫn approved_l1); không period/member nào đổi |
| 3 | Duyệt L2 lại, bấm Đồng ý | Áp snapshot → member lines bị ghi đè; request → approved_l2 |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| period 05/2026 | đã có lines | Confirm fire ở bước duyệt L2 (REQ-017), không phải nút "đồng bộ lại" |

**Postconditions:** Hủy → request giữ approved_l1, dữ liệu nguyên; Đồng ý → L2 + ghi đè từ snapshot.

### TC-021: Đồng bộ bỏ qua tháng locked + báo "đã khóa"

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-018
**Facets:** lifecycle, batch
**Category:** Integration
**Severity:** Critical
**Preconditions:**

- Khoảng gồm 04/2026 (period `locked`) + 05,06 chưa-chốt.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM Đồng bộ cả khoảng | 04/2026 giữ nguyên; 05,06 được tạo/ghi đè |
| 2 | Kiểm kết quả có cấu trúc | 04/2026 trả về `committed_reason = locked` (assert giá trị enum, KHÔNG parse chuỗi tiếng Việt) |
| 3 | Xem report/thông báo | Liệt kê 04/2026 bị bỏ qua, hiển thị "đã khóa" |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| 04/2026.state | locked | committed_reason=locked |

**Postconditions:** Period locked không đổi.

### TC-022: Không sửa được member ở period locked

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-018
**Facets:** lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Period 04/2026 = locked.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Thử write/create/delete member của period locked qua API | Raise UserError |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| period.state | locked | Negative |

**Postconditions:** Không thay đổi member period locked.

### TC-023: Hiển thị trạng thái từng cột tháng

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-019
**Facets:** read, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Khoảng có tháng chưa generate, đã generate, đã khóa.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở plan | Mỗi cột tháng hiện chỉ báo đúng (chưa generate/đã generate/đã khóa) theo period.state |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| months | mixed states | |

**Postconditions:** Không đổi dữ liệu.

### TC-024: Phân quyền plan theo workflow; chỉ IM thấy nút Đồng bộ

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-020
**Facets:** admin, read
**Category:** Security
**Severity:** High
**Preconditions:**

- Có user Delivery Manager / Department Manager / Invoice Manager + 1 user ngoài 3 nhóm.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | User trong 3 nhóm mở module | Thấy menu Resource Plan |
| 2 | Kiểm nút Đồng bộ | **Chỉ Invoice Manager** thấy/nhấn được nút Đồng bộ; Delivery/Dept không thấy |
| 3 | User ngoài 3 nhóm mở/gọi Đồng bộ | Không thấy menu; hành động bị từ chối quyền |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user_group | delivery / dept / IM / out | Negative ở bước 3 |

**Postconditions:** Không đổi dữ liệu.

### TC-025: Chặn Đồng bộ khi plan không hợp lệ

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-021
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Plan rỗng / không dòng nào MM>0 / dòng thiếu rate.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đồng bộ plan rỗng | Bị chặn, nêu lý do; không tạo period |
| 2 | Đồng bộ plan tất cả MM=0 | Bị chặn tương tự |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan | rỗng / MM=0 | Negative |

**Postconditions:** Không tạo period nào.

### TC-026: Khớp snapshot generate_lines; MM/rate/effort_ratio overlay từ plan

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-022
**Facets:** write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Cùng dữ liệu đầu vào cho resource plan và `action_generate_lines`.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sinh member line từ resource plan (Đồng bộ) | Tập snapshot field khung (employee_name, department_id, project_role_id…) khớp output `action_generate_lines` cho cùng input; Đồng bộ tự **unlink** member cũ trước (generate_lines KHÔNG unlink) |
| 2 | So sánh `effort_mm`/`rate_id`/`effort_ratio` | generate_lines đặt effort_mm=0/rate_id=False/effort_ratio **weighted**; sau overlay của Đồng bộ → cả ba lấy **từ plan** (effort_ratio = allocation% của plan, ≠ giá trị weighted; effort_mm/rate ≠ 0/False) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| input | giống nhau | Khung từ generate_lines; MM/rate/effort_ratio overlay từ plan |

**Postconditions:** Khung snapshot nhất quán; MM/rate/effort_ratio là của plan (effort_ratio ≠ weighted).

### TC-027: Sync một chiều — sửa allocation ngoài plan không đổi plan

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-023
**Facets:** write, read
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan đã lưu với dòng HuanTV.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa effort_ratio của allocation HuanTV qua màn project.member | Allocation đổi |
| 2 | Mở lại plan đã lưu | Dòng plan giữ giá trị đã lưu, không tự đổi theo allocation ngoài |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| effort_ratio (ngoài plan) | đổi | |

**Postconditions:** Plan không bị sync ngược.

### TC-028: DelM Submit → tạo request(submitted) + snapshot

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024, REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** lifecycle, write
**Category:** Integration
**Severity:** High
**Preconditions:**

- Plan (stateless) đã khai dòng; user = Delivery Manager phụ trách dự án; không có request in-flight.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM bấm Submit | Tạo `resource.plan.request` state = **submitted**, gắn plan + project + người submit |
| 2 | Kiểm snapshot (`request.line`) | Mỗi dòng plan có MM>0 → 1 snapshot-line grain (employee,role,month), giá-trị-copy (employee_name/role/department/mm/price/currency/effort_ratio); `snapshot_hash` được tính |
| 3 | Kiểm plan | Plan KHÔNG có state; vẫn editable |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| request.state | submitted | Vòng đời nằm trên request |

**Postconditions:** request(submitted) + snapshot bất biến + hash; plan stateless.

### TC-029: DeptM duyệt L1 → IM duyệt L2 → đồng bộ tự động từ snapshot

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** lifecycle, admin
**Category:** Integration
**Severity:** High
**Preconditions:**

- request ở submitted (snapshot hợp lệ).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Department Manager duyệt L1 | request: submitted → **approved_l1** |
| 2 | Invoice Manager duyệt L2 | request: approved_l1 → **approved_l2**; đồng bộ **tự động trong transaction L2** từ snapshot (xem TC-017) |
| 3 | Kiểm `active_request_id` | plan.active_request_id = request vừa L2 |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| flow | submitted → L1 → L2 | 2 cấp trên request |

**Postconditions:** request approved_l2; đồng bộ đã chạy; active_request_id set.

### TC-030: Reject terminal → active giữ nguyên; resubmit = request mới

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Đã có request L2 trước đó (active_request_id trỏ request cũ); request mới đang ở submitted hoặc approved_l1.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Reject (Trả lại) kèm lý do (DeptM@submitted hoặc IM@approved_l1) | request → **rejected** (terminal — không transition tiếp) |
| 2 | Kiểm `active_request_id` | **Giữ nguyên** trỏ request L2 cũ (billable cũ vẫn là nguồn) |
| 3 | DelM Submit lại | Tạo **request mới** (1-in-flight mở lại); request rejected không tái dùng |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| request.state | submitted/approved_l1 → rejected | Reject terminal |

**Postconditions:** request rejected; active_request_id không đổi; resubmit tạo request mới.

### TC-031: Non-Dept/non-IM không duyệt được cấp tương ứng

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** admin
**Category:** Security
**Severity:** High
**Preconditions:**

- Plan ở Submitted (cho L1) và ở Approved L1 (cho L2).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | User ngoài Dept Manager thử duyệt L1 | Không có nút/bị từ chối quyền |
| 2 | User ngoài Invoice Manager thử duyệt L2 | Không có nút/bị từ chối quyền |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user_group | non-dept / non-IM | Negative |

**Postconditions:** Plan không đổi trạng thái.

### TC-032: Đồng bộ lỗi giữa chừng → all-or-nothing, toàn bộ L2 rollback

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014
**Facets:** write, batch, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- request approved_l1, snapshot 3 tháng (04/05/06); mô phỏng lỗi khi tạo member cho tháng 05 (tháng giữa).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM duyệt L2 (sync chạy trong cùng transaction), lỗi ở tháng 05 | **Raise → toàn bộ transaction L2 rollback** (all-or-nothing) |
| 2 | Kiểm request.state | Vẫn **approved_l1** (KHÔNG lên approved_l2) |
| 3 | Kiểm period/member tháng 04 (đã xử lý trước khi lỗi) | **KHÔNG còn** — rollback cả tháng 04, không commit từng phần |
| 4 | Kiểm active_request_id | Không bị set (giữ giá trị cũ/NULL) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| fault inject | member create error tháng 05 | NFR-005 all-or-nothing |

**Postconditions:** L2 không thành công → mọi tháng rollback, request ở approved_l1, không trạng thái dở dang.

### TC-033: Lưới frozen-pane

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-019
**Facets:** read, ui
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan 40 dòng × 6 tháng (E2E Playwright).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Scroll dọc | Hàng header đứng yên |
| 2 | Scroll ngang qua cột tháng | Cột định danh trái đứng yên |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| grid | 40×6 | |

**Postconditions:** Không đổi dữ liệu.

### TC-034: Accessibility — tab-traversal + aria-invalid

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-009
**Facets:** ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- E2E Playwright trên lưới.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Dùng Tab duyệt qua các ô MM | Focus đi theo thứ tự row-major; ô khóa báo read-only |
| 2 | Nhập MM âm | Ô có aria-invalid + thông báo lỗi đọc được (không chỉ tô đỏ) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| effort_mm | -1 | |

**Postconditions:** Không đổi dữ liệu.

### TC-035: Accessibility — dialog Đồng bộ focus trap + Esc

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-017
**Facets:** ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

> ⚠️ **E2E PENDING DESIGN** — dialog cụ thể chốt sau update Claude Design (bước cascade kế tiếp).

- E2E Playwright; request approved_l1 có period chưa-chốt đã có lines → duyệt L2 bật blocking confirm (REQ-017).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở dialog blocking confirm khi **bấm Duyệt L2** | Focus bị trap trong dialog |
| 2 | Bấm Esc | Dialog đóng (Hủy), focus trả về nút Duyệt L2, request giữ approved_l1, không ghi đè |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| dialog | Blocking confirm khi duyệt L2 (REQ-017) | |

**Postconditions:** Không thay đổi dữ liệu; request vẫn approved_l1.

### TC-036: Row-level — Delivery Manager không mở plan dự án ngoài phạm vi

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-020
**Facets:** admin
**Category:** Security
**Severity:** High
**Preconditions:**

- Delivery Manager D1 phụ trách dự án A; plan thuộc dự án B (D1 không phụ trách).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | D1 mở plan dự án B | Bị từ chối (record rule), không thấy/không mở được |
| 2 | D1 mở plan dự án A | Mở được bình thường |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user / plan | D1 / plan(B) | Negative ở bước 1 |

**Postconditions:** Không đổi dữ liệu.

### TC-037: Department Manager chỉ sửa dòng bộ phận mình

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-020
**Facets:** admin, write
**Category:** Security
**Severity:** High
**Preconditions:**

- Plan có dòng nhân sự HBU và dòng bộ phận khác (DEV); user = Department Manager bộ phận HBU.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa/xóa dòng nhân sự HBU | Cho phép |
| 2 | Sửa/xóa dòng nhân sự DEV | Read-only / bị từ chối |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user_dept / row_dept | HBU / DEV | Negative ở bước 2 |

**Postconditions:** Dòng bộ phận khác không đổi.

### TC-038: Reject terminal kèm lý do; resubmit = request mới

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** lifecycle
**Category:** Functional
**Severity:** High
**Preconditions:**

- request ở submitted (cấp L1) hoặc approved_l1 (cấp L2).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Dept Manager bấm "Trả lại" ở submitted, nhập lý do | request → **rejected** (terminal), lưu lý do |
| 2 | IM bấm "Trả lại" ở approved_l1, nhập lý do | request → **rejected** (terminal), lưu lý do |
| 3 | DelM sửa plan và Submit lại | Tạo **request mới** (request rejected không tái dùng) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| reason | "Sai đơn giá" | Reject ở submitted/approved_l1 |

**Postconditions:** request rejected (terminal); resubmit tạo request mới.

### TC-039: Tự duyệt (self-approval cho phép)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** admin, lifecycle
**Category:** Security
**Severity:** Medium
**Preconditions:**

- Người duyệt cũng là người đã sửa/khai plan ở cùng cấp.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Cùng người vừa sửa bấm Duyệt | Cho phép (không chặn self-approval); plan chuyển cấp |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user | người sửa = người duyệt | |

**Postconditions:** Plan chuyển trạng thái thành công.

### TC-040: Sync thiếu quyền project.member → từ chối

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-025
**Facets:** write, admin
**Category:** Security
**Severity:** High
**Preconditions:**

- User được sửa plan nhưng KHÔNG có quyền ghi `project.member`.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Thêm/sửa/xóa dòng plan (kích hoạt sync) | Bị từ chối kèm thông báo quyền; allocation không đổi |
| 2 | Cấp quyền project.member rồi thử lại | Sync thành công |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| project_member write | no / yes | Negative ở bước 1 |

**Postconditions:** Không sửa allocation khi thiếu quyền.

### TC-041: Đồng bộ (L2) ghi đè cả sửa tay trên period

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-026
**Facets:** write, batch
**Category:** Integration
**Severity:** High
**Preconditions:**

- Period 05/2026 đã sinh từ lần L2 trước (chưa-chốt); một member line đã bị sửa tay qua màn period; có request mới được duyệt tới L2.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 0 | **Sanity (anti-false-green):** assert member sửa tay hiện ≠ giá trị snapshot request mới | Đảm bảo fixture thực sự khác nhau trước khi assert ghi đè (nếu trùng → test vô nghĩa) |
| 1 | IM duyệt L2 request mới (snapshot 05/2026) | Sửa tay bị thay bằng dữ liệu **snapshot** (snapshot là nguồn sự thật) |
| 2 | Kiểm member | effort_mm/rate/effort_ratio = snapshot, không còn giá trị sửa tay |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| manual edit | member.effort_mm sửa tay | Bị overlay lại từ snapshot khi L2 |

**Postconditions:** Member line khớp snapshot active.

### TC-042: Sửa đồng thời — optimistic conflict cấp plan (false-conflict)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-027
**Facets:** write
**Category:** Integration
**Severity:** High
**Preconditions:**

- User A và user B cùng mở plan P (cùng `write_date`); A và B sửa **2 dòng khác nhau** (không thật sự xung đột nội dung — false-conflict nhưng vẫn bị chặn vì optimistic ở cấp plan).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 0 | **Sanity-check:** ghi lại `resource_plan.write_date`, sửa 1 ô MM của 1 dòng rồi lưu | `resource_plan.write_date` **đổi** sau khi sửa ô MM (mọi create/write/unlink line touch parent write_date) — chứng minh token cấp plan phản ánh sửa cấp dòng |
| 1 | A sửa dòng 1 và lưu | A lưu thành công; `write_date` plan đổi |
| 2 | B (đã tải bản cũ) sửa dòng 2 và lưu | B bị từ chối (write_date lệch): "Dữ liệu đã thay đổi, vui lòng tải lại" — kể cả khi B sửa dòng khác A |
| 3 | B tải lại rồi sửa và lưu | B lưu thành công |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| sanity | sửa 1 ô MM | assert write_date parent đổi (tiền đề cho optimistic lock) |
| sessions | A sửa dòng 1, B sửa dòng 2 | false-conflict, optimistic cấp plan |

**Postconditions:** Không mất dữ liệu của A; B lưu lại có ý thức sau khi tải lại.

### TC-043: Đồng bộ cảnh báo khi còn thay đổi chưa lưu

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-027
**Facets:** write
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Phiên hiện tại có thay đổi chưa lưu trên plan.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Bấm Đồng bộ khi còn nháp chưa lưu | Hiện cảnh báo "có thay đổi chưa lưu"; Đồng bộ dùng dữ liệu đã lưu (committed) |
| 2 | Lưu rồi Đồng bộ lại | Đồng bộ dùng đúng dữ liệu mới nhất |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| unsaved | có | |

**Postconditions:** Không Đồng bộ nhầm trên dữ liệu nháp chưa commit.

### TC-044: Đồng bộ xảy ra đúng khi request đạt approved_l2

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014
**Facets:** lifecycle, admin
**Category:** Integration
**Severity:** High
**Preconditions:**

- request đi qua submitted / approved_l1 / approved_l2.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Kiểm sau submitted / approved_l1 | CHƯA đồng bộ: không có period/member sinh ra từ snapshot |
| 2 | IM duyệt L2 (approved_l2) | Đồng bộ **tự động** chạy đúng tại sự kiện L2 → tạo period(draft) + member từ snapshot |
| 3 | Không có action "Đồng bộ" thủ công riêng | Đồng bộ là hệ quả của L2, không phải nút bấm độc lập |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| request.state | submitted/approved_l1 (chưa sync) → approved_l2 (sync) | Sync gắn với L2 |

**Postconditions:** Đồng bộ chỉ xảy ra ở approved_l2.

### TC-045: Đồng bộ lại tháng chưa có lines → KHÔNG hiện blocking confirm

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-017
**Facets:** write, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Tháng 06/2026 có period chưa-chốt nhưng CHƯA có member line nào (rỗng).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đồng bộ 06/2026 | KHÔNG hiện blocking confirm (vì chưa có lines để ghi đè); ghi thẳng |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| month | 06/2026 (không lines) | Confirm chỉ khi đã có lines |

**Postconditions:** Member lines mới được tạo, không cần xác nhận.

### TC-046: Summary pivot Department→Project→Member + default filter

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-028
**Facets:** read, ui
**Category:** Integration
**Severity:** High
**Preconditions:**

- Có plan của ≥2 dự án (1 closed, 1 chưa closed), năm hiện tại 2026 + 1 plan năm trước.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở menu Resource Plan Summary | Pivot trục hàng Department → Project → Member; trục cột là tháng |
| 2 | Kiểm chỉ số ô | MM, đơn giá, thành tiền, đơn vị tiền tệ đúng theo **snapshot active** (request L2 mới nhất của project) |
| 3 | Kiểm default filter | Chỉ liệt kê dự án chưa closed, năm hiện tại (loại dự án closed + năm trước) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| projects | closed / open; 2025 / 2026 | Default filter |

**Postconditions:** Không đổi dữ liệu.

### TC-047: Summary đọc snapshot active — sửa plan KHÔNG đổi Summary; rebuild khi L2 ("xanh giả" sanity)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-029
**Facets:** read
**Category:** Integration
**Severity:** High
**Preconditions:**

- Project đã có request L2 (snapshot active) phản ánh vào Summary; Summary `resource.plan.summary` là model stored **đọc/rebuild từ snapshot active** (request L2 mới nhất), rebuild khi sự kiện L2 — KHÔNG refresh theo sửa plan.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | **Sanity (xanh giả):** sửa MM/rate 1 dòng plan (KHÔNG submit/L2) rồi mở Summary | Summary **KHÔNG đổi** — vẫn = snapshot active (chứng minh đọc snapshot, không phải plan live) |
| 2 | DelM Submit + duyệt tới L2 request mới | Summary **rebuild** từ snapshot mới → phản ánh giá trị đã L2 |
| 3 | Reject request mới (chưa L2) | Summary giữ snapshot L2 trước (không đổi) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| op | sửa plan (không L2) vs duyệt L2 | Bước 1 phải đổi plan TRƯỚC khi assert → tránh "xanh giả" |

**Postconditions:** Summary = snapshot active; chỉ đổi khi có request L2 mới; sửa plan đơn thuần không ảnh hưởng.

### TC-048: Summary pivot đa-currency tách theo currency (không cộng lẫn)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-028, REQ-RESOURCE-PLAN-BILLABLE-029
**Facets:** read
**Category:** Integration
**Severity:** High
**Preconditions:**

- Plan có dòng rate currency=VND và dòng rate currency=USD trong cùng Department/Project.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở Summary pivot | Thành tiền tách theo currency (VND và USD ở 2 nhóm/giá trị riêng) |
| 2 | Kiểm tổng nhóm | Amount đa-currency **KHÔNG cộng lẫn** (không có tổng gộp VND+USD thành 1 số) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| rate.price_currency_id | VND + USD cùng Project | Tách theo currency |

**Postconditions:** Không đổi dữ liệu; pivot tách đúng theo currency.

### TC-049: Cột Đơn vị tiền tệ liền sau Đơn giá; ăn theo rate.price_currency_id

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-030
**Facets:** read, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- 2 rate có currency khác nhau (VND, USD).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở grid plan + summary | Cột Đơn vị tiền tệ xuất hiện liền ngay sau cột Đơn giá |
| 2 | Chọn rate currency=VND | Cột Đơn vị tiền tệ = VND (= rate.price_currency_id) |
| 3 | Đổi sang rate currency=USD | Cột Đơn vị tiền tệ cập nhật = USD |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| rate.price_currency_id | VND / USD | Ăn theo rate |

**Postconditions:** Không đổi dữ liệu.

### TC-050: Hiển thị Department (HB) và OB Delivery (BU)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-031
**Facets:** read, ui
**Category:** Functional
**Severity:** Low
**Preconditions:**

- Dự án/nhân sự có Department (HB) và OB Delivery (BU).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở form/grid plan | Hiển thị đúng Department (HB) và OB Delivery (BU) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| HB / BU | có giá trị | |

**Postconditions:** Không đổi dữ liệu.

### TC-051: Cửa sổ 8 tháng theo tz server (freeze current) + thêm tháng ngoài cửa sổ

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-032
**Facets:** read, write, ui
**Category:** Functional
**Severity:** High
**Preconditions:**

- "current" freeze = 2026-06 theo timezone server (UTC), chuẩn hóa về ngày đầu tháng.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở plan với current freeze 2026-06 | Mặc định hiển thị 2026-04 … 2026-11 (current−2 → current+5) |
| 2 | Thêm tháng 2026-12 (ngoài cửa sổ) | Cộng dồn vào cùng plan; không tạo plan thứ hai |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| current (freeze) | 2026-06 (server tz) | Cố định để test ổn định |

**Postconditions:** Plan giữ thêm tháng ngoài cửa sổ.

### TC-052: Tháng đã-chốt — plan editable, billable bị guard

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-033, REQ-RESOURCE-PLAN-BILLABLE-042
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Tháng X có period đã-chốt (state ∈ {approved, sent, paid, locked}); tháng Y chưa-chốt.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa dòng/MM của tháng X **trên plan** | **Cho phép** (plan stateless luôn editable — REQ-042); thay đổi chỉ vào invoice khi Submit→L2 |
| 2 | Đồng bộ (L2) chạm tháng X | **Bỏ qua tháng X** (billable bị guard); báo "đã có/đã khóa"; `month_has_committed_invoice(project, X)` = True (assert enum, không parse chuỗi) |
| 3 | Đồng bộ (L2) chạm tháng Y | Ghi member bình thường |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| period(X).state | approved | Guard ở billable, không ở plan |

**Postconditions:** Plan tháng đã-chốt vẫn sửa được; billable tháng đã-chốt bị guard khi đồng bộ.

### TC-053: Migrate lần 1 tạo request(approved_l2) + snapshot từ invoice nguồn

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-034
**Facets:** batch, write
**Category:** Integration
**Severity:** High
**Preconditions:**

- DB có project invoice hiện hữu (gồm 1 tháng đã-chốt, 1 tháng chưa-chốt) với member lines; chưa có resource plan/request.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chạy migrate lần 1 | Tạo plan (stateless) + **`resource.plan.request` state `approved_l2`** + **snapshot copy từ invoice nguồn** (MM/price lịch sử của member, grain (employee,role,month)); set `active_request_id` |
| 2 | Kiểm **cơ chế** | Migration **insert trực tiếp** record request ở `approved_l2` (KHÔNG gọi `action_approve_l2`) → nhánh Đồng bộ REQ-041 **không** chạy |
| 3 | Kiểm invoice | **KHÔNG re-sync** — period/member invoice cũ giữ nguyên (invoice cũ là chân lý) |
| 4 | Xem report đối chiếu | **số snapshot-line == số member nguồn** VÀ tổng amount snapshot == tổng amount invoice nguồn; Summary (đọc snapshot) khớp invoice cũ |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| source | invoice hiện hữu | request.state=approved_l2; snapshot từ member nguồn |

**Postconditions:** request approved_l2 + snapshot khớp invoice cũ; invoice không đổi; active_request_id set.

### TC-054: Migrate idempotent — rerun không dup request/snapshot

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-034
**Facets:** batch, write
**Category:** Integration
**Severity:** High
**Preconditions:**

- Đã migrate lần 1 (plan line + request approved_l2 + snapshot + cờ `migrated`).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chạy migrate lần 2 | `created = 0`; upsert dòng plan idempotent theo **khóa (project_id, employee, role, month) + cờ `migrated`** (khớp D-02 REQ-034); không tạo plan-line/request/snapshot trùng |
| 2 | Kiểm invoice | Vẫn không bị re-sync/đổi |
| 3 | Xem report | **số snapshot-line == số member nguồn** (không phát sinh dup) VÀ vẫn khớp tổng amount |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| rerun | lần 2 | Idempotent |

**Postconditions:** Không dup request/snapshot; invoice bảo toàn.

### TC-055: Thêm tháng mới trên form → cộng dồn vào plan duy nhất

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-035
**Facets:** write, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Dự án đã có resource plan.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Trên form plan, thêm tháng mới | Cột tháng đó xuất hiện trên cùng plan |
| 2 | Kiểm số bản ghi plan của dự án | Vẫn đúng 1 (không tạo plan thứ hai) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| new month | 2026-12 | Cộng dồn |

**Postconditions:** Plan duy nhất, có thêm tháng.

### TC-056: Invoice — IM edit/delete đầy đủ; QA edit period chưa-chốt KHÔNG delete; nhóm cũ view-only

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-036
**Facets:** admin, write
**Category:** Security
**Severity:** High
**Preconditions:**

- User IM, QA, và user nhóm cũ (Delivery/Dept/PM/FPM); QA group = `project_report.group_project_report_qa`.
- Có period chưa-chốt (state ∈ {draft, review, submitted}) và period đã-chốt (approved).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM mở invoice → edit/delete (state cho phép) | Cho phép edit **và** delete đầy đủ |
| 2 | QA mở period chưa-chốt → edit member | Cho phép edit |
| 3 | QA cố delete member của period chưa-chốt | Bị chặn (ACL `unlink=0` — QA KHÔNG delete) |
| 4 | QA cố delete member của period **approved** (đã-chốt) | Bị chặn (record rule giới hạn state + ACL unlink=0) |
| 5 | QA cố edit member của period **approved** | Bị chặn (record rule giới hạn draft/review/submitted) |
| 6 | User nhóm cũ mở invoice → edit/delete | Chỉ xem; bị từ chối edit/delete (ir.model.access + record rule) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user_group | IM / QA / nhóm cũ | QA = project_report.group_project_report_qa |
| period.state | draft/submitted (chưa-chốt) / approved (đã-chốt) | Negative ở bước 3/4/5/6 |

**Postconditions:** IM edit/delete được; QA chỉ edit period chưa-chốt (không delete, không động period đã-chốt); nhóm cũ view-only.

### TC-057: Đồng bộ khoảng có tháng đã-chốt → bỏ qua + "đã có"

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-037
**Facets:** batch, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Khoảng gồm tháng X period đã-chốt (approved/sent/paid) + các tháng chưa-chốt.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM Đồng bộ cả khoảng | Tháng X bị bỏ qua; các tháng chưa-chốt được đồng bộ |
| 2 | Kiểm kết quả có cấu trúc | Tháng X trả về `committed_reason ∈ {approved, sent, paid}`; thông báo hiển thị "đã có" |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| period(X).state | approved | "đã có" (khác "đã khóa" của locked) |

**Postconditions:** Tháng đã-chốt giữ nguyên.

### TC-058: Period sau Đồng bộ ở draft → QA đẩy tới submitted, DM/Admin/IM duyệt cuối → approved

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-038
**Facets:** lifecycle, admin
**Category:** Integration
**Severity:** High
**Preconditions:**

- Vừa Đồng bộ xong, period ở state `draft`; QA = `project_report.group_project_report_qa`; project có `delivery_manager_user_id`.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Kiểm state period sau Đồng bộ | `draft` |
| 2 | QA thao tác/duyệt period | Đẩy được tới `submitted` (record rule QA giới hạn draft/review/submitted) |
| 3 | QA cố tự đẩy period sang `approved` | Bị từ chối — QA KHÔNG tự duyệt cuối |
| 4 | DM/Admin/IM duyệt cuối (`action_approve_delivery` → `delivery_approved` → `_try_set_approved`) | Period → `approved` |
| 5 | User ngoài QA/DM/Admin/IM duyệt period | Bị từ chối |
| 6 | Duyệt cuối khi project thiếu `delivery_manager_user_id` | `UserError` "Missing manager user…" (precondition REQ-038) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| flow | draft → (QA) submitted → (IM) approved | QA tới submitted, IM duyệt cuối |
| user_group | QA / IM / khác | Negative ở bước 3/5 |

**Postconditions:** Period đi draft → submitted (QA) → approved (IM), độc lập vòng đời plan; QA không tự đẩy sang approved.

### TC-059: Bảng chân trị — predicate + committed_reason (assert enum)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-018
**Facets:** lifecycle, batch
**Category:** Functional
**Severity:** High
**Preconditions:**

- Tập tháng phủ mọi hàng bảng chân trị: (chưa có period) / draft / review / submitted / approved / sent / paid / locked.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | (chưa có period) → Đồng bộ | Tạo period(draft); Sửa plan: cho phép |
| 2 | draft/review/submitted → Đồng bộ | Ghi đè (blocking confirm nếu có lines — REQ-RESOURCE-PLAN-BILLABLE-017); Sửa plan: cho phép |
| 3 | approved/sent/paid → Đồng bộ | Bỏ qua + "đã có"; Sửa plan: chặn; `committed_reason ∈ {approved, sent, paid}` |
| 4 | locked → Đồng bộ | Bỏ qua + "đã khóa"; Sửa plan: chặn; `committed_reason = locked` |
| 5 | Assert giá trị trả về | Kiểm `month_has_committed_invoice` (bool) và `committed_reason` (enum) — **assert giá trị có cấu trúc, KHÔNG parse chuỗi tiếng Việt** |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| period.state | đủ 8 trường hợp | "Committed" = {approved, sent, paid, locked} |

**Postconditions:** Mọi hàng bảng chân trị được kiểm; predicate/enum đúng.

### TC-060: Đo hiệu năng theo điều kiện đo (p95, dataset, warm, 20 runs)

**REQ ID:** NFR-001, NFR-002, NFR-008
**Facets:** batch
**Category:** Performance
**Severity:** Medium
**Preconditions:**

- DB nền: 50 project × 200 dòng (× 12 tháng cho NFR-002/008); cache warm; đo 20 lần lấy p95.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Render plan 200 dòng × 8 tháng (warm, 20 runs) | p95 < 3s (NFR-001) |
| 2 | Đồng bộ plan 200 dòng × 12 tháng (warm, 20 runs) | p95 < 15s, không timeout HTTP (NFR-002) |
| 3 | Render pivot Summary với default filter (warm, 20 runs) | p95 < 5s (NFR-008) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| dataset | 50 proj × 200 dòng × 12 tháng | Điều kiện đo cố định |
| runs | 20, p95, warm cache | Để số đo xác định |

**Postconditions:** Ghi kết quả p95 vào báo cáo nghiệm thu. **Lưu ý:** đây là spot-check đo có điều kiện (xem D-26 §4.3); nếu không dựng được dataset/warm-cache xác định trong CI thì giữ ở mức thủ công và ghi nhận sai số — không đưa vào suite tự động chặn merge.

### TC-061: Chỉ báo lệch chiều (a) plan↔snapshot (plan live ≠ snapshot active)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-039
**Facets:** read, ui
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Project có request L2 (snapshot active); sau đó DelM **sửa plan** (đổi MM/rate 1 dòng) mà chưa Submit request mới → plan live lệch snapshot active.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở grid plan | Dòng đã sửa hiển thị **chỉ báo lệch** "plan khác bản đã chụp (snapshot)" (phân biệt kế hoạch đang sửa vs đã chốt billable) |
| 2 | Kiểm so khớp | So plan live ↔ snapshot active theo key (employee,role,month) MM/rate → đánh dấu dòng lệch |
| 3 | Kiểm giá trị có cấu trúc | Cờ lệch suy ra từ so sánh có cấu trúc — assert cờ, KHÔNG parse chuỗi tiếng Việt |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan vs snapshot | MM đổi 1.0→1.5 | Lệch chiều (a) |

**Postconditions:** Không đổi dữ liệu; chỉ báo lệch plan↔snapshot. (Lệch chiều (b) snapshot↔invoice ở TC-099.)

### TC-062: Race — period bị reset committed→draft giữa lúc Đồng bộ

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-037
**Facets:** write, batch, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Tháng X period `approved` khi Đồng bộ bắt đầu đọc trạng thái; mô phỏng phiên khác reset period X về `draft` giữa chừng (TOCTOU).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Bắt đầu Đồng bộ (đánh giá `month_has_committed_invoice` = True cho X) → reset X về draft trước khi ghi | Đồng bộ không ghi nhầm dựa trên ảnh chụp cũ; quyết định ghi/bỏ qua dựa trên trạng thái có khóa (re-check dưới lock) |
| 2 | Kiểm tính nhất quán | Không có member dở dang cho X; kết quả nhất quán với trạng thái cuối (hoặc bỏ qua, hoặc ghi sau khi đã là draft — không nửa vời) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| period(X) | approved → draft (giữa chừng) | TOCTOU; re-check dưới lock |

**Postconditions:** Không để lại trạng thái dở dang do race reset.

### TC-063: Race — 2 IM Đồng bộ song song (serialize/lock)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014
**Facets:** write, batch
**Category:** Integration
**Severity:** High
**Preconditions:**

- 2 IM cùng bấm Đồng bộ trên cùng plan/khoảng đồng thời.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM-1 và IM-2 gọi Đồng bộ song song | Hành động được **serialize (lock)**; chạy tuần tự, không xen kẽ |
| 2 | Kiểm member sau khi cả hai xong | Mỗi tháng đúng 1 bộ member (không nhân đôi do unlink+generate chạy chồng); period không bị tạo trùng |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| sessions | IM-1 ∥ IM-2 | serialize chống chạy song song |

**Postconditions:** Kết quả như chạy 1 lần; không dòng member nhân đôi.

### TC-064: find-or-create dựa trên UNIQUE(project, month) — không tạo period trùng

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014
**Facets:** write, batch
**Category:** Integration
**Severity:** High
**Preconditions:**

- `project.invoice.period` có ràng buộc **UNIQUE(project_id, month_date)**.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Cố tạo 2 period cùng (project, month) qua API | Bị từ chối bởi UNIQUE(project, month) |
| 2 | Đồng bộ tháng đã có period | find-or-create dùng lại period hiện có; không tạo bản ghi thứ hai |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| constraint | UNIQUE(project_id, month_date) | Nền tảng cho find-or-create |

**Postconditions:** Mỗi (project, month) đúng 1 period.

### TC-065: Cửa sổ 8 tháng vắt qua năm (current=2026-11 → 2027-04)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-003, REQ-RESOURCE-PLAN-BILLABLE-032
**Facets:** read, ui
**Category:** Functional
**Severity:** High
**Preconditions:**

- "current" freeze = **2026-11**.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Mở plan với current=2026-11 | Lưới hiển thị 8 cột **2026-09 … 2027-04** (current−2 → current+5), vắt qua năm đúng |
| 2 | Kiểm thứ tự cột | Tháng 2026-12 → 2027-01 liền mạch (không nhảy/lặp năm) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| current (freeze) | 2026-11 | Cửa sổ vắt qua năm |

**Postconditions:** Không đổi dữ liệu; cửa sổ tính đúng qua mốc năm.

### TC-066: "current" theo timezone server (freeze time)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-032
**Facets:** read
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- "current" tính theo **timezone server (UTC)**, chuẩn hóa về ngày đầu tháng; freeze thời gian trong test.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Freeze server time = 2026-06-30 23:00 UTC | "current" = 2026-06 (không lệch sang 07 do tz user) |
| 2 | Freeze = 2026-07-01 00:30 UTC | "current" = 2026-07; cửa sổ dịch theo tz server (không theo tz user) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| server time (freeze) | 2026-06-30T23:00Z / 2026-07-01T00:30Z | tz server, không tz user |

**Postconditions:** Không đổi dữ liệu; "current" bám tz server.

### TC-067: Migration — employee non-approved / đã nghỉ trong dữ liệu nguồn

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-034
**Facets:** batch, write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Invoice nguồn có member của employee `process_state ≠ approved` hoặc đã nghỉ (inactive).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chạy migrate | Hành vi xác định: nạp dòng (giữ lịch sử) hoặc liệt kê vào report "không hợp lệ" — KHÔNG crash; report ghi rõ |
| 2 | Kiểm report | Liệt kê employee non-approved/đã nghỉ; số dòng vẫn đối chiếu được với nguồn |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee | non-approved / inactive | Dữ liệu bẩn |

**Postconditions:** Migrate không vỡ; dòng bẩn được ghi nhận trong report.

### TC-068: Migration — rate nguồn không map `ntq.project.billable.rate`

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-034
**Facets:** batch, write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Member nguồn có giá trị rate không khớp bản ghi nào trong `ntq.project.billable.rate`.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chạy migrate | Dòng rate-không-map được liệt kê vào report (không tạo rate mới — ngoài phạm vi); KHÔNG crash |
| 2 | Kiểm report đối chiếu | Báo rõ dòng không map rate_id; tổng amount/số dòng chỉ tính dòng map được, chênh lệch được ghi nhận |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| rate nguồn | không có trong ntq.project.billable.rate | Dữ liệu bẩn |

**Postconditions:** Migrate không vỡ; dòng rate-không-map được báo cáo.

### TC-069: Migration — idempotent 1 month-row/member (nguồn không thể trùng project/employee/month)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-034
**Facets:** batch, write
**Category:** Integration
**Severity:** Medium
**Lưu ý (cross-consistency audit):** Nguồn `project.invoice.member` đã có **UNIQUE(period, employee)** và period là UNIQUE(project, month) → **không thể tồn tại >1 member cùng (project, employee, month)** ở nguồn (kịch bản 2-rate cũ là bất khả thi). TC này verify migration tạo **đúng 1 month-row/member** và **rerun không nhân đôi** (idempotent theo (line, month)).

**Preconditions:**

- Nguồn có member hợp lệ cho (project, employee, month).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chạy migrate | Mỗi member nguồn → đúng 1 month-row plan |
| 2 | Chạy migrate lần 2 | created=0, không nhân đôi (idempotent) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| source dup | 2 member cùng (proj,emp,month) | khác rate_id → 2 dòng; cùng rate_id → 1 dòng |

**Postconditions:** Số dòng plan khớp số khóa (project,employee,month,rate_id) duy nhất của nguồn.

### TC-070: Negative — thêm dòng employee trùng (UNIQUE plan, employee, month)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-004
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Plan đã có dòng employee HuanTV.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Thêm dòng thứ hai cùng employee HuanTV trong cùng plan/tháng | Bị chặn bởi UNIQUE(plan, employee, month) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee | HuanTV (trùng) | Negative |

**Postconditions:** Không tạo dòng trùng.

### TC-071: Negative — tạo plan thứ 2 cho cùng project (UNIQUE project) bị chặn

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-002
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- Dự án HBU_123 đã có 1 resource plan.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Tạo resource plan thứ hai cho HBU_123 qua API | Bị chặn bởi UNIQUE(project_id) |
| 2 | Mở lại plan HBU_123 | Mở đúng plan hiện có (không tạo bản ghi thứ hai) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| project | HBU_123 (đã có plan) | Negative |

**Postconditions:** Mỗi project đúng 1 plan.

### TC-072: Allocation edge — xóa dòng có member_id = False (chưa gắn allocation)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-013
**Facets:** write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan có dòng `member_id = False` (chưa kịp tạo/sync allocation, vd thêm tay chưa lưu hoặc lỗi sync trước đó).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Xóa dòng có member_id=False | Xóa dòng plan thành công; KHÔNG raise (không cố set end_at trên None) |
| 2 | Kiểm allocation | Không có thao tác ghi `project.member` nào (vì không có member_id) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| line.member_id | False | Edge: không có allocation gắn |

**Postconditions:** Dòng plan bị xóa; không lỗi None; allocation không đổi.

### TC-073: Allocation edge — thêm dòng employee đã có allocation hiện hữu

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-011
**Facets:** write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Employee NamNV đã có `project.member` đang hiệu lực ở dự án.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Thêm dòng NamNV vào plan rồi lưu | KHÔNG tạo allocation trùng; dòng trỏ tới allocation hiện có (hoặc cập nhật theo plan→allocation một chiều) |
| 2 | Kiểm số `project.member` của (dự án, NamNV) | Không tăng thêm bản ghi dư thừa |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| employee | NamNV (đã có allocation) | Edge: tránh dup allocation |

**Postconditions:** Không phát sinh allocation trùng.

### TC-074: Allocation edge — effort_ratio biên 0% / >100%

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-012
**Facets:** write
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Dòng plan có allocation%.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Nhập allocation% = 0% | Hành vi xác định: lưu được (0% hợp lệ) hoặc bị chặn theo ràng buộc — assert đúng theo quy ước; ghi xuống `project.member.effort_ratio` nhất quán |
| 2 | Nhập allocation% > 100% (vd 150%) | Theo ràng buộc: cho phép (over-allocation) hoặc chặn — assert đúng hành vi đã định; không lưu giá trị bất nhất |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| effort_ratio | 0 / 1.5 | Boundary 0% và >100% |

**Postconditions:** Giá trị biên xử lý nhất quán giữa plan và allocation.

### TC-075: Đồng bộ edge — dòng MM = 0 ở mọi tháng (không sinh member)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-021
**Facets:** write, batch
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan có dòng employee với MM=0 ở tất cả các tháng (các dòng khác có MM>0).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đồng bộ | Dòng MM=0 mọi tháng KHÔNG sinh member line nào (chỉ dòng có MM>0 mới sinh) |
| 2 | Kiểm member của các tháng | Không có member amount=0 dư thừa từ dòng đó |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| line MM | 0 mọi tháng | Không sinh member |

**Postconditions:** Member chỉ sinh cho dòng/tháng có MM>0.

### TC-076: Đồng bộ edge — tháng MM=0 phân biệt với tháng chưa-overlay

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-014, REQ-RESOURCE-PLAN-BILLABLE-022
**Facets:** write, batch
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- 1 dòng có tháng A: MM>0; tháng B: MM=0 (chủ đích); generate_lines luôn đặt effort_mm=0 ban đầu cho mọi tháng.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Đồng bộ | Tháng A: member effort_mm = MM plan (>0, đã overlay). Tháng B: MM=0 chủ đích → KHÔNG sinh member (phân biệt với "chưa overlay" — generate_lines effort_mm=0 mặc định) |
| 2 | Kiểm không nhầm | Không có member effort_mm=0 "rơi rớt" do quên phân biệt 0-chủ-đích vs 0-mặc-định |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| month A / B MM | >0 / 0 | Phân biệt 0-chủ-đích vs 0-mặc-định-generate_lines |

**Postconditions:** Chỉ tháng có MM>0 ở plan sinh member; không nhầm 0-mặc-định.

### TC-077: Đồng bộ edge — khoảng toàn tháng đã-chốt (0 period tạo)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-018, REQ-RESOURCE-PLAN-BILLABLE-037
**Facets:** batch, lifecycle
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Khoảng Đồng bộ gồm toàn bộ tháng có period đã-chốt (approved/locked).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM Đồng bộ khoảng toàn đã-chốt | **0 period mới**, 0 member ghi đè; mọi tháng bị bỏ qua |
| 2 | Kiểm kết quả có cấu trúc | Mỗi tháng trả về `committed_reason ∈ {approved, sent, paid, locked}`; thông báo liệt kê đủ tháng bị bỏ qua |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| range | toàn tháng đã-chốt | 0 tác động |

**Postconditions:** Không tạo/ghi đè period nào; báo bỏ qua đầy đủ.

### TC-078: Multi-department — Dept Manager A sửa dòng bộ phận B → chặn

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-020
**Facets:** admin, write
**Category:** Security
**Severity:** High
**Preconditions:**

- Plan đa bộ phận (dòng bộ phận A và bộ phận B); user = Department Manager bộ phận A.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DM-A sửa/xóa dòng nhân sự bộ phận A | Cho phép |
| 2 | DM-A sửa/xóa dòng nhân sự bộ phận B | Read-only / bị từ chối (record rule row-level theo bộ phận) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user_dept / row_dept | A / B | Negative ở bước 2 |

**Postconditions:** Dòng bộ phận B không đổi.

### TC-079: Multi-department — Dept Manager duyệt L1 toàn plan đa bộ phận

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-020, REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** admin, lifecycle
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan đa bộ phận ở Submitted; user = Department Manager (1 bộ phận).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DM duyệt L1 | Duyệt **cả plan** (Submitted → Approved L1) — duyệt cấp plan, không phải per-dòng; row-level chỉ giới hạn **sửa dòng**, không giới hạn duyệt cấp plan |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan | đa bộ phận, Submitted | Duyệt L1 cấp plan |

**Postconditions:** Plan → Approved L1 (toàn plan).

### TC-080: Self-approval — 1 IM tự duyệt cả L1 + L2 → cho phép

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** admin, lifecycle
**Category:** Security
**Severity:** Medium
**Preconditions:**

- User là Invoice Manager (group IM **implies** Department Manager); plan ở Submitted.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM duyệt L1 (qua quyền Dept Manager implied) | Submitted → Approved L1 (cho phép) |
| 2 | Cùng IM duyệt L2 | Approved L1 → Approved L2 (cho phép — KHÔNG separation-of-duties cho IM) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| user | 1 IM (⊇ Dept) | Tự duyệt L1+L2 theo thiết kế |

**Postconditions:** request Approved L2 bởi cùng 1 IM (hành vi chấp nhận theo thiết kế).

### TC-081: NFR-004 — audit/log sự kiện đồng bộ khi L2

**REQ ID:** NFR-004
**Facets:** batch, read
**Category:** Security
**Severity:** Medium
**Preconditions:**

- IM duyệt L2 một request có snapshot trải tháng chưa-chốt + tháng đã-chốt (bị bỏ qua).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM duyệt L2 (đồng bộ là hệ quả) | Ghi nhận **IM duyệt L2 (người thực hiện) + thời điểm + `request_id`** (audit/log/mail.message) |
| 2 | Kiểm log | Đủ để truy vết **request nào áp xuống invoice gì + các tháng bị bỏ qua do đã-chốt** (assert có bản ghi log/audit, không chỉ kiểm UI) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| range | chưa-chốt + đã-chốt | Assert log IM + request_id + thời điểm + tháng bỏ qua |

**Postconditions:** Có bản ghi truy vết cho lần Đồng bộ.

### TC-082: Tách tầng — type-coercion (UI) vs CHECK (DB) cho MM; approved-employee cần @api.constrains

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-009, REQ-RESOURCE-PLAN-BILLABLE-005
**Facets:** write
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Test phân tầng rõ: tầng UI (type-coercion) vs tầng DB (CHECK constraint) vs tầng model (@api.constrains).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | UI: nhập "abc" vào ô MM | Bị từ chối ở tầng UI (type-coercion Float — không phải số) |
| 2 | DB: ghi effort_mm = -1 **bỏ qua UI** (ORM/SQL trực tiếp) | Bị từ chối ở tầng DB **CHECK (effort_mm >= 0)** — không dựa UI |
| 3 | Model: gán employee non-approved qua ORM | Bị từ chối bởi **`@api.constrains`** kiểm `process_state='approved'` (CHECK DB không đọc được field liên quan → phải constrains ở model) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| MM | "abc" (UI) / -1 (DB) | Tách tầng UI vs CHECK DB |
| employee.process_state | non-approved (ORM) | Cần @api.constrains ở model |

**Postconditions:** Mỗi tầng bảo vệ độc lập; bỏ qua UI vẫn bị DB/model chặn.

### TC-083: Submit tạo snapshot grain (employee,role,month) giá-trị-copy + hash

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** Critical
**Preconditions:**

- Plan có dòng MM>0 trải 2 employee × 2 tháng; user = DelM.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Submit | Tạo request + N snapshot-line đúng số (employee,role,month) MM>0; mỗi line **role_id NOT NULL** |
| 2 | Kiểm từng snapshot-line | Có `employee_name`, `role_id`, `department_id`, `month_date`, `mm`, `price`, `currency_id`, `effort_ratio` = **bản copy giá trị** từ plan (không phải FK sống tới line plan) |
| 3 | Kiểm `snapshot_hash` **canonical** | Hash != rỗng; **deterministic**: hash tính trên các line đã **sort (employee_id, role_id, month_date)** + số (MM/price/effort_ratio) chuẩn hóa scale cố định → tính lại (kể cả thứ tự insert khác) cho **cùng hash** |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan lines | 2 emp × 2 tháng MM>0 | → 4 snapshot-line |
| hash determinism | đảo thứ tự dòng nguồn | Hash phải KHÔNG đổi (canonical sort) |

**Postconditions:** Snapshot đầy đủ field giá-trị-copy + hash canonical deterministic.

### TC-084: Chỉ DelM được Submit

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** admin, lifecycle
**Category:** Security
**Severity:** High
**Preconditions:**

- Plan hợp lệ; users = DelM, DeptM, IM, user thường.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Submit | Cho phép |
| 2 | DeptM / IM / user thường Submit | Bị từ chối (chỉ DelM tạo request) |

**Postconditions:** Chỉ DelM tạo được request.

### TC-085: 1-in-flight — chặn Submit khi đã có request {submitted, approved_l1}

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** lifecycle, write
**Category:** Integration
**Severity:** High
**Preconditions:**

- Plan đã có 1 request ở submitted (hoặc approved_l1).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Submit request thứ 2 | Bị chặn (đã có request in-flight) |
| 2 | Sau khi request cũ kết thúc (approved_l2/rejected/cancelled) | Submit mới được phép |

**Postconditions:** Tối đa 1 request in-flight/plan.

### TC-086: DelM Withdraw request in-flight → cancelled

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- request ở submitted hoặc approved_l1.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Withdraw | request → **cancelled** (terminal) |
| 2 | DelM Submit mới | Cho phép (1-in-flight mở lại) |
| 3 | Non-DelM Withdraw | Bị từ chối |

**Postconditions:** request cancelled; cho Submit lại.

### TC-087: Submit KHÔNG sinh allocation/period

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** lifecycle, write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan hợp lệ; chưa có period từ request này.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Submit | Chỉ tạo request + snapshot |
| 2 | Kiểm period/member invoice | KHÔNG sinh (đồng bộ chỉ khi L2 — TC-044) |
| 3 | Kiểm allocation | Allocation chỉ thay đổi khi sửa plan (sync plan→member), không phải khi Submit |

**Postconditions:** Submit không chạm invoice.

### TC-088: Snapshot immutable — sửa plan sau Submit không đổi snapshot/hash

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** Critical
**Preconditions:**

- Đã Submit (snapshot + hash ban đầu lưu lại).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa MM/rate dòng plan, đổi rate.price, **xóa 1 employee khỏi plan** | Plan đổi (stateless cho phép) |
| 2 | Đọc lại snapshot + hash của request | **KHÔNG đổi** so với ban đầu (snapshot là value-copy, không FK sống) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| plan thay đổi sau Submit | MM/rate/xóa employee | Snapshot bất biến |

**Postconditions:** Snapshot + hash bất biến với mọi thay đổi plan sau Submit.

### TC-089: request.line immutable — write/unlink sau tạo bị chặn

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** write, admin
**Category:** Security
**Severity:** High
**Preconditions:**

- request có snapshot-line.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | write 1 field của request.line (mọi state, mọi role gồm IM/admin) | Bị chặn (immutable-on-create) |
| 2 | unlink 1 request.line | Bị chặn |
| 3 | unlink cả request (terminal) | Theo ACL request (không qua line) — line đi cùng request |

**Postconditions:** snapshot-line không sửa/xóa lẻ được.

### TC-090: Snapshot grain UNIQUE(request, employee, role, month)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Build snapshot từ plan.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Tạo 2 snapshot-line trùng (request, employee, role, month) | DB UNIQUE chặn (uq_rprl_grain) |
| 2 | Tạo snapshot-line với **role_id = NULL** | Bị chặn — `role_id` **NOT NULL** (đảm bảo UNIQUE grain không vỡ do NULL-distinct của Postgres) |

**Postconditions:** Không trùng grain trong 1 request; role_id luôn có giá trị.

### TC-091: Verify hash trước L2 — snapshot tamper → raise

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-041
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- request ở approved_l1; snapshot bị tamper (giả lập: ghi đè trực tiếp 1 giá trị qua SQL, hash không khớp).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM duyệt L2 | Verify hash phát hiện lệch → **raise**, không đồng bộ |
| 2 | Kiểm invoice | Không period/member nào bị ghi (transaction rollback) |

**Postconditions:** L2 từ chối snapshot bị tamper.

### TC-092: Đồng bộ overlay từ SNAPSHOT (không plan live)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-041
**Facets:** write, batch
**Category:** Integration
**Severity:** Critical
**Preconditions:**

- request ở approved_l1, snapshot MM=1.0. Sau Submit, **plan bị sửa MM=2.0** (chưa request mới).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | **Sanity:** xác nhận plan live MM=2.0 ≠ snapshot MM=1.0 trước khi assert | Đảm bảo test thực sự phân biệt 2 nguồn |
| 2 | IM duyệt L2 | Đồng bộ |
| 3 | Kiểm member effort_mm | = **1.0 (snapshot)**, KHÔNG phải 2.0 (plan live) |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| snapshot MM / plan live MM | 1.0 / 2.0 | Đồng bộ phải dùng 1.0 |

**Postconditions:** Invoice khớp snapshot, không plan live.

### TC-093: Đồng bộ idempotent — re-run không nhân đôi

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-041
**Facets:** write, batch
**Category:** Integration
**Severity:** High
**Preconditions:**

- request đã L2 (đã đồng bộ 1 lần).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Gọi lại routine đồng bộ trên cùng request (giả lập retry) | Số period/member không tăng; giá trị giữ nguyên |

**Postconditions:** Đồng bộ idempotent trên cùng request.

### TC-094: active_request_id = request L2 mới nhất qua nhiều chu kỳ

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-041
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Plan có request R1 đã L2 (active = R1).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Submit R2, duyệt L1+L2 | active_request_id → **R2** (mới nhất) |
| 2 | Kiểm Summary | Đọc snapshot R2 |
| 3 | Submit R3 nhưng Reject (chưa L2) | active vẫn = R2 |

**Postconditions:** active luôn trỏ request L2 mới nhất.

### TC-095: Plan stateless — sửa plan khi có request pending / sau L2

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-042
**Facets:** write
**Category:** Functional
**Severity:** High
**Preconditions:**

- (a) request ở submitted; (b) request đã L2 (active set).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa MM dòng plan khi request submitted | Cho phép (plan stateless); snapshot không đổi (TC-088) |
| 2 | Sửa MM dòng plan sau khi request đã L2 | Cho phép; invoice/Summary không đổi cho tới request mới L2 |

**Postconditions:** Plan luôn editable bất kể trạng thái request.

### TC-096: Plan không có field state / action lifecycle

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-042
**Facets:** read
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- Model `resource.plan`.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Kiểm fields của resource.plan | KHÔNG có field `state`; vòng đời nằm ở `resource.plan.request` |
| 2 | Kiểm method | Không có action_submit/approve_l1/approve_l2 trên plan |

**Postconditions:** Plan stateless về cấu trúc.

### TC-097: Không reject ở approved_l2 (terminal)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- request ở approved_l2.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Gọi reject trên request approved_l2 | Bị chặn (approved_l2 là terminal, billable đã sinh) |

**Postconditions:** approved_l2 không reject được.

### TC-098: State machine request — chặn nhảy cấp sai

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-024
**Facets:** lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- request ở submitted.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | IM gọi duyệt L2 khi đang submitted (bỏ qua L1) | Bị chặn (phải approved_l1 trước) |
| 2 | Duyệt L1 → L2 đúng thứ tự | Cho phép |

**Postconditions:** Chuyển trạng thái request tuần tự submitted→approved_l1→approved_l2.

### TC-099: Lệch chiều (b) snapshot↔invoice — phân loại (b1) đã-chốt-skip vs (b2) bất thường

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-039
**Facets:** read
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- request L2 (snapshot có tháng X và tháng Y). **(b1)** tháng X đã-chốt → đồng bộ bỏ qua hợp lệ. **(b2)** tháng Y: period bị **sửa tay** sau L2 (member ≠ snapshot) — lệch không do guard đã-chốt.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Kiểm tháng X (b1) | Trạng thái **"đã chốt" — KHÔNG cảnh báo lệch** (skip hợp lệ, chỉ chú thích); không phải báo động giả |
| 2 | Kiểm tháng Y (b2) | **Cờ "lệch billable" (cảnh báo)** — snapshot≠invoice không do đã-chốt |
| 3 | Kiểm giá trị có cấu trúc | Hai hạng (b1)/(b2) là enum/cờ riêng — assert giá trị, không parse chuỗi; không gộp chung |

**Postconditions:** (b1) không cảnh báo, (b2) cảnh báo; tránh nhiễu cho mọi tháng đã-chốt hợp lệ/sau migration.

### TC-100: Summary "xanh giả" sanity — đổi plan trước khi assert đọc snapshot

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-028, REQ-RESOURCE-PLAN-BILLABLE-029
**Facets:** read
**Category:** Integration
**Severity:** High
**Preconditions:**

- Project có request L2 (snapshot MM=1.0).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa plan MM=3.0 (không Submit/L2) | Plan đổi |
| 2 | **Sanity:** assert plan live MM=3.0 ≠ snapshot 1.0 | Đảm bảo fixture thực sự lệch (chống "xanh giả") |
| 3 | Đọc Summary | = 1.0 (snapshot active), KHÔNG 3.0 |

**Postconditions:** Summary chứng minh đọc snapshot, không plan live; fixture có sanity-check.

### TC-101: Đồng bộ — unlink + sinh lại từ snapshot (employee xóa biến mất)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-016, REQ-RESOURCE-PLAN-BILLABLE-041
**Facets:** write, batch
**Category:** Integration
**Severity:** High
**Preconditions:**

- R1 (snapshot A+B) đã L2 → period 05/2026 có member A+B. R2 mới: snapshot chỉ A (B đã xóa khỏi plan trước khi Submit R2).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 0 | **Sanity (anti-false-green):** assert snapshot R2 KHÔNG chứa B + period 05 hiện CÓ member B (từ R1) | Đảm bảo B thực sự tồn tại trước, và snapshot R2 thực sự bỏ B → test có ý nghĩa |
| 1 | Duyệt R2 tới L2 | Unlink toàn bộ member chưa-chốt rồi sinh lại từ **snapshot R2** |
| 2 | Kiểm member B | Biến mất (không có trong snapshot R2) |
| 3 | Kiểm member A | Còn đúng 1 dòng theo snapshot R2 |

**Postconditions:** Member = ảnh chiếu snapshot active (chỉ A).

### TC-102: Migration — tổng amount = invoice cũ, KHÔNG re-sync

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-034
**Facets:** batch, read
**Category:** Integration
**Severity:** High
**Preconditions:**

- Invoice cũ có tổng amount T trên N member.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Chạy migrate | snapshot tổng amount = T; số snapshot-line = N |
| 2 | Kiểm invoice period/member | **Không đổi** (không re-generate) |
| 3 | Mở Summary | = T (đọc snapshot), khớp invoice cũ |

**Postconditions:** Migration phản chiếu invoice cũ, không tác động invoice.

### TC-103: Row-level request — DelM/DeptM scope

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** admin
**Category:** Security
**Severity:** High
**Preconditions:**

- Project P1 (DelM-1 phụ trách) và P2 (DelM-2); request đa bộ phận có DeptM-A, DeptM-B.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM-1 xem/Submit request P2 | Bị chặn (chỉ dự án mình theo delivery_team_id.manager_id.user_id) |
| 2 | DeptM-A duyệt L1 request bộ phận khác | Chỉ thấy/duyệt request có nhân sự bộ phận mình; duyệt L1 áp cả request |

**Postconditions:** request bị giới hạn theo scope.

### TC-104: active_request_id ondelete SET NULL

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** write
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- Plan có active_request_id = R (R đã L2).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Xóa request R (qua ORM, nếu cho phép) | plan.active_request_id → **NULL** (ondelete SET NULL), không cascade xóa plan, không crash |

**Postconditions:** FK an toàn khi request bị xóa.

### TC-105: "Xanh giả" sanity đồng bộ — đổi plan trước khi assert invoice == snapshot

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-041
**Facets:** write, batch
**Category:** Functional
**Severity:** High
**Preconditions:**

- request approved_l1, snapshot MM=1.0.

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Sửa plan MM=5.0 (không Submit) | Plan live ≠ snapshot |
| 2 | **Sanity:** assert plan live=5.0 ≠ snapshot=1.0 | Fixture thực sự kích hoạt nhánh đọc-snapshot (chống "xanh giả") |
| 3 | Duyệt L2, assert member.effort_mm == 1.0 | Pass vì đọc snapshot |

**Postconditions:** Test đồng bộ-từ-snapshot có sanity-check, không pass nhầm.

### TC-106: Reject/Cancelled terminal — không transition tiếp; resubmit request mới

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** lifecycle
**Category:** Integration
**Severity:** Medium
**Preconditions:**

- request ở rejected (hoặc cancelled).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Gọi approve_l1/approve_l2/reject trên request rejected/cancelled | Bị chặn (terminal) |
| 2 | DelM Submit lại | Tạo request mới (1-in-flight mở lại); request cũ giữ trạng thái terminal |

**Postconditions:** Terminal bất biến; chỉ resubmit tạo request mới.

### TC-107: Race 2 DelM Submit đồng thời → partial UNIQUE chặn (1-in-flight)

**REQ ID:** REQ-RESOURCE-PLAN-BILLABLE-040
**Facets:** write, lifecycle
**Category:** Integration
**Severity:** High
**Preconditions:**

- Cùng 1 plan chưa có request in-flight; mô phỏng 2 transaction Submit chạy song song (đặt 2 cursor/2 env trước khi commit).

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | T1 và T2 cùng kiểm 1-in-flight (đều thấy "trống") rồi cùng INSERT request submitted | Một transaction commit thành công; transaction kia **bị DB từ chối** bởi **partial UNIQUE `uq_rpr_inflight`** (plan WHERE state IN submitted/approved_l1) |
| 2 | Kiểm số request in-flight của plan | Đúng **1** (không phải 2) |
| 3 | Kiểm transaction thua | Nhận lỗi tích hợp → rollback sạch, không tạo request mồ côi/snapshot rác |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| concurrency | 2 Submit song song | Guard tuần tự không đủ → cần ràng buộc DB |

**Postconditions:** Tối đa 1 request in-flight kể cả khi 2 Submit đua nhau (đảm bảo ở tầng DB, không chỉ kiểm tuần tự).

## 4. Ma trận bao phủ (Coverage Matrix)

| REQ ID | Requirement Summary | Test Cases | Facets | Coverage |
|--------|-------------------|------------|--------|----------|
| REQ-RESOURCE-PLAN-BILLABLE-001 | Menu Resource Plan | TC-001 | read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-002 | Plan gắn 1 dự án (UNIQUE project) | TC-002, TC-003, TC-071 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-003 | Cửa sổ mặc định 8 tháng | TC-004, TC-005, TC-065 | read, write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-004 | Ràng buộc lưu dòng (UNIQUE plan,employee,role) | TC-006, TC-070 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-005 | Nhân viên approved (@api.constrains) | TC-007, TC-082 | read, write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-006 | Dept/Role tự hiển thị | TC-008 | read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-007 | Allocation % từ hệ thống | TC-009 | read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-008 | Đơn giá từ bảng rate | TC-010 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-009 | Nhập MM (UI type-coercion vs CHECK DB) | TC-011, TC-012, TC-034, TC-082 | write, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-010 | Pre-fill từ allocation | TC-013 | read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-011 | Thêm dòng → tạo allocation (không dup) | TC-014, TC-073 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-012 | Sửa dòng → cập nhật allocation (biên %) | TC-015, TC-074 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-013 | Xóa dòng → set end_at (member_id=False) | TC-016, TC-072 | write, lifecycle | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-014 | Đồng bộ = sự kiện khi L2, từ snapshot; period(draft) + overlay; find-or-create; serialize | TC-017, TC-032, TC-044, TC-062, TC-063, TC-064, TC-075, TC-076, TC-092, TC-093 | write, batch, lifecycle | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-015 | amount = MM × rate | TC-018 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-016 | Đồng bộ unlink + sinh lại từ snapshot tháng chưa-chốt (member xóa biến mất) | TC-019, TC-101 | write, batch | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-017 | Blocking confirm ghi đè (chỉ khi có lines) | TC-020, TC-035, TC-045 | write, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-018 | Bỏ qua tháng locked + bảng chân trị | TC-021, TC-022, TC-059, TC-077 | lifecycle, batch | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-019 | Hiển thị trạng thái tháng | TC-023, TC-033 | read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-020 | Phân quyền workflow (request) + row-level scope (đa bộ phận) | TC-024, TC-036, TC-037, TC-078, TC-079, TC-103 | admin | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-021 | Validation đồng bộ (snapshot/request không hợp lệ) | TC-025, TC-075 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-022 | Khớp khung generate_lines + overlay MM/rate/effort_ratio từ snapshot | TC-026, TC-076 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-023 | Sync một chiều | TC-027 | write, read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-024 | Vòng đời request 2 cấp + Reject terminal + self-approval (IM⊇Dept) | TC-028, TC-029, TC-030, TC-031, TC-038, TC-039, TC-079, TC-080, TC-097, TC-098 | lifecycle, admin | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-025 | Quyền sync allocation | TC-040 | write, admin | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-026 | Snapshot là nguồn sự thật (ghi đè sửa tay khi L2) | TC-041 | write, batch | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-027 | Concurrency (optimistic cấp plan, false-conflict) | TC-042, TC-043 | write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-028 | Summary pivot Dept→Project→Member từ snapshot active + default filter; đa-currency tách | TC-046, TC-048, TC-100 | read, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-029 | Summary đọc snapshot active, rebuild khi L2 (không refresh-live theo plan) | TC-047, TC-048, TC-100 | read | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-030 | Cột Đơn vị tiền tệ ăn theo rate | TC-049 | read, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-031 | Hiển thị HB / BU | TC-050 | read, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-032 | Cửa sổ 8 tháng theo tz server + thêm tháng; vắt qua năm | TC-051, TC-065, TC-066 | read, write, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-033 | Plan editable; billable bị guard ở tháng đã-chốt | TC-052 | write, lifecycle | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-034 | Migration tạo request approved_l2 + snapshot từ invoice nguồn; KHÔNG re-sync; idempotent; dữ liệu bẩn | TC-053, TC-054, TC-067, TC-068, TC-069, TC-102 | batch, write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-035 | Thêm tháng trên form → cộng dồn plan duy nhất | TC-055 | write, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-036 | Invoice: IM edit/delete; QA edit chưa-chốt KHÔNG delete; nhóm cũ view | TC-056 | admin, write | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-037 | Gate Đồng bộ tháng đã-chốt "đã có" | TC-057, TC-059, TC-062, TC-077 | batch, lifecycle | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-038 | Period sau Đồng bộ: QA→submitted, IM→approved (QA không tự approve) | TC-058 | lifecycle, admin | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-039 | Chỉ báo lệch 2 chiều: (a) plan↔snapshot, (b) snapshot↔invoice | TC-061, TC-099 | read, ui | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-040 | Request + snapshot bất biến: Submit (chỉ DelM), grain+hash canonical, 1-in-flight (DB partial UNIQUE), Withdraw, immutable line, role NOT NULL, scope, active SET NULL, terminal, race-submit | TC-028, TC-083, TC-084, TC-085, TC-086, TC-087, TC-088, TC-089, TC-090, TC-103, TC-104, TC-106, TC-107 | write, lifecycle, admin | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-041 | Đồng bộ từ snapshot khi L2: verify hash, overlay từ snapshot, idempotent, active mới nhất, race 2×L2 | TC-017, TC-063, TC-091, TC-092, TC-093, TC-094, TC-101, TC-105 | write, batch, lifecycle | ✓ |
| REQ-RESOURCE-PLAN-BILLABLE-042 | Plan stateless luôn editable; không field state/action lifecycle trên plan | TC-052, TC-095, TC-096 | write, read | ✓ |
| NFR-001 / NFR-002 / NFR-008 | Hiệu năng có điều kiện đo (p95, dataset, warm, 20 runs) | TC-060 | batch | ✓ |
| NFR-004 | Audit/log thao tác đồng bộ (người/thời điểm/tháng bỏ qua) | TC-081 | batch, read | ✓ |

## 5. Yêu cầu dữ liệu kiểm thử (Test Data Requirements)

- **Dự án** HBU_123 có allocation đa nhân sự (HuanTV/HBU/Tech Lead 50%, NamNV/HBU/Dev 100%); thêm ≥2 dự án (1 closed, 1 chưa closed) cho Summary (TC-046).
- **Nhân viên:** approved (HuanTV, NamNV, LanTT) + ≥1 non-approved (cho TC-007).
- **Bảng rate:** rate 350,000 và 300,000; ≥2 rate khác currency (VND, USD) cho TC-049.
- **Trạng thái request:** request ở đủ state submitted / approved_l1 / approved_l2 / rejected / cancelled (cho TC-028/029/030/044/097/098/106); plan stateless (không state) cho TC-095/096.
- **Snapshot:** request có snapshot-line đủ grain (employee,role,month) + hash; bộ fixture **plan đã sửa-lệch snapshot active** (plan live ≠ snapshot) cho TC-061/088/092/100/105 ("xanh giả" sanity); snapshot bị tamper (hash lệch) cho TC-091.
- **Biên period (đủ bảng chân trị):** (chưa có period) / draft / review / submitted / approved / sent / paid / locked (cho TC-059); period 04/2026 `locked`; period đã-chốt approved/sent/paid; period 05/2026 đã đồng bộ (cho ghi đè); khoảng lệch năm; MM ∈ {0, 0.5, 1.0, -1}.
- **"current" freeze:** cố định = 2026-06 theo tz server cho TC-004/051; **= 2026-11** cho cửa sổ vắt qua năm (TC-065); freeze server time quanh mốc UTC (2026-06-30T23:00Z / 2026-07-01T00:30Z) cho tz-server (TC-066).
- **Migration:** project invoice nguồn có member lines (tổng amount T) cho TC-053/054/102 — migrate tạo request approved_l2 + snapshot copy, KHÔNG re-sync; **dữ liệu bẩn:** employee non-approved/đã nghỉ (TC-067), member rate không map `ntq.project.billable.rate` (TC-068), >1 member cùng (project,employee,month,role) (TC-069).
- **Plan đa bộ phận:** dòng bộ phận A + B; 2 Department Manager (A, B) cho TC-078/079; 1 IM (⊇ Dept) cho self-approval L1+L2 (TC-080).
- **Đồng bộ edge:** dòng MM=0 mọi tháng (TC-075); 1 dòng có tháng MM>0 + tháng MM=0 chủ đích (TC-076); khoảng toàn tháng đã-chốt (TC-077); period reset committed→draft giữa chừng (TC-062); 2 IM song song (TC-063).
- **Allocation edge:** dòng member_id=False (TC-072); employee đã có allocation hiện hữu (TC-073); effort_ratio 0% / 150% (TC-074).
- **Negative ràng buộc:** plan đã có để thử tạo plan thứ 2 cùng project (TC-071); dòng employee trùng (TC-070); UNIQUE(project_id, month_date) trên period (TC-064).
- **REQ-RESOURCE-PLAN-BILLABLE-039:** (a) plan live sửa lệch snapshot active cho TC-061; (b) snapshot có tháng X nhưng billable bị bỏ qua do đã-chốt cho TC-099.
- **1-in-flight / Withdraw:** plan có request submitted/approved_l1 sẵn (TC-085); request để Withdraw (TC-086); request terminal rejected/cancelled (TC-106).
- **User:** mỗi nhóm Delivery Manager / Department Manager / Invoice Manager / QA (`project_report.group_project_report_qa`) + 1 user nhóm cũ + 1 user ngoài (cho TC-024/031/056/058/078/079/080/084/103).
- **Performance dataset:** 50 project × 200 dòng × 12 tháng, warm cache, 20 runs (TC-060).
- Không dùng dữ liệu thật khách hàng; staging ẩn danh.

## Lịch sử sửa đổi (Revision History)

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-12 | OPMS team | Initial creation — 35 test case phủ 24 REQ |
| 1.1 | 2026-06-12 | OPMS team | +6 TC (TC-036…041) cho phân quyền: row-level scope, DM-own-dept, Reject, self-approval, quyền sync, ghi đè sửa tay (REQ-RESOURCE-PLAN-BILLABLE-025/026) — phủ 26 REQ |
| 1.2 | 2026-06-12 | OPMS team | +2 TC (TC-042/043) cho REQ-RESOURCE-PLAN-BILLABLE-027 concurrency (optimistic conflict, Generate cảnh báo nháp) — phủ 27 REQ |
| 1.3 | 2026-06-18 | OPMS team | Đồng bộ theo D-02 v1.6 (38 REQ). Đổi tên Generate→Đồng bộ trong TC hiện có; refactor TC-014/022 (overlay MM/rate, period draft, chỉ Approved L2 + IM); TC-024 lifecycle 2 cấp (TC-028/029/030/031 viết lại: Submit/L1/L2, Reject orphan-by-design); TC-017 blocking-confirm chỉ khi có lines; TC-042 false-conflict. +17 TC mới (TC-044…060): Approved-L2 gate, no-confirm khi rỗng, Summary pivot + live-sync rollback 2 chiều (028/029), currency (030), HB/BU (031), cửa sổ 8 tháng tz (032), chặn sửa đã-chốt (033), migration idempotent (034), thêm tháng form (035), invoice IM+QA (036), gate "đã có" (037), period QA/IM duyệt (038), bảng chân trị + committed_reason enum, NFR-001/002/008 có điều kiện đo. Phủ 38 REQ + NFR perf. |
| 1.4 | 2026-06-19 | OPMS team | Đồng bộ theo D-02 v1.8 (39 REQ). **Sửa TC hiện có:** TC-056 (QA edit chưa-chốt KHÔNG delete + case QA delete approved bị chặn, REQ-RESOURCE-PLAN-BILLABLE-036); TC-058 (QA→submitted, IM duyệt cuối→approved, QA không tự approve, REQ-RESOURCE-PLAN-BILLABLE-038); TC-047/048 đổi từ live-sync rollback 2 chiều → Summary tính-khi-đọc (read_group) + pivot đa-currency tách theo currency (REQ-RESOURCE-PLAN-BILLABLE-028/029); TC-017/019/026 thêm find-or-create không trùng/unlink member chưa-chốt/overlay effort_ratio=% plan (REQ-RESOURCE-PLAN-BILLABLE-014/016/022); TC-042 thêm sanity-check write_date đổi sau sửa 1 ô MM; TC-053/054 key thêm rate_id + assert số dòng==member nguồn. **+22 TC mới (TC-061…082):** REQ-RESOURCE-PLAN-BILLABLE-039 chỉ báo lệch (TC-061); race/TOCTOU + 2 IM song song + UNIQUE(project,month) (TC-062/063/064); cửa sổ vắt qua năm + tz server (TC-065/066); migration dữ liệu bẩn (TC-067/068/069); negative UNIQUE plan/employee/month + plan thứ 2 (TC-070/071); allocation edge member_id=False/đã có allocation/effort_ratio biên (TC-072/073/074); đồng bộ edge MM=0 mọi tháng / 0-chủ-đích vs 0-mặc-định / toàn tháng đã-chốt (TC-075/076/077); multi-department chặn dòng bộ phận khác + duyệt L1 toàn plan (TC-078/079); self-approval IM⊇Dept L1+L2 (TC-080); NFR-004 audit Đồng bộ (TC-081); tách tầng UI type-coercion vs CHECK DB vs @api.constrains (TC-082). Phủ 39 REQ + NFR-001/002/004/008. |
| 1.5 | 2026-06-19 | OPMS team | Đồng bộ D-02 v1.8 (sau verify-code). TC-047/048: Summary là **model stored + hook** (đảo lại "view" v1.4 — Odoo 11 pivot cần model backing, V6/028/029). TC-036: scope Delivery qua `delivery_team_id.manager_id.user_id` (V1/020). TC-058: approve cuối **DM/Admin/IM**, cần `delivery_manager_user_id` (raise nếu thiếu), QA chỉ tới submitted (V2/038). TC-048/049: currency `rate.price_currency_id`, đơn giá `rate.price` (V3/008/030). TC-017/019: đồng bộ ở `submitted` **re-sync downstream** billable/summary/customer-invoice/confirm (V5/014/016). TC-064: UNIQUE `uniq_project_month` đã có sẵn (V4). TC-070/071: grain (plan,employee,role,month) (V7/002). TC-082: REQ-RESOURCE-PLAN-BILLABLE-005 domain UI mềm, bỏ assert @api.constrains (V8). | OPMS team |
| 2.2 | 2026-06-19 | OPMS team | **Tái cấu trúc theo D-02/D-19/D-06/D-26 v2.2 (Request + Snapshot, sau party-mode + adversarial).** Banner v2.2 + §2.1 bản đồ TC bị ảnh hưởng. **Đảo ngữ nghĩa TC cũ:** lifecycle trên plan → **request** (TC-028/029/030/038: Submit tạo request+snapshot, L1/L2, **Reject terminal**); đồng bộ thủ công khi plan-L2 → **sự kiện khi L2 từ snapshot** (TC-017/041/044); Summary refresh-live → **đọc snapshot active** + "xanh giả" sanity (TC-046/047); chặn-sửa-plan → **plan editable, billable guard** (TC-052); migration plan(draft) → **request approved_l2 + snapshot từ invoice nguồn, KHÔNG re-sync** (TC-053/054); lệch 1 chiều → **2 chiều** (TC-061). **+24 TC mới (TC-083…106):** snapshot grain+hash giá-trị-copy (083), chỉ DelM submit (084), 1-in-flight (085), Withdraw (086), submit không sinh invoice (087), **snapshot immutable** (088/089/090), **verify hash** (091), **đồng bộ từ snapshot không plan live** (092), idempotent (093), active mới nhất (094), **plan stateless** (095/096), không-reject-L2 (097), state machine tuần tự (098), lệch chiều (b) (099), Summary "xanh giả" (100), unlink+sinh-lại từ snapshot (101), migration amount=invoice cũ (102), row-level request (103), active SET NULL (104), "xanh giả" đồng bộ sanity (105), terminal bất biến (106). **+REQ-040/041/042.** 82→**106 TC**, phủ 42 REQ + NFR. | OPMS team |
| 2.3 | 2026-06-19 | OPMS team | Vá theo **adversarial review cascade v2.2**. #1: TC-020/TC-035 body → blocking confirm **khi duyệt L2** (bỏ "đồng bộ lại" thủ công, khớp REQ-017). #3: TC-081 → audit = sự kiện L2 (IM+request_id+tháng skip). #4: TC-054 → key idempotent **(project,employee,role,month)+migrated** (khớp D-02 REQ-034). #5: TC-032 → **all-or-nothing**, lỗi 1 tháng → rollback toàn bộ L2, request ở approved_l1. #6: TC-053 → migration **insert trực tiếp** approved_l2 (không gọi approve, không re-sync). #7: TC-083 → `snapshot_hash` **canonical** (sort+scale, đảo thứ tự dòng vẫn cùng hash). #8: TC-090 → role_id **NOT NULL** (UNIQUE grain không vỡ). #10: TC-099 → tách **(b1) đã-chốt-skip không cảnh báo** vs **(b2) lệch bất thường cảnh báo**. #11: thêm **sanity anti-false-green** vào TC-017/041/101. #9: **+TC-107** race 2 Submit → DB partial UNIQUE. 106→**107 TC**. | OPMS team |
