# Copyright (C) 2023 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import jinja2
import base64
import httplib2
import json
from odoo import http

loader = jinja2.PackageLoader('odoo.addons.ecommerce_pro_website', 'views')
env = jinja2.Environment(loader=loader, autoescape=True)

class ProductController(http.Controller):

    @http.route('/product/<int:id>', auth='public', methods=['GET'], website=True)
    def ecommerce_pro_product(self, referrer=None, payment=None, **basura):
        company = http.request.env['res.company'].sudo().search([], limit=1)
        session = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)], limit=1)
        product = http.request.env['product.template'].sudo().search(
            [('id', '=', http.request.endpoint_arguments.get('id'))], limit=1)
        if not product:
            return env.get_template('404.html').render({
                'company': company,
                'company_fhone': company.phone,
                'company_email': company.email,
                'csrf_token': http.request.csrf_token(),
                'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
            })
        if product.attribute_line_ids:
            for attr in product.attribute_line_ids:
                if attr.attribute_id.display_type == 'select':
                    for size in attr.value_ids:
                        jamie = size.name
        # TODO: Definir si se van a contar las visitas
        # http.request.env['product.visit'].sudo().create({
        #     'sid': http.request.session.sid,
        #     'user_id': http.request.env.user.id,
        #     'template_id': product.id
        # })
        # data = {'product': product, 'referrer': referrer}
        # if payment:
        #     travel_payment = http.request.env['travel.payment'].sudo().search([
        #         ('name', 'ilike', payment.replace('-', ' ')),
        #         ('template_id', '=', product.id)
        #     ], limit=1)
        #     if travel_payment:
        #         data.update({
        #             'payment': travel_payment
        #         })
        return env.get_template('product.html').render({
                    'company': company,
                    'company_fhone': company.phone,
                    'company_email': company.email,
                    'csrf_token': http.request.csrf_token(),
                    'product': product,
                    'reviews': len(product.comment_id),
                    'referrer': referrer,
                    'session': session,
                    'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
                })

    @http.route('/product/<string:product_name>', methods=['POST'], website=True, auth='public', csrf=False)
    def ecommerce_pro_product_comment(self, product_name, referrer=None, payment=None, **kwargs):
        partner = http.request.env['res.partner'].sudo().search([('email', 'ilike', kwargs.get('email').strip())],
                                                                limit=1)
        session = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)], limit=1)
        product = http.request.env['product.template'].sudo().search(
            [('name', 'ilike', product_name.replace('-', ' '))], limit=1)
        http.request.env['ecommerce.pro.comment'].sudo().create({
            'name': kwargs.get('name').strip(),
            'email': kwargs.get('email'),
            'comment': kwargs.get('comment')
        })
        company = http.request.env['res.company'].sudo().search([], limit=1)
        return env.get_template('product.html').render({
                    'company': company,
                    'company_fhone': company.phone,
                    'company_email': company.email,
                    'csrf_token': http.request.csrf_token(),
                    'product': product,
                    'reviews': len(product.comment_id),
                    'referrer': referrer,
                    'session': session,
                    'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
                })

ProductController()
