# -*- coding: utf-8 -*-
{
    'name': "BlueMinds Switch Currency V13",

    'summary': """
        * Permite manejar cambios de moneda en los stocks
        * Genera asientos contables convirtiendo los montos""",

    'description': """
        Este modulo permite manejar cambios de moneda en los stocks, 
        y generar asientos contables convirtiendo los montos a la 
        moneda de la compañia.
    """,

    'author': "Blueminds",
    'website': "http://www.blueminds.cl",
    'contributors': ["Boris Silva <silvaboris@gmail.com>"],

    'category': 'Stock',
    'version': '0.1',

    'depends': ['base', 'stock', 'purchase', 'account'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_views.xml',
        'views/account_views.xml',
    ],
}
