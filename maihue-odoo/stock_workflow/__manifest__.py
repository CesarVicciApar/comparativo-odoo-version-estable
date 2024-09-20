# -*- coding: utf-8 -*-
{
    'name': "Stock Workflow",
    'summary': """
        Flujo de estados de los equipos   
    """,
    'description': """
        Flujo de estados de los equipos
    """,
    'author': "Blueminds",
    'website': "http://blueminds.cl",
    'colaborators': "Frank Quatromani <fquatromani@blueminds.cl>",
    'category': 'Account',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['stock', 'stock_exchange_product_lot', 'repair', 'agreement_blueminds'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data_repair_type_line.xml',
        'wizard/stock_ready_confirm_views.xml',
        'wizard/reject_reason_wizard_views.xml',
        'wizard/exchange_serial_number_quant_views.xml',
        'wizard/add_serial_number_quant_views.xml',
        'wizard/product_repair_order_wizard_views.xml',
        'views/res_users_views.xml',
        'views/stock_production_lot_views.xml',
        'views/stock_consumible_pieces_views.xml',
        'views/stock_missing_pieces_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_location_views.xml',
        'views/reject_reason_views.xml',
        'views/equipment_state_views.xml',
        'views/repair_order_view.xml',
        'views/repair_line_type_views.xml',
        'views/stock_quants_view.xml',
        'views/product_views.xml',
        'views/stock_scrap_views.xml',
        'views/history_contract_line_views.xml',
        'views/agreement_views.xml',
        'views/agreement_line_views.xml'
    ],
}
