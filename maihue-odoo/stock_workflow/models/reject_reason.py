from odoo import _, api, fields, models

class RejectReason(models.Model):
    _name = "reject.reason"
    _description = "Motivos de Rechazo"
    
    name = fields.Char("Descripción")