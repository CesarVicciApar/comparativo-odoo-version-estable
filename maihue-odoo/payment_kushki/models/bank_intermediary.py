from odoo import api, fields, models

class BankIntermediary(models.Model):
    _name = "bank.intermediary"
    _description = "Intermediario Bancario"

    name = fields.Char('Nombre')
    country_id = fields.Many2one('res.country', 'Pais')
    agreement_method_payment_id = fields.Many2one('agreement.payment.method', string="Metodo de Pago")
    method_payment_id = fields.Many2one('payment.method', string="Metodo de Pago")
    type_partner = fields.Many2one("agreement.type.partner", required=False, string="Tipo de Contrato", help="tipo de cliente (hogar, empresa, HORECA - INTERNO, HORECA - AUTOEMBOTELLADO)")