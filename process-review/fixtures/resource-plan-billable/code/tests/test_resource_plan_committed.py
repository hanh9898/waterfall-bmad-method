# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanCommitted(ResourcePlanCase):
    """Predicate month_has_committed_invoice + committed_reason (enum), chan sua thang
    da-chot (REQ-033), hien thi trang thai thang (REQ-019), chi bao lech plan<->period (REQ-039)."""

    def _approve_sync(self, mm=1.0):
        line = self._make_line()
        self._make_month(line, '2026-04-01', mm)
        self.plan.action_submit()
        self.plan.action_approve_l1()
        self.plan.action_approve_l2()
        self.plan.action_sync_from_plan()
        return line

    def _period(self, month):
        return self.env['project.invoice.period'].search([
            ('project_id', '=', self.project.id), ('month_date', '=', month)])

    def test_committed_predicate_and_reason_enum(self):
        Plan = self.env['resource.plan']
        self._approve_sync()
        p = self._period('2026-04-01')
        self.assertFalse(Plan.month_has_committed_invoice(self.project, '2026-04-01'))
        self.assertEqual(Plan._committed_reason(self.project, '2026-04-01'), '')
        p.write({'state': 'approved'})
        self.assertTrue(Plan.month_has_committed_invoice(self.project, '2026-04-01'))
        self.assertEqual(Plan._committed_reason(self.project, '2026-04-01'), 'approved')
        p.write({'state': 'locked'})
        self.assertEqual(Plan._committed_reason(self.project, '2026-04-01'), 'locked')

    def test_edit_blocked_on_committed_month(self):
        line = self._approve_sync()
        self._period('2026-04-01').write({'state': 'approved'})
        m = line.month_ids.filtered(lambda x: x.month_date == '2026-04-01')
        with self.assertRaises(UserError):
            m.write({'effort_mm': 2.0})

    def test_edit_blocked_on_locked_month(self):
        line = self._approve_sync()
        self._period('2026-04-01').write({'state': 'locked'})
        m = line.month_ids.filtered(lambda x: x.month_date == '2026-04-01')
        with self.assertRaises(UserError):
            m.unlink()

    def test_month_status_display(self):
        line = self._approve_sync()
        m = line.month_ids.filtered(lambda x: x.month_date == '2026-04-01')
        self.assertEqual(m.committed_reason, '')
        self._period('2026-04-01').write({'state': 'locked'})
        m.invalidate_cache()
        self.assertEqual(m.committed_reason, 'locked')

    def _period_member(self):
        return self._period('2026-04-01').invoice_member_ids.filtered(
            lambda m: m.employee_id == self.employee)

    def test_divergence_after_period_edit(self):
        # Plan sau submit khong sua truc tiep; lech = period (billable) bi sua khac plan.
        self._approve_sync()
        self.assertFalse(self.plan.has_divergence, "Vua dong bo: khong lech")
        self._period_member().write({'effort_mm': 9.0})  # sua truc tiep period
        self.plan.invalidate_cache()
        self.assertTrue(self.plan.has_divergence,
                        "Period bi sua khac plan -> chi bao lech (REQ-039)")

    def test_summary_diverged_flag(self):
        self._approve_sync()
        self._period_member().write({'effort_mm': 9.0})
        summ = self.env['resource.plan.summary'].search([
            ('plan_id', '=', self.plan.id), ('employee_id', '=', self.employee.id),
            ('month_date', '=', '2026-04-01')])
        summ.invalidate_cache()
        self.assertTrue(summ.diverged, "Summary danh dau lech (REQ-039/D5)")
