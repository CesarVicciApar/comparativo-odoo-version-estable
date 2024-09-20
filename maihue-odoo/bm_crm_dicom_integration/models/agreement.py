from odoo import api, fields, models
from datetime import datetime

class Agreement(models.Model):
    _inherit = 'agreement'

    domain_partner_ids = fields.Many2many('res.partner', string="Dominio clientes", compute='compute_domain_partner_ids')

    @api.depends()
    def compute_domain_partner_ids(self):
        ResPartner = self.env['res.partner']
        for record in self:
            partners = ResPartner.search([('contract', '=', True), ('father', '=', True)])
            list_partner = []
            filter_partners = partners.filtered(lambda s: s.status_exception_dicom == 'exception' or (s.status_dicom == 'approved' and s.contract and not s.black_list and s.type_contrib.id == self.type_contrib_partner.id)) if not record.is_template else partners.filtered(lambda s: s.status_exception_dicom == 'exception' or (s.status_dicom == 'approved' and s.contract and not s.black_list and s.type_contrib.id == self.type_contrib.id))
            for partner in filter_partners:
                list_partner.append(partner.id)
            if list_partner:
                record.domain_partner_ids = list_partner
            else:
                record.domain_partner_ids = False
