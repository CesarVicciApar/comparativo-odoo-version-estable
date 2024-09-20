from odoo import api, fields, models 
from datetime import datetime
class HistoryRequestDicom(models.Model):
    _name = 'history.request.dicom'
    _description = 'History Request Dicom'
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='Usuario')
    partner_id = fields.Many2one('res.partner', 'Empresa')
    date = fields.Date('Date', default=fields.Date.context_today)
    request = fields.Text(string="Request")

    def name_get(self):
        result = []
        for record in self:
            name = record.partner_id.name + ' (' + datetime.strftime(record.date, '%d/%m/%Y') + ')'
            result.append((record.id, name))
        return result