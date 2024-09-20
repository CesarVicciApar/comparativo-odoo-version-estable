# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")

class StockMove(models.Model):
    _inherit = "stock.move"

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                   cost):
        res = super(StockMove, self)._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty,
                                                                description, svl_id, cost)
        if isinstance(res, dict):
            res.update({
                'cost_center_id': self.picking_id.cost_center_id.id if self.picking_id.cost_center_id else False
            })
        return res
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
       res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
       for line in res:
           line[2]['cost_center_id'] = self.cost_center_id.id
       return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'type': 'entry',
                'cost_center_id': self.picking_id.cost_center_id.id
            })
            new_account_move.post()

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    cost_center_id = fields.Many2one("cost.center", string="Centro de Costo")

    def button_validate(self):
        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if not all(cost.picking_ids for cost in self):
            raise UserError(_('Please define the transfers on which those additional costs should apply.'))
        cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
        if cost_without_adjusment_lines:
            cost_without_adjusment_lines.compute_landed_cost()
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
                'move_type': 'entry',
                'cost_center_id': cost.cost_center_id.id
            }
            valuation_layer_ids = []
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                # Prorate the value at what's still in stock
                cost_to_add = (remaining_qty / line.move_id.product_qty) * line.additional_landed_cost
                if not cost.company_id.currency_id.is_zero(cost_to_add):
                    valuation_layer = self.env['stock.valuation.layer'].create({
                        'value': cost_to_add,
                        'unit_cost': 0,
                        'quantity': 0,
                        'remaining_qty': 0,
                        'stock_valuation_layer_id': linked_layer.id,
                        'description': cost.name,
                        'stock_move_id': line.move_id.id,
                        'product_id': line.move_id.product_id.id,
                        'stock_landed_cost_id': cost.id,
                        'company_id': cost.company_id.id,
                    })
                    linked_layer.remaining_value += cost_to_add
                    valuation_layer_ids.append(valuation_layer.id)
                # Update the AVCO
                product = line.move_id.product_id
                if product.cost_method == 'average' and not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                    product.with_context(force_company=self.company_id.id).sudo().standard_price += cost_to_add / product.quantity_svl
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move.post()

            if cost.vendor_bill_id and cost.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                all_amls = cost.vendor_bill_id.line_ids | cost.account_move_id.line_ids
                for product in cost.cost_lines.product_id:
                    accounts = product.product_tmpl_id.get_product_accounts()
                    input_account = accounts['stock_input']
                    all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()
        return True
