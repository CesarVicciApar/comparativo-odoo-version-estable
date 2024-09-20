# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


# class InventoryAdjustment(models.Model):
#     _inherit = 'stock.inventory'
#
#     force_date = fields.Datetime(string="Force Date")
#
#     def post_inventory(self):
#         if self.force_date:
#             self.accounting_date = self.force_date
#         res = super(InventoryAdjustment, self).post_inventory()
#         return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    force_date = fields.Datetime(string="Force Date")

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        self.write({'date_done': self.force_date})
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        force_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
            for move in self:
                if move.picking_id:
                    if move.picking_id.force_date:
                        force_date = move.picking_id.force_date
                    else:
                        force_date = move.picking_id.scheduled_date
                # if move.inventory_id:
                #     if move.inventory_id.force_date:
                #         force_date = move.inventory_id.force_date
                #     else:
                #         force_date = move.inventory_id.date

        res = super(StockMove, self)._action_done()
        if self.env.user.has_group('stock_force_date_app.group_stock_force_date'):
            if force_date:
                for move in res:
                    if move.picking_id:
                        self.env.cr.execute("""UPDATE stock_picking SET date = %s, scheduled_date = %s WHERE id = %s""",
                                            (force_date, force_date, move.picking_id.id))
                        if move.move_line_ids:
                            for move_line in move.move_line_ids:
                                move_line.write({'date':force_date})
                        # if move.account_move_ids:
                        #     for account_move in move.account_move_ids:
                        #         if move.inventory_id:
                        #             account_move.write({'ref':move.inventory_id.name})
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if vals.get('ref', False):
            for move in self:
                if move.stock_move_id.picking_id.force_date:
                    move.write({'date': move.stock_move_id.picking_id.force_date})
        return res
