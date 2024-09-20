from odoo import api, fields, models

class ExchangeSerialNumber(models.TransientModel):
    _name = 'exchange.serial.number'
    
    @api.model
    def default_get(self, default_fields):
        #res = super(ExchangeSerialNumber, self).default_get(default_fields)
        res = {}
        active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        lines = []
        if active_id.move_line_ids_without_package:
            for line in active_id.move_line_ids_without_package:
                lots_per_product = active_id.move_line_ids_without_package.filtered(lambda l: l.product_id.id == line.product_id.id and l.lot_id.stage_id.code not in ['domi', 'xrefact']).mapped('lot_id')
                if line.product_id.tracking == 'serial':
                    lot_ids = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id),
                         ('id', 'not in', lots_per_product.ids)])
                    stock_quant = self.env['stock.quant'].search([('location_id', '=', line.location_id.id),
                                                                ('lot_id', 'in', lot_ids.ids), ('available_quantity', '>', 0)]) if lot_ids else False
                    if active_id.location_dest_id.stage_ids:
                        stage_ids = active_id.location_dest_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_ids.ids) if stock_quant else False
                    elif active_id.location_dest_id.warehouse_id.stage_ids:
                        stage_wh_ids = active_id.location_dest_id.warehouse_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_wh_ids.ids) if stock_quant else False
                    lots = stock_quant.mapped('lot_id') if stock_quant else False
                    lines.append([0, 0, {
                        'product_id': line.product_id.id,
                        'origin_picking_id': line.picking_id.id,
                        'move_line_origin_id': line.id,
                        'current_lot_id': line.lot_id.id,
                        'lots_ids_domain': lots.ids if lots else False
                    }])
            res['prduct_lots_ids'] = lines
        return res
    
    prduct_lots_ids = fields.One2many(
        string='Lote Origen',
        comodel_name='exchange.serial.number.line',
        inverse_name='exchange_id',
    )
    
    def action_lines_lot(self):
        for line in self.prduct_lots_ids:
            if line.new_lot_id:
                if line.move_line_dest_id:
                    line.move_line_dest_id.product_uom_qty = 0
                    line.move_line_dest_id.write({
                        'lot_id': line.current_lot_id.id,
                        'product_uom_qty': 1,
                        'state': 'assigned'
                    })
                    line.move_line_origin_id.write({
                        'lot_id':line.new_lot_id.id,
                        'product_uom_qty': 1,
                        'state': 'assigned'
                    })
                    msg_origin = f"""
                        <strong>Intercambio de Lotes<strong>
                        <br />
                        <b>Producto: {line.move_line_origin_id.product_id.name} - Lote: {line.current_lot_id.name} ----> {line.new_lot_id.name}</b>
                        <br />
                    """
                    msg_dest = f"""
                        <strong>Intercambio de Lotes<strong>
                        <br />
                        <b>Producto: {line.move_line_dest_id.product_id.name} - Lote: {line.new_lot_id.name} ----> {line.current_lot_id.name}</b>
                        <br />
                    """
                    line.origin_picking_id.message_post(body=msg_origin)
                    line.dest_picking_id.message_post(body=msg_dest)
                else:
                    msg_origin = f"""
                        <strong>Intercambio de Lotes<strong>
                        <br />
                        <b>Producto: {line.move_line_origin_id.product_id.name} - Lote: {line.current_lot_id.name} ----> {line.new_lot_id.name}</b>
                        <br />
                    """
                    line.move_line_origin_id.write({
                        'lot_id': line.new_lot_id.id,
                        'product_uom_qty': 1,
                        'state': 'assigned'
                    })
                    line.origin_picking_id.message_post(body=msg_origin)

    @api.onchange('prduct_lots_ids')
    def onchange_method(self):
        active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        if self.prduct_lots_ids:
            lines = self.prduct_lots_ids
            for line in self.prduct_lots_ids:
                lot_ids = []
                lots_per_product = active_id.move_line_ids_without_package.filtered(lambda l: l.product_id.id == line.product_id.id and l.lot_id).mapped('lot_id')
                stage_ids = active_id.location_dest_id.stage_ids.ids if active_id.location_dest_id.stage_ids else active_id.location_dest_id.warehouse_id.stage_ids.ids if active_id.location_dest_id.warehouse_id.stage_ids else False
                lot_picking_ids = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id), ('id', 'not in', lots_per_product.ids), ('stage_id', 'in', stage_ids), ('current_location_id', '=', active_id.location_id.id)])
                lot_ids = [lot.id for lot in lot_picking_ids]
                lots = line.lots_ids_domain.ids + lot_ids
                lots_news = [lot.new_lot_id.id for lot in lines]
                for i, lot in enumerate(lots):
                    if lot in lots_news:
                        lots.pop(i)
                for i, lp in enumerate(lots):
                    domain = [('lot_id', '=', lp), ('picking_id', '!=', active_id.id), ('picking_id', '!=', False),
                              ('state', 'in', ['ready', 'assigned', 'check'])]
                    move_line = self.env['stock.move.line'].search(domain)
                    if move_line:
                        dest_stage_ids = move_line.picking_id.location_dest_id.stage_ids.ids if move_line.picking_id.location_dest_id.stage_ids else move_line.picking_id.location_dest_id.warehouse_id.stage_ids.ids if move_line.picking_id.location_dest_id.warehouse_id.stage_ids else False
                        if dest_stage_ids:
                            if line.current_lot_id.stage_id.id not in dest_stage_ids:
                                lots.pop(i)
                for l in self.prduct_lots_ids:
                    l.lots_ids_domain = lots

