
import requests
from odoo.exceptions import UserError
from stdnum import get_cc_module
from odoo.exceptions import ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
import csv
import base64
import io
from odoo.tools import float_is_zero, pycompat
from datetime import date
from datetime import datetime

url_kushki = "http://api-uat.kushkipagos.com"

class PaymentMethodPartner(models.Model):
    _name = 'payment.method.partner'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payment Method Partner'

    def _default_payment_acquirer(self):
        payment = self.env['payment.acquirer'].search([('provider', '=', 'kushki')]).id
        return payment

    token_card = fields.Char(string='Suscripción', required=True)
    date_subscription = fields.Date(string='Customer Signature Date')
    card_number_user = fields.Char(string='Número de Tarjeta / Cuenta', size=20, tracking=1)
    card_number = fields.Char(string='Número de Tarjeta / Cuenta', size=20, tracking=1)
    to_visible = fields.Boolean('To Visible')
    state = fields.Selection(string='Estado', selection=[('draft', 'Borrador'),('env', 'Enviado a Validación'),('refused', 'Validación Rechazada'),('active', 'Activa'), ('cancel', 'Cancelada'), ('request', 'Solicitud de Cancelacion')], readonly=True, copy=False, default="draft", tracking=2)
    # status = fields.Char(string='Status', help="Último estado de cobro a la tarjeta", tracking=3)
    state_link = fields.Selection(selection=[('link', 'Vínculada'), ('unrelated', 'Desvínculada')], store=True, string="Estado Vinculación", compute='_compute_contract_ids')
    brand = fields.Char(string='Marca', tracking=4)
    bank = fields.Char(string='Banco', tracking=5)
    card_type = fields.Selection(string="Tipo de Tarjeta", selection=[('credit', 'Crédito'), ('debito', 'Débito')], tracking=6)
    type_subscription = fields.Selection(string="Intermediario", selection=[('on_demand', 'PAT Kushki - Bajo Demanda'), ('transdata', 'PAT Transdata'), ('webpay', 'PAC Kushki - Webpay'), ('santander', 'PAC Multibanco Santander')], tracking=7)
    type_subscription_contract = fields.Many2one('agreement.payment.method', string="Método de Pago", domain=[("id", "in", ['1','2','3','4'])])
    type_subscription_new = fields.Many2one('agreement.payment.intermediary', string="Servicio del proveedor")
    expiration_date = fields.Char(string="Fecha Vencimiento")
    partner_id = fields.Many2one('res.partner', string='Contacto')
    partner_id_vat = fields.Char(string='RUT')
    name = fields.Char(string="Name", tracking=9)
    last_name = fields.Char(string="Apellido", tracking=10)
    email = fields.Char(string="Correo", tracking=11)
    document_number = fields.Char(string="RUT", tracking=12)
    phone_number = fields.Char(string="Teléfono", tracking=13)
    method_name = fields.Char(string="Método")
    contract_ids = fields.One2many('agreement', 'card_number', string='Contratos', tracking=14)
    history_contract_ids = fields.One2many('history.contracts', 'payment_partner_id', string='Historial Contratos')
    subscription_type = fields.Selection(string='Tipo de Suscripción', selection=[('tc', 'TC'), ('webpay', 'Webpay')], tracking=15)
    payment_acquirer_id = fields.Many2one('payment.acquirer', 'Payment', default=_default_payment_acquirer)
    relationship = fields.Selection(selection=[('iam', 'Soy yo'), ('legal', 'Representante Legal'), ('mom', 'Madre'), ('dad', 'Padre'), ('sister', 'Hermana'), ('brother', 'Hermano')], string='Parentesco')
    country_id = fields.Many2one('res.country', 'Pais', related='partner_id.country_id')
    bank_id = fields.Many2one('kushki.payment.bank', 'Bank')
    payment_account = fields.Many2one('payment.account.kushki', 'TC Mark / Account')
    bank_code = fields.Char(related='bank_id.code')
    create_date = fields.Datetime("Creation Date", readonly=True, default=datetime.today())
    due_date = fields.Date("Due Date")
    status_detail = fields.Char(string='Status Detail Payment Method')
    status_payment = fields.Char(string='State Payment Method')
    # status_last = fields.Char(string='Status Detail Last Response Collection')
    payment_mt_ids = fields.One2many('method.transdata', 'method_id', string='Cargas Transdata', copy=True,
                                     auto_join=True)
    export_method = fields.Boolean('Exportación Masiva', default=False)
    file_method = fields.Many2one('payment.method.file', string='Archivo Metodos de Pago', ondelete='cascade')
    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer')
    domain_payment_method = fields.Many2many('agreement.payment.method', string='Dominio Metodo de pago')
    domain_acquirer = fields.Many2many('payment.acquirer', string='Dominio acquirer')
    domain_intermediary = fields.Many2many('agreement.payment.intermediary', string='Dominio intermediary')
    payment_td_ids = fields.One2many('payment.log', 'move_td_id', string='Pagos Automáticos', copy=True,
                                     auto_join=True)

    @api.onchange('type_subscription_contract', 'acquirer_id')
    def onchange_type_subscription_contract(self):
        self.domain_payment_method = self.domain_intermediary = self.domain_acquirer = False
        if self.type_subscription_contract and self.acquirer_id:
            if self.type_subscription_new.acquirer_id.id != self.acquirer_id.id or self.type_subscription_new.payment_method.id != self.type_subscription_contract.id:
                self.type_subscription_new = False
            acquirer_ids = self.env['payment.acquirer'].search([('state', 'not in', ['disabled']),('payment_method_ids', 'in', self.type_subscription_contract.ids)])
            self.domain_acquirer = [(6, 0, acquirer_ids.ids)] if acquirer_ids else False
            payment_method_ids = self.env['agreement.payment.method'].search([('id', 'in', self.acquirer_id.payment_method_ids.ids)]) if self.acquirer_id.payment_method_ids else False
            self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False
            intermediry_ids = self.env['agreement.payment.intermediary'].search([('acquirer_id', 'in', self.acquirer_id.ids),('payment_method', 'in', self.type_subscription_contract.ids)])
            self.domain_intermediary = [(6, 0, intermediry_ids.ids)] if intermediry_ids else False
        elif not self.type_subscription_contract and self.acquirer_id:
            if self.type_subscription_new.acquirer_id.id != self.acquirer_id.id:
                self.type_subscription_new = False
            acquirer_ids = self.env['payment.acquirer'].search([('state', 'not in', ['disabled'])])
            self.domain_acquirer = [(6, 0, acquirer_ids.ids)] if acquirer_ids else False
            payment_method_ids = self.env['agreement.payment.method'].search([('id', 'in', self.acquirer_id.payment_method_ids.ids)]) if self.acquirer_id.payment_method_ids else False
            self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False
            intermediry_ids = self.env['agreement.payment.intermediary'].search([('acquirer_id', 'in', self.acquirer_id.ids)])
            self.domain_intermediary = [(6, 0, intermediry_ids.ids)] if intermediry_ids else False
        elif self.type_subscription_contract and not self.acquirer_id:
            if self.type_subscription_new.payment_method.id != self.type_subscription_contract.id:
                self.type_subscription_new = False
            acquirer_ids = self.env['payment.acquirer'].search([('state', 'not in', ['disabled']),('payment_method_ids', 'in', self.type_subscription_contract.ids)])
            self.domain_acquirer = [(6, 0, acquirer_ids.ids)] if acquirer_ids else False
            payment_method_ids = self.env['agreement.payment.method'].search([])
            self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False
            intermediry_ids = self.env['agreement.payment.intermediary'].search([('payment_method', 'in', self.type_subscription_contract.ids)])
            self.domain_intermediary = [(6, 0, intermediry_ids.ids)] if intermediry_ids else False
        else:
            acquirer_ids = self.env['payment.acquirer'].search([('state', 'not in', ['disabled'])])
            self.domain_acquirer = [(6, 0, acquirer_ids.ids)]
            payment_method_ids = self.env['agreement.payment.method'].search([])
            self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False
            intermediry_ids = self.env['agreement.payment.intermediary'].search([])
            self.domain_intermediary = [(6, 0, intermediry_ids.ids)] if intermediry_ids else False

    @api.onchange('type_subscription_new')
    def onchange_type_subscription_new(self):
        if self.type_subscription_new:
            self.acquirer_id = self.type_subscription_new.acquirer_id.id
            self.type_subscription_contract = self.type_subscription_new.payment_method.id
        self.onchange_type_subscription_contract()


    @api.onchange('acquirer_id')
    def onchange_acquirer_id(self):
        if self.acquirer_id:
            payment_method_ids = self.env['agreement.payment.method'].search([('id', 'in', self.acquirer_id.payment_method_ids.ids)]) if self.acquirer_id.payment_method_ids else False
            self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False
        else:
            payment_method_ids = self.env['agreement.payment.method'].search([])
            self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False

    # @api.onchange('type_subscription_new')
    # def onchange_type_subscription_new(self):
    #     if self.type_subscription_new:
    #         payment_method_ids = self.env['agreement.payment.method'].search([('id', 'in', self.acquirer_id.payment_method_ids.ids)]) if self.acquirer_id.payment_method_ids else False
    #         self.domain_payment_method = [(6, 0, payment_method_ids.ids)] if payment_method_ids else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'card_number' in vals:
                xs = ''
                len_total = len(vals['card_number'])
                x = int(len_total) - 5
                for y in range(x):
                    xs = str(xs)+'X'
                vals['card_number_user'] = str(vals['card_number'][0]) + str(xs) + str(vals['card_number'][-4:])
                vals['to_visible'] = True
        return super(PaymentMethodPartner, self).create(vals_list)

    def write(self, vals):
        if vals.get('card_number', False):
            x = 'XXXXXX'
            vals['card_number_user'] = str(vals['card_number'][0]) + str(x) + str(vals['card_number'][-4:])
            vals['to_visible'] = True
        return super(PaymentMethodPartner, self).write(vals)

    def method_csv_write_rows(self, rows, lineterminator=u'\r'):
        """
        Write FEC rows into a file
        It seems that Bercy's bureaucracy is not too happy about the
        empty new line at the End Of File.

        @param {list(list)} rows: the list of rows. Each row is a list of strings
        @param {unicode string} [optional] lineterminator: effective line terminator
            Has nothing to do with the csv writer parameter
            The last line written won't be terminated with it

        @return the value of the file
        """
        fecfile = io.BytesIO()
        writer = pycompat.csv_writer(fecfile, delimiter=',', lineterminator='')

        rows_length = len(rows)
        for i, row in enumerate(rows):
            if not i == rows_length - 1:
                # jamie = row[:-1]
                # row[-1] += lineterminator
                writer.writerow(row)
                writer.writerow(lineterminator)
            else:
                writer.writerow(row)

        fecvalue = fecfile.getvalue()
        fecfile.close()
        return fecvalue

    def action_method_payment(self):
        rows_to_write = []
        now = datetime.now()
        filename = 'G-Method Payment-%s.csv' % (str(now.strftime("%d/%m/%y-%H:%M:%S")))
        for method in self:
            if method.partner_id.credit_card_status != 'bloqueada':
                if method.export_method == False:
                    row_list = [
                        method.token_card,
                        method.partner_id_vat,
                        method.card_number,
                        method.due_date,
                        method.status_payment,
                        method.status_detail
                    ]
                    method.write({'export_method': True})
                    rows_to_write.append(row_list)
        if len(rows_to_write) > 0:
            fecvalue = self.method_csv_write_rows(rows_to_write)
            attachment = self.env['ir.attachment'].create({
                'res_model': 'payment.method.partner',
                'name': filename,
                'datas': base64.b64encode(fecvalue),
                'db_datas': filename,
            })
            simplified_form_view = self.env.ref(
                'payment_kushki.view_attachment_method_form')
            action = {
                'name': _('Payment Method File'),
                'view_mode': 'form',
                'view_id': simplified_form_view.id,
                'res_model': 'ir.attachment',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': attachment.id,
            }
            file_values = {
                'name': filename,
                #'type': 'transbank',
                'export_to_transbank': True,
                'export_date': now,
                'db_datas': base64.b64encode(fecvalue),
                'datas': base64.b64encode(fecvalue),
                'state': 'pen',
                'down_user': self.create_uid.id,
            }
            file_method = self.env['payment.method.file'].create(file_values)
            for move in self:
                move.write({'file_method': file_method.id})
            return action

    def valida(self):
        self.write({'state': 'env'})

    def refused(self):
        self.write({'state': 'refused'})

    def act(self):
        self.write({'state': 'active'})

    def cancel(self):
        self.write({'state': 'cancel'})

    def request(self):
        self.write({'state': 'request'})

    # def create_subscription_ondemand(self, response):
    #     response_subscription_dict = response.json()
    #     contact = response_subscription_dict['contactDetails']
    #     pat = self.env['agreement.payment.method'].search([('code', '=', 'pat')])
    #     today = date.today()
    #     str_today = datetime.strftime(today, '%Y-%m-%d')
    #     # fname, lname = post['username'].split(' ')
    #     # number = post['codigo'] + post['phone_credit']
    #     self.create({
    #         'date_subscription': today,
    #         'partner_id': partner.id,
    #         'partner_id_vat': partner.vat,
    #         'token_card': subscriptionId,
    #         'card_number': response['maskedCardNumber'],
    #         'type_subscription': 'on_demand',
    #         'type_subscription_contract': pat.id if pat else False,
    #         'bank': response['bank'],
    #         'brand': response['brand'],
    #         'card_type': response['cardType'],
    #         'status': 'active',
    #         'name': contact['firstName'],
    #         'last_name': contact['lastName'],
    #         'phone_number': contact['phoneNumber'],
    #         'document_number': contact['documentNumber'],
    #         'email': contact['email'],
    #         'relationship': post['relationship']
    #     })
    
    def payment_info(self):
        values = {}
        values['name'] = self.name
        values['date_subscription'] = self.date_subscription
        values['token_card'] = self.token_card
        values['card_number'] = self.card_number
        values['brand'] = self.brand
        values['state'] = self.state
        values['type_subscription_contract'] = {
            'name': self.type_subscription_contract.name,
            'id': self.type_subscription_contract.id
        }
        values['partner'] = {
            'name': self.partner_id.name,
            'vat': self.partner_id.vat,
            'email': self.partner_id.email,
            'phone': self.partner_id.phone
        }
        values['type_subscription_contracts'] = self.type_subscription_contract.search([]).read(['name'])
        if self.contract_ids:
            contracts = self.env['agreement'].browse(self.contract_ids.ids)
            values['contracts'] = contracts.read(['name'])
        else:
            values['contracts'] = False
        return values

    def name_get(self):
        res = []
        for card in self:
            card_number = card.card_number_user if card.card_number_user else card.card_number
            name = card_number
            if card.type_subscription_new:
                name += ' ' + card.type_subscription_new.name
            res.append([card.id, name])
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_id_vat = self.partner_id.vat

    # @api.onchange('type_subscription_contract')
    # def onchange_type_subscription_contract(self):
    #     res = {}
    #     if self.type_subscription_contract:
    #         if self.type_subscription_contract.id != self.type_subscription_new.payment_method.id:
    #             self.type_subscription_new = ''

    # @api.model
    # def default_get(self, fields):
    #     res = super(Agreement, self).default_get(fields)
    #     if res.is_template:
    #         if not res.parent_agreement_id:
    #             templates = self.env['agreement'].search([('is_template', '=', True), ('parent_template_id', '=', False)])
    #             res['domain'] = {
    #                 'payment_period_domain': [('id', 'in', payment_period.ids)],
    #                 'payment_method_domain': [('id', 'in', payment_method.ids)],
    #                 'payment_deadline_domain': [('id', 'in', payment_deadline.ids)],
    #                 # 'type_contrib': [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)],
    #                 # 'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
    #                 # 'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
    #                 'type_contrib_domain': [('id', 'in', type_contrib.ids)]}
    #     return res

    @api.depends('contract_ids')
    def _compute_contract_ids(self):
        for record in self:
            if record.contract_ids:
                record.state_link = 'link'
            else:
                record.state_link = 'unrelated'

    def cancel_subscription(self):
        for record in self:
            if not record.contract_ids:
                headers = {'Private-Merchant-Id': record.payment_acquirer_id.kushki_secret_key, 'content-type': "application/json"}
                response = requests.delete(url_kushki + "/subscriptions/v1/card/" + record.token_card, headers=headers)
                if response.status_code != 204:
                    re = response.json()
                    raise UserError('{} \n {}'.format(re['code'], re['message']))
                record.status = 'cancel'
            else:
                raise UserError('Esta tarjeta esta asociada a %d contratos. Antes de poder cancelar la suscripcion debe crear una suscripcion con una nueva tarjeta y reemplazarla en los contratos asignados')


    @api.onchange('document_number')
    def validate_rut(self):
        mod = get_cc_module('cl', 'rut')
        if self.document_number:
            val_rut = mod.is_valid(self.document_number)
            if val_rut == False:
                raise UserError("El rut ingresado |{0}| no es valido".format(self.document_number))

