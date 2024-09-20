odoo.define('payment_kushki.kushki_contract_webpay', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var session = require('web.session');
    var _t = core._t;

    publicWidget.registry.portalContractWebpayCard = publicWidget.Widget.extend({
        selector: '.contracts_kushki_debit_webpay',
        events: {
            'click .subscribe_debit_card': '_responseDebitCard',
            'click .changepayment1': '_changePaymentMethod',
        },

        _changePaymentMethod: function(){
            $('#modalmethodpaymentdebit').css("display", "none");
            $('#modalmethodpayment').css("display", "block");
        },

        _configObjectKushki: function(){
            var $publicMerchant = this.$('input[name=debitPublicMerchant]');
            var publicKey = ($publicMerchant.val() || '');
            console.log(publicKey);
            const kushki = new Kushki({
                merchantId: publicKey,
                inTestEnvironment: true,
            });
            return kushki
        },

        _responseDebitCard: function(){
        debugger;
            self = this
            var kushki = self._configObjectKushki()

            let $baseUrl = this.$('input[name=debitBaseUrl]');
            let $mail = this.$('input[name=mail]');
            let $debit = this.$('input[name=debit]');
            let $firstname = this.$('input[name=firstname]');
            let $lastname = this.$('input[name=lastname]');
            let $document_number = this.$('input[name=document_number]');
            let $number = this.$('input[name=number]');

            var baseUrl = ($baseUrl.val() || '')
            var mail = ($mail.val() || '')
            var debit = ($debit.val() || '')
            var firstname = ($firstname.val() || '')
            var lastname = ($lastname.val() || '')
            var document_number = ($document_number.val() || '')
            var number = ($number.val() || '')
            var url = baseUrl + '/my/contracts'
            var callback = function(response) {
                if(!response.code){
                    rpc.query({
                        model: 'kushki.log',
                        method: 'create_log_request_token',
                        args: [session.user_id, response, 'requestSubscriptionToken'],
                    }).then(function () {
                        $("#webpaysubsctiptionToken").val(response.token);
                        $("#card_webpay_cajita").submit();
                    });
                }  else {
                    rpc.query({
                        model: 'kushki.log',
                        method: 'create_log_request_token',
                        args: [session.user_id, response, 'requestSubscriptionToken'],
                    }).then(function () {
                        //self.do_warn(_t("Error"), _t(response.message));
                        console.log(_t("Error"), _t(response.message));
                        console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                    });
                }
            }
            kushki.requestSubscriptionCardAsyncToken({
                currency: "CLP",
                email: mail,
                callbackUrl: url,


            }, callback);

        }
    });
});