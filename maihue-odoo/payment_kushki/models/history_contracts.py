from odoo import api, fields, models

class HistoryContracts(models.Model):
    _name = 'history.contracts'
    _description = 'History Contracts'
    _order = 'id desc'

    contract_id = fields.Many2one('agreement', 'Contract')
    payment_partner_id = fields.Many2one('payment.method.partner', 'Payment')
    user_id = fields.Many2one('res.users', 'User')
    date = fields.Datetime('Fecha')
    type = fields.Selection(selection=[('link', 'Vínculada'), ('unrelated', 'Desvínculada')])