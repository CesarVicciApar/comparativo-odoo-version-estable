# -*- coding: utf-8 -*-
{
    'name': "Import Stock Product Lot",
    'summary': """
        Importar numeros de lote/serie en ordenes de recepcion   
    """,
    'description': """
        Importar numeros de lote/serie en ordenes de recepcion
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
        'wizard/import_serial_number_views.xml',
        'views/stock_picking_views.xml'
    ],
}
