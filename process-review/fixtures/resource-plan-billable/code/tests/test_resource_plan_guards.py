# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanSyncGuards(ResourcePlanCase):
    """Guard Dong bo: chan plan khong hop le (REQ-021), bo qua thang da-chot kem
    "da khoa"/"da co" (REQ-018/037), dong MM=0 khong sinh member, effort_ratio bien."""

    def _approve(self):
        self.plan.action_submit()
        self.plan.action_approve_l1()
        self.plan.action_approve_l2()

    def _period(self, month):
        return self.env['project.invoice.period'].search([
            ('project_id', '=', self.project.id), ('month_date', '=', month)])

    def test_sync_invalid_plan_blocked(self):
        self._make_line()  # line nhung khong co month MM>0
        self._approve()
        with self.assertRaises(UserError):
            self.plan.action_sync_from_plan()

    def test_locked_month_skipped_with_message(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        self.plan.action_sync_from_plan()
        self._period('2026-04-01').write({'state': 'locked'})
        res = self.plan.action_sync_from_plan()
        skipped = dict(res['skipped'])
        self.assertIn('2026-04-01', skipped)
        self.assertIn('khoa', skipped['2026-04-01'])

    def test_committed_month_skipped_with_message(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        self.plan.action_sync_from_plan()
        self._period('2026-04-01').write({'state': 'approved'})
        res = self.plan.action_sync_from_plan()
        skipped = dict(res['skipped'])
        self.assertIn('2026-04-01', skipped)
        self.assertIn('co', skipped['2026-04-01'])

    def test_zero_mm_line_no_member(self):
        line1 = self._make_line()
        self._make_month(line1, '2026-04-01', 1.0)
        emp2 = self.env['hr.employee'].create({
            'name': 'RP_Zero', 'work_email': 'rp.zero@test.local',
            'user_name_tmp': 'rp_zero', 'department_id': self.dept.id,
            'start_work_date': '2020-01-01', 'process_state': 'approved',
        })
        line2 = self._make_line(employee_id=emp2.id)
        self._make_month(line2, '2026-04-01', 0.0)
        self._approve()
        res = self.plan.action_sync_from_plan()
        self.assertIn('2026-04-01', res['synced'])
        members = self._period('2026-04-01').invoice_member_ids
        self.assertTrue(members.filtered(lambda m: m.employee_id == self.employee))
        self.assertFalse(members.filtered(lambda m: m.employee_id == emp2),
                         "Dong MM=0 moi thang khong sinh member")

    def test_all_committed_range(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        self.plan.action_sync_from_plan()
        for p in self.env['project.invoice.period'].search([('project_id', '=', self.project.id)]):
            p.write({'state': 'locked'})
        res = self.plan.action_sync_from_plan()
        self.assertFalse(res['synced'], "Khoang toan da-chot: khong sync thang nao")

    def test_effort_ratio_negative_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_line(effort_ratio=-1.0)

    def test_effort_ratio_zero_and_over_100_ok(self):
        l0 = self._make_line(effort_ratio=0.0)
        self.assertTrue(l0.id)
        emp2 = self.env['hr.employee'].create({
            'name': 'RP_Over', 'work_email': 'rp.over@test.local',
            'user_name_tmp': 'rp_over', 'department_id': self.dept.id,
            'start_work_date': '2020-01-01', 'process_state': 'approved',
        })
        l150 = self._make_line(employee_id=emp2.id, effort_ratio=150.0)
        self.assertTrue(l150.id)
