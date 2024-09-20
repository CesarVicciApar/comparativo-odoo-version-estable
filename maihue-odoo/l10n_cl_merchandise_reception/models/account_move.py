from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons.l10n_cl_merchandise_reception.models.l10n_cl_edi_util import InvalidToken
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_cl_dte_acceptation_merch_status = fields.Selection([
        ('pending', 'Pending'),
        ('claimed', 'Claimed'),
        ('accepted', 'Accepted'),
    ], string='Estado de Aceptación Recibo de Mercadería', copy=False)

    def l10n_cl_accept_document_erm(self):
        if not self.l10n_latam_document_type_id._is_doc_type_acceptance():
            raise UserError(_('The document type with code %s cannot be accepted') %
                            self.l10n_latam_document_type_id.code)
        if self.company_id.l10n_cl_dte_service_provider == 'SIITEST':
            self._l10n_cl_send_dte_reception_status('accepted')
            self.l10n_cl_dte_acceptation_merch_status = 'accepted'
            self.message_post(body=_('Claim status was not sending to SII. This feature is not available in '
                                     'certification/test mode'))
            return None
        try:
            response = self._send_sii_claim_response(
                self.company_id.l10n_cl_dte_service_provider, self.partner_id.vat,
                self.company_id._get_digital_signature(user_id=self.env.user.id), self.l10n_latam_document_type_id.code,
                self.l10n_latam_document_number, 'ERM')
        except InvalidToken:
            digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
            digital_signature.last_token = None
            return self.l10n_cl_accept_document_erm()
        if not response:
            return None

        try:
            cod_response = response['codResp']
        except Exception as error:
            _logger.error(error)
            self.message_post(body=_('Exception error parsing the response: %s') % response)
            return None
        if cod_response in [0, 1]:
            self.l10n_cl_dte_acceptation_merch_status = 'accepted'
            self._l10n_cl_send_dte_reception_status('accepted')
            msg = _('Document acceptance was accepted with response:') + '<br/> %s' % response
        else:
            msg = _('Document acceptance failed with response:') + '<br/> %s' % response
        self.message_post(body=msg)