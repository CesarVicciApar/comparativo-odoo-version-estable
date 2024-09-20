# -*- coding: utf-8 -*-
# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
import csv
import base64
import io
from odoo.tools import float_is_zero, pycompat
from datetime import date
class AcoountMove(models.Model):
    _inherit = 'account.move'

    payment_td_ids = fields.One2many('payment.transdata', 'move_td_id', string='Pagos transdata',
                                 states={'posted': [('readonly', True)]}, copy=True,
                                 auto_join=True)
    id_fact = fields.Char(string="ID Factura", required=False, states={'posted': [('readonly', True)]})
    filename_e = fields.Char(
        string="Nombre Archivo",
        required=False)
    file_transdata = fields.Many2one('payment.transdata.file', string='Archivo', ondelete='cascade')
    # internal_reference = fields.Char(string="Internal Reference")
    export_to_transbank = fields.Boolean(string='Exportación Masiva',
        help='Set True if this document type and can be imported on transbank'
    )
    code = fields.Char(
        string="Codigo Archivo",
        required=False)
    export_date = fields.Date(string='Fecha Export', readonly=True,
                              help="Fecha de la ultima exportacion de transbank.")
    export_status = fields.Selection([
        ('0', 'APROBADA'),
        ('11', 'INST. INCOMPLETA'),
        ('16', 'RECHAZO')], "Estado Importacion")
    desc_status = fields.Char(string="Descripcion estado")
    file_code = fields.Char(related="file_transdata.code", string="Codigo Archivo")
    file_export_date = fields.Date(related="file_transdata.export_date", string='Fecha Export')
    file_export_status = fields.Selection(related="file_transdata.state", string="Estado Importacion")
    file_desc_status = fields.Char(related="file_transdata.desc_status", string="Descripcion estado")
    type = fields.Selection(related="file_transdata.type", string="Tipo")

    # def create(self, vals):
    #     res = super(AcoountMove, self).create(vals)
    #     res.write({'id_fact': res.id})
    #     return res

    def write(self, vals):
        if 'status_payment' in vals:
            if vals.get('status_payment') in ['pending', 'rejected'] and not 'tarj_dis' in vals or vals.get('status_payment_alt') in ['pending', 'rejected']and not 'tarj_dis' in vals:
                contract = self.invoice_line_ids.sale_line_ids[0].order_id.agreement_id.id
                cont = 0
                for rentals in self.invoice_line_ids.sale_line_ids:
                    if contract == rentals.order_id.agreement_id.id and cont == 0:
                        if rentals.order_id.agreement_id.card_number.id != self.method_payment_id.id:
                            cont = cont + 1
                            vals['method_payment_id'] = rentals.order_id.agreement_id.card_number.id
                            vals['status_payment'] = 'pending'
        return super(AcoountMove, self).write(vals)


    def action_transbank_invoice(self):
        if any(move.move_type not in ('out_invoice') for move in self):
            raise ValidationError(_("Esta acción no está disponible para este documento."))
        for move in self:
            if move.intermediary_id:
                if move.intermediary_id.id not in [1]:
                    raise ValidationError(_(
                        "Esta acción no está disponible para este documento. Solo se puede elegir esta opcion para los intermediarios bancatios PAT Transdata"))
            if move.intermediary_id_alt:
                if move.intermediary_id_alt.id not in [1]:
                    raise ValidationError(_(
                        "Esta acción no está disponible para este documento. Solo se puede elegir esta opcion para los intermediarios bancatios PAT Transdata"))
        if any(move.status_payment in ('send_paid') for move in self):
            raise ValidationError(_("Esta acción no está disponible para este documento. Existen facturas que ya fueron enviadas a cobro"))
        rows_to_write = []
        now = datetime.now()
        filename = 'G-TransBank-%s.csv' % (str(now.strftime("%d/%m/%y-%H:%M:%S")))
        for move in self:
            if move.partner_id.credit_card_status != 'bloqueada':
                if move.export_to_transbank == False:
                    amount = 0
                    if move.ajust_total != 0:
                        amount = move.ajust_total
                    else:
                        amount = move.amount_residual
                    row_list = [
                        move.partner_id.vat,
                        int(amount),
                        move.id_fact
                    ]
                    move.write({'export_to_transbank': True, 'filename_e': filename, 'export_date': now, 'status_payment': 'send_paid'})
                    rows_to_write.append(row_list)
        if len(rows_to_write) > 0:
            fecvalue = self.transbank_csv_write_rows(rows_to_write)
            attachment = self.env['ir.attachment'].create({
                'res_model': 'account.payment.order',
                'name': filename,
                'datas': base64.b64encode(fecvalue),
                'db_datas': filename,
            })
            simplified_form_view = self.env.ref(
                'payment_transdata.view_attachment_transdata_form')
            action = {
                'name': _('Payment File'),
                'view_mode': 'form',
                'view_id': simplified_form_view.id,
                'res_model': 'ir.attachment',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': attachment.id,
            }
            file_values = {
                'name': filename,
                'type': 'transbank',
                'export_to_transbank': True,
                'export_date': now,
                'db_datas': base64.b64encode(fecvalue),
                'datas': base64.b64encode(fecvalue),
                'state': 'pen',
                'down_user': self.create_uid.id,
            }
            file_transdata = self.env['payment.transdata.file'].create(file_values)
            for move in self:
                move.write({'file_transdata': file_transdata.id})
            return action

    def action_santander_invoice(self):
        if any(move.move_type not in ('out_invoice') for move in self):
            raise ValidationError(_("Esta acción no está disponible para este documento."))
        for move in self:
            if move.intermediary_id:
                if move.intermediary_id_.id not in [2]:
                    raise ValidationError(_("Esta acción no está disponible para este documento. Solo se puede elegir esta opcion para los intermediarios bancatios PAC Multibanco Santander"))
            if move.intermediary_id_alt:
                if move.intermediary_id_alt.id not in [2]:
                    raise ValidationError(_(
                        "Esta acción no está disponible para este documento. Solo se puede elegir esta opcion para los intermediarios bancatios PAC Multibanco Santander"))
        if any(move.status_payment in ('send_paid') for move in self):
            raise ValidationError(_("Esta acción no está disponible para este documento. Existen facturas que ya fueron enviadas a cobro"))
        rows_to_write = []
        now = datetime.now()
        filename = 'G-Santander-%s.csv' % (str(now.strftime("%d/%m/%y-%H:%M:%S")))
        for move in self:
            if move.partner_id.credit_card_status != 'bloqueada':
                if move.export_to_transbank == False:
                    if move.method_payment_id:
                        amount = 0
                        if move.ajust_total != 0:
                            amount = move.ajust_total
                        else:
                            amount = move.amount_residual
                        row_list = [
                            move.method_payment_id.bank_id.code,
                            move.method_payment_id.token_card,
                            move.method_payment_id.card_number,
                            int(amount),
                            move.id_fact
                        ]
                        move.write({'export_to_transbank': True, 'filename_e': filename, 'export_date': now, 'status_payment': 'send_paid'})
                        rows_to_write.append(row_list)
                    else:
                        raise ValidationError(_("La Factura %s, no tiene método de pago asociado para esta acción", move.name))
        if len(rows_to_write) > 0:
            fecvalue = self.transbank_csv_write_rows(rows_to_write)
            attachment = self.env['ir.attachment'].create({
                'res_model': 'account.payment.order',
                'name': filename,
                'datas': base64.b64encode(fecvalue),
                'db_datas': filename,
            })
            simplified_form_view = self.env.ref(
                'payment_transdata.view_attachment_transdata_form')
            action = {
                'name': _('Payment File'),
                'view_mode': 'form',
                'view_id': simplified_form_view.id,
                'res_model': 'ir.attachment',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': attachment.id,
            }
            file_values = {
                'name': filename,
                'type': 'santander',
                'export_to_transbank': True,
                'export_date': now,
                'db_datas': base64.b64encode(fecvalue),
                'datas': base64.b64encode(fecvalue),
                'state': 'pen',
                'down_user': self.create_uid.id,
            }
            file_transdata = self.env['payment.transdata.file'].create(file_values)
            for move in self:
                move.write({'file_transdata': file_transdata.id})
            return action

    def transbank_csv_write_rows(self, rows, lineterminator=u'\r'):
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
                #jamie = row[:-1]
                #row[-1] += lineterminator
                writer.writerow(row)
                writer.writerow(lineterminator)
            else:
                writer.writerow(row)

        fecvalue = fecfile.getvalue()
        fecfile.close()
        return fecvalue

