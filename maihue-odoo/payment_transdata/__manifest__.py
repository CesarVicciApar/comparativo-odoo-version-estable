# coding: utf-8
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Payment Transdata',
    'version': '1.1',
    'author': 'Blue Minds SpA,'
              'Jamie Escalante (jescalante@blueminds.cl)',
    'maintainer': 'Blue Minds SpA,'
                  'Jamie Escalante (jescalante@blueminds.cl)',
    'website': 'http://www.blueminds.cl',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'summary': 'Carga de pagos Transdata',
    'depends': ['account', 'account_bank_statement_import', 'agreement_blueminds'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'views/res_partner_view.xml',
    ],
    #'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False
}
