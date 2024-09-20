
from odoo import api, fields, models

class InvoiceLog(models.Model):
    _name = 'invoice.log'
    _description = 'Invoice Log'

    name = fields.Char('Referencia')
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)
    observations = fields.Char(string="Obsevaciones")
    invoice_gen_queue_id = fields.Many2one('invoice.generation.queue', 'Cola')

