# -*- coding: utf-8 -*-
{
    'name': "l10n_cl_vista_rut",

    'summary': """
        Crea un nuevo filtro en facturas y clientes/proveedor para buscar el VAT""",

    'description': """
        Crea un nuevo filtro en facturas y clientes/proveedor para buscar el VAT
    """,

    'author': "Blue MInds",
    'website': "http://www.blueminds.cl",
    "contributors": ["Gonzalo Robles <grobles@blueminds.cl>"],

    'category': 'Account',
    'version': '15.0',

    'depends': ['base', 'account'],

    'data': [
        'views/account_move_views.xml',
        'views/res_partner_view.xml'
    ],
}

