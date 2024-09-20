# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from stdnum import get_cc_module
import requests
import json

class KushkiLog(models.Model):
    _name = 'kushki.log'
    _description = 'Kushki Log'
    _order = 'id desc'

    name = fields.Char(string="Referencia", default="Nuevo")
    user_id = fields.Many2one('res.users', string="Usuario")
    partner_id = fields.Many2one('res.partner', string="Cliente")
    card_number = fields.Char(string="Número de Tarjeta")
    token_card = fields.Char(string='Suscripción')
    method_name = fields.Char(string="Nombre del método")
    answer = fields.Text(string="Respuesta")
    error_code = fields.Char(string="Código del error")
    description_error = fields.Char(string="Descripción del error")
    document = fields.Char('Documento', help="Documento relacionado al cobro realizado a la tarjeta")

    @api.model
    def validate_document_number(self, val):
        mod = get_cc_module('cl', 'rut')
        val_rut = mod.is_valid(val)
        return val_rut

    @api.model
    def create_log_request_token(self, user, response, method):
        KushkiLog = self.env['kushki.log']
        user_id = self.env['res.users'].search([('id', '=', user)])
        log = KushkiLog.create({
            'partner_id': user_id.partner_id.id,
            'user_id': user_id.id,
            'method_name': method,
            'error_code': response['code'] if 'code' in response else '',
            'description_error': response['message'] if 'message' in response else '',
            'answer': json.dumps(response, indent=4).replace('\n', '<br/>'),
        })
        return log

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            seq = self.env['ir.sequence'].next_by_code('kushki.log') or 'Nuevo'
            vals['name'] = seq
        return super(KushkiLog, self).create(vals)