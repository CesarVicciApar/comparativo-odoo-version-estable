odoo.define('account_cost_center_conciliation.ReconciliationModelInh', function (require) {
    'use strict';

    const BasicModel = require('web.BasicModel');
    const field_utils = require('web.field_utils');
    const utils = require('web.utils');
    const session = require('web.session');
    const core = require('web.core');
    const _t = core._t;
    const { StatementModel } = require('account.ReconciliationModel')

    StatementModel.include({
        quickCreateFields: ['account_id', 'journal_id', 'amount', 'analytic_account_id', 'name', 'tax_ids', 'force_tax_included', 'analytic_tag_ids', 'date', 'to_check', 'cost_center_id'],
        
        _formatToProcessReconciliation: function (line, prop) {
            var amount = -prop.amount;
            if (prop.partial_amount) {
                amount = -prop.partial_amount;
            }
    
            var result = {
                name : prop.name,
                balance : amount,
                analytic_tag_ids: [[6, null, _.pluck(prop.analytic_tag_ids, 'id')]]
            };
            if (!isNaN(prop.id)) {
                result.id = prop.id;
            } else {
                result.account_id = prop.account_id.id;
                if (prop.journal_id) {
                    result.journal_id = prop.journal_id.id;
                }
            }

            if (prop.analytic_account_id) result.analytic_account_id = prop.analytic_account_id.id;
            if (prop.cost_center_id) result.cost_center_id = prop.cost_center_id.id;
            if (prop.tax_ids && prop.tax_ids.length) result.tax_ids = [[6, null, _.pluck(prop.tax_ids, 'id')]];
            if (prop.tax_tag_ids && prop.tax_tag_ids.length) result.tax_tag_ids = [[6, null, _.pluck(prop.tax_tag_ids, 'id')]];
            if (prop.tax_repartition_line_id) result.tax_repartition_line_id = prop.tax_repartition_line_id;
            if (prop.tax_base_amount) result.tax_base_amount = prop.tax_base_amount;
            if (prop.reconcile_model_id) result.reconcile_model_id = prop.reconcile_model_id
            if (prop.currency_id) result.currency_id = prop.currency_id;
            return result;
        },
        updateProposition: function (handle, values) {
            
            var self = this;
            var line = this.getLine(handle);
            var prop = _.last(_.filter(line.reconciliation_proposition, '__focus'));
            if ('to_check' in values && values.to_check === false) {
                // check if we have another line with to_check and if yes don't change value of this proposition
                prop.to_check = line.reconciliation_proposition.some(function(rec_prop, index) {
                    return rec_prop.id !== prop.id && rec_prop.to_check;
                });
            }
            if (!prop) {
                prop = this._formatQuickCreate(line);
                line.reconciliation_proposition.push(prop);
            }
            _.each(values, function (value, fieldName) {
                if (fieldName === 'analytic_tag_ids') {
                    switch (value.operation) {
                        case "ADD_M2M":
                            // handle analytic_tag selection via drop down (single dict) and
                            // full widget (array of dict)
                            var vids = _.isArray(value.ids) ? value.ids : [value.ids];
                            _.each(vids, function (val) {
                                if (!_.findWhere(prop.analytic_tag_ids, {id: val.id})) {
                                    prop.analytic_tag_ids.push(val);
                                }
                            });
                            break;
                        case "FORGET":
                            var id = self.localData[value.ids[0]].ref;
                            prop.analytic_tag_ids = _.filter(prop.analytic_tag_ids, function (val) {
                                return val.id !== id;
                            });
                            break;
                    }
                }
                else if (fieldName === 'tax_ids') {
                    switch(value.operation) {
                        case "ADD_M2M":
                            prop.__tax_to_recompute = true;
                            var vids = _.isArray(value.ids) ? value.ids : [value.ids];
                            _.each(vids, function(val){
                                if (!_.findWhere(prop.tax_ids, {id: val.id})) {
                                    value.ids.price_include = self.taxes[val.id] ? self.taxes[val.id].price_include : false;
                                    prop.tax_ids.push(val);
                                }
                            });
                            break;
                        case "FORGET":
                            prop.__tax_to_recompute = true;
                            var id = self.localData[value.ids[0]].ref;
                            prop.tax_ids = _.filter(prop.tax_ids, function (val) {
                                return val.id !== id;
                            });
                            // Remove all tax tags, they will be recomputed in case of remaining taxes
                            prop.tax_tag_ids = [];
                            break;
                    }
                }
                else {
                    prop[fieldName] = values[fieldName];
                }
            });
            if ('account_id' in values) {
                prop.account_code = prop.account_id ? this.accounts[prop.account_id.id] : '';
            }
            if ('amount' in values) {
                prop.base_amount = values.amount;
            }
            if ('cost_center_id' in values) {
                prop.cost_center_id = values.cost_center_id;
            }
            if ('name' in values || 'force_tax_included' in values || 'amount' in values || 'account_id' in values || 'analytic_account_id' in values || 'analytic_tag_ids' in values) {
                prop.__tax_to_recompute = true;
            }
            line.createForm = _.pick(prop, this.quickCreateFields);
            // If you check/uncheck the force_tax_included box, reset the createForm amount.
            if(prop.base_amount)
                line.createForm.amount = prop.base_amount;
            if (!prop.tax_ids || prop.tax_ids.length !== 1 ) {
                // When we have 0 or more than 1 taxes, reset the base_amount and force_tax_included, otherwise weird behavior can happen
                prop.amount = prop.base_amount;
                line.createForm.force_tax_included = false;
            }
            return this._computeLine(line);
        },
        _formatQuickCreate: function (line, values) {
            values = values || {};
            var today = new moment().utc().format();
            var account = this._formatNameGet(values.account_id);
            var formatOptions = {
                currency_id: line.st_line.currency_id,
            };
            var amount = values.amount !== undefined ? values.amount : line.balance.amount;
    
            var prop = {
                'id': _.uniqueId('createLine'),
                'name': values.name || line.st_line.name,
                'account_id': account,
                'account_code': account ? this.accounts[account.id] : '',
                'analytic_account_id': this._formatNameGet(values.analytic_account_id),
                'analytic_tag_ids': values.analytic_tag_ids || [],
                'journal_id': this._formatNameGet(values.journal_id),
                'tax_ids': this._formatMany2ManyTagsTax(values.tax_ids || []),
                'tax_tag_ids': this._formatMany2ManyTagsTax(values.tax_tag_ids || []),
                'tax_repartition_line_id': values.tax_repartition_line_id,
                'tax_base_amount': values.tax_base_amount,
                'debit': 0,
                'credit': 0,
                'cost_center_id': false,
                'date': values.date ? values.date : field_utils.parse.date(today, {}, {isUTC: true}),
                'force_tax_included': values.force_tax_included || false,
                'base_amount': amount,
                'link': values.link,
                'display': true,
                'invalid': true,
                'to_check': !!values.to_check,
                '__tax_to_recompute': true,
                '__focus': '__focus' in values ? values.__focus : true,
            };
            if (prop.base_amount) {
                // Call to format and parse needed to round the value to the currency precision
                var sign = prop.base_amount < 0 ? -1 : 1;
                var amount = _.unescape(field_utils.format.monetary(Math.abs(prop.base_amount), {}, formatOptions));
                prop.base_amount = sign * field_utils.parse.monetary(amount, {}, formatOptions);
            }
    
            prop.amount = prop.base_amount;
            return prop;
        },
        validate: function (handle) {
            debugger
            var self = this;
            this.display_context = 'validate';
            var handles = [];
            if (handle) {
                handles = [handle];
            } else {
                _.each(this.lines, function (line, handle) {
                    if (!line.reconciled && line.balance && !line.balance.amount && line.reconciliation_proposition.length) {
                        handles.push(handle);
                    }
                });
            }
            var ids = [];
            var values = [];
            var handlesPromises = [];
            _.each(handles, function (handle) {
                debugger
                var line = self.getLine(handle);
                var props = _.filter(line.reconciliation_proposition, function (prop) {return prop && !prop.invalid;});
                var computeLinePromise;
                if (props.length === 0) {
                    // Usability: if user has not chosen any lines and click validate, it has the same behavior
                    // as creating a write-off of the same amount.
                    props.push(self._formatQuickCreate(line, {
                        account_id: [line.st_line.open_balance_account_id, self.accounts[line.st_line.open_balance_account_id]],
                    }));
                    // update balance of line otherwise it won't be to zero and another line will be added
                    line.reconciliation_proposition.push(props[0]);
                    computeLinePromise = self._computeLine(line);
                }
                ids.push(line.id);
                handlesPromises.push(Promise.resolve(computeLinePromise).then(function() {
                    var move_line_values = _.map(_.filter(props, function (prop) {
                        return !isNaN(prop.id) && !prop.is_liquidity_line;
                    }), self._formatToProcessReconciliation.bind(self, line));
                    move_line_values.push(..._.map(_.filter(props, function (prop) {
                        debugger
                        return !isNaN(prop.id) && prop.is_liquidity_line;
                    }), self._formatToProcessReconciliation.bind(self, line)))
                    move_line_values.push(..._.map(_.filter(props, function (prop) {
                        debugger
                        return isNaN(prop.id) && prop.display;
                    }), self._formatToProcessReconciliation.bind(self, line)))
                    values.push({
                        partner_id: line.st_line.partner_id,
                        lines_vals_list: move_line_values,
                        to_check: line.to_check,
                    });
                    line.reconciled = true;
                    self.valuenow++;
                }));
    
                _.each(self.lines, function(other_line) {
                    if (other_line != line) {
                        var filtered_prop = other_line.reconciliation_proposition.filter(p => !line.reconciliation_proposition.map(l => l.id).includes(p.id));
                        if (filtered_prop.length != other_line.reconciliation_proposition.length) {
                            other_line.need_update = true;
                            other_line.reconciliation_proposition = filtered_prop;
                        }
                        self._computeLine(line);
                    }
                })
            });
    
            return Promise.all(handlesPromises).then(function() {
                return self._rpc({
                        model: 'account.reconciliation.widget',
                        method: 'process_bank_statement_line',
                        args: [ids, values],
                        context: self.context,
                    })
                    .then(self._validatePostProcess.bind(self))
                    .then(function () {
                        return {handles: handles};
                    });
            });
        },
    })
})