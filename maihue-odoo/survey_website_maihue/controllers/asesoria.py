# © 2023 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import jinja2
from odoo import http
from odoo.http import request, route
from datetime import date, datetime
from werkzeug.utils import redirect
from odoo.tools.translate import _
from odoo.exceptions import UserError, AccessError, MissingError
from stdnum import get_cc_module
import requests
import json

from odoo import http

loader = jinja2.PackageLoader('odoo.addons.survey_website_maihue', 'views')
env = jinja2.Environment(loader=loader, autoescape=True)

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

    @http.route('/formmaihue', type='http', auth="user", website=True)
    def form_maihue(self, page=1, **kw):
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
            url="/formmaihue",
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
            'page_name': 'formmaihue',
            'pager': pager,
            'default_url': '/formmaihue',
        })
        return request.render("survey_website_maihue.formmaihue", values)

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

class AsesoriaController(http.Controller):

    @http.route('/asesoria', methods=['GET'], auth='none', website=True)
    def ecommerce_pro_contact(self, **kwargs):
        company = http.request.env['res.company'].sudo().search([], limit=1)
        return env.get_template('asesoria.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'csrf_token': http.request.csrf_token(),
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })

    @http.route('/asesoria_checkout', methods=['POST'], website=True, auth='public', csrf=False)
    def asesoria_contact_end(self, **post):
        # cambiar por rut el search
        partner = http.request.env['res.partner'].sudo().search([('email', 'ilike', post.get('email').strip())],
                                                                limit=1)
        if not partner:
            partner = partner.sudo().create({
                'name': post.get('first-name').strip(),
                # 'customer': True,
                # el metodo de pago tiene que ir en un campo referencial
                # servicio referencial (son no editables en nunca ni en lead )
                # Direccion servicio referencial
                # cantidad de equipos
                # se debe concatenar todos en descripcion de formulario
                'email': post.get('email').strip()
            })
            # el check de contrato por default debe ser True
        http.request.env['crm.lead'].sudo().create({
            'name': post.get('first-name').strip(),
            'email_from': post.get('email'),
            'description': post.get('your-message')
        })
        company = http.request.env['res.company'].sudo().search([], limit=1)
        return env.get_template('asesoria.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })

AsesoriaController()