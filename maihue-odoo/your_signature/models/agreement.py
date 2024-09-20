# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Agreement(models.Model):
    _inherit = "agreement"

    # def compute_status_signature(self):
    #     if self.extra_ids:
    #         for record in self.extra_ids:
    #             if record.type_extra.name == 'Contrato':
    #                 #if record.status:
    #                 self.status_signature = record.status

    status_signature = fields.Selection(selection=[("to_sign", "Pend. Firma"), ("signed", "Firmado"), ("cancelled", "Cancelado")],
                              # compute='compute_status_signature',
                                        track_visibility="onchange")

    @api.model
    def create(self, vals):
        res = super(Agreement, self).create(vals)
        if 'extra_ids' in vals:
            for extra in self.extra_ids:
                a = extra.save_pdf()
        return res


    def write(self, vals):
        res = super(Agreement, self).write(vals)
        if 'extra_ids' in vals:
            for extra in self.extra_ids:
                a = extra.save_pdf()
        return res

