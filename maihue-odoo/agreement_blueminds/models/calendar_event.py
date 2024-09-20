# -*- coding: utf-8 -*-
# © 2024 (Jamie Escalante <jescalante@bbrands.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import math
import logging
from datetime import timedelta
from itertools import repeat

import pytz

from odoo import api, fields, models, Command
from odoo.osv.expression import AND
from odoo.addons.base.models.res_partner import _tz_get
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from odoo.tools import pycompat, html2plaintext, is_html_empty
from odoo.exceptions import UserError, ValidationError

class Meeting(models.Model):
    _inherit = 'calendar.event'

    planning_id = fields.Many2one('planning.slot', 'planning id', ondelete='cascade')

    def write(self, values):
        if self.planning_id:
            start = self.start
            stop = self.stop
            if 'start' in values:
                start = values['start']
            if 'stop' in values:
                stop = values['stop']
            self.planning_id.write({'start_datetime': start, 'end_datetime': stop})

        return super(Meeting, self).write(values)