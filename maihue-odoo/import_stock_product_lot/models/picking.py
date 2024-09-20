from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'


class StockPicking(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _get_warehouse(self):
        # company_user = self.env.company
        for record in self:
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', record.location_id.id)], limit=1)
            record.warehouse_id = warehouse.id
            record.write({'warehouse_name': warehouse.id})
            # self.warehouse_name = warehouse.id
            # self.write({'warehouse_name': self.warehouse_id.id})
        #return self

    warehouse_id = fields.Many2one('stock.warehouse', compute='_get_warehouse', string='Bodega')
    warehouse_name = fields.Many2one('stock.warehouse', string='Bodega store')
    # warehouse_id = fields.Many2many('stock.warehouse', 'stock_warehouse_rel', 'warehouse_id',
    #                                          'quant_id', track_visibility="onchange", compute='_get_warehouse',
    #                                          string='Bodega')
    
    
    # def action_import_lot_id(self):
    #     action = {
    #             'name': _('Import Serial Number'),
    #             'view_mode': 'form',
    #             'res_model': 'import.serial.number',
    #             'view_id': self.env.ref('import_stock_product_lot.import_serial_number_view_form').id,
    #             'type': 'ir.actions.act_window',
    #             'res_id': self.id,
    #             'target': 'new'
    #         }
    #     return action