# -*- coding: utf-8 -*-
{
    'name': 'Your Signature',
    'version': '0.1',
    'category': 'Uncategorized',
    'summary': 'Your Signature',
    'description': 'Your Signature',
    'author': 'Blueminds',
    'contribuitors': 'Gabriela Paredes <isabelgpb21@gmail.com>',
    'website': 'https://www.blueminds.cl/',
    'depends': [
        'agreement_blueminds',
        #'payment_integration_base',
        'bus',
    ],
    'data': [
        'data/ir_cron_your_signature.xml',
        'data/data_mail_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/your_signature.xml',
        'views/agreement_extra.xml',
        # 'views/portal_template_your_signature.xml',
        'views/res_config_settings_views.xml',
        'views/res_users.xml',
    ],
    # 'assets':{
    #     'web.assets_frontend': [
    #         'your_signature/static/src/css/style.css',
    #         'your_signature/static/src/js/modal_your_signature.js'
    #     ]
    # },
    'installable': True,
    'auto_install': False,
}
# Part of Odoo. See LICENSE file for full copyright and licensing details.
