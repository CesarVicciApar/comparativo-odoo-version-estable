# -*- coding: utf-8 -*-
# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
import werkzeug
import datetime
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.depends('partner_id', 'agreement_line_ids')
    def _compute_means(self):
        means_ids = []
        #capabilities_ids = []
        if self.partner_id and self.agreement_line_ids:
            if self.partner_id.means_ids:
                for means in self.partner_id.means_ids:
                    if means.id not in means_ids:
                        means_ids.append(means.id)
            if self.agreement_line_ids.means_ids:
                for meansL in self.agreement_line_ids.means_ids:
                    if meansL.id not in means_ids:
                        means_ids.append(meansL.id)
            if self.agreement_line_ids.product_id.means_ids:
                for meansP in self.agreement_line_ids.product_id.means_ids:
                    if meansP.id not in means_ids:
                        means_ids.append(meansP.id)
            #
            # if self.partner_id.capabilities_ids:
            #     for capabilities in self.partner_id.capabilities_ids:
            #         if capabilities.id not in capabilities_ids:
            #             capabilities_ids.append(capabilities.id)
            # if self.agreement_line_ids.capabilities_ids:
            #     for capabilitiesL in self.agreement_line_ids.capabilities_ids:
            #         if capabilitiesL.id not in capabilities_ids:
            #             capabilities_ids.append(capabilitiesL.id)
            # if self.agreement_line_ids.product_id.capabilities_ids:
            #     for capabilitiesP in self.agreement_line_ids.product_id.capabilities_ids:
            #         if capabilitiesP.id not in capabilities_ids:
            #             capabilities_ids.append(capabilitiesP.id)
            #means_ids.append(self.partner_id.means_ids)
            #means_ids.append(self.agreement_line_ids.means_ids)
            #means_ids.append(self.agreement_line_ids.product_id.means_ids)
            # capabilities_ids.append(self.partner_id.capabilities_ids)
            # capabilities_ids.append(self.agreement_line_ids.capabilities_ids)
            # capabilities_ids.append(self.agreement_line_ids.product_id.capabilities_ids)
        if means_ids != []:
            self.means_ids = means_ids
        else:
            self.means_ids = False
        # if capabilities_ids != []:
        #     self.capabilities_ids = capabilities_ids
        # else:
        #     self.capabilities_ids = ''

    @api.depends('partner_id', 'agreement_line_ids')
    def _compute_capabilities(self):
        # means_ids = []
        capabilities_ids = []
        if self.partner_id and self.agreement_line_ids:
        #     if self.partner_id.means_ids:
        #         for means in self.partner_id.means_ids:
        #             if means.id not in means_ids:
        #                 means_ids.append(means.id)
        #     if self.agreement_line_ids.means_ids:
        #         for meansL in self.agreement_line_ids.means_ids:
        #             if meansL.id not in means_ids:
        #                 means_ids.append(meansL.id)
        #     if self.agreement_line_ids.product_id.means_ids:
        #         for meansP in self.agreement_line_ids.product_id.means_ids:
        #             if meansP.id not in means_ids:
        #                 means_ids.append(meansP.id)
            #
            if self.partner_id.capabilities_ids:
                for capabilities in self.partner_id.capabilities_ids:
                    if capabilities.id not in capabilities_ids:
                        capabilities_ids.append(capabilities.id)
            if self.agreement_line_ids.capabilities_ids:
                for capabilitiesL in self.agreement_line_ids.capabilities_ids:
                    if capabilitiesL.id not in capabilities_ids:
                        capabilities_ids.append(capabilitiesL.id)
            if self.agreement_line_ids.product_id.capabilities_ids:
                for capabilitiesP in self.agreement_line_ids.product_id.capabilities_ids:
                    if capabilitiesP.id not in capabilities_ids:
                        capabilities_ids.append(capabilitiesP.id)
            # means_ids.append(self.partner_id.means_ids)
            # means_ids.append(self.agreement_line_ids.means_ids)
            # means_ids.append(self.agreement_line_ids.product_id.means_ids)
            # capabilities_ids.append(self.partner_id.capabilities_ids)
            # capabilities_ids.append(self.agreement_line_ids.capabilities_ids)
            # capabilities_ids.append(self.agreement_line_ids.product_id.capabilities_ids)
        # if means_ids != []:
        #     self.means_ids = means_ids
        # else:
        #     self.means_ids = ''
        if capabilities_ids != []:
            self.capabilities_ids = capabilities_ids
        else:
            self.capabilities_ids = False

    #relacion linea ticket-task
    project_task_line_ids = fields.One2many('project.task.line', 'helpdesk_ticket_id')
    service_order_ids = fields.One2many("project.task", 'helpdesk_ticket_id', string="Orden de Servicio")


    # add new fields
    #unificacion modulo 'custom_parent_id_ticket
    ticket_id = fields.One2many('helpdesk.ticket', 'ticket_ids')
    ticket_ids = fields.Many2one('helpdesk.ticket', 'ticket_id')

    # unificacion modulo 'custom_vista_lista_ticket_helpdesk'
    instalador_ticket = fields.Many2one('res.users', ondelete='set null', string="instalador", select=True,
                                        help="selecciona el usuario instalador")
    agreement_id = fields.Many2one('agreement', string='Contrato', required=False, ondelete='cascade', index=True,
                               copy=False)

    means_ids = fields.Many2many('means', string="Recursos", track_visibility="onchange", compute=_compute_means)
    capabilities_ids = fields.Many2many('capabilities', string="Capacidades", track_visibility="onchange", compute=_compute_capabilities)
    #means_ids = fields.Many2many('means', string="Recursos") #, compute=_compute_means_capabilities
    #capabilities_ids = fields.Many2many('capabilities', string="Capacidades")

    #unificacion modulo 'custom_subcategoria_ticket_helpdesk
    # crear subcategoria que prele de categoria and parent_id

    tag_ids = fields.Many2many('crm.tag', 'crm_lead_tag_rel', 'lead_id', 'tag_id', string='Etiquetas', help="Classify and analyze your lead/opportunity categories like: Training, Service")
    #categoria_maihue_id = fields.Many2one('categoria.maihue', track_visibility="onchange")
    categoria_maihue_id = fields.Many2one('helpdesk.tag', string='Categoria Maihue', track_visibility="onchange")
    subcategoria_maihue_id = fields.Many2one('subcategoria.maihue', string='Sub-Categoria Maihue', track_visibility="onchange")

    #fecha de elaboracion de ticket

    fecha_registro_ticket = fields.Date(
        string='Fecha registro Ticket',
        default=fields.Date.context_today)
    fecha_proyectada = fields.Date(
        string='Fecha Mantencion Proyectada')
    fecha_estimada = fields.Date(
        string='Fecha Estimada')
    fecha_agendada = fields.Date(
        string='Fecha Agendada')

    #crear one2many que apunte a la linea contrato
    agreement_line_ids = fields.Many2one('agreement.line', track_visibility="onchange", string="Linea de Contrato")
    fecha_age_prog = fields.Date("Fecha Estimada")
    agreement_line_keys = fields.Many2one(
        related="agreement_line_ids.agreement_line_keys",
        string="Número de Serie",
        # copy=True,
        track_visibility='onchange')
    slopes_same_ticket = fields.Many2many('helpdesk.ticket', 'slopes_same_tick_rel', 'parent_id',
                                          'ticket_id',
                                          string='Otros Pendientes Mismo Ticket')
    partner_contact_id = fields.Many2one(
        related="agreement_line_ids.partner_contact_id",
        string="Dirección de instalación",
        # copy=True,
        track_visibility='onchange')
    required_asistencia = fields.Boolean(string='Requerido')
    required_asignado = fields.Boolean(string='Requerido')
    required_instalador = fields.Boolean(string='Requerido')
    required_tipo = fields.Boolean(string='Requerido')
    required_categoria = fields.Boolean(string='Requerido')
    required_subcategoria = fields.Boolean(string='Requerido')
    required_prioridad = fields.Boolean(string='Requerido')
    required_ticket_padre = fields.Boolean(string='Requerido')
    required_pendientes = fields.Boolean(string='Requerido')
    required_etiquetas = fields.Boolean(string='Requerido')
    required_fecha = fields.Boolean(string='Requerido')
    required_cliente = fields.Boolean(string='Requerido')
    required_contrato = fields.Boolean(string='Requerido')
    required_linea_contrato = fields.Boolean(string='Requerido')
    required_dir_instala = fields.Boolean(string='Requerido')
    required_fecha_estimada = fields.Boolean(string='Requerido')
    required_serie = fields.Boolean(string='Requerido')
    required_nombre_cliente = fields.Boolean(string='Requerido')
    required_correo = fields.Boolean(string='Requerido')
    required_tlfono = fields.Boolean(string='Requerido')
    required_correocc = fields.Boolean(string='Requerido')
    invisible_asistencia = fields.Boolean(string='Invisible')
    invisible_asignado = fields.Boolean(string='Invisible')
    invisible_instalador = fields.Boolean(string='Invisible')
    invisible_tipo = fields.Boolean(string='Invisible')
    invisible_categoria = fields.Boolean(string='Invisible')
    invisible_subcategoria = fields.Boolean(string='Invisible')
    invisible_prioridad = fields.Boolean(string='Invisible')
    invisible_ticket_padre = fields.Boolean(string='Invisible')
    invisible_pendientes = fields.Boolean(string='Invisible')
    invisible_etiquetas = fields.Boolean(string='Invisible')
    invisible_fecha = fields.Boolean(string='Invisible')
    invisible_cliente = fields.Boolean(string='Invisible')
    invisible_contrato = fields.Boolean(string='Invisible')
    invisible_linea_contrato = fields.Boolean(string='Invisible')
    invisible_dir_instala = fields.Boolean(string='Invisible')
    invisible_fecha_estimada = fields.Boolean(string='Invisible')
    invisible_serie = fields.Boolean(string='Invisible')
    invisible_nombre_cliente = fields.Boolean(string='Invisible')
    invisible_correo = fields.Boolean(string='Invisible')
    invisible_tlfono = fields.Boolean(string='Invisible')
    invisible_correocc = fields.Boolean(string='Invisible')
    readonly_asistencia = fields.Boolean(related='categoria_maihue_id.readonly_asistencia', string='Readonly')
    readonly_asignado = fields.Boolean(related='categoria_maihue_id.readonly_asignado', string='Readonly')
    readonly_instalador = fields.Boolean(related='categoria_maihue_id.readonly_instalador', string='Readonly')
    readonly_tipo = fields.Boolean(related='categoria_maihue_id.readonly_tipo', string='Readonly')
    readonly_categoria = fields.Boolean(related='categoria_maihue_id.readonly_categoria', string='Readonly')
    readonly_subcategoria = fields.Boolean(related='categoria_maihue_id.readonly_subcategoria', string='Readonly')
    readonly_prioridad = fields.Boolean(related='categoria_maihue_id.readonly_prioridad', string='Readonly')
    readonly_ticket_padre = fields.Boolean(related='categoria_maihue_id.readonly_ticket_padre', string='Readonly')
    readonly_pendientes = fields.Boolean(related='categoria_maihue_id.readonly_pendientes', string='Readonly')
    readonly_etiquetas = fields.Boolean(related='categoria_maihue_id.readonly_etiquetas', string='Readonly')
    readonly_fecha = fields.Boolean(related='categoria_maihue_id.readonly_fecha', string='Readonly')
    readonly_cliente = fields.Boolean(related='categoria_maihue_id.readonly_cliente', string='Readonly')
    readonly_contrato = fields.Boolean(related='categoria_maihue_id.readonly_contrato', string='Readonly')
    readonly_linea_contrato = fields.Boolean(related='categoria_maihue_id.readonly_linea_contrato', string='Readonly')
    readonly_dir_instala = fields.Boolean(related='categoria_maihue_id.readonly_dir_instala', string='Readonly')
    readonly_fecha_estimada = fields.Boolean(related='categoria_maihue_id.readonly_fecha_estimada', string='Readonly')
    readonly_serie = fields.Boolean(related='categoria_maihue_id.readonly_serie', string='Readonly')
    readonly_nombre_cliente = fields.Boolean(related='categoria_maihue_id.readonly_nombre_cliente', string='Readonly')
    readonly_correo = fields.Boolean(related='categoria_maihue_id.readonly_correo', string='Readonly')
    readonly_tlfono = fields.Boolean(related='categoria_maihue_id.readonly_tlfono', string='Readonly')
    readonly_correocc = fields.Boolean(related='categoria_maihue_id.readonly_correocc', string='Readonly')

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id.is_close:
            for service_order in self.service_order_ids:
                if service_order.stage_id.name == 'Hecho':
                    continue
                else:
                    raise ValidationError(_(
                        'No se puede cerrar, aun existen ordenes de servicio abiertas'))
                jamie = 1

    @api.model_create_multi
    def create(self, value_list):
        res = {}
        categ = ''
        #seq = str(self.env['ir.sequence'].next_by_code('helpdesk_seq'))
        if 'categoria_maihue_id' in value_list[0] and 'instalation' not in self._context:
            if value_list[0]['categoria_maihue_id']:
                categ = value_list[0]['categoria_maihue_id']
                categ = self.env['helpdesk.tag'].search([('id', '=', categ)],
                                                                     limit=1)
        #part = value_list[0]['partner_name']
            part = self.env['res.partner'].search([('id', '=', value_list[0]['partner_id'])], limit=1,
                                                                      order='id')
            if not value_list[0]['categoria_maihue_id']:
                raise UserError(
                    'No existe categoria_maihue_id')
            if not part.name:
                raise UserError(
                    'No existe part.name')

            value_list[0]['name'] = str(categ.name) + ' ' + str(part.name) + ' '
            res = super(HelpdeskTicket, self).create(value_list)
            res.write({'name': str(res.name) + '/'+ str(res.id)})
        if 'categoria_maihue_id' in res and 'instalation' not in self._context:
            invite = self.env['survey.invite']
            categoria_maihue_id = res.categoria_maihue_id
            for services in res.categoria_maihue_id.categoria_line:
                products_created = []  # valida que no duplique los productos
                url_invite = werkzeug.urls.url_join(services.project_template_id.survey_id.get_base_url(), services.project_template_id.survey_id.get_start_url()) if invite.survey_id else False
                #url_invite = invite._compute_survey_start_url(services.project_template_id.survey_id.id)
                correla = res.name.split("/")
                order_lineM = self.env['project.task'].create({
                    'name': str(res.agreement_line_ids.name) + '-' + str(correla[1]) + '-' + str(self.env['ir.sequence'].next_by_code('task_seq')), #+ services.project_template_ids.product_id.name,
                    'partner_id': res.agreement_id.partner_id.id,
                    'helpdesk_ticket_id': res.id,
                    #'stage_id': 4,
                    'fsm_done': False,
                    'project_id': services.project_id.id,
                    'agreement_id': res.agreement_id.id,
                    'agreement_line_id': res.agreement_line_ids.id,
                    'formulario': url_invite,
                    'survey_id': services.project_template_id.survey_id.id,
                    'type_transfer_equipment': services.project_template_id.type_transfer_equipment,
                    'l10n_cl_delivery_guide_reason': services.project_template_id.l10n_cl_delivery_guide_reason,
                    'task_template_id': services.project_template_id.id,
                })
                for products in services.project_template_id.product_line:
                    product_id = self.env['product.product'].search([('product_tmpl_id', '=', products.product_id.id)],
                                                             limit=1)
                    product_line = self.env['project.task.product'].create({
                            'product_id': product_id.id,
                            'description': products.product_id.name,
                            'planned_qty': products.planned_qty,
                            'product_uom': products.product_id.uom_id.id,
                            'time_spent': products.time_spent,
                            'task_id': order_lineM.id,
                        })
                if services.project_template_id.product_related:
                    for x in res.agreement_line_ids.product_id.product_related_ids:
                        if x.is_principal:
                            # if x.product_id != res.agreement_line_ids.product_principal:
                            #     continue
                            # if x.product_id.id in products_created:
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
                        products_created.append(order_lineM_l.product_id.id)
                if services.project_template_id.product_maintence:
                    if res.agreement_line_ids.maintenance_id:
                        todayM = res.agreement_line_ids.start_date  # datetime.now().date()
                        period_m = datetime.now().date()
                        # period_m = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + '01'
                        # period_m = datetime.strptime(period_date, '%Y-%m-%d')
                        meses = 0
                        mesesM = 0
                        numeracionM = 1
                        mj2 = []
                        num = 0
                        for j in res.agreement_line_ids.maintenance_id.maintenance_m_line:
                            if j.number not in mj2:
                                mj2.append(j.number)
                        while (mesesM < 43):
                            name_list = []
                            mj2 = sorted(mj2, reverse=False)
                            for i in mj2:
                                if datetime.strptime(str(period_m)[0:10], '%Y-%m-%d').date() > todayM:
                                    mesesM = mesesM
                                else:
                                    mesesM = mesesM + int(mj2[0])
                                meses = meses + int(mj2[0])
                                if mesesM >= 36:
                                    break
                                todayM = todayM + relativedelta(months=int(mj2[0]))
                                num = i
                                for x in res.agreement_line_ids.maintenance_id.maintenance_m_line:
                                    if x.number <= num:
                                        if x.type not in name_list:
                                            name_list.append(x.type)
                                        order_lineM_l = self.env['project.task.product'].create({
                                            'product_id': x.product_id.id,
                                            'description': x.product_id.name,
                                            'planned_qty': x.quantity,
                                            'product_uom': x.product_id.uom_id.id,
                                            'time_spent': x.time_spent,
                                            'task_id': order_lineM.id,
                                        })
                                name_new = ''
                                for n in name_list:
                                    name_new = name_new + ' ' + n
                                # ticket_man.write({'name': ticket_man.name + ' ' + name_new})
                                # order_lineM_l.write({'name': order_lineM.name + ' ' + name_new})
                                numeracionM = numeracionM + 1
                if services.project_template_id.product_principal:
                    for x in res.agreement_line_ids.product_id.product_related_ids:
                        if x.is_principal:
                            if x.product_id != res.agreement_line_ids.product_principal:
                                continue
                            if x.product_id.id in products_created:
                                continue
                            if x.product_id == res.agreement_line_ids.product_principal:
                                order_lineM_l = self.env['project.task.product'].create({
                                    'product_id': x.product_id.id,
                                    'description': x.name,
                                    'planned_qty': x.qty,
                                    'product_uom': x.product_id.uom_id.id,
                                    'time_spent': x.time_spent,
                                    'task_id': order_lineM.id,
                                    'is_principal': x.is_principal,
                                })
                            products_created.append(order_lineM_l.product_id.id)
            jamie = 1
        else:
            res = super(HelpdeskTicket, self).create(value_list)
        return res

