from odoo import api, fields, models
from odoo.exceptions import UserError


class AddSerialNumber(models.TransientModel):
    _name = 'add.serial.number'

    @api.model
    def default_get(self, default_fields):
        res = super(AddSerialNumber, self).default_get(default_fields)
        active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        res['picking_id'] = active_id.id
        return res

    picking_id = fields.Many2one('stock.picking', 'Picking')
    prduct_lots_ids = fields.One2many(
        string='Lote Origen',
        comodel_name='add.serial.number.line',
        inverse_name='add_lot_id',
    )

    def action_add_lot(self):
        StockMove = self.env['stock.move']
        StockMoveLine = self.env['stock.move.line']
        product_move_ids = self.picking_id.move_ids_without_package.mapped('product_id')
        products = []
        if not self.prduct_lots_ids:
            raise UserError('Debe incluir al menos una linea para procesar la solicitud')
        else:
            for line in self.prduct_lots_ids:
                if line.product_id.id in product_move_ids.ids:
                    move_ids = self.picking_id.move_ids_without_package.filtered(lambda l: l.product_id.id == line.product_id.id)
                    if len(move_ids) == 1:
                        if move_ids.product_uom_qty == move_ids.reserved_availability:
                            products.append({
                                'product_name': line.product_id.display_name,
                                'lot_name': line.lot_id.name if line.lot_id else '',
                            })
                            #if line.product_id.tracking == 'serial':
                            #move_id = self.picking_id.move_ids_without_package.filtered(lambda s: s.product_id.id == line.product_id.id)
                            vals = {
                                'picking_id': line.picking_id.id,
                                'move_id': move_ids.id,
                                'product_id': line.product_id.id,
                                'location_id': line.picking_id.location_id.id,
                                'location_dest_id': line.picking_id.location_dest_id.id,
                                'owner_id': line.picking_id.owner_id.id if line.picking_id.owner_id else False,
                                'lot_id': line.lot_id.id if line.lot_id else False,
                                'product_uom_qty': 1.0,
                                'qty_done': 1.0,
                                'product_uom_id': line.product_id.uom_id.id,
                                'state': 'assigned'
                            }
                            move_line = StockMoveLine.create(vals)
                            if move_line:
                                line.stock_quant_id.write({
                                    'reserved_quantity': 1.0
                                })
                                qty = move_ids.product_uom_qty + 1.0
                                move_ids.update({
                                    'product_uom_qty': qty
                                })
                        if move_ids.reserved_availability < move_ids.product_uom_qty:
                            vals = {
                                'picking_id': line.picking_id.id,
                                'move_id': move_ids.id,
                                'product_id': line.product_id.id,
                                'location_id': line.picking_id.location_id.id,
                                'location_dest_id': line.picking_id.location_dest_id.id,
                                'owner_id': line.picking_id.owner_id.id if line.picking_id.owner_id else False,
                                'lot_id': line.lot_id.id if line.lot_id else False,
                                'product_uom_qty': 1.0,
                                'qty_done': 1.0,
                                'product_uom_id': line.product_id.uom_id.id,
                                'state': 'assigned'
                            }
                            move_line = StockMoveLine.create(vals)
                            if move_line:
                                line.stock_quant_id.write({
                                    'reserved_quantity': 1.0
                                })

                    elif len(move_ids) > 1:
                        add = False
                        for move_id in move_ids:
                            if move_id.reserved_availability < move_id.product_uom_qty:
                                sm_id = move_id
                                vals = {
                                    'picking_id': line.picking_id.id,
                                    'move_id': move_id.id,
                                    'product_id': line.product_id.id,
                                    'location_id': line.picking_id.location_id.id,
                                    'location_dest_id': line.picking_id.location_dest_id.id,
                                    'owner_id': line.picking_id.owner_id.id if line.picking_id.owner_id else False,
                                    'lot_id': line.lot_id.id if line.lot_id else False,
                                    'product_uom_qty': 1.0,
                                    'qty_done': 1.0,
                                    'product_uom_id': line.product_id.uom_id.id,
                                    'state': 'assigned'
                                }
                                move_line = StockMoveLine.create(vals)
                                if move_line:
                                    line.stock_quant_id.write({
                                        'reserved_quantity': 1.0
                                    })
                                    sm_id.state = 'assigned'
                                add = False
                                break
                            elif move_id.product_uom_qty == move_id.reserved_availability:
                                sm_id = move_id
                                add = True
                        if add:
                            if move_id:
                                vals = {
                                    'picking_id': line.picking_id.id,
                                    'move_id': sm_id.id,
                                    'product_id': line.product_id.id,
                                    'location_id': line.picking_id.location_id.id,
                                    'location_dest_id': line.picking_id.location_dest_id.id,
                                    'owner_id': line.picking_id.owner_id.id if line.picking_id.owner_id else False,
                                    'lot_id': line.lot_id.id if line.lot_id else False,
                                    'product_uom_qty': 1.0,
                                    'qty_done': 1.0,
                                    'product_uom_id': line.product_id.uom_id.id,
                                }
                                StockMoveLine.create(vals)
                                line.stock_quant_id.write({
                                    'reserved_quantity': 1.0
                                })
                                sm_id.product_uom_qty += 1.0
                                sm_id.state = 'assigned'
                else:
                    products.append({
                        'product_name': line.product_id.display_name,
                        'lot_name': line.lot_id.name if line.lot_id else '',
                    })
                    vals_move = {
                        'picking_id': line.picking_id.id,
                        'product_id': line.product_id.id,
                        'name': line.product_id.display_name,
                        'location_id': line.picking_id.location_id.id,
                        'location_dest_id': line.picking_id.location_dest_id.id,
                        'product_uom_qty': 1.0,
                        'product_uom': line.product_id.uom_id.id,
                    }
                    move_id = StockMove.create(vals_move)
                    if move_id:
                        vals = {
                            'picking_id': line.picking_id.id,
                            'move_id': move_id.id,
                            'product_id': line.product_id.id,
                            'location_id': line.picking_id.location_id.id,
                            'location_dest_id': line.picking_id.location_dest_id.id,
                            'owner_id': line.picking_id.owner_id.id if line.picking_id.owner_id else False,
                            'lot_id': line.lot_id.id if line.lot_id else False,
                            'product_uom_qty': 1.0,
                            'qty_done': 1.0,
                            'product_uom_id': line.product_id.uom_id.id,
                        }
                        StockMoveLine.create(vals)
                        line.stock_quant_id.write({
                            'reserved_quantity': 1.0
                        })
            msg = f"""
                <strong>Inclusion de Lotes<strong>
                <br />
            """
            for product in products:
                msg += f"""
                    <b>Producto: {product['product_name']} - Lote: {product['lot_name']}</b>
                    <br />
                """
            self.picking_id.message_post(body=msg)
            #self.picking_id.state = 'assigned'


