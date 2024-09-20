from odoo import api, fields, models


class RepairLineType(models.Model):
    _name = 'repair.line.type'

    name = fields.Char('Descripcion')
    type = fields.Selection([('add', 'Añadir'),
                             ('remove', 'Eliminar')], string="Tipo")
    # repair_type = fields.Selection([
    #     ('repair', 'Orden de Reparacion'),
    #     ('replacement', 'Orden de Reposicion de piezas'),
    #     ('dismantling', 'Orden de Desmantelacion'),
    #     ('change', 'Cambio de Domicilio')
    # ])
    warehouse_id = fields.Many2one('stock.warehouse', 'Bodega')
    location_id = fields.Many2one('stock.location', 'Ubicacion Origen')
    location_dest_id = fields.Many2one('stock.location', 'Ubicacion Destino')
    notes = fields.Text(string="Notes")