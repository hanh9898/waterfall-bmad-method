# -*- coding: utf-8 -*-
from psycopg2 import IntegrityError

from odoo.tools import mute_logger

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanLine(ResourcePlanCase):
    """resource.plan.line: bat buoc employee + rate, UNIQUE(plan, employee, role),
    Department tu dien theo nhan vien, currency theo rate.price_currency_id.
    """

    def test_create_line_ok(self):
        line = self._make_line()
        self.assertTrue(line.id)
        self.assertEqual(line.employee_id, self.employee)
        self.assertEqual(line.rate_id, self.rate)
        self.assertEqual(line.currency_id, self.currency,
                         "currency_id phai bang rate_id.price_currency_id")

    @mute_logger('odoo.sql_db')
    def test_line_requires_employee(self):
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self._make_line(employee_id=False)

    @mute_logger('odoo.sql_db')
    def test_line_requires_rate(self):
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self._make_line(rate_id=False)

    @mute_logger('odoo.sql_db')
    def test_unique_plan_employee_role(self):
        self._make_line()
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._make_line()

    def test_department_autofill_from_employee(self):
        line = self.env['resource.plan.line'].new({
            'plan_id': self.plan.id,
            'employee_id': self.employee.id,
        })
        line._onchange_employee_id()
        self.assertEqual(line.department_id, self.employee.department_id,
                         "Department phai tu dien theo nhan vien")
