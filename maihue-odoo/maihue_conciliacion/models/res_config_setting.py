# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.osv import osv
from ast import literal_eval

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    
    url_api_conciliacion = fields.Char(string='Url base api para conciliación', default='')
    


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        maihue_conciliacion_url_api_conciliacion = str(ICPSudo.get_param('maihue_conciliacion.url_api_conciliacion', default=''))
             
        
        res.update(
                url_api_conciliacion =maihue_conciliacion_url_api_conciliacion,
                
            )
        
        
        return res    

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('maihue_conciliacion.url_api_conciliacion', self.url_api_conciliacion)
        


