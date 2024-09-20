# -*- coding: utf-8 -*-

import base64
import email
import logging
import os

from lxml import etree
from odoo import api, fields, models, tools, _
from odoo.tests import Form
from odoo.tools.misc import formatLang
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

XML_NAMESPACES = {
    'ns0': 'http://www.sii.cl/SiiDte',
    'ns1': 'http://www.w3.org/2000/09/xmldsig#',
    'xml_schema': 'http://www.sii.cl/XMLSchema'
}


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    def _get_invoice_form(self, company_id, partner, default_move_type, from_address, dte_xml, document_number,
                          document_type, msgs):
        """
        This method creates a draft vendor bill from the attached xml in the incoming email.
        """
        with self.env.cr.savepoint(), Form(self.env['account.move'].with_context(
                default_move_type=default_move_type, allowed_company_ids=[company_id],
                account_predictive_bills_disable_prediction=True)) as invoice_form:
            invoice_form.partner_id = partner
            invoice_form.invoice_source_email = from_address
            invoice_date = dte_xml.findtext('.//ns0:FchEmis', namespaces=XML_NAMESPACES)
            if invoice_date is not None:
                invoice_form.invoice_date = fields.Date.from_string(invoice_date)
            # Set the date after invoice_date to avoid the onchange
            invoice_form.date = fields.Date.context_today(
                self.with_context(tz='America/Santiago'))

            invoice_date_due = dte_xml.findtext('.//ns0:FchVenc', namespaces=XML_NAMESPACES)
            if invoice_date_due is not None:
                invoice_form.invoice_date_due = fields.Date.from_string(invoice_date_due)

            journal = self._get_dte_purchase_journal(company_id)
            if journal:
                invoice_form.journal_id = journal
            currency = self._get_dte_currency(dte_xml)
            if currency:
                invoice_form.currency_id = currency

            invoice_form.l10n_latam_document_type_id = document_type
            invoice_form.l10n_latam_document_number = document_number
            invoice_form.backup_document_number = document_number.zfill(6)
            for invoice_line in self._get_dte_lines(dte_xml, company_id, partner.id):
                price_unit = invoice_line.get('price_unit')
                with invoice_form.invoice_line_ids.new() as invoice_line_form:
                    invoice_line_form.product_id = invoice_line.get('product', self.env['product.product'])
                    invoice_line_form.is_line_xml = True
                    invoice_line_form.name = invoice_line.get('name')
                    invoice_line_form.quantity = invoice_line.get('quantity')
                    invoice_line_form.price_unit = price_unit
                    invoice_line_form.discount = invoice_line.get('discount', 0)

                    if not invoice_line.get('default_tax'):
                        invoice_line_form.tax_ids.clear()
                    for tax in invoice_line.get('taxes', []):
                        invoice_line_form.tax_ids.add(tax)
            for reference_line in self._get_invoice_references(dte_xml):
                if not self._is_valid_reference_doc_type(
                        reference_line.get('l10n_cl_reference_doc_type_selection')):
                    msgs.append(_('There is an unidentified reference in this invoice:<br/>'
                                  '<li>Origin: %(origin_doc_number)s<li/>'
                                  '<li>Reference Code: %(reference_doc_code)s<li/>'
                                  '<li>Doc Type: %(l10n_cl_reference_doc_type_selection)s<li/>'
                                  '<li>Reason: %(reason)s<li/>'
                                  '<li>Date:%(date)s') % reference_line)
                    continue
                with invoice_form.l10n_cl_reference_ids.new() as reference_line_form:
                    reference_line_form.origin_doc_number = reference_line['origin_doc_number']
                    reference_line_form.reference_doc_code = reference_line['reference_doc_code']
                    reference_line_form.l10n_cl_reference_doc_type_selection = reference_line[
                        'l10n_cl_reference_doc_type_selection']
                    reference_line_form.reason = reference_line['reason']
                    reference_line_form.date = reference_line['date']

        return invoice_form, msgs

    def _get_dte_lines(self, dte_xml, company_id, partner_id):
        """
        This parse DTE invoice detail lines and tries to match lines with existing products.
        If no products are found, it puts only the description of the products in the draft invoice lines
        """

        gross_amount = dte_xml.findtext('.//ns0:MntBruto', namespaces=XML_NAMESPACES) is not None
        default_purchase_tax = self.env['account.tax'].search(
            [('l10n_cl_sii_code', '=', 14), ('type_tax_use', '=', 'purchase'),
             ('company_id', '=', company_id)], limit=1)
        currency = self._get_dte_currency(dte_xml)
        invoice_lines = []
        for dte_line in dte_xml.findall('.//ns0:Detalle', namespaces=XML_NAMESPACES):
            product_code = dte_line.findtext('.//ns0:VlrCodigo', namespaces=XML_NAMESPACES)
            product_name = dte_line.findtext('.//ns0:NmbItem', namespaces=XML_NAMESPACES)
            product = self._get_vendor_product(product_code, product_name, company_id, partner_id)
            dsc_item = ''
            if dte_line.findtext('.//ns0:DscItem', namespaces=XML_NAMESPACES):
                dsc_item = ' // ' + dte_line.findtext('.//ns0:DscItem', namespaces=XML_NAMESPACES)
            # the QtyItem tag is not mandatory in certain cases (case 2 in documentation).
            # Should be set to 1 if not present.
            # See http://www.sii.cl/factura_electronica/formato_dte.pdf row 15 and row 22 of tag table
            quantity = float(dte_line.findtext('.//ns0:QtyItem', default=1, namespaces=XML_NAMESPACES))
            # in the same case, PrcItem is not mandatory if QtyItem is not present, but MontoItem IS mandatory
            # this happens whenever QtyItem is not present in the invoice.
            # See http://www.sii.cl/factura_electronica/formato_dte.pdf row 38 of tag table.
            price_unit = float(dte_line.findtext(
                './/ns0:PrcItem', default=dte_line.findtext('.//ns0:MontoItem', namespaces=XML_NAMESPACES),
                namespaces=XML_NAMESPACES))
            discount = float(dte_line.findtext('.//ns0:DescuentoPct', default=0, namespaces=XML_NAMESPACES))\
                       or (float(dte_line.findtext('.//ns0:DescuentoMonto', default=0, namespaces=XML_NAMESPACES)) / (price_unit * quantity) * 100
                           if price_unit * quantity != 0 else 0)
            if product:
                product_dsc = product.name + dsc_item
            else:
                product_dsc = product_name + dsc_item

            values = {
                'product': product,
                'name': product_dsc,
                'quantity': quantity,
                'price_unit': price_unit,
                'discount': discount,
                'default_tax': False
            }
            if (dte_xml.findtext('.//ns0:TasaIVA', namespaces=XML_NAMESPACES) is not None and
                    dte_line.findtext('.//ns0:IndExe', namespaces=XML_NAMESPACES) is None):
                values['default_tax'] = True
                values['taxes'] = self._get_withholding_taxes(company_id, dte_line)
            if gross_amount:
                # in case the tag MntBruto is included in the IdDoc section, and there are not
                # additional taxes (withholdings)
                # even if the company has not selected its default tax value, we deduct it
                # from the price unit, gathering the value rate of the l10n_cl default purchase tax
                values['price_unit'] = default_purchase_tax.with_context(force_price_include=True).compute_all(
                    price_unit, currency)['total_excluded']
            invoice_lines.append(values)

        for desc_rcg_global in dte_xml.findall('.//ns0:DscRcgGlobal', namespaces=XML_NAMESPACES):
            line_type = desc_rcg_global.findtext('.//ns0:TpoMov', namespaces=XML_NAMESPACES)
            price_type = desc_rcg_global.findtext('.//ns0:TpoValor', namespaces=XML_NAMESPACES)
            valor_dr = (desc_rcg_global.findtext('.//ns0:ValorDROtrMnda', namespaces=XML_NAMESPACES) or
                        desc_rcg_global.findtext('.//ns0:ValorDR', namespaces=XML_NAMESPACES))
            values = {
                'name': 'DESCUENTO' if line_type == 'D' else 'RECARGO',
                'quantity': 1,
            }
            amount_dr = float(valor_dr)
            percent_dr = amount_dr / 100
            # The price unit of a discount line should be negative while surcharge should be positive
            price_unit_multiplier = 1 if line_type == 'D' else -1
            if price_type == '%':
                inde_exe_dr = desc_rcg_global.findtext('.//ns0:IndExeDR', namespaces=XML_NAMESPACES)
                if inde_exe_dr is None:  # Applied to items with tax
                    dte_amount_tag = (dte_xml.findtext('.//ns0:MntNetoOtrMnda', namespaces=XML_NAMESPACES) or
                                      dte_xml.findtext('.//ns0:MntNeto', namespaces=XML_NAMESPACES))
                    dte_amount = int(dte_amount_tag or 0)
                    # as MntNeto value is calculated after discount
                    # we need to calculate back the amount before discount in order to apply the percentage
                    # and know the amount of the discount.
                    dte_amount_before_discount = dte_amount / (1 - percent_dr)
                    values['price_unit'] = - price_unit_multiplier * dte_amount_before_discount * percent_dr
                    values['default_tax'] = self._use_default_tax(dte_xml)
                elif inde_exe_dr == '2':  # Applied to items not billable
                    dte_amount_tag = dte_xml.findtext('.//ns0:MontoNF', namespaces=XML_NAMESPACES)
                    dte_amount = dte_amount_tag is not None and int(dte_amount_tag) or 0
                    values['price_unit'] = round(
                        dte_amount - (int(dte_amount) / (1 - amount_dr / 100))) * price_unit_multiplier
                elif inde_exe_dr == '1':  # Applied to items without taxes
                    dte_amount_tag = (dte_xml.findtext('.//ns0:MntExeOtrMnda', namespaces=XML_NAMESPACES) or
                                      dte_xml.findtext('.//ns0:MntExe', namespaces=XML_NAMESPACES))
                    dte_amount = dte_amount_tag is not None and int(dte_amount_tag) or 0
                    values['price_unit'] = round(
                        dte_amount - (int(dte_amount) / (1 - amount_dr / 100))) * price_unit_multiplier
            else:
                if gross_amount:
                    amount_dr = default_purchase_tax.with_context(force_price_include=True).compute_all(
                        amount_dr, currency)['total_excluded']
                values['price_unit'] = amount_dr * -1 * price_unit_multiplier
                if desc_rcg_global.findtext('.//ns0:IndExeDR', namespaces=XML_NAMESPACES) not in ['1', '2']:
                    values['default_tax'] = self._use_default_tax(dte_xml)
            invoice_lines.append(values)
        for imp_espec in dte_xml.findall('.//ns0:ImptoReten', namespaces=XML_NAMESPACES):
            vals = {
                'name': 'Impuesto especifico codigo %s' % imp_espec.findtext('.//ns0:TipoImp', namespaces=XML_NAMESPACES),
                'quantity': 1,
                'price_unit': float(imp_espec.findtext('.//ns0:MontoImp', namespaces=XML_NAMESPACES)),
                'default_tax': False
            }
            invoice_lines.append(vals)
        return invoice_lines

    def _create_invoice_from_attachment(self, att_content, att_name, from_address, company_id):
        moves = []
        xml_content = etree.fromstring(att_content)
        for dte_xml in xml_content.xpath('//ns0:DTE', namespaces=XML_NAMESPACES):
            document_number = self._get_document_number(dte_xml)
            document_type_code = self._get_document_type_from_xml(dte_xml)
            xml_total_amount = float(dte_xml.findtext('.//ns0:MntTotal', namespaces=XML_NAMESPACES))
            document_type = self.env['l10n_latam.document.type'].search(
                [('code', '=', document_type_code), ('country_id.code', '=', 'CL')], limit=1)
            if not document_type:
                _logger.info('DTE has been discarded! Document type %s not found' % document_type_code)
                continue
            if document_type and document_type.internal_type not in ['invoice', 'debit_note', 'credit_note']:
                _logger.info('DTE has been discarded! The document type %s is not a vendor bill' % document_type_code)
                continue

            issuer_vat = self._get_dte_issuer_vat(dte_xml)
            partner = self._get_partner(issuer_vat, company_id)
            if partner and self._check_document_number_exists(partner.id, document_number, document_type, company_id) \
                    or (not partner and self._check_document_number_exists_no_partner(document_number, document_type,
                                                                                      company_id, issuer_vat)):
                _logger.info('E-invoice already exist: %s', document_number)
                continue

            default_move_type = 'in_invoice' if document_type_code != '61' else 'in_refund'
            msgs = []
            try:
                invoice_form, msgs = self._get_invoice_form(
                    company_id, partner, default_move_type, from_address, dte_xml, document_number, document_type, msgs)

            except Exception as error:
                _logger.info(error)
                with self.env.cr.savepoint(), Form(self.env['account.move'].with_context(
                        default_move_type=default_move_type, allowed_company_ids=[company_id],
                        account_predictive_bills_disable_prediction=True)) as invoice_form:
                    msgs.append(error)
                    invoice_form.partner_id = partner
                    invoice_form.l10n_latam_document_type_id = document_type
                    invoice_form.l10n_latam_document_number = document_number

            if not partner:
                invoice_form.narration = issuer_vat or ''
            move = invoice_form.save()
            move.amount_total_xml = xml_total_amount
            # move.difference_amount_warning = True if move.amount_total != xml_total_amount else False
            for line in move.invoice_line_ids:
                line.is_line_xml = True
            dte_attachment = self.env['ir.attachment'].create({
                'name': 'DTE_{}.xml'.format(document_number),
                'res_model': move._name,
                'res_id': move.id,
                'type': 'binary',
                'datas': base64.b64encode(etree.tostring(dte_xml, encoding='utf-8'))
            })
            move.l10n_cl_dte_file = dte_attachment.id
            move.generate_pdf_from_xml_file()
            for msg in msgs:
                move.with_context(no_new_invoice=True).message_post(body=msg)

            msg = _('Vendor Bill DTE has been generated for the following vendor: </br>') if partner else \
                  _('Vendor not found: You can generate this vendor manually with the following information: </br>')
            move.with_context(no_new_invoice=True).message_post(
                body=msg + _(
                    '<li><b>Name</b>: %(name)s</li><li><b>RUT</b>: %(vat)s</li><li>'
                    '<b>Address</b>: %(address)s</li>') % {
                    'vat': self._get_dte_issuer_vat(xml_content) or '',
                    'name': self._get_dte_partner_name(xml_content) or '',
                    'address': self._get_dte_issuer_address(xml_content) or ''}, attachment_ids=[dte_attachment.id])

            if float_compare(move.amount_total, xml_total_amount, precision_digits=move.currency_id.decimal_places) != 0:
                move.message_post(
                    body=_('<strong>Warning:</strong> The total amount of the DTE\'s XML is %s and the total amount '
                           'calculated by Odoo is %s. Typically this is caused by additional lines in the detail or '
                           'by unidentified taxes, please check if a manual correction is needed.')
                    % (formatLang(self.env, xml_total_amount, currency_obj=move.currency_id),
                       formatLang(self.env, move.amount_total, currency_obj=move.currency_id)))
            move.l10n_cl_dte_acceptation_status = 'received'
            moves.append(move)
            _logger.info(_('New move has been created from DTE %s with id: %s') % (att_name, move.id))
        return moves

    def _check_document_number_exists(self, partner_id, document_number, document_type, company_id):
        to_check_documents = self.env['account.move'].sudo().search(
            [('move_type', 'in', ['in_invoice', 'in_refund']),
             ('name', 'ilike', document_number),
             ('partner_id', '=', partner_id),
             ('company_id', '=', company_id)])

        return len(to_check_documents.filtered(
            lambda x: x.l10n_latam_document_type_id.code == document_type.code and
                      x.l10n_latam_document_number.lstrip('0') == document_number.lstrip('0')
        )) > 0

    def _check_document_number_exists_no_partner(self, document_number, document_type, company_id, vat):
        """ This is a separate method for the no partner case to not modify the other method in stable.
            If the partner is not found, we put its vat in the narration field, so we avoid to import twice.
        """
        to_check_documents = self.env['account.move'].sudo().search([
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('name', 'ilike', document_number),
            ('partner_id', '=', False),
            ('narration', '=', vat),
            ('company_id', '=', company_id)])

        return len(to_check_documents.filtered(
            lambda x: x.l10n_latam_document_type_id.code == document_type.code and
                      x.l10n_latam_document_number.lstrip('0') == document_number.lstrip('0')
        )) > 0
