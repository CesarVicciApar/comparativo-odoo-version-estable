# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    scheduled_date = fields.Date('Fecha Pautada')
    mass_invoice = fields.Boolean('Factura Masiva')
    pre_valid = fields.Boolean('Preliquidacion validada')
    pre_liquid = fields.Boolean('Preliquidacion')
    uf_rate = fields.Float('Tasa UF', digits=(16, 2), default=lambda self: self._get_uf())
    order_ids = fields.Many2many("sale.order", string='Orders', compute="_get_orders", readonly=True, copy=False)
    order_count = fields.Integer(string='Sale Order Count', compute='_get_orders')
    queue_id = fields.Many2one('invoice.generation.queue', 'Cola de Factura')
    invoice_partner_dir_id = fields.Many2one('res.partner', 'Contacto Facturacion')

    def cron_gen_invoice_queue(self):
        InvoiceGen = self.env['invoice.gen']
        InvoiceGenerationQueue = self.env['invoice.generation.queue']
        currencies = self.env['res.currency'].search([('active', '=', True), ('name', '!=', self.env.company.currency_id.name)])
        list_currencies = []
        for currency in currencies:
            list_currencies.append((0, 0, {
                'currency_id': currency.id,
                'rate': currency.rate_ids.filtered(lambda s: s.name == datetime.today().date() + timedelta(days=1)).inverse_company_rate
            }))
        values = {
            'date_from': datetime.today().date(),
            'date_to': datetime.today().date(),
            'scheduled_date': datetime.today().date() + timedelta(days=1),
            'currency_rate_ids': list_currencies
        }
        _logger.info('Wizard de Facturas masivas: %s' % values)
        record_invoice_gen = InvoiceGen.create(values)
        if record_invoice_gen:
            record_invoice_gen.generate_invoices()
        InvoiceGenerationQueue.cron_process_invoice_queue()


    def _get_uf(self):
        uf = self.env['res.currency'].search([('name', '=', 'UF')])
        rate = 1 / float(uf.rate)
        return rate

    def cron_invoice_public(self):
        # search for invoices of the day to be published
        _logger.info("Cron de publicacion de facturas")
        today_date = fields.Datetime.now()
        invoices = self.env['account.move'].search([('scheduled_date', '=', today_date),
                                                    ('move_type', '=', 'out_invoice'),
                                                    ('mass_invoice', '=', True),
                                                    ('state', '=', 'draft')])
        if invoices:
            for inv in invoices:
                if inv.pre_valid and inv.pre_liquid:
                    try:
                        inv.action_post()
                    except Exception as error:
                        self.env['invoice.log'].create({
                            'name': 'Publicación de facturas',
                            'observations': '%s' % error
                        })
                if not inv.pre_valid and not inv.pre_liquid:
                    try:
                        inv.action_post()
                    except Exception as error:
                        self.env['invoice.log'].create({
                            'name': 'Publicación de facturas',
                            'observations': '%s' % error
                        })
        return True

    #@api.depends('state')
    def _get_orders(self):
        SaleOrder = self.env['sale.order']
        for inv in self:
            sale_ids = SaleOrder.search([('state', '=', 'sale')]).filtered(lambda s: inv.id in s.invoice_ids.ids)
            inv.order_ids = sale_ids
            inv.order_count = len(sale_ids)

    def action_view_order(self):
        orders = self.mapped('order_ids')
        action = self.env.ref('sale_renting.rental_order_today_return_action').read()[0]
        action['domain'] = [('id', 'in', orders.ids)]
        action['context'] = False
        form_view = [(self.env.ref('sale_renting.rental_order_view_tree').id, 'tree')]
        action['views'] = form_view
        return action

    def action_post(self):
        #inherit of the function from account.move to validate a new tax and the priceunit of a downpayment
        moves_with_payments = self.filtered('payment_id')
        other_moves = self - moves_with_payments
        if moves_with_payments:
            moves_with_payments.payment_id.action_post()
        if other_moves:
            other_moves._post(soft=False)
        line_ids = self.mapped('line_ids')
        for line in line_ids:
            if len(line.sale_line_ids) > 1:
                for sol in line.sale_line_ids:
                    if sol.is_downpayment:
                        try:
                            line.sale_line_ids.tax_id = line.tax_ids
                            if all(line.tax_ids.mapped('price_include')):
                                sol.price_unit = line.price_unit
                            else:
                                #To keep positive amount on the sale order and to have the right price for the invoice
                                #We need the - before our untaxed_amount_to_invoice
                                sol.price_unit = -sol.untaxed_amount_to_invoice
                        except UserError:
                            # a UserError here means the SO was locked, which prevents changing the taxes
                            # just ignore the error - this is a nice to have feature and should not be blocking
                            pass
            else:
                if line.sale_line_ids.is_downpayment:
                    try:
                        line.sale_line_ids.tax_id = line.tax_ids
                        if all(line.tax_ids.mapped('price_include')):
                            line.sale_line_ids.price_unit = line.price_unit
                        else:
                            # To keep positive amount on the sale order and to have the right price for the invoice
                            # We need the - before our untaxed_amount_to_invoice
                            line.sale_line_ids.price_unit = -line.sale_line_ids.untaxed_amount_to_invoice
                    except UserError:
                        # a UserError here means the SO was locked, which prevents changing the taxes
                        # just ignore the error - this is a nice to have feature and should not be blocking
                        pass
        return False

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cost_center_str = fields.Char('Centro de Costo')
