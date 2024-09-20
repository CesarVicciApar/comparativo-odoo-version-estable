# -*- coding: utf-8 -*-
{
    'name': "Actualizar Tasa UF SII",
    'summary': """
        Obtener tasas de UF de la url del SII    
    """,
    'description': """
        Obtener tasas de UF de la url del SII 
    """,
    'author': "Blueminds",
    'website': "http://blueminds.cl",
    'colaborators': "Frank Quatromani <fquatromani@blueminds.cl>",
    'category': 'Account',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base'],
    # always loaded
    'data': [
        'data/ir_cron_scrapping_rate_uf.xml'
    ],
}
