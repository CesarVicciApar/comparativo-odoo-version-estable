# -*- coding: utf-8 -*-
{
    'name': "Recepcion de Mercaderías SII",

    'summary': """
        Aceptacion de recepcion de mercaderías
    """,

    'description': """
        Aceptacion de recepcion de mercaderías
    """,

    'author': "Blueminds",
    'website': "http://blueminds.cl",
    'contribuitors': "Frank Quatromani <fquatromani@blueminds.cl>",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'l10n_cl_edi',
    ],

    # always loaded
    'data': [
        'views/account_move_views.xml'
    ],
    
    'installable': True,
    'auto_install': False,
    'demo': [],
    'test': [],
}
