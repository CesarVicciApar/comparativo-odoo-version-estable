# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request
from datetime import datetime
from werkzeug.exceptions import BadRequest

_logger = logging.getLogger(__name__)


class YourSignature(http.Controller):

    @http.route(['/api/hook'], type='json', methods=['GET', 'POST'], auth="public")
    def your_signature_hook(self, **post):
        data = json.loads(request.httprequest.data.decode('utf-8'))
        AgreementExtra = request.env['agreement.extra'].sudo()
        _logger.info('Hook: %s' % data)
        document_id = data['_id']
        agreement_extra_id = AgreementExtra.search([('id_contrato', '=', document_id)])
        agreement_extra_id.obtain_document()
        if agreement_extra_id.send_document_automatic:
            agreement_extra_id.send_signed_document_to_partner()
        return data


    @http.route(['/api/fieldsHook'], type='json', methods=['GET', 'POST'], auth="public")
    def your_signature_fieldsHook(self, **post):
        data = json.loads(request.httprequest.data.decode('utf-8'))
        AgreementExtra = request.env['agreement.extra'].sudo()
        YourSignatureLog = request.env['your.signature.log'].sudo()
        _logger.info('Data fieldsHook: %s' % data)
        signer = data['firmador']
        document_id = data['documentId']
        agreement_extra_id = AgreementExtra.search([('id_contrato', '=', document_id)])
        if agreement_extra_id:
            if agreement_extra_id.company_signed_user_id and agreement_extra_id.email_signed_maihue == signer:
                agreement_extra_id.write({'state_firm4': 'M', 'company_signed_date': datetime.today()})
            elif agreement_extra_id.partner_signed_user_id and agreement_extra_id.email_signed_user == signer:
                agreement_extra_id.write({'state_firm1': 'M', 'fecha_repres1': datetime.today()})
            elif agreement_extra_id.company_signed_user_dos_id and agreement_extra_id.email_signed_user_dos == signer:
                agreement_extra_id.write({'state_firm2': 'M', 'fecha_repres2': datetime.today()})
            elif agreement_extra_id.company_signed_user_tres_id and agreement_extra_id.email_signed_user_tres == signer:
                agreement_extra_id.write({'state_firm3': 'M', 'fecha_repres3': datetime.today()})
        log_your_signature_id = YourSignatureLog.search([('id_contrato', '=', document_id)])
        if log_your_signature_id:
            if log_your_signature_id.company_signed_user_id and log_your_signature_id.email_signed_maihue == signer:
                log_your_signature_id.write({'state_firm4': 'M', 'company_signed_date': datetime.today()})
            elif log_your_signature_id.partner_signed_user_id and log_your_signature_id.email_signed_user == signer:
                log_your_signature_id.write({'state_firm1': 'M', 'fecha_repres1': datetime.today()})
            elif log_your_signature_id.company_signed_user_dos_id and log_your_signature_id.email_signed_user_dos == signer:
                log_your_signature_id.write({'state_firm2': 'M', 'fecha_repres2': datetime.today()})
            elif log_your_signature_id.company_signed_user_tres_id and log_your_signature_id.email_signed_user_tres == signer:
                log_your_signature_id.write({'state_firm3': 'M', 'fecha_repres3': datetime.today()})

        ##### ACTIVAR FIRMADO COMPLETO CLIENTE EN DOCUMENTO #####
        if agreement_extra_id.partner_signed_user_id and agreement_extra_id.company_signed_user_dos_id and  agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm1 == 'M' and agreement_extra_id.state_firm2 == 'M' and agreement_extra_id.state_firm3 == 'M':
                agreement_extra_id.signed_client = True
        elif agreement_extra_id.partner_signed_user_id and not agreement_extra_id.company_signed_user_dos_id and not agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm1 == 'M':
                agreement_extra_id.signed_client = True
        elif not agreement_extra_id.partner_signed_user_id and agreement_extra_id.company_signed_user_dos_id and not agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm2 == 'M':
                agreement_extra_id.signed_client = True
        elif not agreement_extra_id.partner_signed_user_id and not agreement_extra_id.company_signed_user_dos_id and agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm3 == 'M':
                agreement_extra_id.signed_client = True
        elif agreement_extra_id.partner_signed_user_id and agreement_extra_id.company_signed_user_dos_id and not agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm1 == 'M' and agreement_extra_id.state_firm2 == 'M':
                agreement_extra_id.signed_client = True
        elif agreement_extra_id.partner_signed_user_id and not agreement_extra_id.company_signed_user_dos_id and agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm1 == 'M' and agreement_extra_id.state_firm3 == 'M':
                agreement_extra_id.signed_client = True
        elif not agreement_extra_id.partner_signed_user_id and agreement_extra_id.company_signed_user_dos_id and agreement_extra_id.company_signed_user_tres_id:
            if agreement_extra_id.state_firm2 == 'M' and agreement_extra_id.state_firm3 == 'M':
                agreement_extra_id.signed_client = True
        ##### ACTIVAR FIRMADO MAIHUE #######
        if agreement_extra_id.state_firm4 == 'M':
            agreement_extra_id.signed_maihue = True

        #### STATUS FIRMADO COMPLETO GENERAL DOCUMENTO ######
        if agreement_extra_id.signed_maihue and agreement_extra_id.signed_client:
            agreement_extra_id.status = 'signed'
        return data


