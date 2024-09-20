from odoo import api, fields, models

class StockReadyConfirm(models.TransientModel):
    _name = 'stock.ready.confirm'
    
    def action_confirm(self):
        picking = self.env['stock.picking'].search([('id', '=', self.env.context.get('active_id'))])
        if picking:
            picking.state = 'ready'