# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import json
import requests

class YourSignature(models.Model):
	_name = 'your.signature.log'
	_description = 'Your Signature Log'

	status = fields.Selection(selection=[("to_sign", "Pend. Firma"), ("signed", "Firmado"), ("cancelled", "Cancelado"), ("cancelled_signed", "Cancelado post firma"), ("to_cancelled_cont", "Cancelar Contingencia"), ("cancelled_cont", "Cancelado Contingencia")])
	type = fields.Selection([
		('digital', 'Digital'),
		('fisica', 'Fisica'),
	], string="Tipo", default="digital")
	name = fields.Char(string="Nombre del contrato")
	extra_id = fields.Many2one('agreement.extra', string="extra")
	file_report = fields.Binary(string="Documento PDF")
	file_report_signed = fields.Binary(string="Documento PDF Firmado")
	file_name = fields.Char(string="Filename", store=True)
	file_name2 = fields.Char(string="Filename", store=True)
	id_contrato = fields.Char(string="Id contrato", readonly=True)
	cancellation_date = fields.Date(string="Fecha de cancelacion")
	signature_Date = fields.Date(string="Fecha de firma")

	# Firmantes
	partner_signed_user_id = fields.Many2one("res.partner", string="Firmante R1")
	fecha_envio1 = fields.Date(string="Fecha Envio R1")
	fecha_repres1 = fields.Date(string="Fecha de Firma R1")
	email_signed_user = fields.Char('Email Firmante R1')

	company_signed_user_dos_id = fields.Many2one("res.partner", string="Firmante R2")
	fecha_envio2 = fields.Date(string="Fecha Envio R2")
	fecha_repres2 = fields.Date(string="Fecha de Firma R2")
	email_signed_user_dos = fields.Char('Email Firmante R2')

	company_signed_user_tres_id = fields.Many2one("res.partner", string="Firmante R3")
	fecha_envio3 = fields.Date(string="Fecha Envio R3")
	fecha_repres3 = fields.Date(string="Fecha de Firma R3")
	email_signed_user_tres = fields.Char('Email Firmante R3')

	# Compañia
	company_signed_user_id = fields.Many2one("res.partner", string="Firmante Maihue")
	company_signed_date = fields.Date(string="Firmado en")
	email_signed_maihue = fields.Char('Email Firmante Maihue')

	signed_client = fields.Boolean(string='Firmado cliente')
	signed_maihue = fields.Boolean(string='Firmado Maihue')
	firma_type = fields.Many2one('signature.type', string="Tipo de Firma")

	@api.model
	def cron_cancel_cont_contract(self):
		for record in self.search([('status', '=', 'to_cancelled_cont')]):
			config = record.env['ir.config_parameter'].sudo()
			dict_conf = record.extra_id.return_values_your_signature()
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
				record.write({'id_contrato': False, 'status': 'cancelled_cont', 'cancellation_date': datetime.today()})
