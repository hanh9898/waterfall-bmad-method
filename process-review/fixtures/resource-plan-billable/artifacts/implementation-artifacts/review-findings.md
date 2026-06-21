# Code Review Findings — resource-plan-billable (2026-06-19)

## ✅ Resolution (2026-06-19) — all walked through interactively
**Patches applied (15):** P1 CSV newline · P2 reject rule (Dept-Mgr@submitted; IM@submitted/L1; **L2=no reject**) · P3 summary record-rules (IM all/DM scope/QA all) · P4 log swallowed errors · **P5a** divergence = period edited ≠ plan (plan+summary) · **P5b** plan read-only after Submit · P6 ensure_one · P7 end_at clamp · P8 last_sync only-if-synced · P9 normalize add_month · P10 migrate min/max guard · P11 start_from clamp · **D1** re-sync downstream (`_sync_to_billable_tables` for submitted) · **D2** wire Đồng bộ wizard (preview/confirm) · **D6** migration reconciliation report.
**Resolved, no code:** D3 (rely on Odoo `write_date` concurrency via `_touch`) · D8 (sync-all for v1).
**Deferred:** D4 (demote old invoice groups — needs impact review) · D7 (PlanGrid month-matrix frozen-pane — separate FE task) · F1–F5.
**Result:** 17 suites / **87 tests, 0 fail**; coverage **93%**; closeout validator clean; readiness True; Phase 3 gate PASSED.

---


Adversarial review (Blind Hunter · Edge-Case Hunter · Acceptance Auditor) of `project_invoice/` feature code vs D-02 v1.8 / D-06 / D-19 / D-27.
All 80 tests pass + gate PASSED, but the review surfaced real gaps the green suite did not catch (esp. UI-path & cross-module behavior).

## Decision-needed (require your intent)

- [ ] [Review][Decision] **D1 — Sync to `submitted` periods doesn't re-sync downstream** (REQ-014/016) — `action_sync_from_plan` rebuilds member lines but never re-pushes to billable/summary/customer-invoice/confirm for already-submitted months (`invoice_period._sync_to_billable_tables` not called). Spec marks this mandatory. High blast radius.
- [ ] [Review][Decision] **D2 — Blocking-confirm wizard not wired to the form button** (REQ-017) — `resource_plan_views.xml` "Đồng bộ" button calls `action_sync_from_plan` directly → overwrites non-committed lines with no confirm. The `resource.plan.sync.wizard` (needs_confirm/preview) exists but nothing opens it. Options: button → wizard `act_window` (preview first) vs add `rp_confirmed` guard.
- [ ] [Review][Decision] **D3 — Optimistic-lock token never enforced** (REQ-027) — `_touch()` bumps a `revision` int but no save ever compares/rejects a stale token; TC-042 "user B save rejected" can't actually trigger. Options: rely on Odoo built-in `write_date` concurrency (drop custom token) vs implement explicit token check on write.
- [ ] [Review][Decision] **D4 — Previous groups not demoted to view-only on invoice models** (REQ-036) — `ir.model.access.csv`/`record_rule.xml` still grant PM/FPM/Dept-Mgr/Account-Mgr `1,1,1,1` on period/member. Only QA+IM+resource-plan rules were added; old groups keep write/create/unlink. High blast radius on existing invoice workflows.
- [ ] [Review][Decision] **D5 — Divergence indicator absent from Summary pivot** (REQ-039) — `has_divergence` is on `resource.plan` only; `resource.plan.summary` has no committed/divergence field, so the pivot can't "mark đã-chốt, lệch plan". Options: add a computed flag to summary.
- [ ] [Review][Decision] **D6 — Migration has no reconciliation report + no write_date skip** (REQ-034) — `_migrate_from_invoices` returns counts but no amount/line-count reconciliation (TC-053) and skips existing months unconditionally (no "don't overwrite user edits after migrate via write_date").

## Design fidelity (vs Claude Design "OPMS Design System")

