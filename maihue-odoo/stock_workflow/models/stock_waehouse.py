from odoo import api, fields, models

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    input_management_ids = fields.Many2many('res.users', 'user_stock_warehouse_in_rel', 'warehouse_id', 'user_id', string='Recepción')
    output_management_ids = fields.Many2many('res.users', 'user_stock_warehouse_out_rel', 'warehouse_id', 'user_id', string='Entrega')
    state_lot = fields.Selection(
        string='Estado por defecto',
        selection=[('stock', 'En bodega'),
                   ('active', 'Activado'),
                   ('transit', 'En transito'),
                   ('workshop', 'En taller')])
    stage_ids = fields.Many2many('equipment.state', string='Estados de Equipos')
    is_workshop = fields.Boolean(string='Es Taller')
    is_partner = fields.Boolean(string='Bodega Clientes')