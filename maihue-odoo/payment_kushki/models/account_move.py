from odoo import api, fields, models, _
import requests
import json
from odoo.exceptions import UserError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)

url_kushki = "http://api-uat.kushkipagos.com"

class AccountMove(models.Model):
    _inherit = 'account.move'

    def my_button(self):
        button = self.env.ref('payment_kushki.account_move_wizard_view_wzd')
        return{
            'name': _('Payment methods'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move.wizard',
            'views': [(button.id, 'form')],
            'target': 'new',
        }


    def _default_payment_acquirer(self):
        payment = self.env['payment.acquirer'].search([('provider', '=', 'kushki')]).id
        return payment

    history_payment_ids = fields.One2many('move.payment.history', 'move_id', 'History payments')
    payment_acquirer_id = fields.Many2one('payment.acquirer', 'Payment', default=_default_payment_acquirer)
    payment_acquirer = fields.Selection(related='payment_acquirer_id.provider')
    method_payment_id = fields.Many2one('payment.method.partner', 'Número de Tarjeta / Cuenta')
    intermediary_id = fields.Many2one(related='method_payment_id.type_subscription_new', string='Intermediario')
    portal_payment = fields.Boolean(string='Pago Portal', default=True)
    status_payment = fields.Selection(string='Estado de Cobro Fact', selection=[('pending', 'Pendiente Intento de Cobro'),
                                                                ('approved', 'Aprobado'),
                                                                ('send_paid', 'Enviado a Cobro'),
                                                                ('rejected', 'Rechazado')], copy=False, default='pending')
    detall_status_payment = fields.Char(string="Detalle Estado de Cobro Fact", required=False)
    status_method = fields.Char(related='method_payment_id.status_payment', string="Ultimo Estado de Cobro Metodo de pago")
    status_method_detail = fields.Char(related='method_payment_id.status_detail', string="Detalle Ultimo Estado de Cobro Metodo de pago")
    payment_period = fields.Many2one(
        "agreement.payment.period", required=False,
        string="Periodicidad de Pago")
    payment_method = fields.Many2one(
        "agreement.payment.method", required=False,
        string="Método de Pago")
    ajust_total = fields.Monetary(string='Total a Cobrar', store=True, readonly=True)
    tarj_dis = fields.Selection(selection=[
        ('igual', 'Igual'),
        ('dif', 'Distinta'),
    ], string='Tarjeta Distinta')
    method_payment_id_old = fields.Many2one('payment.method.partner', 'Número de Tarjeta / Cuenta Anterior')
    intermediary_id_old = fields.Many2one(related='method_payment_id_old.type_subscription_new', string='Intermediario Anterior')
    status_payment_old = fields.Selection(string='Estado de Cobro Anterior', selection=[('pending', 'Pendiente Intento de Cobro'),
                                                                           ('approved', 'Aprobado'),
                                                                           ('send_paid', 'Enviado a Cobro'),
                                                                           ('rejected', 'Rechazado')], copy=False)
    detall_status_payment_old = fields.Char(string="Detalle Estado de Cobro Anterior", required=False)
    method_payment_id_alt = fields.Many2one('payment.method.partner', 'Número de Tarjeta / Cuenta Alternativo')
    intermediary_id_alt = fields.Many2one(related='method_payment_id_alt.type_subscription_new',
                                          string='Intermediario Alternativo')
    status_payment_alt = fields.Selection(string='Estado de Cobro Alternativo',
                                          selection=[('pending', 'Pendiente Intento de Cobro'),
                                                     ('approved', 'Aprobado'),
                                                     ('send_paid', 'Enviado a Cobro'),
                                                     ('rejected', 'Rechazado')], copy=False)
    detall_status_payment_alt = fields.Char(string="Detalle Estado de Cobro Alternativo", required=False)
    alter_paid = fields.Boolean(string='Pago Alternativo', default=False)

    @api.onchange('method_payment_id')
    def onchange_method_payment_id(self):
        if self.method_payment_id:
            self.intermediary_id = self.method_payment_id.type_subscription_new.id

    def kushki_process_payment(self):
        HistoryPayment = self.env['move.payment.history']
        KushkiLog = self.env['kushki.log']
        AccountPayment = self.env['account.payment']
        conf = self.env['ir.config_parameter'].sudo()
        domain = [('key', '=', 'web.base.url')]
        conf_search = conf.search(domain)
        value = conf_search.value
        user = self.env.uid
        for record in self:
            if record.payment_acquirer_id.provider == 'kushki':
                amount_total = record.amount_residual
                amount_untaxed = record.amount_untaxed
                iva = record.amount_tax
                amount_tax_signed = record.amount_tax_signed
                producto = quantity = 0
                price = 0.0
                title = ''
                for a in record.invoice_line_ids:
                    producto = a.product_id.id
                    title = a.product_id.name
                    price = a.price_unit
                    quantity = a.quantity
                today = datetime.today()
                ################## Request Payment Kushki #########################
                headers = {'Private-Merchant-Id': record.payment_acquirer_id.kushki_secret_key, 'content-type': "application/json"}

                body = {
                    'language': 'es',
                    'amount': {
                        'subtotalIva': amount_untaxed,
                        'subtotalIva0': 0,
                        'ice': 0,
                        'iva': iva,
                        'currency': record.currency_id.name
                    },
                    'fullResponse': True,
                    'contactDetails': {
                        "documentType": "RUT",
                        'documentNumber': record.method_payment_id.document_number,
                        'email': record.method_payment_id.email,
                        'firstName': record.method_payment_id.name,
                        'lastName': record.method_payment_id.last_name,
                        'phoneNumber': record.method_payment_id.phone_number
                    },
                    'orderDetails': {
                        'siteDomain': value,
                        'billingDetails': {
                            'name': record.partner_id.name,
                            'phone': record.partner_id.phone,
                            'address': record.partner_id.street,
                            'city': record.partner_id.city,
                            'region': record.partner_id.state_id.name,
                            'country': record.partner_id.country_id.name,
                        },
                    },
                    'productDetails':{
                        'product':[
                            {
                                'id': producto,
                                'title': title,
                                'price': price,
                                'quantity': quantity,
                            }
                        ]
                    },
                }
                response = requests.post(url_kushki + "/subscriptions/v1/card/" + record.method_payment_id.token_card, data=json.dumps(body), headers=headers)
                response_dict = response.json()
                if response.status_code != 201:
                    kushki_log = KushkiLog.create({
                        'document': record.name,
                        'user_id': user,
                        'method_name': 'Cobro',
                        'answer': response.text,
                        'error_code': response_dict['code'],
                        'description_error': response_dict['message']
                    })
                    record.method_payment_id.status = response_dict['code'] + ' ' + response_dict['message']
                    details = response_dict['details']
                    HistoryPayment.create({
                        'move_id': record.id,
                        'user_id': user,
                        'type': record.method_payment_id.card_type, #details['transaction_details']['cardType'] if 'cardType' in details['transaction_details'] else '',
                        'last_four_digits': details['transaction_details']['lastFourDigitsOfCard'],
                        'date': today.date(),
                        'transaction_id': details['transaction_id'],
                        'transaction_number': response_dict['ticketNumber'] if 'ticketNumber' in response_dict else '',
                        'transaction_reference': response_dict['transactionReference'] if 'transactionReference' in response_dict else '',
                        'amount': amount_total,
                        'state': response_dict['message'],
                        'detail': 'Kushki',
                        'kushki_log_id': kushki_log.id
                    })
                    record.method_payment_id.status_payment = 'Rechazado'
                    record.method_payment_id.status_detail = response_dict['message']
                    #record.write({'status_payment': 'Rechazado'})
                    #record.write({'status_detail': response_dict['message']})
                    return True
                    #raise UserError(response_dict.code, response_dict.message)
                details = response_dict['details']
                ################## Log Kushki #########################
                kushki_log = KushkiLog.create({
                    'partner_id': record.partner_id.id,
                    'document': record.name,
                    'user_id': user,
                    'method_name': 'Cobro',
                    'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
                })
                journal = self.env['account.journal'].search([('id', '=', 7)])
                payment = AccountPayment.create({
                    'payment_type': 'inbound',
                    # 'partner_type': 'customer',
                    'partner_id': record.partner_id.id,
                    'amount': record.amount_residual,
                    'date': today.date(),
                    'ref': response_dict['ticketNumber'],
                    #'journal_id': record.payment_acquirer_id.journal_id.id,
                    'journal_id': journal.id,
                    'payment_method_line_id': journal.inbound_payment_method_line_ids[0].id
                    #'payment_method_line_id': record.payment_acquirer_id.journal_id.inbound_payment_method_line_ids[0].id
                })
                payment.action_post()
                pline = 0
                for line in payment.move_id.line_ids:
                    if line.credit > 0:
                        pline = line.id
                record.js_assign_outstanding_line(pline)
                HistoryPayment.create({
                    'move_id': record.id,
                    'user_id': user,
                    'type': details['binInfo']['type'] if 'type' in details['binInfo'] else '',
                    'last_four_digits': details['lastFourDigits'],
                    'date': today.date(),
                    'transaction_id': details['transactionId'],
                    'transaction_number': response_dict['ticketNumber'],
                    'transaction_reference': response_dict['transactionReference'],
                    'amount': details['requestAmount'],
                    'state': details['transactionStatus'],
                    'state_payment': 'approved' if details['transactionStatus'] == 'APPROVAL' else 'rejected',
                    'detail': 'Kushki',
                    'kushki_log_id': kushki_log.id
                })
                record.method_payment_id.status_payment = 'Aprobado'
                #record.write({'status_payment': 'Aprobado'})
        return True