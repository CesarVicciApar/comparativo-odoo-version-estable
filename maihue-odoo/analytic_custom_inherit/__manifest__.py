# -*- coding: utf-8 -*-
{
    'name': "Cuentas Analiticas 2 y 3",

    'summary': """
        Se agregan modelos cuentas analiticas 2 y 3
    """,

    'description': """
        Se agregan modelos cuentas analiticas 2 y 3
    """,

    'author': "Blueminds",
    'website': "http://www.blueminds.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'analytic', 'base', 'bm_products'],

    # always loaded
    'data': [
        'security/analytic_security.xml',
        'security/ir.model.access.csv',
        'views/analytic_account_two_views.xml',
        'views/analytic_account_three_views.xml',
        'views/analytic_account_four_views.xml',
        'views/account_menuitem.xml',
        'views/account_analytic_default_two_view.xml',
        'views/account_analytic_default_three_view.xml',
        'views/account_analytic_default_four_view.xml',
        'views/account_move_views.xml',
        'views/product_views.xml',
    ]
}
