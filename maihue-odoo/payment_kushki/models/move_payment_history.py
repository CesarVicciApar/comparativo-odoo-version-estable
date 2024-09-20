from odoo import api, fields, models

class MovePaymentHistory(models.Model):
    _name = 'move.payment.history'
    _description = 'Move Payment History'
    _order = 'id desc'

    move_id = fields.Many2one('account.move', 'Move')
    user_id = fields.Many2one('res.users','User')
    date = fields.Date('Fecha')
    type = fields.Selection(selection=[('credit', 'Credito'), ('debit', 'Debito')])
    last_four_digits = fields.Char('Ultimos 4 digitos')
    transaction_id = fields.Char(string='Transaction id')
    transaction_number = fields.Char(string='Transaction number')
    transaction_reference = fields.Char(string='Transaction reference')
    amount = fields.Float(string='Amount')
    state = fields.Char(string='State')
    detail = fields.Char(string='Detail')
    state_payment = fields.Selection(string='Estado de Cobro', selection=[('approved', 'Aprobado'),
                                                                          ('send_paid', 'Enviado a Cobro'),
                                                                          ('rejected', 'Rechazado'),
                                                                          ('pending', 'Pendiente Intento de Cobro')],
                                     copy=False, default="pending", tracking=2)
    kushki_log_id = fields.Many2one('kushki.log', 'Kushki Log')


