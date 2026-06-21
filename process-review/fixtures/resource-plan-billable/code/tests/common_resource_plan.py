# -*- coding: utf-8 -*-
"""Base fixtures dung chung cho cac test cua tinh nang Resource Plan & Billable.

Dat o phase post_install (Odoo 11 KHONG co @tagged; dung at_install/post_install).
Subclass ke thua thuoc tinh phase + cac helper tao plan/line/month/allocation.
"""
from odoo.tests import common
from odoo.tests.common import TransactionCase


@common.at_install(False)
@common.post_install(True)
class ResourcePlanCase(TransactionCase):

    def setUp(self):
        super(ResourcePlanCase, self).setUp()

        self.dept = self.env['hr.department'].create({'name': 'RP_Dept'})
        self.dept_delivery = self.env['hr.department'].create({'name': 'RP_Delivery_Team'})

        self.pm_employee = self.env['hr.employee'].create({
            'name': 'RP_PM',
            'work_email': 'rp.pm@test.local',
            'user_name_tmp': 'rp_pm',
            'department_id': self.dept.id,
            'start_work_date': '2020-01-01',
            'process_state': 'approved',
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'RP_Member',
            'work_email': 'rp.member@test.local',
            'user_name_tmp': 'rp_member',
            'department_id': self.dept.id,
            'start_work_date': '2020-01-01',
            'process_state': 'approved',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'RP_Customer', 'customer': True, 'is_company': True,
        })

        self.project = self.env['project.project'].create({
            'name': 'RP_Project',
            'partner_id': self.partner.id,
            'employee_id': self.pm_employee.id,
            'objective_n_mission': 'Resource plan feature tests.',
            'alias_name': 'rp_project',
            'start_date': '2026-04-01',
            'delivery_team_id': self.dept_delivery.id,
        })

        Currency = self.env['res.currency'].with_context(active_test=False)
        self.currency = self.env.ref('base.VND', raise_if_not_found=False) \
            or Currency.search([('name', '=', 'VND')], limit=1) \
            or Currency.create({'name': 'VND', 'symbol': u'd'})
        self.rate = self.env['ntq.project.billable.rate'].create({
            'name': 'RP_Rate',
            'price_currency_id': self.currency.id,
            'price': 1000000.0,
        })

        self.role = self.env['ntq.project.role.skills'].search([], limit=1)
        if not self.role:
            company_role = self.env['ntq.employee.role'].search([], limit=1) \
                or self.env['ntq.employee.role'].create({'name': 'RP_CompanyRole'})
            self.role = self.env['ntq.project.role.skills'].create({
                'name': 'RP_Role', 'role_id': company_role.id,
            })

        self.plan = self.env['resource.plan'].create({
            'project_id': self.project.id,
            'date_from': '2026-04-01',
            'date_to': '2026-09-01',
        })

    # ----- helpers -----
    def _make_line(self, **kw):
        vals = {
            'plan_id': self.plan.id,
            'employee_id': self.employee.id,
            'department_id': self.dept.id,
            'project_role_id': self.role.id,
            'rate_id': self.rate.id,
            'effort_ratio': 1.0,
        }
        vals.update(kw)
        return self.env['resource.plan.line'].create(vals)

    def _make_month(self, line, month_date, effort_mm):
        return self.env['resource.plan.line.month'].create({
            'line_id': line.id,
            'month_date': month_date,
            'effort_mm': effort_mm,
        })

    def _make_user(self, login, group_xmlids=()):
        user = self.env['res.users'].create({
            'name': login,
            'login': login,
            'email': login + '@test.local',
        })
        if group_xmlids:
            user.write({'groups_id': [(4, self.env.ref(g).id) for g in group_xmlids]})
        return user

    def _make_allocation(self, employee=None, **kw):
        vals = {
            'project_id': self.project.id,
            'employee_id': (employee or self.employee).id,
            'project_role_id': self.role.id,
            'start_from': '2026-04-01',
            'effort_ratio': 1.0,
        }
        vals.update(kw)
        return self.env['project.member'].create(vals)
