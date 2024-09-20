# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    def name_get(self):
        res = super(ProductProduct, self).name_get()
        result = []
        if res and isinstance(res, list):
            for group in self:
                name = ''
                for val in res:
                    if group.id == val[0]:
                        name += val[1]
                if group.product_version_id:
                    name += ' ' + group.product_version_id.name
                result.append((group.id, name))
            return result
        else:
            return res

        # def unlink(self):
        #     for product in self:
        #         product_inst = self.env['agreement'].search([('product_instalation', '=', product)])
        #         product_des = self.env['agreement'].search([('product_desinstalation', '=', product)])
        #         product_relac = self.env['product.related'].search([('product_id', 'in', product)])
        #         product_adic = self.env['agreement.extra.charges.related'].search([('product_id', 'in', product)])
        #     if product_inst:
        #         raise UserError("El producto no se puede eliminar, existe una vinculacion con una pantilla para producto instalacion")
        #     if product_des:
        #         raise UserError("El producto no se puede eliminar, existe una vinculacion con una pantilla para producto desinstalacion")
        #     if product_relac:
        #         raise UserError("El producto no se puede eliminar, existe una vinculacion con un producto en productos relacionados")
        #     if product_adic:
        #         raise UserError("El producto no se puede eliminar, existe una vinculacion con una pantilla para servicios adicionales")
        #     return super(ProductProduct, self).unlink()


class Product(models.Model):
    _inherit = "product.template"

    def name_get(self):
        res = super(Product, self).name_get()
        result = []
        if res and isinstance(res, list):
            for group in self:
                name = ''
                for val in res:
                    if group.id == val[0]:
                        name += val[1]
                if group.product_version_id:
                    name += ' ' + group.product_version_id.name
                result.append((group.id, name))
            return result
        else:
            return res

    agreements_ids = fields.Many2many(
        "agreement",
        string="Agreements")

    product_version_id = fields.Many2one('product.version', string='Version')
    product_related_ids = fields.One2many('product.related', 'product_parent_id', string='Related products',
                                          copy=True, auto_join=True)
    name_key = fields.Char(string='Name on Invoice', required=True)
    means_ids = fields.Many2many('means', string="Resources")
    capabilities_ids = fields.Many2many('capabilities', string="Capabilities")
    is_principal = fields.Boolean(string="It is main service", default=False)
    fleet_vehicle = fields.Many2one('fleet.vehicle', string='Vehiculo Flota')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'product_version_id' in vals:
                version = self.env['product.version'].browse(vals['product_version_id'])
                vals['name'] = str(vals['name']) + ' ' + str(version.name)
        return super(Product, self).create(vals_list)

    # def write(self, values):
    #     if 'product_version_id' in values or 'name' in values:
    #         values['name'] = str(values['name']) + ' ' + str(self.product_version_id.name)
    #     return super(Product, self).write(values)

    def unlink(self):
        product_inst = []
        product_des = []
        product_relac = []
        product_adic = []
        product_line = []
        product_princi = []
        for product in self:
            product_inst = self.env['agreement'].search([('product_instalation', '=', product.id)])
            product_des = self.env['agreement'].search([('product_desistalation', '=', product.id)])
            product_relac = self.env['product.related'].search([('product_id', 'in', [product.id])])
            product_adic = self.env['agreement.extra.charges'].search([('product_id', 'in', [product.id])])
            product_line = self.env['agreement.line'].search([('product_id', 'in', [product.id])])
            product_princi = self.env['agreement.line'].search([('product_principal', 'in', [product.id])])
        if product_inst:
            raise UserError(
                "El producto no se puede eliminar, existe una vinculacion con una pantilla para producto instalacion")
        if product_des:
            raise UserError(
                "El producto no se puede eliminar, existe una vinculacion con una pantilla para producto desinstalacion")
        if product_relac:
            raise UserError(
                "El producto no se puede eliminar, existe una vinculacion con un producto en productos relacionados")
        if product_adic:
            raise UserError(
                "El producto no se puede eliminar, existe una vinculacion con una pantilla para servicios adicionales")
        if product_line:
            raise UserError(
                "El producto no se puede eliminar, existe una vinculacion con un contrato para servicio")
        if product_princi:
            raise UserError(
                "El producto no se puede eliminar, existe una vinculacion con un contrato como producto principal")
        return super(Product, self).unlink()


class ProductVersion(models.Model):
    _name = 'product.version'

    name = fields.Char(string='Version', required=True)

class ProductRelated(models.Model):
    _name = 'product.related'

    product_id = fields.Many2one(
        "product.product",
        string="Product")
    product_parent_id = fields.Many2one('product.template', string='Product Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Char(
        string="Description",
        required=True)
    qty = fields.Float(string="Quantity", default=1)
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of measurement",
        required=True)
    is_principal = fields.Boolean(string="It is main service", default=False)
    time_spent = fields.Float('Time/Hours', precision_digits=2)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id.id
