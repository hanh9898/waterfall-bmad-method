# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase


class TestResourcePlanMigration(ResourcePlanCase):
    """Migration lan dau (REQ-034): nap invoice member -> resource plan(draft); idempotent;
    bo qua employee non-approved / member khong rate; dedup trung (project,employee,month)."""

    def setUp(self):
        super(TestResourcePlanMigration, self).setUp()
        partner = self.env['res.partner'].create({'name': 'RP_Mig_C', 'customer': True})
        self.proj_mig = self.env['project.project'].create({
            'name': 'RP_Mig_Project', 'partner_id': partner.id,
            'employee_id': self.pm_employee.id, 'alias_name': 'rp_mig',
            'objective_n_mission': 'x', 'start_date': '2026-04-01',
            'delivery_team_id': self.dept_delivery.id,
        })
        self.Member = self.env['project.invoice.member']
        self.Period = self.env['project.invoice.period']
        self.period_apr = self.Period.create({
            'project_id': self.proj_mig.id, 'month_date': '2026-04-01'})
        self.Member.create({
            'period_id': self.period_apr.id, 'employee_id': self.employee.id,
            'project_role_id': self.role.id, 'rate_id': self.rate.id,
            'department_id': self.dept.id, 'effort_mm': 1.0,
        })

    def _migrate(self):
        return self.env['resource.plan']._migrate_from_invoices(projects=self.proj_mig)

    def _plan(self):
        return self.env['resource.plan'].search([('project_id', '=', self.proj_mig.id)])

    def test_migrate_creates_plan(self):
        rep = self._migrate()
        plan = self._plan()
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan.state, 'draft')
        line = plan.line_ids.filtered(lambda l: l.employee_id == self.employee)
        self.assertTrue(line)
        self.assertTrue(line.migrated)
        m = line.month_ids.filtered(lambda x: x.month_date == '2026-04-01')
        self.assertEqual(m.effort_mm, 1.0)
        self.assertGreaterEqual(rep['plans'], 1)

    def test_migrate_idempotent(self):
        self._migrate()
        rep2 = self._migrate()
        self.assertEqual(rep2['plans'], 0)
        self.assertEqual(rep2['lines'], 0)
        self.assertEqual(rep2['months'], 0)
        self.assertEqual(len(self._plan()), 1)

    def test_migrate_skips_non_approved(self):
        draft_emp = self.env['hr.employee'].create({
            'name': 'RP_Mig_Draft', 'work_email': 'rp.mig.draft@test.local',
            'user_name_tmp': 'rp_mig_draft', 'department_id': self.dept.id,
            'start_work_date': '2020-01-01', 'process_state': 'draft',
        })
        p2 = self.Period.create({'project_id': self.proj_mig.id, 'month_date': '2026-05-01'})
        self.Member.create({
            'period_id': p2.id, 'employee_id': draft_emp.id, 'project_role_id': self.role.id,
            'rate_id': self.rate.id, 'department_id': self.dept.id, 'effort_mm': 1.0,
        })
        self._migrate()
        self.assertFalse(self._plan().line_ids.filtered(lambda l: l.employee_id == draft_emp),
                         "Employee non-approved bi bo qua")

    def test_migrate_skips_no_rate(self):
        emp2 = self.env['hr.employee'].create({
            'name': 'RP_Mig_NoRate', 'work_email': 'rp.mig.norate@test.local',
            'user_name_tmp': 'rp_mig_norate', 'department_id': self.dept.id,
            'start_work_date': '2020-01-01', 'process_state': 'approved',
        })
        p3 = self.Period.create({'project_id': self.proj_mig.id, 'month_date': '2026-06-01'})
        self.Member.create({
            'period_id': p3.id, 'employee_id': emp2.id, 'project_role_id': self.role.id,
            'rate_id': False, 'department_id': self.dept.id, 'effort_mm': 1.0,
        })
        self._migrate()
        self.assertFalse(self._plan().line_ids.filtered(lambda l: l.employee_id == emp2),
                         "Member khong co rate bi bo qua")

    def test_migrate_one_month_row_per_member(self):
        # Nguon da co UNIQUE(period, employee) -> khong the trung (project,employee,month).
        # Migration dam bao dung 1 month row + re-run khong nhan doi (dedup TC-069).
        self._migrate()
        self._migrate()
        line = self._plan().line_ids.filtered(lambda l: l.employee_id == self.employee)
        months = line.month_ids.filtered(lambda x: x.month_date == '2026-04-01')
        self.assertEqual(len(months), 1, "Dung 1 month row, khong nhan doi")

    def test_migrate_reconciliation_report(self):
        # D6: report co doi chieu so dong + amount plan vs member nguon
        rep = self._migrate()
        self.assertIn('source_member_count', rep)
        self.assertIn('plan_month_count', rep)
        self.assertIn('source_amount', rep)
        self.assertIn('plan_amount', rep)
        self.assertIn('reconciled', rep)
        self.assertGreaterEqual(rep['source_member_count'], 1)
        self.assertEqual(rep['plan_month_count'], rep['source_member_count'],
                         "1 member nguon -> 1 month row plan")
        self.assertTrue(rep['reconciled'])
