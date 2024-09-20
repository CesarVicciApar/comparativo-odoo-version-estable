from odoo import api, fields, models

class StockLocation(models.Model):
    _inherit = 'stock.location'

    input_management_ids = fields.Many2many('res.users', 'user_stock_location_in_rel', 'location_id', 'user_id', string='Recepción')
    output_management_ids = fields.Many2many('res.users', 'user_stock_location_out_rel', 'location_id', 'user_id', string='Entrega')
    stage_ids = fields.Many2many('equipment.state', string='Estados de Equipos')
    trf_without_ro = fields.Boolean(string='Permitir transferencias a taller sin OR')