# coding: utf-8
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    dicom_active = fields.Boolean()
    dicom_user = fields.Char()
    dicom_password = fields.Char()
    dicom_url = fields.Char()
    dicom_message = fields.Text()
    status = fields.Selection(string='Servicio', selection=[('qa_local', 'QA'), ('qa', 'Testing'), ('prod', 'Produccion')], default='qa')
    frequency = fields.Integer(string='Dias')
    approved = fields.Integer(string='Aprobado')
    check = fields.Integer(string='Revisar')