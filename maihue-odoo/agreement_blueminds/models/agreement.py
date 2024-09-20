# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, models, fields
import werkzeug
from datetime import timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import time
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError, ValidationError


class Agreement(models.Model):
    _name = 'agreement'
    _description = 'Agreement'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    def _get_default_parties(self):
        deftext = """
        <h3>Company Information</h3>
        <p>
        ${object.company_id.partner_id.name or ''}.<br>
        ${object.company_id.partner_id.street or ''} <br>
        ${object.company_id.partner_id.state_id.code or ''}
        ${object.company_id.partner_id.zip or ''}
        ${object.company_id.partner_id.city or ''}<br>
        ${object.company_id.partner_id.country_id.name or ''}.<br><br>
        Represented by <b>${object.company_contact_id.name or ''}.</b>
        </p>
        <p></p>
        <h3>Partner Information</h3>
        <p>
        ${object.partner_id.name or ''}.<br>
        ${object.partner_id.street or ''} <br>
        ${object.partner_id.state_id.code or ''}
        ${object.partner_id.zip or ''} ${object.partner_id.city or ''}<br>
        ${object.partner_id.country_id.name or ''}.<br><br>
        Represented by <b>${object.partner_contact_id.name or ''}.</b>
        </p>
        """
        return deftext

    @api.model
    def name_get(self):
        result = []
        for record in self:
            if record.anexo == False:
                name = '%s - %s' % (record.name, 'No permite anexos')
            else:
                name = record.name
            result.append((record.id, name))
        return result

    def _compute_line_count(self):
        line_data = self.sudo().env['agreement.line'].read_group([('agreement_id', 'in', self.ids)], ['agreement_id'], ['agreement_id'])
        mapped_data = dict([(q['agreement_id'][0], q['agreement_id_count']) for q in line_data])
        for agreement in self:
            agreement.line_count = mapped_data.get(agreement.id, 0)

    # Used for Kanban grouped_by view
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["agreement.stage"].search(
            [('stage_type', '=', 'agreement')])
        return stage_ids

    # def _compute_template_agreement_id(self):
    #     res = {}
    #     templates_all = self.search([])
    #     arrs = []
    #     today = datetime.now()
    #     domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
    #     if self.parent_agreement_id:
    #         domain.append(('template_child', '=', True))
    #     if self.team_id:
    #         domain.append(('team_id_domain', 'in', self.team_id.id))
    #     if self.type_contrib_partner:
    #         domain.append(('type_contrib', '=', self.type_contrib_partner.id))
    #     if self.type_partner:
    #         domain.append(('type_partner_domain', 'in', self.type_partner.id))
    #     if self.payment_method:
    #         domain.append(('payment_method_domain', 'in', self.payment_method.id))
    #     if self.payment_period:
    #         domain.append(('payment_period_domain', 'in', self.payment_period.id))
    #     if self.payment_term_id:
    #         domain.append(('payment_deadline_domain', 'in', self.payment_term_id.id))
    #     if self.pricelist_id:
    #         domain.append(('pricelist_id', '=', self.pricelist_id.id))
    #     # if self.agreement_type_id:
    #     #     domain.append(('agreement_type_id', '=', self.agreement_type_id.id))
    #     templates_ids = self.search(domain)
    #     if templates_ids:
    #         for x in templates_ids:
    #             arrs.append(x.id)
    #     if self.template_agreement_id:
    #         res['domain'] = {
    #             'card_number': [
    #                 ('type_subscription_contract', 'in', self.template_agreement_id.payment_method_domain.ids)]}
    #         # self.agreement_type_id = self.template_agreement_id.agreement_type_id.id
    #         self.document_ids = self.template_agreement_id.document_ids
    #         # self.document_ids.recital_ids.recital_contrato_id = self.template_agreement_id.document_ids.recital_ids.recital_contrato_id
    #         self.recital_ids = self.template_agreement_id.recital_ids
    #         # self.agreement_subtype_id = self.template_agreement_id.agreement_subtype_id
    #         self.anexo = self.template_agreement_id.anexo
    #         self.description = self.template_agreement_id.description
    #         # self.end_date = self.template_agreement_id.end_date
    #         self.special_terms = self.template_agreement_id.special_terms
    #         # self.title = self.template_agreement_id.title
    #         self.num_dias = self.template_agreement_id.num_dias
    #         # self.late_fine = self.template_agreement_id.late_fine
    #         self.content = self.template_agreement_id.content
    #         #self.extra_ids = self.template_agreement_id.extra_ids
    #         self.signed_document_ids = self.template_agreement_id.signed_document_ids
    #         self.test_day_domain = self.template_agreement_id.test_day_domain
    #         self.payment_period_domain = self.template_agreement_id.payment_period_domain
    #         extras_document = []
    #         if self.template_agreement_id.extra_ids:
    #             v = 1
    #             for extra_ids in self.template_agreement_id.extra_ids:
    #                 name = str(extra_ids.type_extra.name) + ' ' + str(self.name) + ' V' + str(v)
    #                 v+1
    #             #     if self.is_template:
    #             #         name = str(extra_ids.type_extra.name) + ' ' + str(self.name)
    #             #         anexo = str(self.name)[-1]
    #             #         if int(anexo) ==
    #             # else:
    #             #     name = str(extra_ids.name)
    #             #     anexo = str(self.name)[-1]
    #             #     if int(anexo) == 0:
    #             #         name = str(extra_ids.type_extra.name) + ' ' + str(self.name)
    #             #     else:
    #             #         jamie = 0
    #                 extras_document.append({'name': name, 'type_extra': extra_ids.type_extra.id, 'firma': extra_ids.firma, 'required_sign': extra_ids.required_sign, 'require_maihue': extra_ids.require_maihue, 'content': extra_ids.content, 'agreement_id': self.id})
    #             if extras_document:
    #                 self.extra_ids.unlink()
    #                 self.extra_ids.create(extras_document)
    #         #self.extra_ids = (0, 0, { fields })self.template_agreement_id.extra_ids
    #         self.payment_deadline_domain = self.template_agreement_id.payment_deadline_domain
    #         self.pricelist_id = self.template_agreement_id.pricelist_id
    #         self.product_domain = self.template_agreement_id.product_domain
    #         self.zona_domain = self.template_agreement_id.zona_domain
    #         self.team_id_domain = self.template_agreement_id.team_id_domain
    #         self.template_domain = templates_ids.ids
    #     if not self.template_agreement_id:
    #         payment_method = []
    #         payment_period = []
    #         team_id_domain = []
    #         type_partner_domain = []
    #         template_domain = []
    #         agreement_type = []
    #         payment_deadline_domain = []
    #         pricelist = []
    #         domain = [('is_template', '=', True), ('expiration_date', '>=', today),
    #                   ('template_child', '=', False)]
    #         domain_exc = [('is_template', '=', True), ('expiration_date', '>=', today),
    #                       ('template_child', '=', False)]
    #         if self.partner_id.type_contrib:
    #             domain.append(('type_contrib', '=', self.partner_id.type_contrib.id))
    #             domain_exc.append(('type_contrib', '=', self.partner_id.type_contrib.id))
    #         if self.payment_method:
    #             domain.append(('payment_method_domain', 'in', self.payment_method.id))
    #             domain_exc.append(('payment_method_domain', 'in', self.payment_method.id))
    #         if self.team_id:
    #             domain.append(('team_id_domain', 'in', self.team_id.id))
    #         templates_method = self.env['agreement'].sudo().search(domain)
    #         # if templates_method:
    #         #     for temp in templates_method:
    #         #         template_domain.append(temp.id)
    #         # self.template_domain = template_domain
    #         for a in templates_method:
    #             for paym in a.payment_method_domain:
    #                 if paym.id not in payment_method:
    #                     payment_method.append(paym.id)
    #             for payp in a.payment_period_domain:
    #                 if payp.id not in payment_period:
    #                     payment_period.append(payp.id)
    #             for tids in a.team_id_domain:
    #                 if tids.id not in team_id_domain:
    #                     team_id_domain.append(tids.id)
    #             for deadline in a.payment_deadline_domain:
    #                 if deadline.id not in payment_deadline_domain:
    #                     payment_deadline_domain.append(deadline.id)
    #             for type_p in a.type_partner_domain:
    #                 if type_p.id not in type_partner_domain:
    #                     type_partner_domain.append(type_p.id)
    #             if a.agreement_type_id not in agreement_type:
    #                 agreement_type.append(a.agreement_type_id.id)
    #             if a.pricelist_id not in pricelist:
    #                 pricelist.append(a.pricelist_id.id)
    #         self.template_domain = templates_ids.ids
    #         #self.payment_method_domain = payment_method
    #         self.team_id_domain = team_id_domain
    #         self.payment_deadline_domain = payment_deadline_domain
    #         self.type_partner_domain = type_partner_domain
    #         self.payment_period_domain = payment_period

    # def _compute_template_agreement_id(self):
    #     if self.template_agreement_id:
    #         type_contrib_do = []
    #         template_domain = []
    #         payment_period_do = []
    #         payment_method_do = []Template Empresa
    #         payment_deadline_do = []
    #         arrs = []
    #         today = datetime.now()
    #         domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
    #         if self.parent_agreement_id:
    #             domain.append(('template_child', '=', True))
    #         if self.template_agreement_id.team_id_domain:
    #             domain.append(('team_id_domain', 'in', self.team_id.id))
    #         if self.template_agreement_id.partner_domain:
    #             domain.append(('partner_domain', 'in', self.partner_id.id))
    #         if self.type_contrib_partner:
    #             domain.append(('type_contrib', '=', self.type_contrib_partner.id))
    #         templates_ids = self.search(domain)
    #         if templates_ids:
    #             for x in templates_ids:
    #                 arrs.append(x.id)
    #         if self.payment_method:
    #             self.payment_method_domain = self.template_agreement_id.payment_method_domain
    #         if not self.payment_method:
    #             self.payment_method_domain = [1, 2, 3, 4]
    #         if self.template_agreement_id.parent_template_id:
    #             for type in self.parent_agreement_id.type_contrib_domain:
    #                 if type.code == 'igp':
    #                     type_contrib_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.type_contrib_domain.ids)]
    #             for period in self.template_agreement_id.payment_period_domain:
    #                 if period.code == 'igp':
    #                     payment_period_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.payment_period_domain.ids)]
    #             for method in self.template_agreement_id.payment_method_domain:
    #                 if method.code == 'igp':
    #                     payment_method_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.payment_method_domain.ids)]
    #             for deadline in self.template_agreement_id.payment_deadline_domain:
    #                 if deadline.name == 'Igual al Dominio Padre':
    #                     payment_period_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.payment_deadline_domain.ids)]
    #         # if not type_contrib_do:
    #         #     type_contrib_do = [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)]
    #         if not payment_period_do:
    #             payment_period_do = [('id', 'in', self.template_agreement_id.payment_period_domain.ids)]
    #         if not payment_method_do:
    #             payment_method_do = [('id', 'in', self.template_agreement_id.payment_method_domain.ids)]
    #         if not payment_deadline_do:
    #             payment_deadline_do = [('id', 'in', self.template_agreement_id.payment_deadline_domain.ids)]
    #         self.agreement_type_id = self.template_agreement_id.agreement_type_id.id
    #         self.document_ids = self.template_agreement_id.document_ids
    #         #self.document_ids.recital_ids.recital_contrato_id = self.template_agreement_id.document_ids.recital_ids.recital_contrato_id
    #         self.recital_ids = self.template_agreement_id.recital_ids
    #         self.agreement_subtype_id = self.template_agreement_id.agreement_subtype_id
    #         self.anexo = self.template_agreement_id.anexo
    #         self.description = self.template_agreement_id.description
    #         self.end_date = self.template_agreement_id.end_date
    #         self.special_terms = self.template_agreement_id.special_terms
    #         self.title = self.template_agreement_id.title
    #         self.num_dias = self.template_agreement_id.num_dias
    #         self.late_fine = self.template_agreement_id.late_fine
    #         self.content = self.template_agreement_id.content
    #         self.extra_ids = self.template_agreement_id.extra_ids
    #         self.signed_document_ids = self.template_agreement_id.signed_document_ids
    #         self.test_day_domain = self.template_agreement_id.test_day_domain
    #         self.payment_period_domain = self.template_agreement_id.payment_period_domain
    #         self.extra_ids = self.template_agreement_id.extra_ids
    #         self.payment_method_domain = self.template_agreement_id.payment_method_domain
    #         self.payment_deadline_domain = self.template_agreement_id.payment_deadline_domain
    #         self.pricelist_id_domain = self.template_agreement_id.pricelist_id_domain
    #         self.product_domain = self.template_agreement_id.product_domain
    #         self.zona_domain = self.template_agreement_id.zona_domain
    #         self.template_domain = domain

    @api.depends('line_ids')
    def _compute_total_lines_contract(self):
        # for record in self:
        #     total = 0
        #     if record.line_ids:
        #         for line in record.line_ids:
        #             total += line.price
        #     record.total_service = total
        # servicios adicionales
        zonas = []
        today = datetime.now().date()
        for lines in self.line_ids:
            if lines.zona_comercial not in zonas:
                zonas.append(lines.zona_comercial)
        if zonas:
            existentes = self.env['agreement.extra.charges'].search([('agreement_id', '=', self.ids[0])])
            if existentes:
                if len(existentes) > 1:
                    for exi in existentes:
                        exi.unlink()
                else:
                    existentes.unlink()
            for zona in zonas:
                adicionales = self.env['agreement.extra.charges'].search(
                    [('agreement_id', '=', self.template_agreement_id.id)])
                #cuantas zonas hay y multiplicarlo por los productos que esten en servicios adicionales
                for services in adicionales:
                    pricelist = self.env['product.pricelist.item'].search([('zone', '=', zona.id), (
                    'product_tmpl_id', '=', services.product_id.id), (
                    'pricelist_id', '=', self.pricelist_id.id),
                    ('vigente', '=', 'V'),
                    ('date_start', '<=', today),
                    ('date_end', '>=', today)], limit=1)#.fixed_price
                    serv_adi = self.env['agreement.extra.charges'].create({
                        'product_id': services.product_id.id,
                        'description': services.description,
                        # 'pricelist_id': lines.pricelist_id.id,
                        'currency_id': pricelist.currency_id_m.id,
                        'zona_comercial': zona.id,
                        'price': pricelist.fixed_price, #price,
                        'agreement_id': self.id,
                    })

    # compute the dynamic content for mako expression
    @api.model
    def _compute_dynamic_content(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = (
                    agreement.id
                    and agreement.partner_id.lang
                    or "en_US")
            content = MailTemplates.with_context(lang=lang)._render_template(
                agreement.content, "agreement", agreement.id)
            agreement.dynamic_content = content

    # compute the dynamic content for mako expression
    def _compute_dynamic_description(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            description = MailTemplates.with_context(lang=lang)._render_template(
                agreement.description, "agreement", agreement.id
            )
            agreement.dynamic_description = description

    def _compute_dynamic_parties(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            parties = MailTemplates.with_context(
                lang=lang
            )._render_template(
                agreement.parties, "agreement", agreement.id
            )
            agreement.dynamic_parties = parties

    def _compute_dynamic_special_terms(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            special_terms = MailTemplates.with_context(lang=lang)._render_template(
                agreement.special_terms, "agreement", agreement.id
            )
            agreement.dynamic_special_terms = special_terms

    def _compute_invoice_count(self):
        base_domain = [
            ('agreement_id', 'in', self.ids),
            ('state', 'not in', ('draft', 'cancel'))]
        aio = self.env['account.move']
        out_rg_res = aio.read_group(
            base_domain + [('type', 'in', ('out_invoice', 'out_refund'))],
            ['agreement_id'], ['agreement_id'])
        out_data = dict(
            [(x['agreement_id'][0], x['agreement_id_count']) for x in out_rg_res])
        in_rg_res = aio.read_group(
            base_domain + [('type', 'in', ('in_invoice', 'in_refund'))],
            ['agreement_id'], ['agreement_id'])
        in_data = dict(
            [(x['agreement_id'][0], x['agreement_id_count']) for x in in_rg_res])
        for agreement in self:
            agreement.out_invoice_count = out_data.get(agreement.id, 0)
            agreement.in_invoice_count = in_data.get(agreement.id, 0)

    def _compute_sale_count(self):
        rg_res = self.env['sale.order'].read_group(
            [
                ('agreement_id', 'in', self.ids),
                ('state', 'not in', ('draft', 'sent', 'cancel')),
            ],
            ['agreement_id'], ['agreement_id'])
        mapped_data = dict(
            [(x['agreement_id'][0], x['agreement_id_count']) for x in rg_res])
        for agreement in self:
            agreement.sale_count = mapped_data.get(agreement.id, 0)

    # def _compute_partner_invoice_id(self):
    #     if self.partner_id:
    #         if self.partner_id.company_type == 'company':
    #             partners = self.env['res.partner'].search(
    #                 [('parent_id', '=', self.partner_id.id), ('etiqueta_person', 'in', [4])])
    #
    #             self.partner_invoice_id_domain = partners.ids
    #         else:
    #             partners = self.env['res.partner'].search(
    #                 [('id', '=', self.partner_id.id), ('etiqueta_person', 'in', [4])])
    #             self.partner_invoice_id_domain = partners.ids

    code = fields.Char(
        string="Reference",
        required=True,
        default=lambda self: _("New"),
        track_visibility="onchange",
        copy=False,
        help="ID used for internal contract tracking.")
    name = fields.Char(string='Name', required=False, track_visibility='onchange')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', ondelete='restrict',
        domain=[('parent_id', '=', False)], track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', string='Company', track_visibility="onchange",
        default=lambda self: self.env['res.company']._company_default_get())
    is_template = fields.Boolean(
        string="Is a Template?",
        default=False,
        copy=False,
        help="Set if the agreement is a template. "
        "Template agreements don't require a partner.", track_visibility="onchange"
    )
    line_count = fields.Integer(compute='_compute_line_count', tracking=True)
    father = fields.Boolean(
        string="Father",
        default=False,
        copy=False, track_visibility="onchange",
        help="Set if the agreement is father. "
    )
    agreement_type_id = fields.Many2one(
        'agreement.type',
        string="Document Type", track_visibility="onchange",
        help="Select the type of document",
    )
    domain = fields.Selection(
        '_domain_selection', string='Domain', default='sale',
        track_visibility='onchange')
    active = fields.Boolean(
        string="Active", track_visibility="onchange",
        default=True,
        help="If unchecked, it will allow you to hide the agreement without "
             "removing it.")
    signature_date = fields.Date(track_visibility='onchange')
    start_date = fields.Date(
        string="Start Date", default=fields.Date.context_today,
        track_visibility="onchange",
        help="When the agreement starts.")
    end_date = fields.Date(
        string="End Date", default=time.strftime('9999-01-01'),
        track_visibility="onchange",
        help="When the agreement ends.")
    version = fields.Integer(
        string="Version",
        default=1,
        copy=False,
        help="The versions are used to keep track of document history and "
             "previous versions can be referenced.")
    revision = fields.Integer(
        string="Revision", track_visibility="onchange",
        default=0,
        copy=False,
        help="The revision will increase with every save event.")
    num_dias = fields.Integer(
        string="Days without charge", track_visibility="onchange",
        default=0,
        copy=False)
    anexo = fields.Boolean(string='May have attachments', default=True, track_visibility="onchange",
                           help="Check if you do not want this contract to have annexes.")
    readonly_anexo = fields.Boolean(string='No Edit', default=False)
    description = fields.Text(
        string="Internal Notes",
        track_visibility="onchange",
        help="Description of the agreement")
    dynamic_description = fields.Text(
        compute="_compute_dynamic_description",
        string="Dynamic Description",
        help="Compute dynamic description")
    template_agreement_id = fields.Many2one(
        "agreement", store=True, track_visibility="onchange",
        string="Template") # domain="[('fecha_termino_date', '>=', hoy_date), ('type_contrib', '=', type_contrib_partner), ('is_template', '=', 'True'), ('payment_method_domain', '=', payment_method), ('type_partner_domain', '=', type_partner)]",
    late_fine = fields.Float("Fine per day late", digits='Product Price', track_visibility="onchange")
    color = fields.Integer(string="Color", track_visibility="onchange")
    company_signed_date = fields.Date(
        string="Signed on",
        track_visibility="onchange",
        help="Date the contract was signed by Company.")
    partner_signed_date = fields.Date(
        string="Signed on (Partner)",
        track_visibility="onchange",
        help="Date the contract was signed by the Partner.")
    term = fields.Integer(
        string="Term (Months)",
        track_visibility="onchange",
        help="Number of months this agreement/contract is in effect with the "
             "partner.")
    expiration_notice = fields.Integer(
        string="Exp. Notice (Days)",
        track_visibility="onchange",
        help="Number of Days before expiration to be notified.")
    change_notice = fields.Integer(
        string="Change Notice (Days)",
        track_visibility="onchange",
        help="Number of Days to be notified before changes.")
    special_terms = fields.Text(
        string="Special Terms",
        track_visibility="onchange",
        help="Any terms that you have agreed to and want to track on the "
             "agreement/contract.")
    dynamic_special_terms = fields.Text(
        compute="_compute_dynamic_special_terms",
        string="Dynamic Special Terms",
        help="Compute dynamic special terms")
    increase_type_id = fields.Many2one(
        "agreement.increasetype",
        string="Increase Type",
        track_visibility="onchange",
        help="The amount that certain rates may increase.")
    termination_requested = fields.Date(
        string="Termination Requested Date",
        track_visibility="onchange",
        help="Date that a request for termination was received.")
    termination_date = fields.Date(
        string="Termination Date",
        track_visibility="onchange",
        help="Date that the contract was terminated.")
    reviewed_date = fields.Date(
        string="Reviewed Date", track_visibility="onchange")
    reviewed_user_id = fields.Many2one(
        "res.users", string="Reviewed By", track_visibility="onchange")
    approved_date = fields.Date(
        string="Approved Date", track_visibility="onchange")
    approved_user_id = fields.Many2one(
        "res.users", string="Approved By", track_visibility="onchange")
    currency_id = fields.Many2one("res.currency", string="Currency", track_visibility="onchange")
    partner_contact_id = fields.Many2one(
        "res.partner",
        string="Partner Contact", track_visibility="onchange",
        copy=True,
        domain="[('type', '=', 'delivery')]",
        help="The primary partner contact (If Applicable).")
    partner_contact_phone = fields.Char(
        related="partner_contact_id.phone", string="Partner Phone", track_visibility="onchange")
    partner_contact_email = fields.Char(
        related="partner_contact_id.email", string="Partner Email", track_visibility="onchange")
    company_contact_id = fields.Many2one(
        "res.partner",
        string="Company Contact",
        copy=True, track_visibility="onchange",
        help="The primary contact in the company.")
    company_contact_phone = fields.Char(
        related="company_contact_id.phone", string="Phone", track_visibility="onchange")
    company_contact_email = fields.Char(
        related="company_contact_id.email", string="Email", track_visibility="onchange")
    use_parties_content = fields.Boolean(
        string="Use parties content", track_visibility="onchange",
        help="Use custom content for parties")
    company_partner_id = fields.Many2one(
        related="company_id.partner_id", string="Company's Partner", track_visibility="onchange")
    repres_legal1 = fields.Many2one(
        "res.users", string="Primer Representante Legal", track_visibility="onchange")
    repres_legal2 = fields.Many2one(
        "res.users", string="Segundo Representante Legal", track_visibility="onchange")
    repres_legal3 = fields.Many2one(
        "res.users", string="Tercer Representante Legal", track_visibility="onchange")
    ceder = fields.Boolean(string='Assign/Transfer contract', default=False, track_visibility="onchange",
                           help="Check if you do not want this contract to have the possibility of assigning/transferring the contract (contract version).")
    req_firma = fields.Boolean(string='¿Requires Signature?', default=True, track_visibility="onchange",
                               help="Check if you want this contract to require a signature or not and if it is external or from Maihue")
    template_child = fields.Boolean(string='Annex Template', default=False, track_visibility="onchange",
                                    help="Check if this template is contract or annex")
    expiration_date = fields.Date(
        string="Expiration date", track_visibility="onchange", help="Date on which the template expires",
        default='9999-12-31')
    payment_period = fields.Many2one(
        "agreement.payment.period", required=False, #domain="[('id', 'in', payment_period_domain)]",
        string="Payment Periodicity", track_visibility="onchange")
    payment_method = fields.Many2one(
        "agreement.payment.method", required=False, #domain="[('id', 'in', payment_method_domain)]",
        string="Payment method", track_visibility="onchange")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment deadline', track_visibility="onchange"
                                      #,domain="[('id', 'in', payment_deadline_domain)]"
                                      )
    payment_method_domain = fields.Many2many('agreement.payment.method', 'method_agreement_rel', 'method_id',
                                             'agreement_id', track_visibility="onchange",
                                             string='Payment method')
    payment_period_domain = fields.Many2many('agreement.payment.period', 'period_agreement_rel', 'period_id',
                                             'agreement_id', track_visibility="onchange",
                                             string='Payment Periodicity')
    payment_deadline_domain = fields.Many2many('account.payment.term', 'deadline_agreement_rel', 'deadline_id',
                                               'agreement_id', track_visibility="onchange",
                                               string='Payment deadline')
    team_id_domain = fields.Many2many('crm.team', 'team_agreement_rel', 'team_id',
                                      'agreement_id', track_visibility="onchange",
                                      string='Sales team')
    exception_team_id_domain = fields.Many2many('crm.team', 'team_exc_agreement_rel', 'team_id',
                                      'agreement_id', track_visibility="onchange",
                                      string='Exception Sales team')
    initemplate_date = fields.Date(
        string="Template start date", track_visibility="onchange")
    type_partner = fields.Many2one(
        "agreement.type.partner", required=False, track_visibility="onchange", #compute="_compute_type_partner",
        string="Type of contract", help="type of client (house, company, HORECA - INTERNAL, HORECA - SELF-BOTTLING)")
    parent_template_id = fields.Many2one(
        "agreement", track_visibility="onchange",
        string="Father Template",
        help="Father Template"
    )
    req_orden = fields.Boolean(string='Allows purchase order or prior contract order?', default=False, track_visibility="onchange",
                               help="Check if you want this contract to require a purchase order or prior contract order")
    fecha_termino_date = fields.Date(
        string="End date", track_visibility="onchange")
    fecha_cobro = fields.Date(
        string="Collection Date", track_visibility="onchange", invisible=True)
    fecha_activacion = fields.Date(
        string="Approval date", track_visibility="onchange")
    test_day_domain = fields.Many2many('agreement.test.day', 'test_day_rel', 'test_day_id',
                                       'agreement_id', invisible=True, track_visibility="onchange",
                                       string='Days without charge')
    product_domain = fields.Many2many('product.product', 'product_domain_rel', 'product_id', 'agreement_id',
                                      string='Services', track_visibility="onchange")
    zona_domain = fields.Many2many('zona.comercial', 'agreement_zona_domain', 'zona_id',
                                   'agreement_id',
                                   string='Zonas Comerciales',
                                   track_visibility='onchange')
    test_day = fields.Many2one(
        "agreement.test.day", required=False, track_visibility="onchange",
        string="Days without charge")
    revisado_check = fields.Boolean(string='Revisado', default=False, track_visibility="onchange")
    fecha_repres1 = fields.Date(
        string="Fecha Firma R1", track_visibility="onchange")
    fecha_repres2 = fields.Date(
        string="Fecha Firma R2", track_visibility="onchange")
    fecha_repres3 = fields.Date(
        string="Fecha Firma R3", track_visibility="onchange")
    fecha_envio1 = fields.Date(
        string="Fecha Envio R1", track_visibility="onchange")
    fecha_envio2 = fields.Date(
        string="Fecha Envio R2", track_visibility="onchange")
    fecha_envio3 = fields.Date(
        string="Fecha Envio R3", track_visibility="onchange")
    type_contrib_partner = fields.Many2one(
        "agreement.type.contrib", string='Type of taxpayer', required=False, related='partner_id.type_contrib', track_visibility="onchange")
    type_contrib = fields.Many2one(
        "agreement.type.contrib", required=False, track_visibility="onchange",
        string="Type of taxpayer", domain=[("code", "not in", ['ig', 'na', 'igp'])])
    type_contrib_domain = fields.Many2many('agreement.type.contrib', 'agreement_type_contrib_rel', 'tupe_domain_id',
                                           'agreement_id', track_visibility="onchange",
                                           string='Type of taxpayer')
    pricelist_id = fields.Many2one('product.pricelist', 'Rate', readonly=False, track_visibility="onchange")
    agreement_discount = fields.Many2one(
        "agreement.discount", required=False, track_visibility="onchange",
        string="Discount")
    partner_domain = fields.Many2many('res.partner', 'partner_agreement_rel', 'partner_id', 'agreement_id',
                                      string='Clients', track_visibility="onchange")
    type_partner_domain = fields.Many2many('agreement.type.partner', 'agreement_type_partner_rel', 'type_id',
                                           'agreement_id', default="", track_visibility="onchange",
                                           string='Type of contract')
    pricelist_id_domain = fields.Many2many('product.pricelist', 'agreement_pricelist_rel', 'pricelist_id',
                                           'agreement_id', track_visibility="onchange",
                                           string='Rate')
    signed_document_ids = fields.One2many(
        "agreement.signed.extra", "agreement_id", string="Extra Files", copy=True, track_visibility="onchange")
    tax_id = fields.Many2one('account.tax', string='Taxes', track_visibility="onchange",
                             domain=[('type_tax_use', '=', 'sale'), ('active', '=', True)], default=1)
    # tax_id_domain = fields.Many2many('account.tax', 'agreement_taxes_rel', 'taxes_id',
    #                                        'agreement_id',
    #                                        string='Impuestos')
    gestor_id = fields.Many2one('res.users', string='Managed by', track_visibility="onchange")
    team_id = fields.Many2one('crm.team', 'Sales team', readonly=False, track_visibility="onchange")
    pre_liquid = fields.Boolean('Pre-settlement', track_visibility="onchange")
    incidencia = fields.Boolean('Contractual Incidence', default=False, track_visibility="onchange")
    prueba_aprob = fields.Boolean('Proof without Signature', default=False, track_visibility="onchange", help="La linea de contrato no puede pasar a Prueba en Curso si no esta Firmado el contrato y si no posee metodo de pago al menos que el Check de Prueba sin Firma este activado")
    perm_act = fields.Boolean('Allows partial activation', default=False, track_visibility="onchange", help='Permite pasar el Contrato a Validacion Administrativa con solamente una linea en Validacion Administrativa, de lo contrario deben estar todas las lineas en Validacion Administrativa para poder pasar a Validacion Administrativa para el contrato o que esten canceladas o no vigentes')
    hoy_date = fields.Date(
        string="today", default=fields.Date.context_today, track_visibility="onchange")
    parties = fields.Html(
        string="Parties",
        track_visibility="onchange",
        default=_get_default_parties,
        help="Parties of the agreement")
    dynamic_parties = fields.Html(
        compute="_compute_dynamic_parties",
        string="Dynamic Parties",
        help="Compute dynamic parties")
    agreement_subtype_id = fields.Many2one(
        "agreement.subtype",
        string="Agreement Sub-type",
        track_visibility="onchange",
        help="Select the sub-type of this agreement. Sub-Types are related to "
             "agreement types.")
    product_ids = fields.Many2many(
        "product.template", string="Products & Services", track_visibility="onchange")
    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        track_visibility="onchange",
        help="Select the user who manages this agreement.")
    company_signed_user_id = fields.Many2one(
        "res.users",
        string="Signed By",
        track_visibility="onchange",
        help="The user at our company who authorized/signed the agreement or "
             "contract.")
    partner_signed_user_id = fields.Many2one(
        "res.partner",
        string="Firmante R1",
        track_visibility="onchange",
        help="Contact on the account that signed the agreement/contract.")
    parent_agreement_id = fields.Many2one(
        "agreement", track_visibility="onchange",
        string="Parent Agreement",
        help="Link this agreement to a parent agreement. For example if this "
             "agreement is an amendment to another agreement. This list will "
             "only show other agreements related to the same account.")
    renewal_type_id = fields.Many2one(
        "agreement.renewaltype",
        string="Renewal Type",
        track_visibility="onchange",
        help="Describes what happens after the contract expires.")
    recital_ids = fields.One2many(
        "agreement.recital", "agreement_id", string="Recitals", copy=True, track_visibility="onchange")
    sections_ids = fields.One2many(
        "agreement.section", "agreement_id", string="Sections", copy=True, track_visibility="onchange")
    clauses_ids = fields.One2many(
        "agreement.clause", "agreement_id", string="Clauses", track_visibility="onchange")
    appendix_ids = fields.One2many(
        "agreement.appendix", "agreement_id", string="Appendices", copy=True, track_visibility="onchange")
    previous_version_agreements_ids = fields.One2many(
        "agreement",
        "parent_agreement_id", track_visibility="onchange",
        string="Previous Versions",
        copy=False,
        domain=[("active", "=", False)])
    child_agreements_ids = fields.One2many(
        "agreement",
        "parent_agreement_id", track_visibility="onchange",
        string="Child Agreements",
        copy=False,
        domain=[("active", "=", True)])
    line_ids = fields.One2many(
        "agreement.line",
        "agreement_id", track_visibility="onchange",
        string="Contract Lines",
        copy=False)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("inactive", "Inactive")],
        default="draft",
        track_visibility="always")
    notification_address_id = fields.Many2one(
        "res.partner",
        string="Notification Address", track_visibility="onchange",
        help="The address to send notificaitons to, if different from "
             "customer address.(Address Type = Other)")
    signed_contract_filename = fields.Char(string="Filename", track_visibility="onchange")
    signed_contract = fields.Binary(
        string="Signed Document", track_visibility="always")

    # Dynamic field editor
    field_domain = fields.Char(string='Field Expression',
                               default='[["active", "=", True]]')
    default_value = fields.Char(
        string="Default Value",
        help="Optional value to use if the target field is empty.")
    copyvalue = fields.Char(
        string="Placeholder Expression",
        help="""Final placeholder expression, to be copy-pasted in the desired
             template field.""")
    document_ids = fields.One2many(
        "agreement.document", "agreement_id", string="Documentos Extra", copy=True)
    # rentals_ids = fields.One2many(
    #     "rentals.line",
    #     "agreement_id",
    #     string="Rentals Orders",
    #     copy=False)
    invoicing_ids = fields.One2many(
        "invoice.line",
        "agreement_id",
        string="Invoices",
        copy=False)
    # document
    title = fields.Char(
        string="Title",
        help="The title is displayed on the PDF." "The name is not.")
    content = fields.Html(string="Content")
    dynamic_content = fields.Html(
        compute="_compute_dynamic_content",
        string="Dynamic Content",
        help="compute dynamic Content")
    company_signed_user_dos_id = fields.Many2one(
        "res.users",
        string="Firmante R2",
        track_visibility="onchange",
        help="Segundo Usuario que autorizo/firmo el acuerdo o contrato")
    company_signed_user_tres_id = fields.Many2one(
        "res.users",
        string="Firmante R3",
        track_visibility="onchange",
        help="Tercera Usuario que autorizo/firmo el acuerdo o contrato")
    extra_ids = fields.One2many(
        "agreement.extra", "agreement_id", string="Documentos Oficiales", copy=True, track_visibility="onchange")
    referidor_id = fields.Many2one('res.partner', string='referrer', domain=[("parent_id", "=", False)], track_visibility="onchange")
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Contact Billing",
        copy=True,
        track_visibility='onchange',
        domain="[('type', '=', 'invoice'), ('parent_id', '=', partner_id)]")
    partner_admin_id = fields.Many2one(
        "res.partner",
        string="Administrador Contrato Cliente",
        copy=True,
        track_visibility='onchange')
    admin_id = fields.Many2one('res.users', string='Administrador de Contrato Maihue', track_visibility="onchange")
    partner_invoice_id_domain = fields.Many2many('res.partner', 'partner_invoice_rel', 'partner_id',
                                       'agreement_id',  #compute='_compute_partner_invoice_id',
                                       string='Dominio contacto facturacion')
    state_firm1 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma R1', track_visibility="onchange")
    state_firm2 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma R2', track_visibility="onchange")
    state_firm3 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma R3', track_visibility="onchange")
    state_firm4 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma', track_visibility="onchange")
    agreement_penalty1 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 1", readonly=False)
    agreement_penalty2 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 2", readonly=False)
    agreement_penalty3 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 3", readonly=False)
    agreement_penalty4 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 4", readonly=False)
    agreement_penalty5 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 5", readonly=False)
    charge_extra_ids = fields.One2many(
        "agreement.extra.charges", "agreement_id", string="Extra Charges", copy=True, track_visibility="onchange")
    total_service = fields.Float('Total', store=True, compute='_compute_total_lines_contract', digits='Product Price', track_visibility="onchange")
    product_instalation = fields.Many2one(
        "product.product", readonly=True, track_visibility='onchange', string="Product Installation")
    product_desistalation = fields.Many2one(
        "product.product", readonly=True, track_visibility='onchange', string="Producto Baja")
    template_domain = fields.Many2many('agreement', 'template_agreement_rel', 'parent_id',
                                             'agreement_id', #compute='_compute_template_agreement_id',
                                             string='Domain for contract', track_visibility="onchange")
    stage_id = fields.Many2one(
        "agreement.stage",
        string="Stage", default=1,
        group_expand="_read_group_stage_ids",
        help="Select the current stage of the agreement.",
        track_visibility="onchange",
        index=True)
    invoice_ids = fields.One2many(
        'account.move', 'agreement_id', string='Invoices', readonly=True)
    out_invoice_count = fields.Integer(
        compute='_compute_invoice_count', string='# of Customer Invoices')
    in_invoice_count = fields.Integer(
        compute='_compute_invoice_count', string='# of Vendor Bills')
    sale_id = fields.Many2one('sale.order', string='Sales Order', track_visibility="onchange")
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        copy=False)
    crm_lead_id = fields.Many2one('crm.lead', "CRM Oportunity", help="Crm for which we are creating a contract",
                                  required=False, track_visibility="onchange")
    # sale_ids = fields.One2many(
    #     'sale.order', 'agreement_id', string='Sale Orders', readonly=True)
    # sale_count = fields.Integer(
    #     compute='_compute_sale_count', string='# of Sale Orders')
    canal_id = fields.Many2one(
        'crm.canal',
        string='Channel', track_visibility="onchange")
    subcanal_id = fields.Many2one(
        'crm.subcanal',
        string='Sub Channel', track_visibility="onchange")
    reference_ids = fields.One2many(
        "l10n_cl.account.invoice.reference", "agreement_id", track_visibility="onchange")
    agreement_l10ncl = fields.Many2one(
        "agreement.l10ncl", required=False,
        string="Master Required Documents", track_visibility="onchange")
    l10ncl_domain = fields.Many2many('agreement.l10ncl', 'l10ncl_rel', 'l10ncl_id',
                                     'agreement_id',
                                     string='Required Documents')
    state_ajust = fields.Selection(selection=[
        ('P', 'Pendiente Realizar'),
        ('R', 'Realizado'),
        ('C', 'Cancelado')], string='Status Setting', track_visibility="onchange")
    date_ajuste = fields.Date(
        string="Date Adjustment of Conditions",
        track_visibility="onchange",
        help="Date Adjustment of Conditions")
    check_exception = fields.Boolean(related='crm_lead_id.check_exception', track_visibility="onchange")
    exception = fields.Boolean(related='crm_lead_id.exception', track_visibility="onchange")
    canal_id = fields.Many2one(
        'crm.canal',
        string='Canal', track_visibility="onchange")
    subcanal_id = fields.Many2one(
        'crm.subcanal',
        string='Sub Canal', track_visibility="onchange")
    job_id = fields.Many2one('hr.job', 'Job that Approves Exception', track_visibility="onchange")
    maintences_ids = fields.One2many('helpdesk.ticket', 'agreement_id', string='Mantenciones', copy=True,
                                     auto_join=True, track_visibility="onchange")
    log_admin_ids = fields.One2many(
        "log.admin", "agreement_id", string="Administrador de Contrato Maihue", copy=False)
    borrador_btn = fields.Boolean(string='borrador boton', track_visibility="onchange")
    act_sfirma = fields.Boolean(string='Permite Activación Sin Firma y Método de pago', track_visibility="onchange", help="La linea de contrato no puede pasar a Validacion Admin si no esta Firmado el contrato y si no posee metodo de pago, al menos que el Check de activacion sin Firma este activado")
    ticket_btn = fields.Boolean(string='Solicitud de Baja Activa', track_visibility="onchange")
    motivo_id = fields.Many2one('motivo.cancel', 'Motivo', readonly=False)
    motivo_cancel = fields.Text('Motivo Cancelación', readonly=False, track_visibility='onchange'
                                )
    vali = fields.Boolean(
        string="Paso a Validacion",
        default=False,
        copy=False
    )
    revisado_contract = fields.Boolean(
        string="Paso a revision",
        default=False,
        copy=False
    )
    activado_btn = fields.Boolean(string='Si estuvo activado o no', track_visibility="onchange")

    @api.onchange('partner_id', 'extra_ids.partner_signed_user_id', 'partner_signed_user_id')
    def onchange_domain_partner_repres_doc(self):
        if self.partner_id:
            if self.partner_id.company_type == 'company':
                partners = self.env['res.partner'].search(
                    [('parent_id', '=', self.partner_id.id), ('repres_legal', '=', True)])
            else:
                partners = self.env['res.partner'].search(
                    [('id', '=', self.partner_id.id), ('repres_legal', '=', True)])
            if partners:
                for doc in self.extra_ids:
                    doc.partner_repres_ids_domain = partners.ids
                    doc.partner_signed_user_id = False
                    doc.email_signed_user = False
                    doc.company_signed_user_dos_id = False
                    doc.email_signed_user_dos = False
                    doc.company_signed_user_tres_id = False
                    doc.email_signed_user_tres = False
            else:
                for doc in self.extra_ids:
                    doc.partner_repres_ids_domain = False
                    doc.partner_signed_user_id = False
                    doc.email_signed_user = False
                    doc.company_signed_user_dos_id = False
                    doc.email_signed_user_dos = False
                    doc.company_signed_user_tres_id = False
                    doc.email_signed_user_tres = False

    def action_agreement(self):
        action = self.env.ref('agreement.agreement_form').read()[0]
        action['views'] = [(self.env.ref('agreement.agreement_form').id, 'form')]
        action['context'] = {
                             'name': self.name,
                             'code': self.name,
                            }
        return action

    def action_view_agreement_line(self):
        action = self.env.ref('agreement_blueminds.contract_line_action').read()[0]
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_agreement_id': self.id
        }
        action['domain'] = [('agreement_id', '=', self.id)]
        agreement = self.mapped('line_ids').filtered(lambda l: l.state in (
        'draft', 'pen', 'reage', 'pre', 'prueba', 'fallida', 'win', 'vali', 'revisado', 'act', 'sol_can', 'pro_can',
        'cancelado', 'sol_baja', 'proceso', 'no_vigente'))
        if len(agreement) == 1:
            action['views'] = [(self.env.ref('agreement_blueminds.contract_line_form').id, 'form')]
            action['res_id'] = agreement.id
        return action

    @api.model
    def create(self, vals):
        tiene_seq = False
        father = False
        if 'start_date' in self.env.context:
            vals['journal_id'] = self.env.context.get('journal_id')
        if 'stage_id' in vals:
            if vals['stage_id'] == 7:
                self.write({'fecha_activacion': datetime.now().date(), 'approved_user_id': self._uid, 'approved_date': datetime.now().date()})
                #maintenance = self.agree_maintenance()
            if vals['stage_id'] == 9 or vals['stage_id'] == 12:
                cancelled = self.agree_cancelled()
        if not vals.get('stage_id'):
            vals["stage_id"] = 1
            #self.env.ref("agreement_stage_new").id
        if vals.get('is_template'):
            vals['name'] = vals['name']
            tiene_seq = True
        if vals.get('is_template'):
            father = True
            if 'parent_template_id' in vals:
                if vals['parent_template_id']:
                    father = False
                    agreement = self.env['agreement'].search([('id', '=', vals['parent_template_id'])])
                    if not agreement.anexo:
                        raise UserError(_(
                            'Disculpe, No se puede crear la plantilla, \n \n  Porque la plantilla padre seleccionada no acepta anexos'))
        if not vals.get('is_template'):
            if 'parent_agreement_id' in vals:
                if vals['parent_agreement_id']:
                    agreement = self.env['agreement'].search([('id', '=', vals['parent_agreement_id'])])
                    if not agreement.anexo:
                        raise UserError(_(
                            'Disculpe, No se puede crear la plantilla, \n \n  Porque la plantilla padre seleccionada no acepta anexos'))
                    numa = agreement.name.split("-")
                    vals['name'] = str(numa[0]) + '-1'
                    no_existe_a = False
                    while (no_existe_a == False):
                        existe_a = self.env['agreement'].search([('name', '=', vals['name'])])
                        if existe_a:
                            num = vals['name'].split("-")
                            prox = int(num[-1]) + 1
                            vals['name'] = str(numa[0]) + '-' + str(prox)
                        if not existe_a:
                            no_existe_a = True
                    tiene_seq = True
            if not tiene_seq:
                seq = str(self.env['ir.sequence'].next_by_code('agreement_seq'))
                vals['name'] = str(seq) + '-0'
                father = True
                no_existe = False
                while (no_existe == False):
                    existe = self.env['agreement'].search([('name', '=', vals['name'])])
                    if existe:
                        father = False
                        num = vals['name'].split("-")
                        prox = int(num[-1]) + 1
                        vals['name'] = str(seq) + '-' + str(prox)
                    if not existe:
                        no_existe = True

        vals['father'] = father
        return super(Agreement, self).create(vals)

    def write(self, vals):
        if 'admin_id' in vals:
            date = datetime.now()
            if self.admin_id:
                # desincorporado
                log_vals = {
                    'agreement_id': self.id,
                    'name': self.admin_id.id,
                    'user_id': self.write_uid.id,
                    'date': date,
                    'state': 'des',
                    'vigente': False,
                }
                self.env['log.admin'].create(log_vals)
            # asignado
            log_vals = {
                'agreement_id': self.id,
                'name': vals['admin_id'],
                'user_id': self.write_uid.id,
                'date': date,
                'state': 'asig',
                'vigente': True,
            }
            self.env['log.admin'].create(log_vals)

        if 'parent_agreement_id' in vals:
            if vals.get('parent_agreement_id'):
                vals['father'] = False
                agreement = self.env['agreement'].search([('id', '=', vals['parent_agreement_id'])])
                numa = agreement.name.split("-")
                vals['name'] = str(numa[0]) + '-1'
                no_existe_a = False
                while (no_existe_a == False):
                    existe_a = self.env['agreement'].search([('name', '=', vals['name'])])
                    if existe_a:
                        num = vals['name'].split("-")
                        prox = int(num[-1]) + 1
                        vals['name'] = str(agreement.name) + '-' + str(prox)
                    if not existe_a:
                        no_existe_a = True
            else:
                vals['father'] = True
                agreement = self.env['agreement'].search([('id', '=', self.id)])
                numa = agreement.name.split("-")
                vals['name'] = str(numa[0]) + '-1'
                no_existe_a = False
                while (no_existe_a == False):
                    existe_a = self.env['agreement'].search([('name', '=', vals['name'])])
                    if existe_a:
                        num = vals['name'].split("-")
                        prox = int(num[-1]) + 1
                        vals['name'] = str(agreement.name) + '-' + str(prox)
                    if not existe_a:
                        no_existe_a = True
        if 'partner_id' in vals:
            if self.crm_lead_id:
                crm = self.env['crm.lead'].search([('id', '=', self.crm_lead_id.id)])
                crm.with_context(agreement_exist=True).write({'partner_id': vals.get('partner_id')})
                if self.crm_lead_id.crm_line_ids:
                    for line in self.crm_lead_id.crm_line_ids:
                        line.write({'partner_contact_id': False})
        if 'gestor_id' in vals:
            if self.crm_lead_id:
                crm = self.env['crm.lead'].search([('id', '=', self.crm_lead_id.id)])
                crm.write({'user_id': vals.get('gestor_id')})
        if 'canal_id' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'canal_id': vals.get('canal_id')})
        if 'subcanal_id' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'subcanal_id': vals.get('subcanal_id')})
        if 'team_id' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'team_id': vals.get('team_id')})
        if 'type_partner' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'type_partner': vals.get('type_partner')})
        if 'template_agreement_id' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'template_agreement_id': vals.get('template_agreement_id')})
        if 'payment_term_id' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'payment_term_id': vals.get('payment_term_id')})
        if 'payment_period' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'payment_period': vals.get('payment_period')})
        if 'type_partner' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'type_partner': vals.get('type_partner')})
        if 'payment_method' in vals:
            if self.crm_lead_id:
                self.crm_lead_id.write({'payment_method': vals.get('payment_method')})
            if self.father:
                agreements = self.env['agreement'].search([('parent_agreement_id', '=', self.id)])
                if agreements:
                    for agree in agreements:
                        agree.write({'payment_method': vals.get('payment_method')})
                        agree.crm_lead_id.write({'payment_method': vals.get('payment_method')})
            rentals = self.env['sale.order'].search([('agreement_id', '=', self.id), ('state', '=', 'draft')])
            if rentals:
                for rental in rentals:
                    rental.write({'payment_method': vals['payment_method']})
        if 'card_number' in vals:
            if self.father:
                # solo aplica para las plantillas hijas que posean
                agreements = self.env['agreement'].search([('parent_agreement_id', '=', self.id)])
                if agreements:
                    agreements.write({'card_number': vals.get('card_number')})
            rentals = self.env['sale.order'].search([('agreement_id', '=', self.id)])
            if rentals:
                invoices_line = self.env['account.move.line'].search([('sale_line_ids', 'in', rentals.ids)]) # , ('status_payment', '=', 'pending'), ('payment_state', '!=', 'paid')
                for invoice in invoices_line:
                    if invoice.move_id.status_payment in ['pending', 'rejected'] and invoice.move_id.payment_state != 'paid':
                        if invoice.move_id.method_payment_id.id == vals['card_number']:
                            invoice.move_id.write(
                                {'method_payment_id': vals['card_number'], 'status_payment': 'pending',
                                 'payment_method': self.payment_method.id, 'method_payment_id_alt': False,
                                 'alter_paid': False, 'tarj_dis': 'igual'})
                        else:
                            invoice.move_id.write(
                                {'method_payment_id': vals['card_number'], 'status_payment': 'pending',
                                 'payment_method': self.payment_method.id, 'method_payment_id_alt': False,
                                 'alter_paid': False, 'tarj_dis': 'dif',
                                 'method_payment_id_old': invoice.move_id.method_payment_id.id,
                                 'status_payment_old': 'rejected',
                                 'detall_status_payment_old': invoice.move_id.detall_status_payment})
        if not self.is_template:
            if self.template_agreement_id:
                template_agreement = self.env['agreement'].browse(self.template_agreement_id.id)
                # if template_agreement.extra_ids:
                #     new = template_agreement.extra_ids.copy()
                #     new.write({'agreement_id': vals['template_agreement_id']})
        res = super(Agreement, self).write(vals)
        if not self.reference_ids:
            orders = self.env['sale.order'].search(
                [('agreement_id', '=', self.id), ('state', '=', 'draft')])
            orders.write({'reference_oc': False})
        if self.reference_ids:
            for ref in self.reference_ids:
                if ref.active_s == True:
                    orders = self.env['sale.order'].search(
                        [('agreement_id', '=', self.id), ('state', '=', 'draft'),
                         ('inicio_fecha_alquiler', '<=', ref.date_init)])
                    for orden in orders:
                        orden.write({'reference_oc': ref.id})
                    if not orders:
                        orders = self.env['sale.order'].search(
                            [('agreement_id', '=', self.id), ('state', '=', 'draft')])
                        for orden in orders:
                            orden.write({'reference_oc': False})
        return res

    def pre_prueba(self):
        today = datetime.now()
        if not self.line_ids:
            raise UserError(_('Lo Siento, Por favor cree una linea de contrato antes'))
        state_id = self.env['agreement.stage'].search([('name', '=', 'PRE PRUEBA')], limit=1)
        project_id = self.env['project.project'].search([('name', '=', 'Servicio externo')], limit=1).id
        if state_id:
            self.write({'stage_id': state_id.id})
        # self.write({'stage_id': 2})
        for line in self.line_ids:
            # /// new
            categ_inst = False
            exist_inst = self.env['project.task.template'].search([('instalation', '=', True)], limit=1,
                                                                  order='id')
            if not exist_inst:
                raise UserError(_(
                    'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede pasar a preprueba sin tener una plantilla destinada para la instalacion, \n \n Por favor comuniquese con un Administrador'))
            categ_inst = self.env['helpdesk.tag'].search([('instalation', '=', True)], limit=1,
                                                                  order='id')
            if not categ_inst:
                raise UserError(_(
                    'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede pasar a preprueba sin tener una categoria destinada para la instalacion, \n \n Por favor comuniquese con un Administrador'))
            categoria = self.env['categoria.maihue.template'].search([('project_template_id', '=', exist_inst.id)], limit=1,
                                                                  order='id')

            ticket_man = self.env['helpdesk.ticket'].with_context(instalation=True).create({
                'name': 'Instalación ' + line.product_id.name,
                'partner_id': line.agreement_id.partner_id.id,
                # 'assign_date': self.date_test,
                'fecha_registro_ticket': today,
                'agreement_id': line.agreement_id.id,
                'ticket_type_id': categoria.categoria_id.ticket_type_id.id,
                'categoria_maihue_id': categ_inst.id,
                'agreement_line_ids': line.id,
                'partner_email': line.agreement_id.partner_id.email,
                # 'user_id': line.mantenedor or False,
            })
            invite = self.env['survey.invite']
            url_invite = werkzeug.urls.url_join(exist_inst.survey_id.get_base_url(),
                                                exist_inst.survey_id.get_start_url()) if invite.survey_id else False
            order_lineM = self.env['project.task'].create({
                'name': 'Instalación ' + line.product_id.name,
                'partner_id': line.agreement_id.partner_id.id,
                'helpdesk_ticket_id': ticket_man.id,
                'admin_line_id': line.admin_line_id.id,
                'agreement_id': self.id,
                'agreement_line_id': line.id,
                #'stage_id': 4,
                'fsm_done': False,
                'project_id': project_id,
                'formulario': url_invite,
                'survey_id': exist_inst.survey_id.id,
                'type_transfer_equipment': exist_inst.type_transfer_equipment,
                'l10n_cl_delivery_guide_reason': exist_inst.l10n_cl_delivery_guide_reason,
                'task_template_id': exist_inst.id,
                'admin_line_id': line.admin_line_id.id,
                #'description': self.general_msj,
            })
            for x in line.product_id.product_related_ids:
                if x.is_principal:
                    if x.product_id != line.product_principal:
                        continue
                order_lineM_l = self.env['project.task.product'].create({
                    'product_id': x.product_id.id,
                    'description': x.name,
                    'planned_qty': x.qty,
                    'product_uom': x.product_id.uom_id.id,
                    'time_spent': x.time_spent,
                    'task_id': order_lineM.id,
                    'is_principal': x.is_principal,
                })
            if line.state == 'draft':
                #fecha_cobro = self.date_test + relativedelta(days=int(line.test_day.code))
                line.write({'state': 'pen', 'instalation_btn': True, 'state_inst': 'pen',
                            'state_def': 'pen'})  # 'start_date': self.date_test, 'fecha_cobro': fecha_cobro,
                line.agreement_id.write({'borrador_btn': True})
                #line.write({'state': 'pen'})
        line_id = self._context.get('active_id', False)
        line = self.env['agreement.line'].browse(line_id)


    def borrador(self):
        state_id = self.env['agreement.stage'].search([('name', '=', 'BORRADOR')], limit=1)
        if state_id:
            self.write({'stage_id': state_id.id})
        #self.write({'stage_id': 1})

    def pend_firma(self):
        if self.charge_extra_ids:
            for charge_line in self.charge_extra_ids:
                if charge_line.price == 0 and charge_line.vali_price == False:
                    raise UserError(_(
                        'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede activar con precio cero para un servicio adicional, sin excepcion aprobada'))
        if self.line_ids:
            for line in self.line_ids:
                if not line.product_principal:
                    raise UserError(_(
                        'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no ha sido seleccionado ningun producto principal'))
                if line.price_instalacion == 0:
                    if line.vali_price_inst:
                        self.write({'stage_id': 3})
                    else:
                        raise UserError(_(
                            'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede activar con precio cero para el producto de instalacion, sin excepcion aprobada'))
                if line.price == 0:
                    if line.vali_price_men:
                        self.write({'stage_id': 3})
                    else:
                        raise UserError(_(
                            'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede activar con precio cero para el producto mensualidad, sin excepcion aprobada'))
                if line.price_instalacion > 0 and line.price > 0:
                    self.write({'stage_id': 3})

        else:
            raise UserError(_(
                'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no ha sido creada ninguna linea de contrato'))
        #self.write({'stage_id': 3})

    def firmado(self):
        self.write({'stage_id': 4})
        for line in self.line_ids:
            line.write({'state': 'win'})

    def en_vali(self):
        en_vali = False
        if self.perm_act:
            for line in self.line_ids:
                if line.state in ['vali']:
                    en_vali = True
            if en_vali:
                #stage_id = self.env['crm.stage'].search(['|', ('is_won', '=', True), ('name', '=', 'Perdida')])
                self.write({'stage_id': 5, 'vali': True})
            else:
                raise UserError(_(
                    'Disculpe, No se puede avanzar con el contrato sin ninguna linea en etapa de validación o revisado'))
        else:
            for line in self.line_ids:
                if line.state in ['vali']:
                    en_vali = True
            if en_vali:
                for line2 in self.line_ids:
                    if line2.state not in  ['vali','revisado','act','cancelado', 'no_vigente']:
                        raise UserError(_(
                            'Disculpe, No se puede avanzar con el contrato con lineas en etapas anterior a validación o etapa distinta a cancelado y no vigente, al menos que se encuentre activo el check "Permite la activación parcial"'))
                # state_id = self.env['agreement.stage'].search([('name', '=', 'PRUEBA GANADA')], limit=1)
                # if state_id:
                self.write({'stage_id': 5, 'vali': True})
            else:
                raise UserError(_(
                    'Disculpe, No se puede avanzar con el contrato sin ninguna linea en etapa de validación o revisado'))


    def activar(self):
        #self.write({'stage_id': 6})
        for line in self.line_ids:
            line.agree_maintenance()
        return True

    def revisado(self):
        en_vali = False
        if self.perm_act:
            for line in self.line_ids:
                if line.state in ['revisado']:
                    en_vali = True
            if en_vali:
                # state_id = self.env['agreement.stage'].search([('name', '=', 'PRUEBA GANADA')], limit=1)
                # if state_id:
                self.write({'stage_id': 6, 'reviewed_user_id': self.write_uid.id, 'approved_user_id': self.write_uid.id,
                            'reviewed_date': datetime.now(), 'approved_date': datetime.now(), 'revisado_contract': True})
            else:
                raise UserError(_(
                    'Disculpe, No se puede avanzar con el contrato sin ninguna linea en etapa de revisado'))
        else:
            for line in self.line_ids:
                if line.state in ['revisado']:
                    en_vali = True
            if en_vali:
                for line2 in self.line_ids:
                    if line2.state not in ['revisado', 'act', 'cancelado', 'no_vigente']:
                        raise UserError(_(
                            'Disculpe, No se puede avanzar con el contrato con lineas en etapas anterior a Revisado o etapa distinta a cancelado y no vigente, al menos que se encuentre activo el check "Permite la activación parcial"'))
                self.write(
                    {'stage_id': 6, 'reviewed_user_id': self.write_uid.id, 'approved_user_id': self.write_uid.id,
                     'reviewed_date': datetime.now(), 'approved_date': datetime.now()})
            else:
                raise UserError(_(
                    'Disculpe, No se puede avanzar con el contrato sin ninguna linea en etapa de revisado'))

    def vigente(self):
        if self.status_signature != 'signed':
            raise UserError(_(
                'Disculpe, No se puede avanzar a Vigente con el contrato sin Firmar'))
        if self.state_card_number != 'active':
            raise UserError(_(
                'Disculpe, No se puede avanzar a Vigente con el contrato sin Estado Método de Pago Activo'))
        state_id = self.env['agreement.stage'].search([('name', '=', 'VIGENTE')], limit=1)
        self.write({'stage_id': state_id})
        # for line in self.line_ids:
        #     line.write({'state': 'vigente'})

    def soli_cancelar(self):
        state_id = self.env['agreement.stage'].search([('name', '=', 'SOLICITUD DE CANCELACIÓN')], limit=1)
        if state_id:
            self.write({'stage_id': state_id.id})
        #self.write({'stage_id': 10})
        # for line in self.line_ids:
        #     line.write({'state': 'sol_can'})

    def pro_cancelar(self):
        if not self.motivo_id:
            raise UserError(_(
                'Disculpe, Es necesario señalar un motivo de cancelación para poder avanzar'))
        self.write({'stage_id': 11})
        # for line in self.line_ids:
        #     line.write({'state': 'pro_can'})

    def cancelado(self):
        cance = True
        for line in self.line_ids:
            if line.state not in ['cancelado', 'post_can', 'no_vigente']:
                cance = False
        if cance:
            if self.termination_date:
                self.write({'stage_id': 12, 'end_date': self.termination_date })
            else:
                raise UserError(_(
                    'Para poder cancelar un contrato debe tener Fecha de conclusión'))
        else:
            raise UserError(_('Para poder cancelar un contrato debe tener todas las lineas de contrato descartadas o no Vigentes'))

    def sol_baja(self):
        lines_ids = []
        custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                          "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                          "sol_baja": 14, "proceso": 15, "no_vigente": 16}
        for line in self.line_ids:
            lines_ids.append([line.id, line.state])
        lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
        # for record in self.agreement_id:
        #     agreement_ids.append([record.id, record.stage_id.id])
        # status_agreement = sorted(agreement_ids, key=lambda x: agreement_indices[x[1]])
        for item in lista:
            if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                if item[1] == 'act':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea activa'))
                if item[1] == 'revisado':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea Revisada'))
                if item[1] == 'vali':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea En Validacion'))
                if item[1] == 'win':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea en Prueba Ganada'))
                if item[1] == 'prueba':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea en Prueba'))
                if item[1] == 'pre':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea en pre Prueba'))
                if item[1] == 'pen':
                    raise UserError(
                        _('Lo Siento, Antes de hacer la solicitud de baja todas las lineas deben estar en estado solicitud de baja, no debe existir una linea en Pendiente Agendar'))

        self.write({'stage_id': 14})
        # for line in self.line_ids:
        #     line.write({'state': 'sol_baja'})

    def pro_baja(self):
        self.write({'stage_id': 15})
        # for line in self.line_ids:
        #     line.write({'state': 'proceso'})

    def agree_arrepentido(self):
        if len(self.line_ids) == 1:
            self.write(
                {'stage_id': 8, 'ticket_btn': False})
        else:
            self.write(
                {'stage_id': 7, 'ticket_btn': False})

    def agree_arrepentido_invali(self):
            self.write(
                {'stage_id': 1})

    def agree_fallida(self):
        self.write({'stage_id': 19})
        #self.write({'state': 'fallida'})

    def agree_ticket(self):
        #Aqui debe crear un ticket para la esistalacion de la maquina
        self.write({'ticket_btn': True})

    def no_vigente(self):
        no_v = True
        for line in self.line_ids:
            if line.state not in ['cancelado', 'no_vigente']:
                no_v = False
        if no_v:
            if self.termination_date:
                self.write({'stage_id': 16, 'end_date': self.termination_date })
            else:
                raise UserError(_(
                    'Para poder dar de baja un contrato debe tener Fecha de Conclusión'))
        else:
            raise UserError(_('Para poder dar de baja un contrato debe tener todas las lineas de contrato Canceladas o No Vigentes'))

    # Create New Version Button
    def create_new_version(self, vals):
        for rec in self:
            if not rec.state == "draft":
                # Make sure status is draft
                rec.state = "draft"
            default_vals = {
                "name": "{} - OLD VERSION".format(rec.name),
                "active": False,
                "parent_agreement_id": rec.id,
            }
            # Make a current copy and mark it as old
            rec.copy(default=default_vals)
            # Increment the Version
            rec.version = rec.version + 1
        # Reset revision to 0 since it's a new version
        vals["revision"] = 0
        return super(Agreement, self).write(vals)

    def create_new_agreement(self):
        default_vals = {
            "name": "NEW",
            "active": True,
            "version": 1,
            "revision": 0,
            "state": "draft",
            "stage_id": 1,#self.env.ref("agreement_legal.agreement_stage_new").id,
        }
        res = self.copy(default=default_vals)
        res.sections_ids.mapped('clauses_ids').write({'agreement_id': res.id})
        return {
            "res_model": "agreement",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_id": res.id,
        }

    @api.model
    def _domain_selection(self):
        return [
            ('sale', _('Sale')),
            ('purchase', _('Purchase')),
            ]

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        arrs = []
        today = datetime.now()
        domain = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today)]
        if self.parent_agreement_id:
            domain.append(('template_child', '=', True))
        if self.template_agreement_id.team_id_domain:
            domain.append(('team_id_domain', 'in', self.team_id.ids))
        if self.template_agreement_id.partner_domain:
            domain.append(('partner_domain', 'in', self.partner_id.id))
        if self.type_contrib_partner:
            domain.append(('type_contrib', '=', self.type_contrib_partner.id))
        templates_ids = self.search(domain)
        if templates_ids:
            for x in templates_ids:
                partner_domain = False
                valid_domain = False
                if x.partner_domain:
                    partner_domain = True
                    if self.partner_id.id in x.partner_domain.ids:
                        valid_domain = True
                if partner_domain == True and valid_domain == True:
                    arrs.append(x.id)
                if partner_domain == False and valid_domain == False:
                    arrs.append(x.id)
        if self.partner_id:
            self.type_contrib = self.partner_id.type_contrib.id
            #self.type_partner_domain = self.partner_id.type_contrib.ids
            self.type_partner = self.partner_id.type_contrib.id
            self.notification_address_id = False
            for i in self.line_ids:
                i.partner_con_id = False
                i.partner_contact_id = False
            if self.partner_invoice_id:
                partners_invoice = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id), ('etiqueta_person', 'in', [5])])
                if self.partner_invoice_id.id not in partners_invoice.ids:
                    self.partner_invoice_id = False

        if arrs:
            res = {}
            res['domain'] = {'template_agreement_id': [('id', 'in', arrs)]}
            return res

    # @api.onchange('parent_agreement_id')
    # def onchange_parent_agreement_id(self):
    #     res = {}
    #     if self.parent_agreement_id:
    #         type_contrib_do = {}
    #         payment_period_do = {}
    #         payment_method_do = {}
    #         payment_deadline_do = {}
    #         for period in self.parent_agreement_id.payment_period_domain:
    #             if period.code == 'ig':
    #                 payment_period_do = [('id', 'in', self.template_agreement_id.payment_period_domain.ids)]
    #         for period in self.template_agreement_id.payment_period_domain:
    #             if period.code == 'ig':
    #                 payment_period_do = [('id', 'in', self.template_agreement_id.payment_period_domain.ids)]
    #         for period in self.template_agreement_id.payment_method_domain:
    #             if period.code == 'ig':
    #                 payment_period_do = [('id', 'in', self.template_agreement_id.payment_method_domain.ids)]
    #         for period in self.template_agreement_id.payment_period_domain:
    #             if period.code == 'ig':
    #                 payment_period_do = [('id', 'in', self.template_agreement_id.payment_period_domain.ids)]
    #         res['domain'] = {
    #             'payment_period': [('id', 'in', self.template_agreement_id.payment_period_domain.ids)],
    #             'payment_method': [('id', 'in', self.template_agreement_id.payment_method_domain.ids)],
    #             'test_day': [('id', 'in', self.template_agreement_id.test_day_domain.ids)],
    #             'type_contrib': [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)],
    #             'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
    #             #'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
    #             'payment_term_id': [('id', 'in', self.template_agreement_id.payment_deadline_domain.ids)]}
    #         self.agreement_type_id = self.template_agreement_id.agreement_type_id.id
    #         self.document_ids = self.template_agreement_id.document_ids
    #         #self.document_ids.recital_ids.recital_contrato_id = self.template_agreement_id.document_ids.recital_ids.recital_contrato_id
    #         self.recital_ids = self.template_agreement_id.recital_ids
    #         self.agreement_subtype_id = self.template_agreement_id.agreement_subtype_id
    #         self.anexo = self.template_agreement_id.anexo
    #         self.description = self.template_agreement_id.description
    #         #self.end_date = self.template_agreement_id.end_date
    #         self.special_terms = self.template_agreement_id.special_terms
    #         self.title = self.template_agreement_id.title
    #         self.num_dias = self.template_agreement_id.num_dias
    #         self.late_fine = self.template_agreement_id.late_fine
    #         self.content = self.template_agreement_id.content
    #         #self.extra_ids = self.template_agreement_id.extra_ids
    #         self.signed_document_ids = self.template_agreement_id.signed_document_ids
    #         return res

    @api.onchange('template_agreement_id', 'partner_id', 'type_partner', 'payment_period', 'team_id', 'payment_method','agreement_type_id','parent_agreement_id')
    def onchange_template_agreement(self):
        res = {}
        templates_all = self.search([])
        templates_ids_domain = []
        arrs = []
        today = datetime.now()
        domain = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today)]
        if self.parent_agreement_id:
            domain.append(('template_child', '=', True))
        if self.team_id:
            domain.append(('team_id_domain', 'in', self.team_id.id))
        if self.type_contrib_partner:
            domain.append(('type_contrib', '=', self.type_contrib_partner.id))
        if self.type_partner:
            domain.append(('type_partner_domain', 'in', self.type_partner.id))
        if self.payment_method:
            domain.append(('payment_method_domain', 'in', self.payment_method.id))
        if self.payment_period:
            domain.append(('payment_period_domain', 'in', self.payment_period.id))
        if self.payment_term_id:
            domain.append(('payment_deadline_domain', 'in', self.payment_term_id.id))
        # if self.pricelist_id:
        #     domain.append(('pricelist_id', '=', self.pricelist_id.id))
        # if self.agreement_type_id:
        #     domain.append(('agreement_type_id', '=', self.agreement_type_id.id))
        templates_ids = self.search(domain)
        templates_method = self.search(domain)
        if templates_method:
            for temp in templates_method:
                partner_domain = False
                valid_domain = False
                if temp.partner_domain:
                    partner_domain = True
                    if self.partner_id.id in temp.partner_domain.ids:
                        valid_domain = True
                if partner_domain == True and valid_domain == True:
                    templates_ids_domain.append(temp.id)
                if partner_domain == False and valid_domain == False:
                    templates_ids_domain.append(temp.id)
        if templates_ids:
            for x in templates_ids:
                partner_domain = False
                valid_domain = False
                if x.partner_domain:
                    partner_domain = True
                    if self.partner_id.id in x.partner_domain.ids:
                        valid_domain = True
                if partner_domain == True and valid_domain == True:
                    arrs.append(x.id)
                if partner_domain == False and valid_domain == False:
                    arrs.append(x.id)
                #arrs.append(x.id)
        else:
            self.template_agreement_id = ''
            # self.payment_period = ''
            # self.payment_term_id = ''
            # self.payment_method = ''
        if self.template_agreement_id:
            res['domain'] = {
                'card_number': [
                    ('type_subscription_contract', 'in', self.template_agreement_id.payment_method_domain.ids)]}
            self.agreement_type_id = self.template_agreement_id.agreement_type_id.id
            self.document_ids = self.template_agreement_id.document_ids
            #self.document_ids.recital_ids.recital_contrato_id = self.template_agreement_id.document_ids.recital_ids.recital_contrato_id
            self.recital_ids = self.template_agreement_id.recital_ids
            # self.agreement_subtype_id = self.template_agreement_id.agreement_subtype_id
            self.anexo = self.template_agreement_id.anexo
            self.description = self.template_agreement_id.description
            # self.end_date = self.template_agreement_id.end_date
            self.special_terms = self.template_agreement_id.special_terms
            # self.title = self.template_agreement_id.title
            self.num_dias = self.template_agreement_id.num_dias
            # self.late_fine = self.template_agreement_id.late_fine
            self.content = self.template_agreement_id.content
            # self.extra_ids = self.template_agreement_id.extra_ids
            self.signed_document_ids = self.template_agreement_id.signed_document_ids
            self.test_day_domain = self.template_agreement_id.test_day_domain
            self.payment_period_domain = self.template_agreement_id.payment_period_domain
            # self.extra_ids = self.template_agreement_id.extra_ids
            self.payment_deadline_domain = self.template_agreement_id.payment_deadline_domain
            self.pricelist_id = self.template_agreement_id.pricelist_id
            self.product_domain = self.template_agreement_id.product_domain
            self.zona_domain = self.template_agreement_id.zona_domain
            self.team_id_domain = self.template_agreement_id.team_id_domain
            self.payment_method_domain = self.template_agreement_id.payment_method_domain
            self.product_instalation = self.template_agreement_id.product_instalation
            self.product_desistalation = self.template_agreement_id.product_desistalation
            self.template_domain = templates_ids_domain
            if self.template_agreement_id.id not in self.template_domain.ids:
                self.template_agreement_id = ''
        if not self.template_agreement_id:
            payment_method = []
            payment_period = []
            team_id_domain = []
            type_partner_domain = []
            agreement_type = []
            payment_deadline_domain = []
            pricelist = []
            for a in templates_ids:
                for paym in a.payment_method_domain:
                    if paym.id not in payment_method:
                        payment_method.append(paym.id)
                for payp in a.payment_period_domain:
                    if payp.id not in payment_period:
                        payment_period.append(payp.id)
                for tids in a.team_id_domain:
                    if tids.id not in team_id_domain:
                        team_id_domain.append(tids.id)
                for deadline in a.payment_deadline_domain:
                    if deadline.id not in payment_deadline_domain:
                        payment_deadline_domain.append(deadline.id)
                for type_p in a.type_partner_domain:
                    if type_p.id not in type_partner_domain:
                        type_partner_domain.append(type_p.id)
                if a.agreement_type_id not in agreement_type:
                    agreement_type.append(a.agreement_type_id.id)
                if a.pricelist_id not in pricelist:
                    pricelist.append(a.pricelist_id.id)
            self.template_domain = templates_ids_domain
            self.payment_method_domain = payment_method
            self.team_id_domain = team_id_domain
            self.payment_deadline_domain = payment_deadline_domain
            self.type_partner_domain = type_partner_domain
            self.payment_period_domain = payment_period
        if self.line_ids:
            for line in self.line_ids:
                line._onchange_product_id()

        return res



    # @api.onchange('template_agreement_id') #, 'type_partner', 'payment_period', 'team_id', 'payment_method','agreement_type_id'
    # def onchange_template_agreement(self):
    #     res = {}
    #     if self.template_agreement_id:
    #         type_contrib_do = []
    #         template_domain = []
    #         payment_period_do = []
    #         payment_method_do = []
    #         payment_deadline_do = []
    #         arrs = []
    #         today = datetime.now()
    #         domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
    #         if self.parent_agreement_id:
    #             domain.append(('template_child', '=', True))
    #         if self.team_id:
    #             domain.append(('team_id_domain', 'in', self.team_id.id))
    #         # if self.partner_domain:
    #         #     domain.append(('partner_domain', 'in', self.partner_id.id))
    #         if self.type_contrib_partner:
    #             domain.append(('type_contrib', '=', self.type_contrib_partner.id))
    #         if self.type_partner:
    #             domain.append(('type_partner_domain', 'in', self.type_partner.id))
    #         # if not self.type_partner:
    #         #     self.type_partner_domain = [1, 2, 3, 4]
    #         #     self.template_agreement_id = ''
    #         if self.payment_method:
    #             domain.append(('payment_method_domain', 'in', self.payment_method.id))
    #             self.payment_method_domain = self.template_agreement_id.payment_method_domain
    #         # if not self.payment_method:
    #         #     self.payment_method_domain = [1, 2, 3, 4]
    #         if self.payment_period:
    #             domain.append(('payment_period_domain', 'in', self.payment_period.id))
    #         if self.payment_term_id:
    #             domain.append(('payment_deadline_domain', 'in', self.payment_term_id.id))
    #         if self.pricelist_id:
    #             domain.append(('pricelist_id_domain', 'in', self.pricelist_id.id))
    #         if self.agreement_type_id:
    #             domain.append(('agreement_type_id', '=', self.agreement_type_id.id))
    #         templates_ids = self.search(domain)
    #         # if self.template_agreement_id not in templates_ids:
    #         #     self.template_agreement_id = ''
    #         if templates_ids:
    #             for x in templates_ids:
    #                 arrs.append(x.id)
    #         if self.template_agreement_id.parent_template_id:
    #             for type in self.parent_agreement_id.type_contrib_domain:
    #                 if type.code == 'igp':
    #                     type_contrib_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.type_contrib_domain.ids)]
    #             for period in self.template_agreement_id.payment_period_domain:
    #                 if period.code == 'igp':
    #                     payment_period_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.payment_period_domain.ids)]
    #             for method in self.template_agreement_id.payment_method_domain:
    #                 if method.code == 'igp':
    #                     payment_method_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.payment_method_domain.ids)]
    #             for deadline in self.template_agreement_id.payment_deadline_domain:
    #                 if deadline.name == 'Igual al Dominio Padre':
    #                     payment_period_do = [
    #                         ('id', 'in', self.template_agreement_id.parent_template_id.payment_deadline_domain.ids)]
    #         # if not type_contrib_do:
    #         #     type_contrib_do = [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)]
    #         if not payment_period_do:
    #             payment_period_do = [('id', 'in', self.template_agreement_id.payment_period_domain.ids)]
    #         if not payment_method_do:
    #             payment_method_do = [('id', 'in', self.template_agreement_id.payment_method_domain.ids)]
    #         if not payment_deadline_do:
    #             payment_deadline_do = [('id', 'in', self.template_agreement_id.payment_deadline_domain.ids)]
    #         if self.template_agreement_id.payment_method_domain:
    #             payment_method_do = [('id', 'in', self.template_agreement_id.payment_method_domain.ids)]
    #         res['domain'] = {
    #             # 'payment_period': payment_period_do,
    #             # 'payment_method': payment_method_do,
    #             # 'test_day': [('id', 'in', self.template_agreement_id.test_day_domain.ids)],
    #             # 'type_contrib': type_contrib_do,
    #             # 'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
    #             # 'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
    #             # 'tax_id': [('id', 'in', self.template_agreement_id.tax_id_domain.ids)],
    #             # 'l10ncl_domain': [('id', 'in', self.template_agreement_id.l10ncl_domain.ids)],
    #             # 'payment_term_id': payment_deadline_do,
    #             #'payment_method': [('id', 'in', self.template_agreement_id.payment_method_domain.ids)],
    #             'card_number': [
    #                 ('type_subscription_contract', 'in', self.template_agreement_id.payment_method_domain.ids),
    #                 ('partner_id', 'in', self.partner_id.ids)],
    #             'template_agreement_id': [('id', 'in', arrs)]}
    #         self.agreement_type_id = self.template_agreement_id.agreement_type_id.id
    #         self.document_ids = self.template_agreement_id.document_ids
    #         #self.document_ids.recital_ids.recital_contrato_id = self.template_agreement_id.document_ids.recital_ids.recital_contrato_id
    #         self.recital_ids = self.template_agreement_id.recital_ids
    #         self.agreement_subtype_id = self.template_agreement_id.agreement_subtype_id
    #         self.anexo = self.template_agreement_id.anexo
    #         self.description = self.template_agreement_id.description
    #         self.end_date = self.template_agreement_id.end_date
    #         self.special_terms = self.template_agreement_id.special_terms
    #         self.title = self.template_agreement_id.title
    #         self.num_dias = self.template_agreement_id.num_dias
    #         self.late_fine = self.template_agreement_id.late_fine
    #         self.content = self.template_agreement_id.content
    #         self.extra_ids = self.template_agreement_id.extra_ids
    #         self.signed_document_ids = self.template_agreement_id.signed_document_ids
    #         self.test_day_domain = self.template_agreement_id.test_day_domain
    #         self.payment_period_domain = self.template_agreement_id.payment_period_domain
    #         self.extra_ids = self.template_agreement_id.extra_ids
    #         self.payment_deadline_domain = self.template_agreement_id.payment_deadline_domain
    #         self.pricelist_id_domain = self.template_agreement_id.pricelist_id_domain
    #         self.pricelist_id = self.template_agreement_id.pricelist_id
    #         self.product_domain = self.template_agreement_id.product_domain
    #         self.zona_domain = self.template_agreement_id.zona_domain
    #         self.team_id_domain = self.template_agreement_id.team_id_domain
    #         self.template_domain = templates_ids.ids
    #         # if self.payment_period:
    #         #     if self.payment_period.id not in self.template_agreement_id.payment_period_domain.ids:
    #         #         self.payment_period = ''
    #         # if self.payment_method:
    #         #     if self.payment_method.id not in self.template_agreement_id.payment_method_domain.ids:
    #         #         self.payment_method = ''
    #         if self.payment_term_id:
    #             if self.payment_term_id.id not in self.template_agreement_id.payment_deadline_domain.ids:
    #                 self.payment_term_id = ''
    #         if self.pricelist_id:
    #             if self.pricelist_id.id != self.template_agreement_id.pricelist_id.id:
    #                 self.pricelist_id = ''
    #         return res
    #     if not self.template_agreement_id:
    #         type_contrib_do = []
    #         template_domain = []
    #         payment_period_do = []
    #         payment_method_do = []
    #         payment_deadline_do = []
    #         arrs = []
    #         today = datetime.now()
    #         domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
    #         if self.parent_agreement_id:
    #             domain.append(('template_child', '=', True))
    #         if self.team_id:
    #             domain.append(('team_id_domain', 'in', self.team_id.id))
    #         if self.type_contrib_partner:
    #             domain.append(('type_contrib', '=', self.type_contrib_partner.id))
    #         if self.type_partner:
    #             domain.append(('type_partner_domain', 'in', self.type_partner.id))
    #         # if not self.type_partner:
    #         #     self.type_partner_domain = [1, 2, 3, 4]
    #         #     self.template_agreement_id = ''
    #         if self.payment_method:
    #             domain.append(('payment_method_domain', 'in', self.payment_method.id))
    #             self.payment_method_domain = self.template_agreement_id.payment_method_domain
    #         # if not self.payment_method:
    #         #     self.payment_method_domain = [1, 2, 3, 4]
    #         if self.payment_period:
    #             domain.append(('payment_period_domain', 'in', self.payment_period.id))
    #         if self.payment_term_id:
    #             domain.append(('payment_deadline_domain', 'in', self.payment_term_id.id))
    #         if self.pricelist_id:
    #             domain.append(('pricelist_id_domain', 'in', self.pricelist_id.id))
    #         if self.agreement_type_id:
    #             domain.append(('agreement_type_id', '=', self.agreement_type_id.id))
    #         templates_ids = self.search(domain)
    #         if templates_ids:
    #             for x in templates_ids:
    #                 arrs.append(x.id)
    #         res['domain'] = {'template_agreement_id': [('id', 'in', arrs)]}
    #         self.template_domain = templates_ids.ids

    @api.onchange('template_child')
    def onchange_template_child(self):
        res = {}
        if not self.template_child:
            type_contrib = self.env['agreement.type.contrib'].search([('code', '!=', 'ig')])
            payment_period = self.env['agreement.payment.period'].search([('code', '!=', 'ig')])
            payment_method = self.env['agreement.payment.method'].search([('code', '!=', 'ig')])
            payment_deadline = self.env['account.payment.term'].search([('name', '!=', 'Igual al Padre')])
            res['domain'] = {
                'payment_period_domain': [('id', 'in', payment_period.ids)],
                'payment_method_domain': [('id', 'in', payment_method.ids)],
                'payment_deadline_domain': [('id', 'in', payment_deadline.ids)],
                # 'type_contrib': [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)],
                # 'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
                # 'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
                'type_contrib_domain': [('id', 'in', type_contrib.ids)]}
        else:
            res['domain'] = {
                'payment_period_domain': [],
                'payment_method_domain': [],
                'payment_deadline_domain': [],
                # 'type_contrib': [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)],
                # 'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
                # 'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
                'type_contrib_domain': []}
        return res

    @api.onchange('agreement_discount')
    def onchange_agreement_discount(self):
        today = date.today()
        discount_ids = self.env['agreement.discount'].search(
            [('fecha_inicio', '<=', today), ('fecha_fin', '>=', today)])
        domain = {'agreement_discount': [('id', 'in', discount_ids.ids)]}
        return {'domain': domain}

    @api.onchange('type_contrib')
    def onchange_type_contrib(self):
        domain = {}
        if self.type_contrib:
            if self.type_partner_domain:
                for typec in self.type_partner_domain:
                    if self.type_contrib != typec.type_contrib:
                        self.type_partner_domain = [(6, 0, [])]

    @api.onchange("field_domain", "default_value")
    def onchange_copyvalue(self):
        self.copyvalue = False
        if self.field_domain:
            string_list = self.field_domain.split(",")
            if string_list:
                field_domain = string_list[0][3:-1]
                self.copyvalue = "${{object.{} or {}}}".format(
                    field_domain,
                    self.default_value or "''")

    @api.onchange('test_day', 'start_date')
    def _onchange_num_dias(self):
        self.fecha_cobro = self.start_date + relativedelta(days=int(self.test_day.code))

    @api.onchange('agreement_type_id')
    def agreement_type_change(self):
        if self.agreement_type_id and self.agreement_type_id.domain:
            self.domain = self.agreement_type_id.domain

    @api.onchange('revisado_check')
    def onchange_revisado_check(self):
        if self.revisado_check:
            self.reviewed_user_id = self._uid
            self.reviewed_date = datetime.now().date()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """Always assign a value for code because is required"""
        default = dict(default or {})
        if default.get('code', False):
            return super().copy(default)
        default.setdefault('code', _("%s (copy)") % (self.code))
        return super().copy(default)

    def ajust_agreement(self):
        if not self.date_ajuste:
            raise UserError(_(
                'Disculpe, No se puede ajustar el contrato, \n \n  Debido a que no existe la fecha de ajuste'))
        if self.date_ajuste.day != 1:
            raise UserError(_('Disculpe, No se puede ajustar el contrato, \n \n  Debido a que la fecha de ajuste no es el primero de mes'))
        # borrar lineas
        rentals_ajust = self.env['sale.order'].search(
            [('fecha_estimada', '>=', self.date_ajuste), ('state', '=', 'draft')])
        rentals_ajust.unlink()
        # Rentals
        months = (
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
            "Noviembre",
            "Diciembre")
        meses = 0
        meses2 = 0
        time_periodicy = 0
        descuento = False
        if self.payment_period.code == 'M':
            time_periodicy = 1
        if self.payment_period.code == 'T':
            time_periodicy = 3
        if self.payment_period.code == 'S':
            time_periodicy = 6
        if self.payment_period.code == 'AM' or self.payment_period.code == 'A' or self.payment_period.code == 'AD':
            time_periodicy = 12
        if self.payment_period.code == 'AM' or self.payment_period.code == 'A':
            descuento = 2
        # rental orders
        for line in self.line_ids:
            primero = True
            today = self.date_ajuste
            today_defasado = today
            fin_ciclo = today + relativedelta(months=time_periodicy)
            end_period = str(fin_ciclo.year) + '-' + str(self.date_ajuste.month).zfill(2) + '-' + str(
                self.date_ajuste.day).zfill(2)
            end_period = datetime.strptime(end_period, '%Y-%m-%d')
            if self.payment_period.code == 'S' or self.payment_period.code == 'T' or self.payment_period.code == 'M':
                end_period = fin_ciclo
            numeracion = 1
            proporcional = True
            primero_seq = False
            prorrateo = True
            end_12 = ''
            end_for = ''
            es_primero = 1
            period_day = self.date_ajuste.day
            period_mes_ = self.date_ajuste.month
            period_anio = self.date_ajuste.year
            period_date = str(self.date_ajuste.year) + '-' + str(self.date_ajuste.month).zfill(2) + '-' + '01'
            period_date = datetime.strptime(period_date, '%Y-%m-%d')
            while (meses < 36):
                if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date():
                    meses = meses
                else:
                    meses = meses + time_periodicy
                if self.payment_period.code == 'AM' and meses2 == 12:
                    time_periodicy = 1
                if self.payment_period.code == 'A' and meses2 == 12:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 24:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 36:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 48:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 60:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 72:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 84:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 96:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 108:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 120:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 132:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 144:
                    descuento = 2
                if self.payment_period.code == 'A' and meses2 == 156:
                    descuento = 2
                prorrateo = False
                lista = range(time_periodicy)
                listadef = list(lista)
                meses2 = meses2 + time_periodicy
                if today_defasado > datetime.strptime(str(period_date)[0:10],
                                                      '%Y-%m-%d').date() or datetime.strptime(
                        str(end_period)[0:10], '%Y-%m-%d').date() >= datetime.strptime(str(period_date)[0:10],
                                                                                       '%Y-%m-%d').date():
                    today = today_defasado
                else:
                    if end_12 == '':
                        end_12 = today
                        today = period_date
                for i in listadef:

                    dia_ = today.day
                    mes_ = today.month
                    anio_ = today.year
                    date_def = today
                    if descuento:
                        des = range(descuento)
                        listades = list(des)
                        for des in listades:
                            period_date_des = period_date
                            if prorrateo:
                                period_date_des = period_date + relativedelta(months=1)
                            ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                            fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(
                                2) + '-' + str(
                                ultimo_de_mes[1])
                            order_vals = {
                                'partner_id': self.partner_id.id,
                                'opportunity_id': self.crm_lead_id.id,
                                'agreement_type_id': self.agreement_type_id.id,
                                'agreement_id': self.id,
                                'date_order': datetime.now(),
                                'validity_date': self.end_date,
                                'user_id': self.crm_lead_id.user_id.id,
                                'origin': self.crm_lead_id.name,
                                'partner_dir_id': line.partner_contact_id.id,
                                'is_rental_order': True,
                                'tipo_rental_order': 'descuento',
                                'agreement_id': self.id,
                                'agreement_line_ids': line.id,
                                'payment_period': self.payment_period.id,
                                'payment_method': self.payment_method.id,
                                'payment_term_id': self.payment_term_id.id,
                                'inicio_fecha_alquiler': period_date_des,
                                'fin_fecha_alquiler': fin_mes,
                                'fecha_fact_prog': date_def,
                                'fecha_estimada': date_def,
                                'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(
                                    period_date_des.year),
                                'state': 'sale',  # 'draft',
                                'currency_id': self.currency_id.id,
                                'pricelist_id': line.pricelist_mens.id,
                                'reference_ids': [self.reference_ids.id],
                            }
                            order = self.env['sale.order'].create(order_vals)
                            name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                            order.write({'name': name_order})
                            precio_men = round(line.price, 3) + 0.001
                            order_line = {
                                'order_id': order.id,
                                'product_id': line.product_id.id,
                                'name': str(line.product_id.name_key) + '/' + str(
                                    line.maintenance_id.name) + '/' + str(
                                    line.pricelist_mens.currency_id.name) + '' + str(- precio_men) + '+iva',
                                'price_unit': - line.price,
                                'tax_id': [self.tax_id.id],
                            }
                            order_line = self.env['sale.order.line'].create(order_line)
                            descuento = False
                    line_price = line.price
                    ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
                    fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(
                        ultimo_de_mes[1])
                    month = months[period_date.month - 1]
                    if primero_seq:
                        date_def = today
                        monthRange = calendar.monthrange(period_date.year, period_date.month)
                        montha = monthRange[1]  # es primera vez
                        dia = montha - period_date.day
                        por_dia = line.price / montha
                        line_price = por_dia * dia
                    else:
                        period_date = str(period_date.year) + '-' + str(
                            period_date.month).zfill(2) + '-' + '01'
                        period_date = datetime.strptime(period_date, '%Y-%m-%d')
                    primero_seq = False

                    order_vals = {
                        'partner_id': self.partner_id.id,
                        'opportunity_id': self.crm_lead_id.id,
                        'agreement_type_id': self.agreement_type_id.id,
                        'agreement_id': self.id,
                        'date_order': datetime.now(),
                        'validity_date': self.end_date,
                        'user_id': self.crm_lead_id.user_id.id,
                        'origin': self.crm_lead_id.name,
                        'partner_dir_id': line.partner_contact_id.id,
                        'is_rental_order': True,
                        'tipo_rental_order': 'mensualidad',
                        'agreement_id': self.id,
                        'agreement_line_ids': line.id,
                        'payment_period': self.payment_period.id,
                        'payment_method': self.payment_method.id,
                        'payment_term_id': self.payment_term_id.id,
                        'inicio_fecha_alquiler': period_date,
                        'fin_fecha_alquiler': fin_mes,
                        'fecha_fact_prog': date_def,
                        'fecha_estimada': date_def,
                        'periodo_mes': str(month) + '/' + str(period_date.year),
                        'state': 'sale',  # 'draft',
                        'currency_id': self.currency_id.id,
                        'pricelist_id': line.pricelist_mens.id,
                        'reference_ids': [self.reference_ids.id],
                    }
                    order = self.env['sale.order'].create(order_vals)
                    name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                    order.write({'name': name_order})
                    precio_men = round(line_price, 3) + 0.001
                    order_line = {
                        'order_id': order.id,
                        'product_id': line.product_id.id,
                        'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
                            line.pricelist_mens.currency_id.name) + '' + str(precio_men) + '+iva',
                        'price_unit': line_price,
                        'tax_id': [self.tax_id.id],
                    }
                    order_line = self.env['sale.order.line'].create(order_line)
                    numeracion = numeracion + 1
                    primero = False
                    proporcional = False
                    period_date = period_date + relativedelta(months=1)
                today = today + relativedelta(months=time_periodicy)
        self.write({'state_ajust': 'R'})

    def agree_maintenance(self):
        months = (
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
        "Diciembre")
        meses = 0
        time_periodicy = 0
        descuento = False
        if self.payment_period.code == 'M':
            time_periodicy = 1
        if self.payment_period.code == 'T':
            time_periodicy = 3
        if self.payment_period.code == 'S':
            time_periodicy = 6
        if self.payment_period.code == 'AM' or self.payment_period.code == 'A' or self.payment_period.code == 'AD':
            time_periodicy = 12
        if self.payment_period.code == 'AM' or self.payment_period.code == 'A':
            descuento = 2
        valid = self.fecha_cobro + relativedelta(days=1)
        #rental orders
        for line in self:
            primero = True
            today = datetime.now().date() + relativedelta(days=1) # self.fecha_cobro
            numeracion = 1
            proporcional = True
            es_primero = 1
            period_day = self.fecha_cobro.day
            period_mes_ = self.fecha_cobro.month
            period_anio = self.fecha_cobro.year
            period_date = str(self.fecha_cobro.year) + '-' + str(self.fecha_cobro.month).zfill(2) + '-' + '01'
            period_date = datetime.strptime(period_date, '%Y-%m-%d')
            if self.fecha_cobro.day == 1 or self.fecha_cobro.day == 2 or self.fecha_cobro.day == 3:
                primero = False
            if primero == True:
                first = self.fecha_cobro
                monthRange = calendar.monthrange(first.year, first.month)
                month = monthRange[1]  # es primera vez
                dia = month - first.day + 1
                por_dia = line.price / month
                total = por_dia * dia
                ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
                fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(ultimo_de_mes[1])
                month = months[period_date.month - 1]
                order_vals = {
                    'partner_id': self.partner_id.id,
                    'opportunity_id': self.crm_lead_id.id,
                    'agreement_type_id': self.agreement_type_id.id,
                    'agreement_id': self.id,
                    'date_order': datetime.now(),
                    'validity_date': self.end_date,
                    'user_id': self.crm_lead_id.user_id.id,
                    'origin': self.crm_lead_id.name,
                    'partner_dir_id': line.partner_contact_id.id,
                    'is_rental_order': True,
                    'tipo_rental_order': 'mensualidad',
                    'agreement_id': self.id,
                    'agreement_line_ids': line.id,
                    'payment_period': self.payment_period.id,
                    'payment_method': self.payment_method.id,
                    'payment_deadline': self.payment_deadline.id,
                    'inicio_fecha_alquiler': self.fecha_cobro,
                    'fin_fecha_alquiler': fin_mes,
                    'fecha_fact_prog': today,
                    'next_action_date': today,
                    'periodo_mes': str(month) + '/' + str(period_date.year)
                }
                order = self.env['sale.order'].create(order_vals)
                name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                order.write({'name': name_order})
                order_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'price_unit': total
                }
                order_line = self.env['sale.order.line'].create(order_line)
                period_date = period_date + relativedelta(months=1)
                primero = False
            if descuento:
                des = range(descuento)
                listades = list(des)
                for des in listades:
                    order_vals = {
                        'partner_id': self.partner_id.id,
                        'opportunity_id': self.crm_lead_id.id,
                        'agreement_type_id': self.agreement_type_id.id,
                        'agreement_id': self.id,
                        'date_order': datetime.now(),
                        'validity_date': self.end_date,
                        'user_id': self.crm_lead_id.user_id.id,
                        'origin': self.crm_lead_id.name,
                        'partner_dir_id': line.partner_contact_id.id,
                        'is_rental_order': True,
                        'tipo_rental_order': 'descuento',
                        'agreement_id': self.id,
                        'agreement_line_ids': line.id,
                        'payment_period': self.payment_period.id,
                        'payment_method': self.payment_method.id,
                        'payment_deadline': self.payment_deadline.id,
                        #'fecha_fact_prog': today,
                    }
                    order = self.env['sale.order'].create(order_vals)
                    name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                    order.write({'name': name_order})
                    order_line = {
                        'order_id': order.id,
                        'product_id': line.product_id.id,
                        'price_unit': - line.price
                    }
                    order_line = self.env['sale.order.line'].create(order_line)
                    descuento = False
            while (meses < 37):
                if self.payment_period.code == 'AM' and meses == 12:
                    time_periodicy = 1
                meses = meses + time_periodicy
                dia_ = today.day
                mes_ = today.month
                anio_ = today.year
                if proporcional:
                    date_def = today
                else:
                    date_def = str(today.year) + '-' + str(today.month).zfill(2) + '-' + '01'
                    fecha_dt = datetime.strptime(date_def, '%Y-%m-%d')
                lista = range(time_periodicy)
                listadef = list(lista)
                for i in listadef:
                    ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
                    fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(
                        ultimo_de_mes[1])
                    month = months[period_date.month - 1]
                    order_vals = {
                        'partner_id': self.partner_id.id,
                        'opportunity_id': self.crm_lead_id.id,
                        'agreement_type_id': self.agreement_type_id.id,
                        'agreement_id': self.id,
                        'date_order': datetime.now(),
                        'validity_date': self.end_date,
                        'user_id': self.crm_lead_id.user_id.id,
                        'origin': self.crm_lead_id.name,
                        'partner_dir_id': line.partner_contact_id.id,
                        'is_rental_order': True,
                        'tipo_rental_order': 'mensualidad',
                        'agreement_id': self.id,
                        'agreement_line_ids': line.id,
                        'payment_period': self.payment_period.id,
                        'payment_method': self.payment_method.id,
                        'payment_deadline': self.payment_deadline.id,
                        'inicio_fecha_alquiler': period_date,
                        'fin_fecha_alquiler': fin_mes,
                        'fecha_fact_prog': date_def,
                        'next_action_date': date_def,
                        'periodo_mes': str(month) + '/' + str(period_date.year)
                    }
                    order = self.env['sale.order'].create(order_vals)
                    name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                    order.write({'name': name_order})
                    if today.day == 1 or today.day == 2 or today.day == 3:
                        primero = False
                    if primero == True:
                        first = self.fecha_cobro
                        monthRange = calendar.monthrange(first.year, first.month)
                        month = monthRange[1]  # es primera vez
                        dia = month - first.day
                        por_dia = line.price / month
                        line.price = por_dia * dia
                    order_line = {
                        'order_id': order.id,
                        'product_id': line.product_id.id,
                        'price_unit': line.price
                    }
                    order_line = self.env['sale.order.line'].create(order_line)
                    period_date = period_date + relativedelta(months=1)
                    numeracion = numeracion + 1
                    primero = False
                    proporcional = False
                today = today + relativedelta(months=time_periodicy)
        return True

    def orden_compra(self):
        if self.reference_ids:
            for ref in self.reference_ids:
                if ref.active_s == True:
                    orders = self.env['sale.order'].search(
                        [('agreement_id', '=', self.id), ('state', '=', 'draft'),
                         ('inicio_fecha_alquiler', '<=', ref.date_init)])
                    for orden in orders:
                        vals = {
                            'sale_id': orden.id,
                            'reference_oc': ref.id,
                        }
                        created = self.env['sale_reference_rel'].create(vals)
                        print(created)
                        #orden.write({'reference_oc': ref.id})

    def agree_cancelled(self):
        orders = self.env['sale.order'].search([('agreement_id', '=', self.id)])
        for rental_order in orders:
            rental_order.write({'state': 'cancel'})

