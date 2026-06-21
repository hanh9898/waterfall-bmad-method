# -*- coding: utf-8 -*-
from .common_resource_plan import ResourcePlanCase

IM_GROUP = 'project_invoice.group_project_invoice_manager'


class TestResourcePlanAllocSync(ResourcePlanCase):
    """Dong bo mot chieu plan -> allocation (project.member):
    them dong -> tao member; sua effort -> cap nhat member; xoa dong -> set end_at;
    mot chieu (sua member khong doi plan); chay duoi quyen user (no sudo)."""

    def _members(self, employee):
        return self.env['project.member'].search([
            ('project_id', '=', self.project.id),
            ('employee_id', '=', employee.id),
        ])

    def test_add_line_creates_allocation(self):
        line = self._make_line()
        self.assertTrue(line.member_id, "Them dong phai tao/lien ket allocation")
        self.assertEqual(line.member_id.employee_id, self.employee)
        self.assertEqual(line.member_id.project_id, self.project)

    def test_edit_effort_updates_allocation(self):
        line = self._make_line(effort_ratio=0.5)
        line.write({'effort_ratio': 0.8})
        self.assertEqual(line.member_id.effort_ratio, 0.8)

    def test_unlink_line_sets_end_at(self):
        line = self._make_line()
        member = line.member_id
        line.unlink()
        self.assertTrue(member.exists(), "Khong xoa cung allocation")
        self.assertTrue(member.end_at, "Xoa dong phai set end_at")

    def test_unlink_line_without_member_no_error(self):
        line = self._make_line()
        line.write({'member_id': False})
        line.unlink()  # khong duoc raise
        self.assertFalse(line.exists())

    def test_add_existing_allocation_no_dup(self):
        alloc = self._make_allocation()
        line = self._make_line()
        self.assertEqual(line.member_id, alloc, "Phai lien ket allocation co san")
        self.assertEqual(len(self._members(self.employee)), 1, "Khong tao trung allocation")

    def test_edit_member_does_not_change_plan(self):
        line = self._make_line(effort_ratio=0.5)
        line.member_id.write({'effort_ratio': 0.9})
        self.assertEqual(line.effort_ratio, 0.5, "Sua member khong duoc doi plan (mot chieu)")

    def test_sync_runs_as_user_not_sudo(self):
        im_user = self._make_user('rp_im_sync', [IM_GROUP])
        line = self.env['resource.plan.line'].sudo(im_user).create({
            'plan_id': self.plan.id, 'employee_id': self.employee.id,
            'rate_id': self.rate.id, 'project_role_id': self.role.id,
            'effort_ratio': 1.0,
        })
        self.assertEqual(line.member_id.create_uid, im_user,
                         "Allocation phai tao duoi quyen user (khong sudo)")
