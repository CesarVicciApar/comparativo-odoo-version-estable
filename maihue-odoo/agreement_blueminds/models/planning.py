# -*- coding: utf-8 -*-
# © 2024 (Jamie Escalante <jescalante@bbrands.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import date, datetime, timedelta, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_utils, format_datetime


class Planning(models.Model):
    _inherit = 'planning.slot'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        task = self.env['project.task'].search([('id', '=', res.task_id.id)])
        calendar = {
            'name': 'Visita a: ' + task.partner_id.name,
            'partner_ids': [(6,0,task.partner_id.ids)],
            'start': res.start_datetime,
            'stop': res.end_datetime,
            #'duration': 1,
            'user_id': res.resource_id.id,
            'description': res.name,
            #'alam_ids': 1,
            #'location': 1,
            #'videocall_location': 1,
            #'categ_ids': 1
            'planning_id': res.id
        }
        self.env['calendar.event'].create(calendar)
        return res

