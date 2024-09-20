# Copyright (C) 2023 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import jinja2
import base64
from odoo import http

loader = jinja2.PackageLoader('odoo.addons.mobile_pro_website', 'views')
env = jinja2.Environment(loader=loader, autoescape=True)


class MainController(http.Controller):

    @http.route('/', methods=['GET'], auth='none')
    def mobile_pro_website(self, **kwargs):
        company = http.request.env['res.company'].sudo().search([], limit=1)
        session = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)], limit=1)
        return env.get_template('index.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'session': session,
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })

    """
    @http.route('/blog', methods=['GET'], auth='none')
    def mobile_pro_blog(self, **kwargs):
        company = http.request.env['res.company'].sudo().search([], limit=1)
        session = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)], limit=1)
        return env.get_template('blog1.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'session': session,
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })"""

    @http.route('/contact', methods=['GET'], auth='none')
    def mobile_pro_contact(self, **kwargs):
        company = http.request.env['res.company'].sudo().search([], limit=1)
        session = http.request.env['res.users'].sudo().search([('id', '=', http.request.session.uid)], limit=1)
        return env.get_template('contact.html').render({
            'company': company,
            'company_fhone': company.phone,
            'company_email': company.email,
            'session': session,
            'logo': company.logo and 'data:image/png;base64,%s' % company.logo.decode()
        })

    @http.route('/modal', methods=['GET'], auth='public')
    def modal(self, **kwargs):
        return env.get_template('modal.html').render({
            'csrf_token': http.request.csrf_token(),
        })

    @http.route('/modal', type='json', auth='public')
    def modal_response(self, name, phone, email, message, **kwargs):
        partner = http.request.env['res.partner'].sudo().search([('email', 'ilike', email.strip())], limit=1)
        if not partner:
            partner = partner.sudo().create({
                'name': name.strip(),
                'phone': phone.strip(),
                'email': email.strip(),
            })
        http.request.env['crm.lead'].sudo().create({
            'name': '%s  <%s>' % (name.strip(), email.strip()),
            'partner_id': partner.id,
            'email_from': email.strip(),
            'description': message.strip(),
            'user_id': 2,
        })
        return {
            'name': name,
        }

MainController()
