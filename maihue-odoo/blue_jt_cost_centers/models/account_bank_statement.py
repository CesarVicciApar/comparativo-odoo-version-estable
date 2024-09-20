# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def _cron_process_reconcilie_transdata(self, job_count):
        if not job_count:
            job_count = 100
        #self.ensure_one()
        journal = self.env['account.journal'].search([
            ('name', '=', 'Transdata')])
        if not journal:
            journal = [12]
        #limit = int(self.env["ir.config_parameter"].sudo().get_param("account.reconcile.batch", 1000))
        bank_stmt = self.env['account.bank.statement'].search([
            ('journal_id', 'in', [journal.id]), ('state', '=', 'posted')], order="id desc")
            #('state', '=', 'posted'),
        #], limit=job_count, order="id desc")
        print(bank_stmt)
        if bank_stmt:
            for statement in bank_stmt:
                if statement.state == 'open':
                    statement.button_post()
                bank_stmt_lines = self.env['account.bank.statement.line'].search([
                    ('statement_id', '=', statement.id),
                    ('is_reconciled', '=', False),
                ])
                #statement.button_post()
                #statement.action_bank_reconcile_bank_statements()
                if not bank_stmt_lines:
                    continue
                if bank_stmt_lines:
                    print(bank_stmt_lines)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'bank_statement_reconciliation_view',
                    'context': {'statement_line_ids': bank_stmt_lines.ids,
                                'company_ids': self.mapped('company_id').ids},
                }