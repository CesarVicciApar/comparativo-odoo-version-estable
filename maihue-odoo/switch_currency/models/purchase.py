# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'currency_id': self.currency_id.id,
            'rate': 1 / float(self.currency_id.rate),
            'rate_bkp': 1 / float(self.currency_id.rate)
        })
        return res
