# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError
from collections import OrderedDict

from odoo.fields import Date

class Lead(models.Model):
    _inherit = 'crm.lead'

    # def _compute_template(self):
    #     today = datetime.now()
    #     type_partner = ''
    #     domain = [('is_template', '=', True), ('expiration_date', '>=', today), ('template_child', '=', False)]
    #     domain_exc = [('is_template', '=', True), ('expiration_date', '>=', today)]
    #     if self.partner_id.type_contrib:
    #         domain.append(('type_contrib', '=', self.partner_id.type_contrib.id))
    #         if self.partner_id.company_type == 'company':
    #             type_partner = 1
    #         else:
    #             type_partner = 2
    #         domain.append(('type_partner_domain', 'in', [type_partner]))
    #         domain_exc.append(('type_contrib', '=', self.partner_id.type_contrib.id))
    #     if self.payment_method:
    #         domain.append(('payment_method_domain', 'in', self.payment_method.id))
    #         domain_exc.append(('payment_method_domain', 'in', self.payment_method.id))
    #     if self.team_id:
    #         domain.append(('team_id_domain', 'in', self.team_id.id))
    #         domain_exc.append(('exception_team_id_domain', 'in', self.team_id.id))
    #     templates_ids = self.env['agreement'].sudo().search(domain)
    #     exc_templates_ids = self.env['agreement'].sudo().search(domain_exc)
    #     template_domain = []
    #     if templates_ids:
    #         for temp in templates_ids:
    #             template_domain.append(temp.id)
    #     if exc_templates_ids:
    #         for exc in exc_templates_ids:
    #             if exc.id not in template_domain:
    #                 template_domain.append(exc.id)
    #     self.template_domain = template_domain
    #     self.template_agreement_id = self.team_id.template_agreement_id.id
    #     if not self.team_id.template_agreement_id:
    #         self.template_agreement_id = ''
    #     self.payment_method_domain = self.team_id.template_agreement_id.payment_method_domain.ids
        # self.type_partner_domain = self.team_id.template_agreement_id.type_partner_domain.ids

    # @api.model
    # def default_get(self, fields):
    #     result = super(Lead, self).default_get(fields)
    #     #team_id = result.get('team_id')
    #     if self.partner_id:
    #         if self.partner_id.company_type == 'company':
    #             if self.team_id.template_agreement_company:
    #                 result['template_agreement_id'] = self.team_id.template_agreement_company.id
    #         else:
    #             if self.team_id.template_agreement_person:
    #                 result['template_agreement_id'] = self.team_id.template_agreement_person.id
        # if self.team_id:
        #     templates_ids = self.env['agreement'].sudo().search([
        #         ('is_template', '=', True),
        #         ('team_id_domain', 'in', self.team_id.id)])
        #     exc_templates_ids = self.env['agreement'].sudo().search([
        #         ('is_template', '=', True),
        #         ('exception_team_id_domain', 'in', self.team_id.id)])
        #     template_domain = []
        #     if templates_ids:
        #         for temp in templates_ids:
        #             template_domain.append(temp.id)
        #     if exc_templates_ids:
        #         for exc in exc_templates_ids:
        #             if exc.id not in template_domain:
        #                 template_domain.append(exc.id)
        #     result['template_domain'] = template_domain
        #     result['template_agreement_id'] = self.team_id.template_agreement_id.id
        #     result['payment_method_domain'] = self.team_id.template_agreement_id.payment_method_domain.ids
        #     result['type_partner_domain'] = self.team_id.template_agreement_id.type_partner_domain.ids
        # return result

    def name_get(self):
        result = []
        for lead in self:
            name = str(lead.id) + ' ' + str(lead.name)
            result.append((lead.id, name))
        return result


    def _compute_agreement_count(self):
        agreement_data = self.sudo().env['agreement'].read_group([('state', '!=', 'cancel'), ('crm_lead_id', 'in', self.ids)], ['crm_lead_id'], ['crm_lead_id'])
        mapped_data = dict([(q['crm_lead_id'][0], q['crm_lead_id_count']) for q in agreement_data])
        for agreement in self:
            agreement.agreement_count = mapped_data.get(agreement.id, 0)

    @api.depends('crm_line_ids.price')
    def _amount_line_all(self):
        """
        Compute the total amounts of the crm.
        """
        for lead in self:
            amount_total = 0.0
            for line in lead.crm_line_ids:
                amount_total += line.price
            lead.update({
                'planned_revenue': amount_total,
            })

    partner_id = fields.Many2one(domain="[('parent_id', '=', False)]", tracking=True)
    type_contrib_partner = fields.Many2one(related='partner_id.type_contrib', string='Type of taxpayer', required=False, tracking=True)
    agreement_count = fields.Integer(compute='_compute_agreement_count', tracking=True)
    agreement_id = fields.Many2one('agreement', "Father Contract",
                                   help="Select a parent contract to generate an annex of that selected contract",
                                  required=False, domain="[('partner_id', '=', partner_id), ('is_template', '=', False), ('father', '=', True)]", tracking=True)
    crm_line_ids = fields.One2many('crm.line', 'crm_id', string='Services', tracking=True)
    crm_line_serv_real = fields.One2many('crm.rline', 'crm_id', string='Royal Services', tracking=True)
    planned_revenue = fields.Float(compute='_amount_line_all', tracking=True)
    crm_captado_id = fields.Many2one(
        'res.users',
        string='captured by', tracking=True)
    crm_gestionado_id = fields.Many2one(
        'res.users',
        string='Managed by', tracking=True)
    canal_id = fields.Many2one(
        'crm.canal',
        string='Channel', tracking=True)
    subcanal_id = fields.Many2one(
        'crm.subcanal',
        string='sub channel', tracking=True)
    payment_method = fields.Many2one(
        "agreement.payment.method", required=False, domain="[('id', 'in', [1,2,3,4])]",
        string="Payment method", tracking=True)
    type_partner = fields.Many2one(
        "agreement.type.partner", required=False,
        string="Type of contract", help="Type of client (household, company, HORECA - INTERNAL, HORECA - SELF-BOTTLING)", tracking=True)
    template_agreement_id = fields.Many2one('agreement', string='Template', tracking=True)
    template_child_id = fields.Many2one(related='agreement_id.template_agreement_id', string='Plantilla Padre', tracking=True)
    template_child = fields.Boolean(related='template_agreement_id.template_child', string='Plantilla Padre')
    check_exception = fields.Boolean(string='Exception Template', default=False, tracking=True)
    exception = fields.Boolean(string='Check Exception Template', default=False, tracking=True)
    valid_exception = fields.Boolean(string='Valid Exception Template', default=False, tracking=True)
    template_domain = fields.Many2many('agreement', 'template_lead_rel', 'parent_id',
                                       'lead_id', #compute='_compute_template', #store=True,
                                       string='Domain for contract')
    payment_method_domain = fields.Many2many('agreement.payment.method', 'method_lead_rel', 'method_id',
                                             'lead_id', #store=True,
                                             string='Payment method')
    payment_period = fields.Many2one(
        "agreement.payment.period", required=False,  # domain="[('id', 'in', payment_period_domain)]",
        string="Periodicidad de Pago", tracking=True)
    payment_period_domain = fields.Many2many('agreement.payment.period', 'period_lead_rel', 'period_id',
                                             'lead_id',
                                             string='Dominio Periodicidad de pago')
    type_partner_domain = fields.Many2many('agreement.type.partner', 'lead_type_partner_rel', 'type_id',
                                           'lead_id', #store=True,
                                           string='Type of contract')
    payment_term_id = fields.Many2one('account.payment.term', string='Plazo de Pago', tracking=True
                                      # ,domain="[('id', 'in', payment_deadline_domain)]"
                                      )
    payment_deadline_domain = fields.Many2many('account.payment.term', 'deadline_lead_rel', 'deadline_id',
                                               'lead_id',
                                               string='Dominio Plazo de Pago')
    contract = fields.Boolean(string='Oportunidad de Contrato', default=False, tracking=True)
    contract_partner = fields.Boolean(related='partner_id.contract', tracking=True)
    black_list = fields.Boolean(related='partner_id.black_list', tracking=True)
    agreement = fields.Many2one("agreement", string="Contrato", tracking=True)
    agreement_stage = fields.Many2one(related="agreement.stage_id", string="Estado de Contrato", required=False, copy=True, tracking=True)
    api_form = fields.Char('Formulario')
    api_payment = fields.Char('Forma de pago Formulario')

    @api.depends('partner_id.email')
    def _compute_email_from(self):
        res = super(Lead, self)._compute_email_from()
        for lead in self:
            if not lead.partner_id:
                lead.email_from = ''

    @api.depends('partner_id.phone')
    def _compute_phone(self):
        res = super(Lead, self)._compute_phone()
        for lead in self:
            if not lead.partner_id:
                lead.phone = ''
            else:
                lead.phone = lead.partner_id.phone0


    # @api.onchange('team_id')
    # def onchange_team_id(self):
    #     res = {}
    #     template_domain = []
    #     if self.team_id:
    #         templates_ids = self.env['agreement'].sudo().search([
    #             ('is_template', '=', True),
    #             ('team_id_domain', 'in', self.team_id.id)])
    #         exc_templates_ids = self.env['agreement'].sudo().search([
    #             ('is_template', '=', True),
    #             ('exception_team_id_domain', 'in', self.team_id.id)])
    #         template_domain = []
    #         if templates_ids:
    #             for temp in templates_ids:
    #                 template_domain.append(temp.id)
    #         if exc_templates_ids:
    #             for exc in exc_templates_ids:
    #                 if exc.id not in template_domain:
    #                     template_domain.append(exc.id)
    #     self.template_domain = template_domain
    #     self.template_agreement_id = self.team_id.template_agreement_id.id

    # @api.onchange('agreement_id')
    # def onchange_pagreement_id(self):
    #     res = {}
    #     template_domain = []
    #     payment_method_domain = []
    #     type_partner_domain = []
    #     if self.agreement_id:
    #         templates_parent = self.env['agreement'].sudo().search([
    #             ('parent_template_id', '=', self.template_child_id.id)])
    #         for mt in templates_parent:
    #             for pmd in mt.payment_method_domain:
    #                 if pmd.id in [7, 8]:
    #                     if pmd.id == 7:
    #                         payment_method_domain.append(self.agreement_id.payment_method.id)
    #                     if pmd.id == 8:
    #                         for dominio in self.template_child_id.payment_method_domain:
    #                             payment_method_domain.append(dominio.id)
    #                 else:
    #                     payment_method_domain.append(pmd.id)
    #             for tpd in mt.type_partner_domain:
    #                 type_partner_domain.append(tpd.id)
    #         self.template_agreement_id = ''
    #         self.payment_method = ''
    #         self.type_partner = ''
    #         if not templates_parent:
    #             self.template_domain = False
    #         if templates_parent:
    #             self.template_domain = templates_parent.ids
    #         self.payment_method_domain = payment_method_domain
    #         self.type_partner_domain = type_partner_domain
    #     return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.company_type == 'company':
                if self.team_id.template_agreement_company:
                    self.template_agreement_id = self.team_id.template_agreement_company.id
            else:
                if self.team_id.template_agreement_person:
                    self.template_agreement_id = self.team_id.template_agreement_person.id

    @api.onchange('template_agreement_id', 'payment_method', 'type_partner', 'contract', 'agreement_id', 'partner_id',
                  'service_type', 'team_id', 'payment_period', 'payment_term_id')
    def onchange_template_agreement_id(self):
        today = datetime.now()
        res = {}
        template_domain = []
        payment_method_domain = []
        type_partner = 0
        partner_domain = False
        valid_domain = False
        type_partner_domain = []
        if self.contract:
            if self.template_agreement_id:
                if self.agreement_id:
                    templates_parent = self.env['agreement'].sudo().search([
                        ('parent_template_id', '=', self.template_child_id.id)])
                    for mt in templates_parent:
                        for pmd in mt.payment_method_domain:
                            if pmd.id in [7, 8]:
                                if pmd.id == 7:
                                    payment_method_domain.append(self.agreement_id.payment_method.id)
                                if pmd.id == 8:
                                    for dominio in self.template_child_id.payment_method_domain:
                                        payment_method_domain.append(dominio.id)
                            else:
                                payment_method_domain.append(pmd.id)
                        for tpd in mt.type_partner_domain:
                            type_partner_domain.append(tpd.id)
                    # self.template_agreement_id = ''
                    # self.payment_method = ''
                    # self.type_partner = ''
                    if not templates_parent:
                        self.template_domain = False
                    if templates_parent:
                        self.template_domain = templates_parent.ids
                    if self.template_agreement_id:
                        if self.template_agreement_id.id not in self.template_domain.ids:
                            self.template_agreement_id = ''
                            self.payment_method = ''
                            self.type_partner = ''
                    self.payment_method_domain = payment_method_domain
                    self.payment_period_domain = self.template_child_id.payment_period_domain
                    self.payment_deadline_domain = self.template_child_id.payment_deadline_domain
                    if self.partner_id.company_type == 'company':
                        type_partner = 1
                    else:
                        type_partner = 2
                    self.type_partner_domain = type_partner_domain
                    self.type_partner = type_partner
                    #self.type_partner_domain = self.partner_id.type_contrib.ids
                    self.type_partner = self.partner_id.type_contrib.id
                else:
                    domain = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today),
                              ('template_child', '=', False)]
                    domain_exc = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today),
                                  ('template_child', '=', False)]
                    if self.template_agreement_id.partner_domain:
                        domain.append(('partner_domain', 'in', [self.partner_id.id]))
                        domain_exc.append(('partner_domain', 'in', [self.partner_id.id]))
                    if self.partner_id.type_contrib:
                        domain.append(('type_contrib', '=', self.partner_id.type_contrib.id))
                        domain_exc.append(('type_contrib', '=', self.partner_id.type_contrib.id))
                    if self.payment_method:
                        domain.append(('payment_method_domain', 'in', self.payment_method.id))
                        domain_exc.append(('payment_method_domain', 'in', self.payment_method.id))
                    if self.team_id:
                        domain.append(('team_id_domain', 'in', self.team_id.id))
                        domain_exc.append(('exception_team_id_domain', 'in', self.team_id.id))
                    templates_method = self.env['agreement'].sudo().search(domain)
                    templates_method_exc = self.env['agreement'].sudo().search(domain_exc)
                    if templates_method:
                        for temp in templates_method:
                            partner_domain = False
                            valid_domain = False
                            if temp.partner_domain:
                                partner_domain = True
                                if self.partner_id.id in temp.partner_domain.ids:
                                    valid_domain = True
                            if partner_domain == True and valid_domain == True:
                                template_domain.append(temp.id)
                            if partner_domain == False and valid_domain == False:
                                template_domain.append(temp.id)
                    if templates_method_exc:
                        for exc in templates_method_exc:
                            partner_domain_ex = False
                            valid_domain_ex = False
                            if exc.id not in template_domain:
                                if exc.partner_domain:
                                    partner_domain_ex = True
                                    if self.partner_id.id in exc.partner_domain.ids:
                                        valid_domain_ex = True
                                if partner_domain_ex == True and valid_domain_ex == True:
                                    template_domain.append(exc.id)
                                if partner_domain_ex == False and valid_domain_ex == False:
                                    template_domain.append(exc.id)

                    # for temp1 in self.template_domain:
                    #     for tparner in temp1.type_partner_domain:
                    #         if tparner.id not in type_partner_domain:
                    #             type_partner_domain.append(tparner.id)
                    self.template_domain = template_domain
                    self.payment_method_domain = self.template_agreement_id.payment_method_domain
                    #self.type_partner_domain = self.partner_id.type_contrib.ids
                    self.type_partner = self.partner_id.type_contrib.id
                    self.payment_deadline_domain = self.template_agreement_id.payment_deadline_domain
                if self.team_id.id in self.template_agreement_id.exception_team_id_domain.ids:
                    self.check_exception = True
                else:
                    self.check_exception = False
                if self.template_agreement_id.id not in self.template_domain.ids:
                    self.template_agreement_id = ''
                if self.partner_id.company_type == 'company':
                    type_partner = 1
                else:
                    type_partner = 2
                #self.type_partner_domain = type_partner_domain
                self.type_partner = type_partner
                self.payment_period_domain = self.template_agreement_id.payment_period_domain
            if not self.template_agreement_id:
                domain = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today), ('template_child', '=', False)]
                domain_exc = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today)]
                if self.agreement_id:
                    domain.append(('parent_template_id', '=', self.agreement_id.id))
                if self.partner_id.type_contrib:
                    domain.append(('type_contrib', '=', self.partner_id.type_contrib.id))
                    domain_exc.append(('type_contrib', '=', self.partner_id.type_contrib.id))
                if self.payment_method:
                    domain.append(('payment_method_domain', 'in', self.payment_method.id))
                    domain_exc.append(('payment_method_domain', 'in', self.payment_method.id))
                if self.payment_period:
                    domain.append(('payment_period_domain', 'in', self.payment_period.id))
                    domain_exc.append(('payment_period_domain', 'in', self.payment_period.id))
                if self.payment_term_id:
                    domain.append(('payment_deadline_domain', 'in', self.payment_term_id.id))
                    domain_exc.append(('payment_deadline_domain', 'in', self.payment_term_id.id))
                if self.team_id:
                    domain.append(('team_id_domain', 'in', self.team_id.id))
                    domain_exc.append(('exception_team_id_domain', 'in', self.team_id.id))
                    templates_method = self.env['agreement'].sudo().search(domain)
                    templates_method_exc = self.env['agreement'].sudo().search(domain_exc)
                    if templates_method:
                        for temp in templates_method:
                            partner_domain = False
                            valid_domain = False
                            if temp.partner_domain:
                                partner_domain = True
                                if self.partner_id.id in temp.partner_domain.ids:
                                    valid_domain = True
                            if partner_domain == True and valid_domain == True:
                                template_domain.append(temp.id)
                            if partner_domain == False and valid_domain == False:
                                template_domain.append(temp.id)
                    if templates_method_exc:
                        for exc in templates_method_exc:
                            partner_domain_ex = False
                            valid_domain_ex = False
                            if exc.id not in template_domain:
                                if exc.partner_domain:
                                    partner_domain_ex = True
                                    if self.partner_id.id in exc.partner_domain.ids:
                                        valid_domain_ex = True
                                if partner_domain_ex == True and valid_domain_ex == True:
                                    template_domain.append(exc.id)
                                if partner_domain_ex == False and valid_domain_ex == False:
                                    template_domain.append(exc.id)
                    # for temp1 in self.template_domain:
                    #     for tparner in temp1.type_partner_domain:
                    #         if tparner.id not in type_partner_domain:
                    #             type_partner_domain.append(tparner.id)
                    self.template_domain = template_domain
                    self.payment_method_domain = self.payment_method
                    if self.partner_id.company_type == 'company':
                        type_partner = 1
                        # if self.team_id.template_agreement_company:
                        #     self.template_agreement_id = self.team_id.template_agreement_company.id
                    else:
                        type_partner = 2
                        # if self.team_id.template_agreement_person:
                        #     self.template_agreement_id = self.team_id.template_agreement_person.id
                    #self.type_partner_domain = self.partner_id.type_contrib.ids
                    self.type_partner = self.partner_id.type_contrib.id
                    # self.type_partner_domain = type_partner_domain

    def create_agreement(self):
        if not self.crm_line_ids:
            raise UserError("No se puede crear un contrato sin un Servicio. ")
        if not self.partner_id:
            raise UserError("No se puede crear un contrato sin un Cliente. ")
        if self.check_exception and not self.exception:
            raise UserError("Disculpe aun no ha sido aprobada su peticion de excepción. ")
        if self.partner_id.black_list:
            raise UserError("Lo siento este cliente se encuentra en blacklist. No puede crear contratos estando en BlackList")
        card = False
        if self.agreement_id:
            for mt in self.template_agreement_id:
                for pmd in mt.payment_method_domain:
                    if pmd.id == 7:
                        card = self.agreement_id.card_number.id or False
        created = self.env['agreement'].create({
            'partner_id': self.partner_id.id,
            'description': self.description or 'nuevo',
            'name': 'Nuevo',
            'crm_lead_id': self.id,
            #'agreement_type_id': 1,
            #'end_date': Date.to_string((datetime.now() + timedelta(days=365))),
            'start_date': Date.today(),
            'parent_agreement_id': self.agreement_id.id,
            'is_template': False,
            'gestor_id': self.user_id.id,
            'canal_id': self.canal_id.id,
            'subcanal_id': self.subcanal_id.id,
            'team_id': self.team_id.id,
            'assigned_user_id': self.user_id.id,
            'template_agreement_id': self.template_agreement_id.id,
            'payment_method': self.payment_method.id,
            'payment_period': self.payment_period.id,
            'payment_term_id': self.payment_term_id.id,
            'type_partner': self.type_partner.id,
            'payment_method_domain': self.payment_method_domain,
            'payment_period_domain': self.payment_period_domain,
            'type_partner_domain': self.type_partner_domain,
            'template_domain': self.template_domain,
            'payment_period_domain': self.template_agreement_id.payment_period_domain,
            'payment_deadline_domain': self.template_agreement_id.payment_deadline_domain,
            'card_number': card,
            'pricelist_id': self.template_agreement_id.pricelist_id.id,
        })
        for deltals in self.crm_line_ids:
            contract_line = {
                'agreement_id': created.id,
                'product_id': deltals.product_id.id,
                'type_line': deltals.type_line.id,
                'product_principal': deltals.product_principal.id,
                'name': deltals.product_id.name,
                'uom_id': deltals.product_id.uom_id.id,
                'partner_contact_id': deltals.partner_contact_id.id,
                'partner_invoice_id': deltals.partner_invoice_id.id,
                'price': deltals.price,
                'location': deltals.location,
            }
            line = self.env['agreement.line'].with_context(lead_exist=True).create(contract_line)
            deltals.write({'agreement_line_id': line.id})
            #line.write({'partner_contact_id': deltals.partner_contact_id.id})
        if self.template_agreement_id.extra_ids:
            if self.partner_id.company_type == 'company':
                partners = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id), ('repres_legal', '=', True)])
            else:
                partners = self.env['res.partner'].search([('id', '=', self.partner_id.id), ('repres_legal', '=', True)])
            for document in self.template_agreement_id.extra_ids:
                contract_document = {
                    'agreement_id': created.id,
                    'partner_repres_ids_domain': partners.ids if partners else False,
                    'name': created.name,
                    'firma': document.firma,
                    'firma_type': document.firma_type.id if document.firma_type else False,
                    'type_extra': document.type_extra.id,
                    'required_sign': document.required_sign,
                    'require_maihue': document.require_maihue,
                    'content': document.content,
                }
                line_document = self.env['agreement.extra'].create(contract_document)
        self.write({'agreement': created})
        #created.onchange_partner_id()
        return created

    def action_agreement(self):
        action = self.env.ref('agreement.agreement_form').read()[0]
        action['views'] = [(self.env.ref('agreement.agreement_form').id, 'form')]
        action['context'] = {
                             'name': self.name,
                             'code': self.name,
                            }
        return action

    def action_view_agreement(self):
        action = self.env.ref('agreement_blueminds.agreement_dashboard_agreement').read()[0]
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('crm_lead_id', '=', self.id)] #, ('state', 'in', ['draft', 'sent'])
        #agreement = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        agreement = self.mapped('agreement') #.filtered(lambda l: l.crm_lead_id in ([self.id]))
        if len(agreement) == 1:
            action['views'] = [(self.env.ref('agreement_blueminds.agreement_form').id, 'form')]
            action['res_id'] = agreement.id
        return action

    @api.constrains('agreement_id')
    def _check_agreement(self):
        if self.agreement_id:
            if self.agreement_id.anexo == False:
                raise ValidationError(_('El contrato: %s No permite anexos' %
                                        (self.agreement_id.name)))

    def unlink(self):
        agreements = []
        for record in self:
            agreements = self.env['agreement'].search([('crm_lead_id', '=', record.id)])
            if agreements:
                raise UserError('Lo siento, no se puede eliminar Este contacto, esta vinculado a otro modulo')
        return super(Lead, self).unlink()

    def write(self, values):
        if 'partner_id' in values:
            if 'agreement_exist' not in self._context:
                if values.get('partner_id') != self.partner_id.id:
                    if self.agreement_count != 0:
                        raise UserError("Lo siento, no puedes modificar el cliente de esta oportunidad cuando existe un contrato creado")
        return super(Lead, self).write(values)