class ExchangeSerialNumberLine(models.TransientModel):
    _name = 'exchange.serial.number.line'
    
    exchange_id = fields.Many2one('exchange.serial.number')
    product_id = fields.Many2one('product.product')
    origin_picking_id = fields.Many2one('stock.picking', 'Transferencia Origen')
    dest_picking_id = fields.Many2one('stock.picking', 'Transferencia Actual')
    move_line_origin_id = fields.Many2one('stock.move.line', 'Linea Origen')
    move_line_dest_id = fields.Many2one('stock.move.line', 'Linea Actual')
    exchange_lot_id = fields.Many2one('stock.production.lot', 'Lote')
    current_lot_id = fields.Many2one('stock.production.lot', 'Lote actual')
    new_lot_id = fields.Many2one('stock.production.lot', 'Lote nuevo')
    lots_ids_domain = fields.Many2many('stock.production.lot', string='dominio')

    # @api.model
    # def create(self, values):
    #     print(values)
    #     self.onchange_current_lot_id()
    #     return super(ExchangeSerialNumberLine, self).create(values)

    # @api.onchange('current_lot_id')
    # def onchange_current_lot_id(self):
    #     ids = False
    #     if self.current_lot_id:
    #         lot_ids = self.env['stock.production.lot'].search([('product_id', '=', self.move_line_origin_id.product_id.id),
    #                                                            ('id', '!=', self.current_lot_id.id)])
    #         stock_quant = self.env['stock.quant'].search([('location_id', '=', self.move_line_origin_id.location_id.id),
    #                                                       ('lot_id', 'in', lot_ids.ids)])
    #         ids = stock_quant.mapped('lot_id') if stock_quant else False
    #     return {'domain': {'new_lot_id': [('id', 'in', ids)]}}

    @api.onchange('new_lot_id')
    def _onchange_new_lot_id(self):
        if self.new_lot_id:
            active_id = self._context.get('active_id', False)
            domain = [('lot_id', '=', self.new_lot_id.id), ('state', 'in', ['assigned', 'confirmed', 'ready'])]
            move_line = self.env['stock.move.line'].search(domain)
            if move_line:
                self.write({
                    'dest_picking_id': move_line.picking_id.id,
                    'move_line_dest_id': move_line.id,
                    'exchange_lot_id': move_line.lot_id.id
                })
        else:
            self.write({
                'dest_picking_id': False,
                'move_line_dest_id': False,
                'exchange_lot_id': False
            })
    
    
    def get_exchange_line_ata(self):
        self.ensure_one()
        return {
            'origin_picking_id': self.origin_picking_id.id,
            'dest_picking_id': self.dest_picking_id.id,
            'move_line_origin_id': self.move_line_origin_id.id,
            'move_line_dest_id': self.move_line_dest_id.id,
            'exchange_lot_id': self.exchange_lot_id.id,
            'current_lot_id': self.current_lot_id.id,
            'new_lot_id': self.new_lot_id.id,
        }