class PaymentTransdata(models.Model):
    _name = "payment.log"
    _description = "Log transdata"

    move_td_id = fields.Many2one('payment.method.partner', string='Metodo', required=False, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Char(
        string="Detalle estado",
        required=False)
    rut_partner = fields.Char(
        string="Rut",
        required=False)
    cod_aut = fields.Char(
        string="Codigo autorización",
        required=False)
    ref_int = fields.Char(
        string="Referencia Interna",
        required=False)
    amount = fields.Float(
        string="Monto")
    date_payment = fields.Date('Fecha Cobro', help="Fecha de inicio del movimiento de personal")
    import_date = fields.Date(string='Fecha Importación', readonly=True,
                              help="Fecha de la ultima importación.")
    status_type = fields.Selection([
        ('0', 'APROBADA'),
        ('11', 'INST. INCOMPLETA'),
        ('16', 'RECHAZO'),
    ], required=False, string="Estado")
    type = fields.Selection([
        ('transbank', 'Transdata PAT'),
        ('santander', 'Santander PAC'),
        ('kusca', 'Kusky Cajita'),
        ('kusweb', 'Kusky Webpay')], "Tipo")
    method_payment = fields.Char(string='Metodo de Pago')

class PaymentTransdataFile(models.Model):
    _name = "payment.method.file"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Archivos Metodos de Pago"

    name = fields.Char(
        string="Nombre Archivo",
        required=True)
    code = fields.Char(
        string="Codigo Archivo",
        required=False)
    export_date = fields.Date(string='Fecha Export', readonly=True,
                              help="Fecha de la ultima exportación.")
    import_date = fields.Date(string='Fecha Import', readonly=True,
                              help="Fecha de la ultima importación.")
    export_status = fields.Selection([
        ('0', 'APROBADA'),
        ('11', 'INST. INCOMPLETA'),
        ('16', 'RECHAZO')], "Estado Importacion")
    desc_status = fields.Char(string="Descripcion estado")
    export_to_transbank = fields.Boolean(string='Exportado',
                                         help='Set True if this document type and can be imported on transbank'
                                         )
    type = fields.Selection([
        ('transbank', 'Transdata PAT'),
        ('santander', 'Santander PAC'),
        ('kusca', 'Kusky Cajita'),
        ('kusweb', 'Kusky Webpay')], "Tipo")
    state = fields.Selection([
        #('draft', 'Pendiente'),
        ('pen', 'Pendiente'),
        ('ok', 'Terminado')], "Estado")
    datas = fields.Binary(string='File Content (base64)')
    filename = fields.Char(string='Filename', size=256, readonly=False)
    db_datas = fields.Binary('Database Data', attachment=False)
    down_user = fields.Many2one('res.users', string='Download user', required=False)
    unpload_datas = fields.Binary(string='File Content (base64)')
    unpload_user = fields.Many2one('res.users', string='Unpload user', required=False)
    unpload_filename = fields.Char(string='Filename', size=256, readonly=False)
    unpload_db_datas = fields.Binary('Database Data', attachment=False)

class MethodTransdata(models.Model):
    _name = "method.transdata"
    _description = "Metodos transdata"

    method_id = fields.Many2one('payment.method.partner', string='Method', required=False, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Char(
        string="Detalle estado",
        required=False)
    type_mov = fields.Char(
        string="Tipo de Movimiento",
        required=False)
    man_fisico = fields.Char(
        string="Mandato Fisico",
        required=False)
    rut_partner = fields.Char(
        string="Rut",
        required=False)
    cod_estado = fields.Char(
        string="Codigo estado",
        required=False)
    cod_servi = fields.Char(
        string="Codigo Servicio",
        required=False)
    ref_int = fields.Char(
        string="Referencia Interna",
        required=False)
    id_transaccion = fields.Char(
        string="id_transaccion",
        required=False)
    amount = fields.Float(
        string="Monto")
    date_aprob = fields.Date('Fecha Aprobacion')
    date_ven = fields.Date('Fecha Vencimiento')
    status_type = fields.Selection([
        ('0', 'APROBADA'),
        ('11', 'INST. INCOMPLETA'),
        ('16', 'RECHAZO'),
    ], required=False, string="Estado")
    type = fields.Selection([
        ('transbank', 'Transdata PAT'),
        ('santander', 'Santander PAC'),
        ('kusca', 'Kusky Cajita'),
        ('kusweb', 'Kusky Webpay')], "Tipo")

class KushkiPaymentBank(models.Model):
    _name = 'kushki.payment.bank'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, string='Bank Name')
    code = fields.Char(required=True, string='Bank ID')


class PaymentAccountKushki(models.Model):
    _name = 'payment.account.kushki'

    name = fields.Char(required=True, string='Name')

# class PaymentAcquirer(models.Model):
#     _name = 'payment.acquirer'
#
#     country_id_domain = fields.Many2many('res.country', 'method_country_rel', 'method_id',
#                                              'country_id',
#                                              string='Países Permitidos')
