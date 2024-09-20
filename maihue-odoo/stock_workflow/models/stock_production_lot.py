from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
from collections import defaultdict

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def _default_stage_id(self):
        stage_id = self.env['equipment.state'].search([('code', '=', 'new')])
        if stage_id:
            return stage_id.id

    name = fields.Char('Lot/Serial Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
                       required=True, help="Unique Lot/Serial Number", index=True, tracking=True)
    stage_id = fields.Many2one('equipment.state', string='Estado de Equipo', index=True, tracking=True, copy=False, ondelete='restrict', default=_default_stage_id)
    stage_code = fields.Selection(related='stage_id.code')
    missing_pieces = fields.Boolean(string='Faltan Piezas', compute='_compute_missing_pieces', store=True)
    validate = fields.Boolean(string='Validado', default=False)
    view_validate = fields.Char(compute='_compute_view_validate', string='View check validate')
    missing_pieces_ids = fields.One2many('stock.missing.pieces', inverse_name='production_lot_id', string='Piezas Faltantes')
    consumible_pieces_ids = fields.One2many('stock.consumible.pieces', inverse_name='production_lot_id', string='Piezas Consumidas')
    repair_order_ids = fields.Many2many('repair.order', string="Repair Orders")
    repair_order_count = fields.Integer('Repair order count', compute="_compute_repair_order_ids", store=True)
    current_location_id = fields.Many2one('stock.location', string="Ubicacion Actual", compute="_compute_current_location_id", store=True)
    contract_line_ids = fields.Many2many('history.contract.line', inverse_name='production_lot_id', string="Historial de lineas de Contrato")
    contract_line_count = fields.Integer('Line agreement count', compute="_compute_history_contract_line_ids", store=True)
    current_agreement_line_id = fields.Many2one('agreement.line', string="Linea de contrato actual")
    state_equipment = fields.Selection(string='Estado uso equipo', selection=[('new', 'Nuevo'), ('used', 'Usado'),('outdated', 'Obsoleto'),('out_service', 'Fuera de Servicio'),('discarded', 'Desechado')], default='new')
    customer_id = fields.Many2one('res.partner', string='Cliente (Propietario)')
    franchisee_id = fields.Many2one('res.users', string='Franquiciado a')
    history_franchisee_log_ids = fields.One2many('franchisee.equipment.log', 'production_lot_id', string='Historial Franquiciado',
        required=False)
    business_unit_id = fields.Many2one('agreement.type.partner', string='Unidad de Negocio')
    history_business_unit_ids = fields.One2many('business.unit.log', 'production_lot_id', string='Historial Unidad de Negocio',
                                                 required=False)
    @api.onchange('current_agreement_line_id')
    def onchange_business_unit(self):
        ###### Historial para unidad de Negocio ##################
        if self.current_agreement_line_id and not self.business_unit_id:
            self.env['business.unit.log'].create({
                'production_lot_id': self.id,
                'date': datetime.today().date(),
                'agreement_line_id': self.current_agreement_line_id.id,
                'business_unit_id': self.current_agreement_line_id.agreement_id.type_partner.id,
                'type': 'link'
            })
            self.business_unit_id = self.current_agreement_line_id.agreement_id.type_partner.id
        elif self.current_agreement_line_id and self.business_unit_id:
            current_business_unit_id = self.business_unit_id
            if current_business_unit_id.id != self.current_agreement_line_id.agreement_id.type_partner.id:
                self.env['business.unit.log'].create({
                    'production_lot_id': self.id,
                    'date': datetime.today().date(),
                    'agreement_line_id': self.current_agreement_line_id.id,
                    'business_unit_id': current_business_unit_id.id,
                    'type': 'unrelated'
                })
                self.business_unit_id = self.current_agreement_line_id.agreement_id.type_partner.id
                self.env['business.unit.log'].create({
                    'production_lot_id': self.id,
                    'date': datetime.today().date(),
                    'agreement_line_id': self.current_agreement_line_id.id,
                    'business_unit_id': self.business_unit_id.id,
                    'type': 'link'
                })

    def button_reviewed(self):
        EquipmentState = self.env['equipment.state']
        if self.stage_id.code == 'check':
            stage = EquipmentState.search([('code', 'in', ['reviewed'])])
            if stage:
                self.stage_id = stage.id if stage else self.stage_id.id

    @api.depends()
    def _compute_history_contract_line_ids(self):
        HistoryContractLine = self.env['history.contract.line']
        for lot in self:
            contract_lines = HistoryContractLine.search([('production_lot_id', '=', lot.id)])
            lot.contract_line_ids = contract_lines.ids if contract_lines else False
            lot.contract_line_count = len(contract_lines)

    def view_agreement_lines(self):
        #istory_contract_lines = self.mapped('contract_line_ids')
        history_contract_lines = self.env['history.contract.line'].search([('production_lot_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id("stock_workflow.history_contract_line_action")
        if history_contract_lines:
            action['domain'] = [('id', 'in', history_contract_lines.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _verify_current_repair_order(self):
        repair = self.env['repair.order'].search([('lot_id', '=', self.id), ('state', 'not in', ['done', 'cancel'])])
        if repair:
            return repair
        return False

    @api.depends('quant_ids')
    def _compute_current_location_id(self):
        for record in self:
            location = False
            if record.quant_ids:
                for quant in record.quant_ids.filtered(lambda s: s.location_id.usage == 'internal'):
                    location = quant.location_id
            record.current_location_id = location.id if location else False

    @api.depends('repair_order_ids', 'repair_order_ids.state')
    def _compute_repair_order_ids(self):
        RepairOrder = self.env['repair.order']
        for lot in self:
            repair_orders = RepairOrder.search([('lot_id', 'in', lot.ids)])
            lot.repair_order_ids = repair_orders.ids
            lot.repair_order_count = len(lot.repair_order_ids)

    @api.depends('missing_pieces_ids')
    def _compute_missing_pieces(self):
        for record in self:
            if record.missing_pieces_ids:
                record.missing_pieces = True
            else:
                record.missing_pieces = False

    def _compute_view_validate(self):
        for record in self:
            record.view_validate = False
            if record.env.user.has_group('stock_workflow.validate_number_lot_group'):
                record.view_validate = True

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

    def action_create_repair_order(self):
        active_id = self.browse(self.env.context.get('active_id'))
        repair = active_id._verify_current_repair_order()
        if not repair:
            view_id = self.env.ref('stock_workflow.product_repair_order_wizard_form')
            return {
                'name': 'Wizard Orden Reparacion',
                'type': 'ir.actions.act_window',
                'view_id': view_id.id,
                'view_mode': 'form',
                'views': [(view_id.id, 'form')],
                'res_model': 'product.repair.order.wizard',
                'context': {'default_repair_type': 'repair'},
                'binding_model_id': 'stock.production.lot',
                'binding_view_types': 'form',
                'target': 'new'
            }
        else:
            raise UserError("Hay una orden de reparacion sin finalizar para este equipo")

    def action_create_change_order(self):
        active_id = self.browse(self.env.context.get('active_id'))
        repair = active_id._verify_current_repair_order()
        if not repair:
            stock_quant = self.env['stock.quant'].search([('product_id', '=', active_id.product_id.id), ('lot_id', '=', active_id.id)]).filtered(lambda s: s.location_id.usage == 'internal' and s.quantity > 0)
            warehouse = self.env['stock.warehouse'].search([('is_workshop', '=', True)])
            location_id = warehouse.lot_stock_id if warehouse else False
            if location_id:
                auth_lot, config_lot = self.verify_config_stages_location_warehouse(location_id, active_id)
                if not config_lot:
                    raise UserError(
                        'No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % location_id.display_name)
                if config_lot and not auth_lot:
                    raise UserError(
                        'Este numero de serie no puede ser transferido al Taller porque no se admite el estado atual')
                missing_pieces = []
                if active_id.missing_pieces_ids:
                    for line in active_id.missing_pieces_ids:
                        missing_pieces.append([0, 0, {
                            'production_lot_id': line.production_lot_id.id,
                            'name': line.production_lot_id.product_id.display_name,
                            'product_id': line.production_lot_id.product_id.id,
                            'missing_piece_id': line.id
                        }])
                vals = {
                    'repair_type': 'change',
                    'product_id': active_id.product_id.id,
                    'lot_id': active_id.id,
                    'product_uom': active_id.product_id.uom_id.id,
                    'location_id': location_id.id,
                    'location_source_id': stock_quant.location_id.id,
                    'schedule_date': datetime.today(),
                    'missing_pieces_ids': missing_pieces if missing_pieces else False
                }
                repair_order = self.env['repair.order'].create(vals)
                self.repair_order_ids = repair_order.ids
                active_id._compute_repair_order_ids()
        else:
            raise UserError("Hay una orden de reparacion sin finalizar para este equipo")

    def action_create_replacement_order(self):
        active_id = self.browse(self.env.context.get('active_id'))
        repair = active_id._verify_current_repair_order()
        if not repair:
            stock_quant = self.env['stock.quant'].search([('product_id', '=', active_id.product_id.id), ('lot_id', '=', active_id.id)]).filtered(lambda s: s.location_id.usage == 'internal' and s.quantity > 0)
            warehouse = self.env['stock.warehouse'].search([('is_workshop', '=', True)])
            location_id = warehouse.lot_stock_id if warehouse else False
            if location_id:
                auth_lot, config_lot = self.verify_config_stages_location_warehouse(location_id, active_id)
                if not config_lot:
                    raise UserError(
                        'No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % location_id.display_name)
                if config_lot and not auth_lot:
                    raise UserError(
                        'Este numero de serie no puede ser transferido al Taller porque no se admite el estado atual')
                missing_pieces = []
                if active_id.missing_pieces_ids:
                    for line in active_id.missing_pieces_ids:
                        missing_pieces.append([0, 0, {
                            'production_lot_id': line.production_lot_id.id,
                            'name': line.production_lot_id.product_id.display_name,
                            'product_id': line.production_lot_id.product_id.id,
                            'missing_piece_id': line.id
                        }])
                vals = {
                    'repair_type': 'replacement',
                    'product_id': active_id.product_id.id,
                    'lot_id': active_id.id,
                    'product_uom': active_id.product_id.uom_id.id,
                    'location_id': location_id.id,
                    'location_source_id': stock_quant.location_id.id,
                    'schedule_date': datetime.today(),
                    'missing_pieces_ids': missing_pieces if missing_pieces else False
                }
                repair_order = self.env['repair.order'].create(vals)
                self.repair_order_ids = repair_order.ids
                active_id._compute_repair_order_ids()
        else:
            raise UserError("Hay una orden de reparacion sin finalizar para este equipo")

    def action_create_dismantling_order(self):
        active_id = self.browse(self.env.context.get('active_id'))
        repair = active_id._verify_current_repair_order()
        if not repair:
            stock_quant = self.env['stock.quant'].search([('product_id', '=', active_id.product_id.id), ('lot_id', '=', active_id.id)]).filtered(lambda s: s.location_id.usage == 'internal' and s.quantity > 0)
            warehouse = self.env['stock.warehouse'].search([('is_workshop', '=', True)])
            location_id = warehouse.lot_stock_id if warehouse else False
            if location_id:
                auth_lot, config_lot = self.verify_config_stages_location_warehouse(location_id, active_id)
                if not config_lot:
                    raise UserError(
                        'No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % location_id.display_name)
                if config_lot and not auth_lot:
                    raise UserError(
                        'Este numero de serie no puede ser transferido al Taller porque no se admite el estado atual')
                missing_pieces = []
                if active_id.missing_pieces_ids:
                    for line in active_id.missing_pieces_ids:
                        missing_pieces.append([0, 0, {
                            'production_lot_id': line.product_id.id,
                            'name': line.product_id.display_name,
                            'product_id': line.production_lot_id.product_id.id,
                            'missing_piece_id': line.id
                        }])
                vals = {
                    'repair_type': 'dismantling',
                    'product_id': active_id.product_id.id,
                    'lot_id': active_id.id,
                    'product_uom': active_id.product_id.uom_id.id,
                    'location_id': location_id.id,
                    'location_source_id': stock_quant.location_id.id,
                    'schedule_date': datetime.today(),
                    'missing_pieces_ids': missing_pieces if missing_pieces else False
                }
                repair_order = self.env['repair.order'].create(vals)
                self.repair_order_ids = repair_order.ids
                active_id._compute_repair_order_ids()
        else:
            raise UserError("Hay una orden de reparacion sin finalizar para este equipo")

class StockMissingPieces(models.Model):
    _name = "stock.missing.pieces"
    _description = "Piezas Faltantes"
    _rec_name = "name"

    product_id = fields.Many2one('product.product', string='Pieza')
    name = fields.Char(string='Descripcion')
    production_lot_id = fields.Many2one('stock.production.lot', string='Lote')
    repair_id = fields.Many2one('repair.order', 'Orden de Reparacion')
    quantity = fields.Float('Cantidad')
    final_date = fields.Date(string="Fecha final")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name

class StockConsumiblePieces(models.Model):
    _name = "stock.consumible.pieces"
    _description = "Piezas Consumidas"

    product_id = fields.Many2one('product.product', string='Pieza')
    name = fields.Char(string='Descripcion')
    production_lot_id = fields.Many2one('stock.production.lot', string='Lote')
    quantity = fields.Float('Cantidad')
    date_repair = fields.Date('Fecha')
    repair_id = fields.Many2one('repair.order', string='Orden de reparacion')
    final_date = fields.Date(string="Fecha final")
    warehouse_id = fields.Many2one('stock.warehouse', string='Bodega origen')
    location_id = fields.Many2one('stock.location', string='Ubicacion origen')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name

class HistoryContractLine(models.Model):
    _name = "history.contract.line"
    _description = "Historial lineas de contrato"

    production_lot_id = fields.Many2one('stock.production.lot', string='Lote')
    agreement_line_id = fields.Many2one('agreement.line', 'Linea de Contrato')
    date = fields.Date('Fecha')
    type = fields.Selection(string='Type', selection=[('link', 'Vinculado'), ('unlink', 'Desvinculado')])

class FranchiseeEquipmentLog(models.Model):
    _name = 'franchisee.equipment.log'
    _description = 'Log Equipo Franquiciado'
    _order = "id desc"

    production_lot_id = fields.Many2one('stock.production.lot', string='Equipo')
    picking_id = fields.Many2one('stock.picking', string='Transferencia')
    date = fields.Date('Fecha')
    franchisee_id = fields.Many2one('res.users', string='Franquiciado a')
    type = fields.Selection(selection=[('link', 'Asignado'), ('unrelated', 'Desasignado')], string='Estado')

class BusinessUnitLog(models.Model):
    _name = 'business.unit.log'
    _description = 'Log Unidad de Negocio'
    _order = "id desc"

    production_lot_id = fields.Many2one('stock.production.lot', string='Equipo')
    agreement_line_id = fields.Many2one('agreement.line', string="Linea de contrato")
    date = fields.Date('Fecha')
    business_unit_id = fields.Many2one('agreement.type.partner', string='Unidad de Negocio')
    type = fields.Selection(selection=[('link', 'Asignado'), ('unrelated', 'Desasignado')], string='Estado')