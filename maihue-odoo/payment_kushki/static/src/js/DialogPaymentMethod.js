odoo.define("payment_kushki.DialogPaymentMethod", (require) => {
    "use strict";

    const Dialog = require("web.Dialog");
    const config = require("web.config");
    var core = require("web.core");
    var _t = core._t;

    const DialogPaymentMethod = Dialog.extend({
        template: "payment_kushki.dialogpaymentmethod",
        xmlDependencies: Dialog.prototype.xmlDependencies.concat(["/payment_kushki/static/src/xml/dialog_payment_method.xml"]),
        events: {
            "change .form-control[name='name']": "_onChangeName",
            "change .form-control[name='email']": "_onChangeEmail",
            "change .form-control[name='vat']": "_onChangeVat",
            "change .form-control[name='phone']": "_onChangePhone",
        },
        init: function (parent, options) {
            options.size = options.size || "medium";
            options.buttons = options.buttons;
            options.mode = options.mode || "not_edit";
            options.payment = options.payment;
            options.title = options.title;
            this.size = options.size;
            this.buttons = options.buttons;
            this.payment = options.payment;
            this.title = options.title;
            this.mode = options.mode;
            this.error_message = {
                name: '',
                vat: '',
                phone: '',
                email: ''
            }
            return this._super(parent, options);
        },
        start: function () {
            this._super.apply(this, arguments);
        },
        open: function () {
            this._super(...arguments);
        },
        close: function () {
            this._super.apply(this, arguments);
        },
        _check_field_value: function ($target) {
            let partner = this.payment.partner;
            if ($target.name === "name") {
                let { value } = $target;
                if (value === "") {
                    this.error_message.name = "El siguiente campo es requerido";
                    partner.name = value; 
                } else {
                    this.error_message.name = "";
                    partner.name = value; 
                }
            }
            
            if ($target.name === "email") {
                let { value } = $target;
                if (value === "") {
                    this.error_message.email = "El siguiente campo es requerido";
                    partner.email = value;
                } else {
                    this.error_message.email = "";
                    partner.email = value;
                }
            }

            if ($target.name === "vat") {
                let { value } = $target;
                if (value === "") {
                    this.error_message.vat = "El siguiente campo es requerido";
                    partner.vat = value;
                } else {
                    this.error_message.vat = "";
                    partner.vat = value;
                }
            }

            if ($target.name === "phone") {
                let { value } = $target;
                if (value === "") {
                    this.error_message.phone = "El siguiente campo es requerido";
                    partner.phone = value;
                } else {
                    this.error_message.phone = "";
                    partner.phone = value;
                }
            }

            this.renderElement();
        },
        _onChangeName: function (ev) {
            const check_fields = this._check_field_value(ev.currentTarget);
        },
        _onChangeEmail: function (ev) {
            const check_fields = this._check_field_value(ev.currentTarget);
        },
        _onChangeVat: function (ev) {
            const check_fields = this._check_field_value(ev.currentTarget);
        },
        _onChangePhone: function (ev) {
            const check_fields = this._check_field_value(ev.currentTarget);
        },
    });

    return DialogPaymentMethod;
});