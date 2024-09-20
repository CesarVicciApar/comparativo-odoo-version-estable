# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_form = fields.Boolean(string='Activo')
    api_key = fields.Char(string="Api Contraseña")
    api_user = fields.Char(string="Api Usuario")
    api_url = fields.Char(string="Api URL")
