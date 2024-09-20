# coding: utf-8
from odoo import api, fields, models


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dicom_active = fields.Boolean(related='company_id.dicom_active', readonly=False)
    dicom_user = fields.Char(related='company_id.dicom_user', readonly=False)
    dicom_password = fields.Char(related='company_id.dicom_password', readonly=False)
    dicom_url = fields.Char(related='company_id.dicom_url', readonly=False)
    dicom_message = fields.Text(related='company_id.dicom_message', readonly=False)
    status = fields.Selection(string='Servicio', related='company_id.status', readonly=False)
    frequency = fields.Integer(string='Dias', related='company_id.frequency', readonly=False)
    approved = fields.Integer(string='Aprobado', related='company_id.approved', readonly=False)
    check = fields.Integer(string='Revisar', related='company_id.check', readonly=False)

    @api.onchange('status', 'dicom_active')
    def onchange_partners_status_dicom(self):
        # partners = self.env['res.partner'].search([])
        # for partner in partners:
        #     partner.status = self.status
        #     partner.dicom_active = self.dicom_active
        da = 'true' if self.dicom_active else 'false'
        self.env.cr.execute("""UPDATE res_partner SET status = '%s', dicom_active = '%s';""" % (self.status, da))

