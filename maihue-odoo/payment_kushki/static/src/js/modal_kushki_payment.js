odoo.define('payment_kushki.modal_kushki_payment', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

     publicWidget.registry.modalKsuhkiPayment = publicWidget.Widget.extend({
        selector: '.open_modal_ck',
        events: {
            'click .open_ck': '_openFormKushki',
        },

        _getValuesFieldsForm: function(form){
            var values = {}
            $.each($('#' + form).serializeArray(), function(i, field) {
                values[field.name] = field.value;
            });
            return values;
        },

        _openFormKushki: function(){
            var values = this._getValuesFieldsForm('open_ck_form')

            $("#codigo").attr("value", "+56");
            $("#codigo_webpay").attr("value", "+56");
            $("#subscribe").prop('disabled', true);
            $('#subscribe_debit_card').attr("disabled", true);


            if (values['contractTypes'] == 'all') {
                $('#cajita_kushki').modal('show');
                $('#modalmethodpayment').css("display", "block");
                $('#modalmethodpaymentcredit').css("display", "none");
                $('#modalmethodpaymentdebit').css("display", "none");
                $('#changepayment').css("display", "block");
                $('#changepayment1').css("display", "block");
            }
            if (values['contractTypes'] == 'credit') {
                $('#cajita_kushki').modal('show');
                $('#modalmethodpayment').css("display", "none");
                $('#modalmethodpaymentcredit').css("display", "block");
                $('#changepayment').css("display", "none");
            }
        },
    });

    publicWidget.registry.updateKsuhkiPayment = publicWidget.Widget.extend({
        selector: '.update_suscription',
        events: {
            'click .to_update': '_openFormKushki',
        },

        _getValuesFieldsForm: function(form){
            var values = {}
            $.each($('#' + form).serializeArray(), function(i, field) {
                values[field.name] = field.value;
            });
            return values;
        },

        _openFormKushki: function(){
            debugger;
            var values = this._getValuesFieldsForm('open_ck_form')
            console.log(values);
            var $typeSubscriptionContract = this.$('input[name=type_subscription_contract]');
            var $subscription = this.$('input[name=subscription]');

            $("#subscribe").prop('disabled', true);
            $('#subscribe_debit_card').attr("disabled", true);

            var typeSubscriptionContract = ($typeSubscriptionContract.val() || '')
            var subscription = ($subscription.val() || '')

            if (typeSubscriptionContract == 'PAT'){
                $('#subscriptionToken').val(subscription)
                $('#cajita_kushki').modal('show');
                $('#modalmethodpayment').css("display", "none");
                $('#modalmethodpaymentdebit').css("display", "none");
                $('#modalmethodpaymentcredit').css("display", "block");
                $('#changepayment').css("display", "none");
            }
            if (typeSubscriptionContract == 'PAC'){
                $('#webpaySubsctiptionToken').val(subscription)
                $('#cajita_kushki').modal('show');
                $('#modalmethodpayment').css("display", "none");
                $('#modalmethodpaymentcredit').css("display", "none");
                $('#modalmethodpaymentdebit').css("display", "block");
                $('#changepayment1').css("display", "none");
            }
        },
    });
});