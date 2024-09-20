from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    payment_method_partner_ids = fields.One2many(
        'payment.method.partner',
        'partner_id',
        'Payment Methods')