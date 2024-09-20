odoo.define('payment_kushki.modal_kushki_contract', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

     publicWidget.registry.modalKsuhkiContract = publicWidget.Widget.extend({
        selector: '.modal_kushki_contract',
        events: {
            'click .open_modal_kushki': '_openFormKushki',
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
            var values = this._getValuesFieldsForm('kushki_contract_form')
            var typeMethod = values['typeMethod'];
            var $contractId = this.$('input[name=contractId]');
            var $typeMethod = this.$('input[name=typeMethod]');

            var contractId = ($contractId.val() || '')
            var typeMethod = ($typeMethod.val() || '')
            $("#subscribe").prop('disabled', true);
            $('#subscribe_debit_card').attr("disabled", true);
            if (parseInt(values['payments']) >= 1) {
                $("#selectContractId").val(contractId);
                $("#selectedContract").val(contractId);
                $("#selectedContractType").val(typeMethod);
                if (typeMethod == 'pac'){
                    $('#paymentlist').css("display", "block");
                    $('#paymentlist_pat').css("display", "none");
                }
                if (typeMethod == 'pat'){
                    $('#paymentlist_pat').css("display", "block");
                    $('#paymentlist').css("display", "none");
                }
                $('#cajita_kushki').modal('show');
                $('#modalexistingpayment').css("display", "none");
                $('#modalassociatepayment').css("display", "block");
                $('#changepayment').css("display", "none");
                $('#goBackExisting').css("display", "none");
                $('#modalmethodpayment').css("display", "none");
                $('#modalmethodpaymentdebit').css("display", "none");
                $('#modalmethodpaymentcredit').css("display", "none");
            } else {
                if (typeMethod == 'pac'){
                    $("#webpayContractId").val(contractId);
                    $('#cajita_kushki').modal('show');
                    $('#changepayment').css("display", "none");
                    $('#changepayment1').css("display", "none");
                    $('#goBackExistingCredit').css("display", "none");
                    $('#modalmethodpayment').css("display", "none");
                    $('#modalmethodpaymentdebit').css("display", "block");
                    $('#modalmethodpaymentcredit').css("display", "none");
                }
                if (typeMethod == 'pat'){
                    $("#selectedContract").val(contractId);
                    $('#cajita_kushki').modal('show');
                    $('#modalmethodpayment').css("display", "block");
                    $('#modalmethodpaymentcredit').css("display", "none");
                    $('#modalmethodpaymentdebit').css("display", "none");
                    $('#goBackExistingCredit').css("display", "none");
                    $('#goBackExisting').css("display", "none");
                }
            }
        },
    });
});