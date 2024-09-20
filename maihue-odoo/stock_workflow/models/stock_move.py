from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        for move in self:
            if move.picking_id.picking_type_code == 'internal' and move.picking_id.type_transfer not in ['normal']:
                if move.picking_id.backorder_id:
                    move.picking_id.type_transfer = move.picking_id.backorder_id.type_transfer
                move.picking_id.button_reserve_picking_internal()
            else:
                if move.picking_id.backorder_id:
                    move.picking_id.type_transfer = move.picking_id.backorder_id.type_transfer
                return super(StockMove, move)._action_assign()
