from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    vat = fields.Char(string='RUT')

    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id:
            self.vat = self.partner_id.vat
        return res


