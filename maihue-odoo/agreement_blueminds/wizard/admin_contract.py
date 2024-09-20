# -*- coding: utf-8 -*-
# © 2023 (Jamie Escalante <jescalante@blueminds.cl>)
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class AdminContract(models.TransientModel):
    _name = "admin.contract"
    _description = "Masivo de Administradores de Contratos"

    user_id_last = fields.Many2one(
        "res.users", string="Administrador a Asignar", track_visibility="onchange")

    def save_admin_contract(self):
        if not self.user_id_last:
            raise UserError('Por favor ingrese el administrador Responsable')
        context = dict(self.env.context)
        agreement = context.get('active_ids')
        for contract in agreement:
            line = self.env['agreement'].search([('id', '=', contract)])
            if line:
                line.write({'admin_id': self.user_id_last.id})
        return True

class AdminContractLine(models.TransientModel):
    _name = "admin.contract.line"
    _description = "Masivo de Administradores de lineas de Contratos"

    user_id_last = fields.Many2one(
        "res.users", string="Administrador a Asignar", track_visibility="onchange")

    def save_admin(self):
        if not self.user_id_last:
            raise UserError('Por favor ingrese el administrador Responsable')
        context = dict(self.env.context)
        agre_line = context.get('active_ids')
        for contract in agre_line:
            line = self.env['agreement.line'].search([('id', '=', contract)])
            if line:
                line.write({'admin_line_id': self.user_id_last.id})
        return True

    def save_admin_contract(self):
        if not self.user_id_last:
            raise UserError('Por favor ingrese el administrador Responsable')
        context = dict(self.env.context)
        agreement = context.get('active_ids')
        for contract in agreement:
            line = self.env['agreement.line'].search([('id', '=', contract)]).agreement_id
            if line:
                line.write({'admin_id': self.user_id_last.id})
        return True