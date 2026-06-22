from odoo import fields, models


class ProjectTag(models.Model):
    _name = 'project.tag'

    name = fields.Char(required=True)
    color = fields.Integer()
    project_ids = fields.Many2many('project.project')
