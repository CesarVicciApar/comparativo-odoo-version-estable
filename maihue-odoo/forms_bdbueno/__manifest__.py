# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Forms BdBueno',
    'version': '1.0',
    'category': 'Uncategorized',
    'summary': 'Forms BdBueno',
    'description': 'Forms BdBueno',
    'author': 'Blueminds',
    'contribuitors': 'Jamie Escalante <jamie.escalante7@gmail.com>',
    'website': 'https://www.blueminds.cl/',
    'depends': [
        'agreement_blueminds',
    ],
    'data': [
        'data/ir_cron_crm_form.xml',
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/res_config_settings_views.xml',
        # 'views/res_users.xml',
    ],
    'installable': True,
    'auto_install': False,
}
