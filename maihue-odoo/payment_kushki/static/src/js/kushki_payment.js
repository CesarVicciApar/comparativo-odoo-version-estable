odoo.define('payment_kushki.kushki_payment', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const session = require('web.session');
    const core = require('web.core');
    const DialogPaymentMethodd = require("payment_kushki.DialogPaymentMethod");
    const Dialog = require("web.Dialog");
    const _t = core._t;

    publicWidget.registry.btnShowDialog = publicWidget.Widget.extend({
        selector: ".oe_card_payment #showDialog",
        events: {
            'click': '_onClick'
        },
        _getValuesRpc: function (data) {
            return {
                model: "payment.method.partner",
                method: "payment_info",
                args: [parseInt(data.id)],
            };
        },
        _onClick: async function (ev)  {
            let data = ev.currentTarget.dataset
            let values = this._getValuesRpc(data);
            const payment = await this._rpc(values);
            let options = {
                payment: payment,
                title: `Tarjeta: ${payment.brand}`,
                size: "medium",
                mode: "not_edit",
                buttons: [
                    { text: _t("Close"), classes: "btn-primary", close: true },
                    {
                        text: _t("Modificar Contratos Asociados"),
                        classes: "btn-primary",
                        click: function (ev) {
                            console.log(ev);
                        },
                    },
                    {
                        text: _t("Editar datos de la Tarjeta"),
                        classes: "btn-primary",
                        click: function (ev) {
                            if (this.mode === "not_edit") {
                                ev.currentTarget.textContent = "Guardar";
                                this.mode = "edit";
                            } else {
                                ev.currentTarget.textContent = "Editar datos de tarjeta";
                                let valuesForm = {
                                    name: this.$(".form-control[name='name']").val(),
                                    vat: this.$(".form-control[name='vat']").val(),
                                    email: this.$(".form-control[name='email']").val(),
                                    phone: this.$(".form-control[name='phone']").val(),
                                };
                                this.mode = "not_edit";
                            }
                            this.renderElement();
                        },
                    },
                    {
                        text: "Dar de Baja",
                        classes: "btn-danger",
                        click: function (ev) {
                            if (!this.payment.contracts) {
                                let isRemovePayment = confirm("¿Está seguro que quiere dar de baja su medio de pago?");
                                if (isRemovePayment) {
                                    this.close()
                                }
                            } else {
                                alert("No es posible dar de baja esta tarjeta ya que tiene contratos vigentes o con pagos pendientes asociados. Para dar de baja la tarjeta debe modificar la tarjeta asociada a dichos contratos")
                            }
                        },
                    },
                ],
            };
            const dialogPaymentMethod = new DialogPaymentMethodd(this, options);
            dialogPaymentMethod.open();
        }
    })

    publicWidget.registry.portalCard = publicWidget.Widget.extend({
        selector: '.form_kushki_payment_card',
        events: {
            'click .credit': '_openCreditForm',
            'click .webpay': '_openWebpayForm',
            'click .changepayment': '_changePaymentMethod',
            'click .changepayment1': '_changePaymentMethodWebpay',
            'click .goBackExisting': '_goBackAssociatePayment',
            'click .goBackModalExisting': '_goBackModalAssociatePayment',
            'click .close': '_onCloseModal',
            'click .associate_new_card_button': '_associateNewPayment',
            'click .select_associate_card_button': '_associateExistingPayment',
            'change .relationship': '_fieldFullValue',
            'change .username': '_fieldFullValue',
            'change .document_number': '_validateDocumentNumber',
            'change .document_number_webpay': '_validateDocumentNumberWebpay',
            'change .card': '_fieldFullValue',
            "change .phone_credit": "_fieldFullValue",
            //'change .typecard': '_fieldFullValue',
            'change .cvc': '_fieldFullValue',
            'change .email': '_fieldFullValue',
            'change .expiry_month': '_fieldFullValue',
            'change .expiry_year': '_fieldFullValue',
            'change .accept_tc': '_fieldFullValue',
            'change .relationshipWebpay': '_fieldFullValueWebpay',
            'change .accept_webpay': '_fieldFullValueWebpay',
            'change .mail': '_fieldFullValueWebpay',
            'change .phone_webpay': '_fieldFullValueWebpay',
            'change .firstname': '_fieldFullValueWebpay',
            'change .lastname': '_fieldFullValueWebpay',
            'change .typecard': '_fieldFullValueWebpay',
            'click .associate_card_button': '_associatePayment',
            'click .subscribe_credit_card': '_responseCreditCard',
            'click .subscribe_debit_card': '_responseDebitCard',
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
            $("#creditContractId").val(values['selectContractId']);

            $('#modalmethodpayment').css("display", "none");
            $('#modalmethodpaymentcredit').css("display", "block");
        },

        _openWebpayForm: function(){
            var values = this._getValuesFieldsForm('modalmethodpayment_form');
            $("#webpayContractId").val(values['selectContractId']);

            $('#modalmethodpayment').css("display", "none");
            $('#modalmethodpaymentdebit').css("display", "block");
        },

        _associateExistingPayment: function(){
            $('#modalexistingpayment').css("display", "block");
            $('#modalassociatepayment').css("display", "none");
            $('#modalmethodpayment').css("display", "none");
            $('#modalmethodpaymentcredit').css("display", "none");
        },

        _associateNewPayment: function(){
            var values = this._getValuesFieldsForm('modal_existing_payment');
            if (values['selectedContractType'] == 'pat') {
                $("#creditContractId").val(values['selectedContract']);
                $('#modalmethodpayment').css("display", "none");
                $('#modalexistingpayment').css("display", "none");
                $('#modalassociatepayment').css("display", "none");
                $('#modalmethodpaymentcredit').css("display", "block");
                $('#modalmethodpaymentdebit').css("display", "none");
                $('#changepayment').css("display", "none");
                $('#changepayment1').css("display", "none");
                $('#goBackExistingCredit').css("display", "block");
            }
            if (values['selectedContractType'] == 'pac') {
                $('#modalmethodpayment').css("display", "block");
                $('#modalexistingpayment').css("display", "none");
                $('#modalassociatepayment').css("display", "none");
                $('#modalmethodpaymentcredit').css("display", "none");
                $('#modalmethodpaymentdebit').css("display", "none");
                $('#changepayment').css("display", "block");
                $('#changepayment1').css("display", "block");
                $('#goBackExisting').css("display", "block");
                $('#goBackExistingCredit').css("display", "none");
            }

        },

        _goBackAssociatePayment: function(){
            $('#modalassociatepayment').css("display", "block");
            $('#modalmethodpayment').css("display", "none");
            $('#modalmethodpaymentcredit').css("display", "none");
        },

        _goBackModalAssociatePayment: function(){
            $('#modalassociatepayment').css("display", "block");
            $('#modalexistingpayment').css("display", "none");
        },

        _validateDocumentNumber: function(ev) {
            var self = this
            var values = this._getValuesFieldsForm('kuski_credit_cajita');
            rpc.query({
                model: 'kushki.log',
                method: 'validate_document_number',
                args: [values['document_number']],
            }).then(function (validate) {
                if(validate){
                    $("input[name=val_document_number]").val("valid");
                    self._fieldFullValue(ev);
                } else {
                    $("input[name=val_document_number]").val("");
                    self._fieldFullValue(ev)
                    //self.do_warn("Error", "RUT invalido");
                    console.log("Error", "RUT invalido");
                }
            });
        },

        _validateDocumentNumberWebpay: function(ev) {
            var self = this
            var values = this._getValuesFieldsForm('kuski_cajita');
            rpc.query({
                model: 'kushki.log',
                method: 'validate_document_number',
                args: [values['document_number_webpay']],
            }).then(function (validate) {
                if(validate){
                    $("input[name=val_document_number_webpay]").val("valid");
                    self._fieldFullValueWebpay(ev);
                } else {
                    $("input[name=val_document_number_webpay]").val("");
                    self._fieldFullValueWebpay(ev)
                    //self.do_warn("Error", "RUT invalido");
                    console.log("Error", "RUT invalido");
                }
            });
        },
        
        _createTextWarning: function ($target,message,card_type) {
            if (card_type === "credit") {
                var $MessageAlert = $(`<small class='form-text text-danger warn-credit' id=${$target.name}>${message}</small>`);
            } else {
                var $MessageAlert = $(`<small class='form-text text-danger warn-webpay' id=${$target.name}>${message}</small>`);
            }
            return $MessageAlert;
        },

        _fieldFullValue: function(ev){
            var values = {};
            var emptyFields = false;
            let { name, value } = ev.currentTarget;
            $.each($('#kuski_credit_cajita').serializeArray(), function(i, field) {
                var fieldAttr = $('#' + field.name).attr('required')
                if ($('#' + field.name).attr('required')){
                    values[field.name] = field.value;
                    if (field.name == 'accept_tc'){
                        if (field.value != "on"){
                            emptyFields = true;
                        }
                    }else{
                        if (field.value == ""){
                            emptyFields = true;
                        }
                    }
                }
            });
            var FieldsCheck = $('#kuski_credit_cajita input[type=checkbox]')
            FieldsCheck.each(function() {
                if (!this.checked) {
                    emptyFields = true;
                }
            });
            
            
            // let $warnings = this.$("small.warn");
            // if (!emptyFields && !$warnings.length >= 1) {
            //     $("#subscribe").prop("disabled", false);
            // } else {
            //     $("#subscribe").prop("disabled", true);
            // }
            

            if (value !== "on") {
                let $targetValues = {[name]: value };
                let valid_data = this._validateFields(name !== "document_number" ? $targetValues : {val_document_number: values.val_document_number }, true);
                if (valid_data instanceof Object) {
                    let $warning = this._createTextWarning(ev.currentTarget, valid_data[`${name}`],'credit');
                    let $message = $(`small[id='${name}']`);
                    if ($message.length === 0) {
                        $warning.insertAfter(ev.currentTarget.parentNode);
                    } else {
                        $message.remove();
                        $warning.insertAfter(ev.currentTarget.parentNode);
                    }
                } else {
                    $(`small[id='${name}']`).remove();
                }

            };


            let $warnings = this.$("small.warn-credit");
            if (!emptyFields && !$warnings.length >= 1) {
                $("#subscribe").prop("disabled", false);
            } else {
                $("#subscribe").prop("disabled", true);
            }
        },

        _fieldFullValueWebpay: function(ev){
            var values = {};
            var emptyFields = false;
            let { name, value } = ev.currentTarget;
            $.each($('#kuski_cajita').serializeArray(), function(i, field) {
                var fieldAttr = $('#' + field.name).attr('required')
                if ($('#' + field.name).attr('required')){
                    values[field.name] = field.value;
                    if (field.name == "accept_webpay") {
                        if (field.value != "on") {
                            emptyFields = true;
                        }
                    } else {
                        if (field.value == "") {
                            emptyFields = true;
                        }
                    }
                }
            });

            var FieldsCheck = $('#kuski_cajita input[type=checkbox]')
            FieldsCheck.each(function() {
                if (!this.checked) {
                    emptyFields = true;
                }
            });
            
            // let $warnings = this.$("small.warn");
            // if (!emptyFields && !$warnings.length >= 1) {
            //     $("#subscribe_debit_card").prop("disabled", false);
            // } else {
            //     $("#subscribe_debit_card").prop("disabled", true);
            // }

            if (value !== "on") {
                let $targetValues = { [name]: value };
                let valid_data = this._validateFieldsWebpay(name !== "document_number_webpay" ? $targetValues : { val_document_number_webpay: values.val_document_number_webpay }, true);
                if (valid_data instanceof Object) {
                    let $warning = this._createTextWarning(ev.currentTarget, valid_data[`${name}`]);
                    let $message = $(`small[id='${name}']`);
                    if ($message.length === 0) {
                        $warning.insertAfter(ev.currentTarget.parentNode);
                    } else {
                        $message.remove();
                        $warning.insertAfter(ev.currentTarget.parentNode);
                    }
                } else {
                    $(`small[id='${name}']`).remove();
                }
            };

            let $warnings = this.$("small.warn-webpay");
            if (!emptyFields && !$warnings.length >= 1) {
                $("#subscribe_debit_card").prop("disabled", false);
            } else {
                $("#subscribe_debit_card").prop("disabled", true);
            }
        },

        _validateUsername: function(value){
            var va = value.split(" ").length == 2
            if(!va){
                $('#username').css('border', '2px solid red');
                return false;
            } else {
                $('#username').css('border', '');
                return true;
            }
        },

        _validateCard: function(value){
            var valoresAceptados = /^[0-9]{16}$/;
            var validity = valoresAceptados.test(parseInt(value))
            if (!validity){
               $('#card').css('border', '2px solid red');
               return false;
            } else {
               $('#card').css('border', '');
               return true;
            }   
        },

        _validateCVC: function(value){
            var valoresAceptados = /^[0-9]{3,4}$/;
            if (!valoresAceptados.test(value)){
               $('#cvc').css('border', '2px solid red');
               return false;
            } else {
               $('#cvc').css('border', '');
               return true;
            }
        },

        _validateEmail: function(value){
            var valoresEmail = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;
            if (!valoresEmail.test(value)){
               $('#email').css('border', '2px solid red');
               return false;
            } else {
               $('#email').css('border', '');
               return true;
            }
        },

        _validateEmailWebpay: function(value){
            var valoresEmail = /^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;
            if (!valoresEmail.test(value)){
               $('#mail').css('border', '2px solid red');
               return false;
            } else {
               $('#mail').css('border', '');
               return true;
            }
        },

        _validateExpiryMonth: function(value){
            var valoresAceptados = /^(?:0?[1-9]|1[0-2])$/;
            value.trim();
            if (!valoresAceptados.test(value) || value.length !== 2) {
                $("#expiry_month").css("border", "2px solid red");
                return false;
            } else {
                $("#expiry_month").css("border", "");
                return true;
            }
        },

        _validateExpiryYear: function(value){
            var valoresAceptados = /^[0-9]{2}$/;
            if(!valoresAceptados.test(value)){
               $('#expiry_year').css('border', '2px solid red');
               return false;
            } else {
               $('#expiry_year').css('border', '');
               return true;
            }
        },

        _validateFirstname: function(value){
            var letters = /^[A-Za-z]+$/;
            if (!letters.test(value)){
                $('#firstname').css('border', '2px solid red');
                return false;
            } else {
                $('#firstname').css('border', '');
                return true;
            }
        },

        _validateLastname: function(value){
            var letters = /^[A-Za-z]+$/;
            if (!letters.test(value)){
                $('#lastname').css('border', '2px solid red');
                return false;
            } else {
                $('#lastname').css('border', '');
                return true;
            }
        },

        _validatePhone: function(value){
            var valoresAceptados = /^[0-9]{9}$/;
            if(!valoresAceptados.test(value)){
                $('#phone_credit').css('border', '2px solid red');
                return false;
            } else {
                $('#phone_credit').css('border', '');
                return true;
            }
        },

        _validatePhoneWebpay: function(value){
            var valoresAceptados = /^[0-9]{9}$/;
            if(!valoresAceptados.test(value)){
                $('#phone_webpay').css('border', '2px solid red');
                return false;
            } else {
                $('#phone_webpay').css('border', '');
                return true;
            }
        },

        _onCloseModal: function(){
            $("#subscriptionToken").val("");
            $("#webpaySubsctiptionToken").val("");
            $("#relationship").val("");
            $("#relationshipWebpay").val("");
            $("#username").val("");
            $("#firstname").val("");
            $("#lastname").val("");
            $("#card").val("");
            $("#expiry_month").val("");
            $("#expiry_year").val("");
            $("#cvc").val("");
            $("#email").val("");
            $("#mail").val("");
            $("#document_number").val("");
            $("#document_number_webpay").val("");
            $("#val_document_number").val("");
            $("#val_document_number_webpay").val("");
            $("#phone_credit").val("");
            $("#phone_webpay").val("");
            $("#typecard").val("");
            $("#accept_tc").prop('checked', false);
            $("#accept_webpay").prop('checked', false);
            this.$(".warn").hide();
        },

        _changePaymentMethod: function(){
            $("#codigo").attr("value", "+56");
            $("#codigo_webpay").attr("value", "+56");
            $('#modalmethodpaymentcredit').css("display", "none");
            $('#modalloader').css("display", "none");
            $('#modalerror').css("display", "none");
            $('#modalmethodpayment').css("display", "block");
        },

        _changePaymentMethodWebpay: function(){
            $("#codigo").attr("value", "+56");
            $("#codigo_webpay").attr("value", "+56");
            $('#modalmethodpaymentdebit').css("display", "none");
            $('#modalloader').css("display", "none");
            $('#modalmethodpayment').css("display", "block");
        },

        _configObjectKushki: function(key){
            console.log(key);
            const kushki = new Kushki({
                merchantId: key,
                inTestEnvironment: true,
            });
            return kushki
        },

        _validateFields: function(values,fieldEspecific=false){
            var self = this;
            let errors = {};
            var error = false;
            var message = "";
            if (!fieldEspecific) {
                if (!self._validateUsername(values["username"])) {
                    message = "Debe ingresar el nombre y el apellido. \n";
                    error = true;
                    errors["username"] = message;
                }
                if (!self._validateCard(values["card"])) {
                    message = "Debe ingresar los 16 valores numéricos de la tarjeta. \n";
                    error = true;
                    errors["card"] = message;
                }
                if (!self._validateExpiryMonth(values["expiry_month"])) {
                    message = "Solo se permite el siguiente rango: 01 - 12. \n";
                    error = true;
                    errors["expiry_month"] = message;
                }
                if (!self._validateExpiryYear(values["expiry_year"])) {
                    message = "Solo se permite el siguiente rango: 01 - 99. \n";
                    error = true;
                    errors["expiry_year"] = message;
                }
                if (!self._validateCVC(values["cvc"])) {
                    message = "El campo csv debe tener solo numeros y un minimo 3 digitos o un maximo de 4 \n";
                    error = true;
                    errors["cvc"] = message;
                }
                if (!self._validateEmail(values["email"])) {
                    message = "La dirección de correo " + "|" + values["email"] + "|" + " es incorrecta. \n";
                    error = true;
                    errors["email"] = message;
                }
                if (!self._validatePhone(values["phone_credit"])) {
                    message = "Debe ingresar los 9 valores numéricos del telefono. \n";
                    error = true;
                    errors["phone_credit"] = message;
                }
                if (values["val_document_number"] != "valid") {
                    message = "RUT invalido \n";
                    error = true;
                    errors["document_number"] = message;
                    $("#document_number").css("border", "2px solid red");
                } else {
                    $("#document_number").css("border", "");
                }
                if (error == false) {
                    return true;
                } else {
                    return errors;
                }
            } else {
                if (values.hasOwnProperty("username")) {
                    if (!self._validateUsername(values["username"])) {
                        message = "Debe ingresar el nombre y el apellido. \n";
                        error = true;
                        errors["username"] = message;
                    }
                } else if (values.hasOwnProperty("card")) {
                    if (!self._validateCard(values["card"])) {
                        message = "Debe ingresar los 16 valores numéricos de la tarjeta. \n";
                        error = true;
                        errors["card"] = message;
                    }
                } else if (values.hasOwnProperty("expiry_month")) {
                    if (!self._validateExpiryMonth(values["expiry_month"])) {
                        message = "Solo se permite el siguiente rango: 01 - 12. \n";
                        error = true;
                        errors["expiry_month"] = message;
                    }
                } else if (values.hasOwnProperty("expiry_year")) {
                    if (!self._validateExpiryYear(values["expiry_year"])) {
                        message = "Solo se permite el siguiente rango: 01 - 99. \n";
                        error = true;
                        errors["expiry_year"] = message;
                    }
                } else if (values.hasOwnProperty("cvc")) {
                    if (!self._validateCVC(values["cvc"])) {
                        message = "El campo cvc debe tener solo numeros y un minimo 3 digitos o un maximo de 4 \n";
                        error = true;
                        errors["cvc"] = message;
                    }
                } else if (values.hasOwnProperty("email")) {
                    if (!self._validateEmail(values["email"])) {
                        message = "La dirección de correo " + "|" + values["email"] + "|" + " es incorrecta. \n";
                        error = true;
                        errors["email"] = message;
                    }
                } else if (values.hasOwnProperty("phone_credit")) {
                    if (!self._validatePhone(values["phone_credit"])) {
                        message = "Debe ingresar los 9 valores numéricos del telefono. \n";
                        error = true;
                        errors["phone_credit"] = message;
                    }
                } else if (values.hasOwnProperty("relationship")) {
                    if (values.relationship === "") {
                        message = "Los datos del Propietario de la Tarjeta son invalidos \n";
                        error = true;
                        errors["relationship"] = message;
                        $("#relationship").css("border", "2px solid red");
                    } else {
                        $("#relationship").css("border", "");
                    }
                } else if (values["val_document_number"] != "valid") {
                    message = "RUT invalido \n";
                    error = true;
                    errors["document_number"] = message;
                    $("#document_number").css("border", "2px solid red");
                } else {
                    $("#document_number").css("border", "");
                }

                if (error == false) {
                    return true;
                } else {
                    return errors;
                }
            }
        },

        _validateFieldsWebpay: function(values,fieldEspecific=false){
            var self = this;
            let errors = new Map();
            var error = false;
            var message = {};
            if (!fieldEspecific) {
                if (!self._validateFirstname(values['firstname'])){
                    message = "Debe ingresar el nombre. \n";
                    error = true;
                    error.set("firstname")
                }
                if (!self._validateLastname(values['lastname'])){
                    message += "Debe ingresar el apellido. \n";
                    error = true;
                }
                if (!self._validateEmailWebpay(values['mail'])){
                    message += "La dirección de correo " + "|" + values['mail'] +"|" + " es incorrecta. \n";
                    error = true;
                }
                if (!self._validatePhoneWebpay(values['phone_webpay'])){
                    message += "Debe ingresar los 9 valores numéricos del telefono. \n";
                    error = true;
                }
                if (values['val_document_number_webpay'] != 'valid') {
                    message += "RUT invalido \n";
                    error = true;
                    $('#document_number_webpay').css('border', '2px solid red');
                } else {
                    $('#document_number_webpay').css('border', '');
                }
                if (error === false) {
                    return true;
                } else {
                    return message;
                }
            } else {
                if (values.hasOwnProperty("firstname")) {
                    if (!self._validateFirstname(values["firstname"])) {
                        message["firstname"] = "Debe ingresar el nombre. \n";
                        error = true;
                        errors.set("firstname");
                    }
                } else if (values.hasOwnProperty("lastname")) {
                    if (!self._validateLastname(values["lastname"])) {
                        error = true;
                        message["lastname"] = "Debe ingresar el apellido. \n";
                    }
                } else if (values.hasOwnProperty("mail")) {
                    if (!self._validateEmailWebpay(values["mail"])) {
                        error = true;
                        message["mail"] = "La dirección de correo " + "|" + values["mail"] + "|" + " es incorrecta. \n";
                    }
                } else if (values.hasOwnProperty("phone_webpay")) {
                    if (!self._validatePhoneWebpay(values["phone_webpay"])) {
                        error = true;
                        message["phone_webpay"] = "Debe ingresar los 9 valores numéricos del telefono. \n";
                    }
                } else if (values.hasOwnProperty("typecard")) {
                    if (values.typecard === "") {
                        error = true;
                        message["typecard"] = "Debe seleccionar el tipo de tarjeta. \n";
                        $("#typecard").css("border", "2px solid red");
                    } else {
                        $("#typecard").css("border", "");
                    }
                }else if (values.hasOwnProperty("relationshipWebpay")) {
                    if (values.relationshipWebpay === "") {
                        message["relationshipWebpay"] = "Los datos del Propietario de la Tarjeta son invalidos \n";
                        error = true;
                        $("#relationshipWebpay").css("border", "2px solid red");
                    } else {
                        $("#relationshipWebpay").css("border", "");
                    }
                } else if (values["val_document_number_webpay"] != "valid") {
                    message["document_number_webpay"] = "RUT invalido \n";
                    error = true;
                    $("#document_number_webpay").css("border", "2px solid red");
                } else {
                    $("#document_number_webpay").css("border", "");
                }
                if (error === false) {
                    return true;
                } else {
                    return message;
                }
            }
        },

        _strDateToday: function(dt){
            var dd = dt.getDate();
            var mm = dt.getMonth() + 1; //January is 0!
            var yyyy = dt.getFullYear();

            if (dd < 10) {
              dd = '0' + dd;
            }

            if (mm < 10) {
              mm = '0' + mm;
            }

            var today = yyyy + '/' + mm + '/' + dd;
            return today;
        },

        _createKushkiLog: function(response, method){
            rpc.query({
                model: 'kushki.log',
                method: 'create_log_request_token',
                args: [session.user_id, response, method],
            });

//            .then(function () {
//                //self._kushkiCreateSusbcription();
//            });
        },

        _searchSubscription(resp, resp_binInfo){
            console.log('searchInfoSubscription');
            self = this;
            var subscriptionId = resp
            var settings = {
                "async": true,
                "crossDomain": true,
                "url": "https://api-uat.kushkipagos.com/subscriptions/v1/card/search/",
                "method": "GET",
                "headers": {}
            }
            $.ajax(settings).done(function (response) {
                if(!response.code){
                    self._createKushkiLog(response, 'searchSubscription');

                } else {
                    self._createKushkiLog(response, 'searchSubscription');
                    $("#subscribe").prop('disabled', false);
                    //self.do_warn(_t("Error"), _t(response.message));
                    console.log(_t("Error"), _t(response.message));
                    console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                }
            });
        },

        _kushkiCreateSusbcription: function(resp_binInfo){
            console.log('createSubscription');
            self = this;
            var values = this._getValuesFieldsForm('kuski_credit_cajita');
            var today = new Date();
            var str_today = this._strDateToday(today)
            var username = values['username'].split(" ");
            var subscription = {
                "token": values['subscriptionToken'],
                "planName": values['document_number'],
                "periodicity": "custom",
                "contactDetails": {
                    "documentType": "RUT",
                    "documentNumber": values['document_number'],
                    "email": values['email'],
                    "firstName": username[0],
                    "lastName": username[1],
                    "phoneNumber": values['codigo'] + values['phone_credit']
                },
                "amount": {
                    "subtotalIva": 0,
                    "subtotalIva0": 0,
                    "ice": 0,
                    "iva": 0,
                    "currency": "CLP"
                },
                "startDate": str_today
            }
            var stringSubscription = JSON.stringify(subscription);
            var settings = {
                "async": true,
                "crossDomain": true,
                "url": "https://api-uat.kushkipagos.com/subscriptions/v1/card",
                "method": "POST",
                "headers": {
                    "private-merchant-id": values['creditPublicMerchant'],
                    "content-type": "application/json"
                },
                "processData": false,
                "data": stringSubscription
            }

            
            $.ajax(settings).done(function (response) {
                if(!response.code){
                    self._createKushkiLog(response, 'createSubscription');
                    self._searchSubscription(response, resp_binInfo)
                } else {
                    self._createKushkiLog(response, 'createSubscription');
                    $("#subscribe").prop('disabled', false);
                    //self.do_warn(_t("Error"), _t(response.message));
                    console.log(_t("Error"), _t(response.message));
                    console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                }
            });
        },

        _kushkiWebpayCreateSusbcription: function(){
            console.log('createSubscriptionWebpay');
            self = this;
            var values = this._getValuesFieldsForm('kuski_credit_cajita');
            var today = new Date();
            var str_today = this._strDateToday(today)
            var subscription = {
                "token": values['webpaySubsctiptionToken'],
                "planName": values['document_number_webpay'],
                "periodicity": "custom",
                "contactDetails": {
                    "documentType": "RUT",
                    "documentNumber": values['document_number_webpay'],
                    "email": values['mail'],
                    "firstName": values['firstname'],
                    "lastName": values['lastname'],
                    "phoneNumber": values['codigo_webpay'] + values['phone_webpay']
                },
                "amount": {
                    "subtotalIva": 0,
                    "subtotalIva0": 0,
                    "ice": 0,
                    "iva": 0,
                    "currency": "CLP"
                },
                "startDate": str_today
            }
            var stringSubscription = JSON.stringify(subscription);
            var settings = {
                "async": true,
                "crossDomain": true,
                "url": "https://api-uat.kushkipagos.com/subscriptions/v1/card-async/init",
                "method": "POST",
                "headers": {
                    //"Private-Merchant-Id": values['creditPrivateMerchant'],
                    "content-type": "application/json"
                },
                "processData": false,
                "data": stringSubscription
            }


            $.ajax(settings).done(function (response) {
                if(!response.code){
                    self._createKushkiLog(response, 'createSubscriptionCardAsync');
                } else {
                    self._createKushkiLog(response, 'createSubscriptionCardAsync');
                    $("#subscribe").prop('disabled', false);
                    //self.do_warn(_t("Error"), _t(response.message));
                    console.log(_t("Error"), _t(response.message));
                    console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                }
            });
        },

        _kushkiBinInfo: function(){
            console.log('BinInfo');
            self = this;
            var values = this._getValuesFieldsForm('kuski_credit_cajita');
            var bin = values['card'].substr(0,6)
            var settings = {
                "async": true,
                "crossDomain": true,
                "url": "https://api-uat.kushkipagos.com/card/v1/bin/" + bin,
                "method": "GET",
                "headers": {
                    "Public-Merchant-Id": values['creditPublicMerchant'],
                    "content-type": "application/json",
                }
            }
            $.ajax(settings).done(function (response) {
                if(!response.code){
                    self._createKushkiLog(response, 'BinInfo');
                    self._kushkiCreateSusbcription(response);
                } else {
                    self._createKushkiLog(response, 'BinInfo');
                    $("#subscribe").prop('disabled', false);
                    //self.do_warn(_t("Error"), _t(response.message));
                    console.log(_t("Error"), _t(response.message));
                    console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                }
            });
        },

        _responseCreditCard: function(){
            self = this;
            var msg_errors = {
                msg_relationship: "",
                msg_username: "",
                msg_card: "",
                msg_expiry_month: "",
                msg_expiry_year: "",
                msg_cvc: "",
                msg_email: "",
                msg_document_number: "",
                msg_codigo: "",
                msg_phone_credit: "",
                msg_accept_tc: "",
            };
            $.each(msg_errors, function(item, val) {
                $('#' + item).css('display', 'none');
            })
            var values = this._getValuesFieldsForm('kuski_credit_cajita');
            var validated = this._validateFields(values)
            if (validated == true){
                $("#subscribe").prop('disabled', true);
                $('#modalmethodpaymentcredit').css("display", "none");
                $('#modalloader').css("display", "block");
                // $('#goback').css("display", "none");
                // $('#loader').css("display", "block");
                var kushki = this._configObjectKushki(values['creditPublicMerchant'])
                var requestToken = function(response) {
                    if(!response.code){
                        self._createKushkiLog(response, 'requestSubscriptionToken');
                        // $('#loader').css("display", "none");
                        $("#subscriptionToken").val(response.token);
                        //self._kushkiBinInfo()
                        // $("#modalmethodpaymentcredit").css("display", "block");
                        $("#kuski_credit_cajita").submit()
                    } else {
                        self._createKushkiLog(response, 'requestSubscriptionToken');
                        // $('#loader').css("display", "none");
                        $("#modalloader").css("display", "none");
                        $("#subscribe").prop('disabled', false);
                        //self.do_warn(_t("Error"), _t(response.message));
                        Dialog.alert(self, _t(`${response.message}`), {
                            title: _t(`Error: ${response.code}`),
                            buttons: [{ text: _t("Close"), close: true }],
                        });
                        $("#modalmethodpaymentcredit").css("display", "block");
                        console.log(_t("Error"), _t(response.message));
                        console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                    }
                }
                if (values['subscriptionToken'] == '') {
                    console.log('Token Subscription');
                    kushki.requestSubscriptionToken({
                        currency: "CLP",
                        card: {
                            name: values['username'],
                            number: values['card'],
                            cvc: values['cvc'],
                            expiryMonth: values['expiry_month'],
                            expiryYear: values['expiry_year']
                        }
                    }, requestToken);

                }else {
                    $("#kuski_credit_cajita").attr('action', '/kushki_paymentmethods/update').submit()
                }
            } else {
                $("#subscribe").prop('disabled', true);
                $.each(validated, function(item, msg) {
                    $('#msg_' + item).text(msg)
                    $('#msg_' + item).css('display', 'block');
                })
                //self.do_warn("Error", validated);
            }
        },

        _responseDebitCard: function(){
            var self = this;
            $('.subscribe_debit_card').attr("disabled", true);
            $('#modalmethodpaymentdebit').css("display", "none");
            $('#modalloader').css("display", "block");
            var values = this._getValuesFieldsForm('kuski_cajita');
            var validated = this._validateFieldsWebpay(values)
            if (validated == true){
                var kushki = this._configObjectKushki(values['debitPublicMerchant'])
                var url = values["debitBaseUrl"] + "/payment/success";
                var callback = function(response) {
                    if(!response.code){
                        self._createKushkiLog(response, 'requestSubscriptionToken');
                        $("#webpaySubsctiptionToken").val(response.token);
                        // $("#modalmethodpaymentdebit").css("display", "none");
                        //self._kushkiWebpayCreateSusbcription()
                        $("#kuski_cajita").submit();
                    } else {
                        self._createKushkiLog(response, 'requestSubscriptionToken');
                        $("#subscribe_debit_card").prop('disabled', false);
                        // $('#loader').css("display", "none");
                        $("#modalloader").css("display", "none");
                        Dialog.alert(self, _t(`${response.message}`), {
                            title: _t(`Error: ${response.code}`),
                            buttons: [{ text: _t("Close"), close: true }],
                        });
                        $("#modalmethodpaymentdebit").css("display", "block");
                        console.error('Error: ',response.error, 'Code: ', response.code, 'Message: ',response.message);
                    }
                }
                if (values['webpaySubsctiptionToken'] == '') {
                    console.log('Token Subscription Webpay');
                    kushki.requestSubscriptionCardAsyncToken({
                        currency: "CLP",
                        email: values['mail'],
                        callbackUrl: url,
                    }, callback);
                }
            } else {
                $("#subscribe").prop("disabled", true);
                $("#modalmethodpaymentdebit").css("display", "block");
                $('.subscribe_debit_card').attr("disabled", true);
            }
        },

        _associatePayment: function(){
            var values = this._getValuesFieldsForm('modal_existing_payment');
            if (values['paymentlist'] != ''){
                $("#modal_existing_payment").submit();
            }else{
                //this.do_warn(_t("Campos requeridos"), _t("Debe seleccionar un metodo de pago de la lista"));
                console.log(_t("Campos requeridos"), _t("Debe seleccionar un metodo de pago de la lista"));
            }
        },

    });

});
