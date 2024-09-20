# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from datetime import date, datetime

class Agreement(models.Model):
    _inherit = "agreement"

    card_number = fields.Many2one('payment.method.partner', string='Tarjeta')
    ofi_payment_method = fields.Many2one(related='card_number.type_subscription_contract', string='Método de Pago Oficial')
    intermediary = fields.Selection(related='card_number.type_subscription', string='Intermediario')
    intermediary_id = fields.Many2one('agreement.payment.intermediary', related='card_number.type_subscription_new', string='Intermediario')
    history_contract_id = fields.Many2one('history.contracts', string='Historial Contratos')
    state_card_number = fields.Selection(related='card_number.state')

    @api.onchange('card_number')
    def onchange_card_number(self):
        today = datetime.today()
        if self.card_number:
            history = self.env['history.contracts'].create({
                'contract_id': self.ids[0],
                'payment_partner_id': self.card_number.id,
                'user_id': self.env.uid,
                'date': today,
                'type': 'link'
            })
            if self.history_contract_id:
                self.env['history.contracts'].create({
                    'contract_id': self.ids[0],
                    'payment_partner_id': self.history_contract_id.payment_partner_id.id,
                    'user_id': self.env.uid,
                    'date': today,
                    'type': 'unrelated'
                })
            self.history_contract_id = history.id
