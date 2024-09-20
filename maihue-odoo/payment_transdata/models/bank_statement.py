# -*- coding: utf-8 -*-
# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import tempfile
import binascii
import logging
import io
import numpy as np
from datetime import date
from datetime import datetime
#from odoo.exceptions import Warning
from odoo import models, fields, api, exceptions, _
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from io import StringIO

_logger = logging.getLogger(__name__)
try:
	import csv
except ImportError:
	_logger.debug('Cannot `import csv`.')
try:
	import xlwt
except ImportError:
	_logger.debug('Cannot `import xlwt`.')
try:
	import cStringIO
except ImportError:
	_logger.debug('Cannot `import cStringIO`.')
try:
	import base64
except ImportError:
	_logger.debug('Cannot `import base64`.')
try:
	import xlrd
except ImportError:
	_logger.debug('Cannot `import xlrd`.')




class account_bank_statement_wizard(models.TransientModel):
	_inherit= 'account.bank.statement.import'

	bank_op = fields.Selection([('transdata', 'Transdata'), ('santander', 'Multibanco Santander')],
								 string='Type')
	file_id = fields.Many2one('payment.transdata.file', string='File', readonly=False, domain="[('type', '=', 'transdata')]")
	file_id_t = fields.Many2one('payment.transdata.file', string='File', readonly=False, domain="[('type', '=', 'santander')]")

	# @api.onchange('file_id')
	# def onchange_file_id(self):
	# 	if self.file_id:
	# 		self.attachment_ids = self.file_id.datas

	def import_file(self):  # Fecha actual
		now = datetime.now()
		res = {}
		years = now.year
		if not self.attachment_ids:
			raise UserError(_("Por favor, Seleccione Archivo"))
		if self.bank_op == 'transdata':
			keys = ['type', 'monto', 'id2', 'dato_que_no_se', 'id4', 'id5', 'id6', 'id7', 'rut', 'id9', 'ref_int',
					'cod_auto', 'codigo_estado', 'estado', 'id14', 'id15', 'date_cobro', 'desc_estado']
			keys_down = ['partner_vat', 'monto', 'id_fact']
			data = base64.b64decode(self.attachment_ids.datas)
			data_down = base64.b64decode(self.file_id.datas)

			file_input = io.StringIO(data.decode("utf-8"))
			#file_down = io.StringIO(data_down.decode("utf-8"))
			file_down = data_down.decode("utf-8")
			file_input.seek(0)
			#file_down.seek(0)
			reader_info = []
			reader_down = []
			list_down = []
			reader = csv.reader(file_input, delimiter=';')
			# reader_down = csv.reader(file_down, delimiter=',')
			splits = file_down.split("\r")
			#reader_down = csv.reader(open(self.file_id.datas, 'rU'), dialect=csv.excel_tab)
			#reader_down = csv.reader(file_down, delimiter=',')
			for row in splits:
				array_s = row.split(",")
				list_down.append(array_s[2])
				print(row)

			try:
				reader_info.extend(reader)
			except Exception:
				raise exceptions.Warning(_("No es un archivo válido!"))
			# try:
			# 	reader_down.extend(reader_down)
			# except Exception:
			# 	raise exceptions.Warning(_("No es un archivo válido download!"))
			values = {}
			name_file = 'U-TransBank-%s.csv' % (str(now.strftime("%d/%m/%y-%H:%M:%S")))
			#file_transdata = self.env['payment.transdata.file'].create({'name': name_file})
			file_transdata = self.env['payment.transdata.file'].browse(self.file_id.id)
			statement_values = {
				'name': name_file,
				'journal_id': 7,
				'date': now,
			}
			statement = self.env['account.bank.statement'].create(statement_values)
			len_list = len(list_down) #+ 1
			len_upload = len(reader_info)
			if len_list == len_upload:
				jamie = sorted(list_down)
				for b in sorted(reader_info):
					if b == []:
						continue
					if b[10] not in list_down:
						raise UserError(_(
							"Disculpe, El archivo seleccionado no coincide en la factura %s , al menos", b[10]))
				#jamie = sorted(reader_info.items(), key=reader_info.itemgetter(12), reverse=True)
				reader_info = sorted(reader_info, key=lambda item: (item[12]))
				for i in range(len(reader_info)):
					field = list(map(str, reader_info[i]))
					values = dict(zip(keys, field))
					if values:
						counterpart_aml_dicts = []
						invoice_id = self.env['account.move'].search([('id_fact', '=', values['ref_int'])], limit=1)
						if not invoice_id:
							raise exceptions.Warning(_("No existe la factura con el Id de Factura: " + values['ref_int']))
						if values['date_cobro']:
							date_cobro = str(values['date_cobro'][4:8]) + '-' + str(values['date_cobro'][2:4]) + '-' + str(values['date_cobro'][0:2])
						else:
							date_cobro = now
						status_method = 'Aprobado'
						if values['codigo_estado'] != 0:
							status_method = 'Rechazado'
							if invoice_id.method_payment_id:
								invoice_id.write({'export_to_transbank': False, 'ajust_total': 0, 'status_payment': 'rejected'})
							if invoice_id.method_payment_id_alt:
								invoice_id.write(
									{'export_to_transbank': False, 'ajust_total': 0, 'status_payment_alt': 'rejected'})
						# if values['codigo_estado'] == 16:
						# 	partner_id.write({'credit_card_status': 'bloqueada'})
						if invoice_id.method_payment_id:
							invoice_id.method_payment_id.write(
								{'status_payment': status_method, 'status_detail': str(values['estado']) + ' ' + str(values['desc_estado'] or '')})
						if invoice_id.method_payment_id_alt:
							invoice_id.method_payment_id_alt.write(
								{'status_payment': status_method, 'status_detail': str(values['estado']) + ' ' + str(values['desc_estado'] or '')})
						file_transdata.write({
							'export_status2': values['codigo_estado'],
							'desc_status': str(values['desc_estado'] or ''),
							'unpload_db_datas': base64.b64encode(self.attachment_ids.datas),
							'unpload_datas': base64.b64encode(self.attachment_ids.datas),
							'state': 'ok',
							'unpload_filename': name_file,
							'import_date': now,
							'unpload_user': self.create_uid.id
							})

						payment_transdata = {
							'move_td_id': invoice_id.id,
							'name': str(values['estado']) + ' ' + str(values['desc_estado'] or ''),
							'rut_partner': values['rut'],
							'cod_aut': values['cod_auto'] or '',
							'ref_int': values['ref_int'],
							'date_payment': date_cobro,
							'import_date': now,
							#'status_type': values['codigo_estado'],
							'method_payment': invoice_id.method_payment_id.name,
						}
						transdata_id = self.env['payment.transdata'].create(payment_transdata)
						payment_log = {
							'move_td_id': invoice_id.method_payment_id.id,
							'name': str(values['estado']) + ' ' + str(values['desc_estado'] or ''),
							'rut_partner': values['rut'],
							'cod_aut': values['cod_auto'] or '',
							'ref_int': values['ref_int'],
							'date_payment': date_cobro,
							'import_date': now,
							# 'status_type': values['codigo_estado'],
							'method_payment': invoice_id.method_payment_id.name,
						}
						log_id = self.env['payment.log'].create(payment_log)
						dia = values['date_cobro'][:2]
						mes = values['date_cobro'][2:4]
						anio = values['date_cobro'][4:]
						fecha_carga = str(anio) + '-' + str(mes) + '-' +str(dia)
						if values['codigo_estado'] == '0':
							statement_line = {
								'date': fecha_carga,
								'payment_ref': str(invoice_id.name),
								'partner_id': invoice_id.partner_id.id,
								'company_id': self.env.company.id,
								'statement_id': statement.id,
								'ref': str(values['estado']) + ' ' + str(values['desc_estado']) + ' Id Fact: ' + str (values['ref_int']),
								# 'amount': line[3] * (-1),
								'amount': values['monto'], # int(values['monto'].replace('.', '')) * (-1) / 10,
							}
							invoice_id.write(
								{'status_payment': 'approved'})
							# transdata = self.env['account.bank.statement'].search([
							# 	('id', '=', self._context.get('active_id'))], limit=1)
							res = self.env['account.bank.statement.line'].create(statement_line)
						valores = []
						data = []
						#valores.append(res.id)
				statement.button_post()
				statement.action_bank_reconcile_bank_statements()
				form_view = self.env.ref(
					'account.view_bank_statement_form')
				action = {
					'view_mode': 'form',
					'view_id': form_view.id,
					'res_model': 'account.bank.statement',
					'type': 'ir.actions.act_window',
					'target': 'current',
					'res_id': statement.id,
				}
				return action
			else:
				raise UserError(_("Disculpe, El archivo seleccionado no coincide con el numero de lineas del archivo que desea cargar"))
		if self.bank_op == 'santander':
			keys = ['values']
			keys_down = ['banco', 'servicio', 'cuenta', 'total', 'boleta']
			data = base64.b64decode(self.attachment_ids.datas)
			data_down = base64.b64decode(self.file_id_t.datas)

			file_input = io.StringIO(data.decode("utf-8"))
			#file_down = io.StringIO(data_down.decode("utf-8"))
			file_down = data_down.decode("utf-8")
			file_input.seek(0)
			#file_down.seek(0)
			reader_info = []
			reader_down = []
			list_down = []
			reader = csv.reader(file_input, delimiter=';')
			# reader_down = csv.reader(file_down, delimiter=',')
			splits = file_down.split("\r")
			#reader_down = csv.reader(open(self.file_id.datas, 'rU'), dialect=csv.excel_tab)
			#reader_down = csv.reader(file_down, delimiter=',')
			for row in splits:
				array_s = row.split(",")
				list_down.append(array_s[4])
				print(row)
			try:
				reader_info.extend(reader)
			except Exception:
				raise exceptions.Warning(_("No es un archivo válido!"))
			values = {}
			name_file = 'U-Santander-%s.csv' % (str(now.strftime("%d/%m/%y-%H:%M:%S")))
			file_santander = self.env['payment.transdata.file'].browse(self.file_id_t.id)
			statement_values = {
				'name': name_file,
				'journal_id': 7,
				'date': now,
			}
			len_list = len(list_down)  # + 1
			len_upload = len(reader_info)
			len_upload = len_upload -1
			if len_list != len_upload:
				raise UserError(_(
					"Disculpe, El archivo seleccionado no coincide con el numero de lineas del archivo que desea cargar"))
			statement = self.env['account.bank.statement'].create(statement_values)
			for i in range(len(reader_info)):
				field = list(map(str, reader_info[i]))
				values = dict(zip(keys, field))
				if values:
					str_valores = values['values']
					factura = str_valores[117:125]
					factura = int(factura)
					if str(factura) not in list_down:
						raise UserError(_(
							"Disculpe, El archivo seleccionado no coincide en la factura %s , al menos",
							factura))
					counterpart_aml_dicts = []
					invoice_id = self.env['account.move'].search([('id_fact', '=', factura)], limit=1)
					if not invoice_id:
						raise exceptions.Warning(_("No existe la factura con el Id de Factura: " + values['ref_int']))
					date_cobro = str_valores[125:133]
					if date_cobro:
						date_cobro = str(date_cobro[4:8]) + '-' + str(date_cobro[2:4]) + '-' + str(date_cobro[0:2])
					else:
						date_cobro = now
					codigo_estado = str_valores[95:97]
					desc_estado = str_valores[97:117]
					invoice_id.method_payment_id.write({'status': codigo_estado, 'status_last': desc_estado})
					monto = str_valores[50:58]
					if int(codigo_estado) != 0:
						invoice_id.write({'export_to_transbank': False, 'ajust_total': 0, 'status_payment': 'rejected'})
					else:
						invoice_id.write(
							{'status_payment': 'approved'})
					# if values['codigo_estado'] == 16: date_expected = fields.Date(string='Date')
					# 	partner_id.write({'credit_card_status': 'bloqueada'})
					invoice_id.method_payment_id.write({'status_last': desc_estado})
					file_santander.write({
						'export_status2': codigo_estado,
						'desc_status': desc_estado or '',
						'unpload_db_datas': base64.b64encode(self.attachment_ids.datas),
						'unpload_datas': base64.b64encode(self.attachment_ids.datas),
						'state': 'ok',
						'unpload_filename': name_file,
						'import_date': now,
						'unpload_user': self.create_uid.id,
						})

					payment_transdata = {
						'move_td_id': invoice_id.id,
						'name': str(codigo_estado) + ' ' + str(desc_estado or ''),
						'rut_partner': invoice_id.partner_id.vat,
						'cod_aut': codigo_estado or '',
						'ref_int': factura,
						'date_payment': date_cobro,
						'import_date': now,
						'amount': int(monto),
						'method_payment': invoice_id.method_payment_id.name,
						#'status_type': values['codigo_estado'],
					}
					transdata_id = self.env['payment.transdata'].create(payment_transdata)
					payment_log = {
						'move_td_id': invoice_id.method_payment_id.id,
						'name': str(values['estado']) + ' ' + str(values['desc_estado'] or ''),
						'rut_partner': values['rut'],
						'cod_aut': values['cod_auto'] or '',
						'ref_int': values['ref_int'],
						'date_payment': date_cobro,
						'import_date': now,
						# 'status_type': values['codigo_estado'],
						'method_payment': invoice_id.method_payment_id.name,
					}
					log_id = self.env['payment.log'].create(payment_log)
					if int(codigo_estado) == 0:
						statement_line = {
							'date': date_cobro,
							'payment_ref': str(invoice_id.name),
							'partner_id': invoice_id.partner_id.id,
							'company_id': self.env.company.id,
							'statement_id': statement.id,
							'ref': str(codigo_estado) + ' ' + str(desc_estado) + ' Id Fact: ' + str (factura),
							# 'amount': line[3] * (-1),
							'amount': monto, # int(values['monto'].replace('.', '')) * (-1) / 10,
						}
						# transdata = self.env['account.bank.statement'].search([
						# 	('id', '=', self._context.get('active_id'))], limit=1)
						res = self.env['account.bank.statement.line'].create(statement_line)
					valores = []
					data = []
					#valores.append(res.id)
			statement.button_post()
			statement.action_bank_reconcile_bank_statements()
			form_view = self.env.ref(
				'account.view_bank_statement_form')
			action = {
				'view_mode': 'form',
				'view_id': form_view.id,
				'res_model': 'account.bank.statement',
				'type': 'ir.actions.act_window',
				'target': 'current',
				'res_id': statement.id,
			}
			return action
		else:
			return super(account_bank_statement_wizard, self).import_file()
