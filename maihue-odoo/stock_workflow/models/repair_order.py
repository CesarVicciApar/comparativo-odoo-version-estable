from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime

class RepairOrder(models.Model):
    _inherit = 'repair.order'
    
    picking_id = fields.Many2one('stock.picking', string='Transferencia a Taller')
    state_transfer = fields.Selection(related="picking_id.state")
    repair_type = fields.Selection([
        ('repair', 'Orden de Reparacion'),
        ('replacement', 'Orden de Reposicion de piezas'),
        ('dismantling', 'Orden de Desmantelacion'),
        ('change', 'Cambio de Domicilio')
    ], default='repair', tracking=True)
    state = fields.Selection([
        ('predraft', 'Borrador'),
        ('draft', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('ready', 'Ready to Repair'),
        ('under_repair', 'Under Repair'),
        ('2binvoiced', 'To be Invoiced'),
        ('done', 'Repaired'),
        ('cancel', 'Cancelled')], string='Status',
        copy=False, default='predraft', readonly=True, tracking=True,
        help="* The \'Draft\' status is used when a user is encoding a new and unconfirmed repair order.\n"
             "* The \'Confirmed\' status is used when a user confirms the repair order.\n"
             "* The \'Ready to Repair\' status is used to start to repairing, user can start repairing only after repair order is confirmed.\n"
             "* The \'Under Repair\' status is used when the repair is ongoing.\n"
             "* The \'To be Invoiced\' status is used to generate the invoice before or after repairing done.\n"
             "* The \'Done\' status is set when repairing is completed.\n"
             "* The \'Cancelled\' status is used when user cancel repair order.")
    location_id = fields.Many2one(
        'stock.location', 'Location',
        index=True, readonly=True, required=True, check_company=True,
        help="This is the location where the product to repair is located.",
        states={'predraft': [('readonly', False)], 'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})
    location_source_id = fields.Many2one(
        'stock.location', 'Ubicación Origen',
        index=True, readonly=True, required=True, check_company=True,
        help="This is the location where the product to repair is located.",
        states={'predraft': [('readonly', False)], 'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})
    product_id = fields.Many2one(
        'product.product', string='Product to Repair',
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        readonly=True, required=True, states={'predraft': [('readonly', False)], 'draft': [('readonly', False)]}, check_company=True)
    product_uom = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        readonly=True, required=True, states={'predraft': [('readonly', False)], 'draft': [('readonly', False)]},
        domain="[('category_id', '=', product_uom_category_id)]")
    origin = fields.Char('Documento Origen')
    missing_pieces = fields.Boolean('Faltan piezas', compute='_compute_missing_pieces', store=True)
    state_equipment = fields.Selection(string='Estado uso equipo', selection=[('outdated', 'Obsoleto'),
                                                                  ('out_service', 'Fuera de Servicio')])
    repair_order_id = fields.Many2one('repair.order', 'Order Repair')
    missing_pieces_ids = fields.One2many('repair.missing.pieces', inverse_name='repair_id', string='Piezas Faltantes')
    notes = fields.Text(string="Notes")
    final_date = fields.Date(string="Fecha final")
    start_date = fields.Date(string="Fecha de inicio")
    schedule_date = fields.Date("Scheduled Date", default=datetime.today())
    start = fields.Boolean(string="Inicio")
    final = fields.Boolean(string="Final")

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            stock_quant = self.lot_id.quant_ids.filtered(lambda s: s.location_id.usage == 'internal')
            location_source = False
            if stock_quant:
                if len(stock_quant) == 1:
                    location_source = stock_quant.location_id
                else:
                    location_source = stock_quant[0].location_id
            if location_source:
                self.location_source_id = location_source.id
            else:
                raise ValidationError('No hay una ubicacion interna establecida en este equipo')
            missing_pieces = self.lot_id.missing_pieces_ids
            if missing_pieces:
                lines = []
                for line_piece in missing_pieces:
                    vals = {
                        'product_id': self.product_id.id,
                        'name': self.product_id.display_name + ' ' + self.lot_id.name,
                        'missing_piece_id': line_piece.id
                    }
                    lines.append([0, 0, vals])
                self.missing_pieces_ids = lines

    @api.depends('missing_pieces_ids')
    def _compute_missing_pieces(self):
        for record in self:
            missing = False
            if record.missing_pieces_ids:
                for piece in record.missing_pieces_ids:
                    if not piece.is_installed:
                        missing = True
            record.missing_pieces = missing

    # @api.onchange('missing_pieces_ids.is_installed')
    # def _onchange_missing_pieces(self):
    #     if self.missing_pieces_ids:
    #         for line in self.missing_pieces_ids:
    #             if line.is_installed and line.missing_piece_id:
    #                 line.missing_piece_id.unlink()

    def validate_missing_pieces(self):
        missing_pieces = []
        add = True
        for line in self.operations.filtered(lambda s: s.type == 'remove'):
            if missing_pieces:
                for mp in missing_pieces:
                    if mp['product_id'] == line.product_id.id:
                        mp['quantity'] += line.product_uom_qty
                        add = False
                        break
                    else:
                        add = True
            if add:
                missing_pieces.append({
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'qty_done': 0
                })
        for piece in self.missing_pieces_ids:
            if missing_pieces:
                for mp in missing_pieces:
                    if mp['product_id'] == piece.product_id.id:
                        mp['quantity'] += piece.quantity
                        add = False
                        break
                    else:
                        add = True
            if add:
                missing_pieces.append({
                    'product_id': piece.product_id.id,
                    'quantity': piece.quantity,
                    'qty_done': 0
                })
        return missing_pieces


    @api.onchange('operations', 'operations.type', 'operations.product_id', 'operations.product_uom_qty')
    def onchange_operation_verify_mp(self):
        missing_pieces = self.validate_missing_pieces()
        if self.operations:
            for line in self.operations:
                if line.type == 'add':
                    find_piece = False
                    for mp in missing_pieces:
                        if line.product_id.id == mp['product_id']:
                            diff = mp['quantity'] - mp['qty_done']
                            if diff > 0 and line.product_uom_qty <= diff:
                                mp['qty_done'] += line.product_uom_qty
                                find_piece =True
                                break
                            elif diff <= 0:
                                raise UserError('Esta instalando mas piezas que las faltantes del equipo')
                    if not find_piece:
                        raise UserError('Esta instalando piezas que no le faltan al equipo')



    def verify_out_config_user_location_warehouse(self, location):
        warehouse = location.warehouse_id
        auth = False
        config = True
        if location.output_management_ids:
            if self.env.user.id in location.output_management_ids.ids:
                auth = True
        elif not location.output_management_ids and warehouse.output_management_ids:
            if self.env.user.id in warehouse.output_management_ids.ids:
                auth = True
        elif not location.output_management_ids and not warehouse.output_management_ids:
            config = False
        else:
            auth = False
        return auth, config

    def verify_in_config_user_location_warehouse(self, location):
        warehouse = location.warehouse_id
        auth = False
        config = True
        if location.input_management_ids:
            if self.env.user.id in location.input_management_ids.ids:
                auth = True
        elif not location.input_management_ids and warehouse.input_management_ids:
            if self.env.user.id in warehouse.input_management_ids.ids:
                auth = True
        elif not location.input_management_ids and not warehouse.input_management_ids:
            config = False
        else:
            auth = False
        return auth, config

    def action_generate_picking(self):
        StockQuant = self.env['stock.quant']
        for record in self:
            if record.location_id.id != record.location_source_id.id:
                auth_user, config_user = record.verify_out_config_user_location_warehouse(record.location_source_id)
                if not config_user:
                    raise UserError('No se han configurado los usuarios permitidos a entregar desde %s, revisar permisos con el administrador' % record.location_source_id.display_name)
                if config_user and not auth_user:
                    raise UserError('Usted no tiene autorización para realizar esta acción, revisar permisos con el administrador')
                if config_user and auth_user:
                    warehouse_id = record.location_source_id.warehouse_id
                    pick_id = record.env['stock.picking'].create({
                        'picking_type_id': warehouse_id.int_type_id.id,
                        'location_dest_id': record.location_id.id,
                        'location_id': record.location_source_id.id,
                        'partner_id': record.partner_id.id,
                        'repair_order_id': record.id,
                        'origin': record.name,
                        'type_transfer': 'normal',
                    })
                    vals_move = {
                        'picking_id': pick_id.id,
                        'name': record.product_id.name,
                        'product_id': record.product_id.id,
                        'product_uom_qty': 1,
                        'product_uom': record.product_id.uom_id.id,
                        'location_dest_id': record.location_id.id,
                        'location_id': record.location_source_id.id,
                        'state': 'assigned'
                    }
                    move_id = record.env['stock.move'].create(vals_move)
                    vals_move_line = {
                        'picking_id': pick_id.id,
                        'move_id': move_id.id,
                        'product_id': record.product_id.id,
                        'transfer_manager': record.product_id.transfer_manager,
                        'product_uom_qty': 1,
                        'qty_done': 1,
                        'lot_id': record.lot_id.id if record.lot_id else False,
                        'lot_name': record.lot_id.name if record.lot_id else False,
                        'product_uom_id': record.product_id.uom_id.id,
                        'location_dest_id': record.location_id.id,
                        'location_id': record.location_source_id.id,
                    }
                    record.env['stock.move.line'].create(vals_move_line)
                    quant = StockQuant.search([('product_id', '=', record.product_id.id), ('lot_id', '=', record.lot_id.id)])
                    quant.reserved_quantity = 1
                    record.picking_id = pick_id.id
                    pick_id.action_ready()
            record.state = 'draft'

    def verify_config_stages_location_warehouse(self, location, lot):
        warehouse = location.warehouse_id
        auth = False
        config = True
        if location.stage_ids:
            if lot.stage_id.id in location.stage_ids.ids:
                auth = True
        elif not location.stage_ids and warehouse.stage_ids:
            if lot.stage_id.id in warehouse.stage_ids.ids:
                auth = True
        elif not location.stage_ids and not warehouse.stage_ids:
            config = False
        else:
            auth = False
        return auth, config

    def action_validate(self):
        for record in self:
            if record.picking_id and record.state_transfer == 'ready':
                auth_user, config_user = record.verify_in_config_user_location_warehouse(record.location_id)
                if not config_user:
                    raise UserError(
                        'No se han configurado los usuarios permitidos a recepcionar desde %s, revisar permisos con el administrador' % record.location_id.display_name)
                if config_user and not auth_user:
                    raise UserError(
                        'Usted no tiene autorización para realizar esta acción, revisar permisos con el administrador')
                if config_user and auth_user:
                    auth_lot, config_lot = record.verify_config_stages_location_warehouse(record.location_id, record.lot_id)
                    if not config_lot:
                        raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % record.location_id.display_name)
                    if config_lot and not auth_lot:
                        raise UserError('El porducto %s con el numero de serie %s no puede ser transferido a la ubicacion %s porque se encuentra en estado %s' %
                            (record.product_id.name, record.lot_id.name, record.location_id.display_name,
                             record.lot_id.stage_id.name))
                    record.picking_id.button_validate()
                    if record.state_transfer == 'done':
                        record.state = 'confirmed'
            elif not record.picking_id:
                record.state = 'confirmed'
            elif record.picking_id and record.state_transfer == 'done':
                record.state = 'confirmed'
            else:
                raise ValidationError("La transferencia %s no esta en estado 'Listo'. Para confirmar la reparacion debe validar la Transferencia" % record.picking_id.name)

    def action_repair_start(self):
        res = super(RepairOrder, self).action_repair_start()
        EquipmentState = self.env['equipment.state']
        if self.lot_id:
            stage = EquipmentState.search([('code', 'in', ['in_refact'])])
            self.lot_id.stage_id = stage.id if stage else self.lot_id.stage_id.id
        self.start = True
        self.start_date = datetime.today()
        return res

    def action_repair_end(self):
        res = super(RepairOrder, self).action_repair_end()
        EquipmentState = self.env['equipment.state']
        MissingPieces = self.env['stock.missing.pieces']
        RepairMissingPieces = self.env['repair.missing.pieces']
        RepairOrderObj = self.env['repair.order']
        mp = []
        pc = []
        for repair in self:
            for piece in repair.operations:
                if piece.type == 'remove':
                    vals = {
                        'repair_id': repair.id,
                        'final_date': datetime.today(),
                        'production_lot_id': repair.lot_id.id,
                        'product_id': piece.product_id.id,
                        'name': piece.product_id.display_name,
                        'quantity': piece.product_uom_qty,
                    }
                    missing_piece_id = MissingPieces.create(vals)
                    if missing_piece_id:
                        vals_repair = {
                            'repair_id': repair.id,
                            'production_lot_id': repair.lot_id.id,
                            'product_id': piece.product_id.id,
                            'name': piece.product_id.display_name,
                            'quantity': piece.product_uom_qty,
                            'repair_line_id': piece.id,
                            'missing_piece_id': missing_piece_id.id,
                            'is_installed': False
                        }
                        RepairMissingPieces.create(vals_repair)
                if piece.type == 'add':
                    missing_piece = repair.missing_pieces_ids.filtered(lambda l: l.product_id.id == piece.product_id.id and l.quantity > 0)
                    qty = piece.product_uom_qty
                    if missing_piece:
                        for p in missing_piece:
                            if qty > 0 and qty > p.quantity:
                                last_qty = p.quantity
                                p.quantity = 0
                                p.missing_piece_id.quantity -= last_qty
                                qty -= last_qty
                            if qty > 0 and qty <= p.quantity:
                                p.quantity -= qty
                                p.missing_piece_id.quantity -= qty
                                qty -= qty
                            if p.quantity == 0:
                                p.is_installed = True
                            if p.is_installed:
                                p.missing_piece_id.unlink()
                    values_consumible = {
                        'production_lot_id': repair.lot_id.id,
                        'product_id': piece.product_id.id,
                        'name': piece.product_id.display_name,
                        'quantity': piece.product_uom_qty,
                        'warehouse_id': piece.location_id.warehouse_id.id,
                        'location_id': piece.location_id.id,
                    }
                    pc.append((0, 0, values_consumible))
            missing_pieces = True
            if not repair.missing_pieces_ids:
                missing_pieces = False
            if repair.missing_pieces_ids:
                installed = repair.missing_pieces_ids.mapped('is_installed')
                if len(installed) > 1:
                    missing_pieces = True
                else:
                    for install in installed:
                        if install:
                            missing_pieces = False
                        else:
                            missing_pieces = True
                            break
            repair.missing_pieces = missing_pieces
            if repair.missing_pieces and not repair.state_equipment:
                if repair.lot_id.state_equipment == 'new':
                    stage = EquipmentState.search([('code', 'in', ['new_dismantling'])])
                else:
                    stage = EquipmentState.search([('code', 'in', ['xrefact'])])
                repair.lot_id.stage_id = stage.id if stage else repair.lot_id.stage_id.id
                if repair.lot_id and repair.lot_id.missing_pieces_ids:
                    for line in repair.lot_id.missing_pieces_ids:
                        values = {
                            'production_lot_id': repair.lot_id.id,
                            'product_id': line.product_id.id,
                            'quantity': line.quantity,
                            'missing_piece_id': line.id,
                            'is_installed': False
                        }
                        mp.append((0, 0, values))
                if repair.missing_pieces:
                    repair_type = 'repair' if repair.lot_id.stage_id.code not in ['new', 'new_dismantling'] else 'replacement'
                    repair_id = RepairOrderObj.create({
                        'product_id': repair.product_id.id,
                        'lot_id': repair.lot_id.id if repair.lot_id else False,
                        'product_qty': 1,
                        'product_uom': repair.product_id.uom_id.id,
                        'user_id': repair.user_id.id,
                        'location_id': repair.location_id.id,
                        'location_source_id': repair.lot_id.current_location_id.id,
                        'invoice_method': repair.invoice_method,
                        'description': repair.description,
                        'origin': repair.name,
                        'repair_type': repair_type,
                        'state': 'predraft'
                    })
                    if mp:
                        for l in mp:
                            l[2].update({
                                'repair_id': repair_id.id,
                            })
                        repair_id.missing_pieces_ids = mp
                    repair.repair_order_id = repair_id.id
                    repair.lot_id.repair_order_ids = repair_id.ids
            if not repair.missing_pieces and not repair.state_equipment:
                if repair.lot_id.state_equipment == 'new':
                    stage = EquipmentState.search([('code', 'in', ['new_rearmed'])])
                else:
                    stage = EquipmentState.search([('code', 'in', ['refact'])])
                repair.lot_id.stage_id = stage.id if stage else repair.lot_id.stage_id.id
            if repair.state_equipment in ['outdated']:
                stage = EquipmentState.search([('code', 'in', ['outdated'])])
                repair.lot_id.stage_id = stage.id if stage else repair.lot_id.stage_id.id
                repair.lot_id.state_equipment = 'outdated'
            if repair.state_equipment in ['out_service']:
                stage = EquipmentState.search([('code', 'in', ['out_service'])])
                repair.lot_id.stage_id = stage.id if stage else repair.lot_id.stage_id.id
                repair.lot_id.state_equipment = 'out_service'
        repair.final_date = datetime.today()
        if pc:
            for l in pc:
                l[2].update({
                    'repair_id': repair.id,
                    'date_repair': repair.schedule_date,
                    'final_date': repair.final_date
                })
            repair.lot_id.consumible_pieces_ids = pc
        return res

    def action_repair_done(self):
        """ Creates stock move for operation and stock move for final product of repair order.
        @return: Move ids of final products

        """
        if self.filtered(lambda repair: not repair.repaired):
            raise UserError(_("Repair must be repaired in order to make the product moves."))
        self._check_company()
        self.operations._check_company()
        self.fees_lines._check_company()
        res = {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Move = self.env['stock.move']
        for repair in self:
            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id, repair.lot_id, owner_id=repair.partner_id, strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            moves = self.env['stock.move']
            move = False
            for operation in repair.operations:
                move = Move.create({
                    'name': repair.name,
                    'product_id': operation.product_id.id,
                    'product_uom_qty': operation.product_uom_qty,
                    'product_uom': operation.product_uom.id,
                    'partner_id': repair.address_id.id,
                    'location_id': operation.location_id.id,
                    'location_dest_id': operation.location_dest_id.id,
                    'repair_id': repair.id,
                    'origin': repair.name,
                    'company_id': repair.company_id.id,
                })

                # Best effort to reserve the product in a (sub)-location where it is available
                product_qty = move.product_uom._compute_quantity(
                    operation.product_uom_qty, move.product_id.uom_id, rounding_method='HALF-UP')
                available_quantity = self.env['stock.quant']._get_available_quantity(
                    move.product_id,
                    move.location_id,
                    lot_id=operation.lot_id,
                    strict=False,
                )
                move._update_reserved_quantity(
                    product_qty,
                    available_quantity,
                    move.location_id,
                    lot_id=operation.lot_id,
                    strict=False,
                )
                # Then, set the quantity done. If the required quantity was not reserved, negative
                # quant is created in operation.location_id.
                move._set_quantity_done(operation.product_uom_qty)

                if operation.lot_id:
                    move.move_line_ids.lot_id = operation.lot_id

                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
            # move = Move.create({
            #     'name': repair.name,
            #     'product_id': repair.product_id.id,
            #     'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
            #     'product_uom_qty': repair.product_qty,
            #     'partner_id': repair.address_id.id,
            #     'location_id': repair.location_id.id,
            #     'location_dest_id': repair.location_id.id,
            #     'move_line_ids': [(0, 0, {'product_id': repair.product_id.id,
            #                                'lot_id': repair.lot_id.id,
            #                                'product_uom_qty': 0,  # bypass reservation here
            #                                'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
            #                                'qty_done': repair.product_qty,
            #                                'package_id': False,
            #                                'result_package_id': False,
            #                                'owner_id': owner_id,
            #                                'location_id': repair.location_id.id,
            #                                'company_id': repair.company_id.id,
            #                                'location_dest_id': repair.location_id.id,})],
            #     'repair_id': repair.id,
            #     'origin': repair.name,
            #     'company_id': repair.company_id.id,
            # })
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines = False
            if move:
                produced_lines = move.move_line_ids
                moves |= move
            moves._action_done()
            if produced_lines:
                produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            if move:
                res[repair.id] = move.id
        return res

class RepairLine(models.Model):
    _inherit = 'repair.line'

    #type = fields.Selection(selection_add=[('not_inventory', 'No mueve inventario')], ondelete={'not_inventory': 'set default'})
    repair_line_type = fields.Many2one('repair.line.type', string='Tipo')
    repair_type = fields.Selection(related='repair_id.repair_type', string='Tipo')

    @api.onchange('repair_type')
    def onchange_repair_type(self):
        RepairLineType = self.env['repair.line.type']
        if self.repair_type:
            if self.repair_type in ['repair', 'change']:
                line_type = RepairLineType.search([('type', 'in', ['add', 'remove'])])
            elif self.repair_type in ['replacement']:
                line_type = RepairLineType.search([('type', '=', 'add')])
            elif self.repair_type in ['dismantling']:
                line_type = RepairLineType.search([('type', '=', 'remove')])
            return {'domain': {'repair_line_type': [('id', 'in', line_type.ids)]}}

    @api.onchange('repair_line_type')
    def onchange_repair_line_type(self):
        if self.repair_line_type:
            self.type = self.repair_line_type.type
            self.location_id = self.repair_line_type.location_id.id if self.repair_line_type.location_id else False
            self.location_dest_id = self.repair_line_type.location_dest_id.id if self.repair_line_type.location_dest_id else False

    @api.onchange('type')
    def onchange_operation_type(self):
        res = super(RepairLine, self).onchange_operation_type()
        if self.repair_line_type:
            if self.repair_line_type.location_id:
                self.location_id = self.repair_line_type.location_id.id
            else:
                raise UserError('No se ha configurado una ubicacion de origen para este tipo de accion')
            if self.repair_line_type.location_dest_id:
                self.location_dest_id = self.repair_line_type.location_dest_id.id
            else:
                raise UserError('No se ha configurado una ubicacion de destino para este tipo de accion')
        return res

class RepairMissingPieces(models.Model):
    _name = "repair.missing.pieces"
    _description = "Piezas Faltantes en reparacion"

    product_id = fields.Many2one('product.product', string='Pieza')
    name = fields.Char(string='Descripcion')
    production_lot_id = fields.Many2one('stock.production.lot', string='Lote')
    is_installed = fields.Boolean('Instalado', default=False, store=True, compute='_compute_is_installed')
    repair_line_id = fields.Many2one('repair.line', 'Linea de Reparacion')
    missing_piece_id = fields.Many2one('stock.missing.pieces', 'Linea de pieza faltante')
    repair_id = fields.Many2one('repair.order', 'Orden de Reparacion')
    quantity = fields.Float('Cantidad')

    @api.depends('quantity')
    def _compute_is_installed(self):
        for line in self:
            if line.quantity == 0:
                line.is_installed = True
            else:
                line.is_installed = False

    @api.onchange('is_installed')
    def onchange_unlink_missing_piece(self):
        if self.is_installed:
            self.missing_piece_id.unlink()
