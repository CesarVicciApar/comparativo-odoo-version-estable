odoo.define('account_cost_center_conciliation.reconciliation_renderer_inh', function (require) {
    'use strict';

    // const Widget = require('web.Widget');
    const FieldManagerMixin = require('web.FieldManagerMixin');
    const relational_fields = require('web.relational_fields');
    const basic_fields = require('web.basic_fields');
    const core = require('web.core');
    const qweb = core.qweb;
    const _t = core._t;
    const { LineRenderer } = require('account.ReconciliationRenderer');

    LineRenderer.include({
        init: function (parent, model, state) {
            this._super(parent);
            FieldManagerMixin.init.call(this);

            this.model = model;
            this._initialState = state;
            // let form_fields = this._renderCreate(state);
        },
        _renderCreate: function (state) {
            var self = this;
            return this.model.makeRecord('account.bank.statement.line', [{
                relation: 'account.account',
                type: 'many2one',
                name: 'account_id',
                domain: [['company_id', '=', state.st_line.company_id], ['deprecated', '=', false]],
            }, {
                relation: 'account.journal',
                type: 'many2one',
                name: 'journal_id',
                domain: [['company_id', '=', state.st_line.company_id], ['type', '=', 'general']],
            }, {
                relation: 'account.tax',
                type: 'many2many',
                name: 'tax_ids',
                domain: [['company_id', '=', state.st_line.company_id]],
            }, {
                relation: 'account.analytic.account',
                type: 'many2one',
                name: 'analytic_account_id',
                domain: ["|", ['company_id', '=', state.st_line.company_id], ['company_id', '=', false]],
            }, {
                relation: 'cost.center',
                type: 'many2one',
                name: 'cost_center_id',
                // domain: [['company_id', '=', false]]
            }, {
                relation: 'account.analytic.tag',
                type: 'many2many',
                name: 'analytic_tag_ids',
                domain: ["|", ['company_id', '=', state.st_line.company_id], ['company_id', '=', false]],
            }, {
                type: 'boolean',
                name: 'force_tax_included',
            }, {
                type: 'char',
                name: 'name',
            }, {
                type: 'float',
                name: 'amount',
            }, {
                type: 'date',
                name: 'date',
            }, {
                type: 'boolean',
                name: 'to_check',
            }], {
                account_id: {
                    string: _t("Account"),
                },
                name: {string: _t("Label")},
                amount: {string: _t("Account")},
            }).then(function (recordID) {
                self.handleCreateRecord = recordID;
                var record = self.model.get(self.handleCreateRecord);
    
                self.fields.account_id = new relational_fields.FieldMany2One(self,
                    'account_id', record, {mode: 'edit', attrs: {can_create:false}});
    
                self.fields.journal_id = new relational_fields.FieldMany2One(self,
                    'journal_id', record, {mode: 'edit'});
    
                self.fields.tax_ids = new relational_fields.FieldMany2ManyTags(self,
                    'tax_ids', record, {mode: 'edit', additionalContext: {append_type_to_tax_name: true}});
    
                self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                    'analytic_account_id', record, {mode: 'edit'});
    
                self.fields.analytic_tag_ids = new relational_fields.FieldMany2ManyTags(self,
                    'analytic_tag_ids', record, {mode: 'edit'});
    
                self.fields.force_tax_included = new basic_fields.FieldBoolean(self,
                    'force_tax_included', record, {mode: 'edit'});

                self.fields.cost_center_id = new relational_fields.FieldMany2One(self,
                'cost_center_id', record, { mode: 'edit' , attrs: {can_create:false}});
    
                self.fields.name = new basic_fields.FieldChar(self,
                    'name', record, {mode: 'edit'});
    
                self.fields.amount = new basic_fields.FieldFloat(self,
                    'amount', record, {mode: 'edit'});
    
                self.fields.date = new basic_fields.FieldDate(self,
                    'date', record, {mode: 'edit'});
    
                self.fields.to_check = new basic_fields.FieldBoolean(self,
                    'to_check', record, {mode: 'edit'});
    
                var $create = $(qweb.render("reconciliation.line.create", {'state': state, 'group_tags': self.group_tags, 'group_acc': self.group_acc}));
                self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.account_id));
                self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
                self.fields.tax_ids.appendTo($create.find('.create_tax_id .o_td_field'));
                self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
                self.fields.analytic_tag_ids.appendTo($create.find('.create_analytic_tag_ids .o_td_field'));
                self.fields.force_tax_included.appendTo($create.find('.create_force_tax_included .o_td_field'));
                self.fields.cost_center_id.appendTo($create.find('.create_cost_center_id .o_td_field'));
                self.fields.name.appendTo($create.find('.create_label .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.name));
                self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                    .then(addRequiredStyle.bind(self, self.fields.amount));
                self.fields.date.appendTo($create.find('.create_date .o_td_field'));
                self.fields.to_check.appendTo($create.find('.create_to_check .o_td_field'));
                self.$('.create').append($create);
    
                function addRequiredStyle(widget) {
                    widget.$el.addClass('o_required_modifier');
                }
            });
        },
        // _renderCreate: function (state) {
        //     var self = this;
        //     this.model.makeRecord('account.bank.statement.line', [{
        //         relation: 'cost.center',
        //         type: 'many2one',
        //         name: 'Cost center',
        //         domain: [['code', '=', 'OVIO 020']],

        //     }]).then(function (recordID) {
        //         self.handleCreateRecord = recordID;
        //         var record = self.model.get(self.handleCreateRecord);

        //         self.fields.new_field = new relational_fields.FieldMany2One(self,
        //             'cost_center_id', record, { mode: 'edit' });
                
        //         debugger
        //         var $create = $(qweb.render("reconciliation.line.create", { 'state': state }));
        //         self.fields.withholding_tax_id.appendTo($create.find('.create_cost_center .o_td_field'));
        //         self.$('.create').append($create);

        //         function addRequiredStyle(widget) {
        //             widget.$el.addClass('o_required_modifier');
        //         }
        //     });
        //     this._renderCreate(state) = form_fields;
        // }
    });
    

})