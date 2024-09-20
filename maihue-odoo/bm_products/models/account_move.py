from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import warnings
from datetime import timedelta, date, datetime, tzinfo
from bs4 import BeautifulSoup
import base64
import xml.etree.ElementTree as ET
import xmltodict
import logging

_logger = logging.getLogger(__name__)


XML_NAMESPACES = {
    'ns0': 'http://www.sii.cl/SiiDte',
    'ns1': 'http://www.w3.org/2000/09/xmldsig#',
    'xml_schema': 'http://www.sii.cl/XMLSchema'
}



class AccountMove(models.Model):
    _inherit = 'account.move'

    backup_document_number = fields.Char(string='Backup_document_number')
    amount_total_xml = fields.Float(string='amount_total_xml')
    difference_amount_warning = fields.Boolean(string='Difference_amount_warning', compute='_compute_difference_amount_warning')
    l10n_cl_claim = fields.Selection(selection_add=[('NCA', 'Recepción de NC de anulación que referencia al documento'),
                                                    ('ENC', 'Recepción de NC, distinta de anulación, que referencia al documento')])

    def write(self, values):
        res = super(AccountMove, self).write(values)
        if 'l10n_latam_document_number' in values and self.move_type in ['in_invoice', 'in_refund'] and self.l10n_cl_dte_acceptation_status:
            if self.l10n_latam_document_number != self.backup_document_number:
                raise ValidationError('Este numero de documento no corresponde a esta factura')
        return res

    @api.depends('amount_total')
    def _compute_difference_amount_warning(self):
        for move in self:
            difference_amount_warning = False
            if move.move_type in ['in_invoice', 'in_refund'] and move.l10n_cl_dte_acceptation_status and move.l10n_cl_dte_file:
                if move.amount_total_xml != move.amount_total:
                    difference_amount_warning = True
            move.difference_amount_warning = difference_amount_warning

    @api.onchange('l10n_latam_document_number')
    def onchange_l10n_latam_document_number(self):
        if self.l10n_latam_document_number and self.backup_document_number and self.move_type in ['in_invoice', 'in_refund'] and self.l10n_cl_dte_acceptation_status:
            if self.l10n_latam_document_number != self.backup_document_number:
                raise ValidationError('Este numero de documento no corresponde a esta factura')

    @api.onchange('partner_id')
    def onchange_backup_document_number(self):
        if self.partner_id and self.move_type in ['in_invoice', 'in_refund'] and self.l10n_cl_dte_file:
            data = base64.b64decode(self.l10n_cl_dte_file.datas)
            soup = BeautifulSoup(data, "lxml")
            document_type = soup.find('tipodte').text
            emisor = soup.find('emisor')
            if self.partner_id.vat == emisor.find('rutemisor').text:
                self.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', document_type)]).id
                self.l10n_latam_document_number = self.backup_document_number
            else:
                raise UserError('Este proveedor no corresponde a esta factura')

    def generate_pdf_from_xml_file(self):
        # dte_xml = self.env['ir.attachment'].search('name', '=', '')
        report_data = self.open_xml_file()
        report = self.env.ref('bm_products.action_report_invoice_from_xml')
        pdf, format = report._render_qweb_pdf(res_ids=self.ids, data=report_data)
        b64_pdf = base64.b64encode(pdf)
        date = datetime.now(tz=None).date()
        time = datetime.now(tz=None).time()
        dicom_date = datetime.combine(date, time)
        ATTACHMENT_NAME = 'DTE ' + report_data['emisor']['RznSoc']
        attach_report = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': ATTACHMENT_NAME + '.pdf',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        attach_report.generate_access_token()
        message = _("Factura PDF %s creada apartir del XML") % (self.name)
        self.message_post(body=message, attachment_ids=[attach_report.id])
        return self

    def open_xml_file(self):
        # if self.message_attachment_count > 0:
            #attachment = self.message_ids.attachment_ids.filtered(lambda att: att.name.endswith('.xml'))
        attachment = self.l10n_cl_dte_file
        if attachment:
            att_content = base64.b64decode(attachment.datas).decode('utf-8')
            #xml_content = ET.fromstring(att_content)
            xml_content = xmltodict.parse(att_content)
            list_detalle = []
            list_impto_reten = []
            documento = xml_content['DTE']['Documento']['Encabezado']['IdDoc']
            emisor = xml_content['DTE']['Documento']['Encabezado']['Emisor']
            receptor = xml_content['DTE']['Documento']['Encabezado']['Receptor']
            totales = xml_content['DTE']['Documento']['Encabezado']['Totales']
            detalle = xml_content['DTE']['Documento']['Detalle']
            referencia = xml_content['DTE']['Documento']['Referencia'] if 'Referencia' in xml_content['DTE']['Documento'] else False
            if isinstance(detalle, dict):
                list_detalle.append(detalle)
            else:
                list_detalle = detalle
            impto_reten = totales['ImptoReten'] if 'ImptoReten' in totales else False
            if impto_reten and isinstance(impto_reten, dict):
                list_detalle.append({
                    'NmbItem': 'Impuesto especifico codigo %s' % impto_reten['TipoImp'],
                    'MontoItem': impto_reten['MontoImp']
                })
            report_data = {
                'documento': documento,
                'emisor': emisor,
                'receptor': receptor,
                'detalle': list_detalle,
                'totales': totales,
                'referencia': referencia,
                # 'rut_emisor': dte_xml.findtext('.//ns0:RUTEmisor', namespaces=XML_NAMESPACES),
                # 'rzn_soc': dte_xml.findtext('.//ns0:RznSoc', namespaces=XML_NAMESPACES),
                # 'giro_emis': dte_xml.findtext('.//ns0:GiroEmis', namespaces=XML_NAMESPACES),
                # 'correo_emisor': dte_xml.findtext('.//ns0:CorreoEmisor', namespaces=XML_NAMESPACES),
                # 'dir_origen': dte_xml.findtext('.//ns0:DirOrigen', namespaces=XML_NAMESPACES),
                # 'cmna_origen': dte_xml.findtext('.//ns0:CmnaOrigen', namespaces=XML_NAMESPACES),
                # 'ciudad_origen': dte_xml.findtext('.//ns0:CiudadOrigen', namespaces=XML_NAMESPACES),
                # 'sucursal': dte_xml.findtext('.//ns0:Sucursal', namespaces=XML_NAMESPACES),
                # 'rut_Recep': dte_xml.findtext('.//ns0:RUTRecep', namespaces=XML_NAMESPACES),
                # 'rzn_soc_recep': dte_xml.findtext('.//ns0:RznSocRecep', namespaces=XML_NAMESPACES),
                # 'giro_recep': dte_xml.findtext('.//ns0:GiroRecep', namespaces=XML_NAMESPACES),
                # 'dir_recep': dte_xml.findtext('.//ns0:DirRecep', namespaces=XML_NAMESPACES),
                # 'cmna_recep': dte_xml.findtext('.//ns0:CmnaRecep', namespaces=XML_NAMESPACES),
                # 'ciudad_recep': dte_xml.findtext('.//ns0:CiudadRecep', namespaces=XML_NAMESPACES),
                # 'cmna_postal': dte_xml.findtext('.//ns0:CmnaPostal', namespaces=XML_NAMESPACES),
                # 'fma_pago': dte_xml.findtext('.//ns0:FmaPago', namespaces=XML_NAMESPACES),
                # 'fch_venc': dte_xml.findtext('.//ns0:FchVenc', namespaces=XML_NAMESPACES),
                # 'detalle': dte_xml.findtext('.//ns0:Detalle', namespaces=XML_NAMESPACES),
            }
            # Procesar el contenido del archivo XML como se desee
            return report_data
        else:
            raise UserError(_('No attachment found'))
    
    def create_partner(self):
        self.ensure_one()
        data = base64.b64decode(self.l10n_cl_dte_file.datas)
        soup = BeautifulSoup(data, "lxml")
        emisor = soup.find('emisor')
        folio = soup.find('folio')
        document_type = soup.find('tipodte').text
        partner_id = self.env['res.partner'].search([('vat', '=', emisor.find('rutemisor').text)])
        if not partner_id:
            city_id = self.env['res.city'].search([('name', 'ilike', emisor.find('cmnaorigen').text), ('country_id.code', '=', 'CL')]) if emisor.find('cmnaorigen') else False
            partner_id = self.env['res.partner'].create({
                'vat': emisor.find('rutemisor').text if emisor.find('rutemisor').text else '',
                'name': emisor.find('rznsoc').text if emisor.find('rznsoc').text else '',
                'l10n_cl_activity_description': emisor.find('giroemis').text if emisor.find('giroemis') else '',
                'street': emisor.find('dirorigen').text if emisor.find('dirorigen').text else '',
                'city_id': city_id.id if city_id else None,
                'company_type': 'company',
                'l10n_cl_sii_taxpayer_type': '1',
                'city': emisor.find('ciudadorigen').text if emisor.find('ciudadorigen') else '',
                'country_id': self.env['res.country'].search([('code', '=', 'CL')]).id,
                'l10n_latam_identification_type_id': self.env['l10n_latam.identification.type'].search([('name', '=', 'RUT')]).id
                # 'email': emisor.find('correoemisor').text if emisor.find('ciudadorigen').text else ''
            })
            self.partner_id = partner_id.id
            self.l10n_latam_document_number = folio.text
            self.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', document_type)]).id
        else:
            self.partner_id = partner_id.id
            self.l10n_latam_document_number = folio.text
            self.l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', document_type)]).id

    def button_draft(self):
        for move in self:
            if move.l10n_cl_dte_acceptation_status and  move.l10n_cl_dte_acceptation_status in ['claimed']:
                raise UserError('No puede volver a borrador un documento reclamado')
            elif move.l10n_cl_dte_acceptation_status and  move.l10n_cl_dte_acceptation_status in ['accepted'] and not self.env.user.has_group('bm_products.group_convert_to_draf_supplier_invoice'):
                raise UserError('No tiene autorizacion para volver a borrador una factura aceptada')
        return super(AccountMove, self).button_draft()

    def cron_l10n_cl_verify_claim_status(self):
        records = self.search([('l10n_cl_claim', '=', False), ('l10n_cl_dte_status', 'in', ['accepted', 'objected'])])
        for rec in records:
            rec.l10n_cl_verify_claim_status()

    def action_l10n_cl_verify_claim_status(self):
        for rec in self:
            rec.l10n_cl_verify_claim_status()

    def l10n_cl_verify_claim_status(self):
        if self.company_id.l10n_cl_dte_service_provider == 'SIITEST':
            raise UserError(_('This feature is not available in certification/test mode'))
        response = self._get_dte_claim(
            self.company_id.l10n_cl_dte_service_provider,
            self.company_id.vat,
            self.company_id._get_digital_signature(user_id=self.env.user.id),
            self.l10n_latam_document_type_id.code,
            self.l10n_latam_document_number
        )
        if not response:
            return None

        try:
            if response['codResp'] != 16:
                response_code = response['listaEventosDoc'][0]['codEvento']
            else:
                response_code = response['codResp']
        except Exception as error:
            _logger.error(error)
            if not self.env.context.get('cron_skip_connection_errs'):
                self.message_post(body=_('Asking for claim status with response:') + '<br/>: %s <br/>' % response +
                                       _('failed due to:') + '<br/> %s' % error)
        else:
            if response_code == 16:
                today = datetime.today().date()
                diff = abs((today - self.invoice_date).days)
                if diff >= 8:
                    response_code = 'ACD'
            self.l10n_cl_claim = response_code
            self.message_post(body=_('Asking for claim status with response:') + '<br/> %s' % response)

class AccountMoveLine (models.Model):
    _inherit = 'account.move.line'

    is_line_xml = fields.Boolean(string='Es una linea del XML')

    def cron_is_line_xml(self):
        for rec in self.filtered(lambda s: not s.exclude_from_invoice_tab):
            if rec.l10n_cl_dte_file:
                rec.is_line_xml = True
