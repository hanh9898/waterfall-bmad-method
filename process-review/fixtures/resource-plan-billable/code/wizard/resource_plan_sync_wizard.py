# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResourcePlanSyncWizard(models.TransientModel):
    _name = 'resource.plan.sync.wizard'
    _description = 'Resource Plan Sync Wizard'

    plan_id = fields.Many2one('resource.plan', string='Resource Plan', required=True)
    preview = fields.Text(string='Preview', compute='_compute_preview')
    needs_confirm = fields.Boolean(
        string='Need Confirm', compute='_compute_preview',
        help='Co thang se ghi de len lines da co -> blocking confirm (REQ-017).')

    @api.depends('plan_id')
    def _compute_preview(self):
        Plan = self.env['resource.plan']
        Period = self.env['project.invoice.period']
        for wiz in self:
            lines, needs = [], False
            plan = wiz.plan_id
            if plan and plan.date_from and plan.date_to:
                for month in plan._plan_months():
                    period = Period.search([
                        ('project_id', '=', plan.project_id.id),
                        ('month_date', '=', month)], limit=1)
                    if period and Plan.month_has_committed_invoice(plan.project_id, month):
                        action = 'skip'      # da-chot
                    elif period and period.invoice_member_ids:
                        action = 'overwrite'  # da co lines -> can confirm
                        needs = True
                    else:
                        action = 'create'
                    lines.append('%s: %s' % (month, action))
            wiz.preview = '\n'.join(lines)
            wiz.needs_confirm = needs

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        return self.plan_id.action_sync_from_plan()