class AgreementPaymentMethod(models.Model):
    _name = 'agreement.payment.method'

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Codigo')

class AgreementPaymentIntermediary(models.Model):
    _name = 'agreement.payment.intermediary'

    code = fields.Char(string='Codigo')
    name = fields.Char(required=True, string='Nombre')
    payment_method = fields.Many2one('agreement.payment.method', string="Metodo de Pago", domain=[('code', '!=', 'ig')])
    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer')

class AgreementPaymentPeriod(models.Model):
    _name = 'agreement.payment.period'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string='Nombre', track_visibility="onchange")
    code = fields.Char(required=True, string='Codigo', track_visibility="onchange")
    descuento = fields.Integer(required=False, string='Descuento', track_visibility="onchange")
    periodicidad = fields.Integer(required=True, string='Periodicidad', track_visibility="onchange")
    siguiente_periodicidad = fields.Many2one("agreement.payment.period", required=True, string="Siguiente Periodicidad",
                                             track_visibility="onchange")

class AgreementTypePartner(models.Model):
    _name = 'agreement.type.partner'

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Codigo')
    type_contrib = fields.Many2one('agreement.type.contrib', string="Tipo de contribuyente") #, domain=[("code", "not in", ['ig', 'na', 'igp'])]

class AgreementTestDay(models.Model):
    _name = "agreement.test.day"
    _description = "Agreement Tests Day"

    name = fields.Char(required=True, string='Nombre')
    code = fields.Integer(required=True, string='Días')

