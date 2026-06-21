# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResourcePlanLine(models.Model):
    _name = 'resource.plan.line'
    _description = 'Resource Plan Line'

    plan_id = fields.Many2one(
        'resource.plan', string='Resource Plan',
        required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        domain="[('process_state', '=', 'approved')]")
    department_id = fields.Many2one('hr.department', string='Department')
    project_role_id = fields.Many2one('ntq.project.role.skills', string='Project Role')
    effort_ratio = fields.Float(string='Allocation (%)')
    rate_id = fields.Many2one(
        'ntq.project.billable.rate', string='Billable Rate', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='rate_id.price_currency_id', store=True, readonly=True)
    member_id = fields.Many2one(
        'project.member', string='Allocation', ondelete='set null',
        help='Allocation duoc dong bo mot chieu tu plan (REQ-023).')
    migrated = fields.Boolean(string='Migrated', default=False)
    month_ids = fields.One2many(
        'resource.plan.line.month', 'line_id', string='Monthly Effort')

    _sql_constraints = [
        ('uq_resource_plan_line',
         'unique(plan_id, employee_id, project_role_id)',
         'Moi nhan vien chi co mot dong / vai tro trong mot plan.'),
    ]

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id

    @api.constrains('employee_id')
    def _check_employee_approved(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.process_state != 'approved':
                raise ValidationError(_('Chi chon duoc nhan vien da approved.'))

    @api.constrains('effort_ratio')
    def _check_effort_ratio(self):
        for rec in self:
            if (rec.effort_ratio or 0.0) < 0:
                raise ValidationError(_('Allocation (%) khong duoc am.'))

    @api.multi
    def _check_plan_editable(self):
        """Plan chi sua truc tiep khi o Draft; sau Submit phai reset/Tra lai (REQ-024)."""
        if self.env.context.get('rp_migrating'):
            return
        for rec in self:
            if rec.plan_id and rec.plan_id.state != 'draft':
                raise UserError(_('Plan da submit - Tra lai/reset ve Draft de sua.'))

    # ----- Dong bo mot chieu plan -> allocation (project.member), no sudo (REQ-025) -----
    @api.multi
    def _sync_allocation_create(self):
        if self.env.context.get('rp_migrating'):
            return
        Member = self.env['project.member']
        for line in self:
            if line.member_id or not line.project_role_id:
                continue
            plan = line.plan_id
            existing = Member.search([
                ('project_id', '=', plan.project_id.id),
                ('employee_id', '=', line.employee_id.id),
                ('project_role_id', '=', line.project_role_id.id),
                ('end_at', '=', False),
            ], limit=1)
            if existing:
                line.member_id = existing
            else:
                # start_from >= project.start_date va >= employee.start_work_date
                # (project.member._check) -> clamp (P11)
                cands = [plan.date_from or fields.Date.today()]
                if plan.project_id.start_date:
                    cands.append(plan.project_id.start_date)
                if line.employee_id.start_work_date:
                    cands.append(line.employee_id.start_work_date)
                line.member_id = Member.create({
                    'project_id': plan.project_id.id,
                    'employee_id': line.employee_id.id,
                    'project_role_id': line.project_role_id.id,
                    'start_from': max(cands),
                    'effort_ratio': line.effort_ratio,
                })

    @api.multi
    def _sync_allocation_write(self, vals):
        if 'effort_ratio' not in vals:
            return
        for line in self:
            if line.member_id:
                line.member_id.effort_ratio = line.effort_ratio

    @api.multi
    def _sync_allocation_unlink(self):
        today = fields.Date.today()
        for line in self:
            member = line.member_id
            if member and not member.end_at:
                # end_at >= start_from (project.member._check) -> clamp (P7)
                member.end_at = max(today, member.start_from) if member.start_from else today

    @api.model
    def create(self, vals):
        rec = super(ResourcePlanLine, self).create(vals)
        rec._check_plan_editable()
        rec._sync_allocation_create()
        rec.plan_id._refresh_summary()
        rec.plan_id._touch()
        return rec

    @api.multi
    def write(self, vals):
        self._check_plan_editable()
        res = super(ResourcePlanLine, self).write(vals)
        self._sync_allocation_write(vals)
        plans = self.mapped('plan_id')
        plans._refresh_summary()
        plans._touch()
        return res

    @api.multi
    def unlink(self):
        self._check_plan_editable()
        plans = self.mapped('plan_id')
        self._sync_allocation_unlink()
        res = super(ResourcePlanLine, self).unlink()
        plans._refresh_summary()
        plans._touch()
        return res
