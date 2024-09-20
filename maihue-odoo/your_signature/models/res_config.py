# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_firma = fields.Boolean(related="company_id.is_firma", readonly=False)
    api_key = fields.Char(related="company_id.api_key", readonly=False)
    secret = fields.Char(related="company_id.secret", readonly=False)
    firma_state = fields.Selection(related="company_id.firma_state", readonly=False)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']

        params_obj.sudo().set_param('is_firma', self.is_firma)
        params_obj.sudo().set_param('api_key', self.api_key)
        params_obj.sudo().set_param('secret', self.secret)
        params_obj.sudo().set_param('firma_state', self.firma_state)

        return res
