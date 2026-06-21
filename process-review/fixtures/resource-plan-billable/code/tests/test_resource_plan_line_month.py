# -*- coding: utf-8 -*-
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

from .common_resource_plan import ResourcePlanCase


class TestResourcePlanLineMonth(ResourcePlanCase):
    """resource.plan.line.month: effort_mm >= 0, UNIQUE(line, month),
    them dong employee trung (UNIQUE plan,employee,month) bi chan.
    """

    def test_create_month_ok(self):
        line = self._make_line()
        m = self._make_month(line, '2026-04-01', 1.0)
        self.assertTrue(m.id)
        self.assertEqual(m.effort_mm, 1.0)

    @mute_logger('odoo.sql_db')
    def test_negative_mm_rejected(self):
        line = self._make_line()
        with self.assertRaises(IntegrityError):   # DB CHECK(effort_mm>=0)
            with self.env.cr.savepoint():
                self._make_month(line, '2026-04-01', -0.5)

    @mute_logger('odoo.sql_db')
    def test_unique_line_month(self):
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._make_month(line, '2026-04-01', 0.5)

    @mute_logger('odoo.sql_db')
    def test_duplicate_employee_same_month_rejected(self):
        """TC-070: cung (plan, employee, thang) khong duoc lap.

        Vi mot employee chi co 1 line/plan (UNIQUE plan,employee,role) va 1 line
        chi co 1 month-row/thang (UNIQUE line,month), nen trung (plan,employee,month)
        bi chan boi to hop hai UNIQUE nay.
        """
        line = self._make_line()
        self._make_month(line, '2026-04-01', 1.0)
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._make_month(line, '2026-04-01', 0.5)
