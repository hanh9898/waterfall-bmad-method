# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResourcePlanLineMonth(models.Model):
    _name = 'resource.plan.line.month'
    _description = 'Resource Plan Line Month'
    _order = 'month_date'

    line_id = fields.Many2one(
        'resource.plan.line', string='Plan Line',
        required=True, ondelete='cascade', index=True)
    month_date = fields.Date(string='Month', required=True)
    effort_mm = fields.Float(string='MM', default=0.0)
    committed_reason = fields.Char(
        string='Trang thai thang', compute='_compute_committed_reason',
        help='Trang thai period cua thang neu da-chot (REQ-019).')

    @api.depends('month_date', 'line_id.plan_id.project_id')
    def _compute_committed_reason(self):
        Plan = self.env['resource.plan']
        for rec in self:
            project = rec.line_id.plan_id.project_id
            rec.committed_reason = (
                Plan._committed_reason(project, rec.month_date)
                if project and rec.month_date else '')

    @api.multi
    def _check_month_editable(self):
        """Chan sua/xoa o thuoc thang da-chot (REQ-033)."""
        if self.env.context.get('rp_migrating'):
            return
        Plan = self.env['resource.plan']
        for rec in self:
            project = rec.line_id.plan_id.project_id
            if project and Plan._committed_reason(project, rec.month_date):
                raise UserError(_('Khong sua duoc thang da-chot (period da khoa/duyet).'))

    @api.multi
    def _check_plan_editable(self):
        """Plan chi sua truc tiep khi o Draft; sau Submit phai reset/Tra lai (REQ-024)."""
        if self.env.context.get('rp_migrating'):
            return
        for rec in self:
            plan = rec.line_id.plan_id
            if plan and plan.state != 'draft':
                raise UserError(_('Plan da submit - Tra lai/reset ve Draft de sua.'))

    _sql_constraints = [
        ('uq_resource_plan_line_month',
         'unique(line_id, month_date)',
         'Moi dong chi co mot o / thang.'),
        ('chk_effort_mm_nonneg',
         'CHECK (effort_mm >= 0)',
         'MM khong duoc am.'),
    ]

    @api.model
    def create(self, vals):
        rec = super(ResourcePlanLineMonth, self).create(vals)
        rec._check_plan_editable()
        rec._check_month_editable()
        rec.line_id.plan_id._refresh_summary()
        rec.line_id.plan_id._touch()
        return rec

    @api.multi
    def write(self, vals):
        self._check_plan_editable()
        self._check_month_editable()
        res = super(ResourcePlanLineMonth, self).write(vals)
        plans = self.mapped('line_id.plan_id')
        plans._refresh_summary()
        plans._touch()
        return res

    @api.multi
    def unlink(self):
        self._check_plan_editable()
        self._check_month_editable()
        plans = self.mapped('line_id.plan_id')
        res = super(ResourcePlanLineMonth, self).unlink()
        plans._refresh_summary()
        plans._touch()
        return res
