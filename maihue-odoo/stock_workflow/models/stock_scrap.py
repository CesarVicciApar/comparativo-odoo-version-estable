from odoo import api, models, fields

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    lots_domain = fields.Many2many('stock.production.lot', string='Domain Lots')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(StockScrap, self)._onchange_product_id()
        if self.product_id:
            lots = self.env['stock.production.lot'].search([('product_id', '=', self.product_id.id)])
            lots_filtered = lots.filtered(lambda s: s.state_equipment in ['out_service', 'outdated'])
            self.lots_domain = lots_filtered.ids
        return res

    def action_validate(self):
        res = super(StockScrap, self).action_validate()
        if self.lot_id:
            stage = self.env['equipment.state'].search([('code', '=', 'discarded')])
            self.lot_id.stage_id = stage.id if stage else self.lot_id.stage_id.id
            self.lot_id.state_equipment = 'discarded'
        return res