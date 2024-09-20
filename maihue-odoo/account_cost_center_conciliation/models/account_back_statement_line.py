from odoo import _, api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    cost_center_id = fields.Many2one('cost.center', string='Cost Center')