class AgreementTypeContrib(models.Model):
    _name = "agreement.type.contrib"
    _description = "Agreement Type of taxpayer"

    name = fields.Char(required=True, string='Type')
    code = fields.Char(required=True, string='Code')

class AgreementSignedExtra(models.Model):
    _name = "agreement.signed.extra"
    _description = "Agreement Extra Document"
    _order = "sequence"

    sequence = fields.Integer(string="Secuencia", default=10)
    name = fields.Char(string="Nombre Archivo")
    type_extra = fields.Many2one(
        "type.signed.extra",
        string="Type",
        track_visibility="onchange")
    valid = fields.Boolean('Validado', default=False)
    document = fields.Binary(
        string="Documento", track_visibility="always")
    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Agreement', ondelete='cascade',
        track_visibility='onchange', readonly=False, invisible=True)
    approved_date = fields.Date(
        string="Approved Date", track_visibility="onchange")
    approved_user_id = fields.Many2one(
        "res.users", string="Approved By", track_visibility="onchange")

class TypeSignedExtra(models.Model):
    _name = "type.signed.extra"
    _description = "Type Extra Documento"

    name = fields.Char(string="Type")

class AgreementExtraCharges(models.Model):
    _name = 'agreement.extra.charges'
    _rec_name = 'product_id'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one('product.template', string='Producto', track_visibility="onchange")
    description = fields.Char('Descripcion', track_visibility="onchange")
    currency_id = fields.Many2one('res.currency', 'Moneda', track_visibility="onchange")
    pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precios', readonly=False, invisible=True, track_visibility="onchange")
    zona_comercial = fields.Many2one('zona.comercial', string='Zona', track_visibility="onchange")
    price = fields.Float('Precio', readonly=False, track_visibility='onchange', digits='Product Price')
    vali_price = fields.Boolean('Excepción Precio Cero', default=False, track_visibility="onchange")
    #qty = fields.Float('Cantidad')
    #product_uom = fields.Many2one('uom.uom', 'Unidad de Medida')
    #time_spent = fields.Float('Tiempo/Horas', precision_digits=2)
    #charge = fields.Boolean('Cobrar', default=False)
    agreement_id = fields.Many2one(
        "agreement",
        string="Parent Agreement",)
    is_template = fields.Boolean(string='is_template', related='agreement_id.is_template', track_visibility='onchange')

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.description = self.product_id.name
        #self.uom_id = self.product_id.uom_id.id