class AddSerialNumberLine(models.TransientModel):
    _name = 'add.serial.number.line'

    def default_picking_id(self):
        picking_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        return picking_id

    add_lot_id = fields.Many2one('add.serial.number')
    picking_id = fields.Many2one('stock.picking', 'Picking', default=default_picking_id)
    product_id = fields.Many2one('product.product', string='Producto')
    lot_id = fields.Many2one('stock.production.lot', 'Lote actual')
    lots_ids_domain = fields.Many2many('stock.production.lot', string='dominio')
    stock_quant_id = fields.Many2one('stock.quant', string='Quant')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            states = self.picking_id.location_dest_id.stage_ids.ids if self.picking_id.location_dest_id.stage_ids \
                else self.picking_id.location_dest_id.warehouse_id.stage_ids.ids \
                if self.picking_id.location_dest_id.warehouse_id.stage_ids else False
            stock_quants = self.env['stock.quant'].search([('location_id', '=', self.picking_id.location_id.id),
                                                           ('product_id', '=', self.product_id.id)])
            lots = []
            for sq in stock_quants:
                if sq.available_quantity > 0.0 and sq.lot_id:
                    if states:
                        if sq.lot_id.stage_id.id in states:
                            lots.append(sq.lot_id.id)
            self.lots_ids_domain = lots if lots else False

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        StockQuant = self.env['stock.quant']
        if self.lot_id:
            quant = StockQuant.search([('product_id', '=', self.product_id.id),
                                       ('lot_id', '=', self.lot_id.id),
                                       ('location_id', '=', self.picking_id.location_id.id)])
            if quant:
                self.stock_quant_id = quant.id