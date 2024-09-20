# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    cost_center_id = fields.Many2one("cost.center", string='Centro de Costo')

    @api.model
    def default_get(self, fields):
        result = super(AccountInvoice, self).default_get(fields)
        if result.get('purchase_id'):
            po_id = result.get('purchase_id')
            purchase_order = self.env['purchase.order'].browse(po_id)
            if purchase_order.order_line[0]:
                result.update(
                    {'cost_center_id': purchase_order.order_line[0].cost_center_id and purchase_order.order_line[0].cost_center_id.id or False})
        return result

    @api.onchange('cost_center_id')
    def set_cost_center(self):
        for line in self.invoice_line_ids:
            line.cost_center_id = self.cost_center_id.id

    # def action_post(self):
    #     result = super(AccountInvoice, self).action_post()
    #     for line in self.line_ids:
    #         account = self.env['account.account'].browse(line.id)
    #         line.write({'cost_center_id': self.cost_center_id.id})
    #         jamie = 1
    #     return result

    def check_full_reconcile(self):
        res = super(AccountInvoice, self).check_full_reconcile()
        return res

    def _create_exchange_difference_move(self):
        res = super(AccountInvoice, self)._create_exchange_difference_move()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(AccountInvoice, self).create(vals_list)
        for line in lines.invoice_line_ids:
            if lines.cost_center_id:
                line.cost_center_id = lines.cost_center_id
            jamie = 1
        for line in lines.line_ids:
            account = self.env['account.account'].browse(line.id)
            if line.purchase_line_id:
                line.write({'cost_center_id': line.purchase_line_id.cost_center_id.id})
            if line.purchase_line_id.cost_center_id.id:
                lines.write({'cost_center_id': line.purchase_line_id.cost_center_id.id})
            #account.write({'cost_center_id': line.purchase_line_id.cost_center_id.id})
            jamie = 1
        return lines



class AccountInvoiceLine(models.Model):

    _inherit = 'account.move.line'

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")

    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True)

    @api.onchange('quantity')
    def set_default_cost_center(self):
        if self.move_id.cost_center_id:
            self.cost_center_id = self.move_id.cost_center_id.id


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")


    @api.model
    def create_exchange_rate_entry(self, aml_to_fix, move):
        res = super(AccountPartialReconcile, self).create_exchange_rate_entry(aml_to_fix, move)
        move.cost_center_id = aml_to_fix.cost_center_id.id
        return res
