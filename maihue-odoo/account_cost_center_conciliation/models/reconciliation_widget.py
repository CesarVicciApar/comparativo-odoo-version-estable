from odoo import _, api, fields, models


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def process_bank_statement_line(self, st_line_ids, data):
        res = super(AccountReconciliation, self).process_bank_statement_line(st_line_ids, data)
        st_lines = self.env['account.bank.statement.line'].browse(st_line_ids)
        if not st_lines.journal_id.id == 12:
            vals = data[0]['lines_vals_list']
            cost_center_id = [val.get('cost_center_id', False) for val in vals if val.get('cost_center_id')]
            if cost_center_id:
                move_line_ids = st_lines.move_id.invoice_line_ids
                for line in move_line_ids.filtered(lambda l: not l.cost_center_id):
                    line.write({
                        'cost_center_id': cost_center_id[0]
                    })
        else:
            move_line_ids = st_lines.move_id.invoice_line_ids
            for line in move_line_ids.filtered(lambda l: l.cost_center_id):
                line.write({
                    'cost_center_id': None
                })
        return res

