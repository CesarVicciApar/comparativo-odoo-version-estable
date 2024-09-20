from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import datetime
import json
import time
import uuid
_logger = logging.getLogger(__name__)

try:
    import urllib3
    urllib3.disable_warnings()
    pool = urllib3.PoolManager()
except:
    _logger.warning("no se ha cargado urllib3")

class Proceso(models.Model):

    _name = 'l10n_cl_helpit_conciliacion.proceso'

    journal = fields.Many2one(
            'account.journal',
            string="Diario sobre el que se ejecuta la conciliación"
    )
    state = fields.Selection(string="Estado del proceso",selection=[('in_process','En Proceso'),('no_executed','No Ejecutado'), ('in_queue','En Cola')])
    
    date = fields.Datetime(string="Fecha Inicio")
    date_end = fields.Datetime(string="Fecha Fin")   
    fecha_corte =  fields.Date(string="Fecha Corte")   
    execution_key =  fields.Char(string="Llave de ejecución")   

    @api.model
    def conciliar(self, id):
       _logger.info(f"ID CONSI===>{id}")
       journal = self.search([("id" , "in", id)], limit=1)
       ICPSudo = self.env['ir.config_parameter'].sudo()
       url = ICPSudo.get_param('maihue_conciliacion.url_api_conciliacion')
       _logger.info(f"JJJ===>{journal}, ==> {journal.journal.id} => {journal.fecha_corte}")
       if not url:
            raise UserError("No se ha configurado una url de api de conciliación masiva")
       resp = pool.request('POST',
                           url,
                           headers={'Content-Type': 'application/json'},
                           body= json.dumps({
                               "diario" : journal.journal.id,
                               "fecha_corte" :self.formatDate(journal.fecha_corte),
                               "execution_key" : str(uuid.uuid4())
                           }) )
               
       if resp.status == 200:
          return {
            'type': 'ir.actions.client',
            'tag': 'reload',
          }
       else:
          raise UserError("Hubo un error al ejecutar el proceso") 
    def formatDate(self, obj):
        _logger.info(f"FECHA=> {obj}")
        if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.strftime("%Y-%m-%d")
        else:    
            raise Exception("No es un formato fecha")
    

    @api.model
    def _ejecutar_todo(self):
        try:
            for p in self.search([]):
                p.conciliar([p.id])
                time.sleep(1)

        except Exception as e:
            raise UserError(e) 

