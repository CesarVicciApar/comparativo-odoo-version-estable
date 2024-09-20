from odoo import api, fields, models


CODE = [('new', 'Nuevo'),
        ('new_dismantling', 'Nuevo - Desmantelado'),
        ('new_rearmed', 'Nuevo - Rearmado'),
        ('new_missing_pieces', 'Nuevo Faltan Piezas'),
        ('active', 'Activado'),
        ('domi', 'Cambio de domicilio en curso'),
        ('check', 'Por Revisar'),
        ('reviewed', 'Revisado'),
        ('xrefact', 'Por Refaccionar'),
        ('in_refact', 'En Refaccion'),
        ('refact', 'Refaccionado'),
        ('xrefact_missing_pieces', 'Por Refaccionar Faltan Piezas'),
        ('out_service', 'Fuera de Servicio'),
        ('outdated', 'Obsoleto'),
        ('discarded', 'Desechado')]

class EquipmentState(models.Model):
    _name = 'equipment.state'
    _description = 'Estados de Equipos'

    name = fields.Char('Descripcion')
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    code = fields.Selection(string='Codigo', selection=CODE, default='new')