class HelpdeskTag(models.Model):
    _inherit = 'helpdesk.tag'

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
    instalation = fields.Boolean('Para el uso de Instalación', default=False)
    mantention = fields.Boolean('Para uso de Mantención', default=False)
    campos_ticket_ids = fields.One2many('campos.ticket', 'helpdesk_tag_id')
    required_asistencia = fields.Boolean(string='Requerido', default=False)
    required_asignado = fields.Boolean(string='Requerido', default=False)
    required_instalador = fields.Boolean(string='Requerido', default=False)
    required_tipo = fields.Boolean(string='Requerido', default=False)
    required_categoria = fields.Boolean(string='Requerido', default=False)
    required_subcategoria = fields.Boolean(string='Requerido', default=False)
    required_prioridad = fields.Boolean(string='Requerido', default=False)
    required_ticket_padre = fields.Boolean(string='Requerido', default=False)
    required_pendientes = fields.Boolean(string='Requerido', default=False)
    required_etiquetas = fields.Boolean(string='Requerido', default=False)
    required_fecha = fields.Boolean(string='Requerido', default=False)
    required_cliente = fields.Boolean(string='Requerido', default=False)
    required_contrato = fields.Boolean(string='Requerido', default=False)
    required_linea_contrato = fields.Boolean(string='Requerido', default=False)
    required_dir_instala = fields.Boolean(string='Requerido', default=False)
    required_fecha_estimada = fields.Boolean(string='Requerido', default=False)
    required_serie = fields.Boolean(string='Requerido', default=False)
    required_nombre_cliente = fields.Boolean(string='Requerido', default=False)
    required_correo = fields.Boolean(string='Requerido', default=False)
    required_tlfono = fields.Boolean(string='Requerido', default=False)
    required_correocc = fields.Boolean(string='Requerido', default=False)
    invisible_asistencia = fields.Boolean(string='Invisible', default=False)
    invisible_asignado = fields.Boolean(string='Invisible', default=False)
    invisible_instalador = fields.Boolean(string='Invisible', default=False)
    invisible_tipo = fields.Boolean(string='Invisible', default=False)
    invisible_categoria = fields.Boolean(string='Invisible', default=False)
    invisible_subcategoria = fields.Boolean(string='Invisible', default=False)
    invisible_prioridad = fields.Boolean(string='Invisible', default=False)
    invisible_ticket_padre = fields.Boolean(string='Invisible', default=False)
    invisible_pendientes = fields.Boolean(string='Invisible', default=False)
    invisible_etiquetas = fields.Boolean(string='Invisible', default=False)
    invisible_fecha = fields.Boolean(string='Invisible', default=False)
    invisible_cliente = fields.Boolean(string='Invisible', default=False)
    invisible_contrato = fields.Boolean(string='Invisible', default=False)
    invisible_linea_contrato = fields.Boolean(string='Invisible', default=False)
    invisible_dir_instala = fields.Boolean(string='Invisible', default=False)
    invisible_fecha_estimada = fields.Boolean(string='Invisible', default=False)
    invisible_serie = fields.Boolean(string='Invisible', default=False)
    invisible_nombre_cliente = fields.Boolean(string='Invisible', default=False)
    invisible_correo = fields.Boolean(string='Invisible', default=False)
    invisible_tlfono = fields.Boolean(string='Invisible', default=False)
    invisible_correocc = fields.Boolean(string='Invisible', default=False)
    readonly_asistencia = fields.Boolean(string='No editable', default=False)
    readonly_asignado = fields.Boolean(string='No editable', default=False)
    readonly_instalador = fields.Boolean(string='No editable', default=False)
    readonly_tipo = fields.Boolean(string='No editable', default=False)
    readonly_categoria = fields.Boolean(string='No editable', default=False)
    readonly_subcategoria = fields.Boolean(string='No editable', default=False)
    readonly_prioridad = fields.Boolean(string='No editable', default=False)
    readonly_ticket_padre = fields.Boolean(string='No editable', default=False)
    readonly_pendientes = fields.Boolean(string='No editable', default=False)
    readonly_etiquetas = fields.Boolean(string='No editable', default=False)
    readonly_fecha = fields.Boolean(string='No editable', default=False)
    readonly_cliente = fields.Boolean(string='No editable', default=False)
    readonly_contrato = fields.Boolean(string='No editable', default=False)
    readonly_linea_contrato = fields.Boolean(string='No editable', default=False)
    readonly_dir_instala = fields.Boolean(string='No editable', default=False)
    readonly_fecha_estimada = fields.Boolean(string='No editable', default=False)
    readonly_serie = fields.Boolean(string='No editable', default=False)
    readonly_nombre_cliente = fields.Boolean(string='No editable', default=False)
    readonly_correo = fields.Boolean(string='No editable', default=False)
    readonly_tlfono = fields.Boolean(string='No editable', default=False)
    readonly_correocc = fields.Boolean(string='No editable', default=False)
    readonly_asistencia = fields.Boolean(string='No editable', default=False)
    readonly_asignado = fields.Boolean(string='No editable', default=False)
    readonly_instalador = fields.Boolean(string='No editable', default=False)
    readonly_tipo = fields.Boolean(string='No editable', default=False)
    readonly_categoria = fields.Boolean(string='No editable', default=False)
    readonly_subcategoria = fields.Boolean(string='No editable', default=False)
    readonly_prioridad = fields.Boolean(string='No editable', default=False)
    readonly_ticket_padre = fields.Boolean(string='No editable', default=False)
    readonly_pendientes = fields.Boolean(string='No editable', default=False)
    readonly_etiquetas = fields.Boolean(string='No editable', default=False)
    readonly_fecha = fields.Boolean(string='No editable', default=False)
    readonly_cliente = fields.Boolean(string='No editable', default=False)
    readonly_contrato = fields.Boolean(string='No editable', default=False)
    readonly_linea_contrato = fields.Boolean(string='No editable', default=False)
    readonly_dir_instala = fields.Boolean(string='No editable', default=False)
    readonly_fecha_estimada = fields.Boolean(string='No editable', default=False)
    readonly_serie = fields.Boolean(string='No editable', default=False)
    readonly_nombre_cliente = fields.Boolean(string='No editable', default=False)
    readonly_correo = fields.Boolean(string='No editable', default=False)
    readonly_tlfono = fields.Boolean(string='No editable', default=False)
    readonly_correocc = fields.Boolean(string='No editable', default=False)
    stage_id_asistencia = fields.Many2many('helpdesk.stage', 'helpdesk_stage_asistencia_rel', 'asistencia_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_asignado = fields.Many2many('helpdesk.stage', 'helpdesk_stage_asignado_rel', 'asignado_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_instalador = fields.Many2many('helpdesk.stage', 'helpdesk_stage_instalador_rel', 'instalador_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_tipo = fields.Many2many('helpdesk.stage', 'helpdesk_stage_tipo_rel', 'tipo_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_categoria = fields.Many2many('helpdesk.stage', 'helpdesk_stage_categoria_rel', 'categoria_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_subcategoria = fields.Many2many('helpdesk.stage', 'helpdesk_stage_subcategoria_rel', 'subcategoria_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_prioridad = fields.Many2many('helpdesk.stage', 'helpdesk_stage_prioridad_rel', 'prioridad_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_ticket_padre = fields.Many2many('helpdesk.stage', 'helpdesk_stage_ticket_padre_rel', 'ticket_padre_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_pendientes = fields.Many2many('helpdesk.stage', 'helpdesk_stage_pendientes_rel', 'pendientes_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_etiquetas = fields.Many2many('helpdesk.stage', 'helpdesk_stage_etiquetas_rel', 'etiquetas_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_fecha = fields.Many2many('helpdesk.stage', 'helpdesk_stage_fecha_rel', 'fecha_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_cliente = fields.Many2many('helpdesk.stage', 'helpdesk_stage_cliente_rel', 'cliente_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_contrato = fields.Many2many('helpdesk.stage', 'helpdesk_stage_contrato_rel', 'contrato_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_linea_contrato = fields.Many2many('helpdesk.stage', 'helpdesk_stage_linea_contrato_rel', 'linea_contrato_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_dir_instala = fields.Many2many('helpdesk.stage', 'helpdesk_stage_dir_instala_rel', 'dir_instala_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_fecha_estimada = fields.Many2many('helpdesk.stage', 'helpdesk_stage_fecha_estimada_rel', 'fecha_estimada_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_serie = fields.Many2many('helpdesk.stage', 'helpdesk_stage_serie_rel', 'serie_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_nombre_cliente = fields.Many2many('helpdesk.stage', 'helpdesk_stage_nombre_cliente_rel', 'nombre_cliente_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_correo = fields.Many2many('helpdesk.stage', 'helpdesk_stage_correo_rel', 'correo_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_tlfono = fields.Many2many('helpdesk.stage', 'helpdesk_stage_tlfono_rel', 'tlfono_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')
    stage_id_correocc = fields.Many2many('helpdesk.stage', 'helpdesk_stage_correocc_rel', 'correocc_id',
                                           'stage_id', track_visibility="onchange", store=True,
                                           string='Estados')

    @api.model_create_multi
    def create(self, value_list):
        # Operar el create para saber si existe otra plantilla de instalation o mantention
        if value_list[0]['instalation']:
            exist_inst = self.env['helpdesk.tag'].search([('instalation', '=', True)], limit=1, order='id').id
            if exist_inst:
                raise UserError(
                    'Ya existe una categoria de instalacion')
        if value_list[0]['mantention']:
            exist_man = self.env['helpdesk.tag'].search([('mantention', '=', True)], limit=1, order='id').id
            if exist_man:
                raise UserError(
                    'Ya existe una categoria de Mantencion')
        return super(HelpdeskTag, self).create(value_list)

    def write(self, vals):
        if 'instalation' in vals:
            if vals['instalation']:
                exist_inst = self.env['helpdesk.tag'].search([('instalation', '=', True)], limit=1,
                                                                      order='id').id
                if exist_inst:
                    raise UserError(
                        'Ya existe una categoria de instalacion')
        if 'mantention' in vals:
            if vals['mantention']:
                exist_man = self.env['helpdesk.tag'].search([('mantention', '=', True)], limit=1,
                                                                      order='id').id
                if exist_man:
                    raise UserError(
                        'Ya existe una categoria de Mantencion')

        return super(HelpdeskTag, self).write(vals)

class ProjectTaskLine(models.Model):
    _name = 'project.task.line'
    _description = "Project Task"

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket')

    project_task_id = fields.Many2one('project.task', string='Tareas')

class SubcategoriaMaihue(models.Model):
    _name = 'subcategoria.maihue'

    name = fields.Char('Subcategoria')

    # categoria_maihue_id = fields.Many2one('categoria.maihue', track_visibility="onchange",
    #                                       string="Categoria", required=True)
    categoria_maihue_id = fields.Many2one('helpdesk.tag', string='Categoria Maihue', track_visibility="onchange", required=True)

class CategoriaMaihueTemplate(models.Model):
    _name = 'categoria.maihue.template'
    _rec_name = 'project_template_id'
    _description = "Linea para las plantillas utilizadas para orden de servicio externo"

    project_template_id = fields.Many2one('project.task.template', string='Plantilla')
    categoria_id = fields.Many2one('helpdesk.tag', string='Categ Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True, domain="[('is_fsm', '=', True)]")

    @api.onchange('project_template_id')
    def onchange_project_template_id(self):
        if self.project_template_id:
            self.project_id = self.project_template_id.project_id


class ProjectTaskTemplate(models.Model):
    _name = "project.task.template"
    _inherit = ['mail.thread', 'image.mixin']
    _description = "Plantillas para las ordenes de servicio"

    name = fields.Char('Título', required=True)
    helpdesk_ticket_id = fields.Many2one("helpdesk.ticket", string="Ticket")
    subcateg_id = fields.Many2one('subcategoria.maihue', string='SubCateg Reference', required=False, ondelete='set null', index=True)
    # slopes_same_ticket = fields.Many2many('project.task', 'slopes_same_ticket_rel', 'parent_id',
    #                                       'task_id_id',
    #                                       string='Otros Pendientes Mismo Ticket')
    product_line = fields.One2many('project.template.product', 'task_id', string='Product Lines', copy=True, auto_join=True)
    user_id = fields.Many2one('res.users', string='Asignada a', required=False) # , default=lambda self: self.env.user
    project_id = fields.Many2one('project.project', string='Proyecto',
                                 required=True, domain="[('company_id', '=', company_id)]")
    description = fields.Text("Descripción")
    survey_id = fields.Many2one('survey.survey', string='Encuesta definida', required=False,
                                  ondelete='set null', index=True)
    type_transfer_equipment = fields.Selection(string='Tipo de Ticket', selection=[('install', 'Instalacion'), (
    'uninstall', 'Desinstalacion Termino Contrato'), ('uninstall_repair', 'Desinstalacion Incidencia'),
                                                                                   ('change', 'Cambio de Domicilio'),
                                                                                   ('install_uninstall', 'Instalacion y Desinstalacion'),
                                                                                   ('inci', 'Incidencia'), ])
    product_related = fields.Boolean(string='Productos Relacionados', default=False)
    product_maintence = fields.Boolean(string='Productos Mantencion', default=False)
    product_principal = fields.Boolean(string='Producto Principal', default=False)
    l10n_cl_delivery_guide_reason = fields.Selection([
        ('1', '1. Operación constituye venta'),
        ('2', '2. Ventas por efectuar'),
        ('3', '3. Consignaciones'),
        ('4', '4. Entrega gratuita'),
        ('5', '5. Transferencia interna'),
        ('6', '6. Otras operaciones'),
        ('7', '7. Guia de devolución'),
        ('8', '8. Transferencias por exportaciones'),
        ('9', '9. Ventas de exportación')
    ], string='Razón de la transferencia', default='1')
    btn_asig = fields.Boolean('Boton Asignar Id', default=False)
    btn_desasig = fields.Boolean('Boton Desasignar Id', default=False)
    btn_asig_spp = fields.Boolean('Boton Asignar SPP', default=False)
    btn_desasig_spp = fields.Boolean('Boton Desasignar SPP', default=False)
    instalation = fields.Boolean('Para el uso de Instalación', default=False)
    mantention = fields.Boolean('Para uso de Mantención', default=False)
    perm_edit = fields.Boolean('Permitir editar la dirección de instalación', default=False)
    required_project_id = fields.Boolean(string='Requerido', default=False)
    required_worksheet = fields.Boolean(string='Requerido', default=False)
    required_user = fields.Boolean(string='Requerido', default=False)
    required_slopes = fields.Boolean(string='Requerido', default=False)
    required_formulario = fields.Boolean(string='Requerido', default=False)
    required_survey = fields.Boolean(string='Requerido', default=False)
    required_url = fields.Boolean(string='Requerido', default=False)
    required_contrato = fields.Boolean(string='Requerido', default=False)
    required_linea_contrato = fields.Boolean(string='Requerido', default=False)
    required_visit = fields.Boolean(string='Requerido', default=False)
    required_dir_inst = fields.Boolean(string='Requerido', default=False)
    required_picking = fields.Boolean(string='Requerido', default=False)
    required_admin_maihue = fields.Boolean(string='Requerido', default=False)
    required_cliente = fields.Boolean(string='Requerido', default=False)
    required_tags = fields.Boolean(string='Requerido', default=False)
    required_razon = fields.Boolean(string='Requerido', default=False)
    required_tipo = fields.Boolean(string='Requerido', default=False)
    required_plantilla = fields.Boolean(string='Requerido', default=False)
    required_recurso = fields.Boolean(string='Requerido', default=False)
    required_capacidad = fields.Boolean(string='Requerido', default=False)
    invisible_project_id = fields.Boolean(string='Invisible', default=False)
    invisible_worksheet = fields.Boolean(string='Invisible', default=False)
    invisible_user = fields.Boolean(string='Invisible', default=False)
    invisible_slopes = fields.Boolean(string='Invisible', default=False)
    invisible_formulario = fields.Boolean(string='Invisible', default=False)
    invisible_survey = fields.Boolean(string='Invisible', default=False)
    invisible_url = fields.Boolean(string='Invisible', default=False)
    invisible_contrato = fields.Boolean(string='Invisible', default=False)
    invisible_linea_contrato = fields.Boolean(string='Invisible', default=False)
    invisible_visit = fields.Boolean(string='Invisible', default=False)
    invisible_dir_inst = fields.Boolean(string='Invisible', default=False)
    invisible_picking = fields.Boolean(string='Invisible', default=False)
    invisible_admin_maihue = fields.Boolean(string='Invisible', default=False)
    invisible_cliente = fields.Boolean(string='Invisible', default=False)
    invisible_tags= fields.Boolean(string='Invisible', default=False)
    invisible_razon = fields.Boolean(string='Invisible', default=False)
    invisible_tipo = fields.Boolean(string='Invisible', default=False)
    invisible_plantilla = fields.Boolean(string='Invisible', default=False)
    invisible_recurso = fields.Boolean(string='Invisible', default=False)
    invisible_capacidad = fields.Boolean(string='Invisible', default=False)
    readonly_project_id = fields.Boolean(string='No editable', default=False)
    readonly_worksheet = fields.Boolean(string='No editable', default=False)
    readonly_user = fields.Boolean(string='No editable', default=False)
    readonly_slopes = fields.Boolean(string='No editable', default=False)
    readonly_formulario = fields.Boolean(string='No editable', default=False)
    readonly_survey = fields.Boolean(string='No editable', default=False)
    readonly_url = fields.Boolean(string='No editable', default=False)
    readonly_contrato = fields.Boolean(string='No editable', default=False)
    readonly_linea_contrato = fields.Boolean(string='No editable', default=False)
    readonly_visit = fields.Boolean(string='No editable', default=False)
    readonly_dir_inst = fields.Boolean(string='No editable', default=False)
    readonly_picking = fields.Boolean(string='No editable', default=False)
    readonly_admin_maihue = fields.Boolean(string='No editable', default=False)
    readonly_cliente = fields.Boolean(string='No editable', default=False)
    readonly_tags= fields.Boolean(string='No editable', default=False)
    readonly_razon = fields.Boolean(string='No editable', default=False)
    readonly_tipo = fields.Boolean(string='No editable', default=False)
    readonly_plantilla = fields.Boolean(string='No editable', default=False)
    readonly_recurso = fields.Boolean(string='No editable', default=False)
    readonly_capacidad = fields.Boolean(string='No editable', default=False)


    @api.model_create_multi
    def create(self, value_list):
        # Operar el create para saber si existe otra plantilla de instalation o mantention
        if value_list[0]['instalation']:
            exist_inst = self.env['project.task.template'].search([('instalation', '=', True)], limit=1, order='id').id
            if exist_inst:
                raise UserError(
                    'Ya existe una plantilla de instalacion')
        if value_list[0]['mantention']:
            exist_man = self.env['project.task.template'].search([('mantention', '=', True)], limit=1, order='id').id
            if exist_man:
                raise UserError(
                    'Ya existe una plantilla de Mantencion')
        return super(ProjectTaskTemplate, self).create(value_list)

    def write(self, vals):
        if 'instalation' in vals:
            if vals['instalation']:
                exist_inst = self.env['project.task.template'].search([('instalation', '=', True)], limit=1,
                                                                      order='id').id
                if exist_inst:
                    raise UserError(
                        'Ya existe una plantilla de instalacion')
        if 'mantention' in vals:
            if vals['mantention']:
                exist_man = self.env['project.task.template'].search([('mantention', '=', True)], limit=1,
                                                                      order='id').id
                if exist_man:
                    raise UserError(
                        'Ya existe una plantilla de Mantencion')

        return super(ProjectTaskTemplate, self).write(vals)

class ProjectTemplateProduct(models.Model):
    _name = 'project.template.product'
    _rec_name = 'product_id'
    _description = "Linea para los productos utilizados en orden de servicio externo"

    def _get_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    def _get_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    product_id = fields.Many2one('product.template', string='Producto')
    description = fields.Char('Descripcion')
    uom_id = fields.Many2one('uom.uom',
        default=_get_uom_id, string='Unit of Measure', required=True)
    planned_qty = fields.Float('Cantidad Planificada')
    product_uom = fields.Many2one('uom.uom', default=_get_product_uom_id, string='Unidad de Medida')
    time_spent = fields.Float('Tiempo/Horas', precision_digits=2)
    real_qty = fields.Float('Cantidad Real')
    charge = fields.Boolean('Cobrar', default=False)
    task_id = fields.Many2one('project.task.template', string='Task Reference', required=True, ondelete='cascade', index=True,
                               copy=False)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.description = self.product_id.name
        self.uom_id = self.product_id.uom_id.id

class ProjectTaskProduct(models.Model):
    _name = 'project.task.product'
    _rec_name = 'product_id'
    _description = "Linea para los productos utilizados en orden de servicio externo"

    def _get_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    def _get_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    product_id = fields.Many2one('product.product', string='Producto')
    description = fields.Char('Descripcion')
    planned_qty = fields.Float('Cantidad Planificada')
    product_uom = fields.Many2one('uom.uom', default=_get_product_uom_id, string='Unidad de Medida')
    time_spent = fields.Float('Tiempo/Horas', precision_digits=2)
    real_qty = fields.Float('Cantidad Real')
    uom_id = fields.Many2one('uom.uom',
                             default=_get_uom_id, string='Unit of Measure', required=False)
    charge = fields.Boolean('Cobrar', default=False)
    task_id = fields.Many2one('project.task', string='Task Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    is_principal = fields.Boolean(string="Principal", default=False)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.description = self.product_id.name
        self.uom_id = self.product_id.uom_id.id

    def write(self, vals):
        if 'product_id' in vals:
            jamie = vals['product_id']
            product = self.env['project.task.product'].search(
                [('id', '=', self.id)])
            if product.is_principal:
                product_principal = self.env['product.product'].search(
                    [('id', '=', vals['product_id'])])
                self.task_id.agreement_line_id.write({'product_principal': product_principal.id})

        return super(ProjectTaskProduct, self).write(vals)

class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.depends('survey_id.access_token')
    def _compute_survey_start_url(self):
        for invite in self:
            invite.survey_start_url = werkzeug.urls.url_join(invite.survey_id.get_base_url(),
                                                             invite.survey_id.get_start_url()) if invite.survey_id else False

    @api.model
    def compute_btn_asig(self):
        self.btn_asig = False
        if self.task_template_id:
            self.btn_asig = self.task_template_id.btn_asig
        return self.btn_asig

    @api.model
    def compute_btn_desasig(self):
        self.btn_desasig = False
        if self.task_template_id:
            self.btn_desasig = self.task_template_id.btn_desasig
        return self.btn_desasig

    @api.model
    def compute_btn_asig_spp(self):
        self.btn_asig_spp = False
        if self.task_template_id:
            self.btn_asig_spp = self.task_template_id.btn_asig_spp
        return self.btn_asig_spp

    @api.model
    def compute_btn_desasig_spp(self):
        self.btn_desasig_spp = False
        if self.task_template_id:
            self.btn_desasig_spp = self.task_template_id.btn_desasig_spp
        return self.btn_desasig_spp

    @api.depends('product_line')
    def _compute_totals(self):
        for order in self:
            total = 0.0
            for line in order.product_line:
                total = total + line.time_spent
            order.totals = total
        #return self.totals

    @api.depends('task_line')
    def _compute_total_visit(self):
        for order in self:
            total = 0.0
            for line in order.task_line:
                total = total + line.task.totals
            order.totals_visit = total
        #return self.totals_visit

    @api.depends('planned_visit_end', 'planned_visit_begin')
    def _compute_planned_visit_end(self):
        for order in self:
            if order.father:
                if order.planned_visit_begin:
                    num = str(order.totals_visit).split(".") # %H:%M:%S
                    minutos = 60 / 100 * int(num[1])
                    order.planned_visit_end = order.planned_visit_begin + relativedelta(hours=order.totals_visit)#, minutes=minutos)
        #return self.planned_visit_end

    # @api.onchange('planned_visit_begin')
    # def _onchange_planned_visit_end(self):
    #     if self.env.context.get('visita'):
    #         if self.planned_visit_begin:
    #             num = str(self.totals_visit).split(".")  # %H:%M:%S
    #             minutos = 60 / 100 * int(num[1])
    #             self.planned_visit_end = self.planned_visit_begin + relativedelta(
    #                 hours=self.totals_visit)  # , minutes=minutos)
    #     return self.planned_visit_end

    @api.onchange('task_line')
    def _onchange_total_visita(self):
        total = 0.0
        for line in self.task_line:
            total = total + line.task.totals
        self.totals_visit = total
        #return self.totals_visit


    @api.depends('partner_id', 'project_id')
    def _get_records(self):
        for rec in self:
            lines = []
            lines_visit = []
            if rec.partner_id and rec.project_id:
                task_obj = rec.env['project.task'].search([('partner_id', '=', rec.partner_id.id), ('project_id', '=', rec.project_id.id), ('visit_id', '=', False), ('stage_id', 'not in', [129, 130])])
                if task_obj:
                    for t in task_obj:
                        if not t.father:
                            vals = (0, 0, {
                                'task_id': t.id,
                                'task': t.id,
                                'helpdesk_ticket_id': t.helpdesk_ticket_id.id or False,
                                #'team_id': t.team_id or False,
                                #'ticket_type_id': t.ticket_type_id or False,
                                'stage_id': t.stage_id.id,
                            })
                            lines.append(vals)
                    if rec.task_line_pen:
                        rec.task_line_pen.unlink()
                    rec.task_line_pen = lines

    @api.depends('partner_id', 'project_id')
    def _get_record(self):
        for rec in self:
            lines = []
            if rec.partner_id and rec.project_id:
                task_obj = rec.env['project.task'].search(
                    [('partner_id', '=', rec.partner_id.id), ('project_id', '=', rec.project_id.id), ('father', '=', True), ('stage_id', 'not in', [129, 130])])
                if task_obj:
                    for t in task_obj:
                        vals = (0, 0, {
                            'task_id': t.id,
                            'task': t.id,
                            'helpdesk_ticket_id': t.helpdesk_ticket_id.id or False,
                            # 'team_id': t.team_id or False,
                            # 'ticket_type_id': t.ticket_type_id or False,
                            'stage_id': t.stage_id.id,
                        })
                        lines.append(vals)
                    if rec.task_visit_agen:
                        rec.task_visit_agen.unlink()
                    rec.task_visit_agen = lines

    helpdesk_ticket_id = fields.Many2one("helpdesk.ticket", string="Helpdesk Ticket", copy=False)
    slopes_same_ticket = fields.Many2many('project.task', 'slopes_same_task_rel', 'parent_id',
                                          'task_id_id',
                                          string='Otros Pendientes Misma Orden')
    product_line = fields.One2many('project.task.product', 'task_id', string='Product Lines', copy=True, auto_join=True)
    project_task_id = fields.Many2one('project.task')
    formulario = fields.Char('Formulario')
    visit_id = fields.Many2one('project.task', string='Visita', index=True)
    father = fields.Boolean('Visita')
    survey_id = fields.Many2one('survey.survey', string='Formulario', required=True)
    survey_start_url = fields.Char('Formulario URL', compute='_compute_survey_start_url')
    visita_id = fields.Many2one('helpdesk.visita', string='Visit Reference', required=False, ondelete='cascade', index=True,
                               copy=False)
    picking_id = fields.Many2one('stock.picking', 'Picking', check_company=True)
    admin_line_id = fields.Many2one('res.users', string='Administrador de Linea Maihue', track_visibility="onchange")
    agreement_id = fields.Many2one(
        "agreement", string="Contrato", ondelete="cascade")
    agreement_line_id = fields.Many2one('agreement.line', string="Linea de contrato")
    # ticket_type_id = fields.Many2one(
    #     "helpdesk.ticket.type",
    #     string="Tipo de ticket",
    #     required=True)
    type_transfer_equipment = fields.Selection(string='Tipo de Ticket', selection=[('install', 'Instalacion'), (
        'uninstall', 'Desinstalacion Termino Contrato'), ('uninstall_repair', 'Desinstalacion Incidencia'),
                                                                                   ('change', 'Cambio de Domicilio'),
                                                                                   ('install_uninstall',
                                                                                    'Instalacion y Desinstalacion'),
                                                                                   ('inci', 'Incidencia'), ])
    l10n_cl_delivery_guide_reason = fields.Selection([
        ('1', '1. Operación constituye venta'),
        ('2', '2. Ventas por efectuar'),
        ('3', '3. Consignaciones'),
        ('4', '4. Entrega gratuita'),
        ('5', '5. Transferencia interna'),
        ('6', '6. Otras operaciones'),
        ('7', '7. Guia de devolución'),
        ('8', '8. Transferencias por exportaciones'),
        ('9', '9. Ventas de exportación')
    ], string='Razón de la transferencia')
    task_template_id = fields.Many2one("project.task.template", string="Plantilla servicio")
    btn_asig = fields.Boolean('Boton Asignar Id', compute=compute_btn_asig)
    btn_desasig = fields.Boolean('Boton Desasignar Id', compute=compute_btn_desasig)
    btn_asig_spp = fields.Boolean('Boton Asignar SPP', compute=compute_btn_asig_spp)
    btn_desasig_spp = fields.Boolean('Boton Desasignar SPP',compute=compute_btn_desasig_spp)
    partner_contact_id = fields.Many2one(
        related="agreement_line_id.partner_contact_id",
        string="Dirección de instalación",
        # copy=True,
        track_visibility='onchange')
    totals = fields.Float(compute='_compute_totals')
    task_line = fields.One2many('project.task.order', 'task_id', string='Lineas de ordenes', copy=True,
                                 auto_join=True)
    task_line_pen = fields.One2many('project.task.order.pen', 'task_id', string='Ordenes de Servicio Pendiente', copy=True,
                                 auto_join=True, compute=_get_records, store=True)
    task_visit_agen = fields.One2many('project.visit.agen', 'task_id', string='Visitas Agendadas', copy=True,
                                 auto_join=True, compute=_get_record, store=True)
    partner_contact = fields.Many2one(
        "res.partner",
        string="Dirección de instalación",
        copy=True,
        track_visibility='onchange',
        domain="[('type', '=', 'delivery'), ('parent_id', '=', partner_id)]",
        help="The primary partner contact (If Applicable).",
        # states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    totals_visit = fields.Float(compute='_compute_total_visit', store=True)
    planned_visit_begin = fields.Datetime("Fecha planificada", tracking=True)
    planned_visit_end = fields.Datetime("Fecha fin", tracking=True, compute='_compute_planned_visit_end', store=True)
    means_ids = fields.Many2many('means', string="Recursos")
    capabilities_ids = fields.Many2many('capabilities', string="Capacidades")
    location = fields.Char(related='agreement_line_id.location', string='Ubicacion')
    zona_comercial = fields.Many2one('zona.comercial', string='Zona Comercial',
                                     track_visibility='onchange')
    zona_domain = fields.Many2many(related='agreement_id.template_agreement_id.zona_domain',
                                   string='Zonas Comerciales')
    partner_contact_change = fields.Many2one(
        "res.partner",
        string="Cambio de Dirección de instalación",
        # copy=True,
        track_visibility='onchange',
        domain="[('type', '=', 'delivery'), ('parent_id', '=', partner_id), ('commune', '=', comuna_id)]",
        help="The primary partner contact (If Applicable).",
        # states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    #change_domain = fields.Many2many("res.partner", string="Direcciones comerciales")
    btn_perm_edit = fields.Boolean(related='task_template_id.perm_edit', string='Perm_edit')
    comuna_id = fields.Many2one('res.country.commune', 'Comuna', track_visibility="onchange")
    comuna_domain = fields.Many2many("res.country.commune", string="Comunas comerciales")
    location_change = fields.Char(string='Ubicacion de cambio',
                           track_visibility='onchange')
    #planned_date_end = fields.Datetime(compute='_compute_planned_date_end')

    # project_id = fields.Many2one(related='project_task_id.project_id', track_visibility="onchange")
    # project_id = fields.Many2one('project.project', 'Project Shared', domain=[('privacy_visibility', '=', 'portal')],
    #                              required=True, readonly=True)

    @api.onchange('task_template_id')
    def _onchange_task_template_id(self):
        self.btn_asig = False
        self.btn_desasig = False
        self.btn_asig_spp = False
        self.btn_desasig_spp = False
        if self.task_template_id:
            self.btn_asig = self.task_template_id.btn_asig
            self.btn_desasig = self.task_template_id.btn_desasig
            self.btn_asig_spp = self.task_template_id.btn_asig_spp
            self.btn_desasig_spp = self.task_template_id.btn_desasig_spp

    @api.onchange('zona_comercial')
    def _onchange_zona_comercial(self):
        if self.zona_comercial:
            comunas_id = self.env['comuna.comercial'].search([('zona_id', '=', self.zona_comercial.id)]).commune
            if comunas_id:
                self.comuna_domain = comunas_id.ids

    @api.model_create_multi
    def create(self, value_list):
        #Revisar si es cambio de domicilio
        # if 'partner_contact_id' in value_list:
        #     self.agreement_line_id.write({'partner_contact_id': value_list('partner_contact_id')})
        # Operar el create para saber si es father o no
        if self.env.context.get('visita'):
            value_list[0]['father'] = True
            value_list[0]['planned_date_begin'] = value_list[0]['planned_visit_begin']
            value_list[0]['planned_date_end'] = value_list[0]['planned_visit_end']
        res = super(ProjectTask, self).create(value_list)
        if res.father:
            for line in self.task_line:
                line.write({'planned_date_begin': res.planned_visit_begin, 'planned_date_end': res.planned_visit_end, 'visit_id': res.id})
        return res

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if self.stage_id.name == 'Hecho':
            self.agreement_line_id.write({'partner_contact_id': self.partner_contact_change,
                                          'zona_comercial': self.zona_comercial,
                                          'comuna_id': self.comuna_id, 'location': self.location_change})
        return res


    def create_transfer_order(self):
        """ Este metodo debe ser llamado desde la orden en terreno para instalacion """
        StockWarehouse = self.env['stock.warehouse']
        user_id = self.env.user
        for line in self:
            type_transfer_equipment = ''
            if not line.agreement_line_id.agreement_line_keys and not line.agreement_line_id.picking_id:
                warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
                location_id = line.env.user.default_stock_location_id
                if line.agreement_line_id.admin_line_id.is_admin and user_id.is_admin and line.agreement_line_id.admin_line_id.id == user_id.id:
                    if location_id:
                        if line.type_transfer_equipment == 'inci':
                            type_transfer_equipment = 'install'
                        else:
                            type_transfer_equipment = line.type_transfer_equipment
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': type_transfer_equipment,
                            'location_id': location_id.id,
                            'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.agreement_line_id.id,
                            'is_partner': True,
                            'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        for products in line.product_line:
                            if products.real_qty < 0:
                                raise UserError(
                                    'Las cantidades no pueden ser negativas')
                            if products.is_principal:
                                if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                    raise UserError(
                                        'El producto principal no puede ser mayor a 1 ni menor a 1')
                                if products.product_id != line.agreement_line_id.product_principal:
                                    continue
                            if products.real_qty == 0:
                                continue
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': products.product_id.name,
                                'product_id': products.product_id.id,
                                'transfer_manager': products.product_id.transfer_manager,
                                'product_uom_qty': products.real_qty,
                                'product_uom': products.product_id.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            line.agreement_line_id.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    else:
                        raise UserError(
                            'Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador')
                elif not line.agreement_line_id.admin_line_id:
                    if location_id:
                        if line.type_transfer_equipment == 'inci':
                            type_transfer_equipment = 'install'
                        else:
                            type_transfer_equipment = line.type_transfer_equipment
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': type_transfer_equipment,
                            'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.agreement_line_id.id,
                            'is_partner': True,
                            'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        for products in line.product_line:
                            if products.real_qty < 0:
                                raise UserError(
                                    'Las cantidades no pueden ser negativas')
                            if products.is_principal:
                                if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                    raise UserError(
                                        'El producto principal no puede ser mayor a 1 ni menor a 1')
                                if products.product_id != line.agreement_line_id.product_principal:
                                    continue
                            if products.real_qty == 0:
                                continue
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': products.product_id.name,
                                'product_id': products.product_id.id,
                                'transfer_manager': products.product_id.transfer_manager,
                                'product_uom_qty': products.real_qty,
                                'product_uom': products.product_id.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            line.agreement_line_id.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    else:
                        raise ValidationError(
                            "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_admin:
                    if location_id:
                        if line.type_transfer_equipment == 'inci':
                            type_transfer_equipment = 'install'
                        else:
                            type_transfer_equipment = line.type_transfer_equipment
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': type_transfer_equipment,
                            'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.agreement_line_id.id,
                            'is_partner': True,
                            'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        for products in line.product_line:
                            if products.real_qty < 0:
                                raise ValueError('Las cantidades no pueden ser negativas')
                            if products.is_principal:
                                if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                    raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                                if products.product_id != line.agreement_line_id.product_principal:
                                    continue
                            if products.real_qty == 0:
                                continue
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': products.product_id.name,
                                'product_id': products.product_id.id,
                                'transfer_manager': products.product_id.transfer_manager,
                                'product_uom_qty': products.real_qty,
                                'product_uom': products.product_id.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            line.agreement_line_id.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    elif not line.agreement_line_id.admin_line_id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    else:
                        raise ValidationError(
                            "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_franchisee and line.agreement_line_id.admin_line_id.id != user_id.id:
                    raise ValidationError(
                        "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                elif line.agreement_line_id.admin_line_id.is_admin and user_id.is_franchisee:
                    raise ValidationError(
                        "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
            elif not line.agreement_line_id.agreement_line_keys and line.agreement_line_id.picking_id:
                if line.agreement_line_id.picking_id.state in ['draft', 'confirmed', 'waiting', 'assigned', 'ready', 'check']:
                    raise ValidationError("Esta linea de contrato ya tiene una orden de transferencia en proceso")
                elif line.agreement_line_id.picking_id.state == 'cancel':
                    warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
                    location_id = line.env.user.default_stock_location_id
                    if line.agreement_line_id.admin_line_id.is_admin and user_id.is_admin and line.agreement_line_id.admin_line_id.id == user_id.id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_admin:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_franchisee and line.agreement_line_id.admin_line_id.id != user_id.id:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_admin and user_id.is_franchisee:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
                    elif not line.agreement_line_id.admin_line_id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_franchisee and line.agreement_line_id.admin_line_id.id != user_id.id:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_admin and user_id.is_franchisee:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
                    elif not line.agreement_line_id.admin_line_id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                                    if products.product_id != line.agreement_line_ids.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
            else:
                raise ValidationError(
                    "Esta linea de contrato ya tiene un equipo asignado. Para asignar uno nuevo debe primero desaginar el equipo actual")

    def create_transfer_asig_spp(self):
        """ Este metodo debe ser llamado desde la orden en terreno para instalacion """
        StockWarehouse = self.env['stock.warehouse']
        user_id = self.env.user
        for line in self:
            type_transfer_equipment = ''
            if not line.agreement_line_id.agreement_line_keys and not line.agreement_line_id.picking_id:
                warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
                location_id = line.env.user.default_stock_location_id
                if line.agreement_line_id.admin_line_id.is_admin and user_id.is_admin and line.agreement_line_id.admin_line_id.id == user_id.id:
                    if location_id:
                        if line.type_transfer_equipment == 'inci':
                            type_transfer_equipment = 'install'
                        else:
                            type_transfer_equipment = line.type_transfer_equipment
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': type_transfer_equipment,
                            'location_id': location_id.id,
                            'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.agreement_line_id.id,
                            'is_partner': True,
                            'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        for products in line.product_line:
                            if products.real_qty < 0:
                                raise UserError(
                                    'Las cantidades no pueden ser negativas')
                            if products.is_principal:
                                if int(products.real_qty) > 1:
                                    raise UserError(
                                        'El producto principal no puede ser mayor a 1')
                                if products.product_id != line.agreement_line_id.product_principal:
                                    continue
                            if products.real_qty == 0:
                                continue
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': products.product_id.name,
                                'product_id': products.product_id.id,
                                'transfer_manager': products.product_id.transfer_manager,
                                'product_uom_qty': products.real_qty,
                                'product_uom': products.product_id.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            line.agreement_line_id.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    else:
                        raise UserError(
                            'Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador')
                elif not line.agreement_line_id.admin_line_id:
                    if location_id:
                        if line.type_transfer_equipment == 'inci':
                            type_transfer_equipment = 'install'
                        else:
                            type_transfer_equipment = line.type_transfer_equipment
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': type_transfer_equipment,
                            'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.agreement_line_id.id,
                            'is_partner': True,
                            'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        for products in line.product_line:
                            if products.real_qty < 0:
                                raise UserError(
                                    'Las cantidades no pueden ser negativas')
                            if products.is_principal:
                                if int(products.real_qty) > 1:
                                    raise UserError(
                                        'El producto principal no puede ser mayor a 1')
                                if products.product_id != line.agreement_line_id.product_principal:
                                    continue
                            if products.real_qty == 0:
                                continue
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': products.product_id.name,
                                'product_id': products.product_id.id,
                                'transfer_manager': products.product_id.transfer_manager,
                                'product_uom_qty': products.real_qty,
                                'product_uom': products.product_id.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            line.agreement_line_id.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    else:
                        raise ValidationError(
                            "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_admin:
                    if location_id:
                        if line.type_transfer_equipment == 'inci':
                            type_transfer_equipment = 'install'
                        else:
                            type_transfer_equipment = line.type_transfer_equipment
                        pick_id = line.env['stock.picking'].create({
                            'picking_type_id': warehouse_partner.int_type_id.id,
                            'type_transfer': 'normal',
                            'type_transfer_equipment': type_transfer_equipment,
                            'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                            'location_id': location_id.id,
                            'location_dest_id': warehouse_partner.lot_stock_id.id,
                            'agreement_line_id': line.agreement_line_id.id,
                            'is_partner': True,
                            'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                            'state': 'confirmed'
                        })
                        for products in line.product_line:
                            if products.real_qty < 0:
                                raise ValueError('Las cantidades no pueden ser negativas')
                            if products.is_principal:
                                if int(products.real_qty) > 1:
                                    raise ValueError('El producto principal no puede ser mayor a 1')
                                if products.product_id != line.agreement_line_id.product_principal:
                                    continue
                            if products.real_qty == 0:
                                continue
                            vals_move = {
                                'picking_id': pick_id.id,
                                'name': products.product_id.name,
                                'product_id': products.product_id.id,
                                'transfer_manager': products.product_id.transfer_manager,
                                'product_uom_qty': products.real_qty,
                                'product_uom': products.product_id.uom_id.id,
                                'location_dest_id': pick_id.location_dest_id.id,
                                'location_id': pick_id.location_id.id,
                                'state': 'confirmed'
                            }
                            line.env['stock.move'].create(vals_move)
                            line.picking_id = pick_id.id
                            line.agreement_line_id.picking_id = pick_id.id
                        pick_id.button_reserve_picking_internal()
                    elif not line.agreement_line_id.admin_line_id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    else:
                        raise ValidationError(
                            "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_franchisee and line.agreement_line_id.admin_line_id.id != user_id.id:
                    raise ValidationError(
                        "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                elif line.agreement_line_id.admin_line_id.is_admin and user_id.is_franchisee:
                    raise ValidationError(
                        "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
            elif not line.agreement_line_id.agreement_line_keys and line.agreement_line_id.picking_id:
                if line.agreement_line_id.picking_id.state in ['draft', 'confirmed', 'waiting', 'assigned', 'ready', 'check']:
                    raise ValidationError("Esta linea de contrato ya tiene una orden de transferencia en proceso")
                elif line.agreement_line_id.picking_id.state == 'cancel':
                    warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
                    location_id = line.env.user.default_stock_location_id
                    if line.agreement_line_id.admin_line_id.is_admin and user_id.is_admin and line.agreement_line_id.admin_line_id.id == user_id.id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_admin:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_franchisee and line.agreement_line_id.admin_line_id.id != user_id.id:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_admin and user_id.is_franchisee:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
                    elif not line.agreement_line_id.admin_line_id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1')
                                    if products.product_id != line.agreement_line_id.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_franchisee and user_id.is_franchisee and line.agreement_line_id.admin_line_id.id != user_id.id:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de otro Franquiciado. Contacte a su administrador")
                    elif line.agreement_line_id.admin_line_id.is_admin and user_id.is_franchisee:
                        raise ValidationError(
                            "No tienes acceso para asignar un numero de serie a una linea de un Ejecutivo de Maihue. Contacte a su administrador")
                    elif not line.agreement_line_id.admin_line_id:
                        if location_id:
                            if line.type_transfer_equipment == 'inci':
                                type_transfer_equipment = 'install'
                            else:
                                type_transfer_equipment = line.type_transfer_equipment
                            pick_id = line.env['stock.picking'].create({
                                'picking_type_id': warehouse_partner.int_type_id.id,
                                'type_transfer': 'normal',
                                'type_transfer_equipment': type_transfer_equipment,
                                'l10n_cl_delivery_guide_reason': line.l10n_cl_delivery_guide_reason,
                                'location_id': location_id.id,
                                'location_dest_id': warehouse_partner.lot_stock_id.id,
                                'agreement_line_id': line.agreement_line_id.id,
                                'is_partner': True,
                                'customer_id': line.agreement_line_id.agreement_id.partner_id.id,
                                'state': 'confirmed'
                            })
                            for products in line.product_line:
                                if products.real_qty < 0:
                                    raise ValueError('Las cantidades no pueden ser negativas')
                                if products.is_principal:
                                    if int(products.real_qty) > 1:
                                        raise ValueError('El producto principal no puede ser mayor a 1')
                                    if products.product_id != line.agreement_line_ids.product_principal:
                                        continue
                                if products.real_qty == 0:
                                    continue
                                vals_move = {
                                    'picking_id': pick_id.id,
                                    'name': products.product_id.name,
                                    'product_id': products.product_id.id,
                                    'transfer_manager': products.product_id.transfer_manager,
                                    'product_uom_qty': products.real_qty,
                                    'product_uom': products.product_id.uom_id.id,
                                    'location_dest_id': pick_id.location_dest_id.id,
                                    'location_id': pick_id.location_id.id,
                                    'state': 'confirmed'
                                }
                                line.env['stock.move'].create(vals_move)
                                line.picking_id = pick_id.id
                                line.agreement_line_id.picking_id = pick_id.id
                            pick_id.button_reserve_picking_internal()
                        else:
                            raise ValidationError(
                                "Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
            else:
                raise ValidationError(
                    "Esta linea de contrato ya tiene un equipo asignado. Para asignar uno nuevo debe primero desaginar el equipo actual")

    def create_transfer_order_uninstall(self, type_transfer_equipment='uninstall'):
        """ Este metodo debe ser llamado desde la orden en terreno para desinstalacion """
        StockWarehouse = self.env['stock.warehouse']
        StockQuant = self.env['stock.quant']
        type_transfer_equipment = ''
        if self.agreement_line_id.agreement_line_keys:
            warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
            location_dest_id = self.env.user.default_stock_location_id
            if location_dest_id:
                if self.type_transfer_equipment == 'inci':
                    type_transfer_equipment = 'uninstall_repair'
                else:
                    type_transfer_equipment = self.type_transfer_equipment
                pick_id = self.env['stock.picking'].create({
                    'picking_type_id': warehouse_partner.int_type_id.id,
                    'type_transfer': 'normal',
                    'location_dest_id': location_dest_id.id,
                    'location_id': warehouse_partner.lot_stock_id.id,
                    'type_transfer_equipment': type_transfer_equipment,
                    'agreement_line_id': self.agreement_line_id.id,
                    'customer_id': self.agreement_line_id.agreement_id.partner_id.id,
                    'state': 'confirmed'
                })
                for products in self.product_line:
                    if products.real_qty < 0:
                        raise ValueError('Las cantidades no pueden ser negativas')
                    if products.is_principal:
                        if int(products.real_qty) > 1 or int(products.real_qty) < 1:
                            raise ValueError('El producto principal no puede ser mayor a 1 ni menor a 1')
                        if products.product_id != self.agreement_line_id.product_principal:
                            continue
                    if products.real_qty == 0:
                        continue
                    vals_move = {
                        'picking_id': pick_id.id,
                        'name': products.product_id.name,
                        'product_id': products.product_id.id,
                        'transfer_manager': products.product_id.transfer_manager,
                        'product_uom_qty': products.real_qty,
                        'product_uom': products.product_id.uom_id.id,
                        'location_dest_id': pick_id.location_dest_id.id,
                        'location_id': pick_id.location_id.id,
                        'state': 'assigned'
                    }
                    move_id = self.env['stock.move'].create(vals_move)
                    lot_id = False
                    lot_name = False
                    if products.is_principal:
                        lot_id = self.agreement_line_id.agreement_line_keys.id if self.agreement_line_id.agreement_line_keys else False
                        lot_name = self.agreement_line_id.agreement_line_keys.name if self.agreement_line_id.agreement_line_keys else False
                    vals_move_line = {
                        'picking_id': pick_id.id,
                        'move_id': move_id.id,
                        'product_id': products.product_id.id,
                        'transfer_manager': products.product_id.transfer_manager,
                        'product_uom_qty': products.real_qty,
                        'qty_done': 0,
                        'lot_id': lot_id,
                        'lot_name': lot_name,
                        'franchisee_id': self.agreement_line_id.agreement_line_keys.franchisee_id.id if self.agreement_line_id.agreement_line_keys.franchisee_id else False,
                        'product_uom_id': products.product_id.uom_id.id,
                        'location_dest_id': pick_id.location_dest_id.id,
                        'location_id': pick_id.location_id.id,
                    }
                    self.env['stock.move.line'].create(vals_move_line)
                    quant = StockQuant.search([('product_id', '=', products.product_id.id), ('lot_id', '=', self.agreement_line_id.agreement_line_keys.id)])
                    quant.reserved_quantity = products.real_qty
                    self.picking_id = pick_id.id
                    self.agreement_line_id.picking_id = pick_id.id
            else:
                raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
        else:
            raise ValidationError(
                "No se puede desvincular un equipo en esta linea de contrato ya que no se ha asignado ninguno.")

    def create_transfer_order_uninstall_spp(self, type_transfer_equipment='uninstall'):
        """ Este metodo debe ser llamado desde la orden en terreno para desinstalacion """
        StockWarehouse = self.env['stock.warehouse']
        StockQuant = self.env['stock.quant']
        type_transfer_equipment = ''
        if self.agreement_line_id.agreement_line_keys:
            warehouse_partner = StockWarehouse.search([('is_partner', '=', True)])
            location_dest_id = self.env.user.default_stock_location_id
            if location_dest_id:
                if self.type_transfer_equipment == 'inci':
                    type_transfer_equipment = 'uninstall_repair'
                else:
                    type_transfer_equipment = self.type_transfer_equipment
                pick_id = self.env['stock.picking'].create({
                    'picking_type_id': warehouse_partner.int_type_id.id,
                    'type_transfer': 'normal',
                    'location_dest_id': location_dest_id.id,
                    'location_id': warehouse_partner.lot_stock_id.id,
                    'type_transfer_equipment': type_transfer_equipment,
                    'agreement_line_id': self.agreement_line_id.id,
                    'customer_id': self.agreement_line_id.agreement_id.partner_id.id,
                    'state': 'confirmed'
                })
                for products in self.product_line:
                    if products.real_qty < 0:
                        raise ValueError('Las cantidades no pueden ser negativas')
                    if products.is_principal:
                        if int(products.real_qty) > 1:
                            raise ValueError('El producto principal no puede ser mayor a 1')
                        if products.product_id != self.agreement_line_id.product_principal:
                            continue
                    if products.real_qty == 0:
                        continue
                    vals_move = {
                        'picking_id': pick_id.id,
                        'name': products.product_id.name,
                        'product_id': products.product_id.id,
                        'transfer_manager': products.product_id.transfer_manager,
                        'product_uom_qty': products.real_qty,
                        'product_uom': products.product_id.uom_id.id,
                        'location_dest_id': pick_id.location_dest_id.id,
                        'location_id': pick_id.location_id.id,
                        'state': 'assigned'
                    }
                    move_id = self.env['stock.move'].create(vals_move)
                    lot_id = False
                    lot_name = False
                    if products.is_principal:
                        lot_id = self.agreement_line_id.agreement_line_keys.id if self.agreement_line_id.agreement_line_keys else False
                        lot_name = self.agreement_line_id.agreement_line_keys.name if self.agreement_line_id.agreement_line_keys else False
                    vals_move_line = {
                        'picking_id': pick_id.id,
                        'move_id': move_id.id,
                        'product_id': products.product_id.id,
                        'transfer_manager': products.product_id.transfer_manager,
                        'product_uom_qty': products.real_qty,
                        'qty_done': 0,
                        'lot_id': lot_id,
                        'lot_name': lot_name,
                        'franchisee_id': self.agreement_line_id.agreement_line_keys.franchisee_id.id if self.agreement_line_id.agreement_line_keys.franchisee_id else False,
                        'product_uom_id': products.product_id.uom_id.id,
                        'location_dest_id': pick_id.location_dest_id.id,
                        'location_id': pick_id.location_id.id,
                    }
                    self.env['stock.move.line'].create(vals_move_line)
                    quant = StockQuant.search([('product_id', '=', products.product_id.id), ('lot_id', '=', self.agreement_line_id.agreement_line_keys.id)])
                    quant.reserved_quantity = products.real_qty
                    self.picking_id = pick_id.id
                    self.agreement_line_id.picking_id = pick_id.id
            else:
                raise ValidationError("Debe configurar su ubicacion predeterminada en su usuario. Contacte a su administrador")
        else:
            raise ValidationError(
                "No se puede desvincular un equipo en esta linea de contrato ya que no se ha asignado ninguno.")


class ProjectTaskLine(models.Model):
    _name = 'project.task.order'
    _rec_name = 'task_id'

    @api.model
    def _compute_adreess_domain(self):
        for record in self:
            principal_ids = False
            domain = []
            if record.task_id:
                principal_ids = self.env['project.task'].search(
                    [('partner_contact_id', '=', record.task_id.partner_contact.id),
                     ('project_id', '=', record.task_id.project_id.id)])
                list_pd = []
        #self.task = principal_ids.ids
        self.task_domain = [(6, 0, principal_ids.ids)]

    @api.onchange('task')
    def _onchange_task(self):
        for record in self:
            principal_ids = False
            domain = []
            not_domain = []
            for task_not in record.task_id.task_line:
                if task_not.task.id:
                    not_domain.append(task_not.task.id)
            no_incluir = self.env['project.task.order'].search([]) #[('visit_id', '=', False)]
            for task_agen in no_incluir:
                if task_agen.task.id:
                    if task_agen.task.id not in not_domain:
                        not_domain.append(task_agen.task.id)
            principal_ids = self.env['project.task'].search(
                [('partner_contact_id', '=', record.task_id.partner_contact.id),
                 ('project_id', '=', record.task_id.project_id.id),
                 ('visit_id', '=', False),
                 ('id', 'not in', not_domain)])
            if record.task_id:
                list_pd = []
        #self.task = principal_ids.ids
        self.task_domain = [(6, 0, principal_ids.ids)]

    # @api.onchange('task')
    # def _onchange_task(self):
    #     for record in self:
    #         principal_ids = False
    #         domain = []
    #         if record.task_id:
    #             principal_ids = self.env['project.task'].search(
    #                 [('partner_contact_id', '=', record.task_id.partner_contact.id),
    #                  ('project_id', '=', record.task_id.project_id.id)])
    #         if principal_ids:
    #             for pri in principal_ids:
    #                 if pri.id not in self.task_id.ids:
    #                     domain.append(pri)
    #             list_pd = []
    #     # self.task = principal_ids.ids
    #     self.task_domain = [(6, 0, domain.ids)]

    task_id = fields.Many2one('project.task', string='Task Reference', required=True, ondelete='cascade', index=True,
                              copy=False)
    task = fields.Many2one('project.task', string='orden de servicio', required=True, ondelete='cascade', index=True,
                       copy=False) #, compute="_compute_adreess_domain"
    task_domain = fields.Many2many('project.task', 'project_task_rel', 'task_rel_id',
                                        'domain_id', track_visibility="onchange",
                                        compute="_compute_adreess_domain",
                                        string='Tareas Dominio')
    helpdesk_ticket_id = fields.Many2one(
        related="task.helpdesk_ticket_id",
        string="Ticket",
        # copy=True,
        track_visibility='onchange')
    team_id = fields.Many2one(related="helpdesk_ticket_id.team_id", string="Equipo")
    ticket_type_id = fields.Many2one(related="helpdesk_ticket_id.ticket_type_id", string="Tipo")
    totals = fields.Float(related="task.totals",
        string="Duración",
        # copy=True,
        track_visibility='onchange')
    stage_id = fields.Many2one(
        related="task.stage_id", string='Etapa',
        help='Minimum stage a ticket needs to reach in order to satisfy this SLA.')

class ProjectTaskLinePen(models.Model):
    _name = 'project.task.order.pen'
    _rec_name = 'task_id'


    # @api.model
    # def _compute_task_line_pen(self):
    #     task_ids = self.env['project.task'].search(
    #         [('partner_id', '=', self.partner_id.id)])
    #     return task_ids.ids

    # @api.model
    # def _compute_adreess_domain(self):
    #     for record in self:
    #         principal_ids = False
    #         domain = []
    #         if record.task_id:
    #             principal_ids = self.env['project.task'].search(
    #                 [('partner_contact_id', '=', record.task_id.partner_contact.id),
    #                  ('project_id', '=', record.task_id.project_id.id)])
    #             list_pd = []
    #     #self.task = principal_ids.ids
    #     self.task_domain = [(6, 0, principal_ids.ids)]

    # @api.onchange('task')
    # def _onchange_task(self):
    #     for record in self:
    #         principal_ids = False
    #         domain = []
    #         if record.task_id:
    #             principal_ids = self.env['project.task'].search(
    #                 [('partner_contact_id', '=', record.task_id.partner_contact.id),
    #                  ('project_id', '=', record.task_id.project_id.id)])
    #             list_pd = []
    #     #self.task = principal_ids.ids
    #     self.task_domain = [(6, 0, principal_ids.ids)]

    task_id = fields.Many2one('project.task', string='Task Reference', required=True, ondelete='cascade', index=True,
                              copy=False)
    task = fields.Many2one('project.task', string='orden de servicio', required=True, ondelete='cascade', index=True,
                       copy=False) #, compute="_compute_adreess_domain"
    # task_domain = fields.Many2many('project.task', 'project_task_rel', 'task_rel_id',
    #                                     'domain_id', track_visibility="onchange",
    #                                     #compute="_compute_adreess_domain",
    #                                     string='Tareas Dominio')
    helpdesk_ticket_id = fields.Many2one(
        related="task.helpdesk_ticket_id",
        string="Ticket",
        # copy=True,
        track_visibility='onchange')
    team_id = fields.Many2one(related="helpdesk_ticket_id.team_id", string="Equipo")
    ticket_type_id = fields.Many2one(related="helpdesk_ticket_id.ticket_type_id", string="Tipo")
    totals = fields.Float(related="task.totals",
        string="Duración",
        # copy=True,
        track_visibility='onchange')
    stage_id = fields.Many2one(
        related="task.stage_id", string='Etapa',
        help='Minimum stage a ticket needs to reach in order to satisfy this SLA.')

class ProjectVisitAgen(models.Model):
    _name = 'project.visit.agen'
    _rec_name = 'task_id'

    # @api.model
    # def _compute_adreess_domain(self):
    #     for record in self:
    #         principal_ids = False
    #         domain = []
    #         if record.task_id:
    #             principal_ids = self.env['project.task'].search(
    #                 [('partner_contact_id', '=', record.task_id.partner_contact.id),
    #                  ('project_id', '=', record.task_id.project_id.id)])
    #             list_pd = []
    #     #self.task = principal_ids.ids
    #     self.task_domain = [(6, 0, principal_ids.ids)]

    # @api.onchange('task')
    # def _onchange_task(self):
    #     for record in self:
    #         principal_ids = False
    #         domain = []
    #         if record.task_id:
    #             principal_ids = self.env['project.task'].search(
    #                 [('partner_contact_id', '=', record.task_id.partner_contact.id),
    #                  ('project_id', '=', record.task_id.project_id.id)])
    #             list_pd = []
    #     #self.task = principal_ids.ids
    #     self.task_domain = [(6, 0, principal_ids.ids)]

    task_id = fields.Many2one('project.task', string='Task Reference', required=False, ondelete='cascade', index=True,
                              copy=False)
    task = fields.Many2one('project.task', string='orden de servicio', required=False, ondelete='cascade', index=True,
                       copy=False) #, compute="_compute_adreess_domain"
    # task_domain = fields.Many2many('project.task', 'project_task_rel', 'task_rel_id',
    #                                     'domain_id', track_visibility="onchange",
    #                                     #compute="_compute_adreess_domain",
    #                                     string='Tareas Dominio')
    helpdesk_ticket_id = fields.Many2one(
        related="task.helpdesk_ticket_id",
        string="Ticket",
        # copy=True,
        track_visibility='onchange')
    team_id = fields.Many2one(related="helpdesk_ticket_id.team_id", string="Equipo")
    ticket_type_id = fields.Many2one(related="helpdesk_ticket_id.ticket_type_id", string="Tipo")
    totals = fields.Float(related="task.totals",
        string="Duración",
        # copy=True,
        track_visibility='onchange')
    stage_id = fields.Many2one(
        related="task.stage_id", string='Etapa',
        help='Minimum stage a ticket needs to reach in order to satisfy this SLA.')

class CamposTicket(models.Model):
    _name = 'campos.ticket'
    _rec_name = 'campo'

    campo = fields.Selection(
        selection=[
            ('name', 'Asunto'),
            ('team_id', 'Equipo de servicio de asistencia'),
            ('user_id', 'Asignado a'),
            ('instalador_ticket', 'instalador'),
            ('ticket_type_id', 'Tipo'),
            ('categoria_maihue_id', 'Categoria Maihue')],
        string='Campo',
        required=True)
    atributo = fields.Selection(
        selection=[
            ('readonly', 'Readonly'),
            ('invisible', 'Invisible'),
            ('required', 'Required')],
        string='Atributo',
        required=True)
    stage_id = fields.Many2one('helpdesk.stage', track_visibility="onchange",
                                               string='Estado')
    helpdesk_tag_id = fields.Many2one("helpdesk.tag", string="Helpdesk Tag", copy=False)





