from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_edit_quantity_done(self):
        for picking in self:
            user = picking.env.user
            warehouse_id = picking.location_id.warehouse_id
            edit = False
            if picking.picking_type_id.code == 'internal' and picking.location_id and picking.location_dest_id:
                if picking.location_id.output_management_ids:
                    if user.id not in picking.location_id.output_management_ids.ids:
                        edit = False
                    else:
                        edit = True
                elif warehouse_id.output_management_ids.ids:
                    if user.id not in warehouse_id.output_management_ids.ids:
                        edit = False
                    else:
                        edit = True
        else:
            edit = True
        picking.edit_quantity_done = edit

    edit_quantity_done = fields.Boolean(string='Editar Cantidades', compute=_compute_edit_quantity_done)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Asignado'),
        ('ready', 'Listo'),
        ('check', 'Revisar'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")
    reject_reason_id = fields.Many2one('reject.reason', string='Motivo rechazo', tracking=True)
    repair_order_id = fields.Many2one('repair.order', string='Orden de Reparacion')
    is_partner = fields.Boolean(string='Bodega Clientes')
    customer_id = fields.Many2one('res.partner', string='Cliente (Propietario)')
    source_franchisee_id = fields.Many2one('res.users', string='Franquiciar de')
    franchisee_id = fields.Many2one('res.users', string='Franquiciar a')
    type_transfer = fields.Selection(string='Tipo de transferencia', selection=[('normal', 'Normal'),('franchisee', 'Franquiciar'), ('change_franchisee', 'Cambiar Franquiciado')])
    lines_franchisee = fields.Boolean(string='Lineas con otro franquiciado', compute='_compute_lines_franchisee')
    agreement_line_id = fields.Many2one('agreement.line', string="Linea de contrato actual")
    type_transfer_equipment = fields.Selection(string='Tipo de Ticket', selection=[('install', 'Instalacion'), ('uninstall', 'Desinstalacion Termino Contrato'), ('uninstall_repair', 'Desinstalacion Incidencia'), ('change', 'Cambio de Domicilio'), ('inci', 'Incidencia')])

    def verify_main_products(self):
        invalid = False
        line_products = []
        main_products = self.agreement_line_id.product_id.product_related_ids.filtered(lambda s: s.is_principal).mapped('product_id')
        for line in self.move_ids_without_package:
            if line.product_id.id in main_products.ids:
                if line_products:
                    invalid = True
                    break
                elif not line_products and line.product_uom_qty == 1:
                    line_products.append(line.product_id.id)
                elif not line_products and line.product_uom_qty > 1:
                    invalid = True
                    break
        return invalid

    def write(self, values):
        invalid = False
        if self.move_ids_without_package:
            invalid = self.verify_main_products()
        if invalid:
            raise UserError('No puede incluir mas de 1 producto principal')
        return super(StockPicking, self).write(values)


    def _compute_lines_franchisee(self):
        for picking in self:
            franchisee = False
            if picking.type_transfer not in ['normal']:
                for line in picking.move_line_ids_without_package:
                    if line.franchisee_id:
                        franchisee = True
                        break
            picking.lines_franchisee = franchisee


    @api.onchange('location_id', 'location_dest_id', 'picking_type_id')
    def _onchange_locations(self):
        for sm in self.move_ids_without_package:
            sm.location_id = self.location_id.id
            sm.location_dest_id = self.location_dest_id.id
        for sml in self.move_line_ids_without_package:
            sml.location_id = self.location_id.id
            sml.location_dest_id = self.location_dest_id.id
        if self.picking_type_code == 'internal' and self.type_transfer not in ['normal']:
            self.location_dest_id = self.location_id.id
        if self.location_id and self.location_dest_id:
            if not self.location_id.warehouse_id.is_partner and self.location_dest_id.warehouse_id.is_partner:
                self.l10n_cl_delivery_guide_reason = '3'
                self.update({
                    'is_partner': self.location_dest_id.warehouse_id.is_partner
                })
            elif self.location_id.warehouse_id.is_partner and not self.location_dest_id.warehouse_id.is_partner:
                self.l10n_cl_delivery_guide_reason = '7'
            elif not self.location_id.warehouse_id.is_partner and not self.location_dest_id.warehouse_id.is_partner:
                self.l10n_cl_delivery_guide_reason = '5'

    @api.depends('state')
    def _compute_show_validate(self):
        for picking in self:
            if not (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned') and picking.picking_type_code in ['outgoing', 'incoming']:
                picking.show_validate = False
            elif picking.state not in ('ready') and picking.picking_type_code in ['internal']:
                picking.show_validate = False
            else:
                picking.show_validate = True

    def button_reserve_picking_internal(self):
        for picking in self:
            picking.message_post(body=_('Reservando cantidades'))
            for line in picking.move_ids_without_package:
                if line.transfer_manager and line.product_id.tracking == 'serial' and line.reserved_availability < line.product_uom_qty:
                    if picking.type_transfer == 'normal':
                        stage_ids = picking.location_dest_id.stage_ids.ids if picking.location_dest_id.stage_ids else self.location_dest_id.warehouse_id.stage_ids.ids if self.location_dest_id.warehouse_id.stage_ids else False
                        if stage_ids:
                            quantity = line.product_uom_qty - line.reserved_availability
                            quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                            lots = []
                            if picking.agreement_line_id and picking.agreement_line_id.admin_line_id and picking.agreement_line_id.admin_line_id.is_franchisee:
                                quants = quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id == picking.agreement_line_id.admin_line_id.id)
                            elif picking.agreement_line_id and picking.agreement_line_id.admin_line_id and picking.agreement_line_id.admin_line_id.is_admin:
                                quants = quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and not s.franchisee_id )
                            elif not picking.agreement_line_id and picking.user_id.is_franchisee:
                                quants = quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id == picking.user_id.id)
                            else:
                                quants = quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and not s.franchisee_id)
                            for quant in quants:
                                if len(lots) < quantity:
                                    lots.append(quant.lot_id)
                                    quant.reserved_quantity = 1
                            for lot in lots:
                                vals_move_line = {
                                    'picking_id': line.picking_id.id,
                                    'move_id': line.id,
                                    'product_id': line.product_id.id,
                                    'transfer_manager': line.product_id.transfer_manager,
                                    'franchisee_id': lot.franchisee_id.id if lot.franchisee_id else False,
                                    'product_uom_qty': 1,
                                    'lot_id': lot.id,
                                    'lot_name': lot.name,
                                    'product_uom_id': line.product_id.uom_id.id,
                                    'location_dest_id': line.location_dest_id.id,
                                    'location_id': line.picking_id.location_id.id,
                                }
                                picking.env['stock.move.line'].create(vals_move_line)
                        else:
                            raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % self.location_dest_id.display_name)
                    elif picking.type_transfer == 'franchisee':
                        stage_ids = picking.location_dest_id.stage_ids.ids if picking.location_dest_id.stage_ids else self.location_dest_id.warehouse_id.stage_ids.ids if self.location_dest_id.warehouse_id.stage_ids else False
                        if stage_ids:
                            quantity = line.product_uom_qty - line.reserved_availability
                            quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                            lots = []
                            if quants:
                                for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id == False):
                                    if len(lots) < quantity:
                                        lots.append(quant.lot_id)
                                        quant.reserved_quantity = 1
                                for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id != line.picking_id.franchisee_id.id):
                                    if len(lots) < quantity:
                                        lots.append(quant.lot_id)
                                        quant.reserved_quantity = 1
                                for lot in lots:
                                    vals_move_line = {
                                        'picking_id': line.picking_id.id,
                                        'move_id': line.id,
                                        'product_id': line.product_id.id,
                                        'transfer_manager': line.product_id.transfer_manager,
                                        'product_uom_qty': 1,
                                        'franchisee_id': lot.franchisee_id.id if lot.franchisee_id else False,
                                        'lot_id': lot.id,
                                        'lot_name': lot.name,
                                        'product_uom_id': line.product_id.uom_id.id,
                                        'location_dest_id': line.location_dest_id.id,
                                        'location_id': line.picking_id.location_id.id,
                                    }
                                    picking.env['stock.move.line'].create(vals_move_line)
                        else:
                            raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % self.location_dest_id.display_name)
                    elif picking.type_transfer == 'change_franchisee':
                        stage_ids = picking.location_dest_id.stage_ids.ids if picking.location_dest_id.stage_ids else self.location_dest_id.warehouse_id.stage_ids.ids if self.location_dest_id.warehouse_id.stage_ids else False
                        if stage_ids:
                            quantity = line.product_uom_qty - line.reserved_availability
                            quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                            lots = []
                            if quants:
                                for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id == line.picking_id.source_franchisee_id.id):
                                    if len(lots) < quantity:
                                        lots.append(quant.lot_id)
                                        quant.reserved_quantity = 1
                                for lot in lots:
                                    vals_move_line = {
                                        'picking_id': line.picking_id.id,
                                        'move_id': line.id,
                                        'product_id': line.product_id.id,
                                        'transfer_manager': line.product_id.transfer_manager,
                                        'product_uom_qty': 1,
                                        'franchisee_id': lot.franchisee_id.id if lot.franchisee_id else False,
                                        'lot_id': lot.id,
                                        'lot_name': lot.name,
                                        'product_uom_id': line.product_id.uom_id.id,
                                        'location_dest_id': line.location_dest_id.id,
                                        'location_id': line.picking_id.location_id.id,
                                    }
                                    picking.env['stock.move.line'].create(vals_move_line)
                        else:
                            raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % self.location_dest_id.display_name)
                elif not line.transfer_manager and line.product_id.tracking == 'serial' and line.reserved_availability < line.product_uom_qty:
                    if picking.type_transfer == 'normal':
                        quantity = line.product_uom_qty - line.reserved_availability
                        quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                        lots = []
                        if picking.agreement_line_id and picking.agreement_line_id.admin_line_id and picking.agreement_line_id.admin_line_id.is_franchisee:
                            quants = quants.filtered(lambda s: s.available_quantity > 0 and s.franchisee_id.id == picking.agreement_line_id.admin_line_id.id)
                        elif picking.agreement_line_id and picking.agreement_line_id.admin_line_id and picking.agreement_line_id.admin_line_id.is_admin:
                            quants = quants.filtered(lambda s: s.available_quantity > 0 and not s.franchisee_id )
                        elif not picking.agreement_line_id and picking.user_id.is_franchisee:
                            quants = quants.filtered(lambda s: s.available_quantity > 0 and s.franchisee_id.id == picking.user_id.id)
                        else:
                            quants = quants.filtered(lambda s: s.available_quantity > 0 and not s.franchisee_id)
                        for quant in quants:
                            if len(lots) < quantity:
                                lots.append(quant.lot_id)
                                quant.reserved_quantity = 1
                        for lot in lots:
                            vals_move_line = {
                                'picking_id': line.picking_id.id,
                                'move_id': line.id,
                                'product_id': line.product_id.id,
                                'transfer_manager': line.product_id.transfer_manager,
                                'franchisee_id': lot.franchisee_id.id if lot.franchisee_id else False,
                                'product_uom_qty': 1,
                                'lot_id': lot.id,
                                'lot_name': lot.name,
                                'product_uom_id': line.product_id.uom_id.id,
                                'location_dest_id': line.location_dest_id.id,
                                'location_id': line.picking_id.location_id.id,
                            }
                            picking.env['stock.move.line'].create(vals_move_line)
                    elif picking.type_transfer == 'franchisee':
                        stage_ids = picking.location_dest_id.stage_ids.ids if picking.location_dest_id.stage_ids else self.location_dest_id.warehouse_id.stage_ids.ids if self.location_dest_id.warehouse_id.stage_ids else False
                        if stage_ids:
                            quantity = line.product_uom_qty - line.reserved_availability
                            quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                            lots = []
                            if quants:
                                for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id == False):
                                    if len(lots) < quantity:
                                        lots.append(quant.lot_id)
                                        quant.reserved_quantity = 1
                                for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id != line.picking_id.franchisee_id.id):
                                    if len(lots) < quantity:
                                        lots.append(quant.lot_id)
                                        quant.reserved_quantity = 1
                                for lot in lots:
                                    vals_move_line = {
                                        'picking_id': line.picking_id.id,
                                        'move_id': line.id,
                                        'product_id': line.product_id.id,
                                        'transfer_manager': line.product_id.transfer_manager,
                                        'product_uom_qty': 1,
                                        'franchisee_id': lot.franchisee_id.id if lot.franchisee_id else False,
                                        'lot_id': lot.id,
                                        'lot_name': lot.name,
                                        'product_uom_id': line.product_id.uom_id.id,
                                        'location_dest_id': line.location_dest_id.id,
                                        'location_id': line.picking_id.location_id.id,
                                    }
                                    picking.env['stock.move.line'].create(vals_move_line)
                        else:
                            raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % self.location_dest_id.display_name)
                    elif picking.type_transfer == 'change_franchisee':
                        stage_ids = picking.location_dest_id.stage_ids.ids if picking.location_dest_id.stage_ids else self.location_dest_id.warehouse_id.stage_ids.ids if self.location_dest_id.warehouse_id.stage_ids else False
                        if stage_ids:
                            quantity = line.product_uom_qty - line.reserved_availability
                            quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                            lots = []
                            if quants:
                                for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids and s.available_quantity > 0 and s.franchisee_id.id == line.picking_id.source_franchisee_id.id):
                                    if len(lots) < quantity:
                                        lots.append(quant.lot_id)
                                        quant.reserved_quantity = 1
                                for lot in lots:
                                    vals_move_line = {
                                        'picking_id': line.picking_id.id,
                                        'move_id': line.id,
                                        'product_id': line.product_id.id,
                                        'transfer_manager': line.product_id.transfer_manager,
                                        'product_uom_qty': 1,
                                        'franchisee_id': lot.franchisee_id.id if lot.franchisee_id else False,
                                        'lot_id': lot.id,
                                        'lot_name': lot.name,
                                        'product_uom_id': line.product_id.uom_id.id,
                                        'location_dest_id': line.location_dest_id.id,
                                        'location_id': line.picking_id.location_id.id,
                                    }
                                    picking.env['stock.move.line'].create(vals_move_line)
                        else:
                            raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % self.location_dest_id.display_name)
                elif line.product_id.tracking in ['none', 'lot']: # and line.reserved_availability < line.product_uom_qty:
                    line._action_confirm()
                    # quantity = line.product_uom_qty - line.reserved_availability
                    # quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                    # # for quant in quants.filtered(lambda s: s.lot_id.stage_id.id in stage_ids):
                    # qty = quantity
                    # if quants:
                    #     if line.reserved_availability == 0:
                    #         for quant in quants.filtered(lambda s: s.available_quantity > 0):
                    #             if line.reserved_availability < line.product_uom_qty:
                    #                 if quant.available_quantity >= line.product_uom_qty:
                    #                     quant.reserved_quantity = line.product_uom_qty
                    #                 else:
                    #                     qty = quant.available_quantity
                    #                     quant.reserved_quantity += qty
                    #                 vals_move_line = {
                    #                     'picking_id': line.picking_id.id,
                    #                     'move_id': line.id,
                    #                     'product_id': line.product_id.id,
                    #                     'transfer_manager': line.product_id.transfer_manager,
                    #                     'product_uom_qty': qty,
                    #                     'product_uom_id': line.product_id.uom_id.id,
                    #                     'location_dest_id': line.location_dest_id.id,
                    #                     'location_id': line.picking_id.location_id.id,
                    #                     'customer_id': line.picking_id.customer_id.id if line.picking_id.customer_id else False
                    #                 }
                    #                 picking.env['stock.move.line'].create(vals_move_line)
                    #     else:
                    #         move_line = picking.move_line_ids_without_package.filtered(lambda l: l.product_id.id == line.product_id.id and l.move_id.id == line.id)
                    #         if move_line:
                    #             for quant in quants.filtered(lambda s: s.available_quantity > 0):
                    #                 if line.reserved_availability < line.product_uom_qty:
                    #                     if quant.available_quantity >= line.product_uom_qty:
                    #                         quant.reserved_quantity = line.product_uom_qty
                    #                     else:
                    #                         qty = quant.available_quantity
                    #                         quant.reserved_quantity += qty
                    #                 move_line.product_uom_qty = qty
                # elif line.product_id.tracking == 'lot': # and line.reserved_availability < line.product_uom_qty:
                #     line._action_confirm()
                    # quantity = line.product_uom_qty - line.reserved_availability
                    # quants = picking.env['stock.quant'].search([('location_id', '=', line.picking_id.location_id.id), ('product_id', '=', line.product_id.id), ('available_quantity', '>', 0)])
                    # if quants:
                    #     quant = quants[0]
                    #     lot = quants[0].lot_id
                    #     vals_move_line = {
                    #         'picking_id': line.picking_id.id,
                    #         'move_id': line.id,
                    #         'product_id': line.product_id.id,
                    #         'product_uom_qty': quantity,
                    #         'lot_id': lot.id,
                    #         'lot_name': lot.name,
                    #         'product_uom_id': line.product_id.uom_id.id,
                    #         'location_dest_id': line.location_dest_id.id,
                    #         'location_id': line.picking_id.location_id.id,
                    #     }
                    #     picking.env['stock.move.line'].create(vals_move_line)
                    #     quant.reserved_quantity = quantity
            state = 'assigned'
            for line in picking.move_ids_without_package.filtered(lambda l: l.product_id.tracking == 'serial'):
                if line.reserved_availability < line.product_uom_qty and line.reserved_availability == 0:
                    state = 'confirmed'
                if line.reserved_availability < line.product_uom_qty and line.reserved_availability > 0:
                    state = 'partially_available'
                line.state = state
            #self.state == state

    def action_confirm(self):
        for picking in self:
            warehouse_wksh = picking.location_dest_id.warehouse_id.is_workshop
            if picking.move_ids_without_package:
                if picking.picking_type_code == 'internal':
                    if warehouse_wksh:  # Si el destino es el Taller verifica si el origen tiene excepcion de OR o no
                        if not picking.location_id.trf_without_ro and not picking.repair_order_id:
                            raise UserError('Necesita una orden de reparacion para transferir los productos desde %s' % picking.location_id.display_name)
                    if picking.is_partner and not picking.agreement_line_id:
                        raise UserError('No puede transferir un equipo a un Cliente sin tener una linea de contrato asociada')
                    picking.button_reserve_picking_internal()
                else:
                    return super(StockPicking, picking).action_confirm()
            else:
                if picking.picking_type_code == 'internal':
                    if picking.is_partner and not picking.agreement_line_id:
                        raise UserError('No puede transferir un equipo a un Cliente sin tener una linea de contrato asociada')
                    picking.button_reserve_picking_internal()
                else:
                    return super(StockPicking, picking).action_confirm()

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

    def verify_config_stages_location_warehouse(self, location, lot):
        warehouse = location.warehouse_id
        auth = False
        config = True
        list_products = []
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

    def action_ready(self):
        uid = self.env.user.id
        for picking in self:
            if picking.user_id.id == uid:
                state = 'assigned'
                if picking.picking_type_code != 'incoming':
                    warehouse_wksh = picking.location_dest_id.warehouse_id.is_workshop
                    auth_user, config_user = picking.verify_out_config_user_location_warehouse(picking.location_id)
                    line_review = picking.move_line_ids_without_package.mapped('qty_done')
                    line_review = set(line_review)
                    if warehouse_wksh: # Si el destino es el Taller verifica si el origen tiene excepcion de OR o no
                        if not picking.location_id.trf_without_ro and not picking.repair_order_id:
                            raise UserError('Necesita una orden de reparacion para trnsferir los productos desde %s' % picking.location_id.display_name)
                    if not config_user:
                        raise UserError('No se han configurado los usuarios permitidos a entregar desde %s, revisar permisos con el administrador' % picking.location_id.display_name)
                    if config_user and not auth_user:
                        raise UserError('Usted no tiene autorización para realizar esta acción, revisar permisos con el administrador')
                    if config_user and auth_user:
                        for line in picking.move_line_ids_without_package:
                            if line.transfer_manager:
                                auth_lot, config_lot = picking.verify_config_stages_location_warehouse(picking.location_dest_id, line.lot_id)
                                if not config_lot:
                                    raise UserError('No se han configurado los estados de equipos permitidos en %s, revisar permisos con el administrador' % picking.location_dest_id.display_name)
                                if config_lot and not auth_lot:
                                    raise UserError('El porducto %s con el numero de serie %s no puede ser transferido a la ubicacion %s porque se encuentra en estado %s' %
                                                                (line.product_id.name, line.lot_id.name, line.location_dest_id.display_name, line.lot_id.stage_id.name))
                    if len(line_review) == 1:
                        if list(line_review)[0] != 0:
                            state = 'ready'
                        else:
                            raise UserError('Debe ingresar las cantidades a entregar')
                    if len(line_review) > 1:
                        return {
                            'name': 'Confirmar',
                            'type': 'ir.actions.act_window',
                            'view_id': picking.env.ref('stock_workflow.stock_ready_confirm_form').id,
                            'view_mode': 'form',
                            'res_model': 'stock.ready.confirm',
                            'target': 'new'
                        }
                else:
                    state = 'ready'
                picking.state = state
            else:
                raise UserError('La solicitud debe ser procesada por el usuario responsable')

    
    def action_reject(self):
        for picking in self:
            warehouse_id = picking.location_dest_id.warehouse_id
            user = picking.env.user
            if picking.location_dest_id.input_management_ids:
                if user.id in picking.location_dest_id.input_management_ids.ids:
                    return {
                        'name': 'Motivo de Rechazo',
                        'type': 'ir.actions.act_window',
                        'view_id': picking.env.ref('stock_workflow.reject_reason_wizard_form').id,
                        'view_mode': 'form',
                        'res_model': 'reject.reason.wizard',
                        'target': 'new'
                    }
                else:
                    raise UserError("No esta autorizado para rechazar los productos en la ubicación %s" % picking.location_dest_id.display_name)
            elif warehouse_id.input_management_ids:
                if user.id in warehouse_id.input_management_ids.ids:
                    return {
                        'name': 'Motivo de Rechazo',
                        'type': 'ir.actions.act_window',
                        'view_id': picking.env.ref('stock_workflow.reject_reason_wizard_form').id,
                        'view_mode': 'form',
                        'res_model': 'reject.reason.wizard',
                        'target': 'new'
                    }
                else:
                    raise UserError("No esta autorizado para rechazar los productos en %s" % warehouse_id.display_name)
            else:
                raise UserError('Usted no tiene autorización para realizar esta acción, revisar permisos con el administrador')
        
    def action_assign(self):
        for picking in self:
            picking.message_post(body=_('Comprobando disponibilidad'))
        return super(StockPicking, self).action_assign()

    def update_stage_equipment(self):
        EquipmentState = self.env['equipment.state']
        picking = self
        warehouse_origin_id = picking.location_id.warehouse_id
        warehouse_dest_id = picking.location_dest_id.warehouse_id
        if picking.is_partner and picking.picking_type_code == 'internal':
            stage = EquipmentState.search([('code', 'in', ['active'])])
            for line in picking.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
                line.lot_id.stage_id = stage.id if stage else line.stage_id.id
                line.lot_id.state_equipment = 'used'
        if picking.picking_type_code == 'internal' and warehouse_origin_id.is_partner:
            stage = EquipmentState.search([('code', 'in', ['check'])])
            for line in picking.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
                line.lot_id.stage_id = stage.id if stage else line.stage_id.id
        if picking.picking_type_code == 'internal' and not picking.is_partner and picking.customer_id:
            if picking.type_transfer_equipment != 'change':
                stage = EquipmentState.search([('code', 'in', ['check'])])
                for line in picking.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
                    line.lot_id.stage_id = stage.id if stage else line.stage_id.id
            else:
                stage = EquipmentState.search([('code', 'in', ['domi'])])
                for line in picking.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
                    line.lot_id.stage_id = stage.id if stage else line.stage_id.id
        if picking.picking_type_code == 'internal' and warehouse_dest_id.is_workshop:
            stage = EquipmentState.search([('code', 'in', ['xrefact'])])
            for line in picking.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
                line.lot_id.stage_id = stage.id if stage else line.lot_id.stage_id.id

    def action_assing_customer_equipment(self):
        StockQuant = self.env['stock.quant']
        HistoryContractLine = self.env['history.contract.line']
        for line in self.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
            if line.picking_id.customer_id and line.picking_id.type_transfer_equipment in ['install']:
                line.lot_id.customer_id = line.picking_id.customer_id.id
                line.lot_id.current_agreement_line_id = line.picking_id.agreement_line_id.id
                line.lot_id.onchange_business_unit()
                quant = StockQuant.search([('lot_id', '=', line.lot_id.id),('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                if quant:
                    quant.customer_id = line.picking_id.customer_id.id
                if line.picking_id.agreement_line_id.product_principal == line.product_id:
                    line.picking_id.agreement_line_id.agreement_line_keys = line.lot_id.id
                HistoryContractLine.create({
                    'production_lot_id': line.picking_id.agreement_line_id.agreement_line_keys.id,
                    'date': datetime.today().date(),
                    'agreement_line_id': line.picking_id.agreement_line_id.id,
                    'type': 'link'
                })
            elif line.picking_id.customer_id and line.picking_id.type_transfer_equipment in ['uninstall', 'uninstall_repair']:
                line.lot_id.customer_id = False
                line.lot_id.current_agreement_line_id = False
                line.lot_id.onchange_business_unit()
                quant = StockQuant.search([('lot_id', '=', line.lot_id.id),('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                if quant:
                    quant.customer_id = False
                #if line.picking_id.agreement_line_id.product_principal == line.product_id:
                line.picking_id.agreement_line_id.agreement_line_keys = False
                HistoryContractLine.create({
                    'production_lot_id': line.picking_id.agreement_line_id.agreement_line_keys.id,
                    'date': datetime.today().date(),
                    'agreement_line_id': line.picking_id.agreement_line_id.id,
                    'type': 'unlink'
                })

    def action_assing_franchisee_equipment(self):
        StockQuant = self.env['stock.quant']
        for line in self.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
            if line.picking_id.franchisee_id:
                if not line.lot_id.franchisee_id:
                    line.lot_id.franchisee_id = line.picking_id.franchisee_id.id
                    self.env['franchisee.equipment.log'].create({
                        'production_lot_id': line.lot_id.id,
                        'picking_id': line.picking_id.id,
                        'date': fields.Date.today(),
                        'franchisee_id': line.picking_id.franchisee_id.id,
                        'type': 'link'
                    })
                else:
                    self.env['franchisee.equipment.log'].create({
                        'production_lot_id': line.lot_id.id,
                        'picking_id': line.picking_id.id,
                        'date': fields.Date.today(),
                        'franchisee_id': line.lot_id.franchisee_id.id,
                        'type': 'unrelated'
                    })
                    line.lot_id.franchisee_id = line.picking_id.franchisee_id.id
                    self.env['franchisee.equipment.log'].create({
                        'production_lot_id': line.lot_id.id,
                        'picking_id': line.picking_id.id,
                        'date': fields.Date.today(),
                        'franchisee_id': line.picking_id.franchisee_id.id,
                        'type': 'link'
                    })
                quant = StockQuant.search([('lot_id', '=', line.lot_id.id),('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                if quant:
                    quant.franchisee_id = line.picking_id.franchisee_id.id
            elif not line.picking_id.franchisee_id and line.picking_id.type_transfer == 'normal' and line.franchisee_id:
                quant = StockQuant.search(
                    [('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(
                    lambda s: s.location_id.usage == 'internal')
                if quant:
                    quant.franchisee_id = line.franchisee_id.id
            elif not line.picking_id.franchisee_id and line.picking_id.type_transfer == 'change_franchisee':
                self.env['franchisee.equipment.log'].create({
                    'production_lot_id': line.lot_id.id,
                    'picking_id': line.picking_id.id,
                    'date': fields.Date.today(),
                    'franchisee_id': line.lot_id.franchisee_id.id,
                    'type': 'unrelated'
                })
                line.lot_id.franchisee_id = False
                quant = StockQuant.search([('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(
                    lambda s: s.location_id.usage == 'internal')
                if quant:
                    quant.franchisee_id = False

    def action_management_equiptments(self):
        StockQuant = self.env['stock.quant']
        HistoryContractLine = self.env['history.contract.line']
        FranchiseeEquipmentLog = self.env['franchisee.equipment.log']
        for line in self.move_line_ids_without_package.filtered(lambda s: s.qty_done > 0):
            picking = line.picking_id
            if picking.type_transfer in ['normal']:
                if picking.is_partner and picking.customer_id and picking.type_transfer_equipment in ['install']:
                    line.lot_id.customer_id = picking.customer_id.id
                    line.lot_id.current_agreement_line_id = picking.agreement_line_id.id
                    line.lot_id.onchange_business_unit()
                    line.lot_id.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    quant = StockQuant.search([('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if quant:
                        quant.customer_id = line.picking_id.customer_id.id
                        quant.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    if line.picking_id.agreement_line_id.product_principal == line.product_id:
                        picking.agreement_line_id.agreement_line_keys = line.lot_id.id
                    HistoryContractLine.create({
                        'production_lot_id': line.picking_id.agreement_line_id.agreement_line_keys.id,
                        'date': datetime.today().date(),
                        'agreement_line_id': line.picking_id.agreement_line_id.id,
                        'type': 'link'
                    })
                elif picking.customer_id and picking.type_transfer_equipment in ['uninstall', 'uninstall_repair']:
                    line.lot_id.customer_id = False
                    line.lot_id.current_agreement_line_id = False
                    line.lot_id.onchange_business_unit()
                    line.lot_id.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    quant = StockQuant.search([('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if quant:
                        quant.reserved_quantity = 0.0
                        quant.customer_id = False
                        quant.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    picking.agreement_line_id.agreement_line_keys = False
                    picking.agreement_line_id.picking_id = False
                    HistoryContractLine.create({
                        'production_lot_id': line.picking_id.agreement_line_id.agreement_line_keys.id,
                        'date': datetime.today().date(),
                        'agreement_line_id': line.picking_id.agreement_line_id.id,
                        'type': 'unlink'
                    })
                elif picking.customer_id and picking.type_transfer_equipment in ['change']:
                    line.lot_id.customer_id = picking.customer_id.id
                    line.lot_id.onchange_business_unit()
                    line.lot_id.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    quant = StockQuant.search([('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if quant:
                        quant.reserved_quantity = 0.0
                        quant.customer_id = picking.customer_id.id
                        quant.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    picking.agreement_line_id.picking_id = False
                elif not picking.customer_id and not picking.type_transfer_equipment:
                    line.lot_id.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
                    quant = StockQuant.search(
                        [('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if quant:
                        quant.franchisee_id = line.franchisee_id.id if line.franchisee_id else False
            elif picking.type_transfer in ['franchisee']:
                line.lot_id.franchisee_id = picking.franchisee_id.id
                FranchiseeEquipmentLog.create({
                    'production_lot_id': line.lot_id.id,
                    'picking_id': picking.id,
                    'date': fields.Date.today(),
                    'franchisee_id': picking.franchisee_id.id,
                    'type': 'link'
                })
                quant = StockQuant.search([('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                if quant:
                    quant.franchisee_id = picking.franchisee_id.id
            elif picking.type_transfer in ['change_franchisee']:
                if not picking.franchisee_id:
                    FranchiseeEquipmentLog.create({
                        'production_lot_id': line.lot_id.id,
                        'picking_id': picking.id,
                        'date': fields.Date.today(),
                        'franchisee_id': line.lot_id.franchisee_id.id,
                        'type': 'unrelated'
                    })
                    line.lot_id.franchisee_id = False
                    quant = StockQuant.search(
                        [('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(
                        lambda s: s.location_id.usage == 'internal')
                    if quant:
                        quant.franchisee_id = False
                elif picking.franchisee_id:
                    if not line.lot_id.franchisee_id:
                        line.lot_id.franchisee_id = picking.franchisee_id.id
                        FranchiseeEquipmentLog.create({
                            'production_lot_id': line.lot_id.id,
                            'picking_id': picking.id,
                            'date': fields.Date.today(),
                            'franchisee_id': picking.franchisee_id.id,
                            'type': 'link'
                        })
                    else:
                        FranchiseeEquipmentLog.create({
                            'production_lot_id': line.lot_id.id,
                            'picking_id': picking.id,
                            'date': fields.Date.today(),
                            'franchisee_id': line.lot_id.franchisee_id.id,
                            'type': 'unrelated'
                        })
                        line.lot_id.franchisee_id = picking.franchisee_id.id
                        FranchiseeEquipmentLog.create({
                            'production_lot_id': line.lot_id.id,
                            'picking_id': line.picking_id.id,
                            'date': fields.Date.today(),
                            'franchisee_id': picking.franchisee_id.id,
                            'type': 'link'
                        })
                    quant = StockQuant.search([('lot_id', '=', line.lot_id.id), ('location_id', '=', line.location_dest_id.id)]).filtered(lambda s: s.location_id.usage == 'internal')
                    if quant:
                        quant.franchisee_id = picking.franchisee_id.id


    def button_validate(self):
        for picking in self:
            if picking.picking_type_code != 'incoming':
                user = picking.env.user
                warehouse_id = picking.location_dest_id.warehouse_id
                if picking.location_dest_id.input_management_ids:
                    if user.id in picking.location_dest_id.input_management_ids.ids:
                        picking.update_stage_equipment()
                        res = super(StockPicking, picking).button_validate()
                        picking.action_management_equiptments()
                        return res
                    else:
                        raise UserError("No esta autorizado para recibir los productos en la ubicación %s" % self.location_dest_id.display_name)
                elif warehouse_id.input_management_ids:
                    if user.id in warehouse_id.input_management_ids.ids:
                        picking.update_stage_equipment()
                        res = super(StockPicking, picking).button_validate()
                        picking.action_management_equiptments()
                        return res
                    else:
                        raise UserError("No esta autorizado para recepcionar los productos desde %s" % warehouse_id.display_name)
                else:
                    raise UserError('Usted no tiene autorización para realizar esta acción, revisar permisos con el administrador')
            else:
                return super(StockPicking, picking).button_validate()

class StockMove(models.Model):
    _inherit = 'stock.move'

    transfer_manager = fields.Boolean(string='Aplica gestión de transferencias')
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Asignado'),
        ('ready', 'Listo'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")

    @api.onchange('product_id', 'picking_type_id')
    def _onchange_product_id(self):
        res = super(StockMove, self)._onchange_product_id()
        if self.product_id:
            self.transfer_manager = self.product_id.transfer_manager
        return res


    @api.model_create_multi
    def create(self, vals_list):

        lines = super().create(vals_list)
        for line in lines:
            if line.picking_id:
                if line.product_id:
                    msg = _("Se agrego el producto %s  con cantidad %s") % (line.product_id.display_name, line.product_uom_qty)
                    line.picking_id.message_post(body=msg)
        return lines

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    edit_quantity_done = fields.Boolean(string='Editar Cantidades', related="picking_id.edit_quantity_done")
    transfer_manager = fields.Boolean(string='Aplica gestión de transferencias', related='move_id.transfer_manager')
    customer_id = fields.Many2one('res.partner', string='Cliente (Propietario)')
    franchisee_id = fields.Many2one('res.users', string='Franquiciado a')


