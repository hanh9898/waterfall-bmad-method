# Cross-Consistency Audit — resource-plan-billable (2026-06-19)

3-way cross-check: **D-02 v1.8 (requirements) → Claude Design → D-06/D-19/D-26/D-27 → code**.
Authority order = a gap is attributed to the *lower-priority* artifact (it must change to match the higher).

## ✅ RESOLUTION (2026-06-19) — walked through interactively
**Decisions:** A1 = keep `@api.constrains` guard + **D-02 v1.9** flips REQ-005/V8 to allow it · A2 = **D-02 REQ-024 + D-06 §4** updated: Approved L2 (synced) cannot be rejected (code already enforces) · A3 = D-02 REQ-024 + D-06 documents "plan read-only after Submit".
**Code fixes:** B1 `effort_mm` DB `CHECK(>=0)` (+ test→IntegrityError) · B2 Summary pivot adds **Project** row axis · B3 dropped unused `rejected` state.
**Docs synced (C1–C8):** D-26/D-27 v1.7→v1.8/1.9 · D-19 pay-rate→`price_currency_id` · Summary read_group→**stored+hook** (D-26/D-27) · TC-058 + D-06 §1 → DM/Admin/IM + missing-`delivery_manager_user_id` step · TC-070 UNIQUE(…role) · D-19 "3 groups"→2 · D-19 enum dropped `rejected` · REQ-039 cause = period edited · TC-069 marked unreachable. D-02 bumped **v1.9** (revision row added).
**Deferred:** D (Claude Design mockup updates) + E1 (PlanGrid month-matrix FE) — separate FE pass.
**Verification:** 17 suites / 87 tests still GREEN (code change = B1/B2/B3 only).

---

Inputs: D-02 v1.8 (39 REQ), D-06 v1.3, D-19 v1.3, D-26 v1.3, D-27 v1.5, Claude Design (Resource Plan.html + components), code (`project_invoice/`). 4 parallel auditors (req↔design, req↔docs, design↔code, docs↔code).

---
## A. DECISION-NEEDED — genuine conflicts (your call)

- [ ] **A1 — Approved-employee enforcement: D-02 says UI-only, but code + TC-082 use `@api.constrains`** — D-02 v1.8 (V8) states approved-employee is **domain-UI-only, KHÔNG `@api.constrains`/DB**. Code has `resource_plan_line._check_employee_approved` (hard constrains) and D-27 TC-082/TC-007 + D-26 §3.1 assert a server-side block. Conflict between D-02 and (code + D-27). **Decide:** (a) follow D-02 → remove the constrains + update TC-082; or (b) keep the hard guard → update D-02 V8 wording. *(Note: I added the constrains in TASK-007 following TC-082.)*
- [ ] **A2 — Reject from Approved L2: docs allow it, code blocks it (your prior instruction)** — D-02 REQ-024 + D-06 §4 state diagram draw `ApprovedL2 → Draft` (Reject keeps committed periods). Code blocks reject at `approved_l2` (P2, per your instruction "đã đồng bộ rồi thì ko cho reject"). **Decide:** (a) update D-02/D-06 to match your no-reject-after-sync rule (recommended — keep code); or (b) revert code to allow L2 reject.
- [ ] **A3 — "Plan read-only after Submit" (P5b) is your rule but not in D-02/D-06** — You instructed plan edits only in Draft (reject/reset to edit). Code enforces it (P5b). D-02/D-06 don't state it explicitly. **Decide:** document this rule in D-02 REQ-024 / D-06 (recommended) — else code adds an unspecified constraint.

## B. CODE must-fix (doc/design higher authority)

