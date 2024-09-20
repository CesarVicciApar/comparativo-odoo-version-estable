# -*- coding: utf-8 -*-
# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, SUPERUSER_ID, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_card_status = fields.Selection([
        ('activa', 'Activa'),
        ('bloqueada', 'Bloqueada')], "Estado Tarjeta de Credito")