from odoo import api, fields, models

class DicomMassiveCrm(models.TransientModel):
    _name = 'dicom.massive.crm'
    _description = 'Dicom Massive Crm'

    @api.model
    def default_get(self, fields_list):
        res = super(DicomMassiveCrm, self).default_get(fields_list)
        lead_ids = self._context.get('active_ids')
        res['lead_ids'] = lead_ids
        return res

    lead_ids = fields.Many2many(
        comodel_name='crm.lead',
        string='Oportunidades'
    )

    def execute_report_dicom(self):
        for lead in self.lead_ids:
            lead.action_request_dicom_report()
