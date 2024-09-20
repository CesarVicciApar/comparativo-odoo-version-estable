# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models, tools

class SaleSubscriptionCloseReasonWizardKushki(models.TransientModel):
    _inherit = "sale.subscription.close.reason.wizard"


    def set_close(self):
        subscription = self.env['sale.subscription'].browse(self.env.context.get('active_id'))
        if subscription.kushki_subscription_token:
            subscription.payment_token_id.acquirer_id._disable_kushki_subscription(subscription.kushki_subscription_token)
            subscription.update({'kushki_subscription_token': ''})
        super(SaleSubscriptionCloseReasonWizardKushki, self).set_close()
        