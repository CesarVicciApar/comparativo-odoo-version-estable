# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import Warning, UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    lead_your_firm = fields.Boolean(string="Firmante Maihue")