class TypeDocumentExtra(models.Model):
    _name = "type.document.extra"
    _description = "Type Extra"

    name = fields.Char(string="Type")

class CrmCanal(models.Model):
    _name = 'crm.canal'

    name = fields.Char(required=True, string='Nombre')

class CrmSubCanal(models.Model):
    _name = 'crm.subcanal'

    name = fields.Char(required=True, string='Nombre')
    canal_id = fields.Many2one(
        'crm.canal',
        string='Canal')

class LogAdmin(models.Model):
    _name = 'log.admin'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id asc'

    name = fields.Many2one(
        "res.users", string="Administrador de Contrato Maihue", track_visibility="onchange")
    user_id = fields.Many2one(
        "res.users", string="Responsable", track_visibility="onchange")
    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Contrato', ondelete='cascade',
        track_visibility='onchange', readonly=False, invisible=True)
    state = fields.Selection(
        [("asig", "Asignado"), ("des", "Desactivado")],
        default="asig", string='Estado',
        track_visibility="always")
    date = fields.Datetime(
        string="Fecha",
        track_visibility="onchange")
    vigente = fields.Boolean(
        string="Vigente",
        default=False,
        copy=False, track_visibility="onchange"
    )

class LogContract(models.Model):
    _name = 'log.contract'
    _order = 'id asc'

    name = fields.Many2one(
        "res.users", string="Administrador de Contrato Maihue", track_visibility="onchange")
    user_id = fields.Many2one(
        "res.users", string="Responsable", track_visibility="onchange")
    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Contrato', ondelete='cascade',
        track_visibility='onchange', readonly=False, invisible=True)
    state = fields.Selection(
        [("asig", "Asignado"), ("des", "Desactivado")],
        default="asig", string='Estado',
        track_visibility="always")
    date = fields.Datetime(
        string="Fecha",
        track_visibility="onchange")
    vigente = fields.Boolean(
        string="Vigente",
        default=False,
        copy=False, track_visibility="onchange"
    )
