# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanPrefill(ResourcePlanCase):
    """Pre-fill dong tu allocation (project.member) + chi cho nhan vien approved
    (@api.constrains process_state) + effort_ratio khop project.member.
    """

    def test_employee_must_be_approved(self):
        draft_emp = self.env['hr.employee'].create({
            'name': 'RP_Draft_Emp', 'work_email': 'rp.draft@test.local',
            'user_name_tmp': 'rp_draft', 'department_id': self.dept.id,
            'start_work_date': '2020-01-01', 'process_state': 'draft',
        })
        with self.assertRaises(ValidationError):
            self._make_line(employee_id=draft_emp.id)

    def test_approved_employee_ok(self):
        line = self._make_line()  # self.employee approved
        self.assertTrue(line.id)

    def test_prefill_from_allocation(self):
        alloc = self._make_allocation(effort_ratio=0.5)
        n_before = len(self.plan.line_ids)
        self.plan.action_prefill_from_allocation()
        lines = self.plan.line_ids.filtered(lambda l: l.employee_id == self.employee)
        self.assertTrue(lines, "Pre-fill phai tao dong cho nhan vien da allocation")
        self.assertEqual(lines[0].effort_ratio, 0.5,
                         "effort_ratio phai khop project.member")
        self.assertEqual(lines[0].member_id, alloc,
                         "Dong phai lien ket allocation nguon")
        self.assertGreater(len(self.plan.line_ids), n_before)

    def test_prefill_idempotent(self):
        self._make_allocation()
        self.plan.action_prefill_from_allocation()
        n1 = len(self.plan.line_ids)
        self.plan.action_prefill_from_allocation()
        self.assertEqual(len(self.plan.line_ids), n1,
                         "Pre-fill lan 2 khong tao trung dong")