from datetime import datetime

class PaymentTransdata(models.Model):
    _name = "payment.transdata"
    _description = "Pagos transdata"

    move_td_id = fields.Many2one('account.move', string='Factura', required=False, ondelete='cascade', index=True,
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
    _name = "payment.transdata.file"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Pagos transdata Archivos"

    # move_id = fields.Many2one('account.move', string='Factura', required=True, ondelete='cascade', index=True,
    #                            copy=False)
    name = fields.Char(
        string="Nombre Archivo",
        required=True)
    code = fields.Char(
        string="Codigo Archivo",
        required=False)
    export_date = fields.Date(string='Fecha Export', readonly=True,
                              help="Fecha de la ultima exportacion.")
    import_date = fields.Date(string='Fecha Import', readonly=True,
                              help="Fecha de la ultima importacion.")
    export_status = fields.Selection([
        ('0', 'APROBADA'),
        ('11', 'INST. INCOMPLETA'),
        ('01', 'SALDO INSUFICIENTE'),
        ('16', 'RECHAZO')], "Estado Importacion")
    export_status2 = fields.Char(string="Estado Importacion")
    desc_status = fields.Char(string="Descripcion estado")
    export_to_transbank = fields.Boolean(string='Exportado Transbank',
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
    down_user = fields.Many2one('res.users', string='Download user', required=False)
    filename = fields.Char(string='Filename', size=256, readonly=False)
    db_datas = fields.Binary('Database Data', attachment=False)
    unpload_datas = fields.Binary(string='File Content (base64)')
    unpload_user = fields.Many2one('res.users', string='Unpload user', required=False)
    unpload_filename = fields.Char(string='Filename', size=256, readonly=False)
    unpload_db_datas = fields.Binary('Database Data', attachment=False)

