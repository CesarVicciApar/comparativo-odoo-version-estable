# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class StockPicking(models.Model):
    _inherit = "stock.picking"

    currency_id = fields.Many2one('res.currency', 'Moneda')
    rate = fields.Float('Tasa')
    rate_bkp = fields.Float('Tasa OC')

    @api.onchange('force_date', 'currency_id')
    def _onchange_currency(self):
        currate = self.env['res.currency.rate']
        rate_id = False
        i = 0
        if self.currency_id:
            while not rate_id and i < 11:
                rate_date = self.force_date - timedelta(+i)
                rate_id = currate.search([
                    ('name', '=', rate_date),
                    ('currency_id', '=', self.currency_id.id)])
                i += 1
            self.rate = 1 / rate_id.rate if rate_id else 1 / self.currency_id.rate

    # @api.constrains('scheduled_date')
    # def set_rate(self):
    #     for rt in self:
    #         rt._onchange_currency()


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        if self.env.company.currency_id != self.picking_id.currency_id:
            if self.picking_id.rate_bkp == 0 or self.picking_id.rate == 0:
                raise ValidationError(
                    _("La tasa '%s' debe ser mayor a cero (0).") % (self.picking_id.currency_id.name,))
            rate1 = self.picking_id.rate_bkp
            rate2 = self.picking_id.rate
            cost = (rate2 * cost) / rate1
        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(cost)
        credit_value = debit_value

        valuation_partner_id = self._get_partner_id_for_valuation_lines()
        res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

        return res