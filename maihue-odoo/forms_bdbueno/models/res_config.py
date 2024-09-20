# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_form = fields.Boolean(related="company_id.is_form", readonly=False)
    api_key = fields.Char(string="Api Contraseña")
    api_user = fields.Char(string="Api Usuario")
    api_url = fields.Char(string="Api URL")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']

        params_obj.sudo().set_param('is_form', self.is_form)
        params_obj.sudo().set_param('api_key', self.api_key)
        params_obj.sudo().set_param('api_user', self.api_user)
        params_obj.sudo().set_param('api_url', self.api_url)

        return res
