# -*- coding: utf-8 -*-
from odoo import models, fields, api

PLAN_STATES = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('approved_l1', 'Approved L1'),
    ('approved_l2', 'Approved L2'),
]


class ResourcePlanSummary(models.Model):
    _name = 'resource.plan.summary'
    _description = 'Resource Plan Summary'
    _order = 'department_id, project_id, employee_id, month_date'

    plan_id = fields.Many2one('resource.plan', string='Resource Plan',
                              ondelete='cascade', index=True)
    project_id = fields.Many2one('project.project', string='Project')
    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    role_id = fields.Many2one('ntq.project.role.skills', string='Project Role')
    month_date = fields.Date(string='Month')
    mm = fields.Float(string='MM')
    price = fields.Float(string='Rate Price')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')
    state = fields.Selection(PLAN_STATES, string='Status')
    diverged = fields.Boolean(
        string='Lech vs billable', compute='_compute_diverged',
        help='Period (billable) cua o nay da bi sua khac voi plan - REQ-039.')

    @api.depends('plan_id', 'employee_id', 'role_id', 'month_date', 'mm')
    def _compute_diverged(self):
        cache = {}
        for rec in self:
            plan = rec.plan_id
            if plan.id not in cache:
                cache[plan.id] = plan._divergent_keys() if plan else set()
            rec.diverged = (rec.employee_id.id, rec.role_id.id,
                            rec.month_date) in cache[plan.id]

    @api.model
    def _rebuild_for_plans(self, plans):
        """Dung lai (xoa + tao) toan bo dong summary cua cac plan tu line/month.
        Chay sudo (he thong duy tri, khong qua UI - D-19 3.4)."""
        plans = plans.exists()
        if not plans:
            return
        self.search([('plan_id', 'in', plans.ids)]).unlink()
        for plan in plans:
            for line in plan.line_ids:
                price = line.rate_id.price or 0.0
                for m in line.month_ids:
                    self.create({
                        'plan_id': plan.id,
                        'project_id': plan.project_id.id,
                        'department_id': line.department_id.id,
                        'employee_id': line.employee_id.id,
                        'role_id': line.project_role_id.id,
                        'month_date': m.month_date,
                        'mm': m.effort_mm,
                        'price': price,
                        'amount': (m.effort_mm or 0.0) * price,
                        'currency_id': line.currency_id.id,
                        'state': plan.state,
                    })
