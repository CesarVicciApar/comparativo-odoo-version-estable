# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import date, timedelta


class AccountMove(models.Model):
    _inherit = "account.move"

    rate = fields.Float('Tasa')

    @api.onchange('date', 'currency_id')
    def _onchange_currency(self):
        if self.move_type in ['out_invoice']:
            if self.invoice_date:
                currate = self.env['res.currency.rate']
                rate_id = False
                i = 0
                while not rate_id and i < 11:
                    rate_date = self.invoice_date - timedelta(+i)
                    rate_id = currate.search([
                        ('name', '=', rate_date),
                        ('currency_id', '=', self.currency_id.id)])
                    i += 1
                self.rate = 1 / rate_id.rate if rate_id else 1 / self.currency_id.rate
        return super(AccountMove, self)._onchange_currency()


class AccountPayment(models.Model):
    _inherit = "account.payment"

    rate = fields.Float('Tasa')

    @api.onchange('currency_id')
    def _onchange_currency(self):
        self.rate = 1 / self.currency_id.rate
        #return super(AccountPayment, self)._onchange_currency()