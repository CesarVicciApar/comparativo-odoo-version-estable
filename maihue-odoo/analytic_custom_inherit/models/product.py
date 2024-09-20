# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'


    analytic_account_expense_id = fields.Many2one('account.analytic.account', string='Analytic Account Expense', index=True,
                                          readonly=False, check_company=False, copy=True)
    analytic_account_two_expense_id = fields.Many2one('account.analytic.account.two', string='Analytic Account Expense 2', index=True,
                                              readonly=False, check_company=False, copy=True)
    analytic_account_three_expense_id = fields.Many2one('account.analytic.account.three', string='Analytic Account Expense 3',
                                                index=True, readonly=False, check_company=False, copy=True)
    analytic_account_four_expense_id = fields.Many2one('account.analytic.account.four',
                                                       string='Analytic Account Expense 4',
                                                       index=True, readonly=False, check_company=False, copy=True)
    analytic_account_income_id = fields.Many2one('account.analytic.account', string='Analytic Account Income', index=True,
                                          readonly=False, check_company=False, copy=True)
    analytic_account_two_income_id = fields.Many2one('account.analytic.account.two', string='Analytic Account Income 2', index=True,
                                              readonly=False, check_company=False, copy=True)
    analytic_account_three_income_id = fields.Many2one('account.analytic.account.three', string='Analytic Account Income 3',
                                                index=True, readonly=False, check_company=False, copy=True)
    analytic_account_four_income_id = fields.Many2one('account.analytic.account.four',
                                                      string='Analytic Account Income 4',
                                                      index=True, readonly=False, check_company=False, copy=True)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_product_analytic_accounts(self):
        analytics = []
        income = [
            self.analytic_account_income_id,
            self.analytic_account_two_income_id,
            self.analytic_account_three_income_id,
            self.analytic_account_four_income_id,
        ]
        expense = [
            self.analytic_account_expense_id.id,
            self.analytic_account_two_expense_id.id,
            self.analytic_account_three_expense_id.id,
            self.analytic_account_four_expense_id.id,
        ]
        analytics = {'income': income, 'expense': expense}
        return analytics
