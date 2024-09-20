from odoo import api, fields, models 

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_franchisee = fields.Boolean(string='Franquiciado')
    default_stock_location_id = fields.Many2one('stock.location', string='Ubicacion predeterminada')
