from odoo import api, fields, models

class SignatureType(models.Model):
    _name = 'signature.type'
    _description = 'Tipo de Firma'

    name = fields.Char('Descripcion')
    code = fields.Char('Codigo')
    type = fields.Selection([('digital', 'Digital'), ('fisica', 'Fisica')], string='Tipo')

