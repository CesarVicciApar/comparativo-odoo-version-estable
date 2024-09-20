# -*- coding: utf-8 -*-
{
    'name': "Productos Blueminds",

    'summary': """
        Customizacion de modulos a solicitud de clientes """,

    'description': """
        Adecuaciones a solicitud:

        - Al leer XML desde email DTE se debe crear un PDF a partir de ese XML y dejarlo Adjunto
        - Al leer el XML desde email DTE en la descripcion de la factura debe concatenar el <NmbItem> seguido de  // y por ultimo el <DscItem>
        - 
    """,

    'author': "Blueminds Spa",
    'website': "http://www.blueminds.cl",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_cl_edi', 'account'],

    # always loaded
    'data': [
        'security/group_account.xml',
        'data/ir_cron.xml',
        'report/report_invoice_from_xml.xml',
        # 'views/views.xml',
        'views/account_move.xml',
        'views/res_partner_view.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            '/bm_products/static/src/css/style.css',
        ],
    },
}