- [ ] [Review][Decision] **D7 — Core PlanGrid (month×employee frozen-pane matrix) not implemented; form uses a flat `line_ids` tree** — Design `components/odoo/PlanGrid` + `Resource Plan.html` specify an editable matrix: sticky/frozen descriptor columns (employee/dept/role/rate) + scrolling **month columns** with per-period state (`open`/`gen`/`locked`, committed = tinted/cross-hatched) + MM cells + totals footer. TASK-016 form instead shows a plain editable list of lines with no month grid. This is the feature's core UX (REQ-019 per-month status, TC-033 frozen-pane). Options: ① build the PlanGrid widget (custom Odoo 11 JS/QWeb — significant FE) · ② accept flat list for v1, defer grid · ③ partial (month columns via a computed o2m, no freeze).
- [ ] [Review][Decision] **D8 — Đồng bộ has no per-month selection; design lets user pick months ("Đồng bộ ({selCount} tháng)")** — `action_sync_from_plan` syncs ALL plan months unconditionally; design dialog offers month selection + per-month new/overwrite/skip preview. Ties into D2 (wizard). Options: ① add month selection to wizard · ② sync-all (current) acceptable for v1.
- _Note: design **confirms** D2 (preview/confirm dialog — "Xem trước & xác nhận" with Overwrite toggle) and D5 (divergence indicator shown on grid + summary) are intended — strengthens rec ① for both._

## Patch (unambiguous fixes)

- [ ] [Review][Patch] **P1 — Corrupted ACL CSV: missing trailing newline merged two rows; `resource.plan` IM ACL row lost** [security/ir.model.access.csv:65] (masked in tests only because IM⊇DM)
- [ ] [Review][Patch] **P2 — `action_reject` has no permission check and no source-state guard** (any writer can reject `approved_l2`→draft) [models/resource_plan.py:action_reject]
- [ ] [Review][Patch] **P3 — `resource.plan.summary` has no record rule → DM/QA see ALL projects' financials** [security/record_rule.xml]
- [ ] [Review][Patch] **P4 — `action_sync_from_plan` `except Exception` swallows real errors as 'loi' (no logging)** [models/resource_plan.py:action_sync_from_plan]
- [ ] [Review][Patch] **P5 — `has_divergence` false-positive: flags a normal Draft plan whose window covers a past committed month (no Reject)** [models/resource_plan.py:_compute_has_divergence]
- [ ] [Review][Patch] **P6 — `_overlay_period` is `@api.multi` but assumes one record (no `ensure_one`)** [models/resource_plan.py:_overlay_period]
- [ ] [Review][Patch] **P7 — `_sync_allocation_unlink` sets `end_at=today` which can be < `start_from` (future allocation) → violates project.member._check** [models/resource_plan_line.py]
- [ ] [Review][Patch] **P8 — `last_sync_at`/`by` written even when 0 months synced (misrepresents sync)** [models/resource_plan.py:action_sync_from_plan]
- [ ] [Review][Patch] **P9 — `action_add_month` does not normalize `month_date` to first-of-month (off-grid cells, string compare)** [models/resource_plan.py:action_add_month]
- [ ] [Review][Patch] **P10 — `_migrate_from_invoices` `min/max(months)` crashes if any `month_date` is falsy** [models/resource_plan.py:_migrate_from_invoices]
- [ ] [Review][Patch] **P11 — `_sync_allocation_create` `start_from=plan.date_from` can violate `project.member._check` (start_from ≥ project.start_date / employee.start_work_date)** [models/resource_plan_line.py:_sync_allocation_create]

## Deferred (real, not blocking now)

- [x] [Review][Defer] **F1 — Duplicate XML id `project_invoice_dept_summary_line_department_manager`** [security/record_rule.xml] — pre-existing, not introduced by this change.
- [x] [Review][Defer] **F2 — Summary rebuild (delete+recreate all rows) + `_touch` fire on every line/month CUD; not batched** — NFR perf; correct but heavy on large plans. Needs an Odoo-11-aware perf pass (debounce/scope regen).
- [x] [Review][Defer] **F3 — `effort_ratio` scale ambiguity (0–1 vs 0–100) pass-through plan↔member** — no concrete bug (consistent in tests); document the convention.
- [x] [Review][Defer] **F4 — `_sync_allocation_write` only propagates `effort_ratio`, not employee/role changes** — stale allocation if a line's employee/role is edited; low-frequency.
- [x] [Review][Defer] **F5 — Summary `currency_id` may lag (related-store) at migration create** — minor; tests show currency correct in normal flow.

## Dismissed (noise / false positive)
- CSV "load-breaking" severity — module loads (extra CSV columns ignored); real bug is the lost row → P1.
- `_check_month_editable` runs after `super().create` — rollback-safe within Odoo transaction.
- `'rejected'` state unused — D-06 specifies Reject → **Draft**; setting `draft` is spec-correct.
- `action_generate_lines` duplicate (employee,role) member[0] — relies on upstream generate_lines dedup; not triggered in covered paths.
