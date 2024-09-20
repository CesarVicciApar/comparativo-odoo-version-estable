from odoo import api, fields, models
from odoo.exceptions import UserError

class ExchangeSerialNumberQuant(models.TransientModel):
    _name = 'exchange.serial.number.quant'

    @api.model
    def default_get(self, default_fields):
        res = super(ExchangeSerialNumberQuant, self).default_get(default_fields)
        quants = self.env['stock.quant'].browse(self.env.context.get('active_ids'))
        validate = quants.mapped('validate')
        for valid in validate:
            if valid:
                raise UserError('Debe seleccionar 2 registros que no esten validados')
        if len(quants) == 2:
            res['first_quant_id'] = quants[0].id
            res['second_quant_id'] = quants[1].id
        else:
            raise UserError('Debe seleccionar 2 registros para intercambiar los equipos entre ellos')
        self.first_quant_id.action_set_inventory_quantity()
        self.second_quant_id.action_set_inventory_quantity()
        return res

    first_quant_id = fields.Many2one('stock.quant', 'Ubicacion 1')
    second_quant_id = fields.Many2one('stock.quant', 'Ubicacion 2')

    def action_exchange_lot_quant(self):
        StockMoveLine = self.env['stock.move.line']
        StockMove = self.env['stock.move']
        inventory_loss_location = self.env['stock.location'].search([('name', '=', 'Inventory adjustment')])
        first_lot = self.first_quant_id.lot_id
        second_lot = self.second_quant_id.lot_id
        ####### PRIMER MOVIMIENTO #############
        vals_move_adjustment = {
            'product_id': self.first_quant_id.product_id.id,
            'name': self.first_quant_id.product_id.display_name,
            'location_id': self.first_quant_id.location_id.id,
            'location_dest_id': inventory_loss_location.id,
            'lot_ids': [(4, first_lot.ids)],
            'product_uom_qty': 1,
            'quantity_done': 1,
            'product_uom': first_lot.product_id.uom_id.id,
            'company_id': self.env.company.id,
        }
        move_adjustment_id1 = StockMove.create(vals_move_adjustment)
        vals_adjustment_move2 = {
            'product_id': self.second_quant_id.product_id.id,
            'name': self.second_quant_id.product_id.display_name,
            'location_id': self.second_quant_id.location_id.id,
            'location_dest_id': inventory_loss_location.id,
            'lot_ids': [(4, second_lot.ids)],
            'product_uom_qty': 1,
            'quantity_done': 1,
            'product_uom': second_lot.product_id.uom_id.id,
            'company_id': self.env.company.id,
        }
        move_adjustment_id2 = StockMove.create(vals_adjustment_move2)
        move_adjustment_id1._action_done()
        move_adjustment_id2._action_done()
        ####### SEGUNDO MOVIMIENTO #############
        vals_move1 = {
            'product_id': self.first_quant_id.product_id.id,
            'name': self.first_quant_id.product_id.display_name,
            'location_id': inventory_loss_location.id,
            'location_dest_id': self.first_quant_id.location_id.id,
            'lot_ids': [(4, second_lot.ids)],
            'product_uom_qty': 1,
            'quantity_done': 1,
            'product_uom': second_lot.product_id.uom_id.id,
            'company_id': self.env.company.id,
            # 'state': 'done'
        }
        move_id1 = StockMove.create(vals_move1)
        vals_move2 = {
            'product_id': self.second_quant_id.product_id.id,
            'name': self.second_quant_id.product_id.display_name,
            'location_id': inventory_loss_location.id,
            'location_dest_id': self.second_quant_id.location_id.id,
            'lot_ids': [(4, first_lot.ids)],
            'product_uom_qty': 1,
            'quantity_done': 1,
            'product_uom': first_lot.product_id.uom_id.id,
            'company_id': self.env.company.id,
        }
        move_id2 = StockMove.create(vals_move2)

        move_id1._action_done()
        move_id2._action_done()
