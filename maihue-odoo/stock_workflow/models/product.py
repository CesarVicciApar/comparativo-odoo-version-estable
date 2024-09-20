from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    transfer_manager = fields.Boolean(string='Aplica gestión de transferencias')

    @api.onchange('transfer_manager')
    def onchange_transfer_manager(self):
        pickings = self.env['stock.picking'].search([('state', 'in', ['draft'])])
        product = self.env['product.product'].search([('product_tmpl_id', '=', self.id.origin)])
        if pickings:
            for picking in pickings:
                for line in picking.move_ids_without_package.filtered(lambda l: l.product_id.id in product.ids):
                    line.transfer_manager = self.transfer_manager

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.constrains('default_code')
    def _check_default_code_variants(self):
        for record in self.search([]):
            if record.default_code:
                if any(record.default_code == rec.default_code for rec in self.search([]).filtered(lambda s: s.id != record.id)):
                    raise ValidationError('Existe otro producto con el mismo SKU')