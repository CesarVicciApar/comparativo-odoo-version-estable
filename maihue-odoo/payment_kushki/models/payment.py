# -*- coding: utf-8 -*-
import logging
import requests
from requests.exceptions import HTTPError
from werkzeug import urls
import json

from odoo import _, api, fields, models, tools
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)

class PaymentAcquirerKushki(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('kushki', 'Kushki')], ondelete={'kushki': 'cascade'})
    kushki_secret_key = fields.Char(groups='base.group_user')
    kushki_publishable_key = fields.Char(required_if_provider='kushki', groups='base.group_user')
    kushki_image_url = fields.Char(
        "Checkout Image URL", groups='base.group_user',
        help="A relative or absolute URL pointing to a square image of your "
             "brand or product. As defined in your Stripe profile. See: "
             "https://stripe.com/docs/checkout")
    payment_method_ids = fields.Many2many('agreement.payment.method', string='Metodo de Pago')

    @api.model
    def _get_kushki_api_url(self):
        if self.state == 'test':
            return 'https://api-uat.kushkipagos.com/subscriptions/v1/card/'
        return 'https://api-uat.kushkipagos.com/card/v1/' #TODO set url to production

    def _kushki_request(self, url, data=False, method='POST'):
        self.ensure_one()
        url = urls.url_join(self._get_kushki_api_url(), url)
        headers = {
            'content-type': 'application/json',
            'Public-Merchant-Id': self.sudo().kushki_publishable_key,
            'Private-Merchant-Id': self.sudo().kushki_secret_key
            }
        _logger.info(data)
        data = json.dumps(data)
        resp = requests.request(method, url, data=data, headers=headers)

        if not resp.ok and not (400 <= resp.status_code < 500 and resp.json().get('error', {}).get('code')):
            try:
                resp.raise_for_status()
            except HTTPError:
                _logger.error(resp.text)
                kushki_error = resp.json().get('message', '')
                error_msg = " " + (_("Kushki gave us the following info about the problem: '%s'") % kushki_error)
                raise ValidationError(error_msg)
        if method == 'DELETE':
            return resp
        return resp.json()

    @api.model
    def kushki_s2s_form_process(self, data):
        last4 = data.get('last4', '')
        token = ''
        if not last4:
            # PM was created with a setup intent, need to get last4 digits through
            # yet another call -_-
            acquirer_id = self.env['payment.acquirer'].browse(int(data['acquirer_id']))
            response = acquirer_id._kushki_request('tokens', data=data.get('data_kushki', {}), method='POST')
            _logger.info(response)
            _logger.info("@"*600)
            token = response.get('token', '')
            last4 = data.get('card', 'xxxx')[-4:]

        payment_token = self.env['payment.token'].sudo().create({
            'acquirer_id': int(data['acquirer_id']),
            'partner_id': int(data['partner_id']),
            'name': 'XXXXXXXXXXXX%s' % last4,
            'acquirer_ref': token
        })
        return payment_token

    def _create_kushki_subscription(self, data):
        self.ensure_one()
        response = self._kushki_request('', data=data, method='POST')
        _logger.info(response)
        _logger.info("="*600)
        return response.get('subscriptionId', '')
    
    def _disable_kushki_subscription(self, subscriptionid):
        self.ensure_one()
        response = self._kushki_request(subscriptionid, data={}, method='DELETE')
        _logger.info(response)
        _logger.info("="*600)
        return response


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    kushki_state_token = fields.Selection([('valid', 'Valid'), ('expired', 'Expired')], default='valid')
