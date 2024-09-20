from odoo import http
from odoo.http import request, route
from datetime import date, datetime
from werkzeug.utils import redirect
from odoo.tools.translate import _
from odoo.exceptions import UserError, AccessError, MissingError
from stdnum import get_cc_module
import requests
import json

from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager, CustomerPortal

url_kushki = "http://api-uat.kushkipagos.com"

class CustomerPortalPaymentMethods(CustomerPortal):

    def _get_domain_search(self, partner):
        return [
            ('partner_id.id', 'in', [partner.id, partner.commercial_partner_id.id]),
        ]

    def _prepare_portal_layout_values(self):
        """ Add payment method partner to main account page """
        values = super(CustomerPortalPaymentMethods, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values['paymentmethod_count'] = request.env['payment.method.partner'].search_count(self._get_domain_search(partner))
        values['contracts_count'] = request.env['agreement'].search_count(self._get_domain_search(partner))
        return values

    @http.route('/my/paymentmethods', type='http', auth="user", website=True)
    def my_paymentmethods(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PaymentMethods = request.env['payment.method.partner'].sudo()
        Agreement = request.env['agreement'].sudo()
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        parameter_url = request.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')])

        domain = self._get_domain_search(partner)

        # pager
        paymentmethod_count = PaymentMethods.search_count(domain)
        pager = portal_pager(
            url="/my/paymentmethods",
            url_args={},
            total=paymentmethod_count,
            page=page,
            step=self._items_per_page
        )

        paymentspartner = PaymentMethods.search(domain, limit=self._items_per_page, offset=pager['offset'])
        contractspartner = Agreement.search(domain, limit=self._items_per_page, offset=pager['offset'])
        # request.session['my_subscriptions_history'] = accounts.ids[:100]
        typePayment = contractspartner.mapped("payment_method")
        subscription = 'all'
        for tp in typePayment:
            if tp.code == 'pac':
                subscription = 'all'
                break
            if tp.code == 'pat':
                subscription = 'credit'

        values.update({
            'type_subscription': subscription,
            'payment_acquirer': PaymentAcquirer,
            'paymentspartners': paymentspartner,
            'contracts': contractspartner,
            'base_url': parameter_url.value,
            'page_name': 'paymentmethods',
            'pager': pager,
            'default_url': '/my/paymentmethods',
        })
        return request.render("payment_kushki.portal_my_payment_methods_partner", values)

    @http.route('/my/contracts', type='http', auth="user", website=True)
    def my_contracts(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        contracts = request.env['agreement'].sudo()
        payment_partner = request.env['payment.method.partner'].sudo()
        partner = request.env.user.partner_id
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        parameter_url = request.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')])
        domain = self._get_domain_search(partner)
        contracts_count = contracts.search_count(domain)

        pager = portal_pager(
            url="/my/contracts",
            url_args={},
            total=contracts_count,
            page=page,
            step=self._items_per_page
        )
        contracts_partner = contracts.search(domain, limit=self._items_per_page, offset=pager['offset'])
        type = contracts_partner.mapped("payment_method")
        #domain.append([''])
        paymentspartner = payment_partner.search(domain, limit=self._items_per_page, offset=pager['offset'])

        # headers = {
        #     'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
        #     'content-type': "application/json"
        # }
        # for contract in contracts_partner:
        #     if contract.card_number.type_subscription == 'webpay':
        #         response = requests.get(url_kushki + "/subscriptions/v1/card/search/" + contract.card_number.token_card, headers=headers)
        #         response_dict = response.json()
        #         if response.status_code != 200:
        #             raise UserError((response_dict['code']), (response_dict['message']))
        #         if 'maskedCardNumber' in response_dict:
        #             contract.card_number.card_number = response_dict['maskedCardNumber']
        #             contract.card_number.brand = response_dict['paymentBrand']
        #             contract.card_number.card_type = response_dict['cardType']
        #         elif 'lastFourDigits' in response_dict and 'paymentBrand' in response_dict:
        #             contract.card_number.card_number = 'XXXXXXXXXXXXXXXX' + response_dict['lastFourDigits']
        #             contract.card_number.brand = response_dict['paymentBrand']
        #     else:
        #         pass
        paymentspartner_filter = paymentspartner.filtered(lambda s: s.card_type == 'credit')
        values.update({
            'payment_acquirer': PaymentAcquirer,
            'contracts_partner': contracts_partner,
            'payments_partner': paymentspartner,
            'payments_partner_filter': paymentspartner_filter,
            'countpayments_partner': len(paymentspartner),
            'base_url': parameter_url.value,
            'page_name': 'contracts',
            'pager': pager,
            'default_url': '/my/contracts',
        })

        return request.render(
            "payment_kushki.portal_my_contracts", values)

class PortalPaymentMethods(http.Controller):

    def _get_page_view_values(self, document, access_token, values, session_history, no_breadcrumbs, **kwargs):
        if access_token:
            # if no_breadcrumbs = False -> force breadcrumbs even if access_token to `invite` users to register if they click on it
            values['no_breadcrumbs'] = no_breadcrumbs
            values['access_token'] = access_token
            values['token'] = access_token  # for portal chatter

        # Those are used notably whenever the payment form is implied in the portal.
        if kwargs.get('error'):
            values['error'] = kwargs['error']
        if kwargs.get('warning'):
            values['warning'] = kwargs['warning']
        if kwargs.get('success'):
            values['success'] = kwargs['success']
        # Email token for posting messages in portal view with identified author
        if kwargs.get('pid'):
            values['pid'] = kwargs['pid']
        if kwargs.get('hash'):
            values['hash'] = kwargs['hash']

        history = request.session.get(session_history, [])
        values.update(get_records_pager(history, document))

        return values

    def _paymentmethod_get_page_view_values(self, payment, access_token, **kwargs):
        values = {
            'page_name': 'invoice',
            'payment_method': payment,
        }
        return self._get_page_view_values(payment, access_token, values, 'my_invoices_history', False, **kwargs)

    @http.route(['/my/paymentmethods/<int:paymentmethod_id>'], type='http', auth="public", website=True)
    def portal_my_payment_method_detail(self, paymentmethod_id, access_token=None, report_type=None, download=False, **kw):
        try:
            payment_method = self._document_check_access('payment.method.partner', paymentmethod_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=payment_method, report_type=report_type, report_ref='account.account_invoices',
                                     download=download)

        values = self._invoice_get_page_view_values(payment_method, access_token, **kw)
        # acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
        #     values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual,
        #                                                                  invoice_sudo.currency_id, country_id)

        return request.render("account.portal_invoice_page", values)

class KushkiCajita(http.Controller):

    @http.route('/kushki_paymentmethods', type='http', auth='user', csrf=True, website=True)
    def kushki_paymentmethods(self, **post):
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        partner = request.env.user.partner_id
        KushkiLog = request.env['kushki.log'].sudo()
        url = '/payment/success'
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        fname, lname = post['username'].split(' ')
        number = post['codigo'] + post['phone_credit']
        subscription = {
            "token": post['subscriptionToken'],
            "planName": post['document_number'],
            "periodicity": "custom",
            "contactDetails": {
                "documentType": "RUT",
                "documentNumber": post['document_number'],
                "email": post['email'],
                "firstName": fname,
                "lastName": lname,
                "phoneNumber": number,
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "startDate": str_today
        }
        headers = {
            'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
            'content-type': "application/json"
        }
        response = requests.post(url_kushki + "/subscriptions/v1/card", data=json.dumps(subscription), headers=headers)
        response_dict = response.json()
        if response.status_code != 201:
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'createSubscription',
                'error_code': response_dict['code'],
                'description_error': response_dict['message'],
                'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError((response_dict['code']) + '\n' + (response_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'method_name': 'createSubscription',
            'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
        })
        subscriptionId = response_dict['subscriptionId']
        response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId,
                                             headers=headers)
        response_subscription_dict = response_subscription.json()

        if response_subscription.status_code != 200:
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'error_code': response_subscription_dict['code'],
                'description_error': response_subscription_dict['message'],
                'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError((response_subscription_dict['code']) + '\n' + (response_subscription_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'method_name': 'getSubscription',
            'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
        })
        return request.redirect(url + '?subscriptionId=%s' % subscriptionId)

    @http.route('/kushki_contract_paymentmethods', type='http', auth='user', csrf=True, website=True)
    def kushki_contract_paymentmethods(self, **post):
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        partner = request.env.user.partner_id
        AgreementPaymentMethods = request.env['agreement.payment.method'].sudo()
        KushkiLog = request.env['kushki.log'].sudo()
        Agreement = request.env['agreement'].sudo()
        url = '/payment/success'
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        fname, lname = post['username'].split(' ')
        number = post['codigo'] + post['phone_credit']
        subscription = {
            "token": post['subscriptionToken'],
            "planName": post['document_number'],
            "periodicity": "custom",
            "contactDetails": {
                "documentType": "RUT",
                "documentNumber": post['document_number'],
                "email": post['email'],
                "firstName": fname,
                "lastName": lname,
                "phoneNumber": number
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "startDate": str_today
        }
        headers = {
            'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
            'content-type': "application/json"
        }
        response = requests.post(url_kushki + "/subscriptions/v1/card", data=json.dumps(subscription), headers=headers)
        response_dict = response.json()
        if response.status_code != 201:
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'createSubscription',
                'error_code': response_dict['code'],
                'description_error': response_dict['message'],
                'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError((response_dict['code']), (response_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'method_name': 'createSubscription',
            'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
        })
        subscriptionId = response_dict['subscriptionId']
        response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId,
                                             headers=headers)
        response_subscription_dict = response_subscription.json()

        if response_subscription.status_code != 200:
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'error_code': response_subscription_dict['code'],
                'description_error': response_subscription_dict['message'],
                'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError((response_subscription_dict['code']), (response_subscription_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'method_name': 'getSubscription',
            'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
        })
        search_agreement = Agreement.search([('id', '=', post['creditContractId'])])

        return request.redirect(url + '?subscriptionId=%s&contrac_id=%s' % (subscriptionId, search_agreement.id))

    @http.route('/kushki_webpay_paymentmethods', type='http', auth='user', csrf=True, website=True)
    def kushki_webpay_paymentmethods(self, **post):
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        KushkiLog = request.env['kushki.log'].sudo()
        url = '/my/paymentmethods'
        headers = {
            'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
            'content-type': "application/json"
        }
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        number = post['codigo_webpay'] + post['phone_webpay']
        subscription = {
            "token": post['webpaySubsctiptionToken'],
            "planName": post['document_number_webpay'],
            "periodicity": "custom",
            "contactDetails": {
                "documentNumber": post['document_number_webpay'],
                "email": post['mail'],
                "firstName": post['firstname'],
                "lastName": post['lastname'],
                "phoneNumber": number
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "startDate": str_today
        }
        response = requests.post(url_kushki + "/subscriptions/v1/card-async/init", data=json.dumps(subscription), headers=headers)
        response_dict = response.json()
        if response.status_code != 201:
            KushkiLog.create({
                'user_id': request.env.user.id,
                'method_name': 'createSubscriptionCardAsync',
                'error_code': response_dict['code'],
                'description_error': response_dict['message'],
                'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError('{} \n {}'.format(response_dict['code'], response_dict['message']))
        KushkiLog.create({
            'user_id': request.env.user.id,
            'method_name': 'createSubscriptionCardAsync',
            'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
        })
        subscriptionId = response_dict['subscriptionId']
        redirectUrl = response_dict['redirectUrl']
        response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId, headers=headers)
        response_subscription_dict = response_subscription.json()
        if response_subscription.status_code != 200:
            KushkiLog.create({
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'error_code': response_subscription_dict['code'],
                'description_error': response_subscription_dict['message'],
                'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError('{} \n {}'.format(response_subscription_dict['code'], response_subscription_dict['message']))
        KushkiLog.create({
            'user_id': request.env.user.id,
            'method_name': 'getSubscription',
            'answer': json.dumps(response_subscription.text, indent=4).replace('\n', '<br/>'),
        })
        return redirect(redirectUrl)

    @http.route('/kushki_webpay_contract_paymentmethods', type='http', auth='user', csrf=True, website=True)
    def kushki_webpay_contract_paymentmethods(self, **post):
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        partner = request.env.user.partner_id
        PaymentMethods = request.env['payment.method.partner'].sudo()
        AgreementPaymentMethods = request.env['agreement.payment.method'].sudo()
        pac = AgreementPaymentMethods.search([('code', '=', 'pac')])
        Agreement = request.env['agreement'].sudo()
        KushkiLog = request.env['kushki.log'].sudo()
        url = '/my/paymentmethods'
        headers = {
            'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
            'content-type': "application/json"
        }
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        number = post['codigo_webpay'] + post['phone_webpay']
        subscription = {
            "token": post['webpaySubsctiptionToken'],
            "planName": post['document_number_webpay'],
            "periodicity": "custom",
            "contactDetails": {
                "documentNumber": post['document_number_webpay'],
                "email": post['mail'],
                "firstName": post['firstname'],
                "lastName": post['lastname'],
                "phoneNumber": number
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "startDate": str_today
        }
        response = requests.post(url_kushki + "/subscriptions/v1/card-async/init", data=json.dumps(subscription),
                                 headers=headers)
        response_dict = response.json()
        if response.status_code != 201:
            KushkiLog.create({
                'user_id': request.env.user.id,
                'method_name': 'createSubscriptionCardAsync',
                'error_code': response_dict['code'],
                'description_error': response_dict['message'],
                'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError('{} \n {}'.format(response_dict['code'], response_dict['message']))
        KushkiLog.create({
            'user_id': request.env.user.id,
            'method_name': 'createSubscriptionCardAsync',
            'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
        })
        subscriptionId = response_dict['subscriptionId']
        redirectUrl = response_dict['redirectUrl']
        response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId,
                                             headers=headers)
        response_subscription_dict = response_subscription.json()
        if response_subscription.status_code != 200:
            KushkiLog.create({
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'error_code': response_subscription_dict['code'],
                'description_error': response_subscription_dict['message'],
                'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError(
                '{} \n {}'.format(response_subscription_dict['code'], response_subscription_dict['message']))
        KushkiLog.create({
            'user_id': request.env.user.id,
            'method_name': 'getSubscription',
            'answer': json.dumps(response_subscription.text, indent=4).replace('\n', '<br/>'),
        })
        contact = response_subscription_dict['contactDetails']
        # Payment = PaymentMethods.create({
        #     'date_subscription': today,
        #     'partner_id': partner.id,
        #     'partner_id_vat': partner.vat,
        #     'type_subscription': 'webpay',
        #     'acquirer_id': PaymentAcquirer.id,
        #     'type_subscription_contract': pac.id if pac else False,
        #     'token_card': subscriptionId,
        #     'name': contact['firstName'],
        #     'last_name': contact['lastName'],
        #     'phone_number': contact['phoneNumber'],
        #     'document_number': contact['documentNumber'],
        #     'email': contact['email'],
        # })
        # search_agreement = Agreement.search([('id', '=', post['webpayContractId'])])
        # search_agreement.write({
        #     'card_number': Payment.id
        # })
        return redirect(redirectUrl)


    @http.route('/kushki_paymentmethods/cancel', type='http', auth='user', csrf=True, website=True)
    def kushki_paymentmethods_cancel(self, **post):
        url = '/my/paymentmethods'
        #headers = {'Private-Merchant-Id': 'be7c9a71e9d842fda2fe42b84ead2577', 'content-type': "application/json"}
        subscriptionId = post['subscription']
        # response = requests.delete(url_kushki + "/subscriptions/v1/card/"+subscriptionId, headers=headers)
        # if response.status_code != 204:
        #     re = response.json()
        #     raise UserError('{} \n {}'.format(re['code'], re['message']))
        payment_partner = request.env['payment.method.partner'].sudo()
        partner = request.env.user.partner_id
        domain = [('token_card', '=', subscriptionId), ('partner_id', '=', partner.id)]
        payment_search = payment_partner.search(domain)
        payment_search.write({
            'state': 'request'
        })
        return request.redirect(url)

    @http.route('/kushki_paymentmethods/update', type='http', auth='user', csrf=True, website=True)
    def kushki_paymentmethods_update(self, **post):
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        KushkiLog = request.env['kushki.log'].sudo()
        partner = request.env.user.partner_id
        url = '/my/paymentmethods'
        headers = {
            'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
            'content-type': "application/json"
        }
        subscriptionId = post['subscriptionToken']
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        number = post['codigo'] + post['phone_credit']
        fname, lname = post['username'].split(' ')
        subscription = {
            "planName": post['document_number'],
            "periodicity": "custom",
            "contactDetails": {
                "documentType": "RUT",
                "documentNumber": post['document_number'],
                "email": post['email'],
                "firstName": fname,
                "lastName": lname,
                "phoneNumber": number,
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "language": "es",
            "startDate": str_today
        }

        response = requests.patch(url_kushki + "/subscriptions/v1/card/" + subscriptionId, data=json.dumps(subscription), headers=headers)
        response_subscription_dict = response.request.body.json()
        if response.status_code != 204:
            re = response.json()
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'error_code': response_subscription_dict['code'],
                'description_error': response_subscription_dict['message'],
                'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError('{} \n {}'.format(re['code'], re['message']))
        payment_partner = request.env['payment.method.partner'].sudo()
        partner = request.env.user.partner_id
        domain = [('token_card', '=', subscriptionId), ('partner_id', '=', partner.id)]
        payment_search = payment_partner.search(domain)
        return request.redirect(url)

    @http.route('/kushki_webpay_paymentmethods/update', type='http', auth='user', csrf=True, website=True)
    def kushki_webpay_paymentmethods_update(self, **post):
        url = '/my/paymentmethods'
        headers = {'Private-Merchant-Id': 'be7c9a71e9d842fda2fe42b84ead2577', 'content-type': "application/json"}
        subscriptionId = post['subscription']
        response = requests.delete(url_kushki + "/subscriptions/v1/card/"+subscriptionId, headers=headers)
        if response.status_code != 204:
            re = response.json()
            raise UserError('{} \n {}'.format(re['code'], re['message']))
        payment_partner = request.env['payment.method.partner'].sudo()
        partner = request.env.user.partner_id
        domain = [('token_card', '=', subscriptionId), ('partner_id', '=', partner.id)]
        payment_search = payment_partner.search(domain)


    ##################################### ASSOCIATE CONTRACT #####################################
    @http.route('/associate', type='http', auth='user', csrf=True, website=True)
    def assciate_contracts_payment(self, **post):
        url = '/my/contracts'
        subscriptionId = post['selectedSubscription']
        contract = post['contractList']
        payment_partner = request.env['payment.method.partner'].sudo()
        agreement = request.env['agreement'].sudo()
        partner = request.env.user.partner_id
        domain = [('token_card', '=', subscriptionId), ('partner_id', '=', partner.id)]
        payment_search = payment_partner.search(domain)
        contract_search = agreement.search([('id', '=', int(contract)),('is_template', '=', False)])
        contract_ids = []
        if payment_search:
            if payment_search.contract_ids:
                for cont in payment_search.contract_ids:
                    contract_ids.append(cont.id)
        contract_ids.append(contract_search.id)
        payment_search.write({
            'contract_ids': [(6, 0, contract_ids)]
        })
        contract_search.onchange_card_number()
        return request.redirect(url)

    ##################################### ASSOCIATE CARD TO CONTRACT #####################################
    @http.route('/asociate_payment', type='http', auth='user', csrf=True, website=True)
    def assciate_contracts(self, **post):
        url = '/my/contracts'
        contractId = post['selectedContract']
        paymentId = post['paymentlist']
        payment_partner = request.env['payment.method.partner'].sudo()
        agreement = request.env['agreement'].sudo()
        #partner = request.env.user.partner_id
        domain = [('id', '=', paymentId)]
        payment_search = payment_partner.search(domain)
        contract_search = agreement.search([('id', '=', contractId)])
        contract_search.write({
            'card_number': payment_search.id
        })
        contract_search.onchange_card_number()
        return request.redirect(url)


    ################################## CONTRACT WEBSITE VIEWS ##################################
    @http.route('/kushki_contracts', type='http', auth='user', csrf=True, website=True)
    def kushki_contracts(self, **post):
        PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
        partner = request.env.user.partner_id
        Agreement = request.env['agreement'].sudo()
        PaymentMethods = request.env['payment.method.partner'].sudo()
        AgreementPaymentMethods = request.env['agreement.payment.method'].sudo()
        pat = AgreementPaymentMethods.search([('code', '=', 'pat')])
        KushkiLog = request.env['kushki.log'].sudo()
        Bus = request.env['bus.bus']
        url = '/payment/success'
        headers_pub = {
            'Public-Merchant-Id': PaymentAcquirer.kushki_publishable_key,
            'content-type': "application/json"
        }
        ######################### BIN INFO CARD ###########################
        bin_info = post['card'][:6]
        response_bin_info = requests.get(url_kushki + "/card/v1/bin/" + bin_info, headers=headers_pub)
        response_bin_info_dict = response_bin_info.json()
        if response_bin_info.status_code != 200:
            answer = json.dumps(response_bin_info_dict, indent=4)
            if '\n' in answer:
                answer = answer.replace('\n', '<br/>')
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'binInfo',
                'error_code': response_bin_info_dict['code'],
                'description_error': response_bin_info_dict['message'],
                'answer': answer,
            })
            title = response_bin_info_dict['code']
            subject = response_bin_info_dict['message'],
            Bus.sendone(
                (Bus._cr.dbname, 'res.partner', partner.id),
                {'type': 'simple_notification', 'title': title,
                 'message': subject}
            )
            return
            # raise UserError((response_bin_info_dict['code']), (response_bin_info_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'card_number': '',
            'token_card': '',
            'method_name': 'binInfo',
            'answer': json.dumps(response_bin_info_dict, indent=4).replace('\n', '<br/>'),
        })
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        fname, lname = post['username'].split(' ')
        number = post['codigo'] + post['phone_credit']
        # mod = get_cc_module('cl', 'rut')
        # rut = post['document_number']
        # val_rut = mod.is_valid(rut)
        # if val_rut == False:
        #     print(rut, 'falso')
        #     raise UserError("El rut ingresado |{0}|no es valido".format(rut))
        # if val_rut == True:
        subscription = {
            "token": post['subscriptionToken'],
            "planName": post['document_number'],
            "periodicity": "custom",
            "contactDetails": {
                "documentType": "RUT",
                "documentNumber": post['document_number'],
                "email": post['email'],
                "firstName": fname,
                "lastName": lname,
                "phoneNumber": number,
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "startDate": str_today
        }
        headers = {
            'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
            'content-type': "application/json"
        }
        response = requests.post(url_kushki + "/subscriptions/v1/card", data=json.dumps(subscription), headers=headers)
        response_dict = response.json()
        if response.status_code != 201:
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'createSubscription',
                'error_code': response_dict['code'],
                'description_error': response_dict['message'],
                'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError((response_dict['code']), (response_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'method_name': 'createSubscription',
            'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
        })
        subscriptionId = response_dict['subscriptionId']
        response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId,
                                             headers=headers)
        response_subscription_dict = response_subscription.json()

        if response_subscription.status_code != 200:
            KushkiLog.create({
                'partner_id': partner.id,
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'error_code': response_subscription_dict['code'],
                'description_error': response_subscription_dict['message'],
                'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
            })
            raise UserError((response_subscription_dict['code']), (response_subscription_dict['message']))
        KushkiLog.create({
            'partner_id': partner.id,
            'user_id': request.env.user.id,
            'method_name': 'getSubscription',
            'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
        })
        contact = response_subscription_dict['contactDetails']
        payment_contract = PaymentMethods.create({
            'date_subscription': today,
            'partner_id': partner.id,
            'partner_id_vat': partner.vat,
            'token_card': subscriptionId,
            'card_number': response_subscription_dict['maskedCardNumber'],
            'type_subscription': 'on_demand',
            'type_subscription_contract': pat.id if pat else False,
            'bank': response_bin_info_dict['bank'],
            'brand': response_bin_info_dict['brand'],
            'card_type': response_bin_info_dict['cardType'],
            'name': contact['firstName'],
            'last_name': contact['lastName'],
            'phone_number': contact['phoneNumber'],
            'document_number': contact['documentNumber'],
            'email': contact['email'],
            'relationship': post['relationship']
        })
        if 'creditContractId' in post:
            search_agreement = Agreement.search([('id', '=', post['creditContractId'])])
            search_agreement.write({
                'card_number': payment_contract.id
            })
        return request.redirect(url)

    @http.route('/kushki_webpay_contracts', type='http', auth='user', csrf=True, website=True)
    def kushki_webpay_contracts(self, **post):
        url = '/my/contracts'
        AgreementPaymentMethods = request.env['agreement.payment.method'].sudo()
        pac = AgreementPaymentMethods.search([('code', '=', 'pac')])
        today = date.today()
        str_today = datetime.strftime(today, '%Y-%m-%d')
        subscription = {
            "token": post['webpaySubsctiptionToken'],
            "planName": post['document_number'],
            "periodicity": "custom",
            "contactDetails": {
                "documentNumber": post['document_number'],
                "email": post['mail'],
                "firstName": post['firstname'],
                "lastName": post['lastname'],
                "phoneNumber": post['number']
            },
            "amount": {
                "subtotalIva": 0,
                "subtotalIva0": 0,
                "ice": 0,
                "iva": 0,
                "currency": "CLP"
            },
            "startDate": str_today
        }
        headers = {'Private-Merchant-Id': 'be7c9a71e9d842fda2fe42b84ead2577', 'content-type': "application/json"}
        response = requests.post(url_kushki + "/subscriptions/v1/card-async/init", data=json.dumps(subscription),
                                 headers=headers)
        if response.status_code != 201:
            re = response.json()
            raise UserError('{} \n {}'.format(re['code'], re['message']))

        re = response.json()
        print(re)
        subscriptionId = re.get('subscriptionId', False)
        redirectUrl = re.get('redirectUrl', False)
        response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId,
                                             headers=headers)

        if response_subscription.status_code != 200:
            re_subcription = response_subscription.json()
            raise UserError('{} \n {}'.format(re_subcription['code'], re_subcription['message']))

        re_subcription = response_subscription.json()
        subscriptionId = re_subcription['subscriptionId']
        payment_partner = request.env['payment.method.partner'].sudo()
        partner = request.env.user.partner_id
        payment_partner.create({
            'partner_id': partner.id,
            'type_subscription': 'webpay',
            'type_subscription_contract': pac.id if pac else False,
            'token_card': subscriptionId,
        })
        return redirect(redirectUrl)
    
    @http.route('/payment/success', type="http", auth='user', csrf=True, website=True)
    def payment_success_create(self,**kw):
        PaymentMethods = request.env['payment.method.partner'].sudo()
        PaymentAccountKushki = request.env['payment.account.kushki'].sudo()
        KushkiLog = request.env['kushki.log'].sudo()
        Agreement = request.env['agreement'].sudo()
        Bus = request.env['bus.bus']
        AgreementPaymentMethods = request.env['agreement.payment.method'].sudo()
        AgreementPaymentIntermediary = request.env['agreement.payment.intermediary'].sudo()
        partner = request.env.user.partner_id
        if 'code' in kw:
            if kw['code'] == 'E500':
                KushkiLog.create({
                    'user_id': request.env.user.id,
                    'method_name': 'getSubscription',
                    'error_code': kw['code'],
                    'description_error': kw['message'],
                    'answer': kw,
                })
                return request.redirect("/my/paymentmethods")
        if 'subscriptionId' in kw:
            PaymentAcquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'kushki')])
            subscriptionId = kw['subscriptionId']
            headers = {
                'Private-Merchant-Id': PaymentAcquirer.kushki_secret_key,
                'content-type': "application/json"
            }
            response_subscription = requests.get(url_kushki + "/subscriptions/v1/card/search/" + subscriptionId,
                                                 headers=headers)
            response_subscription_dict = response_subscription.json()
            if response_subscription.status_code != 200:
                KushkiLog.create({
                    'user_id': request.env.user.id,
                    'method_name': 'getSubscription',
                    'error_code': response_subscription_dict['code'],
                    'description_error': response_subscription_dict['message'],
                    'answer': json.dumps(response_subscription_dict, indent=4).replace('\n', '<br/>'),
                })
                raise UserError(
                    '{} \n {}'.format(response_subscription_dict['code'], response_subscription_dict['message']))
            KushkiLog.create({
                'user_id': request.env.user.id,
                'method_name': 'getSubscription',
                'answer': json.dumps(response_subscription.text, indent=4).replace('\n', '<br/>'),
            })
            contact = response_subscription_dict['contactDetails']
            today = date.today()

            vals = {
                'date_subscription': today,
                'partner_id': partner.id,
                'partner_id_vat': partner.vat,
                'type_subscription': 'webpay',
                'acquirer_id': PaymentAcquirer.id,
                'token_card': subscriptionId,
                'name': contact['firstName'],
                'last_name': contact['lastName'],
                'phone_number': contact['phoneNumber'],
                'document_number': contact['documentNumber'],
                'email': contact['email'],
                'phone_number': contact['phoneNumber'],
            }
            if 'maskedCardNumber' in response_subscription_dict:
                headers_pub = {
                    'Public-Merchant-Id': PaymentAcquirer.kushki_publishable_key,
                    'content-type': "application/json"
                }
                bin_info = response_subscription_dict['bin']
                response_bin_info = requests.get(url_kushki + "/card/v1/bin/" + bin_info, headers=headers_pub)
                response_bin_info_dict = response_bin_info.json()
                if response_bin_info.status_code != 200:
                    answer = json.dumps(response_bin_info_dict, indent=4)
                    if '\n' in answer:
                        answer = answer.replace('\n', '<br/>')
                    KushkiLog.create({
                        'partner_id': partner.id,
                        'user_id': request.env.user.id,
                        'method_name': 'binInfo',
                        'error_code': response_bin_info_dict['code'],
                        'description_error': response_bin_info_dict['message'],
                        'answer': answer,
                    })
                    title = response_bin_info_dict['code']
                    subject = response_bin_info_dict['message'],
                    Bus.sendone(
                        (Bus._cr.dbname, 'res.partner', partner.id),
                        {'type': 'simple_notification', 'title': title,
                         'message': subject}
                    )
                    return
                KushkiLog.create({
                    'partner_id': partner.id,
                    'user_id': request.env.user.id,
                    'card_number': '',
                    'token_card': '',
                    'method_name': 'binInfo',
                    'answer': json.dumps(response_bin_info_dict, indent=4).replace('\n', '<br/>'),
                })
                card_number = response_subscription_dict['maskedCardNumber']
                brand = response_subscription_dict['paymentBrand']
                card_type = response_subscription_dict['cardType']
                agreement_method = AgreementPaymentMethods.search([('code', '=', 'pat')])
                agreement_intermediary = AgreementPaymentIntermediary.search([('payment_method', '=', agreement_method.id), ('acquirer_id', '=', PaymentAcquirer.id)])
                vals.update({
                    'type_subscription_contract': agreement_method.id if agreement_method else False,
                    'card_number': card_number,
                    'bank': response_bin_info_dict['bank'],
                    'brand': response_bin_info_dict['brand'],
                    'card_type': card_type,
                    'type_subscription_new': agreement_intermediary.id
                })
            elif 'lastFourDigits' in response_subscription_dict and 'paymentBrand' in response_subscription_dict:
                card_number = 'XXXXXXXXXXXXXXXX' + response_subscription_dict['lastFourDigits']
                brand = response_subscription_dict['paymentBrand']
                agreement_method = AgreementPaymentMethods.search([('code', '=', 'pac')])
                agreement_intermediary = AgreementPaymentIntermediary.search([('payment_method', '=', agreement_method.id), ('acquirer_id', '=', PaymentAcquirer.id)])
                vals.update({
                    'type_subscription_contract': agreement_method.id if agreement_method else False,
                    'card_number': card_number,
                    'type_subscription_new': agreement_intermediary.id
                })
            else:
                pass
            payment_account_kushki = PaymentAccountKushki.search([('name', '=', brand)])
            vals.update({
                'payment_account': payment_account_kushki.id if payment_account_kushki else False
            })
            Payment = PaymentMethods.create(vals)
            if 'contract_id' in kw:
                search_agreement = Agreement.search([('id', '=', kw['contract_id'])])
                search_agreement.write({
                    'card_number': Payment.id
                })
        return request.render("payment_kushki.successful_payment", {})
    

