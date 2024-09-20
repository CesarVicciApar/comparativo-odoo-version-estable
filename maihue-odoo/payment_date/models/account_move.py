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

    invoice_payment_date = fields.Text(string='Ultima fecha de pago')