class CrmtLine(models.Model):
    _name = "crm.line"
    _description = "CRM Lines"

    @api.model
    def default_get(self, fields):
        template_id = False
        result = super(CrmtLine, self).default_get(fields)
        context = dict(self.env.context)
        if context.get('template_agreement_id', False):
            template_id = context.get('template_agreement_id', False)
            template_id = self.env['agreement'].search([
                ('id', '=', template_id)])
        #team_id = result.get('team_id')
        # if not template_id:
        #     raise UserError("No se ha seleccionado ninguna plantilla")
        if template_id:
            result['product_domain'] = template_id.product_domain.ids
            result.update({'product_domain': template_id.product_domain.ids})
            self.product_domain = template_id.product_domain.ids
        return result

    @api.model
    def _compute_principal_domain(self):
        for record in self:
            principal_ids = False
            domain = []
            if record.product_id:
                #for do in record.product_domain:
                domain.append(record.product_id.product_tmpl_id.id)
                principal_ids = self.env['product.related'].search(
                    [('product_parent_id', 'in', domain), ('is_principal', '=', True)])
                list_pd = []
                for pd in principal_ids:
                    list_pd.append(pd.product_id.id)
                principal_domain = list_pd
                record.principal_domain = [(6, 0, principal_domain)]

    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     if self.template_agreement_id:
    #         self.product_id = self.template_agreement_id.product_domain.ids

    product_id = fields.Many2one("product.product", string="Servicio real", tracking=True)
    product_domain = fields.Many2many('product.product', 'product_line_domain_rel', 'product_id', 'line_id',
                                      string='Dominio Servicio', track_visibility="onchange")
    principal_domain = fields.Many2many('product.product', 'product_principal_rel_lead', 'product_id',
                                        'principal_id', track_visibility="onchange",
                                        compute="_compute_principal_domain",
                                        string='Productos Dominio')
    product_principal = fields.Many2one(
        "product.product",
        string="Product", track_visibility='onchange',
        # states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    type_line = fields.Many2one('agreement.line.type', string='Tipo de línea', readonly=False,
                                track_visibility='onchange'
                                )
    name = fields.Char(string="Description", required=True, tracking=True)
    crm_id = fields.Many2one("crm.lead", string="CRM", ondelete="cascade", tracking=True)
    partner_id = fields.Many2one(related="crm_id.partner_id", string="Partner", required=False, copy=True, tracking=True)
    qty = fields.Float(string="Cantidad", default="1", tracking=True)
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True, tracking=True)
    location = fields.Char('Ubicación', tracking=True)
    #agreement_line_id = fields.Integer('linea de contrato', tracking=True)
    agreement_line_id = fields.Many2one('agreement.line', "linea de contrato", required=False,
                                   tracking=True)
    price = fields.Float('Precio', digits='Product Price', tracking=True)
    partner_contact_id = fields.Many2one("res.partner", string="Dirección", #copy=True,
        domain="[('type', '=', 'delivery'), ('parent_id', '=', partner_id)]", tracking=True)
    partner_invoice_id = fields.Many2one("res.partner", string="Dirección Facturación", copy=True,
        domain="[('type', '=', 'invoice'), ('parent_id', '=', partner_id)]", tracking=True)
    state = fields.Selection(related='agreement_line_id.state', string='Estado', copy=False, readonly=True, tracking=True)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id.id
        for record in self:
            principal_ids = False
            domain = []
            if record.product_id:
                #for do in record.product_domain:
                domain.append(record.product_id.product_tmpl_id.id)
                principal_ids = self.env['product.related'].search(
                    [('product_parent_id', 'in', domain), ('is_principal', '=', True)])
                list_pd = []
                for pd in principal_ids:
                    list_pd.append(pd.product_id.id)
                principal_domain = list_pd
                record.principal_domain = [(6, 0, principal_domain)]

class CrmLine(models.Model):
    _name = 'crm.rline'
    _description = "CRM Linea Real"

    product_id = fields.Many2one("product.product", string="Servicio")
    name = fields.Char(string="Description", required=True)
    crm_id = fields.Many2one("crm.lead", string="CRM", ondelete="cascade", domain="[('agreement_count', '=', False)]")
    partner_id = fields.Many2one(related="crm_id.partner_id", string="Partner", required=False, copy=True)
    qty = fields.Float(string="Cantidad", default="1")
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True)
    location = fields.Char('Ubicación')
    price = fields.Float('Precio', digits='Product Price')
    partner_contact_id = fields.Many2one("res.partner", string="Dirección", domain="[('parent_id', '=', False)]")
    partner_invoice_id = fields.Many2one("res.partner", string="Dirección Facturación", copy=True, domain="[('parent_id', '=', False)]")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id.id
