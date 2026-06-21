# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase


class TestResourcePlanSummary(ResourcePlanCase):
    """resource.plan.summary (stored): phan anh plan (mm, amount=mm*price, currency
    theo rate.price_currency_id), refresh qua hook khi sua line/month.
    """

    def _summary(self):
        return self.env['resource.plan.summary'].search([('plan_id', '=', self.plan.id)])

    def test_summary_reflects_plan(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self._make_month(line, '2026-05-01', 0.5)
        rows = self._summary()
        self.assertEqual(len(rows), 2, "Phai co 1 dong summary moi thang co MM")
        by_month = {r.month_date: r for r in rows}
        r_apr = by_month['2026-04-01']
        self.assertEqual(r_apr.mm, 1.0)
        self.assertEqual(r_apr.amount, 1.0 * self.rate.price)
        self.assertEqual(r_apr.currency_id, self.currency)
        self.assertEqual(r_apr.employee_id, self.employee)
        self.assertEqual(by_month['2026-05-01'].amount, 0.5 * self.rate.price)

    def test_summary_refresh_on_month_edit(self):
        line = self._make_line()
        m = self._make_month(line, '2026-04-01', 1.0)
        m.write({'effort_mm': 2.0})
        rows = self._summary().filtered(lambda r: r.month_date == '2026-04-01')
        self.assertEqual(rows.mm, 2.0)
        self.assertEqual(rows.amount, 2.0 * self.rate.price)

    def test_summary_cleared_when_line_removed(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        self.assertTrue(self._summary())
        line.unlink()
        self.assertFalse(self._summary(), "Xoa line phai xoa summary tuong ung")
