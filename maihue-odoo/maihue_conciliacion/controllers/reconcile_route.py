from odoo import models, http, api
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import logging
import base64
_logger = logging.getLogger(__name__)
class ReconcileApi(http.Controller):
    @http.route("/reconcile", type='json', auth="user")
    def reconcile(self, **rec):
           
        #_logger.info(f"HOLA SI LLEGA {rec}")   
        #journal = request.env['account.journal'].search([("id", "=", rec["journal"])])
        widget = request.env['account.reconciliation.widget']
        reconciliation = None
        for p in rec["records"]:
            try:
                reconciliation = widget.process_bank_statement_line(p["lines"], p["data"])
            except Exception as e: _logger.info(f"ERRROOOOORRRR=> {e}")   
                 
        #_logger.info(f"PD===========================> {pdf}")
        return {'result': reconciliation}
        