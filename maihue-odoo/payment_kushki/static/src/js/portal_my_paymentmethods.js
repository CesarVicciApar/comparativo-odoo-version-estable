odoo.define('payment_kushki.portal_my_paymentmethods', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var session = require('web.session');

    publicWidget.registry.portalMyPaymentMethods = publicWidget.Widget.extend({
        selector: '.modalmethodpayment',
        events: {
            'click .credit': '_openCreditForm',
            'click .webpay': '_openWebpayForm',
        },

        _getValuesFieldsForm: function(form){
            var values = {}
            $.each($('#' + form).serializeArray(), function(i, field) {
                values[field.name] = field.value;
            });
            return values;
        },

        _openCreditForm: function(){
            var values = this._getValuesFieldsForm('modalmethodpayment_form');
            $("#creditPublicMerchant").val(values['selectPublicMerchant']);
            $("#creditPrivateMerchant").val(values['selectPrivateMerchant']);
            $("#creditBaseUrl").val(values['selectBaseUrl']);
            $("#creditContractId").val(values['selectContractId']);

            $('#modalmethodpayment').css("display", "none");
            $('#modalmethodpaymentcredit').css("display", "block");
        },

        _openWebpayForm: function(){
            var values = this._getValuesFieldsForm('modalmethodpayment_form');
            $("#debitBaseUrl").val(values['selectBaseUrl']);
            $("#debitPublicMerchant").val(values['selectPublicMerchant']);
            $("#debitPrivateMerchant").val(values['selectPrivateMerchant']);

            $('#modalmethodpayment').css("display", "none");
            $('#modalmethodpaymentdebit').css("display", "block");
        }
    });

});