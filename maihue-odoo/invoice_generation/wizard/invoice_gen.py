# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from logging import getLogger

_logger = getLogger(__name__)


class InvoiceGen(models.TransientModel):
    _name = 'invoice.gen'
    _description = u'Generación de Facturas'

    def default_date_scheduled(self):
        date_scheduled = date.today() + timedelta(days=1)
        return date_scheduled

    def default_currency_rates(self):
        currency = self.env['res.currency'].search([('active', '=', True)]).ids
        return currency

    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    type_gen = fields.Selection(selection=[
        ('integral', 'Integral Cliente'),
        ('contrato', 'Separada por Contrato')], string='Tipo de Generación', required=False)
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[])
    uf_rate = fields.Float('Tasa UF', digits=(16, 2), default=lambda self: self._get_uf())
    currency_rate_ids = fields.One2many('invoice.gen.currency', 'invoice_gen_id', string='Tasas')
    scheduled_date = fields.Date('Fecha Pautada', default=default_date_scheduled)
    not_date = fields.Boolean()

    def _get_uf(self):
        uf = self.env['res.currency'].search([('name', '=', 'UF')])
        rate_date = uf.rate_ids.filtered(lambda s: s.name == self.scheduled_date)
        return rate_date.inverse_company_rate

    @api.onchange('scheduled_date')
    def onchange_scheduled_date(self):
        if self.scheduled_date:
            currencies = self.env['res.currency'].search([('active', '=', True), ('name', '!=', self.env.company.currency_id.name)])
            if currencies:
                if not self.currency_rate_ids:
                    for currency in currencies:
                        vals = {
                            'invoice_gen_id': self.id,
                            'currency_id': currency.id,
                            'rate': currency.rate_ids.filtered(lambda s: s.name == self.scheduled_date).inverse_company_rate
                        }
                        self.env['invoice.gen.currency'].create(vals)
                else:
                    for curr_rate in self.currency_rate_ids:
                        curr_rate.rate = curr_rate.currency_id.rate_ids.filtered(lambda s: s.name == self.scheduled_date).inverse_company_rate
            if self.scheduled_date <= date.today():
                self.not_date = True
            else:
                self.not_date = False
                self.uf_rate = self._get_uf()

    def generate_invoices(self):
        currencies = []
        selected_currencies = self.currency_rate_ids.filtered(lambda r: r.rate != 0.00).mapped('currency_id')
        currency_rates = self.currency_rate_ids.filtered(lambda r: r.rate != 0.00)
        for currency in selected_currencies:
            currencies.append(currency.id)
        currencies.append(self.env.company.currency_id.id)
        if self.not_date:
            raise ValidationError('La fecha pautada debe ser estrictamente mayor a la fecha de hoy')
        # elif self.currency_rate_ids.filtered(lambda r: r.rate == 0.0):
        #     raise ValidationError('Las tasas no pueden ser cero (0)')
        else:
            s_default = [
                ('state', '=', 'sale'),
                ('invoice_status', '=', 'to invoice'),
                ('agreement_currency_id', 'in', currencies),
                ('fecha_fact_prog', '>=', self.date_from),
                ('fecha_fact_prog', '<=', self.date_to)
            ]
            if self.partner_id:
                s_default.append(('partner_id', '=', self.partner_id.id))
            orders = self.env['sale.order'].search(s_default, order='id desc')#.filtered(lambda s: s.fecha_fact_prog >= self.date_from and s.fecha_fact_prog <= self.date_to)
            #type_gen = ['contrato']
            queue_ids = []
            list_rates = []
            InvoiceGenQueueCurrency = self.env['invoice.generation.queue.currency']
            #for tg in type_gen:
            list_orders = []
            if orders:
                for order in orders:
                    if ((order.req_orden and order.reference_ids) or not order.req_orden) and (order.agreement_currency_id.id in selected_currencies.ids or order.agreement_currency_id.id == self.env.ref('base.CLP').id):
                        _logger.info('%s' % order.name)
                        vals = {
                            #'scheduled_date': self.scheduled_date,
                            'mass_invoice': True,
                            'uf_rate': currency_rates.filtered(lambda r: r.currency_id.id == order.agreement_currency_id.id).rate
                        }
                        order.write(vals)
                        list_orders.append(order.id)
                for rate in currency_rates:
                    list_rates.append((0, 0, {
                        'currency_id': rate.currency_id.id,
                        'rate': rate.rate
                    }))
                vals_queue = {
                    'name': 'Cola de creacion de facturas desde %s hasta %s' % (self.date_from, self.date_to),
                    'date': date.today(),
                    'scheduled_date': self.scheduled_date,
                    #'type_gen': tg,
                    'rental_ids': list_orders,
                    'queue_rate_ids': list_rates
                }
                try:
                    queue_id = self.env['invoice.generation.queue'].create(vals_queue)
                    self.env['invoice.log'].create({
                        'name': 'Creacion colas de rentals',
                        'observations': 'la cola %s ha sido creada con exito' % queue_id.name,
                        'invoice_gen_queue_id': queue_id.id
                    })
                    queue_ids.append(queue_id.id)
                except Exception as error:
                    self.env['invoice.log'].create({
                        'name': 'Creacion colas de rentals',
                        'observations': '%s' % error
                    })
            else:
                if 'from_cron' not in self.env.context:
                    raise ValidationError('No se encontraron registros coincidentes')
                else:
                    self.env['invoice.log'].create({
                        'name': 'Creacion colas de rentals',
                        'observations': 'No se encontraron registros coincidentes'
                    })
            if queue_ids and 'from_cron' not in self.env.context:
                action = self.env["ir.actions.actions"]._for_xml_id("invoice_generation.invoice_generation_queue_action")
                if len(queue_ids) > 1:
                    action['domain'] = [('id', 'in', queue_ids)]
                elif len(queue_ids) == 1:
                    form_view = [(self.env.ref('invoice_generation.invoice_generation_queue_view_form').id, 'form')]
                    if 'views' in action:
                        action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
                    else:
                        action['views'] = form_view
                    action['res_id'] = queue_ids[0]
                else:
                    action = {'type': 'ir.actions.act_window_close'}
                return action

class InvoiceGen(models.TransientModel):
    _name = 'invoice.gen.currency'
    _description = u'Generacion Facturas Tasas'

    invoice_gen_id = fields.Many2one('invoice.gen')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    date = fields.Date(related='invoice_gen_id.scheduled_date', store=True)
    rate = fields.Float(string='Tasa')

    @api.onchange('date')
    def onchange_date_get_rate(self):
        if self.date:
            rate_date = self.currency_id.rate_ids.filtered(lambda s: s.name == self.date)
            self.rate = rate_date.inverse_company_rate
