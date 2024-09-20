odoo.define('payment_kushki.modal_list_contract', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;

    publicWidget.registry.modalListContract = publicWidget.Widget.extend({
        selector: '.open_modal_list_contract',
        events: {
            'click .associate': '_openListContract',
        },

        _openListContract: function(){

            var $subscriptionId = this.$('input[name=subscriptionContract]');
            var subscriptionId = ($subscriptionId.val() || '')
            $("#selectedSubscription").val(subscriptionId);

            $('#list_contract').modal('show');
        },
    });
});