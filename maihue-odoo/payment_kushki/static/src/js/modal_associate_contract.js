odoo.define('payment_kushki.modal_associate_contract', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    publicWidget.registry.modalAssociateContract = publicWidget.Widget.extend({
        selector: '.form_select_contract_associate',
        events: {
            'click .associate_button': '_associateContract',
        },

        _associateContract: function(){
            var $subscriptionId = this.$('input[name=selectedSubscription]');
            var $contractId = this.$('select[name=contractList]');

            var subscriptionId = ($subscriptionId.val() || '')
            var contractId = ($contractId.val())
            if (subscriptionId != '' && contractId != ''){
                $("#form_list_contract").attr('action', '/associate').submit();
            }else{
                console.log(_t("Campos requeridos"), _t("Debe seleccionar un contrato de la lista"));
                //this.do_warn(_t("Campos requeridos"), _t("Debe seleccionar un contrato de la lista"));
            }
        },
    });
});