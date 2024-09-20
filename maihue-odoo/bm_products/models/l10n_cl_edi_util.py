from odoo import api, fields, models, _
from zeep import Client, Settings


class L10nClEdiUtilMixin(models.AbstractModel):
    _inherit = 'l10n_cl.edi.util'

    def _get_dte_claim(self, mode, company_vat, digital_signature, document_type_code, document_number):
        digital_signature.last_token = False
        token = self._get_token(mode, digital_signature)
        if token is None:
            self._report_connection_err(_('Token cannot be generated. Please try again'))
            return False
        settings = Settings(strict=False, extra_http_headers={'Cookie': 'TOKEN=' + token})
        return self._get_dte_claim_ws(mode, settings, company_vat, document_type_code, document_number)
