# -*- coding: utf-8 -*-
from psycopg2 import IntegrityError

from odoo.tests import common
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@common.at_install(False)
@common.post_install(True)
class TestResourcePlanHeader(TransactionCase):
    """resource.plan header: tao plan gan 1 du an, du lieu ben vung khi mo lai,
    rang buoc 1 plan / du an (UNIQUE project_id), state mac dinh 'draft'.
    """

    def setUp(self):
        super(TestResourcePlanHeader, self).setUp()

        self.dept = self.env['hr.department'].create({'name': 'RP_TEST_Dept'})

        # PM employee la field bat buoc khi tao project (ntq_project);
        # work_email + user_name_tmp + department_id deu required (ntq_hr).
        self.pm_employee = self.env['hr.employee'].create({
            'name': 'RP_TEST_PM',
            'work_email': 'pm.resource.plan@test.local',
            'user_name_tmp': 'rp_test_pm',
            'department_id': self.dept.id,
            'start_work_date': '2020-01-01',
        })

        self.partner = self.env['res.partner'].create({
            'name': 'RP_TEST_Customer',
            'customer': True,
            'is_company': True,
        })

        self.project = self.env['project.project'].create({
            'name': 'RP_TEST_Project',
            'partner_id': self.partner.id,
            'employee_id': self.pm_employee.id,
            'objective_n_mission': 'Resource plan header test.',
            'alias_name': 'rp_test_project',
            'start_date': '2026-04-01',
        })

    def _make_plan(self, project=None):
        return self.env['resource.plan'].create({
            'project_id': (project or self.project).id,
            'date_from': '2026-04-01',
            'date_to': '2026-09-01',
        })

    def test_create_plan_for_project(self):
        plan = self._make_plan()
        self.assertTrue(plan.id, "Plan phai duoc tao")
        self.assertEqual(plan.project_id, self.project,
                         "Plan phai gan dung du an")
        self.assertEqual(plan.state, 'draft',
                         "State mac dinh phai la 'draft'")

    def test_plan_persists_after_reload(self):
        plan = self._make_plan()
        plan.invalidate_cache()
        reloaded = self.env['resource.plan'].browse(plan.id)
        self.assertEqual(reloaded.project_id, self.project)
        self.assertEqual(reloaded.date_from, '2026-04-01')
        self.assertEqual(reloaded.date_to, '2026-09-01')

    @mute_logger('odoo.sql_db')
    def test_second_plan_same_project_rejected(self):
        self._make_plan()
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self._make_plan()
