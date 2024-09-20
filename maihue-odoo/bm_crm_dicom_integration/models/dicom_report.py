# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, tools


class DicomReport(models.Model):
    _name = 'dicom.report'
    _description = 'Report Dicom'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner', required=True, string="Client", ondelete="restrict")
    date = fields.Datetime(string="Date", default=lambda self: fields.Datetime.now())
    score = fields.Integer(string="Score Dicom")
    file_report_attachment = fields.Many2many('ir.attachment', string="File")
    file_report = fields.Binary(string="File")
    file_name = fields.Char(string='Filename', store=True)
    user_id = fields.Many2one('res.users', string="User", tracking=True, default=lambda self: self.env.user)
    history_dicom_id = fields.Many2one('history.request.dicom', string='Historial')
    service_type = fields.Selection(string='Informe', selection=[('commercial', 'Empresarial'), ('platinum', 'Platinum360')])