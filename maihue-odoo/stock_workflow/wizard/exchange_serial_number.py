from odoo import api, fields, models

class ExchangeSerialNumber(models.TransientModel):
    _inherit = 'exchange.serial.number'

    @api.model
    def default_get(self, default_fields):
        active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        lines = []
        res = {}
        if active_id.type_transfer == 'normal' and active_id.move_line_ids_without_package:
            for line in active_id.move_line_ids_without_package:
                lots_per_product = active_id.move_line_ids_without_package.filtered(
                    lambda l: l.product_id.id == line.product_id.id and l.lot_id.stage_id.code not in ['domi',
                                                                                                       'xrefact']).mapped(
                    'lot_id')
                if line.product_id.tracking == 'serial':
                    lot_ids = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id),
                                                                       ('id', 'not in', lots_per_product.ids), ('current_location_id', '=', line.location_id.id)])
                    if active_id.agreement_line_id and not active_id.agreement_line_id.admin_line_id:
                        lot_ids = lot_ids.filtered(lambda x: not x.franchisee_id)
                    if active_id.user_id.is_franchisee:
                        lot_ids = lot_ids.filtered(lambda x: x.franchisee_id.id == active_id.user_id.id)
                    stock_quant = self.env['stock.quant'].search([('lot_id', 'in', lot_ids.ids)]) if lot_ids else False
                    if active_id.location_id.stage_ids:
                        stage_ids = active_id.location_dest_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_ids.ids and l.lot_id.current_location_id.id == line.location_id.id) if stock_quant else False
                    elif active_id.location_id.warehouse_id.stage_ids:
                        stage_wh_ids = active_id.location_dest_id.warehouse_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_wh_ids.ids and l.lot_id.current_location_id.id == line.location_id.id) if stock_quant else False


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
        elif active_id.type_transfer == 'franchisee' and active_id.move_line_ids_without_package:
            for line in active_id.move_line_ids_without_package:
                lots_per_product = active_id.move_line_ids_without_package.filtered(
                    lambda l: l.product_id.id == line.product_id.id and l.lot_id.stage_id.code not in ['domi',
                                                                                                       'xrefact']).mapped(
                    'lot_id')
                if line.product_id.tracking == 'serial':
                    lot_ids = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id),
                                                                       ('id', 'not in', lots_per_product.ids), ('current_location_id', '=', line.location_id.id)])
                    stock_quant = self.env['stock.quant'].search([('lot_id', 'in', lot_ids.ids)]) if lot_ids else False
                    if active_id.location_id.stage_ids:
                        stage_ids = active_id.location_dest_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_ids.ids and l.lot_id.current_location_id.id == line.location_id.id) if stock_quant else False
                    elif active_id.location_id.warehouse_id.stage_ids:
                        stage_wh_ids = active_id.location_dest_id.warehouse_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_wh_ids.ids and l.lot_id.current_location_id.id == line.location_id.id) if stock_quant else False
                    if active_id.user_id.is_franchisee:
                        stock_quant = stock_quant.filtered(lambda x: not x.lot_id.franchisee_id)
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
        elif active_id.type_transfer == 'change_franchisee' and active_id.move_line_ids_without_package:
            for line in active_id.move_line_ids_without_package:
                lots_per_product = active_id.move_line_ids_without_package.filtered(
                    lambda l: l.product_id.id == line.product_id.id and l.lot_id.stage_id.code not in ['domi',
                                                                                                       'xrefact']).mapped(
                    'lot_id')
                if line.product_id.tracking == 'serial':
                    lot_ids = self.env['stock.production.lot'].search([('product_id', '=', line.product_id.id),
                                                                       ('id', 'not in', lots_per_product.ids), ('current_location_id', '=', line.location_id.id)])
                    stock_quant = self.env['stock.quant'].search([('lot_id', 'in', lot_ids.ids)]) if lot_ids else False
                    if active_id.location_id.stage_ids:
                        stage_ids = active_id.location_dest_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_ids.ids and l.lot_id.franchisee_id.id == active_id.source_franchisee_id.id and l.lot_id.current_location_id.id == line.location_id.id) if stock_quant else False
                    elif active_id.location_id.warehouse_id.stage_ids:
                        stage_wh_ids = active_id.location_dest_id.warehouse_id.stage_ids
                        stock_quant = stock_quant.filtered(lambda l: l.lot_id.stage_id.id in stage_wh_ids.ids and l.lot_id.franchisee_id.id == active_id.source_franchisee_id.id and l.lot_id.current_location_id.id == line.location_id.id) if stock_quant else False
                    if active_id.user_id.is_franchisee:
                        stock_quant = stock_quant.filtered(lambda x: x.lot_id.franchisee_id.id != active_id.user_id.id and x.lot_id.franchisee_id)
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
        else:
            return super(ExchangeSerialNumber, self).default_get(default_fields)
        # active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        # if active_id.is_picking_franchisee:
        #     if 'prduct_lots_ids' in res:
        #         for index, line in enumerate(res['prduct_lots_ids']):
        #             lots_ids_domain = self.env['stock.production.lot'].browse(line[2]['lots_ids_domain'])
        #             res['prduct_lots_ids'][index][2]['lots_ids_domain'] = lots_ids_domain.filtered(lambda s: s.franchisee_id.id != active_id.franchisee_id.id).ids
        # return res

    @api.onchange('prduct_lots_ids')
    def onchange_method(self):
        active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        if active_id.type_transfer == 'normal' and active_id.agreement_line_id:
            if self.prduct_lots_ids:
                lines = self.prduct_lots_ids
                for line in self.prduct_lots_ids:
                    lot_ids = []
                    lots_per_product = active_id.move_line_ids_without_package.filtered(
                        lambda l: l.product_id.id == line.product_id.id and l.lot_id).mapped('lot_id')
                    stage_ids = active_id.location_dest_id.stage_ids.ids if active_id.location_dest_id.stage_ids else active_id.location_dest_id.warehouse_id.stage_ids.ids if active_id.location_dest_id.warehouse_id.stage_ids else False
                    lot_picking_ids = self.env['stock.production.lot'].search(
                        [('product_id', '=', line.product_id.id), ('id', 'not in', lots_per_product.ids),
                         ('stage_id', 'in', stage_ids), ('current_location_id', '=', active_id.location_id.id)])
                    if active_id.agreement_line_id and active_id.agreement_line_id.admin_line_id and active_id.agreement_line_id.admin_line_id.is_franchisee:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: l.franchisee_id.id == active_id.agreement_line_id.admin_line_id.id)
                    elif active_id.agreement_line_id and active_id.agreement_line_id.admin_line_id and active_id.agreement_line_id.admin_line_id.is_admin:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: not l.franchisee_id)
                    elif active_id.agreement_line_id and not active_id.agreement_line_id.admin_line_id:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: not l.franchisee_id)
                    elif not active_id.agreement_line_id and active_id.user_id.is_franchisee:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: l.franchisee_id.id == active_id.user_id.id)
                    # else:
                    #     lot_picking_ids = lot_picking_ids.filtered(lambda l: l.franchisee_id == False)
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
        elif active_id.type_transfer == 'normal' and not active_id.agreement_line_id:
            if self.prduct_lots_ids:
                lines = self.prduct_lots_ids
                for line in self.prduct_lots_ids:
                    lot_ids = []
                    lots_per_product = active_id.move_line_ids_without_package.filtered(
                        lambda l: l.product_id.id == line.product_id.id and l.lot_id).mapped('lot_id')
                    stage_ids = active_id.location_dest_id.stage_ids.ids if active_id.location_dest_id.stage_ids else active_id.location_dest_id.warehouse_id.stage_ids.ids if active_id.location_dest_id.warehouse_id.stage_ids else False
                    lot_picking_ids = self.env['stock.production.lot'].search(
                        [('product_id', '=', line.product_id.id), ('id', 'not in', lots_per_product.ids),
                         ('stage_id', 'in', stage_ids), ('current_location_id', '=', active_id.location_id.id)])
                    if active_id.user_id.is_franchisee:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: l.franchisee_id.id == active_id.user_id.id)
                    # else:
                    #     lot_picking_ids = lot_picking_ids.filtered(lambda l: l.franchisee_id == False)
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
        elif active_id.type_transfer == 'franchisee':
            if self.prduct_lots_ids:
                lines = self.prduct_lots_ids
                for line in self.prduct_lots_ids:
                    lot_ids = []
                    lots_per_product = active_id.move_line_ids_without_package.filtered(
                        lambda l: l.product_id.id == line.product_id.id and l.lot_id).mapped('lot_id')
                    stage_ids = active_id.location_dest_id.stage_ids.ids if active_id.location_dest_id.stage_ids else active_id.location_dest_id.warehouse_id.stage_ids.ids if active_id.location_dest_id.warehouse_id.stage_ids else False
                    lot_picking_ids = self.env['stock.production.lot'].search(
                        [('product_id', '=', line.product_id.id), ('id', 'not in', lots_per_product.ids),
                         ('stage_id', 'in', stage_ids), ('franchisee_id', '!=', active_id.franchisee_id.id), ('current_location_id', '=', active_id.location_id.id)])
                    if active_id.user_id.is_franchisee:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: not l.franchisee_id)
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
        elif active_id.type_transfer == 'change_franchisee':
            if self.prduct_lots_ids:
                lines = self.prduct_lots_ids
                for line in self.prduct_lots_ids:
                    lot_ids = []
                    lots_per_product = active_id.move_line_ids_without_package.filtered(
                        lambda l: l.product_id.id == line.product_id.id and l.lot_id).mapped('lot_id')
                    stage_ids = active_id.location_dest_id.stage_ids.ids if active_id.location_dest_id.stage_ids else active_id.location_dest_id.warehouse_id.stage_ids.ids if active_id.location_dest_id.warehouse_id.stage_ids else False
                    lot_picking_ids = self.env['stock.production.lot'].search(
                        [('product_id', '=', line.product_id.id), ('id', 'not in', lots_per_product.ids),
                         ('stage_id', 'in', stage_ids), ('franchisee_id', '=', active_id.source_franchisee_id.id), ('current_location_id', '=', active_id.location_id.id)])
                    if active_id.user_id.is_franchisee:
                        lot_picking_ids = lot_picking_ids.filtered(lambda l: l.franchisee_id.id != active_id.user_id.id and l.franchisee_id)
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
        else:
            return super(ExchangeSerialNumber, self).onchange_method()

    def action_lines_lot(self):
        StockQuant = self.env['stock.quant']
        for line in self.prduct_lots_ids:
            if line.new_lot_id:
                if line.move_line_dest_id:
                    state = 'assigned' if line.dest_picking_id.state == 'assigned' else 'check'
                    # line.move_line_dest_id.write({
                    #     'lot_id': line.current_lot_id.id,
                    #     'product_uom_qty': 1,
                    #     'qty_done': 0,
                    # })
                    francheesi_id = line.current_lot_id.franchisee_id.id if  line.current_lot_id.franchisee_id else 'null'
                    self.env.cr.execute("""
                        UPDATE stock_move_line SET lot_id = %s, product_uom_qty = 1, qty_done = 0, franchisee_id = %s WHERE id = %s
                    """ % (line.current_lot_id.id, francheesi_id, line.move_line_dest_id.id))
                    # line.move_line_origin_id.write({
                    #     'lot_id':line.new_lot_id.id,
                    #     'product_uom_qty': 1,
                    #     'qty_done': 0,
                    # })
                    francheesi_id = line.new_lot_id.franchisee_id.id if line.new_lot_id.franchisee_id else 'null'
                    self.env.cr.execute("""
                        UPDATE stock_move_line SET lot_id = %s, product_uom_qty = 1, qty_done = 0, franchisee_id = %s WHERE id = %s
                    """ % (line.new_lot_id.id, francheesi_id, line.move_line_origin_id.id))
                    sq_origin = StockQuant.search([('lot_id', '=', line.new_lot_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    sq_dest = StockQuant.search([('lot_id', '=', line.current_lot_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if sq_origin and sq_dest:
                        sq_dest.reserved_quantity = 1
                        sq_origin.reserved_quantity = 1
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
                    #line.move_line_origin_id.state = 'assigned'
                    #line.move_line_dest_id.state = 'assigned'
                    line.dest_picking_id.state = state
                else:
                    msg_origin = f"""
                        <strong>Intercambio de Lotes<strong>
                        <br />
                        <b>Producto: {line.move_line_origin_id.product_id.name} - Lote: {line.current_lot_id.name} ----> {line.new_lot_id.name}</b>
                        <br />
                    """
                    # line.move_line_origin_id.update({
                    #     'lot_id': line.new_lot_id.id,
                    #     'product_uom_qty': 1,
                    #     'qty_done': 0,
                    #     'state': 'assigned'
                    # })
                    francheesi_id = line.new_lot_id.franchisee_id.id if line.new_lot_id.franchisee_id else 'null'
                    self.env.cr.execute("""
                        UPDATE stock_move_line SET lot_id = %s, product_uom_qty = 1, qty_done = 0, franchisee_id = %s WHERE id = %s
                    """ % (line.new_lot_id.id, francheesi_id, line.move_line_origin_id.id))
                    sq_origin = StockQuant.search([('lot_id', '=', line.new_lot_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    sq_dest = StockQuant.search([('lot_id', '=', line.current_lot_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if sq_origin and sq_dest:
                        sq_dest.reserved_quantity = 0
                        sq_origin.reserved_quantity = 1
                    line.origin_picking_id.message_post(body=msg_origin)

    @api.onchange('new_lot_id')
    def _onchange_new_lot_id(self):
        if self.new_lot_id:
            active_id = self._context.get('active_id', False)
            domain = [('lot_id', '=', self.new_lot_id.id)]
            move_line = self.env['stock.move.line'].search(domain)
            if move_line:
                self.write({
                    'dest_picking_id': move_line.picking_id.id,
                    'move_line_dest_id': move_line.id,
                    'exchange_lot_id': move_line.lot_id.id
                })