# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, SUPERUSER_ID, _
from logging import getLogger


class HelpdeskVisita(models.Model):
    _name = "helpdesk.visita"
    _description = "Visitas Comerciales"

    name = fields.Char('Visita', size=30)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    planned_date_begin = fields.Datetime("Fecha Inicio", tracking=True, task_dependency_tracking=True)
    planned_date_end = fields.Datetime("Fecha Fin", tracking=True, task_dependency_tracking=True)
    visita_line = fields.One2many('helpdesk.visita.line', 'visita_id', string='Lineas Visitas', copy=True,
                                 auto_join=True)

class HelpdeskVisitaLine(models.Model):
    _name = "helpdesk.visita.line"
    _description = "Linea Visitas Comerciales"
    _rec_name = 'task_id'

    visita_id = fields.Many2one('helpdesk.visita', string='Referencia Visita', required=True, ondelete='cascade', index=True,
                               copy=False)
    task_id = fields.Many2one('project.task', string='Orden de Servicio', required=True, ondelete='cascade', index=True,
                              copy=False)
    project_id = fields.Many2one(related='task_id.project_id', string='Proyecto', track_visibility="onchange")

