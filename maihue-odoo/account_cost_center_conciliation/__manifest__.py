# -*- encoding: utf-8 -*-
{
    'name': 'Account Cost Center Conciliation',
    'version': '14.0',
    'summary': 'Account Cost Center Conciliation',
    'description': 'Account Cost Center Conciliation',
    'category': 'Extra Tools',
    'author': 'Blueminds',
    'license': 'LGPL-3',
    'contributors': 'Luis Cartaya <luiscartaya653@gmail.com>',
    'depends': [
        'account_accountant', 'blue_jt_cost_centers', 'account'
    ],
    # 'data': [
    #     '',
    # ],
    'assets': {
        'web.assets_backend': [
            'account_cost_center_conciliation/static/src/js/reconciliation/reconciliation_renderer.js',
            'account_cost_center_conciliation/static/src/js/reconciliation/reconciliation_model.js',
        ],
        'web.assets_qweb': [
            'account_cost_center_conciliation/static/src/xml/account_reconciliation.xml',
        ],
    },
    'installable': True
}