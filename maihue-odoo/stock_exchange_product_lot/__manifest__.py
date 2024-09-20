# -*- coding: utf-8 -*-
{
    'name': "Stock Exchange Product Lot",
    'summary': """
        Intercambiar numeros de lote/serie entre transferenicas en proceso   
    """,
    'description': """
        Intercambiar numeros de lote/serie entre transferenicas en proceso
    """,
    'author': "Blueminds",
    'website': "http://blueminds.cl",
    'colaborators': "Frank Quatromani <fquatromani@blueminds.cl>",
    'category': 'uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['stock'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/exchange_serial_number_views.xml',
        'views/stock_picking_views.xml'
    ],
}
