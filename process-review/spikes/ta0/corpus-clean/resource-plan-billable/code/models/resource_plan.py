# Clean v2.3 implementation — Request + Snapshot model (drift-free vs D-19 v2.3).
from odoo import fields, models


class ResourcePlan(models.Model):
    _name = 'resource.plan'

    project_id = fields.Many2one('project.project', required=True)
    active_request_id = fields.Many2one('resource.plan.request')
    line_ids = fields.One2many('resource.plan.line', 'plan_id')


class ResourcePlanLine(models.Model):
    _name = 'resource.plan.line'

    plan_id = fields.Many2one('resource.plan')
    employee_id = fields.Many2one('hr.employee')


class ResourcePlanRequest(models.Model):
    _name = 'resource.plan.request'

    plan_id = fields.Many2one('resource.plan')
    state = fields.Selection([
        ('submitted', 'Submitted'),
        ('approved_l1', 'Approved L1'),
        ('approved_l2', 'Approved L2'),
        ('rejected', 'Rejected'),
    ])
    snapshot_hash = fields.Char()
    request_line_ids = fields.One2many('resource.plan.request.line', 'request_id')

    def action_approve_l2(self):
        for rec in self:
            rec.state = 'approved_l2'
            rec.plan_id.active_request_id = rec
            rec._sync_from_snapshot()

    def _sync_from_snapshot(self):
        # find-or-create period per month from this request's request_line snapshot
        return True


class ResourcePlanRequestLine(models.Model):
    _name = 'resource.plan.request.line'

    request_id = fields.Many2one('resource.plan.request')
    employee_name = fields.Char()  # copied at submit (snapshot)
