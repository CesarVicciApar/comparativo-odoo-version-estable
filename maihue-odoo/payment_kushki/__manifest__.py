{
    'name': 'Quemari Kushki integration',
    'version': '0.1',
    'category': 'Payment',
    'summary': 'Quemari Kushki integration',
    'description': """
        Quemari Kushki integration
        ==========================
    """,
    'website': 'https://www.blueminds.cl/',
    'authors':  'Quemari,'
                'Frank Quatromani <fquatromani@blueminds.cl>,'
                'Blueminds',
    'depends': [
        'base',
        'payment',
        'agreement_blueminds',
        'web',
        'website'
    ],
    'data': [
        'security/ir.model.access.csv',
        #'views/assets.xml',
        'data/sequence_kushki.xml',
        'wizard/payment_method_wizard_view.xml',
        'views/account_move_views.xml',
        'views/payment_kushki_view.xml',
        'views/kushki_log.xml',
        'views/res_partner_views.xml',
        'views/portal_template.xml',
        'views/portal_template_payment_methods_partner.xml',
        'views/portal_template_my_contracts.xml',
        'views/contracts.xml',
        'views/payment_method_partner.xml',
        'views/account_move_views.xml',
        'views/bank_intermediary_views.xml',
        'views/payment_bank_view.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            #'payment_kushki/static/src/js/kushki.min.js',
            'payment_kushki/static/src/css/style.scss',
            'payment_kushki/static/src/js/modal_kushki_payment.js',
            'payment_kushki/static/src/js/modal_list_contract.js',
            'payment_kushki/static/src/js/modal_associate_contract.js',
            'payment_kushki/static/src/js/modal_kushki_contract.js',
            'payment_kushki/static/src/js/kushki_payment.js',
            'payment_kushki/static/src/js/DialogPaymentMethod.js'
        ],
        'web.assets_qweb': [
            'payment_kushki/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
}
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

