# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError, ValidationError
import werkzeug
from datetime import datetime, date, timedelta
import csv
import copy
#from calendar import monthrange
from dateutil.rrule import rrule, MONTHLY

# Variable global para el uso de rentals
MONTHS = ("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
          "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre")


class AgreementLine(models.Model):
    _name = "agreement.line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Agreement Lines"

    def name_get(self):
        result = []
        for group in self:
            if group.is_template:
                name = group.name
            else:
                name = group.name + ' ' + group.product_id.name
            result.append((group.id, name))
        return result

    @api.model
    def _compute_principal_domain(self):
        for record in self:
            principal_ids = False
            domain = []
            # if record.agreement_id:
            #     if record.agreement_id.crm_lead_id:
            #         if record.agreement_id.crm_lead_id.crm_line_ids:
            #             for line_crm in record.agreement_id.crm_lead_id.crm_line_ids:
            #                 if line_crm.product_id == record.product_id:
            #                     if not record.partner_contact_id:
            #                         if line_crm.partner_contact_id:
            #                             record.partner_contact_id = line_crm.partner_contact_id.id
            if record.product_domain:
                for do in record.product_domain:
                    domain.append(do.product_tmpl_id.id)
                principal_ids = self.env['product.related'].search(
                    [('product_parent_id', 'in', domain), ('is_principal', '=', True)])
                list_pd = []
                for pd in principal_ids:
                    list_pd.append(pd.product_id.id)
                principal_domain = list_pd
                record.principal_domain = [(6, 0, principal_domain)]


    product_id = fields.Many2one('product.product', track_visibility="onchange")
    product_domain = fields.Many2many(related='agreement_id.template_agreement_id.product_domain', string='Services', track_visibility="onchange")
    principal_domain = fields.Many2many('product.product', 'product_principal_rel', 'product_id',
                                             'principal_id', track_visibility="onchange", compute="_compute_principal_domain",
                                             string='Productos Dominio')
    name = fields.Char(
        string="Line",
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    agreement_id = fields.Many2one(
        "agreement",
        string="Agreement",
        ondelete="cascade",
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    qty = fields.Float(string="Quantity", default=1, track_visibility="onchange",
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        required=False,
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    location = fields.Char('Location',
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    price = fields.Float('Monthly Price', readonly=False,
        track_visibility='onchange', digits='Product Price')
    price_instalacion = fields.Float('installation price', readonly=False, track_visibility='onchange', digits='Product Price')
    partner_id = fields.Many2one(
        related="agreement_id.partner_id",
        string="Client",
        required=False,
        copy=True,
        track_visibility='onchange',
        help="The customer or vendor this agreement is related to.")
    partner_vat = fields.Char(
        related="partner_id.vat", track_visibility='onchange', string="Rut", readonly=True)
    partner_contact_id = fields.Many2one(
        "res.partner",
        string="Installation Address",
        #copy=True,
        track_visibility='onchange',
        domain="[('type', '=', 'delivery'), ('parent_id', '=', partner_id)]",
        help="The primary partner contact (If Applicable).",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Contact Billing",
        copy=True,
        track_visibility='onchange',
        #domain="[('type', '=', 'invoice'), ('parent_id', '=', partner_id)]",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    valor = fields.Float("Inst Value", store=True,
        track_visibility='onchange', digits='Product Price',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                         )
    is_template = fields.Boolean(string='is_template', related='agreement_id.is_template', track_visibility='onchange')
    agreement_line_keys = fields.Many2one("stock.production.lot", string="Serial number", copy=True,
        track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                          )
    # key_contact_id = fields.Many2one(
    #     "res.partner",
    #     string="Contacto Clave",
    #     copy=True,
    #     domain="[('parent_id', '=', partner_id)]")
    # user_install_id = fields.Many2one('res.users', string='Instalador Prueba', ondelete='cascade')
    # user_finish_id = fields.Many2one('res.users', string='Instalador Definitivo', ondelete='cascade')
    # charge_maintence = fields.Many2one('res.users', string='Encargado Mantenciones', ondelete='cascade')
    # date_test = fields.Date(string='Inicio Prueba', default=fields.Date.context_today)
    # date_finish = fields.Date(string='Definitiva', default=fields.Date.context_today)
    mantenedor = fields.Many2one(
        "res.users", string="Maintainer", track_visibility="onchange",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    product_principal = fields.Many2one(
        "product.product",
        string="Product", track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    partner_con_id = fields.Many2one(
        "res.partner",
        string="Contact Service",
        copy=True,
        track_visibility='onchange',
        #domain="[('type', '=', 'contact'), ('parent_id', '=', partner_id)]", readonly=True,
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    start_date = fields.Date(
        string="Test Start", #default=fields.Date.context_today,
        track_visibility="onchange", readonly=False,
        help="Test start date",
        #states={'pre': [('readonly', False)]}
    )
    test_day = fields.Many2one(
        "agreement.test.day", required=False, track_visibility='onchange',
        string="Days without charge",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state = fields.Selection([
        ('draft', 'BORRADOR'),
        ('pen', 'PRUEBA PENDIENTE AGENDAR'),
        ('reage', 'REAGENDAR'),
        ('pre', 'PRUEBA AGENDADA'),
        ('prueba', 'PRUEBA EN CURSO'),
        ('fallida', 'PRUEBA FALLIDA'),
        ('win', 'PRUEBA GANADA'),
        ('vali', 'EN VALIDACION ADM'),
        ('revisado', 'REVISADO PEND ACTIVAR'),
        ('act', 'ACTIVADO'),
        #('act_end', 'VALIDADO'),
        #('vigente', 'VIGENTE'),
        #('inci', 'INCIDENCIA'),
        ('sol_can', 'SOLICITUD DE CANCELACIÓN'),
        ('pro_can', 'EN PROCESO CANCELACIÓN'),
        ('cancelado', 'CANCELADO'),
        #('post_can', 'DESCARTADO POST-PRUEBA'),
        ('sol_baja', 'SOLICITUD DE BAJA'),
        ('proceso', 'EN PROCESO BAJA'),
        ('no_vigente', 'NO VIGENTE')], 'State', default='draft',
        copy=False, readonly=True, tracking=True)
    invoicing_line_ids = fields.One2many(
        "invoice.line",
        "agreement_line_ids",
        string="Invoices", readonly=True,
        track_visibility='onchange',
        copy=False)
    # tickets_line_ids = fields.One2many(
    #     "helpdesk.ticket",
    #     "agreement_line_ids",
    #     string="Tickets", readonly=True,
    #     track_visibility='onchange',
    #     copy=False)
    date_end_contract = fields.Date(
        string="Fecha de Baja", readonly=False,
        track_visibility="onchange",
        help="Date of cancellation of the contract line")
    pricelist_inst = fields.Many2one(related='agreement_id.pricelist_id', string='Installation Rate', track_visibility="onchange")
    pricelist_mens = fields.Many2one(related='agreement_id.pricelist_id', string='Monthly rate', track_visibility="onchange")
    pricelist_inst_domain = fields.Many2many('product.pricelist', 'agreement_pricelist_inst', 'pricelist_id',
                                           'agreement_line_id',
                                           string='Installation Rate', readonly=True,
                                           track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                             )
    pricelist_mens_domain = fields.Many2many('product.pricelist', 'agreement_pricelist_mens', 'pricelist_id',
                                           'agreement_line_id',
                                           string='Monthly rate', readonly=True,
                                           track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                             )
    date_inst = fields.Date(
        string="Test Installation Date", track_visibility="onchange", readonly=True,
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_inst = fields.Selection([
        ('pen', 'Pendiente Agendar'),
        ('agen', 'Agendada'),
        ('reali', 'Realizada'),
        ('rea', 'Reagendar'),
        ('cancel', 'Cancelada')], 'Status Installation Test', track_visibility="onchange",
        copy=False, readonly=False, states={'pre': [('readonly', False)]})
    state_desinst = fields.Selection([
        ('pen', 'Pendiente Agendar'),
        ('agen', 'Agendada'),
        ('reali', 'Realizada'),
        ('rea', 'Reagendar'),
        ('cancel', 'Cancelada')], 'Uninstall Status', track_visibility="onchange",
        copy=False) #, readonly=True, states={'pre': [('readonly', False)]}
    date_def = fields.Date(
        string="Final Installation Date", track_visibility="onchange", readonly=False)
    date_desinst = fields.Date(
        string="Uninstall Date", track_visibility="onchange", readonly=False,
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_def = fields.Selection([
        ('pen', 'Pendiente Agendar'),
        ('agen', 'Agendada'),
        ('reali', 'Realizada'),
        ('rea', 'Reagendar'),
        ('cancel', 'Cancelada')], 'Final Installation Status', track_visibility="onchange",
        copy=False, readonly=False)
    type_line = fields.Many2one('agreement.line.type', string='Line Type', readonly=False,
                                      track_visibility='onchange'
                                      )
    zona_com = fields.Many2one('maihue.zone', string="Commercial zone", readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                               )
    sector_comercial = fields.Many2one('sector.comercial', string='Sector Comercial', readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                     )
    zona_comercial = fields.Many2one('zona.comercial', string='Commercial zone', readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)], 'pen': [('readonly', False)]}
                                     )
    zona_mantencion = fields.Many2one('zona.mantencion', string='Zona Mantencion ', readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                      )
    sector_mantencion = fields.Many2one('sector.mantencion', string='Sector Mantencion ', readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                      )
    zona_man = fields.Many2one('maihue.zone', string="Maintenance area", readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                               )
    comisiona_id = fields.Many2one('res.users', string='Responsible Commission', readonly=True, track_visibility='onchange',
                                         states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                   )
    date_comision_pag = fields.Date(
        string="Commission Payment Date", track_visibility="onchange", readonly=False,
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_comision = fields.Char('State Commission', readonly=False, track_visibility='onchange',
                           #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                 )
    insta_prueba_id = fields.Many2one('res.users', string='Test Installer', readonly=False, track_visibility='onchange')
    desinst_id = fields.Many2one('res.users', string='Uninstaller', readonly=False, track_visibility='onchange',
                                   #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                 )
    insta_def_id = fields.Many2one('res.users', string='Instalador Final', readonly=False, track_visibility='onchange')
    cost_center = fields.Char(string="Cost center",
        required=False, readonly=True, track_visibility="onchange",
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                  )
    asesor_id = fields.Many2one('hr.employee', string='Advised By',
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                )
    gestor_id = fields.Many2one(related="agreement_id.gestor_id", string='Managed by',
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                )
    team_id = fields.Many2one(related="agreement_id.team_id", string='Sales team',
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                              )
    fecha_cobro = fields.Date(
        string="Fecha Cobro", track_visibility="onchange", invisible=True)
    general_msj = fields.Text('General Message', readonly=False, track_visibility='onchange')
    motivo_cancel = fields.Text('Motivo Cancelación', readonly=False, track_visibility='onchange'
                              )
    means_ids = fields.Many2many('means', string="Resources", track_visibility='onchange')
    capabilities_ids = fields.Many2many('capabilities', string="Capabilities", track_visibility='onchange')
    zona_domain = fields.Many2many('zona.comercial', 'agreement_zona_rel', 'zona_id',
                                             'agreement_line_id',
                                             string='Zonas Comerciales', readonly=True,
                                             track_visibility='onchange',
                                             states={'draft': [('readonly', False)], 'pre': [('readonly', False)],
                                                     'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                   )
    date_ajuste = fields.Date(
        string="Date Adjustment of Conditions", readonly=False,
        #states={'cerrado': [('readonly', False)]},
        track_visibility="onchange",
        help="Date Adjustment of Conditions")
    incidencia = fields.Boolean('Incidencia Contractual Linea', default=False, track_visibility="onchange")
    not_activate = fields.Boolean('No permite Activación', default=False, track_visibility="onchange")
    comuna_id = fields.Many2one(related='partner_contact_id.commune', string='Commune', required=False, track_visibility="onchange")
    referidor_id = fields.Many2one(related="agreement_id.referidor_id", string='Referrer', track_visibility="onchange")
    currency_id_inst = fields.Many2one("res.currency", string="currency", track_visibility="onchange")
    currency_id_men = fields.Many2one("res.currency", string="currency", track_visibility="onchange")
    reason_dis = fields.Selection([
        ('b_mai', 'BAJA MAIHUE'),
        ('b_cli', 'BAJA CLIENTE'),
        ('tras', 'TRASPASO'),
        ('up', 'UPGRADE'),
        ('down', 'DOWNGRADE')], 'Reason for Discharge', track_visibility="onchange",
        copy=False, readonly=False)
    description_dis = fields.Text('Description for Discharge', readonly=False, track_visibility="onchange")
    fut_line_rel = fields.Many2one("agreement.line", string="Fut Related Line", track_visibility="onchange")
    fut_state_rele = fields.Selection(related='fut_line_rel.state', string="Fut Related Line", track_visibility="onchange")
    fut_motivo_rel = fields.Selection([
        ('b_mai', 'BAJA MAIHUE'),
        ('b_cli', 'BAJA CLIENTE'),
        ('tras', 'TRASPASO'),
        ('up', 'UPGRADE'),
        ('down', 'DOWNGRADE')], 'Fut Reason Related',
        copy=False, readonly=False, track_visibility="onchange")
    fut_description_rel = fields.Text('Fut Related Description', track_visibility="onchange")
    pass_line_rel = fields.Many2one("agreement.line", string="Pass Related Line", track_visibility="onchange")
    pass_state_rele = fields.Selection(related='pass_line_rel.state', string="Pass State Related Line", track_visibility="onchange")
    pass_motivo_rel = fields.Selection([
        ('b_mai', 'BAJA MAIHUE'),
        ('b_cli', 'BAJA CLIENTE'),
        ('tras', 'TRASPASO'),
        ('up', 'UPGRADE'),
        ('down', 'DOWNGRADE')], 'Pass Reason Related',
        copy=False, readonly=False, track_visibility="onchange")
    pass_description_rel = fields.Text('Pass Related Description', track_visibility="onchange")
    sale_line_id = fields.Many2one('sale.order.line',
                                   string='Sales Order Line', track_visibility="onchange")
    maintenance_id = fields.Many2one('product.maintenance_m', string='Maintenance', track_visibility="onchange")
    agreement_penalty = fields.Many2one(
        "agreement.penalty", required=False,
        string="Penalty", readonly=False, track_visibility="onchange",
        states={'pre': [('readonly', False)]})
    discounts_line_ids = fields.One2many('agreement.discount', 'agreement_id', string='Discounts', copy=True,
                                         auto_join=True, track_visibility="onchange")
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', track_visibility="onchange")
    maintences_line_ids = fields.One2many('helpdesk.ticket', 'agreement_line_ids', string='Mantenciones', track_visibility="onchange")
    incidence_line_ids = fields.One2many('helpdesk.ticket', 'agreement_line_ids', string='Incidencias', track_visibility="onchange")
    vali_price_inst = fields.Boolean('Excepción Precio inst', default=False, track_visibility="onchange")
    vali_price_men = fields.Boolean('Excepción Precio men', default=False, track_visibility="onchange")
    admin_line_id = fields.Many2one('res.users', string='Administrador de Linea Maihue', track_visibility="onchange")
    log_admin_ids = fields.One2many(
        "log.admin.line", "agreement_line_id", string="Log admin de Contrato", copy=False, track_visibility="onchange")
    admin_id = fields.Many2one(related="agreement_id.admin_id", string='Administrador de Contrato')
    stage_id = fields.Many2one(related="agreement_id.stage_id", string='Estado de Contrato')
    instalation_btn = fields.Boolean(string='instalacion boton', track_visibility="onchange")
    fecha_agendada = fields.Date('Fecha Inicio Agendada')
    def_btn = fields.Boolean(string='Excepción instalación definitiva', track_visibility="onchange")
    ticket_btn = fields.Boolean(string='Solicitud de Baja Activa', track_visibility="onchange")
    activado_btn = fields.Boolean(string='Si estuvo activado o no', track_visibility="onchange")
    prueba_btn = fields.Boolean(string='Si hubo prueba o no', track_visibility="onchange")
    motivo_id = fields.Many2one('motivo.cancel', 'Motivo', readonly=False)
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

    @api.onchange('test_day', 'start_date')
    def _onchange_num_dias(self):
        if self.start_date and self.test_day:
            self.fecha_cobro = self.start_date + relativedelta(days=int(self.test_day.code))

    @api.onchange('agreement_line_keys')
    def onchange_agreement_line_keys(self):
        if self.agreement_line_keys:
            self.agreement_line_keys.current_agreement_line_id = self._origin.id
            self.agreement_line_keys.onchange_business_unit()

    @api.onchange('pass_line_rel')
    def _onchange_pass_line_rel(self):
        if self.pass_line_rel:
            self.pass_motivo_rel = self.pass_line_rel.reason_dis
            self.pass_description_rel = self.pass_line_rel.description_dis

    # @api.onchange('product_id', 'partner_contact_id', 'zona_comercial', 'product_principal')
    # def _onchange_partner_contact_id(self):
    #     if self.partner_contact_id:
    #         zona = []
    #         sector = []
    #         zona_id = self.env['comuna.comercial'].search([('commune', '=', self.comuna_id.id)]).zona_id
    #         comuna_man = self.env['comuna.mantencion'].search([('commune', '=', self.comuna_id.id)])
    #         sector_man = self.env['sector.mantencion'].search([('comuna_id', '=', comuna_man.id)])
    #         zona_template = ''
    #         res = {}
    #         if self.agreement_id.template_agreement_id.line_ids:
    #             zona_template = self.agreement_id.template_agreement_id.zona_domain
    #         if zona_template:
    #             if zona_id in zona_template:
    #                 zona = zona_id.ids
    #                 # self.zona_comercial = zona_id
    #         else:
    #             if zona_id:
    #             # self.zona_comercial = zona_id
    #                 zona = zona_id.ids
    #         # if sector_man:
    #         # self.zona_mantencion = sector_man
    #         if sector_man:
    #             sector = sector_man.ids
    #         res['domain'] = {
    #             'zona_comercial': [('id', 'in', zona)],
    #             'zona_mantencion': [('id', 'in', sector)]}
    #         if self.zona_comercial:
    #             if self.zona_comercial.id not in zona:
    #                 self.zona_comercial = ''
    #         if self.zona_mantencion:
    #             if self.zona_mantencion.id not in comuna_man.ids:
    #                 self.zona_mantencion = ''
    #         return res

    @api.onchange('product_id', 'partner_contact_id', 'zona_comercial', 'product_principal')
    def _onchange_product_id(self):
        # self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id.id
        today = datetime.now().date()
        zona = []
        sector = []
        zona_id = self.env['comuna.comercial'].search([('commune', '=', self.comuna_id.id)]).zona_id
        comuna_man = self.env['comuna.mantencion'].search([('commune', '=', self.comuna_id.id)])
        sector_man = self.env['sector.mantencion'].search([('comuna_id', '=', comuna_man.id)])
        zona_template = ''
        res = {}
        if not self.is_template:
            principal_ids = self.env['product.related'].search(
                [('product_parent_id', '=', self.product_id.product_tmpl_id.id), ('is_principal', '=', True)])
            product_domain = []
            principal_domain = []
            if self.agreement_id.template_agreement_id.product_domain:
                product_domain = self.agreement_id.product_domain.ids
            if principal_ids:
                list_pd = []
                for pd in principal_ids:
                    list_pd.append(pd.product_id.id)
                principal_domain = list_pd
            else:
                self.product_principal = ''
                self.price_instalacion = ''
                self.price = ''
            if self.product_principal:
                if self.product_principal.id not in principal_domain:
                    self.product_principal = ''
        if self.partner_contact_id:
            #res = {}
            if self.agreement_id.template_agreement_id.zona_domain:
                zona_template = self.agreement_id.template_agreement_id.zona_domain
            if zona_template:
                if zona_id in zona_template:
                    zona = zona_id.ids
                    # self.zona_comercial = zona_id
            # else:
            #     if zona_id:
            #     # self.zona_comercial = zona_id
            #         zona = zona_id.ids
            # if sector_man:
            # self.zona_mantencion = sector_man
            if sector_man:
                sector = sector_man.ids
            # res['domain'] = {
            #     'zona_comercial': [('id', 'in', zona)],
            #     'zona_mantencion': [('id', 'in', sector)]}
            if self.zona_comercial:
                if self.zona_comercial.id not in zona:
                    self.zona_comercial = ''
                    zona = []
            else:
                self.price_instalacion = ''
                self.price = ''
            if self.zona_mantencion:
                if self.zona_mantencion.id not in comuna_man.ids:
                    self.zona_mantencion = ''
        if not self.is_template:
            # res['domain'] = {
            #     'zona_comercial': [('id', 'in', zona_domain)]
            # }
            if self.product_id and self.zona_comercial:
                pricelist_men = self.env['product.pricelist.item'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('pricelist_id', '=', self.agreement_id.pricelist_id.id),
                ('payment_method_p', 'in', self.agreement_id.payment_method.ids),
                ('payment_period_p', 'in', self.agreement_id.payment_period.ids),
                ('zone', 'in', self.zona_comercial.ids),
                ('type_partner', 'in', self.agreement_id.type_partner.ids),
                ('vigente', '=', 'V'),
                ('date_start', '<=', today),
                ('date_end', '>=', today),], limit=1)
                pricelist_inst = self.env['product.pricelist.item'].search([('product_tmpl_id', '=', self.agreement_id.template_agreement_id.product_instalation.product_tmpl_id.id),
                ('pricelist_id', '=', self.agreement_id.pricelist_id.id),
                ('payment_method_p', 'in', self.agreement_id.payment_method.ids),
                ('payment_period_p', 'in', self.agreement_id.payment_period.ids),
                ('zone', 'in', self.zona_comercial.ids),
                ('type_partner', 'in', self.agreement_id.type_partner.ids),
                ('vigente', '=', 'V'),
                ('date_start', '<=', today),
                ('date_end', '>=', today),], limit=1)
                if pricelist_men:
                    self.price = pricelist_men.fixed_price
                    self.currency_id_men = pricelist_men.currency_id_m.id
                else:
                    self.price = ''
                if pricelist_inst:
                    self.price_instalacion = pricelist_inst.fixed_price
                    self.currency_id_inst = pricelist_inst.currency_id_m.id
                else:
                    self.price_instalacion = ''
        res['domain'] = {
            #'product_id': [('id', 'in', product_domain)],
            'product_principal': [('id', 'in', principal_domain)
                                  ],
            'test_day': [('id', 'in', self.agreement_id.template_agreement_id.test_day_domain.ids)],
            'zona_comercial': [('id', 'in', zona)],
            'zona_mantencion': [('id', 'in', sector)],
        }
        return res

    def edit_ticket(self):
        for ticket in self.incidence_line_ids:
            ticket.write({
                'name': 'Instalación ' + self.product_id.name,
                'partner_id': self.agreement_id.partner_id.id,
                'partner_email': self.agreement_id.partner_id.email,
            })
            for orden_s in ticket.service_order_ids:
                orden_s.write({
                    'name': 'Instalación ' + self.product_id.name,
                    'partner_id': self.agreement_id.partner_id.id,
                    'agreement_id': self.agreement_id.id,
                    'agreement_line_id': self.id,
                    'admin_line_id': self.admin_line_id.id,
                })
                orden_s.product_line.unlink()
                for x in self.product_id.product_related_ids:
                    if x.is_principal:
                        if x.product_id != self.product_principal:
                            continue
                    order_lineM_l = self.env['project.task.product'].create({
                        'product_id': x.product_id.id,
                        'description': x.name,
                        'planned_qty': x.qty,
                        'product_uom': x.product_id.uom_id.id,
                        'time_spent': x.time_spent,
                        'task_id': orden_s.id,
                        'is_principal': x.is_principal,
                    })
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'snailmail_invalid_address', {
                    'title': _("Reestructuracion de Ticket"),
                    'message': _("El ticket se actualizo correctamente en el sistema"),
                })
        #en_vali = False

    def agree_pend_agendar(self):
        self.write({'state': 'pen'})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 2})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5, "prueba_ganada": 6, "en_vali": 7,
            #                   "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_revisado(self):
        revisado = True
        if self.agreement_id.stage_id.id in [5,6,7]:
            self.write({'state': 'revisado', 'revisado_contract': True})
            if len(self.agreement_id.line_ids) == 1:
                # self.agreement_id.write({'stage_id': 6})
                revisado = True
            else:
                lines_ids = []
                custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                                  "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                                  "sol_baja": 14, "proceso": 15, "no_vigente": 16}
                # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
                #                      "prueba_ganada": 6, "en_vali": 7,
                #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
                for line in self.agreement_id.line_ids:
                    lines_ids.append([line.id, line.state])
                lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
                # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
                for item in lista:
                    if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                        if item[1] == 'act':
                            self.agreement_id.write({'stage_id': 7})
                        if item[1] == 'revisado':
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            else:
                                self.agreement_id.write({'stage_id': 5})
                        if item[1] == 'vali':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'win':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'prueba':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 20})
                        if item[1] == 'pre':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 17})
                        if item[1] == 'pen':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 2})
            return True #{
            #     'type': 'ir.actions.client',
            #     'tag': 'reload',
            # }
        else:
            raise UserError(_(
                'Disculpe, Es necesario que el contrato este en estado Validacion Adm, para poder dar por revisado la linea de contrato'))

    def agree_cancela(self):
        # for line in self.agreement_id.line_ids:
        self.write({'state': 'sol_can'})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 10})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_pro_can(self):
        if not self.motivo_id:
            raise UserError(_(
                'Disculpe, Es necesario señalar un motivo de cancelacion para poder avanzar'))
        # for line in self.agreement_id.line_ids:
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 11})
        self.write({'state': 'pro_can'})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # def agree_incidencia(self):
    #     self.write({'state': 'inci'})

    def agree_admin(self):
        vali = True
        if not self.agreement_id.act_sfirma:
            if self.agreement_id.state_card_number != 'active':
                raise UserError(_('Lo Siento, El contrato no posee el metodo de pago activo'))
            if self.agreement_id.status_signature != 'signed':
                raise UserError(_('Lo Siento, El contrato aun no esta firmado'))
        if not self.insta_prueba_id:
            raise UserError(_('Lo Siento, El Campo Instalador es requerido'))
        if not self.start_date:
            raise UserError(_('Lo Siento, El Campo Fecha Inicio de Prueba es requerido'))
        if self.state_inst != 'reali':
            raise UserError(_('Lo Siento, El Estado Prueba de instalación aun no ha sido Realizado '))
        if not self.def_btn:
            if not self.insta_def_id:
                raise UserError(_('Lo Siento, La linea de contrato debe tener un Instalador Final'))
            if not self.date_def:
                raise UserError(_('Lo Siento, La Fecha de instalación final es Requerida'))
            if self.state_def != 'reali':
                raise UserError(_('Lo Siento, El Estado de instalación final aun no ha sido Realizada'))
        self.write({'state': 'vali', 'vali': True})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 5})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                            self.agreement_id.write({'stage_id': 2})

    def agree_agendada(self):
        if not self.fecha_agendada:
            raise UserError(_('Lo Siento, El Campo Fecha Agendada es requerido'))
        self.write({'state': 'pre', 'state_inst': 'agen', 'state_def': 'agen'})
        if len(self.agreement_id.line_ids) == 1:
            state_id = self.env['agreement.stage'].search([('name', '=', 'AGENDADA')], limit=1)
            if state_id:
                self.agreement_id.write({'stage_id': state_id.id})
        else:
            lines_ids = []
            agreement_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {1: 1, 2: 2, 17: 3, 20: 4, 18: 5,
            #                      5: 6, 6: 7,
            #                      7: 8, 8: 9, 9: 10}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # for record in self.agreement_id:
            #     agreement_ids.append([record.id, record.stage_id.id])
            # status_agreement = sorted(agreement_ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_arrepentido(self):
        if self.activado_btn == True:
            if len(self.agreement_id.line_ids) == 1:
                self.agreement_id.write({'stage_id': 8})
            self.write({'state': 'act', 'reason_dis': '', 'description_dis': '', 'date_end_contract': '', 'ticket_btn': False})
        else:
            self.write(
                {'state': 'vali', 'reason_dis': '', 'description_dis': '', 'date_end_contract': '',
                 'ticket_btn': False})
            if len(self.agreement_id.line_ids) == 1:
                self.agreement_id.write({'stage_id': 5})
            else:
                lines_ids = []
                custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                                  "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                                  "sol_baja": 14, "proceso": 15, "no_vigente": 16}
                # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
                #                      "prueba_ganada": 6, "en_vali": 7,
                #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
                for line in self.agreement_id.line_ids:
                    lines_ids.append([line.id, line.state])
                lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
                # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
                for item in lista:
                    if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                        if item[1] == 'act':
                            self.agreement_id.write({'stage_id': 7})
                        if item[1] == 'revisado':
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            else:
                                self.agreement_id.write({'stage_id': 5})
                        if item[1] == 'vali':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'win':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'prueba':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                                self.agreement_id.write({'stage_id': 20})
                        if item[1] == 'pre':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                                self.agreement_id.write({'stage_id': 17})
                        if item[1] == 'pen':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            if self.agreement_id.revisado_contract != True and self.agreement_id.vali != True:
                                self.agreement_id.write({'stage_id': 2})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_curso(self):
        if not self.agreement_id.prueba_aprob:
            if self.agreement_id.state_card_number != 'active':
                raise UserError(_('Lo Siento, El contrato no posee el metodo de pago activo'))
            if self.agreement_id.status_signature != 'signed':
                raise UserError(_('Lo Siento, El contrato aun no esta firmado'))
        if not self.agreement_line_keys:
            raise UserError(_('Lo Siento, La linea de contrato debe tener un numero de serie'))
        if not self.insta_prueba_id:
            raise UserError(_('Lo Siento, El Campo Instalador es requerido'))
        if not self.start_date:
            raise UserError(_('Lo Siento, El Campo Fecha Inicio de Prueba es requerido'))
        if self.state_inst != 'reali':
            raise UserError(_('Lo Siento, El Estado Prueba de instalación aun no ha sido Realizado '))
        self.write({'state': 'prueba', 'prueba_btn': True})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 20})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
                    if self.agreement_id.activado_btn:
                        if len(self.agreement_id.line_ids) != 1:
                            self.agreement_id.write({'stage_id': 7})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_ganada(self):
        if self.state_inst != 'reali':
            raise UserError(_('Lo Siento, El Estado Prueba de instalación aun no ha sido Realizado '))
        #self.agreement_id.write({'stage_id': 18})
        self.write({'state': 'win'})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 18})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
                    if self.agreement_id.activado_btn:
                        if len(self.agreement_id.line_ids) != 1:
                            self.agreement_id.write({'stage_id': 7})
        #self.agreement_id.write({'stage_id': 18})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_fallida(self):
        self.write({'state': 'fallida'})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 19})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
                    if self.agreement_id.activado_btn:
                        if len(self.agreement_id.line_ids) != 1:
                            self.agreement_id.write({'stage_id': 7})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def agree_baja(self):
        self.write({'state': 'sol_baja'})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 14})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
                    if self.agreement_id.activado_btn:
                        if len(self.agreement_id.line_ids) != 1:
                            self.agreement_id.write({'stage_id': 7})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

        #self.agreement_id.write({'stage_id': 14})

    def agree_ticket(self):
        #Aqui debe crear un ticket para la esistalacion de la maquina
        self.write({'ticket_btn': True})

    def agree_baja_pro(self):
        todayI = datetime.now().date() #+ relativedelta(days=1)
        # existentes = self.env['sale.order'].search([('agreement_line_ids', '=', self.id), ('state', '!=', 'sale')])
        # if existentes:
        #     if len(existentes) > 1:
        #         for exi in existentes:
        #             exi.unlink()
        order_valsI = {
            'partner_id': self.agreement_id.partner_id.id,
            'opportunity_id': self.agreement_id.crm_lead_id.id,
            'agreement_type_id': self.agreement_id.agreement_type_id.id,
            'agreement_id': self.agreement_id.id,
            'date_order': datetime.now(),
            'validity_date': self.agreement_id.end_date,
            'user_id': self.agreement_id.crm_lead_id.user_id.id,
            'origin': self.agreement_id.crm_lead_id.name,
            'partner_dir_id': self.partner_contact_id.id,
            # 'partner_invoice_id': line.partner_invoice.id,
            'is_rental_order': True,
            'tipo_rental_order': 'baja',
            'agreement_id': self.agreement_id.id,
            'agreement_line_ids': self.id,
            'payment_period': self.agreement_id.payment_period.id,
            'payment_method': self.agreement_id.payment_method.id,
            'payment_term_id': self.agreement_id.payment_term_id.id,
            # 'inicio_fecha_alquiler': line.start_date,
            # 'fin_fecha_alquiler': line.start_date,
            # 'fecha_fact_prog': todayI,
            # 'fecha_estimada': todayI,
            # 'periodo_mes': str(month) + '/' + str(line.start_date.year),
            'state': 'sale',  # 'draft',
            'currency_id': self.agreement_id.currency_id.id,
            'pricelist_id': self.agreement_id.pricelist_id.id,
            # 'reference_ids': [self.agreement_id.reference_ids.id],
            # 'agreement_currency_id': self.currency_id_inst.id,
        }
        orderI = self.env['sale.order'].create(order_valsI)
        name_orderI = str(orderI.name) + ' Contrato: ' + str(self.name) + ' - ' + str(todayI)
        orderI.write({'name': name_orderI})
        # precio_inst = float(line.price_instalacion) + 0.0001  # round(line.price_instalacion) + 0.0001
        order_lineI = {
            'order_id': orderI.id,
            'product_id': self.agreement_id.template_agreement_id.product_desistalation.id,
            'name': 'RENTAL DE BAJA',
            # str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
            # line.currency_id_inst.name) + '' + str(precio_inst) + '+iva',
            'price_unit': 0,  # "{:0.4f}".format(line.price_instalacion),
            'tax_id': [self.agreement_id.tax_id.id],
        }
        order_lineI = self.env['sale.order.line'].create(order_lineI)
        self.write({'state': 'proceso'})
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 15})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

        #self.agreement_id.write({'stage_id': 15})

    def agree_reagendar(self):
        if len(self.agreement_id.line_ids) == 1:
            self.agreement_id.write({'stage_id': 2})
            self.write({'state': 'reage'})
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
                    if self.agreement_id.activado_btn:
                        if len(self.agreement_id.line_ids) != 1:
                            self.agreement_id.write({'stage_id': 7})

    def agree_no_vigente(self):
        if not self.desinst_id:
            raise UserError(_('Lo Siento, El Campo Desinstalador es requerido'))
        if not self.date_desinst:
            raise UserError(_('Lo Siento, El Campo Fecha de Desinstalación es requerido'))
        if not self.date_end_contract:
            raise UserError(_('Lo Siento, El Campo Fecha de Baja es requerido'))
        if self.state_desinst != 'reali':
            raise UserError(_('Lo Siento, El Estado de Desinstalación aun no ha sido Realizado '))
        self.write({'state': 'no_vigente'})
        if self.fut_line_rel:
            if self.fut_line_rel.state == 'act':
                existentes = self.env['sale.order'].search([('agreement_line_ids', '=', self.id), ('state', '!=', 'sale'), ('tipo_rental_order', '!=', 'baja')])
                if existentes:
                    if len(existentes) > 1:
                        for exi in existentes:
                            exi.unlink()
            else:
                raise UserError(_('Lo Siento, El estado de la linea futura debe ser Activo'))
        else:
            existentes = self.env['sale.order'].search([('agreement_line_ids', '=', self.id), ('state', '!=', 'sale'), ('tipo_rental_order', '!=', 'baja')])
            if existentes:
                if len(existentes) > 1:
                    for exi in existentes:
                        exi.unlink()
        #     self.line_rel.write({'pass_line_rel': self.id, 'pass_motivo_rel': self.motivo_rel, 'pass_description_rel': self.description_rel})
        self.write({'state': 'no_vigente'})
        #self.agreement_id.write({'stage_id': 16})

    def agree_cerrar(self):
        # Falta si existe un ticket agendado (instalacion) debe estar cancelado o finalizado para esta linea debe cancelarse
        if self.state_inst == 'reali':
            if not self.desinst_id:
                raise UserError(_('Para poder cancelar una linea de contrato debe tener un Desinstalador'))
            if not self.date_desinst:
                raise UserError(_('Para poder cancelar una linea de contrato debe tener una Fecha de Desinstalación'))
            if self.state_desinst != 'reali':
                raise UserError(_('Para poder cancelar una linea de contrato debe tener estar en Estado de desinstalación Realizada'))
        self.write({'state': 'cancelado'})
        if len(self.agreement_id.line_ids) == 1:
            #self.agreement_id.write({'stage_id': 12})
            jamie = 1
        else:
            lines_ids = []
            custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                              "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                              "sol_baja": 14, "proceso": 15, "no_vigente": 16}
            # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
            #                      "prueba_ganada": 6, "en_vali": 7,
            #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
            for line in self.agreement_id.line_ids:
                lines_ids.append([line.id, line.state])
            lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
            # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
            for item in lista:
                if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                    if item[1] == 'act':
                        self.agreement_id.write({'stage_id': 7})
                    if item[1] == 'revisado':
                        if self.agreement_id.revisado_contract == True:
                            self.agreement_id.write({'stage_id': 6})
                        else:
                            self.agreement_id.write({'stage_id': 5})
                    if item[1] == 'vali':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'win':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 18})
                    if item[1] == 'prueba':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 20})
                    if item[1] == 'pre':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 17})
                    if item[1] == 'pen':
                        if self.agreement_id.vali == True:
                            self.agreement_id.write({'stage_id': 5})
                        else:
                            self.agreement_id.write({'stage_id': 2})
                    if self.agreement_id.activado_btn:
                        if len(self.agreement_id.line_ids) != 1:
                            self.agreement_id.write({'stage_id': 7})

    def agree_cancel(self):
        if not self.instalation_btn:
            self.write({'state': 'draft'})
            if len(self.agreement_id.line_ids) == 1:
                self.agreement_id.write({'stage_id': 1})
            else:
                lines_ids = []
                custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                                  "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                                  "sol_baja": 14, "proceso": 15, "no_vigente": 16}
                # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
                #                      "prueba_ganada": 6, "en_vali": 7,
                #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
                for line in self.agreement_id.line_ids:
                    lines_ids.append([line.id, line.state])
                lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
                # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
                for item in lista:
                    if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                        if item[1] == 'act':
                            self.agreement_id.write({'stage_id': 7})
                        if item[1] == 'revisado':
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            else:
                                self.agreement_id.write({'stage_id': 5})
                        if item[1] == 'vali':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'win':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'prueba':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 20})
                        if item[1] == 'pre':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 17})
                        if item[1] == 'pen':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 2})
                        if self.agreement_id.activado_btn:
                            if len(self.agreement_id.line_ids) != 1:
                                self.agreement_id.write({'stage_id': 7})

            return True
        if not self.prueba_btn:
            self.write({'state': 'pen'})
            if len(self.agreement_id.line_ids) == 1:
                self.agreement_id.write({'stage_id': 2})
            else:
                lines_ids = []
                custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                                  "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                                  "sol_baja": 14, "proceso": 15, "no_vigente": 16}
                # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
                #                      "prueba_ganada": 6, "en_vali": 7,
                #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
                for line in self.agreement_id.line_ids:
                    lines_ids.append([line.id, line.state])
                lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
                # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
                for item in lista:
                    if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                        if item[1] == 'act':
                            self.agreement_id.write({'stage_id': 7})
                        if item[1] == 'revisado':
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            else:
                                self.agreement_id.write({'stage_id': 5})
                        if item[1] == 'vali':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'win':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'prueba':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 20})
                        if item[1] == 'pre':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 17})
                        if item[1] == 'pen':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 2})

            return True
        if self.prueba_btn:
            if len(self.agreement_id.line_ids) == 1:
                self.agreement_id.write({'stage_id': 19})
                self.write({'state': 'fallida'})
            else:
                self.write({'state': 'prueba'})
                lines_ids = []
                custom_indices = {"draft": 1, "pen": 2, "reage": 3, "pre": 4, "prueba": 5, "fallida": 6, "win": 7,
                                  "vali": 8, "revisado": 9, "act": 10, "sol_can": 11, "pro_can": 12, "cancelado": 13,
                                  "sol_baja": 14, "proceso": 15, "no_vigente": 16}
                # agreement_indices = {"borrador": 1, "pre_prueba": 2, "agendada": 3, "en_prueba": 4, "prueba": 5,
                #                      "prueba_ganada": 6, "en_vali": 7,
                #                      "revisado": 8, "act_parcial": 9, "act_completo": 10, "vigente": 11}
                for line in self.agreement_id.line_ids:
                    lines_ids.append([line.id, line.state])
                lista = sorted(lines_ids, key=lambda x: custom_indices[x[1]])
                # status_agreement = sorted(self.agreement_id.ids, key=lambda x: agreement_indices[x[1]])
                for item in lista:
                    if item[1] in ['pen', 'pre', 'prueba', 'win', 'vali', 'revisado', 'act']:
                        if item[1] == 'act':
                            self.agreement_id.write({'stage_id': 7})
                        if item[1] == 'revisado':
                            if self.agreement_id.revisado_contract == True:
                                self.agreement_id.write({'stage_id': 6})
                            else:
                                self.agreement_id.write({'stage_id': 5})
                        if item[1] == 'vali':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'win':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 18})
                        if item[1] == 'prueba':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 20})
                        if item[1] == 'pre':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 17})
                        if item[1] == 'pen':
                            if self.agreement_id.vali == True:
                                self.agreement_id.write({'stage_id': 5})
                            else:
                                self.agreement_id.write({'stage_id': 2})

            return True

    @api.onchange("test_day")
    def _onchange_test_day(self):
        res = {}
        res['domain'] = {
            'test_day': [('id', 'in', self.agreement_id.template_agreement_id.test_day_domain.ids)]}
        return res

    def unlink(self):
        user = self.env['res.users'].browse(self.env.uid)
        raise UserError(_('Sorry, you are not authorized to delete contract lines'))

    #Comienza desarrollo de Rentals

    def calcularProrrateo(self, rental):

        dias_mes = ((self.siguienteMes(rental["fecha_estimada"], 1) - timedelta(days=1)) - date(rental["fecha_estimada"].year,
                                                                                        rental["fecha_estimada"].month,
                                                                                        1)).days + 1
        dias_a_cobrar = dias_mes - rental["fecha_estimada"].day + 1
        #precio = round((self.price / dias_mes) * dias_a_cobrar)
        precio = float((self.price / dias_mes) * dias_a_cobrar)
        return precio

    def crearInstalacion(self, rental, contrato):
        #rental_creado = {"nombre": rental["nombre"], "valor": rental["valor"]}
        rental_creado = {  # 'name': self.name,
            'partner_id': self.partner_id.id,
            'opportunity_id': self.agreement_id.crm_lead_id.id,
            'user_id': self.agreement_id.crm_lead_id.user_id.id,
            'origin': self.agreement_id.crm_lead_id.name,
            'is_rental_order': True,
            'agreement_id': self.agreement_id.id,
            'agreement_line_ids': self.id,
            'partner_dir_id': self.partner_contact_id.id,
            'payment_period': self.agreement_id.payment_period.id,
            'payment_method': self.agreement_id.payment_method.id,
            'state': 'draft',  # 'sale',
            'pricelist_id': self.agreement_id.pricelist_id.id,
            'payment_term_id': self.agreement_id.payment_term_id.id,
            'tipo_rental_order': 'instalacion',
            'currency_id': self.agreement_id.currency_id.id,
            'reference_ids': [self.agreement_id.reference_ids.id],
            # 'cost_center': self.cost_center.id,
        }  # {"nombre": rentals["nombre"], "valor": rentals["valor"]}
        orden_line = []
        if contrato["fecha_estimada"] < date.today():
            rental_creado["fecha_fact_prog"] = date.today() + timedelta(days=1)
            rental_creado["fecha_estimada"] = contrato["fecha_estimada"]
        else:
            rental_creado["fecha_fact_prog"] = contrato["fecha_estimada"]
            rental_creado["fecha_estimada"] = contrato["fecha_estimada"]
        rental_creado["inicio_fecha_alquiler"] = rental_creado["fecha_estimada"]
        rental_creado["fin_fecha_alquiler"] = rental_creado["fecha_estimada"]
        rental_creado["periodo_mes"] = str(MONTHS[rental_creado["fecha_estimada"].month - 1]) + '/' + str(rental_creado["fecha_estimada"].year)
        orden_line.append((0, 0, {
            "price_unit": "{:0.10f}".format(float(self.price_instalacion)),
            "tax_id": [(6, 0, self.agreement_id.tax_id.ids)],
            "product_id": self.product_id.id,
            "product_uom": self.product_id.uom_id.id,
            "name": str(self.product_id.name_key) + '/' + str(self.maintenance_id.name) + '/' + str(
                self.currency_id_inst.name) + '' + str(
                "{:0.4f}".format(float(self.price_instalacion + 0.0001))) + '+iva',
        }))
        rental_creado['order_line'] = orden_line

        return rental_creado

    def siguienteMes(self, fecha, meses_a_agregar):

        for _ in range(meses_a_agregar):
            if (fecha.month + 1) < 13:
                siguiente = date(year=fecha.year, month=fecha.month + 1, day=1)
            else:
                siguiente = date(year=fecha.year + 1, month=1, day=1)

        return siguiente

    def adicionarMesesFuturos(self, rentals_creados, ultimo_rental_creado, rental, contrato, rentals_pasados):
        meses_futuros = 36
        contrato = copy.deepcopy(ultimo_rental_creado)
        mes_adicional = 1 if self.agreement_id.payment_period.code != "M" and int(contrato["fecha_estimada"].day) >= 4 else 0
        descuento = self.agreement_id.payment_period.descuento # frecuencias[contrato["frecuencia"]]["descuento"]
        contrato["fecha_estimada"] = self.siguienteMes(ultimo_rental_creado["fecha_estimada"], 1)
        contrato["fecha_fact_prog"] = contrato["fecha_estimada"]
        contrato["frecuencia"] = self.agreement_id.payment_period.siguiente_periodicidad#frecuencias[contrato["frecuencia"]]["siguiente_periodicidad"]
        self.agreement_id.payment_period = self.agreement_id.payment_period.siguiente_periodicidad#frecuencias[contrato["frecuencia"]]["siguiente_periodicidad"]

        meses_futuros_calculados = meses_futuros + rentals_pasados + (
            descuento if descuento is not None else 0) + mes_adicional

        while ((len(rentals_creados) + mes_adicional) <= meses_futuros_calculados):
            rentals_creados = rentals_creados + self.crearMensualidad(rental, contrato, False, False, False)
            contrato["fecha_estimada"] = self.siguienteMes(rentals_creados[-1]["fecha_estimada"], 1)
            contrato["fecha_fact_prog"] = contrato["fecha_estimada"]

        return rentals_creados

    def aplicarDecuentos(self, rentalsCreados, descuentos):
        rentals_descuentos = []
        for indice in range(len(rentalsCreados), len(rentalsCreados) - descuentos, -1):
            rental_descuento = copy.deepcopy(rentalsCreados[indice - 1])
            rental_descuento['tipo_rental_order'] = 'descuento'
            rental_descuento['order_line'][0][2]["price_unit"] = float(rental_descuento['order_line'][0][2]["price_unit"]) * -1
            rentals_descuentos.append(rental_descuento)

        return rentalsCreados + rentals_descuentos

    def crearMensualidad(self, rental, contrato, aplicar_descuentos=True, aplicar_prorrateo=True, aplicar_meses_futuros=True):
        rentals_creados = []
        precio = self.price
        ciclos = self.agreement_id.payment_period.periodicidad # frecuencias[contrato["frecuencia"]]["periodicidad"]
        descuentos = self.agreement_id.payment_period.descuento # frecuencias[contrato["frecuencia"]]["descuento"]
        fecha_cobro = contrato["fecha_estimada"]
        fecha_programada = None
        rentals_pasados = len([dt for dt in rrule(MONTHLY, dtstart=date(fecha_cobro.year, fecha_cobro.month, 1),
                                                  until=date(date.today().year, date.today().month, 1))])
        rentals_pasados = rentals_pasados if rentals_pasados > 0 else 0
        ciclos = ciclos + 1 if self.agreement_id.payment_period.code != "M" and fecha_cobro.day >= 4 else ciclos

        for ciclo in range(ciclos):
            # print(f"{ciclo+1},  {ciclos}")

            #rental_creado = {"nombre": rental["nombre"], "valor": rental["valor"]}
            rental_creado = {  # 'name': self.name,
                'partner_id': self.partner_id.id,
                'opportunity_id': self.agreement_id.crm_lead_id.id,
                'user_id': self.agreement_id.crm_lead_id.user_id.id,
                'origin': self.agreement_id.crm_lead_id.name,
                'is_rental_order': True,
                'agreement_id': self.agreement_id.id,
                'agreement_line_ids': self.id,
                'partner_dir_id': self.partner_contact_id.id,
                'payment_period': self.agreement_id.payment_period.id,
                'payment_method': self.agreement_id.payment_method.id,
                'state': 'draft',  # 'sale',
                'pricelist_id': self.agreement_id.pricelist_id.id,
                'payment_term_id': self.agreement_id.payment_term_id.id,
                'tipo_rental_order': 'mensualidad',
                'currency_id': self.agreement_id.currency_id.id,
                'reference_ids': [self.agreement_id.reference_ids.id],
                # 'cost_center': self.cost_center.id,
            }  # {"nombre": rentals["nombre"], "valor": rentals["valor"]}

            if ciclo == 0:
                if contrato["fecha_estimada"] < date.today():
                    rental_creado["fecha_fact_prog"] = date.today() + timedelta(days=1)
                    rental_creado["fecha_estimada"] = fecha_cobro
                    fecha_programada = rental_creado["fecha_fact_prog"]
                else:
                    rental_creado["fecha_fact_prog"] = fecha_cobro
                    rental_creado["fecha_estimada"] = fecha_cobro
                    fecha_programada = fecha_cobro
                if aplicar_prorrateo:
                    precio = self.calcularProrrateo(rental_creado)

            elif ((ciclo) % ciclos) == 0:
                fecha_programada = self.siguienteMes(fecha_programada, ciclos)
                if fecha_programada < date.today():
                    rental_creado["fecha_fact_prog"] = date.today() + timedelta(days=1)
                    rental_creado["fecha_estimada"] = fecha_cobro
                else:
                    rental_creado["fecha_fact_prog"] = fecha_programada
                    rental_creado["fecha_estimada"] = fecha_cobro
            else:
                rental_creado["fecha_fact_prog"] = fecha_programada
                rental_creado["fecha_estimada"] = fecha_cobro
            orden_line = []
            orden_line.append((0, 0, {
                "price_unit": "{:0.10f}".format(float(precio)),
                "tax_id": [(6, 0, self.agreement_id.tax_id.ids)],
                "product_id": self.product_id.id,
                "product_uom": self.product_id.uom_id.id,
                "name": str(self.product_id.name_key) + '/' + str(self.maintenance_id.name) + '/' + str(
                    self.currency_id_men.name) + '' + str(
                    "{:0.4f}".format(float(precio + 0.0001))) + '+iva',
            }))
            rental_creado['order_line'] = orden_line
            # rental_creado["fin_fecha_alquiler"] = str(rental_creado["fecha_estimada"].year) + '-' + str(
            #     rental_creado["fecha_estimada"].month).zfill(
            #     2) + '-' + str(
            #     calendar.monthrange(rental_creado["fecha_fact_prog"].year, rental_creado["fecha_fact_prog"].month)[1])
            rentals_creados.append(rental_creado)
            fecha_cobro = self.siguienteMes(fecha_cobro, 1)

        if aplicar_descuentos and descuentos:
            rentals_creados = self.aplicarDecuentos(rentals_creados, descuentos)

        if aplicar_meses_futuros:
            rentals_creados = self.adicionarMesesFuturos(rentals_creados, rental_creado, rental, contrato, rentals_pasados)
        return rentals_creados

    def agree_maintenance(self):
        rentals = []
        contrato = {
            #"name": "luis Meza",
            "fecha_estimada": self.fecha_cobro, #date(2024, 2, 7),
            "fecha_programada": self.fecha_cobro, #date(2024, 2, 7),
            "frecuencia": self.agreement_id.payment_period,
            "rentals": [
                {"valor": self.price, "nombre": self.product_id.name},
            ]
        }
        for rental in contrato["rentals"]:
            rentals.append(self.crearInstalacion(rental, contrato))
            rentals = rentals + self.crearMensualidad(rental, contrato)
            #rentals = self.crearMensualidad(rentals, contrato)
            if rentals:
                #raise UserError(_(rentals))
                self.env['sale.order'].create(rentals)
        # Mantenciones
        # for line in self:
        #     project_id = self.env['project.project'].search([('name', '=', 'Servicio externo')], limit=1).id
        #     if line.maintenance_id:
        #         todayM = line.start_date# datetime.now().date()
        #         period_m = datetime.now().date()
        #         #period_m = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + '01'
        #         #period_m = datetime.strptime(period_date, '%Y-%m-%d')
        #         meses = 0
        #         mesesM = 0
        #         numeracionM = 1
        #         mj2 = []
        #         num = 0
        #         for j in line.maintenance_id.maintenance_m_line:
        #             if j.number not in mj2:
        #                 mj2.append(j.number)
        #         while (mesesM < 43):
        #             name_list = []
        #             mj2 = sorted(mj2, reverse=False)
        #             for i in mj2:
        #                 if datetime.strptime(str(period_m)[0:10], '%Y-%m-%d').date() > todayM:
        #                     mesesM = mesesM
        #                 else:
        #                     mesesM = mesesM + int(mj2[0])
        #                 meses = meses + int(mj2[0])
        #                 if mesesM >= 36:
        #                     break
        #                 todayM = todayM + relativedelta(months=int(mj2[0]))
        #                 num = i
        #                 # /// new
        #                 categ_inst = False
        #                 exist_inst = self.env['project.task.template'].search([('mantention', '=', True)], limit=1,
        #                                                                       order='id')
        #                 if not exist_inst:
        #                     raise UserError(_(
        #                         'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede pasar a preprueba sin tener una plantilla destinada para la mantención, \n \n Por favor comuniquese con un Administrador'))
        #                 categ_inst = self.env['helpdesk.tag'].search([('mantention', '=', True)], limit=1,
        #                                                              order='id')
        #                 if not categ_inst:
        #                     raise UserError(_(
        #                         'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede pasar a preprueba sin tener una categoria destinada para la mantención, \n \n Por favor comuniquese con un Administrador'))
        #                 categoria = self.env['categoria.maihue.template'].search(
        #                     [('project_template_id', '=', exist_inst.id)], limit=1,
        #                     order='id')
        #                 ticket_man = self.env['helpdesk.ticket'].with_context(instalation=True).create({
        #                     'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
        #                     'partner_id': self.agreement_id.partner_id.id,
        #                     'assign_date': todayM,
        #                     'fecha_registro_ticket': todayM,
        #                     'agreement_id': self.agreement_id.id,
        #                     'ticket_type_id': categoria.categoria_id.ticket_type_id.id,
        #                     'categoria_maihue_id': categ_inst.id,
        #                     'ticket_type_id': 1,
        #                     'agreement_line_ids': line.id,
        #                     'partner_email': self.agreement_id.partner_id.email,
        #                     #'user_id': line.mantenedor or False,
        #                 })
        #                 invite = self.env['survey.invite']
        #                 url_invite = werkzeug.urls.url_join(exist_inst.survey_id.get_base_url(),
        #                                                     exist_inst.survey_id.get_start_url()) if invite.survey_id else False
        #                 order_lineM = self.env['project.task'].create({
        #                     'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
        #                     'partner_id': self.agreement_id.partner_id.id,
        #                     'helpdesk_ticket_id': ticket_man.id,
        #                     # 'stage_id': 4,
        #                     'fsm_done': False,
        #                     'project_id': project_id,
        #                     'agreement_id': line.agreement_id.id,
        #                     'agreement_line_id': line.id,
        #                     'formulario': url_invite,
        #                     'survey_id': exist_inst.survey_id.id,
        #                     'type_transfer_equipment': exist_inst.type_transfer_equipment,
        #                     'l10n_cl_delivery_guide_reason': exist_inst.l10n_cl_delivery_guide_reason,
        #                     'task_template_id': exist_inst.id,
        #                     'admin_line_id': line.admin_line_id.id,
        #                     'description': self.general_msj,
        #                 })
        #                 for x in line.maintenance_id.maintenance_m_line:
        #                     if x.number <= num:
        #                         if x.type not in name_list:
        #                             name_list.append(x.type)
        #                         order_lineM_l = self.env['project.task.product'].create({
        #                             'product_id': x.product_id.id,
        #                             'description': x.product_id.name,
        #                             'planned_qty': x.quantity,
        #                             'product_uom': x.product_id.uom_id.id,
        #                             'time_spent': x.time_spent,
        #                             'task_id': order_lineM.id,
        #                         })
        #                 name_new = ''
        #                 for n in name_list:
        #                     name_new = name_new + ' ' + n
        #                 ticket_man.write({'name': ticket_man.name + ' ' + name_new})
        #                 order_lineM.write({'name': order_lineM.name + ' ' + name_new})
        #                 numeracionM = numeracionM + 1
        #     if len(self.agreement_id.line_ids) == 1:
        #         self.agreement_id.write({'stage_id': 8, 'activado_btn': True})
        #         self.write({'state': 'act', 'activado_btn': True})
        #     else:
        #         self.agreement_id.write({'stage_id': 7, 'activado_btn': True})
        #         self.write({'state': 'act', 'activado_btn': True})
        #
        # orden_compra = self.agreement_id.orden_compra()
        #
        # state_line = True
        # for line in self.agreement_id.line_ids:
        #     if line.state not in ['act', 'cancelado', 'no_vigente']:
        #         state_line = False
        # line.write({'state': 'act', 'activado_btn': True})
        # if state_line:
        #     state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO COMPLETO')], limit=1)
        #     self.agreement_id.write({'stage_id': state_id})
        # else:
        #     state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO PARCIAL')], limit=1)
        #     self.agreement_id.write({'stage_id': state_id})

        #return True
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # def agree_maintenance(self):
    #     if self.stage_id.id not in [6,7]: #revisado y activado parcial
    #         raise UserError(_(
    #             'Disculpe, Es necesario que el contrato este en estado Revisado, para poder activar la linea de contrato'))
    #     if self.not_activate:
    #         raise UserError(_('Lo Siento, No se puede activar una Linea de Contrato con el check de No permite Activación'))
    #     # if self.line_rel:
    #     #     self.line_rel.write({'state_rel': 'no_vi'})
    #     months = (
    #     "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
    #     "Diciembre")
    #     # instalacion
    #     for line in self:
    #         if int(line.price_instalacion) <= 0 and line.vali_price_inst == False:
    #             raise UserError(_('Lo Siento, No se puede activar un contrato con precio de instalacion cero'))
    #         fecha_activacion = datetime.now().date()
    #         todayI = datetime.now().date() + relativedelta(days=1)
    #         if fecha_activacion < line.fecha_cobro:
    #             todayI = line.fecha_cobro
    #         ultimo_de_mes = calendar.monthrange(line.start_date.year, line.start_date.month)
    #         fin_mes = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + str(ultimo_de_mes[1])
    #         month = months[line.start_date.month - 1]
    #         order_valsI = {
    #                     'partner_id': self.agreement_id.partner_id.id,
    #                     'opportunity_id': self.agreement_id.crm_lead_id.id,
    #                     'agreement_type_id': self.agreement_id.agreement_type_id.id,
    #                     'agreement_id': self.agreement_id.id,
    #                     'date_order': datetime.now(),
    #                     'validity_date': self.agreement_id.end_date,
    #                     'user_id': self.agreement_id.crm_lead_id.user_id.id,
    #                     'origin': self.agreement_id.crm_lead_id.name,
    #                     'partner_dir_id': line.partner_contact_id.id,
    #                     # 'partner_invoice_id': line.partner_invoice.id,
    #                     'is_rental_order': True,
    #                     'tipo_rental_order': 'instalacion',
    #                     'agreement_id': self.agreement_id.id,
    #                     'agreement_line_ids': line.id,
    #                     'payment_period': self.agreement_id.payment_period.id,
    #                     'payment_method': self.agreement_id.payment_method.id,
    #                     'payment_term_id': self.agreement_id.payment_term_id.id,
    #                     'inicio_fecha_alquiler': line.start_date,
    #                     'fin_fecha_alquiler': line.start_date,
    #                     'fecha_fact_prog': todayI,
    #                     'fecha_estimada': todayI,
    #                     'periodo_mes': str(month) + '/' + str(line.start_date.year),
    #                     'state': 'sale',  # 'draft',
    #                     'currency_id': self.agreement_id.currency_id.id,
    #                     'pricelist_id': line.pricelist_inst.id,
    #                     'reference_ids': [self.agreement_id.reference_ids.id],
    #                     'agreement_currency_id': line.currency_id_inst.id,
    #                 }
    #         orderI = self.env['sale.order'].create(order_valsI)
    #         name_orderI = str(orderI.name) + ' Contrato: ' + str(self.name) + ' - ' + str(todayI)
    #         orderI.write({'name': name_orderI})
    #         precio_inst = float(line.price_instalacion) + 0.0001 # round(line.price_instalacion) + 0.0001
    #         int_part, dec_part = str(line.price_instalacion).split(".")
    #         precio_inst = float(".".join((int_part, dec_part[:4])))
    #         order_lineI = {
    #             'order_id': orderI.id,
    #             'product_id': line.product_id.id,
    #             'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
    #                 line.currency_id_inst.name) + '' + str(float(precio_inst)) + '+iva',
    #             'price_unit': "{:0.10f}".format(line.price_instalacion),
    #             'tax_id': [self.agreement_id.tax_id.id],
    #         }
    #         order_lineI = self.env['sale.order.line'].create(order_lineI)
    #     # Rentals
    #     meses = 0
    #     meses2 = 0
    #     time_periodicy = 0
    #     descuento = False
    #     if self.agreement_id.payment_period.code == 'M':
    #         time_periodicy = 1
    #     if self.agreement_id.payment_period.code == 'T':
    #         time_periodicy = 3
    #     if self.agreement_id.payment_period.code == 'S':
    #         time_periodicy = 6
    #     if self.agreement_id.payment_period.code == 'AM' or self.agreement_id.payment_period.code == 'A' or self.agreement_id.payment_period.code == 'AD':
    #         time_periodicy = 12
    #     if self.agreement_id.payment_period.code == 'AM' or self.agreement_id.payment_period.code == 'A':
    #         descuento = 2
    #     if self.agreement_id.agreement_discount:
    #         ultimo_de_mesD = calendar.monthrange(line.fecha_cobro.year,
    #                                              line.fecha_cobro.month)
    #         fin_mes = str(line.fecha_cobro.year) + '-' + str(line.fecha_cobro.month).zfill(
    #             2) + '-' + str(ultimo_de_mesD[1])
    #         monthD = months[line.fecha_cobro.month - 1]
    #         if self.agreement_id.agreement_discount.type == 'porcentaje':
    #             total = 0.0
    #             for line in self:
    #                 porcentaje = 0
    #                 porcentaje = (float(self.agreement_id.agreement_discount.code) * line.price) / 100.0
    #                 total = total + porcentaje
    #             order_vals = {
    #                 'partner_id': self.agreement_id.partner_id.id,
    #                 'opportunity_id': self.agreement_id.crm_lead_id.id,
    #                 'agreement_type_id': self.agreement_id.agreement_type_id.id,
    #                 'agreement_id': self.agreement_id.id,
    #                 'date_order': datetime.now(),
    #                 'validity_date': self.agreement_id.end_date,
    #                 'user_id': self.agreement_id.crm_lead_id.user_id.id,
    #                 'origin': self.agreement_id.crm_lead_id.name,
    #                 'partner_dir_id': line.partner_contact_id.id,
    #                 'is_rental_order': True,
    #                 'cost_center_id': line.cost_center,
    #                 'tipo_rental_order': 'descuento',
    #                 'agreement_id': self.agreement_id.id,
    #                 'agreement_line_ids': line.id,
    #                 # 'partner_invoice_id': line.partner_invoice.id,
    #                 'payment_period': self.agreement_id.payment_period.id,
    #                 'payment_method': self.agreement_id.payment_method.id,
    #                 'payment_term_id': self.agreement_id.payment_term_id.id,
    #                 'inicio_fecha_alquiler': line.fecha_cobro,
    #                 'fin_fecha_alquiler': fin_mes,
    #                 'fecha_fact_prog': datetime.now().date() + relativedelta(days=1),
    #                 'fecha_estimada': datetime.now().date() + relativedelta(days=1),
    #                 'periodo_mes': str(monthD) + '/' + str(line.fecha_cobro.year),
    #                 'state': 'sale',  # 'draft',
    #                 'currency_id': self.agreement_id.currency_id.id,
    #                 'pricelist_id': line.pricelist_mens.id,
    #                 'reference_ids': [self.agreement_id.reference_ids.id],
    #                 #'agreement_currency_id': line.currency_id_men.id,
    #             }
    #             order = self.env['sale.order'].create(order_vals)
    #             name_order = str(order.name) + ' ' + str(line.fecha_cobro) + ' - Descuento Promocional'
    #             order.write({'name': name_order})
    #             order_line = {
    #                 'order_id': order.id,
    #                 'product_id': line.product_id.id,
    #                 'price_unit': - total,
    #                 'tax_id': [self.agreement_id.tax_id.id],
    #             }
    #             order_line = self.env['sale.order.line'].create(order_line)
    #         if self.agreement_id.agreement_discount.type == 'valor':
    #             total = float(self.agreement_id.agreement_discount.code)
    #             order_vals = {
    #                 'partner_id': self.agreement_id.partner_id.id,
    #                 'opportunity_id': self.agreement_id.crm_lead_id.id,
    #                 'agreement_type_id': self.agreement_id.agreement_type_id.id,
    #                 'agreement_id': self.agreement_id.id,
    #                 'date_order': datetime.now(),
    #                 'validity_date': self.agreement_id.end_date,
    #                 'user_id': self.agreement_id.crm_lead_id.user_id.id,
    #                 'origin': self.agreement_id.crm_lead_id.name,
    #                 'partner_dir_id': line.partner_contact_id.id,
    #                 'is_rental_order': True,
    #                 'cost_center_id': line.cost_center,
    #                 'tipo_rental_order': 'descuento',
    #                 'agreement_id': self.agreement_id.id,
    #                 # 'partner_invoice_id': line.partner_invoice.id,
    #                 'agreement_line_ids': line.id,
    #                 'payment_period': self.agreement_id.payment_period.id,
    #                 'payment_method': self.agreement_id.payment_method.id,
    #                 'payment_term_id': self.agreement_id.payment_term_id.id,
    #                 'inicio_fecha_alquiler': line.fecha_cobro,
    #                 'fin_fecha_alquiler': fin_mes,
    #                 'fecha_fact_prog': datetime.now().date() + relativedelta(days=1),
    #                 'fecha_estimada': datetime.now().date() + relativedelta(days=1),
    #                 'periodo_mes': str(monthD) + '/' + str(line.fecha_cobro.year),
    #                 'state': 'sale',  # 'draft',
    #                 'currency_id': self.agreement_id.currency_id.id,
    #                 'pricelist_id': line.pricelist_mens.id,
    #                 'reference_ids': [self.agreement_id.reference_ids.id],
    #             }
    #             order = self.env['sale.order'].create(order_vals)
    #             name_order = str(order.name) + ' ' + str(line.fecha_cobro) + ' - Descuento Promocional'
    #             order.write({'name': name_order})
    #             order_line = {
    #                 'order_id': order.id,
    #                 'product_id': line.product_id.id,
    #                 'price_unit': - total,
    #                 'tax_id': [self.agreement_id.tax_id.id],
    #             }
    #             order_line = self.env['sale.order.line'].create(order_line)
    #     #rental orders
    #     for line in self:
    #         paso = False
    #         fin_ciclo = False
    #         primero = True
    #         fecha_activacion = datetime.now().date()
    #         today = datetime.now().date() + relativedelta(days=1)
    #         if fecha_activacion < line.fecha_cobro:
    #             today = line.fecha_cobro
    #             fin_ciclo = today + relativedelta(months=time_periodicy)
    #         if fecha_activacion > line.fecha_cobro:
    #             fin_ciclo = line.fecha_cobro + relativedelta(months=time_periodicy)
    #         else:
    #             fin_ciclo = today + relativedelta(months=time_periodicy)
    #         today_defasado = today
    #
    #         end_period = str(fin_ciclo.year) + '-' + str(fin_ciclo.month).zfill(2) + '-' + str(
    #             fin_ciclo.day).zfill(2)
    #         end_period = datetime.strptime(end_period, '%Y-%m-%d')
    #         if self.agreement_id.payment_period.code == 'S' or self.agreement_id.payment_period.code == 'T': #or self.agreement_id.payment_period.code == 'M':
    #             end_period = fin_ciclo
    #         numeracion = 1
    #         proporcional = True
    #         primero_seq = False
    #         prorrateo = False
    #         end_12 = ''
    #         end_for = ''
    #         es_primero = 1
    #         period_day = line.fecha_cobro.day
    #         period_mes_ = line.fecha_cobro.month
    #         period_anio = line.fecha_cobro.year
    #         period_date = str(line.fecha_cobro.year) + '-' + str(line.fecha_cobro.month).zfill(2) + '-' + '01'
    #         period_date = datetime.strptime(period_date, '%Y-%m-%d')
    #         if line.fecha_cobro.day == 1 or line.fecha_cobro.day == 2 or line.fecha_cobro.day == 3:
    #             primero = False
    #             primero_seq = True
    #             prorrateo = True
    #             proporcional = False
    #         if primero == True:
    #             first = line.fecha_cobro
    #             monthRange = calendar.monthrange(first.year, first.month)
    #             month = monthRange[1]  # es primera vez
    #             dia = month - first.day + 1
    #             por_dia = line.price / month
    #             total = por_dia * dia
    #             ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
    #             fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(ultimo_de_mes[1])
    #             month = months[period_date.month - 1]
    #             order_vals = {
    #                 'partner_id': self.agreement_id.partner_id.id,
    #                 'opportunity_id': self.agreement_id.crm_lead_id.id,
    #                 'agreement_type_id': self.agreement_id.agreement_type_id.id,
    #                 'agreement_id': self.agreement_id.id,
    #                 'date_order': datetime.now(),
    #                 #'date_order': today_defasado,
    #                 'validity_date': self.agreement_id.end_date,
    #                 'user_id': self.agreement_id.crm_lead_id.user_id.id,
    #                 'origin': self.agreement_id.crm_lead_id.name,
    #                 'partner_dir_id': line.partner_contact_id.id,
    #                 'is_rental_order': True,
    #                 'cost_center_id': line.cost_center,
    #                 'tipo_rental_order': 'mensualidad',
    #                 'agreement_id': self.agreement_id.id,
    #                 # 'partner_invoice_id': line.partner_invoice.id,
    #                 'agreement_line_ids': line.id,
    #                 'payment_period': self.agreement_id.payment_period.id,
    #                 'payment_method': self.agreement_id.payment_method.id,
    #                 'payment_term_id': self.agreement_id.payment_term_id.id,
    #                 'inicio_fecha_alquiler': line.fecha_cobro,
    #                 'fin_fecha_alquiler': fin_mes,
    #                 'fecha_fact_prog': today,
    #                 'fecha_estimada': today,
    #                 'periodo_mes': str(month) + '/' + str(period_date.year),
    #                 'state': 'sale',  # 'draft',
    #                 'currency_id': self.agreement_id.currency_id.id,
    #                 'pricelist_id': line.pricelist_mens.id,
    #                 'reference_ids': [self.agreement_id.reference_ids.id],
    #                 'agreement_currency_id': line.currency_id_men.id,
    #             }
    #             order = self.env['sale.order'].create(order_vals)
    #             name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
    #             order.write({'name': name_order})
    #             precio_men = float(total) + 0.0001 # round(total, 4) + 0.0001
    #             if float(total) <= 0.0 and line.vali_price_men == False:
    #                 raise UserError(_('Lo Siento, No se puede activar un contrato con precio de mensualidad cero'))
    #             int_part, dec_part = str(precio_men).split(".")
    #             precio_men = float(".".join((int_part, dec_part[:4])))
    #             order_line = {
    #                 'order_id': order.id,
    #                 'product_id': line.product_id.id,
    #                 'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
    #                     line.currency_id_men.name) + '' + str(float(precio_men)) + '+iva',
    #                 'price_unit': "{:0.10f}".format(total),
    #                 'tax_id': [self.agreement_id.tax_id.id]
    #             }
    #             order_line = self.env['sale.order.line'].create(order_line)
    #             period_date = period_date + relativedelta(months=1)
    #             #primero = False
    #             # if self.agreement_id.payment_period.code == 'M':
    #             #     paso = True
    #             #     today = today + relativedelta(months=time_periodicy)
    #         while (meses <= 36):
    #             # if paso == False:
    #             #     today = today + relativedelta(months=time_periodicy)
    #             if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date():
    #                 meses = meses
    #             else:
    #                 meses = meses + time_periodicy
    #             if self.agreement_id.payment_period.code == 'AM' and meses2 == 12:
    #                 time_periodicy = 1
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 12:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 24:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 36:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 48:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 60:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 72:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 84:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 96:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 108:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 120:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 132:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 144:
    #                 descuento = 2
    #             if self.agreement_id.payment_period.code == 'A' and meses2 == 156:
    #                 descuento = 2
    #             #prorrateo = False
    #             lista = range(time_periodicy)
    #             listadef = list(lista)
    #             meses2 = meses2 + time_periodicy
    #             # if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date() or datetime.strptime(
    #             #         str(end_period)[0:10], '%Y-%m-%d').date() >= datetime.strptime(str(period_date)[0:10],
    #             #                                                                        '%Y-%m-%d').date():
    #             jamie = datetime.strptime(str(period_date)[0:10],'%Y-%m-%d').date()
    #             if primero == True:
    #                 today = today_defasado
    #             elif today_defasado > datetime.strptime(str(period_date)[0:10],'%Y-%m-%d').date():
    #                 today = today_defasado
    #             else:
    #                 if end_12 == '':
    #                     end_12 = today
    #                     today = period_date
    #             primero = False
    #             for i in listadef:
    #
    #                 dia_ = today.day
    #                 mes_ = today.month
    #                 anio_ = today.year
    #                 date_def = today
    #                 if descuento:
    #                     des = range(descuento)
    #                     listades = list(des)
    #                     for des in listades:
    #                         period_date_des = period_date
    #                         if prorrateo:
    #                             period_date_des = period_date + relativedelta(months=1)
    #                         ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
    #                         fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
    #                             ultimo_de_mes[1])
    #                         order_vals = {
    #                             'partner_id': self.agreement_id.partner_id.id,
    #                             'opportunity_id': self.agreement_id.crm_lead_id.id,
    #                             'agreement_type_id': self.agreement_id.agreement_type_id.id,
    #                             'agreement_id': self.agreement_id.id,
    #                             'date_order': datetime.now(),
    #                             #'date_order': today_defasado,
    #                             'validity_date': self.agreement_id.end_date,
    #                             'user_id': self.agreement_id.crm_lead_id.user_id.id,
    #                             'origin': self.agreement_id.crm_lead_id.name,
    #                             'partner_dir_id': line.partner_contact_id.id,
    #                             'is_rental_order': True,
    #                             'cost_center_id': line.cost_center,
    #                             'tipo_rental_order': 'descuento',
    #                             'agreement_id': self.agreement_id.id,
    #                             # 'partner_invoice_id': line.partner_invoice.id,
    #                             'agreement_line_ids': line.id,
    #                             'payment_period': self.agreement_id.payment_period.id,
    #                             'payment_method': self.agreement_id.payment_method.id,
    #                             'payment_term_id': self.agreement_id.payment_term_id.id,
    #                             'inicio_fecha_alquiler': period_date_des,
    #                             'fin_fecha_alquiler': fin_mes,
    #                             'fecha_fact_prog': date_def,
    #                             'fecha_estimada': date_def,
    #                             'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
    #                             'state': 'sale',  # 'draft',
    #                             'currency_id': self.agreement_id.currency_id.id,
    #                             'pricelist_id': line.pricelist_mens.id,
    #                             'reference_ids': [self.agreement_id.reference_ids.id],
    #                             'agreement_currency_id': line.currency_id_men.id,
    #                         }
    #                         order = self.env['sale.order'].create(order_vals)
    #                         name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
    #                         order.write({'name': name_order})
    #                         precio_men = float(line.price) + 0.0001 # round(line.price, 4) + 0.0001
    #                         if float(line.price) <= 0.0 and line.vali_price_men == False:
    #                             raise UserError(
    #                                 _('Lo Siento, No se puede activar un contrato con precio de mensualidad cero'))
    #                         int_part, dec_part = str(precio_men).split(".")
    #                         precio_men = float(".".join((int_part, dec_part[:4])))
    #                         order_line = {
    #                             'order_id': order.id,
    #                             'product_id': line.product_id.id,
    #                             'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
    #                                 line.currency_id_men.name) + '' + str(- float(precio_men)) + '+iva',
    #                             'price_unit': -  float("{:0.10f}".format(line.price)),
    #                             'tax_id': [self.agreement_id.tax_id.id],
    #                         }
    #                         order_line = self.env['sale.order.line'].create(order_line)
    #                         descuento = False
    #                 line_price = line.price
    #                 ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
    #                 fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(
    #                     ultimo_de_mes[1])
    #                 month = months[period_date.month - 1]
    #                 if primero_seq:
    #                     date_def = today
    #                     monthRange = calendar.monthrange(period_date.year, period_date.month)
    #                     montha = monthRange[1]  # es primera vez
    #                     dia = montha - period_date.day
    #                     por_dia = line.price / montha
    #                     line_price = por_dia * dia
    #                 else:
    #                     period_date = str(period_date.year) + '-' + str(
    #                         period_date.month).zfill(2) + '-' + '01'
    #                     period_date = datetime.strptime(period_date, '%Y-%m-%d')
    #                 primero_seq = False
    #
    #                 order_vals = {
    #                     'partner_id': self.agreement_id.partner_id.id,
    #                     'opportunity_id': self.agreement_id.crm_lead_id.id,
    #                     'agreement_type_id': self.agreement_id.agreement_type_id.id,
    #                     'agreement_id': self.agreement_id.id,
    #                     'date_order': datetime.now(),
    #                     #'date_order': today_defasado,
    #                     'validity_date': self.agreement_id.end_date,
    #                     'user_id': self.agreement_id.crm_lead_id.user_id.id,
    #                     'origin': self.agreement_id.crm_lead_id.name,
    #                     'partner_dir_id': line.partner_contact_id.id,
    #                     'is_rental_order': True,
    #                     'cost_center_id': line.cost_center,
    #                     'tipo_rental_order': 'mensualidad',
    #                     'agreement_id': self.agreement_id.id,
    #                     # 'partner_invoice_id': line.partner_invoice.id,
    #                     'agreement_line_ids': line.id,
    #                     'payment_period': self.agreement_id.payment_period.id,
    #                     'payment_method': self.agreement_id.payment_method.id,
    #                     'payment_term_id': self.agreement_id.payment_term_id.id,
    #                     'inicio_fecha_alquiler': period_date,
    #                     'fin_fecha_alquiler': fin_mes,
    #                     'fecha_fact_prog': date_def,
    #                     'fecha_estimada': date_def,
    #                     'periodo_mes': str(month) + '/' + str(period_date.year),
    #                     'state': 'sale',  # 'draft',
    #                     'currency_id': self.agreement_id.currency_id.id,
    #                     'pricelist_id': line.pricelist_mens.id,
    #                     'reference_ids': [self.agreement_id.reference_ids.id],
    #                     'agreement_currency_id': line.currency_id_men.id,
    #                 }
    #                 order = self.env['sale.order'].create(order_vals)
    #                 name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
    #                 order.write({'name': name_order})
    #                 precio_men = float(line_price) + 0.0001 # round(line_price, 4) + 0.0001
    #                 if float(line_price) <= 0.0  and line.vali_price_men == False:
    #                     raise UserError(
    #                         _('Lo Siento, No se puede activar un contrato con precio de mensualidad cero'))
    #                 int_part, dec_part = str(precio_men).split(".")
    #                 precio_men = float(".".join((int_part, dec_part[:4])))
    #                 order_line = {
    #                     'order_id': order.id,
    #                     'product_id': line.product_id.id,
    #                     'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
    #                         line.currency_id_men.name) + '' + str(float(precio_men)) + '+iva',
    #                     'price_unit': "{:0.10f}".format(line_price),
    #                     'tax_id': [self.agreement_id.tax_id.id],
    #                 }
    #                 order_line = self.env['sale.order.line'].create(order_line)
    #                 numeracion = numeracion + 1
    #                 primero = False
    #                 proporcional = False
    #                 period_date = period_date + relativedelta(months=1)
    #             today = today + relativedelta(months=time_periodicy)
    #             #today_defasado = today + relativedelta(months=time_periodicy)
    #
    #
    #     # Mantenciones
    #     for line in self:
    #         project_id = self.env['project.project'].search([('name', '=', 'Servicio externo')], limit=1).id
    #         if line.maintenance_id:
    #             todayM = line.start_date# datetime.now().date()
    #             period_m = datetime.now().date()
    #             #period_m = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + '01'
    #             #period_m = datetime.strptime(period_date, '%Y-%m-%d')
    #             meses = 0
    #             mesesM = 0
    #             numeracionM = 1
    #             mj2 = []
    #             num = 0
    #             for j in line.maintenance_id.maintenance_m_line:
    #                 if j.number not in mj2:
    #                     mj2.append(j.number)
    #             while (mesesM < 43):
    #                 name_list = []
    #                 mj2 = sorted(mj2, reverse=False)
    #                 for i in mj2:
    #                     if datetime.strptime(str(period_m)[0:10], '%Y-%m-%d').date() > todayM:
    #                         mesesM = mesesM
    #                     else:
    #                         mesesM = mesesM + int(mj2[0])
    #                     meses = meses + int(mj2[0])
    #                     if mesesM >= 36:
    #                         break
    #                     todayM = todayM + relativedelta(months=int(mj2[0]))
    #                     num = i
    #                     # /// new
    #                     categ_inst = False
    #                     exist_inst = self.env['project.task.template'].search([('mantention', '=', True)], limit=1,
    #                                                                           order='id')
    #                     if not exist_inst:
    #                         raise UserError(_(
    #                             'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede pasar a preprueba sin tener una plantilla destinada para la mantención, \n \n Por favor comuniquese con un Administrador'))
    #                     categ_inst = self.env['helpdesk.tag'].search([('mantention', '=', True)], limit=1,
    #                                                                  order='id')
    #                     if not categ_inst:
    #                         raise UserError(_(
    #                             'Disculpe, No se puede avanzar con el contrato, \n \n  Porque no se puede pasar a preprueba sin tener una categoria destinada para la mantención, \n \n Por favor comuniquese con un Administrador'))
    #                     categoria = self.env['categoria.maihue.template'].search(
    #                         [('project_template_id', '=', exist_inst.id)], limit=1,
    #                         order='id')
    #                     ticket_man = self.env['helpdesk.ticket'].with_context(instalation=True).create({
    #                         'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
    #                         'partner_id': self.agreement_id.partner_id.id,
    #                         'assign_date': todayM,
    #                         'fecha_registro_ticket': todayM,
    #                         'agreement_id': self.agreement_id.id,
    #                         'ticket_type_id': categoria.categoria_id.ticket_type_id.id,
    #                         'categoria_maihue_id': categ_inst.id,
    #                         'ticket_type_id': 1,
    #                         'agreement_line_ids': line.id,
    #                         'partner_email': self.agreement_id.partner_id.email,
    #                         #'user_id': line.mantenedor or False,
    #                     })
    #                     invite = self.env['survey.invite']
    #                     url_invite = werkzeug.urls.url_join(exist_inst.survey_id.get_base_url(),
    #                                                         exist_inst.survey_id.get_start_url()) if invite.survey_id else False
    #                     order_lineM = self.env['project.task'].create({
    #                         'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
    #                         'partner_id': self.agreement_id.partner_id.id,
    #                         'helpdesk_ticket_id': ticket_man.id,
    #                         # 'stage_id': 4,
    #                         'fsm_done': False,
    #                         'project_id': project_id,
    #                         'agreement_id': line.agreement_id.id,
    #                         'agreement_line_id': line.id,
    #                         'formulario': url_invite,
    #                         'survey_id': exist_inst.survey_id.id,
    #                         'type_transfer_equipment': exist_inst.type_transfer_equipment,
    #                         'l10n_cl_delivery_guide_reason': exist_inst.l10n_cl_delivery_guide_reason,
    #                         'task_template_id': exist_inst.id,
    #                         'admin_line_id': line.admin_line_id.id,
    #                         'description': self.general_msj,
    #                     })
    #                     for x in line.maintenance_id.maintenance_m_line:
    #                         if x.number <= num:
    #                             if x.type not in name_list:
    #                                 name_list.append(x.type)
    #                             order_lineM_l = self.env['project.task.product'].create({
    #                                 'product_id': x.product_id.id,
    #                                 'description': x.product_id.name,
    #                                 'planned_qty': x.quantity,
    #                                 'product_uom': x.product_id.uom_id.id,
    #                                 'time_spent': x.time_spent,
    #                                 'task_id': order_lineM.id,
    #                             })
    #                     name_new = ''
    #                     for n in name_list:
    #                         name_new = name_new + ' ' + n
    #                     ticket_man.write({'name': ticket_man.name + ' ' + name_new})
    #                     order_lineM.write({'name': order_lineM.name + ' ' + name_new})
    #                     numeracionM = numeracionM + 1
    #         if len(self.agreement_id.line_ids) == 1:
    #             self.agreement_id.write({'stage_id': 8, 'activado_btn': True})
    #             self.write({'state': 'act', 'activado_btn': True})
    #         else:
    #             self.agreement_id.write({'stage_id': 7, 'activado_btn': True})
    #             self.write({'state': 'act', 'activado_btn': True})
    #
    #     orden_compra = self.agreement_id.orden_compra()
    #
    #     state_line = True
    #     for line in self.agreement_id.line_ids:
    #         if line.state not in ['act', 'cancelado', 'no_vigente']:
    #             state_line = False
    #     #line.write({'state': 'act', 'activado_btn': True})
    #     if state_line:
    #         state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO COMPLETO')], limit=1)
    #         self.agreement_id.write({'stage_id': state_id})
    #     else:
    #         state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO PARCIAL')], limit=1)
    #         self.agreement_id.write({'stage_id': state_id})
    #
    #     #return True
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'reload',
    #     }

    def cancel_agreement(self):
        self.write({'state': 'proceso'})
        rentals = self.env['sale.order'].search([
            ('agreement_line_ids', '=', self.id),
            ('state', '=', 'sale')])
        rentals.action_cancel()
        jamie = 1

    def close_agreement(self):
        self.write({'state': 'cerrado'})

    def no_vigent_agreement(self):
        self.write({'state': 'prueba'})

    @api.model
    def create(self, vals):
        if not vals.get('is_template'):
            agreement_name = self.env['agreement'].search([('id', '=', vals['agreement_id'])])
            vals['name'] = str(agreement_name.name) + '-1'
            no_existe = False
            while (no_existe == False):
                existe = self.env['agreement.line'].search([('name', '=', vals['name'])])
                if not existe:
                    no_existe = True
                if existe:
                    num = vals['name'].split("-")
                    prox = int(num[-1]) + 1
                    vals['name'] = str(agreement_name.name) + '-' + str(prox)
        res = super(AgreementLine, self).create(vals)
        crm_line = self.env['crm.line'].search([('agreement_line_id', '=', res.id)])
        if not crm_line:
            if 'lead_exist' not in self._context:
                crm_line = {
                    #'agreement_id': res.agreement_id.id,
                    'product_id': res.product_id.id,
                    'crm_id': res.agreement_id.crm_lead_id.id,
                    'product_principal': res.product_principal.id,
                    'name': res.product_id.name,
                    'uom_id': res.product_id.uom_id.id,
                    'partner_contact_id': res.partner_contact_id.id,
                    'agreement_line_id': res.id,
                    #'partner_invoice_id': deltals.partner_invoice_id.id,
                    #'price': deltals.price,
                    'location': res.location,
                }
                line = self.env['crm.line'].create(crm_line)
        if 'pass_line_rel' in vals:
            rel = self.browse(vals['pass_line_rel'])
            rel.write({
                        'fut_line_rel': res.id,
                        # 'fut_motivo_rel': self.pass_motivo_rel,
                        # 'fut_description_rel': self.pass_description_rel
            })
        return res

    def write(self, vals):
        if 'partner_contact_id' in vals:
            crm_line = self.env['crm.line'].search([('agreement_line_id', '=', self.id)])
            if not crm_line:
                raise UserError(
                    _('Lo Siento, No se puede editar porque esta obsoleta la data, por favor contactese con el administrador'))
            crm_line.write({'partner_contact_id': vals['partner_contact_id']})
        if 'location' in vals:
            crm_line = self.env['crm.line'].search([('agreement_line_id', '=', self.id)])
            if not crm_line:
                raise UserError(
                    _('Lo Siento, No se puede editar porque esta obsoleta la data, por favor contactese con el administrador'))
            crm_line.write({'location': vals['location']})
        if 'product_id' in vals:
            crm_line = self.env['crm.line'].search([('agreement_line_id', '=', self.id)])
            if not crm_line:
                raise UserError(
                    _('Lo Siento, No se puede editar porque esta obsoleta la data, por favor contactese con el administrador'))
            crm_line.write({'product_id': vals['product_id']})
        if 'product_principal' in vals:
            crm_line = self.env['crm.line'].search([('agreement_line_id', '=', self.id)])
            if not crm_line:
                raise UserError(
                    _('Lo Siento, No se puede editar porque esta obsoleta la data, por favor contactese con el administrador'))
            jamie = vals['product_principal']
            crm_line.write({'product_principal': vals['product_principal']})
        if 'admin_line_id' in vals:
            date = datetime.now()
            if self.admin_line_id:
                # desincorporado
                log_vals = {
                    'agreement_line_id': self.id,
                    'name': self.admin_line_id.id,
                    'user_id': self.write_uid.id,
                    'date': date,
                    'state': 'des',
                    'vigente': False,
                }
                self.env['log.admin.line'].create(log_vals)
            # asignado
            log_vals = {
                'agreement_line_id': self.id,
                'name': vals['admin_line_id'],
                'user_id': self.write_uid.id,
                'date': date,
                'state': 'asig',
                'vigente': True,
            }
            self.env['log.admin.line'].create(log_vals)

        if 'pass_line_rel' in vals:
            rel = self.browse(vals['pass_line_rel'])
            rel.write({
                        'fut_line_rel': self.id,
                        # 'fut_motivo_rel': self.pass_motivo_rel,
                        # 'fut_description_rel': self.pass_description_rel
            })
        if 'cost_center' in vals:
            orders = self.env['sale.order'].search(
                [('agreement_id', '=', self.agreement_id.id), ('agreement_line_ids', '=', self.id), ('state', '=', 'draft')])
            if orders:
                orders.write({'cost_center_id': vals['cost_center']})
        return super(AgreementLine, self).write(vals)

    def diff_month(self, d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    def cron_agreement_robot_rentals(self):
        jamie_end = 0
        agreements_lines = self.env['agreement.line'].search([]) #[('stage_id', 'in', [9,10,11])]
        for agreement_line in agreements_lines:
            if jamie_end == 1:
                break
            last_sales_orders = self.env['sale.order'].search([('agreement_line_ids', '=', agreement_line.id)], order="id desc", limit=1)
            if last_sales_orders:
                jamie1 = last_sales_orders.fecha_estimada
                jamie2 = datetime.now().date()
                diferencia = self.diff_month(jamie1, jamie2)
                jamie = diferencia
                if diferencia < 36:
                    num_veces = diferencia - 36
                    # if agreement_line.stage_id.id not in [6,7]: #revisado y activado parcial
                    #     raise UserError(_(
                    #         'Disculpe, Es necesario que el contrato este en estado Revisado, para poder activar la linea de contrato'))
                    # if agreement_line.agreement_id.not_activate:
                    #     raise UserError(_('Lo Siento, No se puede activar una Linea de Contrato con el check de No permite Activación'))
                    # if self.line_rel:
                    #     self.line_rel.write({'state_rel': 'no_vi'})
                    months = (
                    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
                    "Diciembre")
                    # Rentals
                    meses = 0
                    meses2 = 0
                    time_periodicy = 0
                    descuento = False
                    if agreement_line.agreement_id.payment_period.code == 'M':
                        time_periodicy = 1
                    if agreement_line.agreement_id.payment_period.code == 'T':
                        time_periodicy = 3
                    if agreement_line.agreement_id.payment_period.code == 'S':
                        time_periodicy = 6
                    if agreement_line.agreement_id.payment_period.code == 'AM' or agreement_line.agreement_id.payment_period.code == 'A' or agreement_line.agreement_id.payment_period.code == 'AD':
                        time_periodicy = 12
                    if agreement_line.agreement_id.payment_period.code == 'AM' or agreement_line.agreement_id.payment_period.code == 'A':
                        descuento = 2
                    #rental orders
                    primero = True
                    today = last_sales_orders.fecha_estimada  + relativedelta(months=time_periodicy) #datetime.now().date() + relativedelta(days=1)
                    today_defasado = today
                    fin_ciclo = today + relativedelta(months=time_periodicy)
                    end_period = str(fin_ciclo.year) + '-' + str(agreement_line.fecha_cobro.month).zfill(2) + '-' + str(
                        agreement_line.fecha_cobro.day).zfill(2)
                    end_period = datetime.strptime(end_period, '%Y-%m-%d')
                    if agreement_line.agreement_id.payment_period.code == 'S' or agreement_line.agreement_id.payment_period.code == 'T' or agreement_line.agreement_id.payment_period.code == 'M':
                        end_period = fin_ciclo
                    numeracion = 1
                    proporcional = True
                    primero_seq = False
                    prorrateo = True
                    end_12 = ''
                    end_for = ''
                    es_primero = 1
                    period_day = today.day
                    period_mes_ = today.month
                    period_anio = today.year
                    period_date = str(today) #str(agreement_line.fecha_cobro.year) + '-' + str(agreement_line.fecha_cobro.month).zfill(2) + '-' + '01'
                    period_date = datetime.strptime(period_date, '%Y-%m-%d')
                    if agreement_line.fecha_cobro.day == 1 or agreement_line.fecha_cobro.day == 2 or agreement_line.fecha_cobro.day == 3:
                        primero = False
                        primero_seq = True
                        prorrateo = True
                        proporcional = False
                    while (meses < 36):
                        if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date():
                            meses = meses
                        else:
                            meses = meses + time_periodicy
                        if agreement_line.agreement_id.payment_period.code == 'AM' and meses2 == 12:
                            time_periodicy = 1
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 12:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 24:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 36:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 48:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 60:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 72:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 84:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 96:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 108:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 120:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 132:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 144:
                            descuento = 2
                        if agreement_line.agreement_id.payment_period.code == 'A' and meses2 == 156:
                            descuento = 2
                        prorrateo = False
                        lista = range(time_periodicy)
                        listadef = list(lista)
                        meses2 = meses2 + time_periodicy
                        if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date() or datetime.strptime(
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
                                    period_date_des = today_defasado
                                    if prorrateo:
                                        period_date_des = today_defasado
                                    ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                                    fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
                                        ultimo_de_mes[1])
                                    order_vals = {
                                        'partner_id': agreement_line.agreement_id.partner_id.id,
                                        'opportunity_id': agreement_line.agreement_id.crm_lead_id.id,
                                        'agreement_type_id': agreement_line.agreement_id.agreement_type_id.id,
                                        'agreement_id': agreement_line.agreement_id.id,
                                        'date_order': datetime.now(),
                                        'validity_date': agreement_line.agreement_id.end_date,
                                        'user_id': agreement_line.agreement_id.crm_lead_id.user_id.id,
                                        'origin': agreement_line.agreement_id.crm_lead_id.name,
                                        'partner_dir_id': agreement_line.partner_contact_id.id,
                                        'is_rental_order': True,
                                        'cost_center_id': agreement_line.cost_center,
                                        'tipo_rental_order': 'descuento',
                                        'agreement_id': agreement_line.agreement_id.id,
                                        # 'partner_invoice_id': line.partner_invoice.id,
                                        'agreement_line_ids': agreement_line.id,
                                        'payment_period': agreement_line.agreement_id.payment_period.id,
                                        'payment_method': agreement_line.agreement_id.payment_method.id,
                                        'payment_term_id': agreement_line.agreement_id.payment_term_id.id,
                                        'inicio_fecha_alquiler': period_date_des,
                                        'fin_fecha_alquiler': fin_mes,
                                        'fecha_fact_prog': date_def,
                                        'fecha_estimada': date_def,
                                        'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
                                        'state': 'sale',  # 'draft',
                                        'currency_id': agreement_line.agreement_id.currency_id.id,
                                        'pricelist_id': agreement_line.pricelist_mens.id,
                                        'reference_ids': [agreement_line.agreement_id.reference_ids.id],
                                        'agreement_currency_id': agreement_line.currency_id_men.id,
                                    }
                                    order = self.env['sale.order'].create(order_vals)
                                    name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                                    order.write({'name': name_order})
                                    precio_men = float(agreement_line.price) + 0.0001 # round(line.price, 4) + 0.0001
                                    if float(agreement_line.price) <= 0.0 and agreement_line.vali_price_men == False:
                                        raise UserError(
                                            _('Lo Siento, No se puede activar un contrato con precio de mensualidad cero'))
                                    order_line = {
                                        'order_id': order.id,
                                        'product_id': agreement_line.product_id.id,
                                        'name': str(agreement_line.product_id.name_key) + '/' + str(agreement_line.maintenance_id.name) + '/' + str(
                                            agreement_line.currency_id_men.name) + '' + str(- precio_men) + '+iva',
                                        'price_unit': -  float("{:0.4f}".format(agreement_line.price)),
                                        'tax_id': [agreement_line.agreement_id.tax_id.id],
                                    }
                                    order_line = self.env['sale.order.line'].create(order_line)
                                    descuento = False
                            line_price = agreement_line.price
                            ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
                            fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(
                                ultimo_de_mes[1])
                            month = months[period_date.month - 1]
                            if primero_seq:
                                date_def = today
                                monthRange = calendar.monthrange(period_date.year, period_date.month)
                                montha = monthRange[1]  # es primera vez
                                dia = montha - period_date.day
                                por_dia = agreement_line.price / montha
                                line_price = por_dia * dia
                            else:
                                period_date = str(period_date.year) + '-' + str(
                                    period_date.month).zfill(2) + '-' + '01'
                                period_date = datetime.strptime(period_date, '%Y-%m-%d')
                            primero_seq = False

                            order_vals = {
                                'partner_id': agreement_line.agreement_id.partner_id.id,
                                'opportunity_id': agreement_line.agreement_id.crm_lead_id.id,
                                'agreement_type_id': agreement_line.agreement_id.agreement_type_id.id,
                                'agreement_id': agreement_line.agreement_id.id,
                                'date_order': datetime.now(),
                                'validity_date': agreement_line.agreement_id.end_date,
                                'user_id': agreement_line.agreement_id.crm_lead_id.user_id.id,
                                'origin': agreement_line.agreement_id.crm_lead_id.name,
                                'partner_dir_id': agreement_line.partner_contact_id.id,
                                'is_rental_order': True,
                                'cost_center_id': agreement_line.cost_center,
                                'tipo_rental_order': 'mensualidad',
                                'agreement_id': agreement_line.agreement_id.id,
                                # 'partner_invoice_id': line.partner_invoice.id,
                                'agreement_line_ids': agreement_line.id,
                                'payment_period': agreement_line.agreement_id.payment_period.id,
                                'payment_method': agreement_line.agreement_id.payment_method.id,
                                'payment_term_id': agreement_line.agreement_id.payment_term_id.id,
                                'inicio_fecha_alquiler': period_date,
                                'fin_fecha_alquiler': fin_mes,
                                'fecha_fact_prog': date_def,
                                'fecha_estimada': date_def,
                                'periodo_mes': str(month) + '/' + str(period_date.year),
                                'state': 'sale',  # 'draft',
                                'currency_id': agreement_line.agreement_id.currency_id.id,
                                'pricelist_id': agreement_line.pricelist_mens.id,
                                'reference_ids': [agreement_line.agreement_id.reference_ids.id],
                                'agreement_currency_id': agreement_line.currency_id_men.id,
                            }
                            order = self.env['sale.order'].create(order_vals)
                            name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                            order.write({'name': name_order})
                            precio_men = float(line_price) + 0.0001 # round(line_price, 4) + 0.0001
                            if float(line_price) <= 0.0  and agreement_line.vali_price_men == False:
                                raise UserError(
                                    _('Lo Siento, No se puede activar un contrato con precio de mensualidad cero'))
                            order_line = {
                                'order_id': order.id,
                                'product_id': agreement_line.product_id.id,
                                'name': str(agreement_line.product_id.name_key) + '/' + str(agreement_line.maintenance_id.name) + '/' + str(
                                    agreement_line.currency_id_men.name) + '' + str(precio_men) + '+iva',
                                'price_unit': "{:0.4f}".format(line_price),
                                'tax_id': [agreement_line.agreement_id.tax_id.id],
                            }
                            order_line = self.env['sale.order.line'].create(order_line)
                            numeracion = numeracion + 1
                            primero = False
                            proporcional = False
                            period_date = period_date + relativedelta(months=1)
                        today = today + relativedelta(months=time_periodicy)
                        meses = 37
                        jamie_end = 1
            #break


        # # Mantenciones
        # for line in self:
        #     if line.maintenance_id:
        #         todayM = line.start_date# datetime.now().date()
        #         period_m = datetime.now().date()
        #         #period_m = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + '01'
        #         #period_m = datetime.strptime(period_date, '%Y-%m-%d')
        #         meses = 0
        #         mesesM = 0
        #         numeracionM = 1
        #         mj2 = []
        #         num = 0
        #         for j in line.maintenance_id.maintenance_m_line:
        #             if j.number not in mj2:
        #                 mj2.append(j.number)
        #         while (mesesM < 43):
        #             name_list = []
        #             mj2 = sorted(mj2, reverse=False)
        #             for i in mj2:
        #                 if datetime.strptime(str(period_m)[0:10], '%Y-%m-%d').date() > todayM:
        #                     mesesM = mesesM
        #                 else:
        #                     mesesM = mesesM + int(mj2[0])
        #                 meses = meses + int(mj2[0])
        #                 if mesesM >= 36:
        #                     break
        #                 todayM = todayM + relativedelta(months=int(mj2[0]))
        #                 num = i
        #                 ticket_man = self.env['helpdesk.ticket'].create({
        #                     'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
        #                     'partner_id': self.agreement_id.partner_id.id,
        #                     'assign_date': todayM,
        #                     'fecha_registro_ticket': todayM,
        #                     'agreement_id': self.agreement_id.id,
        #                     'ticket_type_id': 1,
        #                     'agreement_line_ids': line.id,
        #                     'partner_email': self.agreement_id.partner_id.email,
        #                     #'user_id': line.mantenedor or False,
        #                 })
        #                 order_lineM = self.env['project.task'].create({
        #                     'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
        #                     'partner_id': self.agreement_id.partner_id.id,
        #                     'helpdesk_ticket_id': ticket_man.id,
        #                     'description': self.general_msj,
        #                     #'stage_id': 4,
        #                     'fsm_done': False,
        #                     'project_id': 2,
        #                 })
        #                 for x in line.maintenance_id.maintenance_m_line:
        #                     if x.number <= num:
        #                         if x.type not in name_list:
        #                             name_list.append(x.type)
        #                         # order_lineM_l = self.env['project.task.product'].create({
        #                         #     'product_id': x.product_id.id,
        #                         #     'description': x.product_id.name,
        #                         #     'planned_qty': x.quantity,
        #                         #     'product_uom': x.product_id.uom_id.id,
        #                         #     'time_spent': x.time_spent,
        #                         #     'task_id': order_lineM.id,
        #                         # })
        #                 name_new = ''
        #                 for n in name_list:
        #                     name_new = name_new + ' ' + n
        #                 ticket_man.write({'name': ticket_man.name + ' ' + name_new})
        #                 order_lineM.write({'name': order_lineM.name + ' ' + name_new})
        #                 numeracionM = numeracionM + 1
        #     if len(self.agreement_id.line_ids) == 1:
        #         self.agreement_id.write({'stage_id': 8, 'activado_btn': True})
        #         self.write({'state': 'act', 'activado_btn': True})
        #     else:
        #         self.agreement_id.write({'stage_id': 7, 'activado_btn': True})
        #         self.write({'state': 'act', 'activado_btn': True})
        #
        # orden_compra = self.agreement_id.orden_compra()
        #
        # state_line = True
        # for line in self.agreement_id.line_ids:
        #     if line.state not in ['act', 'cancelado', 'no_vigente']:
        #         state_line = False
        # #line.write({'state': 'act', 'activado_btn': True})
        # if state_line:
        #     state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO COMPLETO')], limit=1)
        #     self.agreement_id.write({'stage_id': state_id})
        # else:
        #     state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO PARCIAL')], limit=1)
        #     self.agreement_id.write({'stage_id': state_id})
        #
        # #return True
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

class ProductMaintenance(models.Model):
    _name = 'product.maintenance_m'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    sequence = fields.Integer('Sequence')
    name = fields.Text(string='Name', required=True)
    product_id = fields.Many2one('product.product', string='Service')
    maintenance_m_line = fields.One2many('product.maintenance_m.line', 'maintenance_id', string='Maintenance Lines')

    # @api.onchange('product_id')
    # def get_product_maintenance(self):
    #     if self.product_id:
    #         for m in self.maintenance_m_line.product_id:
    #             m.product_id = self.product_id.id


class CategoriaMaihue(models.Model):
    _name = 'categoria.maihue'
    _description = 'Categoria Maihue'

    name = fields.Char('Categoria')
    active = fields.Boolean(default=True)

    subcategoria_maihue_ids = fields.One2many(
        "subcategoria.maihue",
        "categoria_maihue_id",
        string="Subcategoria"
    )
    ticket_type_id = fields.Many2one(
        "helpdesk.ticket.type",
        string="Tipo de ticket",
        required=True)
    categoria_line = fields.One2many('categoria.maihue.template', 'categoria_id', string='categoria Lines',
                                        copy=True,
                                        auto_join=True)

class CategoriaMaihueTemplate(models.Model):
    _name = 'categoria.maihue.template'
    _rec_name = 'project_template_id'
    _description = "Linea para las plantillas utilizadas para orden de servicio externo"

    project_template_id = fields.Many2one('project.task.template', string='Plantilla')
    categoria_id = fields.Many2one('categoria.maihue', string='Categ Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True, domain="[('is_fsm', '=', True)]")

    @api.onchange('project_template_id')
    def onchange_project_template_id(self):
        if self.project_template_id:
            self.project_id = self.project_template_id.project_id

class ProductMaintenanceLine(models.Model):
    _name = 'product.maintenance_m.line'

    sequence = fields.Integer('Sequence')
    maintenance_id = fields.Many2one('product.maintenance_m', string='Maintenance Reference', required=True, ondelete='cascade', index=True)
    periodicity = fields.Selection(
        selection=[
            ('hours', 'Hours'),
            ('days', 'Days'),
            ('month', 'Month'),
            ('year', 'Years')],
        string='Periodicity',
        default='month',
        required=True)
    time_spent = fields.Float('Time/Hours', precision_digits=2)
    type = fields.Selection(
        selection=[
            ('media', 'Mean'),
            ('full', 'Full'),
            ('membrana', 'Membrane')],
        string='Type',
        default='media',
        required=True)
    number = fields.Integer('Number')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float("Quantity", default=1, required=True)

class AgreementLineKeys(models.Model):
    _name = "agreement.line.keys"
    _description = "Agreement Invoice Lines Ids products"

    name = fields.Char(
        string="Number",
        required=True)

class AgreementPenalty(models.Model):
    _name = 'agreement.penalty'

    name = fields.Char(required=True, string='Name')
    code = fields.Float(required=True, string='Value')
    type = fields.Selection(selection=[('porcentaje', 'Percentage'), ('valor', 'Net worth')], string='Type')
    type_id = fields.Many2one('penalty.type', 'Class', readonly=False)
    pricelist_id = fields.Many2one('product.pricelist', 'Rate', readonly=False)
    med_apl = fields.Text(string='Metodología de Aplicación', required=True)

class AgreementDiscount(models.Model):
    _name = 'agreement.discount'

    @api.model
    def _cron_agreement_discounts(self):
        discounts = self.env['agreement.discount'].sudo().search([
                        ('state', '=', 'in_progress')])
        for dis in discounts:
            months = (
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
                "Noviembre",
                "Diciembre")
            today = datetime.now().date()
            if dis.intervalo:
                descuento = 1
                state = 'in_progress'
                des = range(descuento)
                listades = list(des)
                for des in listades:
                    period_date_des = dis.fecha_inicio
                    date_def = period_date_des
                    ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                    fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
                        ultimo_de_mes[1])
                    order_vals = {
                        'partner_id': dis.agreement_id.partner_id.id,
                        'opportunity_id': dis.agreement_id.crm_lead_id.id,
                        'agreement_type_id': dis.agreement_id.agreement_type_id.id,
                        'agreement_id': dis.agreement_id.id,
                        'date_order': datetime.now(),
                        'validity_date': dis.agreement_id.end_date,
                        'user_id': dis.agreement_id.crm_lead_id.user_id.id,
                        'origin': dis.agreement_id.crm_lead_id.name,
                        'partner_dir_id': dis.agreement_line_id.partner_contact_id.id,
                        'is_rental_order': True,
                        'cost_center_id': dis.agreement_line_id.cost_center,
                        'tipo_rental_order': 'descuento',
                        'agreement_id': dis.agreement_id.id,
                        'agreement_line_ids': dis.agreement_line_id.id,
                        'payment_period': dis.agreement_id.payment_period.id,
                        'payment_method': dis.agreement_id.payment_method.id,
                        'payment_term_id': dis.agreement_id.payment_term_id.id,
                        'inicio_fecha_alquiler': period_date_des,
                        'fin_fecha_alquiler': fin_mes,
                        'fecha_fact_prog': date_def,
                        'fecha_estimada': date_def,
                        'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
                        'state': 'sale',  # 'draft',
                        'currency_id': dis.agreement_id.currency_id.id,
                        'pricelist_id': dis.agreement_line_id.pricelist_mens.id,
                        'reference_ids': [dis.agreement_id.reference_ids.id],
                        'agreement_currency_id': dis.agreement_line_id.currency_id_men.id,
                    }
                    order = self.env['sale.order'].create(order_vals)
                    name_order = str(order.name) + ' ' + str(today)
                    order.write({'name': name_order})
                    valor = 0
                    if dis.aplic == 'inst':
                        valor = dis.agreement_line_id.price_instalacion
                    else:
                        valor = dis.agreement_line_id.price
                    if dis.type == 'valor':
                        precio = dis.code
                    else:
                        precio = (float(dis.code) * valor) / 100.0
                    order_line = {
                        'order_id': order.id,
                        'product_id': dis.product_id.id,
                        'name': 'Descuento',
                        'price_unit': - precio,
                        'tax_id': [dis.agreement_id.tax_id.id],
                    }
                    order_line = self.env['sale.order.line'].create(order_line)
                    #self.fecha_inicio = self.fecha_inicio + relativedelta(months=1)
        return True

    name = fields.Char(required=True, string='Name')
    code = fields.Float(required=True, string='Value')
    intervalo = fields.Integer(required=True, string='Num Repeticiones')
    type = fields.Selection(selection=[('porcentaje', 'Porcentaje'), ('valor', 'Valor Neto')], string='Tipo')
    fecha_inicio = fields.Date('Start date')
    fecha_fin = fields.Date('End date')
    pricelist_id = fields.Many2one('product.pricelist', 'Rate', readonly=False)
    agreement_id = fields.Many2one('agreement', ondelete='cascade', index=True, copy=False)
    agreement_line_id = fields.Many2one('agreement.line', ondelete='cascade', index=True, copy=False)
    aplic = fields.Selection(
        [("inst", "Instalation"), ("men", "Mensualidad")],
        default="men",
        track_visibility="always", string='Aplicar a')
    state = fields.Selection(
        [("draft", "Draft"), ("confir", "Confirmed"), ("in_progress", "In Progress"), ("done", "done")],
        default="draft",
        track_visibility="always")
    product_id = fields.Many2one('product.product', string='Producto Descuento')

    def confirm(self):
        months = (
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
            "Noviembre",
            "Diciembre")
        today = datetime.now().date()
        if self.intervalo:
            descuento = 0
            if self.intervalo == -1:
                descuento = 1
                state = 'in_progress'
            else:
                descuento = self.intervalo
                state = 'confir'
            des = range(descuento)
            listades = list(des)
            for des in listades:
                period_date_des = self.fecha_inicio
                date_def = period_date_des
                ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
                    ultimo_de_mes[1])
                order_vals = {
                    'partner_id': self.agreement_id.partner_id.id,
                    'opportunity_id': self.agreement_id.crm_lead_id.id,
                    'agreement_type_id': self.agreement_id.agreement_type_id.id,
                    'agreement_id': self.agreement_id.id,
                    'date_order': datetime.now(),
                    'validity_date': self.agreement_id.end_date,
                    'user_id': self.agreement_id.crm_lead_id.user_id.id,
                    'origin': self.agreement_id.crm_lead_id.name,
                    'partner_dir_id': self.agreement_line_id.partner_contact_id.id,
                    'is_rental_order': True,
                    'cost_center_id': self.agreement_line_id.cost_center,
                    'tipo_rental_order': 'descuento',
                    'agreement_id': self.agreement_id.id,
                    'agreement_line_ids': self.agreement_line_id.id,
                    'payment_period': self.agreement_id.payment_period.id,
                    'payment_method': self.agreement_id.payment_method.id,
                    'payment_term_id': self.agreement_id.payment_term_id.id,
                    'inicio_fecha_alquiler': period_date_des,
                    'fin_fecha_alquiler': fin_mes,
                    'fecha_fact_prog': date_def,
                    'fecha_estimada': date_def,
                    'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
                    'state': 'sale',  # 'draft',
                    'currency_id': self.agreement_id.currency_id.id,
                    'pricelist_id': self.agreement_line_id.pricelist_mens.id,
                    'reference_ids': [self.agreement_id.reference_ids.id],
                    'agreement_currency_id': self.agreement_line_id.currency_id_men.id,
                }
                order = self.env['sale.order'].create(order_vals)
                name_order = str(order.name) + ' ' + str(today)
                order.write({'name': name_order})
                valor = 0
                if self.aplic == 'inst':
                    valor = self.agreement_line_id.price_instalacion
                else:
                    valor = self.agreement_line_id.price
                if self.type == 'valor':
                    precio = self.code
                else:
                    precio = (float(self.code) * valor) / 100.0
                order_line = {
                    'order_id': order.id,
                    'product_id': self.product_id.id,
                    'name': 'Descuento',
                    'price_unit': - precio,
                    'tax_id': [self.agreement_id.tax_id.id],
                }
                order_line = self.env['sale.order.line'].create(order_line)
                self.fecha_inicio = self.fecha_inicio + relativedelta(months=1)
        self.write({'state': state})

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        if self.pricelist_id:
            product_domain = []
            for item in self.pricelist_id.item_ids:
                if item.compute_price == 'percentage':
                    product_domain.append(item.product_tmpl_id.id)
            return {'domain':{'product_id':[('id','in',product_domain)]}}

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            for item in self.pricelist_id.item_ids:
                if item.product_tmpl_id.id == self.product_id.id:
                    self.type = 'porcentaje'
                    self.code = item.percent_price



class AgreementLineType(models.Model):
    _name = 'agreement.line.type'

    name = fields.Char(required=True, string='Name')
    code = fields.Char(required=True, string='Code')

class AgreementL10nCl(models.Model):
    _name = 'agreement.l10ncl'

    name = fields.Char(required=True, string='Name')
    code = fields.Char(required=True, string='Code')

class PenaltyType(models.Model):
    _name = 'penalty.type'

    name = fields.Char(required=True, string='Name')

class motivoCancel(models.Model):
    _name = 'motivo.cancel'

    name = fields.Char(required=True, string='Nombre')

class LogAdminLine(models.Model):
    _name = 'log.admin.line'
    _order = 'id asc'

    name = fields.Many2one(
        "res.users", string="Administrador de linea Contrato Maihue", track_visibility="onchange")
    user_id = fields.Many2one(
        "res.users", string="Responsable", track_visibility="onchange")
    agreement_line_id = fields.Many2one(
        comodel_name='agreement.line', string='Linea de Contrato', ondelete='cascade',
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

