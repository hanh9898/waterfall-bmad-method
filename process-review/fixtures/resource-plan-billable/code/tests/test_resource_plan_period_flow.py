# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase

QA_GROUP = 'project_report.group_project_report_qa'


class TestResourcePlanPeriodFlow(ResourcePlanCase):
    """REQ-038: sau Dong bo, period(draft) di qua luong duyet: QA day (-> review/submitted),
    Admin/IM duyet (-> approved). Dung lai workflow period san co cua develop."""

    def setUp(self):
        super(TestResourcePlanPeriodFlow, self).setUp()
        self.qa_user = self._make_user('rp_pf_qa', [QA_GROUP])
        # Cau hinh Delivery Manager cho project (period flow yeu cau manager)
        dm_user = self._make_user('rp_pf_dm')
        dm_emp = self.env['hr.employee'].create({
            'name': 'RP_PF_DM', 'work_email': 'rp.pf.dm@test.local',
            'user_name_tmp': 'rp_pf_dm', 'department_id': self.dept.id,
            'user_id': dm_user.id,
        })
        self.dept_delivery.write({'manager_id': dm_emp.id})
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self.plan.action_submit()
        self.plan.action_approve_l1()
        self.plan.action_approve_l2()
        self.plan.action_sync_from_plan()
        self.period = self.env['project.invoice.period'].search([
            ('project_id', '=', self.project.id), ('month_date', '=', '2026-04-01')])

    def test_synced_period_is_draft(self):
        self.assertEqual(self.period.state, 'draft')
        self.assertTrue(self.period.invoice_member_ids, "Period co member sau Dong bo")

    def test_qa_can_push_to_review(self):
        self.period.sudo(self.qa_user).action_send_to_dm_review()
        self.assertEqual(self.period.state, 'review')

    def test_full_period_flow_to_approved(self):
        self.period.sudo(self.qa_user).action_send_to_dm_review()
        self.period.action_submit()
        self.assertEqual(self.period.state, 'submitted')
        self.period.action_admin_approve()
        self.assertEqual(self.period.state, 'approved')
