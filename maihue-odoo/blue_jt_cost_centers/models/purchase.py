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


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        res['journal_id'] = journal.id
        return res

    @api.onchange('cost_center_id')
    def set_cost_center(self):
        for line in self.order_line:
            line.cost_center_id = self.cost_center_id.id

    # def action_create_invoice(self):
    #     """
    #     Prepare the dict of values to create the new invoice for a sales order. This method may be
    #     overridden to implement custom invoice generation (making sure to call super() to establish
    #     a clean extension chain).
    #     """
    #     self.ensure_one()
    #     result = super(PurchaseOrder, self).action_create_invoice()
    #
    #     for inv in self.invoice_ids:
    #         journal = self.env['account.move'].with_context(default_move_type=inv.move_type)._get_default_journal()
    #         inv.journal_id = journal.id
    #     # result['context'].pop({
    #     #     'default_journal_id': journal
    #     # })
    #     return result


    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
                if order.order_line[0]:
                    picking.write({'cost_center_id': order.order_line[0].cost_center_id})
                for stock_m in picking.move_ids_without_package:
                    stock_m.write({'cost_center_id': order.order_line[0].cost_center_id})
        return True


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo",)

    @api.onchange('product_qty')
    def set_default_cost_center(self):
        if self.cost_center_id:
            self.order_id.cost_center_id = self.cost_center_id
        # if self.order_id.cost_center_id:
        #     self.cost_center_id = self.order_id.cost_center_id.id
