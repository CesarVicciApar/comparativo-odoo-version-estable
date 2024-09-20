from odoo import api, fields, models

class DicomMassivePartner(models.TransientModel):
    _name = 'dicom.massive.partner'
    _description = 'Dicom Massvie Partner'

    @api.model
    def default_get(self, fields_list):
        res = super(DicomMassivePartner, self).default_get(fields_list)
        partner_ids = self._context.get('active_ids')
        res['partner_ids'] = partner_ids
        return res

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Partners'
    )

    def execute_report_dicom(self):
        for partner in self.partner_ids:
            partner.action_request_dicom_report()
