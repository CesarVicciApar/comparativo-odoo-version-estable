from odoo import fields, models
from odoo.exceptions import UserError

class RejectReasonWizard(models.TransientModel):
    _name = "reject.reason.wizard"
    _description = "Wizard motivo rechazo"
    
    reject_reason_id = fields.Many2one('reject.reason', string='Motivo')
    reason_detail = fields.Char('Descripcion detallada')
    
    def applied_reason(self):
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])
        if self.reject_reason_id:
            picking.reject_reason_id = self.reject_reason_id.id
            msg = f"""
                <strong>Detalle del Motivo<strong>
                <br />
                <br />
                <b>Motivo:  {self.reject_reason_id.name}</b>
                <br />
                <b>Descripcion Detallada:  {self.reason_detail}</b>
                <br />
            """
            picking.message_post(body=msg)
            picking.state = 'check'
        else:
            raise UserError("Debe seleccionar un motivo de rechazo")