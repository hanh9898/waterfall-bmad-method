# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, AccessError

from .common_resource_plan import ResourcePlanCase

IM_GROUP = 'project_invoice.group_project_invoice_manager'
DM_GROUP = 'ntq_project.group_project_department_manager'


class TestResourcePlanLifecycle(ResourcePlanCase):
    """Vong doi 2 cap: Submit -> Approved L1 (Dept Mgr) -> Approved L2 (IM); Reject ->
    Draft + ly do; self-approval cho phep; optimistic-lock token tang khi sua line/month."""

    def setUp(self):
        super(TestResourcePlanLifecycle, self).setUp()
        self.im_user = self._make_user('rp_lc_im', [IM_GROUP])
        self.dm_user = self._make_user('rp_lc_dm', [DM_GROUP])
        self.plain_user = self._make_user('rp_lc_plain')
        # dm_user phu trach delivery cua project
        dm_emp = self.env['hr.employee'].create({
            'name': 'RP_LC_DM_Emp', 'work_email': 'rp.lc.dm@test.local',
            'user_name_tmp': 'rp_lc_dm_emp', 'department_id': self.dept.id,
            'user_id': self.dm_user.id,
        })
        self.dept_delivery.write({'manager_id': dm_emp.id})

    def test_submit(self):
        self.plan.action_submit()
        self.assertEqual(self.plan.state, 'submitted')
        self.assertTrue(self.plan.submitted_by)

    def test_two_level_approval(self):
        self.plan.action_submit()
        self.plan.sudo(self.dm_user).action_approve_l1()
        self.assertEqual(self.plan.state, 'approved_l1')
        self.plan.sudo(self.im_user).action_approve_l2()
        self.assertEqual(self.plan.state, 'approved_l2')

    def test_reject_returns_to_draft_with_reason(self):
        self.plan.action_submit()
        self.plan.action_reject('thieu rate')
        self.assertEqual(self.plan.state, 'draft')
        self.assertEqual(self.plan.reject_reason, 'thieu rate')
        # resubmit duoc
        self.plan.action_submit()
        self.assertEqual(self.plan.state, 'submitted')

    def test_non_manager_cannot_approve(self):
        self.plan.action_submit()
        with self.assertRaises(UserError):
            self.plan.sudo(self.plain_user).action_approve_l1()

    def test_self_approval_allowed(self):
        # 1 IM tu submit + duyet L1 + L2 (IM bao gom Dept) - khong bi chan
        self.plan.sudo(self.im_user).action_submit()
        self.plan.sudo(self.im_user).action_approve_l1()
        self.plan.sudo(self.im_user).action_approve_l2()
        self.assertEqual(self.plan.state, 'approved_l2')

    def test_optimistic_lock_token_bumps(self):
        line = self._make_line()
        r0 = self.plan.revision
        self._make_month(line, '2026-04-01', 1.0)
        self.assertGreater(self.plan.revision, r0, "Sua month phai tang token plan")
        r1 = self.plan.revision
        line.write({'effort_ratio': 0.7})
        self.assertGreater(self.plan.revision, r1, "Sua line phai tang token plan")

    def test_dept_mgr_out_of_scope_cannot_edit(self):
        other_dm = self._make_user('rp_lc_dm2', [DM_GROUP])
        line = self._make_line()
        with self.assertRaises(AccessError):
            line.sudo(other_dm).write({'effort_ratio': 0.9})

    def test_dept_mgr_approves_whole_plan(self):
        self._make_line()
        self.plan.action_submit()
        self.plan.sudo(self.dm_user).action_approve_l1()
        self.assertEqual(self.plan.state, 'approved_l1')

    # ----- P2: rule Tra lai -----
    def test_dept_mgr_reject_only_at_submitted(self):
        self.plan.action_submit()
        self.plan.sudo(self.dm_user).action_reject('thieu')   # OK tu submitted
        self.assertEqual(self.plan.state, 'draft')
        self.plan.action_submit()
        self.plan.sudo(self.dm_user).action_approve_l1()
        with self.assertRaises(UserError):                    # DM khong reject o L1
            self.plan.sudo(self.dm_user).action_reject('x')

    def test_reject_blocked_at_approved_l2(self):
        self.plan.action_submit()
        self.plan.sudo(self.dm_user).action_approve_l1()
        self.plan.sudo(self.im_user).action_approve_l2()
        with self.assertRaises(UserError):                    # da Dong bo -> khong reject
            self.plan.sudo(self.im_user).action_reject('x')

    # ----- P5b: plan read-only sau Submit -----
    def test_plan_readonly_after_submit(self):
        line = self._make_line()
        self.plan.action_submit()
        with self.assertRaises(UserError):
            line.write({'effort_ratio': 0.9})
        with self.assertRaises(UserError):
            self._make_month(line, '2026-05-01', 1.0)
