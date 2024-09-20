# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
import base64
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        AccountMoveLine = self.env['account.move.line']
        excluded_move_ids = []

        if self._context.get('suspense_moves_mode'):
            excluded_move_ids = AccountMoveLine.search(
                AccountMoveLine._get_suspense_moves_domain() + [('move_id', 'in', self.ids)]).mapped('move_id').ids

        for move in self:
            if move in move.line_ids.mapped('full_reconcile_id.exchange_move_id'):
                raise UserError(_('You cannot reset to draft an exchange difference journal entry.'))
            if move.tax_cash_basis_rec_id or move.tax_cash_basis_origin_move_id:
                # If the reconciliation was undone, move.tax_cash_basis_rec_id will be empty;
                # but we still don't want to allow setting the caba entry to draft
                # (it'll have been reversed automatically, so no manual intervention is required),
                # so we also check tax_cash_basis_origin_move_id, which stays unchanged
                # (we need both, as tax_cash_basis_origin_move_id did not exist in older versions).
                raise UserError(_('You cannot reset to draft a tax cash basis journal entry.'))
            if move.restrict_mode_hash_table and move.state == 'posted' and move.id not in excluded_move_ids:
                raise UserError(_('You cannot modify a posted entry of this journal because it is in strict mode.'))
            # We remove all the analytics entries for this journal
            move.mapped('line_ids.analytic_line_ids').unlink()
            move.mapped('line_ids.analytic_line_two_ids').unlink()
            move.mapped('line_ids.analytic_line_three_ids').unlink()
            move.mapped('line_ids.analytic_line_four_ids').unlink()

        self.mapped('line_ids').remove_move_reconcile()
        self.write({'state': 'draft', 'is_move_sent': False})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_line_two_ids = fields.One2many('account.analytic.line.two', 'move_id', string='Analytic lines 2')
    analytic_account_two_id = fields.Many2one('account.analytic.account.two', string='Analytic Account 2', index=True,
                                              compute="_compute_analytic_account_two_id", store=True,
                                              readonly=False, check_company=True, copy=True)
    analytic_tag_two_ids = fields.Many2many('account.analytic.tag.two', string='Analytic Tags 2',
                                            compute="_compute_analytic_tag_two_ids", store=True,
                                            readonly=False, check_company=True, copy=True)

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_account_two_id(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default.two'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec:
                    record.analytic_account_id = rec.analytic_id

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_tag_two_ids(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default.two'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec:
                    record.analytic_tag_ids = rec.analytic_tag_ids

    analytic_line_three_ids = fields.One2many('account.analytic.line.three', 'move_id', string='Analytic lines 3')
    analytic_account_three_id = fields.Many2one('account.analytic.account.three', string='Analytic Account 3',
                                                index=True,
                                                readonly=False, check_company=True, copy=True)
    analytic_tag_three_ids = fields.Many2many('account.analytic.tag.three', string='Analytic Tags 3',
                                              readonly=False, check_company=True, copy=True)

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_account_three_id(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default.two'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec:
                    record.analytic_account_id = rec.analytic_id

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_tag_three_ids(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default.three'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec:
                    record.analytic_tag_three_ids = rec.analytic_tag_three_ids

    analytic_line_four_ids = fields.One2many('account.analytic.line.four', 'move_id', string='Analytic lines 4')
    analytic_account_four_id = fields.Many2one('account.analytic.account.four', string='Analytic Account 4', index=True,
                                               store=True,
                                               readonly=False, check_company=True, copy=True)
    analytic_tag_four_ids = fields.Many2many('account.analytic.tag.four', string='Analytic Tags 4', store=True,
                                             readonly=False, check_company=True, copy=True)

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_account_four_id(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default.four'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec:
                    record.analytic_account_id = rec.analytic_id

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_tag_four_ids(self):
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default.four'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id
                )
                if rec:
                    record.analytic_tag_ids = rec.analytic_tag_ids

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.is_line_xml:
            self.account_id = self._get_computed_account()
            analytics_accounts = self.product_id._get_product_analytic_accounts()
            if self.move_id.is_purchase_document(include_receipts=True):
                analytics = analytics_accounts['expense']
            else:
                analytics = analytics_accounts['income']
            self.analytic_account_id = analytics[0]
            self.analytic_account_two_id = analytics[1]
            self.analytic_account_three_id = analytics[2]
            self.analytic_account_four_id = analytics[3]
        else:
            res = super(AccountMoveLine, self)._onchange_product_id()
            analytics_accounts = self.product_id._get_product_analytic_accounts()
            if self.move_id.is_purchase_document(include_receipts=True):
                analytics = analytics_accounts['expense']
            else:
                analytics = analytics_accounts['income']
            self.analytic_account_id = analytics[0]
            self.analytic_account_two_id = analytics[1]
            self.analytic_account_three_id = analytics[2]
            self.analytic_account_four_id = analytics[3]
            return res

    @api.model_create_multi
    def create(self, vals_list):
        if not 'sale_import' in self.env.context:
           
            for vals in vals_list:
                if vals.get('analytic_account_id') and vals.get('analytic_tag_ids') is not None and vals.get('analytic_tag_ids')[0][2] != []:
                    raise UserError(
                        _('No se puede cargar la cuenta analitica y la etiqueta analitica 1.'))
                if vals.get('analytic_account_two_id') and vals.get('analytic_tag_ids') is not None and vals.get('analytic_tag_two_ids')[0][2] != []:
                    raise UserError(
                        _('No se puede cargar la cuenta analitica y la etiqueta analitica 2.'))
                if vals.get('analytic_account_three_id') and vals.get('analytic_tag_ids') is not None and vals.get('analytic_tag_three_ids')[0][2] != []:
                    raise UserError(
                        _('No se puede cargar la cuenta analitica y la etiqueta analitica 3.'))
                if vals.get('analytic_account_four_id') and vals.get('analytic_tag_ids') is not None and vals.get('analytic_tag_four_ids')[0][2] != []:
                    raise UserError(
                        _('No se puede cargar la cuenta analitica y la etiqueta analitica 4.'))
        return super(AccountMoveLine, self).create(vals_list)

    def create_analytic_lines(self):
        """ Create analytic items upon validation of an account.move.line having an analytic account or an analytic distribution.
        """
        lines_to_create_analytic_entries = self.env['account.move.line']
        lines_to_create_analytic_entries_two = self.env['account.move.line']
        lines_to_create_analytic_entries_three = self.env['account.move.line']
        lines_to_create_analytic_entries_four = self.env['account.move.line']
        analytic_line_vals = []
        analytic_line_two_vals = []
        analytic_line_three_vals = []
        analytic_line_four_vals = []

        for obj_line in self:
            analytic_tags = obj_line._get_analytic_tag_ids_active_distribution(obj_line)
            analytic_two_tags = obj_line._get_analytic_tag_two_ids_active_distribution(obj_line)
            analytic_three_tags = obj_line._get_analytic_tag_three_ids_active_distribution(obj_line)
            analytic_four_tags = obj_line._get_analytic_tag_four_ids_active_distribution(obj_line)
            if analytic_tags:
                for tag in analytic_tags:
                    for distribution in tag.analytic_distribution_ids:
                        analytic_line_vals.append(obj_line._prepare_analytic_distribution_line(distribution))
            if analytic_two_tags:
                for tag in analytic_two_tags:
                    for distribution in tag.analytic_distribution_ids:
                        analytic_line_two_vals.append(obj_line._prepare_analytic_distribution_line(distribution))
            if analytic_three_tags:
                for tag in analytic_three_tags:
                    for distribution in tag.analytic_distribution_ids:
                        analytic_line_three_vals.append(obj_line._prepare_analytic_distribution_line(distribution))
            if analytic_four_tags:
                for tag in analytic_four_tags:
                    for distribution in tag.analytic_distribution_ids:
                        analytic_line_four_vals.append(obj_line._prepare_analytic_distribution_line(distribution))

            if obj_line.analytic_account_id:
                lines_to_create_analytic_entries |= obj_line
            if obj_line.analytic_account_two_id:
                lines_to_create_analytic_entries_two |= obj_line
            if obj_line.analytic_account_three_id:
                lines_to_create_analytic_entries_three |= obj_line
            if obj_line.analytic_account_four_id:
                lines_to_create_analytic_entries_four |= obj_line

        if lines_to_create_analytic_entries:
            analytic_line = 'analytic_line'
            analytic_line_vals += lines_to_create_analytic_entries._prepare_analytic_line(analytic_line)
        if lines_to_create_analytic_entries_two:
            analytic_line = 'analytic_line_two'
            analytic_line_two_vals += lines_to_create_analytic_entries_two._prepare_analytic_line(analytic_line)
        if lines_to_create_analytic_entries_three:
            analytic_line = 'analytic_line_three'
            analytic_line_three_vals += lines_to_create_analytic_entries_three._prepare_analytic_line(analytic_line)
        if lines_to_create_analytic_entries_four:
            analytic_line = 'analytic_line_four'
            analytic_line_four_vals += lines_to_create_analytic_entries_four._prepare_analytic_line(analytic_line)

        if analytic_line_vals:
            self.env['account.analytic.line'].create(analytic_line_vals)
        if analytic_line_two_vals:
            self.env['account.analytic.line.two'].create(analytic_line_two_vals)
        if analytic_line_three_vals:
            self.env['account.analytic.line.three'].create(analytic_line_three_vals)
        if analytic_line_four_vals:
            self.env['account.analytic.line.four'].create(analytic_line_four_vals)

    def _prepare_analytic_line(self, analytic_line):
        """ Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
            an analytic account. This method is intended to be extended in other modules.
            :return list of values to create analytic.line
            :rtype list
        """
        result = []
        for move_line in self:
            amount = (move_line.credit or 0.0) - (move_line.debit or 0.0)
            default_name = move_line.name or (
                    move_line.ref or '/' + ' -- ' + (move_line.partner_id and move_line.partner_id.name or '/'))
            category = 'other'
            if move_line.move_id.is_sale_document():
                category = 'invoice'
            elif move_line.move_id.is_purchase_document():
                category = 'vendor_bill'
            result.append({
                'name': default_name,
                'date': move_line.date,
                'account_id': move_line._get_account_id(move_line, analytic_line),
                'group_id': move_line._get_group_id(move_line, analytic_line),
                'tag_ids': [(6, 0, move_line._get_analytic_tag_ids())],
                'unit_amount': move_line.quantity,
                'product_id': move_line.product_id and move_line.product_id.id or False,
                'product_uom_id': move_line.product_uom_id and move_line.product_uom_id.id or False,
                'amount': amount,
                'general_account_id': move_line.account_id.id,
                'ref': move_line.ref,
                'move_id': move_line.id,
                'user_id': move_line.move_id.invoice_user_id.id or self._uid,
                'partner_id': move_line.partner_id.id,
                'company_id': move_line._get_company_from_analytic_account(
                    move_line, analytic_line) or move_line.move_id.company_id.id,
                'category': category,
            })
        return result

    def _get_analytic_tag_ids_active_distribution(self, obj_line):
        if obj_line.analytic_tag_ids:
            return obj_line.analytic_tag_ids.filtered('active_analytic_distribution')

    def _get_analytic_tag_two_ids_active_distribution(self, obj_line):
        if obj_line.analytic_tag_two_ids:
            return self.analytic_tag_two_ids.filtered('active_analytic_distribution')

    def _get_analytic_tag_three_ids_active_distribution(self, obj_line):
        if obj_line.analytic_tag_three_ids:
            return self.analytic_tag_three_ids.filtered('active_analytic_distribution')

    def _get_analytic_tag_four_ids_active_distribution(self, obj_line):
        if obj_line.analytic_tag_four_ids:
            return self.analytic_tag_four_ids.filtered('active_analytic_distribution')

    def _get_analytic_tag_ids(self):
        if self.analytic_tag_ids:
            return self.analytic_tag_ids.filtered(lambda r: not r.active_analytic_distribution).ids
        elif self.analytic_tag_two_ids:
            return self.analytic_tag_two_ids.filtered(lambda r: not r.active_analytic_distribution).ids
        elif self.analytic_tag_three_ids:
            return self.analytic_tag_three_ids.filtered(lambda r: not r.active_analytic_distribution).ids
        elif self.analytic_tag_four_ids:
            return self.analytic_tag_four_ids.filtered(lambda r: not r.active_analytic_distribution).ids
        else:
            return []

    def _get_account_id(self, move_line, analytic_line):
        if move_line.analytic_account_id and analytic_line == 'analytic_line':
            return move_line.analytic_account_id.id
        elif move_line.analytic_account_two_id and analytic_line == 'analytic_line_two':
            return move_line.analytic_account_two_id.id
        elif move_line.analytic_account_three_id and analytic_line == 'analytic_line_three':
            return move_line.analytic_account_three_id.id
        elif move_line.analytic_account_four_id and analytic_line == 'analytic_line_four':
            return move_line.analytic_account_four_id.id

    def _get_group_id(self, move_line, analytic_line):
        if move_line.analytic_account_id.group_id and analytic_line == 'analytic_line':
            return move_line.analytic_account_id.group_id.id
        elif move_line.analytic_account_two_id.group_id and analytic_line == 'analytic_line_two':
            return move_line.analytic_account_two_id.group_id.id
        elif move_line.analytic_account_three_id.group_id and analytic_line == 'analytic_line_three':
            return move_line.analytic_account_three_id.group_id.id
        elif move_line.analytic_account_four_id.group_id and analytic_line == 'analytic_line_four':
            return move_line.analytic_account_four_id.group_id.id

    def _get_company_from_analytic_account(self, move_line, analytic_line):
        if move_line.analytic_account_id.company_id and analytic_line == 'analytic_line':
            return move_line.analytic_account_id.company_id.id
        elif move_line.analytic_account_two_id.company_id and analytic_line == 'analytic_line_two':
            return move_line.analytic_account_two_id.company_id.id
        elif move_line.analytic_account_three_id.company_id and analytic_line == 'analytic_line_three':
            return move_line.analytic_account_three_id.company_id.id
        elif move_line.analytic_account_four_id.company_id and analytic_line == 'analytic_line_four':
            return move_line.analytic_account_four_id.company_id.id
