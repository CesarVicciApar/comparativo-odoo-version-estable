# -*- coding: utf-8 -*-
{
    'name': "Conciliación Bancaria Maihue",

    'summary': """
       Servicio de Conciliación Bancaria Maihue
        """,

    'description': """
        Servicio de Conciliación Bancaria Maihue
    """,

    'author': "Luis Meza",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '1.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/conciliacion_masiva.xml',     
        'views/menu.xml',
        'data/data.xml',
        'views/res_config_setting.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
}