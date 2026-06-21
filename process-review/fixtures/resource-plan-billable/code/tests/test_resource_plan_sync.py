# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanSync(ResourcePlanCase):
    """Dong bo plan -> invoice period/member: tao period(draft) + member overlay MM/rate;
    amount=MM*price; dong bo lai replace/ghi de; find-or-create khong trung; bo qua da-chot."""

    def _build_and_approve(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._make_month(line, '2026-05-01', 0.5)
        self.plan.action_submit()
        self.plan.action_approve_l1()
        self.plan.action_approve_l2()
        return line

    def _period(self, month):
        return self.env['project.invoice.period'].search([
            ('project_id', '=', self.project.id), ('month_date', '=', month)])

    def _member(self, month):
        return self._period(month).invoice_member_ids.filtered(
            lambda x: x.employee_id == self.employee)

    def test_sync_requires_approved_l2(self):
        self._make_line()
        with self.assertRaises(UserError):
            self.plan.action_sync_from_plan()

    def test_sync_creates_period_and_member(self):
        self._build_and_approve()
        self.plan.action_sync_from_plan()
        p = self._period('2026-04-01')
        self.assertEqual(len(p), 1)
        self.assertEqual(p.state, 'draft')
        m = self._member('2026-04-01')
        self.assertTrue(m, "Phai tao member cho nhan vien")
        self.assertEqual(m.effort_mm, 1.0)
        self.assertEqual(m.rate_id, self.rate)
        self.assertEqual(self._member('2026-05-01').effort_mm, 0.5)

    def test_amount_is_mm_times_price(self):
        self._build_and_approve()
        self.plan.action_sync_from_plan()
        self.assertEqual(self._member('2026-04-01').amount, 1.0 * self.rate.price)

    def test_resync_overwrites_manual_edit(self):
        self._build_and_approve()
        self.plan.action_sync_from_plan()
        self._member('2026-04-01').write({'effort_mm': 99.0})
        self.plan.action_sync_from_plan()
        self.assertEqual(self._member('2026-04-01').effort_mm, 1.0,
                         "Dong bo lai phai ghi de sua tay (plan la nguon su that)")

    def test_no_duplicate_period_on_resync(self):
        self._build_and_approve()
        self.plan.action_sync_from_plan()
        self.plan.action_sync_from_plan()
        self.assertEqual(len(self._period('2026-04-01')), 1, "Khong tao period trung")

    def test_committed_period_skipped(self):
        self._build_and_approve()
        self.plan.action_sync_from_plan()
        self._period('2026-04-01').write({'state': 'approved'})  # da-chot
        # Dong bo lai: thang da-chot bi bo qua -> member giu nguyen, khong bi regenerate
        self.plan.action_sync_from_plan()
        self.assertEqual(self._member('2026-04-01').effort_mm, 1.0,
                         "Thang da-chot khong bi Dong bo ghi de")

    def test_resync_submitted_period_downstream(self):
        # D1: period da `submitted` (da day downstream) -> Dong bo lai re-sync, khong loi
        self._build_and_approve()
        self.plan.action_sync_from_plan()
        period = self._period('2026-04-01')
        period.action_submit()
        self.assertEqual(period.state, 'submitted')
        res = self.plan.action_sync_from_plan()
        self.assertIn('2026-04-01', res['synced'],
                      "Thang submitted phai duoc re-sync (khong roi vao skip 'loi')")
        self.assertEqual(self._member('2026-04-01').effort_mm, 1.0)
