
from odoo import api, fields, models

class PaymentMethod(models.Model):
    _name = 'payment.method'

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Codigo')
    agreement_method_payment_id = fields.Many2one('agreement.payment.method', required=True, string="Metodo de Pago")