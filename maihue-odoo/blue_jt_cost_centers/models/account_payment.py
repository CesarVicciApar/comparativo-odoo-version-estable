# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger

_logger = getLogger(__name__)


class account_payment(models.Model):
    _inherit = 'account.payment'

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")

    def set_payment_cost_center(self):
        for line in self.move_id.line_ids:
            if not line.cost_center_id:
                line.write({'cost_center_id': self.cost_center_id})

    def action_post(self):
        r = super(account_payment, self).action_post()
        self.set_payment_cost_center()
        return r

    def _prepare_payment_moves(self):
        res = super(account_payment, self)._prepare_payment_moves()
        for line in res:
            line.update({'cost_center_id': self.cost_center_id.id})
            return line