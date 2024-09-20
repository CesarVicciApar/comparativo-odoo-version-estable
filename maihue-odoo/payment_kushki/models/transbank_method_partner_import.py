# -*- coding: utf-8 -*-
# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

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

import logging
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

class TransbankMethodPartnerImport(models.TransientModel):
    _name = 'transbank.method.partner.import'
    _description = 'Import transbank method'

    file_id = fields.Many2one('payment.method.file', string='File', readonly=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Files', required=True, help='Get you bank statements in electronic format from your bank and select them here.')

    def import_file(self):
        """ Process the file chosen in the wizard, create bank statement(s) and go to reconciliation. """
        self.ensure_one()
        method_ids_all = []
        PaymentMethodPartner = self.env['payment.method.partner']
        statement_line_ids_all = []
        notifications_all = []
        now = datetime.now()
        res = {}
        years = now.year
        if not self.attachment_ids:
            raise UserError(_("Por favor, Seleccione Archivo"))
        for data_file in self.attachment_ids:
            keys = ['type_mov', 'cod_servi', 'suscrip', 'id3', 'rut_partner', 'num_tarjeta', 'date_ven', 'man_fisico', 'id8', 'id9',
                    'date_aprob', 'id_transaccion', 'id12', 'id13', 'id14', 'id15', 'id16', 'cod_estado', 'estado', 'desc_estado']
            data = base64.b64decode(data_file.datas)
            data_down = base64.b64decode(self.file_id.datas)
            file_input = io.StringIO(data.decode("utf-8"))
            file_down = data_down.decode("utf-8")
            # file_down = io.StringIO(data_down.decode("utf-8"))
            file_input.seek(0)
            # file_down.seek(0)
            reader_info = []
            reader_down = []
            list_down = []
            reader = csv.reader(file_input, delimiter=';')
            splits = file_down.split("\r")
            for row in splits:
                array_s = row.split(",")
                list_down.append(array_s[0])
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
            file_method = self.env['payment.transdata.file'].browse(self.file_id.id)
            for i in range(len(reader_info)):
                if i == 0:
                    continue
                field = list(map(str, reader_info[i]))
                values = dict(zip(keys, field))
                if values:
                    counterpart_aml_dicts = []
                    method_id = self.env['payment.method.partner'].search([('token_card', '=', values['suscrip'])], limit=1)
                    if not method_id:
                        raise exceptions.Warning(
                            _("No existe la suscripcion con el Id: " + values['suscrip']))
                    if values['date_aprob']:
                        date_cobro = str(values['date_aprob'][0:4]) + '-' + str(
                            values['date_aprob'][4:6]) + '-' + str(values['date_aprob'][6:8])
                    else:
                        date_cobro = now
                    # if values['codigo_estado'] != 0:
                    #     method_id.write({'export_to_transbank': False})
                    # if values['codigo_estado'] == 16:
                    # 	partner_id.write({'credit_card_status': 'bloqueada'})
                    # file_transdata.write({
                    #     'export_status': values['codigo_estado'],
                    #     'desc_status': str(values['desc_estado'] or ''),
                    #     'unpload_db_datas': base64.b64encode(self.attachment_ids.datas),
                    #     'unpload_datas': base64.b64encode(self.attachment_ids.datas),
                    #     'state': 'ok',
                    #     'unpload_filename': name_file
                    # })
                    method_transdata = {
                        'method_id': method_id.id,
                        'name': str(values['estado']) + ' ' + str(values['desc_estado'] or ''),
                        'rut_partner': values['rut_partner'],
                        'man_fisico': values['man_fisico'] or '',
                        'type_mov': values['type_mov'],
                        'date_aprob': date_cobro,
                        'cod_servi': values['cod_servi'],
                        'cod_estado': values['cod_estado'],
                        'id_transaccion': values['id_transaccion'],
                    }
                    transdata_id = self.env['method.transdata'].create(method_transdata)
                    method_ids_all.append(method_id.id)
                    method_id.write({'status_payment': values['estado'], 'status_detail': values['desc_estado'] or ''})
            # Prepare import feedback
            notifications = []
            file_method.write({
                'export_status2': values['codigo_estado'],
                'desc_status': str(values['desc_estado'] or ''),
                'unpload_db_datas': base64.b64encode(self.attachment_ids.data),
                'unpload_datas': base64.b64encode(self.attachment_ids.data),
                'state': 'ok',
                'unpload_filename': name_file,
                'import_date': now,
                'import_user': self.create_uid.id
            })
            num_ignored = len(method_ids_all)
            if num_ignored > 0:
                notifications += [{
                    'type': 'warning',
                    'message': _("%d transactions had already been imported and were ignored.", num_ignored)
                    if num_ignored > 1
                    else _("1 transaction had already been imported and was ignored."),
                    'details': {
                        'name': _('Already imported items'),
                        'model': 'payment.method.partner',
                        'ids': PaymentMethodPartner.search(
                            [('name', 'in', method_ids_all)]).ids
                    }
                }]
                # Post the warnings on the payment method import
                msg = ""
                for notif in notifications:
                    msg += (
                        f"{notif['message']}<br/><br/>"
                        f"{notif['details']['name']}<br/>"
                        f"{notif['details']['model']}<br/>"
                        f"{notif['details']['ids']}<br/><br/>"
                    )
                    if msg:
                        method_id.message_post(body=msg)
            # return {
            #     'type': 'ir.actions.client',
            #     #'tag': 'view_payment_method_partner_tree',
            #     'context': {#'statement_line_ids': statement_line_ids_all,
            #                 #'company_ids': self.env.user.company_ids.ids,
            #                 'notifications': notifications,
            #                 },
            # }
            form_view = self.env.ref(
                'payment_kushki.view_payment_method_partner_tree')
            action = {
                'name': _('Upload'),
                'view_mode': 'tree',
                'view_id': form_view.id,
                'res_model': 'payment.method.partner',
                'type': 'ir.actions.act_window',
                'target': 'current',
                #'res_id': statement.id,
            }
            return action
