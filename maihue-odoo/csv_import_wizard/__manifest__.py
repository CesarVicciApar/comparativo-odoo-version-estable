# -*- coding: utf-8 -*-
{
    'name': 'Import csv',
    'version' : '13.0.0.0.1',
    'summary': '',
    'description': """ Módulo que genera la carga masiva de clientes y facturas """,
    'category': '',
    'author': 'Blueminds',
    'website': 'www.Blueminds.cl',
    "contributors": [
        "Gabriela Paredes <isabelgpb21@gmail.com>",
    ],
    'depends': [
        'base',
        'account',
        'account_accountant',
        'l10n_cl',
        'l10n_latam_invoice_document',
        'bus',
    ],
    'data': [
        'data/data_product.xml',
        'security/ir.model.access.csv',
        'wizard/import_wizard.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
