# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError

from .common_resource_plan import ResourcePlanCase

IM_GROUP = 'project_invoice.group_project_invoice_manager'
DM_GROUP = 'ntq_project.group_project_department_manager'
QA_GROUP = 'project_report.group_project_report_qa'


class TestResourcePlanSecurity(ResourcePlanCase):
    """3-lop bao mat resource_plan: ACL (IM full, user thuong bi chan),
    record rule Delivery scope theo project.delivery_team_id.manager_id.user_id,
    summary doc cho IM/DM/QA, QA doc duoc customer invoice.
    """

    def setUp(self):
        super(TestResourcePlanSecurity, self).setUp()
        self.im_user = self._make_user('rp_im', [IM_GROUP])
        self.dm_user = self._make_user('rp_dm', [DM_GROUP])
        self.qa_user = self._make_user('rp_qa', [QA_GROUP])
        self.plain_user = self._make_user('rp_plain')

        # DM phu trach project qua delivery team -> manager -> user
        self.dm_employee = self.env['hr.employee'].create({
            'name': 'RP_DM_Emp', 'work_email': 'rp.dm.emp@test.local',
            'user_name_tmp': 'rp_dm_emp', 'department_id': self.dept.id,
            'user_id': self.dm_user.id,
        })
        self.dept_delivery.write({'manager_id': self.dm_employee.id})

    def test_im_full_access(self):
        Plan = self.env['resource.plan'].sudo(self.im_user)
        plan = Plan.browse(self.plan.id)
        self.assertTrue(plan.read())
        plan.write({'date_to': '2026-10-01'})
        line = self.env['resource.plan.line'].sudo(self.im_user).create({
            'plan_id': self.plan.id, 'employee_id': self.pm_employee.id,
            'rate_id': self.rate.id, 'project_role_id': self.role.id,
        })
        self.assertTrue(line.id)

    def test_plain_user_denied(self):
        with self.assertRaises(AccessError):
            self.env['resource.plan'].sudo(self.plain_user).browse(self.plan.id).read()

    def test_delivery_manager_scope(self):
        # plan2 thuoc project khac, delivery team khong do DM nay quan ly
        partner2 = self.env['res.partner'].create({'name': 'RP_C2', 'customer': True})
        dept_other = self.env['hr.department'].create({'name': 'RP_Other_Team'})
        project2 = self.env['project.project'].create({
            'name': 'RP_Project2', 'partner_id': partner2.id,
            'employee_id': self.pm_employee.id, 'alias_name': 'rp_project2',
            'objective_n_mission': 'x', 'start_date': '2026-04-01',
            'delivery_team_id': dept_other.id,
        })
        plan2 = self.env['resource.plan'].create({
            'project_id': project2.id, 'date_from': '2026-04-01', 'date_to': '2026-09-01',
        })
        visible = self.env['resource.plan'].sudo(self.dm_user).search([]).ids
        self.assertIn(self.plan.id, visible, "DM phai thay plan cua project minh phu trach")
        self.assertNotIn(plan2.id, visible, "DM khong duoc thay plan ngoai pham vi")

    def test_qa_reads_summary(self):
        # khong loi AccessError khi QA doc summary
        self.env['resource.plan.summary'].sudo(self.qa_user).search([])

    def test_qa_reads_customer_invoice(self):
        self.env['project.customer.invoice'].sudo(self.qa_user).search([])
