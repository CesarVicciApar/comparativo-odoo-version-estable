# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_firma = fields.Boolean(string='Activo')
    api_key = fields.Char(string="Api Key")
    secret = fields.Char(string="Secret")
    firma_state = fields.Selection([('test', 'Testing'), ('prod', 'Produccion')], string="Estatus", default='test')
