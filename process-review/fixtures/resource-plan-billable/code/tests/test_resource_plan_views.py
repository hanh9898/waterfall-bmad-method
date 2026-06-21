# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase


class TestResourcePlanViews(ResourcePlanCase):
    """REQ-001/031: menu + action + tree/form view resource.plan ton tai va load duoc;
    form hien thi cac field chinh (project, lines, department=HB)."""

    def test_action_and_menu_exist(self):
        action = self.env.ref('project_invoice.action_resource_plan')
        self.assertEqual(action.res_model, 'resource.plan')
        self.assertTrue(self.env.ref('project_invoice.menu_resource_plan'))

    def test_form_view_has_key_fields(self):
        view = self.env.ref('project_invoice.view_resource_plan_form')
        arch = view.arch
        for f in ('project_id', 'state', 'line_ids', 'department_id'):
            self.assertIn(f, arch, "Form thieu field %s" % f)

    def test_form_renders(self):
        # fields_view_get khong loi -> view hop le, render duoc
        fv = self.env['resource.plan'].fields_view_get(
            view_id=self.env.ref('project_invoice.view_resource_plan_form').id, view_type='form')
        self.assertTrue(fv.get('arch'))
