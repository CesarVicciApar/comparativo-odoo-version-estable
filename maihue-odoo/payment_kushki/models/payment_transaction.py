# -*- coding: utf-8 -*-
import logging
from odoo import _, api, fields, models, tools
from odoo.tools.float_utils import float_round
import pprint

_logger = logging.getLogger(__name__)



class PaymentTransactionKushki(models.Model):
    _inherit = 'payment.transaction'

    kushki_payment_intent = fields.Char(string='Kushki Payment Intent ID', readonly=True)
    kushki_payment_intent_secret = fields.Char(string='Kushki Payment Intent Secret', readonly=True)

    def _kushki_create_payment_intent(self, acquirer_ref=None, email=None):
        charge_params = {
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": int(self.amount),
                "ice": 0,
                "iva": 0,
                "currency": self.currency_id.name
            },
            "metadata": {
                "contractID": self.reference
            },
            "fullResponse": True
            }

        _logger.info('_kushki_create_payment_intent: Sending values to stripe, values:\n%s', pprint.pformat(charge_params))
        res = self.acquirer_id._kushki_request(acquirer_ref, charge_params)
        if res.get('charges') and res.get('charges').get('total_count'):
            res = res.get('charges').get('data')[0]
        _logger.info('_kushki_create_payment_intent: Values received:\n%s', pprint.pformat(res))
        return res
    
    def _kushki_s2s_validate_tree(self, tree):
        self.ensure_one()
        if self.state not in ("draft", "pending"):
            _logger.info('Kushki: trying to validate an already validated tx (ref %s)', self.reference)
            return True
        status = tree.get('ticketNumber', False)
        if status:
            datails = tree.get('details', {})
            tx_id = datails.get('transactionId')
            tx_secret = datails.get("processorId")
            vals = {
                "date": fields.datetime.now(),
                "acquirer_reference": tx_id,
                "kushki_payment_intent": tx_id,
                "kushki_payment_intent_secret": tx_secret
            }
            self.write(vals)
            self._set_transaction_done()
            self.execute_callback()

            return True
        else:
            error = tree.get("message")
            self._set_transaction_error(error)
            return False


    def kushki_s2s_do_transaction(self, **kwargs):
        if self.callback_model_id.model == 'sale.subscription':
            acquirer_ref = self.env['sale.subscription'].browse(self.callback_res_id).kushki_subscription_token
        self.ensure_one()
        result = self._kushki_create_payment_intent(acquirer_ref=acquirer_ref, email=self.partner_email)
        return self._kushki_s2s_validate_tree(result)