- [ ] **B1 — `effort_mm` missing DB `CHECK (>= 0)`** — D-19 §3.3 + TC-082 require a DB CHECK rejecting raw-SQL negatives; code only has `@api.constrains` (doesn't fire on raw SQL). → add `_sql_constraints` CHECK.
- [ ] **B2 — Summary pivot missing Project row axis** — D-19 §3.4 + design + TC-046 require rows **Department → Project → Member**; code pivot rows = department/employee/currency (no project, no role). → add `project_id` (and role) to pivot rows.
- [ ] **B3 — `resource.plan.state` selection has unused `rejected`** — D-02/D-06 model Reject→Draft (no terminal `rejected`). Code keeps `rejected` in the Selection (unreachable). → drop it (and D-19 ER enum) — see B-docs.
- [ ] **B4 (verify) — submitted re-sync scope** — D-19 §3.4 names re-gen of customer-invoice/confirm too; code calls only `_sync_to_billable_tables()` (your D1 choice was the narrow scope). Confirm `_sync_to_billable_tables` cascades, else doc overstates. *(Likely OK per your D1 decision.)*

## C. DOCS must-fix (stale vs D-02 v1.8 / D-19 — code is already correct)

- [ ] **C1 — D-26/D-27 headers still cite "D-02 v1.7"** → bump to v1.8.
- [ ] **C2 — D-19 overview text uses pay-rate `rate.currency_id`** (lines 158, 183) while the rest correctly uses `price_currency_id` (REQ-030 forbids pay-rate). → fix the two overview lines.
- [ ] **C3 — D-26/D-27 still describe Summary as `read_group`/SQL view "không hook"** (D-26 §2.1/§3.2/risk; D-27 TC-047) — D-02 v1.8 (V6) + code = **stored model + ORM hook**. → fix prose.
- [ ] **C4 — D-27 TC-058 + D-06 §1 diagram: final period approver = "IM only"** — D-02 v1.8 (V2) = **DM/Admin/IM** + raise if `delivery_manager_user_id` missing. → fix TC-058 + D-06 §1 diagram; **add a TC for the missing-delivery-manager UserError** (currently no coverage).
- [ ] **C5 — D-27 TC-070 + coverage say UNIQUE `(plan, employee, month)`** — D-19/code = `(plan, employee, role)` (v1.8 grain V7). → fix D-27 wording.
- [ ] **C6 — D-19 §3.5 "3 nhóm" overstates** — code has 2 Odoo groups (IM + shared Department/Delivery-Manager group). → reword.
- [ ] **C7 — D-19 ER `state` enum lists `rejected`** — contradicts Reject→Draft. → drop from D-19 enum (pairs with B3).
- [ ] **C8 — TC-069 scenario (>1 member same project/employee/month, different rate) is impossible** — source has UNIQUE(period, employee); → note TC-069 as not-reachable or re-scope.

## D. DESIGN updates (Claude Design — authority #2 but mockup)

- [ ] **D1 — Period-flow role gating wrong** — design gates BOTH "QA push→Submitted" and "IM approve→Approved" on `role==invoice`; REQ-038 separates QA (push) vs DM/Admin/IM (approve). → fix design role gating.
- [ ] **D2 — REQ-GAP: design shows states not in D-02** — `mixed`/"Hỗn hợp" plan badge, `synced` month state, and an add-month cap at Dec/2026 — not in D-02. → drop in design or add to D-02.
- [ ] **D3 — Design mockup omits affordances for REQ-005 (approved-only picker), REQ-008 (rate picker), REQ-034 (migration), REQ-027 (stale-write conflict), REQ-025 (perm-denied)** — minor mockup completeness.

## E. DEFER — large UI build (already tracked as D7)

- [x] **E1 — PlanGrid month×employee frozen-pane matrix not implemented** — design's core editing UX; code form = flat line tree; `resource.plan.line.month` never surfaced in any view. Plus thinner form/list (no committed-count badge, HB/BU, add-month button, divergence chip), and a simpler sync wizard (no per-month selection/Overwrite toggle, plain-text preview). → dedicated FE task (custom Odoo 11 JS/QWeb).

---
**Headline:** code & D-02 are largely aligned on logic; the real gaps are (1) **doc staleness** (C1–C8 — cheap, high-value), (2) **2 genuine req-vs-code conflicts from your verbal overrides** (A1, A2/A3 — docs should be updated to match your decisions), (3) **2 small code fixes** (B1 DB CHECK, B2 pivot Project axis), and (4) the **PlanGrid UI** (E1, deferred).
