{
    'name': 'Crm Dicom Integration',
    'version': '0.3',
    'category': 'Uncategorized',
    'summary': 'Dicom Integration',
    'description': 'Dicom Integration',
    'depends': [
        'contacts', 'crm', 'base', 'contacts', 'agreement_blueminds'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'templates/template_request.xml',
        'report/report_dicom_platinum.xml',
        'report/report_dicom_commercial.xml',
        'views/history_request_dicom_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_view.xml',
        'views/res_config_settings_view.xml',
        'views/dicom_report.xml',
        'views/agreement_views.xml',
        'wizards/dicom_massive_crm_wizard.xml',
        'wizards/dicom_massive_partner_wizard.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            '/bm_crm_dicom_integration/static/src/css/dicom.css',
        ],
    },
    'installable': True,
    'auto_install': False,
}
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
