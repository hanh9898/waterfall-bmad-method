# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanWindow(ResourcePlanCase):
    """Cua so 8 thang (current-2..current+5), from>to bi tu choi, cot currency theo
    rate.price_currency_id, them thang vao plan duy nhat."""

    def test_month_window_8_months(self):
        w = self.env['resource.plan']._month_window('2026-06-15')
        self.assertEqual(w, ['2026-04-01', '2026-05-01', '2026-06-01', '2026-07-01',
                             '2026-08-01', '2026-09-01', '2026-10-01', '2026-11-01'])

    def test_month_window_crosses_year(self):
        w = self.env['resource.plan']._month_window('2026-11-15')
        self.assertEqual(w, ['2026-09-01', '2026-10-01', '2026-11-01', '2026-12-01',
                             '2027-01-01', '2027-02-01', '2027-03-01', '2027-04-01'])

    def test_default_window_applied(self):
        partner2 = self.env['res.partner'].create({'name': 'RP_C9', 'customer': True})
        project2 = self.env['project.project'].create({
            'name': 'RP_P9', 'partner_id': partner2.id, 'employee_id': self.pm_employee.id,
            'alias_name': 'rp_p9', 'objective_n_mission': 'x', 'start_date': '2026-04-01',
        })
        plan2 = self.env['resource.plan'].create({'project_id': project2.id})
        window = self.env['resource.plan']._month_window()
        self.assertEqual(plan2.date_from, window[0])
        self.assertEqual(plan2.date_to, window[-1])

    def test_from_after_to_rejected(self):
        partner3 = self.env['res.partner'].create({'name': 'RP_C9b', 'customer': True})
        project3 = self.env['project.project'].create({
            'name': 'RP_P9b', 'partner_id': partner3.id, 'employee_id': self.pm_employee.id,
            'alias_name': 'rp_p9b', 'objective_n_mission': 'x', 'start_date': '2026-04-01',
        })
        with self.assertRaises(ValidationError):
            self.env['resource.plan'].create({
                'project_id': project3.id, 'date_from': '2026-09-01', 'date_to': '2026-04-01',
            })

    def test_currency_follows_rate(self):
        line = self._make_line()
        self.assertEqual(line.currency_id, self.rate.price_currency_id)
        self.assertEqual(line.currency_id, self.currency)

    def test_add_month_to_single_plan(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self.plan.action_add_month('2026-12-01')
        months = line.month_ids.filtered(lambda m: m.month_date == '2026-12-01')
        self.assertTrue(months, "Them thang phai tao o cho moi dong")
        self.assertGreaterEqual(self.plan.date_to, '2026-12-01')
        self.assertEqual(self.env['resource.plan'].search_count(
            [('project_id', '=', self.project.id)]), 1, "Van la plan duy nhat")
