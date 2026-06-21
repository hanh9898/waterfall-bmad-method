# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase


class TestResourcePlanSummaryViews(ResourcePlanCase):
    """REQ-028 (pivot summary + menu, tach currency), NFR-004 (audit Dong bo),
    NFR perf (Dong bo nhieu dong khong loi)."""

    def _approve(self):
        self.plan.action_submit()
        self.plan.action_approve_l1()
        self.plan.action_approve_l2()

    def test_pivot_action_and_menu_exist(self):
        action = self.env.ref('project_invoice.action_resource_plan_summary')
        self.assertEqual(action.res_model, 'resource.plan.summary')
        self.assertIn('pivot', action.view_mode)
        self.assertTrue(self.env.ref('project_invoice.menu_resource_plan_summary'))
        pivot = self.env.ref('project_invoice.view_resource_plan_summary_pivot')
        self.assertIn('currency_id', pivot.arch)  # tach theo currency

    def test_sync_records_audit(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        self.assertFalse(self.plan.last_sync_by)
        self.plan.action_sync_from_plan()
        self.assertTrue(self.plan.last_sync_by, "Dong bo phai ghi audit last_sync_by")
        self.assertTrue(self.plan.last_sync_at)

    def test_sync_multiline_smoke(self):
        for i in range(3):
            emp = self.env['hr.employee'].create({
                'name': 'RP_Perf_%d' % i, 'work_email': 'rp.perf%d@test.local' % i,
                'user_name_tmp': 'rp_perf_%d' % i, 'department_id': self.dept.id,
                'start_work_date': '2020-01-01', 'process_state': 'approved',
            })
            line = self._make_line(employee_id=emp.id)
            self._make_month(line, '2026-04-01', 1.0)
            self._make_month(line, '2026-05-01', 0.5)
        self._approve()
        res = self.plan.action_sync_from_plan()
        self.assertTrue(res['synced'])
