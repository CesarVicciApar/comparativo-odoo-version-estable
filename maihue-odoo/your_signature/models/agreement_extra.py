# -*- coding: utf-8 -*-
import base64
import json
import requests
import logging
import PyPDF2
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

_logger = logging.getLogger(__name__)


class AgreementExtra(models.Model):
    _inherit = "agreement.extra"

    visible = fields.Boolean(string="visible")
    file_report = fields.Binary(string="Documento PDF")
    file_report_signed = fields.Binary(string="Documento PDF Firmado", track_visibility="onchange")
    file_name = fields.Char(string="Filename", store=True)
    id_contrato = fields.Char(string="Id contrato (TuFirma)", readonly=True, track_visibility="onchange")
    company_type1 = fields.Selection(related="partner_signed_user_id.company_type")
    company_type2 = fields.Selection(related="company_signed_user_dos_id.company_type")
    status = fields.Selection(selection=[("to_sign", "Pend. Firma"), ("signed", "Firmado"), ("cancelled", "Cancelado")], track_visibility="onchange")
    company_type3 = fields.Selection(related="company_signed_user_tres_id.company_type")
    msg = fields.Text(string="Msg error tu firma")
    signed = fields.Boolean(string="Firmado")
    cancelled = fields.Boolean(string="Cancelado")
    count_signature = fields.Integer(string="Firmas", required=False, compute='number_of_signatures')
    signature_ids = fields.One2many('your.signature.log', 'extra_id', string="Log de Firmas")
    signed_client = fields.Boolean(string='Firmado cliente', track_visibility="onchange")
    signed_maihue = fields.Boolean(string='Firmado Maihue', track_visibility="onchange")
    company_type_code = fields.Char(related='firma_type.code')
    special_group = fields.Boolean('Permiso especial documentos', compute='_compute_special_group')
    signed_one = fields.Boolean(string='Firma1', compute='_compute_date_signed_readonly')
    signed_two = fields.Boolean(string='Firma2', compute='_compute_date_signed_readonly')
    signed_three = fields.Boolean(string='Firma3', compute='_compute_date_signed_readonly')
    signed_four = fields.Boolean(string='Firma4', compute='_compute_date_signed_readonly')
    version = fields.Integer(string='Version', default=1, track_visibility="onchange")

    def _compute_date_signed_readonly(self):
        for record in self:
            signed1 = signed2 = signed3 = signed4 = False
            if not record.partner_signed_user_id and record.company_type_code in ['fisica_cliente', 'fisica_todos']:
                signed1 = True
            if not record.company_signed_user_dos_id and record.company_type_code in ['fisica_cliente', 'fisica_todos']:
                signed2 = True
            if not record.company_signed_user_tres_id and record.company_type_code in ['fisica_cliente', 'fisica_todos']:
                signed3 = True
            if record.company_signed_user_id and record.company_type_code in ['fisica_cliente']:
                signed4 = True
            if record.status == 'signed':
                signed1 = signed2 = signed3 = signed4 = True
            record.signed_one = signed1
            record.signed_two = signed2
            record.signed_three = signed3
            record.signed_four = signed4

    @api.onchange('fecha_repres1','fecha_repres2','fecha_repres3','company_signed_date')
    def _onchange_date_repres_update_state(self):
        if self.fecha_repres1:
            self.state_firm1 = 'M'
        else:
            self.state_firm1 = 'T'

        if self.fecha_repres2:
            self.state_firm2 = 'M'
        else:
            self.state_firm2 = 'T'

        if self.fecha_repres3:
            self.state_firm3 = 'M'
        else:
            self.state_firm3 = 'T'

        if self.company_signed_date:
            self.state_firm4 = 'M'
        else:
            self.state_firm4 = 'T'

    @api.onchange('state_firm1', 'state_firm2', 'state_firm3')
    def onchange_method(self):
        signed = False
        if self.partner_signed_user_id and self.company_signed_user_dos_id and self.company_signed_user_tres_id:
            if self.state_firm1 == 'M' and self.state_firm2 == 'M' and self.state_firm3 == 'M':
                signed = True
        elif self.partner_signed_user_id and not self.company_signed_user_dos_id and not self.company_signed_user_tres_id:
            if self.state_firm1 == 'M':
                signed = True
        elif not self.partner_signed_user_id and self.company_signed_user_dos_id and not self.company_signed_user_tres_id:
            if self.state_firm2 == 'M':
                signed = True
        elif not self.partner_signed_user_id and not self.company_signed_user_dos_id and self.company_signed_user_tres_id:
            if self.state_firm3 == 'M':
                signed = True
        elif self.partner_signed_user_id and self.company_signed_user_dos_id and not self.company_signed_user_tres_id:
            if self.state_firm1 == 'M' and self.state_firm2 == 'M':
                signed = True
        elif self.partner_signed_user_id and not self.company_signed_user_dos_id and self.company_signed_user_tres_id:
            if self.state_firm1 == 'M' and self.state_firm3 == 'M':
                signed = True
        elif not self.partner_signed_user_id and self.company_signed_user_dos_id and self.company_signed_user_tres_id:
            if self.state_firm2 == 'M' and self.state_firm3 == 'M':
                signed = True
        self.signed_client = signed

    @api.onchange('signed_client', 'signed_maihue', 'signed_contract')
    def onchange_update_status_signed(self):
        if self.signed_client and self.signed_maihue and self.signed_contract:
            self.status = 'signed'
            if self.firma == 'fisica':
                signature_obj = self.env['your.signature.log'].search([('type', '=', self.firma),
                    ('firma_type', '=', self.firma_type.id), ('status', '=', 'to_sign')])
                if signature_obj:
                    signature_obj.write({
                        'name': self.name,
                        'status': self.status
                    })
            else:
                signature_obj = self.env['your.signature.log'].search([('id_contrato', '=', self.id_contrato), ('type', '=', self.firma),
                    ('firma_type', '=', self.firma_type.id), ('status', '=', 'to_sign')])
                if signature_obj:
                    signature_obj.write({
                        'name': self.name,
                        'status': self.status
                    })


    def _compute_special_group(self):
        for record in self:
            special_group = False
            if record.env.user.has_group('your_signature.group_special_agreement_extra'):
                special_group = True
            record.special_group = special_group

    @api.onchange('firma')
    def onchange_firma(self):
        self.firma_type = False

    @api.model
    def _get_values_your_signature(self, firma_state):
        config_your_signature = self.env['ir.config_parameter'].sudo()
        if firma_state == 'test':
            return {
                'api_key': config_your_signature.get_param('api_key'),
                'secret': config_your_signature.get_param('secret'),
                'url': 'https://testapi.tufirma.digital/',
            }
        else:
            return{
                'api_key': config_your_signature.get_param('api_key'),
                'secret': config_your_signature.get_param('secret'),
                'url': 'https://api.tufirma.digital/'
            }

    def view_your_signature_log(self):
        action = self.env['ir.actions.act_window']._for_xml_id('your_signature.action_your_signature_log')
        action['domain'] = [('extra_id', '=', self.id)]
        action['context'] = {'default_extra_id': self.id}
        return action

    def number_of_signatures(self):
        for sig in self:
            sig.count_signature = len(sig.signature_ids)

    def return_values_your_signature(self):
        config_your_signature = self.env['ir.config_parameter'].sudo().get_param('firma_state')
        url = self._get_values_your_signature(config_your_signature)
        return url


    # def create(self, vals):
    #     res = super(AgreementExtra, self).write(vals)
    #     if 'agreement_id' in vals:
    #         print(self.name)
    #         self.name = self.agreement_id.name
    #     return res


    def write(self, vals):
        res = super(AgreementExtra, self).write(vals)
        content = vals.get('content')
        if content:
            self.save_pdf()
        return res


    # @api.onchange('partner_signed_user_id', 'company_signed_user_dos_id', 'company_signed_user_tres_id')
    # def validate_signers(self):
    #     for record in self:
    #         if record.company_type1 != 'person':
    #             raise UserError('Los firmantes debe ser de tipo individual')
    #         if record.company_type2 != 'person':
    #             raise UserError('Los firmantes debe ser de tipo individual')
    #         if record.company_type3 != 'person':
    #             raise UserError('Los firmantes debe ser de tipo individual')


    def save_pdf(self):
        if self.content:
            report_name = self.env.ref('agreement_blueminds.partner_agreement_contract_document')
            pdf, formato = report_name._render_qweb_pdf(self.id)
            data = base64.b64encode(pdf)
            self.file_report = data
            self.file_name = str(self.agreement_id.name) + '-' + self.name + '.pdf'
            return self.file_report


    def send_to_your_signature(self):
        for record in self:
            config = self.env['ir.config_parameter'].sudo()
            firma_avanzanda = []
            dict_conf = record.return_values_your_signature()
            if not config.get_param('is_firma'):
                raise UserError('Operacion no permitida, contacte al Administrador para activar las credenciales.')
            headers = {
                'x-api-key': dict_conf.get('api_key', False),
                'secret': dict_conf.get('secret', False),
                'Content-Type': 'application/json',
            }
            url = dict_conf.get('url') + 'api/documents/create'
            save_pdf = record.save_pdf()
            pdf_decode = save_pdf.decode('utf-8')
            if record.partner_signed_user_id:
                record.email_signed_user = record.partner_signed_user_id.email
                last_name = ''
                if record.partner_signed_user_id.father_name and record.partner_signed_user_id.mother_name:
                    last_name +=  record.partner_signed_user_id.father_name + ' ' + record.partner_signed_user_id.mother_name
                elif not record.partner_signed_user_id.father_name and record.partner_signed_user_id.mother_name:
                    last_name +=  record.partner_signed_user_id.mother_name
                elif record.partner_signed_user_id.father_name and not record.partner_signed_user_id.mother_name:
                    last_name +=  record.partner_signed_user_id.father_name
                vat = record.partner_signed_user_id.vat_child if record.partner_signed_user_id.parent_id else record.partner_signed_user_id.vat
                firma_avanzanda.append({
                    "nombre": record.partner_signed_user_id.name,
                    "email": record.partner_signed_user_id.email,
                    "extras": "",
                    "profile": {
                        "name": record.partner_signed_user_id.full_name,
                        "lastName":last_name,
                        "phone":record.partner_signed_user_id.phone0,
                        "rut": vat,
                    },
                })
                record.write({'state_firm1': 'T', 'fecha_envio1': datetime.today()})
            if record.company_signed_user_dos_id:
                record.email_signed_user_dos = record.company_signed_user_dos_id.email
                last_name = ''
                if record.company_signed_user_dos_id.father_name and record.company_signed_user_dos_id.mother_name:
                    last_name += record.company_signed_user_dos_id.father_name + ' ' + record.company_signed_user_dos_id.mother_name
                elif not record.company_signed_user_dos_id.father_name and record.company_signed_user_dos_id.mother_name:
                    last_name += record.company_signed_user_dos_id.mother_name
                elif record.company_signed_user_dos_id.father_name and not record.company_signed_user_dos_id.mother_name:
                    last_name += record.company_signed_user_dos_id.father_name
                vat = record.company_signed_user_dos_id.vat_child if record.company_signed_user_dos_id.parent_id else record.company_signed_user_dos_id.vat
                firma_avanzanda.append({
                    "nombre": record.company_signed_user_dos_id.name,
                    "email": record.company_signed_user_dos_id.email,
                    "extras": "",
                    "profile": {
                        "name": record.company_signed_user_dos_id.full_name,
                        "lastName":last_name,
                        "phone":record.company_signed_user_dos_id.phone0,
                        "rut": vat,
                    },
                })
                record.write({'state_firm2': 'T', 'fecha_envio2': datetime.today()})
            if record.company_signed_user_tres_id:
                record.email_signed_user_tres = record.company_signed_user_tres_id.email
                last_name = ''
                if record.company_signed_user_tres_id.father_name and record.company_signed_user_tres_id.mother_name:
                    last_name += record.company_signed_user_tres_id.father_name + ' ' + record.company_signed_user_tres_id.mother_name
                elif not record.company_signed_user_tres_id.father_name and record.company_signed_user_tres_id.mother_name:
                    last_name += record.company_signed_user_tres_id.mother_name
                elif record.company_signed_user_tres_id.father_name and not record.company_signed_user_tres_id.mother_name:
                    last_name += record.company_signed_user_tres_id.father_name
                vat = record.company_signed_user_tres_id.vat_child if record.company_signed_user_tres_id.parent_id else record.company_signed_user_tres_id.vat
                firma_avanzanda.append({
                    "nombre": record.company_signed_user_tres_id.name,
                    "email": record.company_signed_user_tres_id.email,
                    "extras": "",
                    "profile": {
                        "name": record.company_signed_user_tres_id.full_name,
                        "lastName":last_name,
                        "phone":record.company_signed_user_tres_id.phone0,
                        "rut": vat,
                    },
                })
                record.write({'state_firm3': 'T', 'fecha_envio3': datetime.today()})
            if record.company_signed_user_id:
                record.email_signed_maihue = record.company_signed_user_id.email
                last_name = ''
                if record.company_signed_user_id.partner_id.father_name and record.company_signed_user_id.partner_id.mother_name:
                    last_name += record.company_signed_user_id.partner_id.father_name + ' ' + record.company_signed_user_id.partner_id.mother_name
                elif not record.company_signed_user_id.partner_id.father_name and record.company_signed_user_id.partner_id.mother_name:
                    last_name += record.company_signed_user_id.partner_id.mother_name
                elif record.company_signed_user_id.partner_id.father_name and not record.company_signed_user_id.partner_id.mother_name:
                    last_name += record.company_signed_user_id.partner_id.father_name
                firma_avanzanda.append({
                    "nombre": record.company_signed_user_id.name,
                    "email": record.company_signed_user_id.email,
                    "extras": "",
                    "profile": {
                        "name": record.company_signed_user_id.partner_id.full_name,
                        "lastName":last_name,
                        "phone":record.company_signed_user_id.phone0,
                        "rut": record.company_signed_user_id.vat,
                    },
                })
                record.write({'state_firm4': 'T'})
            vals = {
                'nombre': record.name,
                'descripcion': record.name,
                'firmantes': [],
                'firmantesFea': firma_avanzanda,
                'viewers': [],
                "tags": [ ],
                "hook": config.get_param('web.base.url') + "/api/hook",
                "fieldsHook": config.get_param('web.base.url') + "/api/fieldsHook",
                "redirectUrl": "https://biolib.roblecode.cl/health-check",
                "documentoMimeType": 'application/pdf',
                'documentoB64': pdf_decode,
            }
            # print(json.dumps(vals, indent=4, ensure_ascii=False))
            a = json.dumps(vals, indent=4, ensure_ascii=False)
            _logger.info('json: %s' % a)
            response = requests.post(url, headers=headers, data=json.dumps(vals, indent=4, ensure_ascii=False))
            if response.status_code != 200:
                print(response.status_code)
                raise UserError(response.text)
            else:
                print(response.status_code)
                # id_pruebas = '1234567890'
                dict_list = json.loads(response.text.encode('utf8'))
                record.write({'id_contrato': dict_list.get('id'), 'visible': True, 'status': 'to_sign'})
                if record.firma_type.code in ['simple', 'fisica_cliente']:
                    record.write({'signed_maihue': True, 'company_signed_date': datetime.today().date(), 'state_firm4': 'M'})
                #record.onchange_status()
                record.send_values_to_log()

    def send_to_signature(self):
        for record in self:
            record.write({'visible': True, 'status': 'to_sign'})
            if record.partner_signed_user_id:
                record.email_signed_user = record.partner_signed_user_id.email
                record.write({'state_firm1': 'T', 'fecha_envio1': datetime.today()})
            if record.company_signed_user_dos_id:
                record.email_signed_user_dos = record.company_signed_user_dos_id.email
                record.write({'state_firm2': 'T', 'fecha_envio2': datetime.today()})
            if record.company_signed_user_tres_id:
                record.email_signed_user_tres = record.company_signed_user_tres_id.email
                record.write({'state_firm3': 'T', 'fecha_envio3': datetime.today()})
            if record.company_signed_user_id:
                record.email_signed_maihue = record.company_signed_user_id.email
                record.write({'state_firm4': 'T'})
            if record.firma_type.code in ['simple', 'fisica_cliente']:
                record.write({'signed_maihue': True, 'company_signed_date': datetime.today().date(), 'state_firm4': 'M'})
            #record.onchange_status()
            record.send_values_to_log()


    def onchange_status(self):
        for record in self:
            if record.company_signed_user_id:
                record.write({'state_firm4': 'T'})
            if record.partner_signed_user_id:
                record.write({'state_firm1': 'T', 'fecha_envio1': datetime.today()})
            if record.company_signed_user_dos_id:
                record.write({'state_firm2': 'T', 'fecha_envio2': datetime.today()})
            if record.company_signed_user_tres_id:
                record.write({'state_firm3': 'T', 'fecha_envio3': datetime.today()})

    def send_values_to_log(self):
        for record in self:
            signature_obj = record.env['your.signature.log']
            num = signature_obj.search([('extra_id', '=', record.id)])
            name = 1
            if num:
                name = int(len(num)) + 1
            if record.firma == 'digital':
                signature_values = {
                    'name': str(record.name), # + ' V'+ str(name),
                    'partner_signed_user_id': record.partner_signed_user_id.id,
                    'fecha_envio1': record.fecha_envio1,
                    'company_signed_user_dos_id': record.company_signed_user_dos_id.id,
                    'fecha_envio2': record.fecha_envio2,
                    'company_signed_user_tres_id': record.company_signed_user_tres_id.id,
                    'fecha_envio3': record.fecha_envio3,
                    'fecha_repres1': record.fecha_repres1,
                    'fecha_repres2': record.fecha_repres2,
                    'fecha_repres3': record.fecha_repres3,
                    'company_signed_user_id': record.company_signed_user_id.id,
                    'company_signed_date': record.company_signed_date,
                    'file_report': record.file_report,
                    'file_name': record.file_name,
                    'extra_id': record.id,
                    'id_contrato': record.id_contrato,
                    'status': 'to_sign',
                    'type': 'digital',
                    'firma_type': record.firma_type.id
                }
            else:
                signature_values = {
                    'name': str(record.name), # + ' V'+ str(name),
                    'partner_signed_user_id': record.partner_signed_user_id.id,
                    'fecha_envio1': record.fecha_envio1,
                    'company_signed_user_dos_id': record.company_signed_user_dos_id.id,
                    'fecha_envio2': record.fecha_envio2,
                    'company_signed_user_tres_id': record.company_signed_user_tres_id.id,
                    'fecha_envio3': record.fecha_envio3,
                    'fecha_repres1': record.fecha_repres1,
                    'fecha_repres2': record.fecha_repres2,
                    'fecha_repres3': record.fecha_repres3,
                    'company_signed_user_id': record.company_signed_user_id.id,
                    'company_signed_date': record.company_signed_date,
                    'file_report': record.file_report,
                    'file_name': record.file_name,
                    'extra_id': record.id,
                    'id_contrato': record.id_contrato,
                    'status': 'to_sign',
                    'type': 'fisica',
                    'firma_type': record.firma_type.id
                }
            signature_obj.create(signature_values)

    def default_get(self, default_fields):
        res = super(AgreementExtra, self).default_get(default_fields)
        leader = self.env['res.users'].search([('lead_your_firm', '=', True)])
        res.update({
            'company_signed_user_id': leader.id,
            'name': self.agreement_id.name,
        })
        return res

    def obtain_document(self):
        for record in self:
            config = record.env['ir.config_parameter'].sudo()
            if not config.get_param('is_firma'):
                    raise UserError('Operacion no permitida, contacte al Administrador para activar las credenciales.')
            dict_conf = record.return_values_your_signature()
            headers = {
                    'x-api-key': dict_conf.get('api_key', False),
                    'secret': dict_conf.get('secret', False),
                    'Content-Type': 'application/json',
            }
            url = dict_conf.get('url') + 'api/documents/get?id=' + record.id_contrato
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise UserError(response.text)
            else:
                count = 0
                dict_list = json.loads(response.text.encode('utf8'))
                firmantes = dict_list.get('feaSigners')
                document = dict_list.get('document')
                for fir in firmantes:
                    if fir.get('name') == record.partner_signed_user_id.name:
                        if fir.get('ready') == True:
                            count += 1
                            record.write({'state_firm1': 'M', 'fecha_repres1': datetime.today()})
                            signature_obj = record.env['your.signature.log'].search([('status', '!=', 'cancelled'), ('id_contrato', '=', record.id_contrato)])
                            if signature_obj:
                                for sig in signature_obj:
                                    sig.write({'signed_client': True})
                    if fir.get('name') == record.company_signed_user_dos_id.name:
                        if fir.get('ready') == True:
                            count += 1
                            record.write({'state_firm2': 'M', 'fecha_repres2': datetime.today()})
                            signature_obj = record.env['your.signature.log'].search([('status', '!=', 'cancelled'), ('id_contrato', '=', record.id_contrato)])
                            if signature_obj:
                                for sig in signature_obj:
                                    sig.write({'signed_client': True})
                    if fir.get('name') == record.company_signed_user_tres_id.name:
                        if fir.get('ready') == True:
                            count += 1
                            record.write({'state_firm3': 'M', 'fecha_repres3': datetime.today()})
                            signature_obj = record.env['your.signature.log'].search([('status', '!=', 'cancelled'), ('id_contrato', '=', record.id_contrato)])
                            if signature_obj:
                                for sig in signature_obj:
                                    sig.write({'signed_client': True})
                    if fir.get('name') == record.company_signed_user_id.name:
                        if fir.get('ready') == True:
                            count += 1
                            record.write({'state_firm4': 'M', 'company_signed_date': datetime.today()})
                            signature_obj = record.env['your.signature.log'].search([('status', '!=', 'cancelled'), ('id_contrato', '=', record.id_contrato)])
                            if signature_obj:
                                for sig in signature_obj:
                                    sig.write({'signed_maihue': True})
                    if count == len(firmantes):
                        record.write({'status': 'signed', 'file_report_signed': document, 'company_signed_date': datetime.today()})
                        signature_obj = record.env['your.signature.log'].search([('status', '!=', 'cancelled'), ('id_contrato', '=', record.id_contrato)])
                        print(signature_obj)
                        if signature_obj:
                            record.write({'status':'signed'})
                            for sig in signature_obj:
                                sig.write({'status': 'signed', 'signature_Date': datetime.today(), 'file_report_signed': document, 'company_signed_date': datetime.today()})

    #### CANCELAR FIRMA DIGITAL #####
    def cancel_contract_digital(self):
        for record in self:
            config = record.env['ir.config_parameter'].sudo()
            signature_obj = record.env['your.signature.log']
            dict_conf = record.return_values_your_signature()
            headers = {
                'x-api-key': dict_conf.get('api_key', False),
                'secret': dict_conf.get('secret', False),
                'Content-Type': 'application/json',
            }
            if not config.get_param('is_firma'):
                raise UserError('Operacion no permitida, contacte al Administrador para activar las credenciales.')
            url = dict_conf.get('url') + 'api/documents/cancel?id=' + record.id_contrato
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise UserError(response.text)
            else:
                search_signature = signature_obj.search([('id_contrato', '=', record.id_contrato), ('type', '=', record.firma), ('firma_type', '=', record.firma_type.id), ('status', '!=', 'signed')])
                if record.company_signed_user_id:
                    record.email_signed_maihue = record.company_signed_user_id.email
                    record.write({'company_signed_date': False, 'state_firm4': 'cancelled'})
                if record.partner_signed_user_id:
                    record.email_signed_user = record.partner_signed_user_id.email
                    record.write({'fecha_repres1': False, 'state_firm1': 'cancelled'})
                if record.company_signed_user_dos_id:
                    record.email_signed_user_dos = record.company_signed_user_dos_id.email
                    record.write({'fecha_repres2': False, 'state_firm2': 'cancelled'})
                if record.company_signed_user_tres_id:
                    record.email_signed_user_tres = record.company_signed_user_tres_id.email
                    record.write({'fecha_repres3': False, 'state_firm3': 'cancelled'})
                if search_signature:
                    for search in search_signature:
                        search.write({'status': 'cancelled', 'cancellation_date': datetime.today(), 'file_report_signed': record.file_report_signed})
                    split = 'V' + str(record.version)
                    if split in str(record.name):
                        name = str(record.name).split(split)[0].strip()
                    else:
                        name = str(record.name).strip()
                    version = record.version + 1
                    record.write({'id_contrato': False,
                                  'visible': False,
                                  'status':'cancelled',
                                  'name': name + ' V' + str(version),
                                  'version': version,
                                  'signed_client': False,
                                  'signed_maihue': False})

    ###### cancelar firma fisica #####
    def cancel_contract(self):
        for record in self:
            signature_obj = record.env['your.signature.log']
            search_signature = signature_obj.search([('type', '=', record.firma), ('firma_type', '=', record.firma_type.id), ('status', '!=', 'signed')])
            if record.company_signed_user_id:
                record.email_signed_maihue = record.company_signed_user_id.email
                record.write({'company_signed_date': False, 'state_firm4': 'cancelled'})
            if record.partner_signed_user_id:
                record.email_signed_user = record.partner_signed_user_id.email
                record.write({'fecha_repres1': False,'fecha_envio1': False, 'state_firm1': 'cancelled'})
            if record.company_signed_user_dos_id:
                record.email_signed_user_dos = record.company_signed_user_dos_id.email
                record.write({'fecha_repres2': False,'fecha_envio2': False,'state_firm2': 'cancelled'})
            if record.company_signed_user_tres_id:
                record.email_signed_user_tres = record.company_signed_user_tres_id.email
                record.write({'fecha_repres3': False,'fecha_envio3': False,'state_firm3': 'cancelled'})
            if search_signature:
                for search in search_signature:
                    search.write({'status': 'cancelled', 'cancellation_date': datetime.today(), 'file_report_signed': record.signed_contract, 'file_name2': record.signed_contract_filename})
                split = 'V' + str(record.version)
                if split in str(record.name):
                    name = str(record.name).split(split)[0].strip()
                else:
                    name = str(record.name).strip()
                version = record.version + 1
                record.write({'visible': False,
                              'status':'cancelled',
                              'name': name + ' V' + str(version),
                              'version': version,
                              'signed_client': False,
                              'signed_maihue': False,
                              'signed_contract': False})

    #### CANCELAR FIRMA EXCEPCION POST FIRMA#######
    def cancel_exception_contract(self):
        for record in self:
            signature_obj = record.env['your.signature.log']
            search_signature = signature_obj.search([('type', '=', record.firma), ('firma_type', '=', record.firma_type.id), ('status', '=', 'signed')])
            if record.company_signed_user_id:
                record.email_signed_maihue = record.company_signed_user_id.email
                record.write({'company_signed_date': False, 'state_firm4': 'cancelled'})
            if record.partner_signed_user_id:
                record.email_signed_user = record.partner_signed_user_id.email
                record.write({'fecha_repres1': False,'fecha_envio1': False, 'state_firm1': 'cancelled'})
            if record.company_signed_user_dos_id:
                record.email_signed_user_dos = record.company_signed_user_dos_id.email
                record.write({'fecha_repres2': False,'fecha_envio2': False,'state_firm2': 'cancelled'})
            if record.company_signed_user_tres_id:
                record.email_signed_user_tres = record.company_signed_user_tres_id.email
                record.write({'fecha_repres3': False,'fecha_envio3': False,'state_firm3': 'cancelled'})
            if search_signature:
                for search in search_signature:
                    search.write({'status': 'cancelled_signed', 'cancellation_date': datetime.today(), 'file_report_signed': record.signed_contract, 'file_name2': record.signed_contract_filename})
                split = 'V' + str(record.version)
                if split in str(record.name):
                    name = str(record.name).split(split)[0].strip()
                else:
                    name = str(record.name).strip()
                version = record.version + 1
                record.write({'visible': False,
                              'status':'cancelled',
                              'name': name + ' V' + str(version),
                              'version': version,
                              'signed_client': False,
                              'signed_maihue': False,
                              'signed_contract': False})

    ###### CANCELAR FIRMA DIGITAL CONTINGENCIA ########
    def cancel_document_digital(self):
        for record in self:
            signature_obj = record.env['your.signature.log']
            search_signature = signature_obj.search([('id_contrato', '=', record.id_contrato), ('status', '!=', 'signed')])
            if record.company_signed_user_id:
                record.email_signed_maihue = record.company_signed_user_id.email
                record.write({'company_signed_date': False, 'state_firm4': 'cancelled'})
            if record.partner_signed_user_id:
                record.email_signed_user = record.partner_signed_user_id.email
                record.write({'fecha_repres1': False, 'state_firm1': 'cancelled'})
            if record.company_signed_user_dos_id:
                record.email_signed_user_dos = record.company_signed_user_dos_id.email
                record.write({'fecha_repres2': False, 'state_firm2': 'cancelled'})
            if record.company_signed_user_tres_id:
                record.email_signed_user_tres = record.company_signed_user_tres_id.email
                record.write({'fecha_repres3': False, 'state_firm3': 'cancelled'})
            if search_signature:
                for search in search_signature:
                    search.write({'status': 'to_cancelled_cont', 'cancellation_date': datetime.today()})
                split = 'V' + str(record.version)
                if split in str(record.name):
                    name = str(record.name).split(split)[0].strip()
                else:
                    name = str(record.name).strip()
                version = record.version + 1
                record.write({'id_contrato': False,
                              'visible': False,
                              'status':'cancelled',
                              'name': name + ' V' + str(version),
                              'version': version,
                              'signed_client': False,
                              'signed_maihue': False})

    def send_signed_document_to_partner(self):
        template_id = self.env.ref('your_signature.your_signature_send_signed_document')
        IrAttachment = self.env['ir.attachment']
        MailMail = self.env['mail.mail']
        for record in self:
            if record.file_report_signed:
                file_report_signed = base64.b64decode(record.file_report_signed)
                pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(file_report_signed))
                pdf_writer = PyPDF2.PdfFileWriter()
                password = record.agreement_id.partner_id.vat[:4]
                pdf_writer.encrypt(password)
                for page_num in range(pdf_reader.numPages):
                    pdf_writer.addPage(pdf_reader.getPage(page_num))
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                encrypted_data = output_buffer.getvalue()
                encrypted_data_encoded = base64.b64encode(encrypted_data)
                document_attachment = IrAttachment.create({
                    'name': record.file_name,
                    'res_model': record._name,
                    'res_id': record.id,
                    'type': 'binary',
                    'datas': encrypted_data_encoded
                })
                mail_id = template_id.send_mail(record.id, force_send=True, email_values={'attachment_ids': [document_attachment.id]})
                email = MailMail.search([('id', '=', mail_id)])
                if email.state == 'exception':
                    record.message_post(body=_('Documento no enviado al cliente'))
                    record.message_post(body=email.failure_reason)
                    record.status_send_document = 'failed'
                else:
                    record.message_post(body=_('Documento Firmado enviado al cliente'))
                    record.status_send_document = 'send'