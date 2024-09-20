from odoo import api, fields, models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        invoice = self.env['account.move'].browse(self._context.get('active_id'))
        if isinstance(res, dict):
            res.update({
                'cost_center_id': invoice.cost_center_id.id if invoice.cost_center_id else False
            })
        return res
