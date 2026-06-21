# -*- coding: utf-8 -*-
import logging

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

WINDOW_BEFORE = 2   # so thang truoc thang hien tai
WINDOW_TOTAL = 8    # tong so thang cua so mac dinh (current-2 .. current+5)
COMMITTED_STATES = ('approved', 'sent', 'paid', 'locked')   # period da-chot (REQ-016/018/033)


class ResourcePlan(models.Model):
    _name = 'resource.plan'
    _description = 'Resource Plan'

    @api.model
    def _month_window(self, ref_date=None):
        """Tra ve danh sach 8 dau-thang (current-2 .. current+5) - REQ-003/032."""
        ref = fields.Date.from_string(ref_date or fields.Date.today())
        start = ref.replace(day=1) - relativedelta(months=WINDOW_BEFORE)
        return [fields.Date.to_string(start + relativedelta(months=i))
                for i in range(WINDOW_TOTAL)]

    project_id = fields.Many2one(
        'project.project', string='Project',
        required=True, ondelete='cascade', index=True)
    date_from = fields.Date(string='From Month', required=True,
                            default=lambda self: self._month_window()[0])
    date_to = fields.Date(string='To Month', required=True,
                          default=lambda self: self._month_window()[-1])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved_l1', 'Approved L1'),
        ('approved_l2', 'Approved L2'),
    ], string='Status', default='draft', required=True, index=True)

    # Vong doi 2 cap: nguoi duyet + dau vet thoi gian
    dept_manager_id = fields.Many2one('res.users', string='Department Manager')
    im_id = fields.Many2one('res.users', string='Invoice Manager')
    submitted_by = fields.Many2one('res.users', string='Submitted By')
    submitted_at = fields.Datetime(string='Submitted At')
    approved_l1_by = fields.Many2one('res.users', string='Approved L1 By')
    approved_l1_at = fields.Datetime(string='Approved L1 At')
    approved_l2_by = fields.Many2one('res.users', string='Approved L2 By')
    approved_l2_at = fields.Datetime(string='Approved L2 At')
    reject_reason = fields.Text(string='Reject Reason')

    line_ids = fields.One2many(
        'resource.plan.line', 'plan_id', string='Resource Plan Lines')
    revision = fields.Integer(
        string='Revision', default=0,
        help='Token bump khi sua line/month -> plan.write_date phan anh sua cap dong '
             '(de Odoo optimistic-lock theo write_date hoat dong) - REQ-027.')
    has_divergence = fields.Boolean(
        string='Lech plan-period', compute='_compute_has_divergence',
        help='Period (billable) da bi sua truc tiep, khac voi plan da Dong bo - REQ-039.')
    last_sync_by = fields.Many2one('res.users', string='Last Synced By', readonly=True)
    last_sync_at = fields.Datetime(string='Last Synced At', readonly=True)

    _sql_constraints = [
        ('uq_resource_plan_project',
         'unique(project_id)',
         'Moi du an chi co mot resource plan.'),
    ]

    # ----- Vong doi 2 cap (REQ-024) -----
    @api.multi
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chi submit duoc tu Draft.'))
            rec.write({'state': 'submitted', 'submitted_by': self.env.uid,
                       'submitted_at': fields.Datetime.now()})
        return True

    @api.multi
    def action_approve_l1(self):
        if not (self.env.user.has_group('base.group_system')
                or self.env.user.has_group('ntq_project.group_project_department_manager')):
            raise UserError(_('Chi Department Manager duyet cap 1.'))
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Chi duyet L1 tu Submitted.'))
            rec.write({'state': 'approved_l1', 'approved_l1_by': self.env.uid,
                       'approved_l1_at': fields.Datetime.now()})
        return True

    @api.multi
    def action_approve_l2(self):
        if not (self.env.user.has_group('base.group_system')
                or self.env.user.has_group('project_invoice.group_project_invoice_manager')):
            raise UserError(_('Chi Invoice Manager duyet cap 2.'))
        for rec in self:
            if rec.state != 'approved_l1':
                raise UserError(_('Chi duyet L2 tu Approved L1.'))
            rec.write({'state': 'approved_l2', 'approved_l2_by': self.env.uid,
                       'approved_l2_at': fields.Datetime.now()})
        return True

    @api.multi
    def action_reject(self, reason=None):
        """Tra lai ve Draft (REQ-024). Dept Manager chi reject o Submitted; IM/Admin o
        Submitted hoac Approved L1. Approved L2 da Dong bo -> KHONG cho reject."""
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        is_im = user.has_group('project_invoice.group_project_invoice_manager')
        is_dm = user.has_group('ntq_project.group_project_department_manager')
        for rec in self:
            if rec.state == 'approved_l2':
                raise UserError(_('Plan da Approved L2 (da Dong bo) - khong duoc Tra lai.'))
            if rec.state == 'submitted':
                if not (is_admin or is_im or is_dm):
                    raise UserError(_('Chi Dept Manager/IM/Admin duoc Tra lai.'))
            elif rec.state == 'approved_l1':
                if not (is_admin or is_im):
                    raise UserError(_('Chi IM/Admin duoc Tra lai o Approved L1.'))
            else:
                raise UserError(_('Chi Tra lai duoc tu Submitted hoac Approved L1.'))
            rec.write({'state': 'draft', 'reject_reason': reason or rec.reject_reason})
        return True

    # ----- Dong bo plan -> invoice period/member (REQ-014/015/016/022/026) -----
    @api.multi
    def _plan_months(self):
        self.ensure_one()
        start = fields.Date.from_string(self.date_from).replace(day=1)
        end = fields.Date.from_string(self.date_to).replace(day=1)
        out, cur = [], start
        while cur <= end:
            out.append(fields.Date.to_string(cur))
            cur += relativedelta(months=1)
        return out

    @api.multi
    def _overlay_period(self, period, month):
        """Overlay effort_mm/rate_id/effort_ratio tu plan len member line cua period."""
        self.ensure_one()
        Member = self.env['project.invoice.member']
        for line in self.line_ids:
            mrow = line.month_ids.filtered(lambda m: m.month_date == month)
            if not mrow:
                continue
            member = period.invoice_member_ids.filtered(
                lambda x: x.employee_id == line.employee_id
                and x.project_role_id == line.project_role_id)
            if member:
                member = member[0]
            else:
                member = Member.create({
                    'period_id': period.id,
                    'employee_id': line.employee_id.id,
                    'project_role_id': line.project_role_id.id,
                    'department_id': line.department_id.id,
                })
            member.write({
                'effort_mm': mrow.effort_mm,
                'rate_id': line.rate_id.id,
                'effort_ratio': line.effort_ratio,
            })

    # ----- Predicate da-chot + chi bao lech (REQ-018/019/033/037/039) -----
    @api.model
    def _committed_reason(self, project, month):
        """Tra ve state period neu thang da-chot (approved/sent/paid/locked), nguoc lai ''."""
        period = self.env['project.invoice.period'].search([
            ('project_id', '=', project.id), ('month_date', '=', month)], limit=1)
        if period and period.state in COMMITTED_STATES:
            return period.state
        return ''

    @api.model
    def month_has_committed_invoice(self, project, month):
        return bool(self._committed_reason(project, month))

    @api.multi
    def _divergent_keys(self):
        """Tap (employee_id, role_id, month) ma billable period KHAC plan da Dong bo
        (period bi sua truc tiep) - REQ-039. Rong neu plan chua tung Dong bo."""
        self.ensure_one()
        diverged = set()
        if not self.last_sync_at or not self.project_id:
            return diverged
        Period = self.env['project.invoice.period']
        plan_map = {}
        for line in self.line_ids:
            for m in line.month_ids:
                plan_map[(line.employee_id.id, line.project_role_id.id,
                          m.month_date)] = m.effort_mm or 0.0
        for month in self._plan_months():
            period = Period.search([
                ('project_id', '=', self.project_id.id),
                ('month_date', '=', month)], limit=1)
            if not period:
                continue
            for mem in period.invoice_member_ids:
                key = (mem.employee_id.id, mem.project_role_id.id, month)
                plan_mm = plan_map.get(key)
                mem_mm = mem.effort_mm or 0.0
                if plan_mm is None:
                    if mem_mm > 0:
                        diverged.add(key)
                elif abs(mem_mm - plan_mm) > 1e-9:
                    diverged.add(key)
        return diverged

    @api.depends('state', 'last_sync_at', 'line_ids.month_ids.effort_mm', 'line_ids.rate_id')
    def _compute_has_divergence(self):
        for rec in self:
            rec.has_divergence = bool(rec._divergent_keys())

    @api.multi
    def _check_sync_valid(self):
        """Chan Dong bo khi plan khong hop le (REQ-021)."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Plan rong, khong the Dong bo.'))
        bad = self.line_ids.filtered(
            lambda l: any((m.effort_mm or 0.0) > 0 for m in l.month_ids) and not l.rate_id)
        if bad:
            raise UserError(_('Co dong MM>0 nhung thieu rate.'))
        if not any((m.effort_mm or 0.0) > 0
                   for l in self.line_ids for m in l.month_ids):
            raise UserError(_('Plan khong co MM>0 nao de Dong bo.'))

    @api.multi
    def action_open_sync_wizard(self):
        """Mo wizard Dong bo (xem truoc + blocking confirm) - REQ-017."""
        self.ensure_one()
        wiz = self.env['resource.plan.sync.wizard'].create({'plan_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dong bo Billable'),
            'res_model': 'resource.plan.sync.wizard',
            'res_id': wiz.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def action_sync_from_plan(self):
        """Dong bo: voi moi thang trong plan -> find-or-create period(draft),
        dung lai member skeleton bang action_generate_lines roi overlay MM/rate tu plan.
        Bo qua thang da-chot (kem ly do "da khoa"/"da co"). Period dang submitted thi
        re-sync downstream billable. Moi thang chay trong savepoint (atomic). Serialize
        bang row-lock tren plan (REQ-014..018/021/022/026/037).
        Tra ve {'synced': [month...], 'skipped': [(month, ly_do)...]}."""
        self.ensure_one()
        if not (self.env.user.has_group('base.group_system')
                or self.env.user.has_group('project_invoice.group_project_invoice_manager')):
            raise UserError(_('Chi Invoice Manager moi Dong bo.'))
        if self.state != 'approved_l2':
            raise UserError(_('Chi Dong bo khi plan da Approved L2.'))
        self._check_sync_valid()
        # Serialize: khoa hang plan -> 2 IM song song khong nhan doi (REQ-014)
        self.env.cr.execute('SELECT id FROM resource_plan WHERE id = %s FOR UPDATE', (self.id,))
        Period = self.env['project.invoice.period']
        result = {'synced': [], 'skipped': []}
        for month in self._plan_months():
            period = Period.search([
                ('project_id', '=', self.project_id.id),
                ('month_date', '=', month),
            ], limit=1)
            if not period:
                period = Period.create({
                    'project_id': self.project_id.id, 'month_date': month,
                })
            if period.state in COMMITTED_STATES:   # re-check duoi lock (TOCTOU)
                reason = _('da khoa') if period.state == 'locked' else _('da co')
                result['skipped'].append((month, reason))
                continue
            was_submitted = period.state == 'submitted'
            try:
                with self.env.cr.savepoint():
                    period.invoice_member_ids.unlink()
                    period.action_generate_lines()
                    self._overlay_period(period, month)
                    # Dong MM=0 (chu dich hoac mac dinh) -> khong sinh member billable
                    period.invoice_member_ids.filtered(
                        lambda m: (m.effort_mm or 0.0) <= 0.0).unlink()
                    # Period da submitted da day downstream -> re-sync (REQ-014/016)
                    if was_submitted and hasattr(period, '_sync_to_billable_tables'):
                        period._sync_to_billable_tables()
                result['synced'].append(month)
            except UserError:
                raise
            except Exception:
                _logger.exception(
                    'Resource plan %s: Dong bo thang %s that bai', self.id, month)
                result['skipped'].append((month, _('loi')))
        # Audit Dong bo (NFR-004) - chi khi thuc su co thang duoc dong bo
        if result['synced']:
            self.sudo().write({
                'last_sync_by': self.env.uid,
                'last_sync_at': fields.Datetime.now(),
            })
        return result

    @api.multi
    def _touch(self):
        """Bump revision -> plan.write_date doi khi sua line/month, de Odoo
        optimistic-lock theo write_date hoat dong o cap plan (REQ-027)."""
        if self.env.context.get('rp_no_touch'):
            return
        for rec in self:
            rec.sudo().write({'revision': rec.revision + 1})

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_('Tu thang khong duoc sau Den thang.'))

    @api.multi
    def action_add_month(self, month_date):
        """Them mot thang vao plan duy nhat: tao o cho moi dong + mo rong date_to (REQ-035)."""
        self.ensure_one()
        # Chuan hoa ve dau thang (P9)
        month_date = fields.Date.to_string(
            fields.Date.from_string(month_date).replace(day=1))
        Month = self.env['resource.plan.line.month']
        for line in self.line_ids:
            if not line.month_ids.filtered(lambda m: m.month_date == month_date):
                Month.create({'line_id': line.id, 'month_date': month_date,
                              'effort_mm': 0.0})
        if not self.date_to or month_date > self.date_to:
            self.date_to = month_date
        return True

    @api.model
    def _migrate_from_invoices(self, projects=None):
        """Migration lan dau (REQ-034): nap project.invoice.member -> resource plan.
        Idempotent (key: project,employee,role,month); bo qua employee non-approved
        va member khong co rate; dedup trung (project,employee,month). Tra ve report
        kem doi chieu (so dong + tong amount plan vs member nguon)."""
        Member = self.env['project.invoice.member']
        Line = self.env['resource.plan.line']
        Month = self.env['resource.plan.line.month']
        report = {'plans': 0, 'lines': 0, 'months': 0, 'skipped': 0}
        domain = [('period_id', '!=', False)]
        if projects is not None:
            domain.append(('period_id.project_id', 'in', projects.ids))
        source_members = Member.search(domain)
        by_project = {}
        for m in source_members:
            proj = m.period_id.project_id
            if proj:
                by_project.setdefault(proj, self.env['project.invoice.member'])
                by_project[proj] |= m
        for proj, mems in by_project.items():
            plan = self.search([('project_id', '=', proj.id)], limit=1)
            if not plan:
                months = [d for d in mems.mapped('period_id.month_date') if d]
                if not months:
                    continue
                plan = self.with_context(rp_migrating=True).create({
                    'project_id': proj.id, 'state': 'draft',
                    'date_from': min(months), 'date_to': max(months),
                })
                report['plans'] += 1
            for m in mems:
                emp, role = m.employee_id, m.project_role_id
                if not emp or emp.process_state != 'approved' or not m.rate_id \
                        or not m.period_id.month_date:
                    report['skipped'] += 1
                    continue
                line = Line.search([
                    ('plan_id', '=', plan.id), ('employee_id', '=', emp.id),
                    ('project_role_id', '=', role.id)], limit=1)
                if not line:
                    line = Line.with_context(rp_migrating=True).create({
                        'plan_id': plan.id, 'employee_id': emp.id,
                        'project_role_id': role.id, 'department_id': m.department_id.id,
                        'rate_id': m.rate_id.id, 'effort_ratio': m.effort_ratio,
                        'migrated': True,
                    })
                    report['lines'] += 1
                month_date = m.period_id.month_date
                if Month.search([('line_id', '=', line.id),
                                 ('month_date', '=', month_date)], limit=1):
                    continue  # idempotent + dedup (project,employee,month)
                Month.with_context(rp_migrating=True).create({
                    'line_id': line.id, 'month_date': month_date,
                    'effort_mm': m.effort_mm,
                })
                report['months'] += 1
        # ----- Doi chieu (REQ-034 / TC-053) -----
        plan_recs = self.search([('project_id', 'in', [p.id for p in by_project])]) \
            if by_project else self.browse()
        plan_months = Month.search([('line_id.plan_id', 'in', plan_recs.ids)]) \
            if plan_recs else Month.browse()
        report['source_member_count'] = len(source_members)
        report['source_amount'] = sum(source_members.mapped('amount'))
        report['plan_month_count'] = len(plan_months)
        report['plan_amount'] = sum(
            (mo.effort_mm or 0.0) * (mo.line_id.rate_id.price or 0.0)
            for mo in plan_months)
        report['reconciled'] = (
            report['skipped'] == 0
            and report['plan_month_count'] == report['source_member_count'])
        return report

    @api.multi
    def action_prefill_from_allocation(self):
        """Pre-fill dong tu allocation (project.member) hien co cua du an (REQ-010).
        Chi nhan vien approved; effort_ratio/role/dept lay tu allocation; rate_id
        dat mac dinh (rate dau tien) de user dieu chinh sau."""
        self.ensure_one()
        Line = self.env['resource.plan.line']
        default_rate = self.env['ntq.project.billable.rate'].search([], limit=1)
        existing_emp = self.line_ids.mapped('employee_id')
        members = self.env['project.member'].search(
            [('project_id', '=', self.project_id.id)])
        for m in members:
            emp = m.employee_id
            if not emp or emp in existing_emp:
                continue
            if emp.process_state != 'approved' or not default_rate:
                continue
            Line.create({
                'plan_id': self.id,
                'employee_id': emp.id,
                'project_role_id': m.project_role_id.id,
                'department_id': emp.department_id.id,
                'effort_ratio': m.effort_ratio,
                'member_id': m.id,
                'rate_id': default_rate.id,
            })
            existing_emp |= emp
        return True

    @api.multi
    def _refresh_summary(self):
        """Dung lai summary cho cac plan nay (goi tu hook CUD line/month)."""
        if self.env.context.get('rp_no_summary'):
            return
        self.env['resource.plan.summary'].sudo()._rebuild_for_plans(self)
