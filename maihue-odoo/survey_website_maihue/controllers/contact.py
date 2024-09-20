# Copyright (C) 2023 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import jinja2

from odoo import http

loader = jinja2.PackageLoader('odoo.addons.ecommerce_pro_website', 'views')
env = jinja2.Environment(loader=loader, autoescape=True)


class ContactController(http.Controller):

    @http.route('/contact', methods=['GET'], auth='none', website=True)
    def ecommerce_pro_contact(self, **kwargs):
        company = http.request.env['res.company'].sudo().search([], limit=1)
        return env.get_template('contact.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'csrf_token': http.request.csrf_token(),
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })

    @http.route('/contact', methods=['POST'], website=True, auth='public', csrf=False)
    def ecommerce_pro_contact_end(self, **kwargs):
        partner = http.request.env['res.partner'].sudo().search([('email', 'ilike', kwargs.get('email').strip())],
                                                                limit=1)
        if not partner:
            partner = partner.sudo().create({
                'name': kwargs.get('first-name').strip(),
                # 'customer': True,
                'email': kwargs.get('email').strip()
            })
        http.request.env['crm.lead'].sudo().create({
            'name': kwargs.get('first-name').strip(),
            'email_from': kwargs.get('email'),
            'description': kwargs.get('your-message')
        })
        company = http.request.env['res.company'].sudo().search([], limit=1)
        return env.get_template('contact.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })

ContactController()
