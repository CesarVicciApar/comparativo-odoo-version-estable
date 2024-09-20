from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime

class AgreementLine(models.Model):
    _inherit = "agreement.line"

    picking_id = fields.Many2one('stock.picking', string='Transferencia')

    def create_transfer_order(self):
        """ Este metodo debe ser llamado desde la orden en terreno para instalacion """
        StockWarehouse = self.env['stock.warehouse']
        user_id = self.env.user
        for line in self:
            if not line.agreement_line_keys and not line.picking_id:
                warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
                location_id = line.env.user.default_stock_location_id
                if line.admin_line_id.is_admin and user_id.is_admin and line.admin_line_id.id == user_id.id:
                    if location_id:
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': 'install',
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.id,
                            'is_partner': True,
                            'customer_id': line.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        vals_move = {
                            'picking_id': pick_id.id,
                            'name': line.product_principal.name,
                            'product_id': line.product_principal.id,
                            'transfer_manager': line.product_principal.transfer_manager,
                            'product_uom_qty': 1,
                            'product_uom': line.product_principal.uom_id.id,
                            'location_dest_id': pick_id.location_dest_id.id,
                            'location_id': pick_id.location_id.id,
                            'state': 'confirmed'
                        }
                        line.env['stock.move'].create(vals_move)
                        line.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    else:
                        raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif not line.admin_line_id:
                    if location_id:
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': 'install',
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.id,
                            'is_partner': True,
                            'customer_id': line.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        vals_move = {
                            'picking_id': pick_id.id,
                            'name': line.product_principal.name,
                            'product_id': line.product_principal.id,
                            'transfer_manager': line.product_principal.transfer_manager,
                            'product_uom_qty': 1,
                            'product_uom': line.product_principal.uom_id.id,
                            'location_dest_id': pick_id.location_dest_id.id,
                            'location_id': pick_id.location_id.id,
                            'state': 'confirmed'
                        }
                        line.env['stock.move'].create(vals_move)
                        line.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    else:
                        raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif line.admin_line_id.is_franchisee and user_id.is_admin:
                    if location_id:
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': 'install',
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.id,
                            'is_partner': True,
                            'customer_id': line.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        vals_move = {
                            'picking_id': pick_id.id,
                            'name': line.product_principal.name,
                            'product_id': line.product_principal.id,
                            'transfer_manager': line.product_principal.transfer_manager,
                            'product_uom_qty': 1,
                            'product_uom': line.product_principal.uom_id.id,
                            'location_dest_id': pick_id.location_dest_id.id,
                            'location_id': pick_id.location_id.id,
                            'state': 'confirmed'
                        }
                        line.env['stock.move'].create(vals_move)
                        line.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    elif not line.admin_line_id:
                        if location_id:
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': 'install',
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.id,
                                'is_partner': True,
                                'customer_id': line.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': line.product_principal.name,
                                'product_id': line.product_principal.id,
                                'transfer_manager': line.product_principal.transfer_manager,
                                'product_uom_qty': 1,
                                'product_uom': line.product_principal.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    else:
                        raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif line.admin_line_id.is_franchisee and user_id.is_franchisee and line.admin_line_id.id != user_id.id:
                    raise ValidationError("No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                elif line.admin_line_id.is_admin and user_id.is_franchisee:
                    raise ValidationError("No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
            elif not line.agreement_line_keys and line.picking_id:
                if line.picking_id.state in ['draft', 'confirmed', 'waiting', 'assigned', 'ready', 'check']:
                    raise ValidationError("Esta linea de contrato ya tiene una orden de transferencia en proceso")
                elif line.picking_id.state == 'cancel':
                    warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
                    location_id = line.env.user.default_stock_location_id
                    if line.admin_line_id.is_admin and user_id.is_admin and line.admin_line_id.id == user_id.id:
                        if location_id:
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.id,
                                'is_partner': True,
                                'customer_id': line.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': line.product_principal.name,
                                'product_id': line.product_principal.id,
                                'transfer_manager': line.product_principal.transfer_manager,
                                'product_uom_qty': 1,
                                'product_uom': line.product_principal.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.admin_line_id.is_franchisee and user_id.is_admin:
                        if location_id:
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': 'install',
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.id,
                                'is_partner': True,
                                'customer_id': line.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': line.product_principal.name,
                                'product_id': line.product_principal.id,
                                'transfer_manager': line.product_principal.transfer_manager,
                                'product_uom_qty': 1,
                                'product_uom': line.product_principal.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.admin_line_id.is_franchisee and user_id.is_franchisee and line.admin_line_id.id != user_id.id:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                    elif line.admin_line_id.is_admin and user_id.is_franchisee:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
                    elif not line.admin_line_id:
                        if location_id:
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': 'install',
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.id,
                                'is_partner': True,
                                'customer_id': line.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': line.product_principal.name,
                                'product_id': line.product_principal.id,
                                'transfer_manager': line.product_principal.transfer_manager,
                                'product_uom_qty': 1,
                                'product_uom': line.product_principal.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.admin_line_id.is_franchisee and user_id.is_franchisee and line.admin_line_id.id != user_id.id:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                    elif line.admin_line_id.is_admin and user_id.is_franchisee:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
                    elif not line.admin_line_id:
                        if location_id:
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': 'install',
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.id,
                                'is_partner': True,
                                'customer_id': line.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': line.product_principal.name,
                                'product_id': line.product_principal.id,
                                'transfer_manager': line.product_principal.transfer_manager,
                                'product_uom_qty': 1,
                                'product_uom': line.product_principal.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
            else:
                raise ValidationError("Esta linea de contrato ya tiene un equipo asignado. Para asignar uno nuevo debe primero desaginar el equipo actual")

    def create_transfer_order_uninstall(self, type_transfer_equipment='uninstall'):
        """ Este metodo debe ser llamado desde la orden en terreno para desinstalacion """
        StockWarehouse = self.env['stock.warehouse']
        StockQuant = self.env['stock.quant']
        if self.agreement_line_keys:
            warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
            location_dest_id = self.env.user.default_stock_location_id
            if location_dest_id:
                pick_id = self.env['stock.picking'].create({
                    'picking_type_id': warehouse_partner.int_type_id.id,
                    'type_transfer': 'normal',
                    'location_dest_id': location_dest_id.id,
                    'location_id': warehouse_partner.lot_stock_id.id,
                    'type_transfer_equipment': type_transfer_equipment,
                    'agreement_line_id': self.id,
                    'customer_id': self.agreement_id.partner_id.id,
                    'state': 'confirmed'
                })
                vals_move = {
                    'picking_id': pick_id.id,
                    'name': self.product_principal.name,
                    'product_id': self.product_principal.id,
                    'transfer_manager': self.product_principal.transfer_manager,
                    'product_uom_qty': 1,
                    'product_uom': self.product_principal.uom_id.id,
                    'location_dest_id': pick_id.location_dest_id.id,
                    'location_id': pick_id.location_id.id,
                    'state': 'assigned'
                }
                move_id = self.env['stock.move'].create(vals_move)
                vals_move_line = {
                    'picking_id': pick_id.id,
                    'move_id': move_id.id,
                    'product_id': self.product_principal.id,
                    'transfer_manager': self.product_principal.transfer_manager,
                    'product_uom_qty': 1,
                    'qty_done': 0,
                    'lot_id': self.agreement_line_keys.id if self.agreement_line_keys else False,
                    'lot_name': self.agreement_line_keys.name if self.agreement_line_keys else False,
                    'franchisee_id': self.agreement_line_keys.franchisee_id.id if self.agreement_line_keys.franchisee_id else False,
                    'product_uom_id': self.product_principal.uom_id.id,
                    'location_dest_id': pick_id.location_dest_id.id,
                    'location_id': pick_id.location_id.id,
                }
                self.env['stock.move.line'].create(vals_move_line)
                quant = StockQuant.search([('product_id', '=', self.product_principal.id), ('lot_id', '=', self.agreement_line_keys.id)])
                quant.reserved_quantity = 1
            else:
                raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
        else:
            raise ValidationError(
                "No se puede desvincular un equipo en esta linea de contrato ya que no se ha asignado ninguno.")

    def button_create_transfer_order_uninstall(self):
        for line in self:
            line.create_transfer_order_uninstall()