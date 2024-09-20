from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    
    def action_change_lot_id(self):
        action = {
                'name': _('Change Serial Number'),
                'view_mode': 'form',
                'res_model': 'exchange.serial.number',
                'view_id': self.env.ref('stock_exchange_product_lot.exchange_serial_number_view_form').id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new'
            }
        return action