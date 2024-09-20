from odoo import fields, models
from odoo.exceptions import UserError
from datetime import datetime


class ProductRepairOrderWizard(models.TransientModel):
    _name = "product.repair.order.wizard"
    _description = "Wizard Orden Reparacion"

    def _default_location_workflow(self):
        wh = self.env['stock.warehouse'].search([('is_workshop', '=', True)])
        if wh:
            return wh[0].id
        else:
            return False

    warehouse_id = fields.Many2one('stock.warehouse', string='Bodega', default=_default_location_workflow)
    repair_type = fields.Selection([
        ('repair', 'Orden de Reparacion'),
        ('replacement', 'Orden de Reposicion de piezas'),
        ('dismantling', 'Orden de Desmantelacion'),
        ('change', 'Cambio de Domicilio')
    ], default='repair', tracking=True)

    def _verify_current_repair_order(self):
        repair = self.env['repair.order'].search([('lot_id', '=', self.id), ('state', 'not in', ['done', 'cancel'])])
        if repair:
            return repair
        return False

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

    def action_create_order(self):
        active_id = self.env['stock.production.lot'].browse(self.env.context.get('active_id'))
        stock_quant = self.env['stock.quant'].search([('product_id', '=', active_id.product_id.id), ('lot_id', '=', active_id.id)]).filtered(lambda s: s.location_id.usage == 'internal' and s.quantity > 0)
        #warehouse = self.env['stock.warehouse'].search([('is_workshop', '=', True)])
        location_id = self.warehouse_id.lot_stock_id
        repair = active_id._verify_current_repair_order()
        if not repair:
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
                    'repair_type': self.repair_type,
                    'product_id': active_id.product_id.id,
                    'lot_id': active_id.id,
                    'product_uom': active_id.product_id.uom_id.id,
                    'location_id': location_id.id,
                    'location_source_id': stock_quant.location_id.id,
                    'schedule_date': datetime.today(),
                    'missing_pieces_ids': missing_pieces if missing_pieces else False
                }
                repair_order = self.env['repair.order'].create(vals)
                active_id.repair_order_ids = repair_order.ids
                active_id._compute_repair_order_ids()
                action = self.env["ir.actions.actions"]._for_xml_id("repair.action_repair_order_tree")
                form_view = [(self.env.ref('repair.view_repair_order_form').id, 'form')]
                if 'views' in action:
                    action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
                else:
                    action['views'] = form_view
                action['res_id'] = repair_order.id
                return action
        else:
            raise UserError("Hay una orden de reparacion sin finalizar para este equipo")