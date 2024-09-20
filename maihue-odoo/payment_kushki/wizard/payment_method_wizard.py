# -*- encoding: utf-8 -*-
from odoo import api, fields, models
import requests
import json
from odoo.exceptions import ValidationError
from datetime import date, datetime

url_kushki = "http://api-uat.kushkipagos.com"

class AccountMoveWizard(models.Model):
    _name = 'payment.method.wizard'

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMoveWizard, self).default_get(default_fields)
        active_id = self._context.get('active_id')
        rec = self.env['account.move'].browse(int(active_id))
        res.update({
            'partner_id': rec.partner_id.id,
            'amount': rec.amount_residual,
            'payment_method_id': rec.method_payment_id.id,
            'payment_acquirer_id': rec.payment_acquirer_id.id,
        })
        return res

    partner_id = fields.Many2one('res.partner', string='Cliente',)
    payment_acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer')
    intermediary_id = fields.Many2one('agreement.payment.intermediary', 'Intermediario')
    payment_method_id = fields.Many2one('payment.method.partner', 'Tarjeta')
    domain_payment_method_ids = fields.Many2many('payment.method.partner', string='Domain Tarjeta')
    amount = fields.Float('Monto')
    domain_acquirer_id = fields.Many2many('payment.acquirer', string='Domain acquirer')

    @api.onchange('payment_method_id', 'payment_acquirer_id')
    def onchange_payment_method_id(self):
        acquirer = self.env['payment.acquirer'].search([('state', 'not in', ['disabled'])])
        payment_methods = self.env['payment.method.partner'].search([('state', 'in', ['active']),('partner_id', '=', self.partner_id.id)])
        intermediary_id = False
        if acquirer:
            payment_methods = payment_methods.filtered(lambda s: s.acquirer_id.id in acquirer.ids)
        if self.payment_method_id and self.payment_acquirer_id:
            intermediary_id = self.payment_method_id.type_subscription_new.id
            acquirer = acquirer.filtered(lambda s: s.id == self.payment_acquirer_id.id)
        elif not self.payment_method_id and self.payment_acquirer_id:
            #acquirer = acquirer.filtered(lambda s: s.id == self.payment_acquirer_id.id)
            payment_methods = payment_methods.filtered(lambda s: s.acquirer_id.id == self.payment_acquirer_id.id)
        elif self.payment_method_id and not self.payment_acquirer_id:
            acquirer = acquirer.filtered(lambda s: s.id == self.payment_method_id.acquirer_id.id)
            payment_methods = payment_methods.filtered(lambda s: s.acquirer_id.id == self.payment_acquirer_id.id)
            intermediary_id = self.payment_method_id.type_subscription_new.id
            self.payment_acquirer_id = acquirer.id
        self.intermediary_id = intermediary_id
        self.domain_acquirer_id = acquirer.ids
        self.domain_payment_method_ids = payment_methods.ids if payment_methods else False

    @api.onchange('amount')
    def validate_residual_amount(self):
        for val in self:
            active_id = val._context.get('active_id')
            rec = val.env['account.move'].browse(int(active_id))
            if val.amount == 0:
                raise ValidationError("El monto ingresado no puede ser 0")
            if val.amount > rec.amount_residual:
                raise ValidationError(
                "El monto ingresado |{}| no puede ser mayor al importe adeudado |{}| ".format(
                    val.amount, rec.amount_residual))


    def kushki_process_payment(self):
        for kushki in self:
            active_id = kushki._context.get('active_id')
            historyPayment = kushki.env['move.payment.history']
            kushkiLog = kushki.env['kushki.log']
            accountPayment = kushki.env['account.payment']
            record = kushki.env['account.move'].browse(int(active_id))
            conf = self.env['ir.config_parameter'].sudo()
            domain = [('key', '=', 'web.base.url')]
            conf_search = conf.search(domain)
            value = conf_search.value
            user = kushki.env.uid
            amount_tax_signed = record.amount_tax_signed
            amount_untaxed = kushki.amount
            iva = 0
            for a in record.invoice_line_ids:
                produto = a.product_id.id
                title = a.product_id.name
                price = a.price_unit
                quantity = a.quantity
            today = datetime.today()
            headers = {'Private-Merchant-Id': str(record.payment_acquirer_id.kushki_secret_key), 'content-type': "application/json"}

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
                    'documentNumber': self.payment_method_id.document_number,
                    'email': self.payment_method_id.email,
                    'firstName': self.payment_method_id.name,
                    'lastName': self.payment_method_id.last_name,
                    'phoneNumber': self.payment_method_id.phone_number
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
                            'id': produto,
                            'title': title,
                            'price': price,
                            'quantity': quantity,
                        },
                    ]
                },
            }
            print(body, 'BODY WIZARD')
            response = requests.post(url_kushki + "/subscriptions/v1/card/" + str(self.payment_method_id.token_card), data=json.dumps(body), headers=headers)
            response_dict = response.json()
            if response.status_code != 201:
                k_log = kushkiLog.create({
                    'partner_id': self.partner_id.id,
                    'document': record.name,
                    'user_id': user,
                    'method_name': 'Cobro',
                    'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>'),
                    'error_code': response_dict['code'],
                    'description_error': response_dict['message']
                })
                details = response_dict['details']
                historyPayment.create({
                    'move_id': record.id,
                    'user_id': user,
                    'type': record.method_payment_id.card_type,
                    # details['transaction_details']['cardType'] if 'cardType' in details['transaction_details'] else '',
                    'last_four_digits': details['transaction_details']['lastFourDigitsOfCard'],
                    'date': today.date(),
                    'transaction_id': details['transaction_id'],
                    'transaction_number': response_dict['ticketNumber'] if 'ticketNumber' in response_dict else '',
                    'transaction_reference': response_dict[
                        'transactionReference'] if 'transactionReference' in response_dict else '',
                    'amount': self.amount,
                    'state': response_dict['message'],
                    'state_payment': 'approved' if details['transactionStatus'] == 'APPROVAL' else 'rejected',
                    'detail': 'Kushki',
                    'kushki_log_id': k_log.id
                })
                kushki.payment_method_id.status_payment = 'Aprobado'
                kushki.payment_method_id.status_detail = response_dict['message']
                return True
            details = response_dict['details']
            k_log = kushkiLog.create({
                'partner_id': self.partner_id.id,
                'document': record.name,
                'user_id': user,
                'method_name': 'Cobro',
                'answer': json.dumps(response_dict, indent=4).replace('\n', '<br/>')
            })
            journal = self.env['account.journal'].search([('id', '=', 7)])
            payment = accountPayment.create({
                'payment_type': 'inbound',
                #'partner_type': 'customer',
                'partner_id': record.partner_id.id,
                'amount': kushki.amount,
                'date': today.date(),
                'ref': response_dict['ticketNumber'],
                'journal_id': journal.id,
                #'journal_id': record.payment_acquirer_id.journal_id.id,
                'payment_method_line_id': journal.inbound_payment_method_line_ids[0].id
                #'payment_method_id': record.payment_acquirer_id.journal_id.inbound_payment_method_line_ids[0].id
            })
            payment.action_post()
            pline = 0
            for line in payment.move_id.line_ids:
                if line.credit > 0:
                    pline = line.id
            record.js_assign_outstanding_line(pline)
            historyPayment.create({
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
                'state_payment': 'Aprobado' if details['transactionStatus'] == 'APPROVAL' else 'Rechazado',
                'detail': 'Kushki',
                'kushki_log_id': k_log.id
            })
            kushki.payment_method_id.status_payment = 'Aprobado'

    def action_button(self):
        invoice_id = self._context.get('active_id', False)
        if invoice_id:
            invoice = self.env['account.move'].sudo().browse(invoice_id)
            if self.payment_acquirer_id.provider == 'kushki':
                self.kushki_process_payment()
            else:
                if int(invoice.amount_residual) != int(self.amount):
                    invoice.write({'ajust_total': self.amount})
                if invoice.method_payment_id.id != self.payment_method_id.id:
                    if invoice.status_payment == 'send_paid':
                        raise ValidationError("Disculpe esta factura tiene un intento de cobro activo por no es posible realizar otro intento de cobro en paralelo")
                    invoice.write({'alter_paid': True,
                                   'method_payment_id_alt': self.payment_method_id.id,
                                   'status_payment_alt': 'pending'})
        # self.validate_residual_amount()
        # self.kushki_process_payment()

