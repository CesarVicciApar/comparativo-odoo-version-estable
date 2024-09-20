# -*- coding: utf-8 -*-
{
    'name': 'Account - Renconcile all Lines',
    'version': '14.0.1.0.0',
    'summary': 'Renconcile all Lines',
    'description': 'Renconcile all Lines',
    'category': '',
    'author': 'Blueminds',
    'website': "blueminds.cl",
    'license': 'LGPL-3',
    'contributors': [
        'Luis Cartaya <luiscartaya653@gmail.com>',
    ],
    'depends': [
        'account', 'account_accountant'
    ],
    # 'data': [
    #     'views/assets.xml',
    # ],
    'assets': {
        'web.assets_backend': [
            'account_accountant_renconcile_all/static/src/js/reconciliation_validate_all.js',
        ],
        'web.assets_qweb': [
            'account_accountant_renconcile_all/static/src/xml/account_reconciliation.xml',
        ],
    },
    # 'qweb': [
    #     'static/src/xml/account_reconciliation.xml',
    # ],
    'installable': True,
}