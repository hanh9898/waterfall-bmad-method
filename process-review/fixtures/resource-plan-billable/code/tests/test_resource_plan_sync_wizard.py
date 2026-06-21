# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase


class TestResourcePlanSyncWizard(ResourcePlanCase):
    """Wizard Dong bo: preview create/overwrite/skip; blocking confirm chi khi co thang
    se ghi de lines da co (REQ-017); confirm chay Dong bo."""

    def _approve(self):
        self.plan.action_submit()
        self.plan.action_approve_l1()
        self.plan.action_approve_l2()

    def _wizard(self):
        return self.env['resource.plan.sync.wizard'].create({'plan_id': self.plan.id})

    def test_preview_create_only_no_confirm(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        wiz = self._wizard()
        self.assertFalse(wiz.needs_confirm, "Chua co lines -> khong blocking confirm")
        self.assertIn('create', wiz.preview)

    def test_overwrite_needs_confirm(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        self.plan.action_sync_from_plan()   # tao period + members
        wiz = self._wizard()
        self.assertTrue(wiz.needs_confirm, "Da co lines -> blocking confirm")
        self.assertIn('overwrite', wiz.preview)

    def test_confirm_runs_sync(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        self._wizard().action_confirm()
        period = self.env['project.invoice.period'].search([
            ('project_id', '=', self.project.id), ('month_date', '=', '2026-04-01')])
        self.assertTrue(period.invoice_member_ids, "Confirm phai chay Dong bo")

    def test_open_sync_wizard_action(self):
        # D2: nut form mo wizard preview thay vi sync thang
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._approve()
        act = self.plan.action_open_sync_wizard()
        self.assertEqual(act['res_model'], 'resource.plan.sync.wizard')
        self.assertEqual(act['target'], 'new')
        wiz = self.env['resource.plan.sync.wizard'].browse(act['res_id'])
        self.assertEqual(wiz.plan_id, self.plan)
