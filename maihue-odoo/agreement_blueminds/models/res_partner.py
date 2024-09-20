# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import fields, models, api
from odoo.exceptions import Warning, UserError
from datetime import timedelta, date, datetime, tzinfo
from stdnum import get_cc_module

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_admin = fields.Boolean(string='Administrador de Contratos')

class Partner(models.Model):
    _name = "res.partner"
    _inherit = ['res.partner', 'mail.thread', 'mail.activity.mixin']

    def _compute_agreement_count(self):
        agreement_data = self.sudo().env['agreement'].read_group([('state', '!=', 'cancel'), ('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
        mapped_data = dict([(q['partner_id'][0], q['partner_id_count']) for q in agreement_data])
        for agreement in self:
            agreement.agreement_count = mapped_data.get(agreement.id, 0)

    @api.model
    def default_get(self, default_fields):
        """Add the company of the parent as default if we are creating a child partner.
        Also take the parent lang by default if any, otherwise, fallback to default DB lang."""
        context = dict(self.env.context)
        context_comp = context.get('default_parent_id')
        values = super().default_get(default_fields)
        parent = self.browse(context_comp)
        #parent = self.env["res.partner"]
        if context_comp:
            values['commune'] = parent.commune.id
        return values

    def _get_contact_name(self, partner, name):
        res = super(Partner, self)._get_contact_name(partner, name)
        res = name
        return res

    def get_ep(self):
        eti = []
        if self.type == 'contact':
            eti = [4, 5]
        if self.company_type == 'person' and self.contract == True:
            eti = [4, 5]
        return eti

    def _compute_type_contrib(self):
        for partner in self:
            if partner.company_type:
                if partner.company_type == 'person':
                    partner.type_contrib_domain = [2]
                    partner.l10n_cl_sii_taxpayer_type = '3'
                    partner.type_contrib = 2
                    # self.repres_legal = True
                if partner.company_type == 'company':
                    partner.type_contrib_domain = [1]
                    partner.l10n_cl_sii_taxpayer_type = '1'
                    partner.type_contrib = 1
                    # self.repres_legal = False

    name = fields.Char(track_visibility="onchange")
    title = fields.Many2one(track_visibility="onchange")
    function = fields.Char(track_visibility="onchange")
    country_id = fields.Many2one(track_visibility="onchange")
    comment = fields.Html(track_visibility="onchange")
    email = fields.Char(track_visibility="onchange")
    type = fields.Selection(track_visibility="onchange")
    agreement_ids = fields.One2many(
        "agreement",
        "partner_id",
        string="Agreements")
    etiqueta_person = fields.Many2many('etiqueta.person', 'etiqueta_person_rel', 'person_id',
                                             'partner_id', default=get_ep,
                                             string='Tipo de persona', track_visibility="onchange")
    type_contrib = fields.Many2one(
        "agreement.type.contrib", required=False,
        string="Tipo de Contribuyente", track_visibility="onchange")
    type_contrib_domain = fields.Many2many('agreement.type.contrib', 'type_contrib_rel', 'type_contrib_id',
                                             'partner_id', #compute='_compute_type_contrib',
                                             string='type contrib domain', track_visibility="onchange")
    taxpayer_type_domain = fields.Many2many('agreement.taxpayer', 'taxpayer_type_rel', 'taxpayer_id',
                                             'partner_id', #compute='_compute_type_contrib',
                                             string='taxpayer type domain', track_visibility="onchange")
    commune = fields.Many2one('res.country.commune', 'Comuna', track_visibility="onchange")

    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type',
        string="Identification Type", index=True, auto_join=True,
        default=lambda self: self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False),
        help="The type of identification", track_visibility="onchange")
    vat = fields.Char(string='Identification Number', help="Identification Number for selected type", track_visibility="onchange")

    add_another_number = fields.Boolean(string="Agregar otro numero", track_visibility="onchange")
    add_another_number1 = fields.Boolean(string="+")
    add_another_number2 = fields.Boolean(string="+")
    add_another_number3 = fields.Boolean(string="+")
    phone0 = fields.Char(string="Teléfono0", track_visibility="onchange")
    phone1 = fields.Char(string="Teléfono1", track_visibility="onchange")
    phone2 = fields.Char(string="Teléfono2", track_visibility="onchange")
    phone3 = fields.Char(string="Teléfono3", track_visibility="onchange")
    phone4 = fields.Char(string="Teléfono4", track_visibility="onchange")
    etiqueta_telefono = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias", track_visibility="onchange")
    etiqueta1 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias", track_visibility="onchange")
    etiqueta2 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias", track_visibility="onchange")
    etiqueta3 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias", track_visibility="onchange")
    etiqueta4 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias", track_visibility="onchange")
    means_ids = fields.Many2many('means', string="Recursos", track_visibility="onchange")
    capabilities_ids = fields.Many2many('capabilities', string="Capacidades", track_visibility="onchange")
    geolocation_x = fields.Char(string="Geolocalización X", track_visibility="onchange")
    geolocation_y = fields.Char(string="Geolocalización Y", track_visibility="onchange")
    geolocation_url = fields.Char(string="Geolocalización URL", track_visibility="onchange")
    phone_code = fields.Integer('Codigo de llamada de pais', track_visibility="onchange")
    sucursal = fields.Char(string="Sucursal", track_visibility="onchange")
    zona_comercial = fields.Many2one('zona.comercial', string='Zona', track_visibility="onchange")
    fact_integral = fields.Selection([('contrato', 'Separada por Contrato')],
                                 string="Tipo de Facturación", default='contrato', track_visibility="onchange")
    status_payment = fields.Selection(
        [('al', 'Al Día'), ('atr', 'Atrasado')], string='Payment status', track_visibility="onchange")
    status_method_payment = fields.Char(string='Payment Method Status', track_visibility="onchange")
    vinculation_id = fields.Many2one('res.partner', string='Vinculation Contact', index=True, track_visibility="onchange")
    contract = fields.Boolean(string='Contrato', default=False, track_visibility="onchange")
    special_maihue = fields.Boolean(string='Especial para el uso RUT', track_visibility="onchange")
    vinculation_maihue = fields.Boolean(string='Vinculacion maihue', track_visibility="onchange")
    check_maihue = fields.Boolean(string='check maihue', default=False, track_visibility="onchange")
    is_user_internal = fields.Boolean(string='Usuario Interno', compute='_compute_is_internal_user', store=True, track_visibility="onchange")
    repres_legal = fields.Boolean('Representante Legal', track_visibility="onchange")
    father = fields.Boolean('Cliente/Proveedor Maihue', default=True, track_visibility="onchange")
    ocul_repres_legal = fields.Selection(related='parent_id.company_type', string='Oculta representante legal', track_visibility="onchange")
    vat_child = fields.Char(string='Rut Contacto de Cliente', index=True,
                      help="Rut de Contacto de Cliente", track_visibility="onchange")
    log_ids = fields.One2many(
        "log.partner", "partner_id", string="Log Cliente", copy=False, track_visibility="onchange")
    type = fields.Selection(track_visibility="onchange")
    bussines_name = fields.Char(string='Razon Social', track_visibility="onchange")
    full_name = fields.Char(string='Nombres', track_visibility="onchange")
    father_name = fields.Char(string='Apellido Paterno', track_visibility="onchange")
    mother_name = fields.Char(string='Apellido Materno', track_visibility="onchange")
    fantasy_name = fields.Char(string='Nombre Fantasia', track_visibility="onchange")
    black_list = fields.Boolean('Blacklist', tracking=True)
    compute_black_list = fields.Boolean('Blacklist', compute='_compute_activate_black_list')
    #agreement_count = fields.Integer(compute='_compute_agreement_count', string='Contratos')

    def _compute_activate_black_list(self):
        for record in self:
            active = False
            if self.env.user.has_group('agreement_blueminds.manage_activate_blacklist'):
                active = True
            record.compute_black_list = active

    @api.depends()
    def _compute_is_internal_user(self):
        ResUsers = self.env['res.users']
        for partner in self:
            user = ResUsers.search([('partner_id', '=', partner.id)])
            if user:
                partner.is_user_internal = True
            else:
                partner.is_user_internal = False


    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            type_contrib = self.env['agreement.type.contrib'].search([
                ('code', '=', 'J')], limit=1)
            self.type_contrib = type_contrib.id
            self.type_contrib_domain = [type_contrib.id]
            self.repres_legal = False
            self.l10n_cl_dte_email = 'dte@dte.cl'
            self.etiqueta_person = [4, 3]
        else:
            type_contrib = self.env['agreement.type.contrib'].search([
                ('code', '=', 'N')], limit=1)
            self.type_contrib = type_contrib.id
            self.type_contrib_domain = [type_contrib.id]
            self.repres_legal = True
            self.l10n_cl_dte_email = 'dte@dte.cl'
            self.l10n_cl_activity_description = 'Sin Giro'
            self.etiqueta_person = []

    @api.onchange('type')
    def onchange_type_m(self):
        if self.type == 'contact':
            if self.parent_id.company_type != 'company':
                self.etiqueta_person = [4,3]
            else:
                self.etiqueta_person = []
        else:
            self.etiqueta_person = []

    @api.onchange('type_contrib')
    def onchange_type_contrib(self):
        if self.type_contrib.code == 'J':
            self.l10n_cl_sii_taxpayer_type = '1'
        if self.type_contrib.code == 'N':
            self.l10n_cl_sii_taxpayer_type = '3'
        if self.type_contrib.code == 'PE':
            self.l10n_cl_sii_taxpayer_type = '4'
        if self.type_contrib.code == 'PBH':
            self.l10n_cl_sii_taxpayer_type = '2'

    # @api.onchange('repres_legal''repres_legal', 'etiqueta_person', 'phone0', 'email', 'name')
    # def onchange_repres_legal(self):
    #     if self.parent_id:
    #         if self.parent_id.company_type == 'person':
    #             if self.repres_legal == True:
    #                 repres_legal = self.env['res.partner'].search([('parent_id', 'in', self.parent_id.ids), ('repres_legal', '=', True), ('vat', '=', self.vat)])
    #                 if len(repres_legal) > 2:
    #                     raise UserError(
    #                         'Lo siento, no se puede crear mas de un representante legal para un cliente individual')



    def validate_phone(self, phone):
        if self.country_id.name == 'Chile':
            numero = list(phone)
            for num in numero:
                if not num.isdigit():
                    raise UserError("El campo |Teléfono| debe tener unicamente valores numericos")
            if len(numero) == 9:
                res_country_code = self.country_id.phone_code
                cod_area_f = str(res_country_code)
                numero1 = '+' + cod_area_f + phone
                phone = numero1
            else:
                raise UserError('El campo |Teléfono| Debe tener 9 digitos')
        return phone



    @api.onchange('mobile', 'phone0', 'phone1', 'phone2', 'phone3', 'phone4', 'country_id')
    def activate_phone_validation(self):
        for record in self:
            if record.country_id.name == 'Chile':
                if record.mobile:
                    record.validate_phone(record.mobile)
            if record.phone0:
                record.validate_phone(record.phone0)
            if record.phone1:
                record.validate_phone(record.phone1)
            if record.phone2:
                record.validate_phone(record.phone2)
            if record.phone3:
                record.validate_phone(record.phone3)
            if record.phone4:
                record.validate_phone(record.phone4)


    @api.onchange('email')
    def validate_email(self):
        if self.email:
            email_format = re.compile(r"[^@]+@[^@]+\.[^@]+")
            if not email_format.match(self.email):
                raise UserError("El campo |Correo electrónico| tiene un formato invalido")


    @api.onchange('vat_child')
    def validate_rut_child(self):
        mod = get_cc_module('cl', 'rut')
        if self.country_id.name == 'Chile':
            if self.vat_child and self.l10n_latam_identification_type_id.id == 4:
                val_rut = mod.is_valid(self.vat_child)
                if val_rut == False:
                    raise UserError("El rut ingresado |{0}| no es valido".format(self.vat_child))

    @api.onchange('vat')
    def validate_rut(self):
        mod = get_cc_module('cl', 'rut')
        if self.country_id.name == 'Chile':
            if self.contract == True and self.vat == False:
                raise UserError("Por favor ingresar RUT para el cliente tipo contrato")
            if self.vat and self.l10n_latam_identification_type_id.id == 4:
                val_rut = mod.is_valid(self.vat)
                if val_rut == False:
                    raise UserError("El rut ingresado |{0}| no es valido".format(self.vat))

    @api.onchange('country_id')
    def place_code_according_to_country(self):
        if self.country_id:
            code = self.country_id.phone_code
            self.phone_code = code
        else:
            self.phone_code = 0

    @api.model
    def create(self, vals):
        jamie = self._context.get('active_id')
        self.with_context(create_pem=True)
        #self._context.update({'create_pem': True})
        if not vals.get('vat'):
            if vals.get('country_id') == 46 and vals.get('company_type') == 'person':
                raise UserError(
                    "El Rut es requerido para chile")
            if vals.get('country_id') == 46 and vals.get('company_type') == 'company':
                raise UserError(
                    "El Rut es requerido para chile")
        if vals.get('vat'):
            if vals.get('country_id') == 46 and vals.get('l10n_latam_identification_type_id') == 4:
                vats = self.env['res.partner'].search([('vat', '=', vals.get('vat')), ('parent_id', '=', False)])
                if vats:
                    for vat_special in vats:
                        if vals.get('special_maihue'):
                            if vat_special.company_type == vals.get('company_type'):
                                raise UserError(
                                    "Lo siento, El Rut que desea crear ya existe (No es posible aplicar el mismo rut a dos clientes del mismo tipo)")
                        else:
                            raise UserError(
                                "Lo siento, El Rut que desea crear ya existe, si desea guardarlo active el check Especial para el uso RUT")
            if vals.get('country_id') == 46 and vals.get('l10n_latam_identification_type_id') != 4:
                raise UserError(
                    "El Rut es requerido para chile")
        # if not vals.get('special_maihue'):
        #     if vals.get('vat'):
        #         vats = self.env['res.partner'].search([('vat', '=', vals['vat'])])
        #         if vats:
        #             raise UserError("Lo siento, El Rut que desean crear ya existe, si desea guardarlo active Especial para el uso RUT")
        if vals.get('contract'):
            vals['check_maihue'] = True
        if vals.get('parent_id'):
            vals['father'] = False
            # if self.parent_id.company_type == 'person':
            #     if 'child_ids' in vals:
            #         for jai in vals['child_ids']:
            #             jamie =1
            #     rep_legal = self.env['res.partner'].search([('parent_id', '=', self.parent_id.id), ('etiqueta_person', 'in', [1])])
            #     if rep_legal:
            #         raise UserError('Lo siento, no se puede crear mas de un representante legal para un cliente individual')
            name = ''
            if vals.get('type') == 'other' or vals.get('type') == 'delivery':
                comuna = self.env['res.country.commune'].search([('id', '=', vals['commune'])])
                if vals['street']:
                    name = str(vals['street'])
                if comuna:
                    name = name + ', ' +str(comuna.name)
                if vals['street2']:
                    name = name + ', ' +str(vals['street2'])
                if vals['sucursal']:
                    name = name + ', ' +str(vals['sucursal'])
                vals['name'] = name
        else:
            vals['father'] = True
        if 'company_type' in vals:
            if vals['company_type'] == 'company':
                vals['etiqueta_person'] = False
        res = super(Partner, self).create(vals)
        # if res.company_type == 'person' and res.contract == True:
        #     contact_values = {
        #             'name': res.name,
        #             'sucursal': res.sucursal,
        #             'title': res.title,
        #             'function': res.function,
        #             'country_id': res.country_id.id,
        #             'comment': res.comment,
        #             'email': res.email,
        #             'l10n_latam_identification_type_id': res.l10n_latam_identification_type_id.id,
        #             'vat': res.vat,
        #             'etiqueta_person': res.etiqueta_person.ids,
        #             'phone_code': res.phone_code,
        #             'phone0': res.phone0,
        #             'phone1': res.phone1,
        #             'phone2': res.phone2,
        #             'phone3': res.phone3,
        #             'phone4': res.phone4,
        #             'etiqueta_telefono': res.etiqueta_telefono,
        #             'etiqueta1': res.etiqueta1,
        #             'etiqueta2': res.etiqueta2,
        #             'etiqueta3': res.etiqueta3,
        #             'etiqueta4': res.etiqueta4,
        #             'add_another_number': res.add_another_number,
        #             'add_another_number1': res.add_another_number1,
        #             'add_another_number2': res.add_another_number2,
        #             'add_another_number3': res.add_another_number3,
        #             'parent_id': res.id,
        #             'type': 'contact',
        #             'repres_legal': res.repres_legal,
        #             'vinculation_maihue': True,
        #             'father': False,
        #     }
        #     child = super(Partner, self).create(contact_values)
        #     res.write({'vinculation_id': child.id})
        return res

    # def action_view_agreement(self):
    #     action = self.env.ref('agreement_blueminds.agreement_dashboard_agreement').read()[0]
    #     action['context'] = {
    #         'search_default_draft': 1,
    #         'search_default_partner_id': self.id,
    #         'default_partner_id': self.id,
    #         #'default_opportunity_id': self.id
    #     }
    #     action['domain'] = [('partner_id', '=', self.id)]  # , ('state', 'in', ['draft', 'sent'])
    #     # agreement = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
    #     agreement = self.mapped('agreement')  # .filtered(lambda l: l.crm_lead_id in ([self.id]))
    #     if len(agreement) == 1:
    #         action['views'] = [(self.env.ref('agreement_blueminds.agreement_form').id, 'form')]
    #         action['res_id'] = agreement.id
    #     return action

    def write(self, values):
        vali = False
        create_ids = self.id or False
        # today = datetime.now().date()
        # today2 = self.create_date.date()
        if create_ids:
            if self.create_date.date() == datetime.now().date():
                create_ids = False
        type_company = ''
        contract = ''
        country_id = ''
        special_maihue = ''
        l10n_latam_identification_type_id = ''
        continuo = False
        primero = False
        if 'vat' in values:
            vat = values.get('vat')
        else:
            vat = self.vat
        if not self.vat:
            if self.country_id == 46 and self.company_type == 'person':
                raise UserError(
                    "El Rut es requerido para chile")
            if self.country_id == 46 and self.company_type == 'company':
                raise UserError(
                    "El Rut es requerido para chile")
        if self.vat:
            if self.country_id == 46 and self.l10n_latam_identification_type_id == 4:
                vats = self.env['res.partner'].search([('vat', '=', self.vat), ('parent_id', '=', False)])
                if vats:
                    for vat_special in vats:
                        if self.special_maihue:
                            if vat_special.company_type == self.company_type:
                                raise UserError(
                                    "Lo siento, El Rut que desea crear ya existe (No es posible aplicar el mismo rut a dos clientes del mismo tipo)")
                        else:
                            raise UserError(
                                "Lo siento, El Rut que desea crear ya existe, si desea guardarlo active el check Especial para el uso RUT")
            if self.country_id == 46 and self.l10n_latam_identification_type_id != 4:
                raise UserError(
                    "El Rut es requerido para chile")
        if values:
            if not 'child_ids' in values:
                for id in self:
                    log_vals = {
                        'partner_id': id.id,
                        'name': values,
                        'user_id': id.write_uid.id,
                    }
                    self.env['log.partner'].create(log_vals)
        for partner in self:
            if partner.type == 'contact' and partner.parent_id:
                agreements = self.env['agreement'].search([('partner_id', '=', partner.id)])
                if agreements:
                    if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                        if 'child_ids' in values:
                            for child in values['child_ids']:
                                if type(child[1]) == str:
                                    vali = True
                        if not vali:
                            raise UserError(
                                "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados")
                    # raise UserError(
                    #     "Usted no tiene permisos para editar Contactos Vinculados")
                crm_leads = self.env['crm.lead'].search([('partner_id', '=', partner.id)])
                # if crm_leads:
                #     if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                #         if 'child_ids' in values:
                #             for child in values['child_ids']:
                #                 if type(child[1]) == str:
                #                     vali = True
                #         if not vali:
                #             raise UserError(
                #                 "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados")
                #     # raise UserError(
                #     #     "Usted no tiene permisos para editar Contactos Vinculados")
                agreements_contact_legal = self.env['agreement'].search([('partner_invoice_id', '=', partner.id)])
                if agreements_contact_legal:
                    if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                        if 'child_ids' in values:
                            for child in values['child_ids']:
                                if type(child[1]) == str:
                                    vali = True
                        if not vali:
                            raise UserError(
                                "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados HIJO 1")
                    # raise UserError(
                    #     "Usted no tiene permisos para editar Contactos Vinculados")
                agreements_contact_serv = self.env['agreement.line'].search([('partner_con_id', '=', partner.id)])
                if agreements_contact_serv:
                    if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                        if 'child_ids' in values:
                            for child in values['child_ids']:
                                if type(child[1]) == str:
                                    vali = True
                        if not vali:
                            raise UserError(
                                "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados HIJO 2")
            if partner.type == 'delivery':
                # crm_in_line = self.env['crm.line'].search([('partner_contact_id', '=', partner.id)], limit=1)
                # if crm_in_line:
                #     if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                #         if 'child_ids' in values:
                #             for child in values['child_ids']:
                #                 if type(child[1]) == str:
                #                     vali = True
                #         if not vali:
                #             raise UserError(
                #                 "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados HIJO 3")
                agreements_in_line = self.env['agreement.line'].search([('partner_contact_id', '=', partner.id)],
                                                                       limit=1)
                if agreements_in_line:
                    if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                        if 'child_ids' in values:
                            for child in values['child_ids']:
                                if type(child[1]) == str:
                                    vali = True
                        if not vali:
                            raise UserError(
                                "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados HIJO 4")
                    #hasta aqui
            if 'contract' in values:
                contract = values.get('contract')
                new = True
            else:
                contract = partner.contract
            if 'company_type' in values:
                type_company = values.get('company_type')
            else:
                type_company = partner.company_type
            if 'l10n_latam_identification_type_id' in values:
                l10n_latam_identification_type_id = values.get('l10n_latam_identification_type_id')
            else:
                l10n_latam_identification_type_id = partner.l10n_latam_identification_type_id.id
            if 'country_id' in values:
                country_id = values.get('country_id')
            else:
                country_id = partner.country_id.id
            if 'special_maihue' in values:
                special_maihue = values.get('special_maihue')
            else:
                special_maihue = partner.special_maihue
            if not partner.parent_id:
                if not partner.env.user.has_group('agreement_blueminds.manage_edit_addresses'):
                    #print(values)
                    if 'child_ids' in values:
                        vali = True
                    if 'reminder_date_before_receipt' in values:
                        vali = True
                    if 'dicom_last_score' in values:
                        vali = True
                    if not vali:
                        if create_ids:
                            raise UserError(
                                "Usted no tiene permisos para editar Contactos y Contactos hijos Vinculados PADRE")
                if not vat:
                    if country_id == 46 and type_company == 'person' and contract == True:
                        raise UserError(
                            "El Rut es requerido para chile")
                    if country_id == 46 and type_company == 'company' and not partner.id == 1:
                        raise UserError(
                            "El Rut es requerido para chile")
                if vat:
                    if country_id == 46 and l10n_latam_identification_type_id == 4:
                        vats = self.env['res.partner'].search([('vat', '=', vat), ('parent_id', '=', False)])
                        if vats:
                            if len(vats) == 1:
                                if vats.id in partner.ids:
                                    continuo = True
                                    primero = True
                            for vat_special in vats:
                                if vat_special.id not in partner.ids:
                                    primero =  False
                                    if self.special_maihue and vat_special.company_type == type_company:
                                        raise UserError("Lo siento, El Rut que desea crear ya existe (No es posible aplicar el mismo rut a dos clientes del mismo tipo)")
                                if primero == False and special_maihue == False:
                                    raise UserError(
                                         "Lo siento, El Rut que desea crear ya existe, si desea guardarlo active el check Especial para el uso RUT")
                    if country_id == 46 and l10n_latam_identification_type_id != 4:
                        raise UserError(
                            "El Rut es requerido para chile")

            if 'contract' in values:
                if values.get('contract'):
                    values['check_maihue'] = True
            new = False
            if partner.parent_id and not partner.type == 'contact':
                values['vat'] = ''
                # values['commune'] = self.parent_id.commune
                rep_legal = self.env['res.partner'].search(
                    [('parent_id', '=', partner.parent_id.id), ('repres_legal', '=', True), ('vat', '=', partner.vat)])
                if len(rep_legal) > 1:
                    raise UserError('Lo siento, no se puede crear mas de un representante legal para un cliente individual')
                # if self.parent_id.company_type == 'person':
                #     if 'child_ids' in values:
                #         for jai in values['child_ids']:
                #             jamie =1
                        # if 'etiqueta_person' in values['child_ids'][2][2]:
                        #     eti_person = values['child_ids'][2][2].get('etiqueta_person')
                        #     if 1 in eti_person[0][2]:
                        #         rep_legal = self.env['res.partner'].search([('parent_id', '=', self.parent_id.id), ('etiqueta_person', 'in', [1])])
                        #         if rep_legal:
                        #             raise UserError('Lo siento, no se puede crear mas de un representante legal para un cliente individual')
        ResCountryCommune = self.env['res.country.commune']
        for partner in self:
            name = ''
            if partner.type == 'other' or partner.type == 'delivery':
                if 'street' in values or 'street2' in values or 'commune' in values or 'sucursal' in values or 'name' in values:
                    if 'commune' in values:
                        comuna = ResCountryCommune.search([('id', '=', values['commune'])])
                    else:
                        comuna = ResCountryCommune.search([('id', '=', partner.commune.id)])
                    if 'street' in values:
                        if not values.get('street') == False:
                            name = str(values['street'])
                    else:
                        if partner.street:
                            name = str(partner.street)
                    if 'street2' in values:
                        if not values.get('street2') == False:
                            name = name + ', ' + str(values['street2'])
                    else:
                        if partner.street2:
                            name = name + ', ' + str(partner.street2)
                    if comuna:
                        name = name + ', ' + str(comuna.name)
                    if 'sucursal' in values:
                        if not values.get('sucursal') == False:
                            name = name + ', ' + str(values['sucursal'])
                    else:
                        if partner.sucursal:
                            name = name + ', ' + str(partner.sucursal)
                    values['name'] = name
        return super(Partner, self).write(values)

    def unlink(self):
        agreements = []
        crm_leads = []
        for record in self:
            if record.type == 'contact':
                if record.parent_id:
                    agreements = self.env['agreement'].search([('partner_id', '=', record.parent_id.id)])
                else:
                    agreements = self.env['agreement'].search([('partner_id', '=', record.id)])
                if record.parent_id:
                    crm_leads = self.env['crm.lead'].search([('partner_id', '=', record.parent_id.id)])
                else:
                    crm_leads = self.env['crm.lead'].search([('partner_id', '=', record.id)])
                if crm_leads:
                    raise UserError('Lo siento, no se puede eliminar Este contacto, esta vinculado a otro modulo')
                if not agreements:
                    childs = self.env['res.partner'].search([('parent_id', '=', record.id)])
                    for child in childs:
                        child.unlink()
                else:
                    raise UserError('Lo siento, no se puede eliminar Este contacto, esta vinculado a otro modulo')
            if record.type == 'delivery':
                crm_in_line = self.env['crm.line'].search([('partner_contact_id', '=', record.id)], limit=1)
                if crm_in_line:
                    raise UserError('Lo siento, no se puede eliminar esta Dirección, esta vinculado a una oportunidad: '+str(crm_in_line.crm_id.name))
                agreements_in_line = self.env['agreement.line'].search([('partner_contact_id', '=', record.id)],
                                                                       limit=1)
                if agreements_in_line:
                    raise UserError('Lo siento, no se puede eliminar esta Dirección, esta vinculado a un contrato: ' + str(agreements_in_line.agreement_id.name))
        return super(Partner, self).unlink()

    # @api.model
    # def write(self, vals):
    #     if self.parent_id:
    #         name = ''
    #         if self.type == 'other' or self.type == 'delivery':
    #             if 'street' in vals or 'street2' in vals or 'commune' in vals or 'sucursal' in vals:
    #                 comuna = self.env['res.country.commune'].search([('id', '=', vals['commune'])])
    #                 if vals['street']:
    #                     name = str(vals['street'])
    #                 if comuna:
    #                     name = ' ' + str(comuna.name)
    #                 if vals['street2']:
    #                     name = ' ' + str(vals['street2'])
    #                 if vals['sucursal']:
    #                     name = ' ' + str(vals['sucursal'])
    #                 vals['name'] = name
    #     return super(Partner, self).write()

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            return True
            #raise ValidationError(_('You cannot create recursive Partner hierarchies.'))


class EtiquetaPerson(models.Model):
    _name = 'etiqueta.person'
    _description = 'Etiqueta Tipo de persona'

    name = fields.Char('Nombre')

class AgreementTaxpayer(models.Model):
    _name = 'agreement.taxpayer'
    _description = 'Domain for taxpayer type'

    name = fields.Char('Nombre')

class ResCountryStateRegion(models.Model):
    _name = 'res.country.state.region'
    _description = 'Region of a state'

    name = fields.Char(string='Region Name', required=True,
                       help='The state code.')
    code = fields.Char(string='Region Code', required=True,
                       help='The region code.')
    # child_ids = fields.One2many('res.country.state', 'region_id',
    #                             string='Child Regions')


class ResCountryProvinces(models.Model):
    _name = 'res.country.provinces'
    _description = "Res Country Provinces"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)
    state_id = fields.Many2one('res.country.state', 'Región')

class ResCountryCommune(models.Model):
    _name = 'res.country.commune'
    _description = "Res Country Commune"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)
    prov_id = fields.Many2one('res.country.provinces', 'Provincia')

class LogPartner(models.Model):
    _name = 'log.partner'

    name = fields.Char(required=True, string='Campos')
    user_id = fields.Many2one(
        "res.users", string="Usuario", track_visibility="onchange")
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Cliente', ondelete='cascade',
        track_visibility='onchange', readonly=False, invisible=True)
