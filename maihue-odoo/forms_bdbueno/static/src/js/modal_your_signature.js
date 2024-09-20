odoo.define('your_signature.modal_your_signature', function (require) {

	'use strict';
    var rpc = require('web.rpc');

    $(document).ready(function(){
        $("#open_modal_your_signature").click(function(){
            $('#cajita_tu_firma').modal('show');
        });
        $("#boton_validar").click(function(){
            $('#modal_firma_contrato').css("display", "none");
            $('#modalvalidacion').css("display", "block");
        });
        $("#boton_siguiente").click(function(){
            $('#modal_firma_contrato').css("display", "none");
            $('#modalvalidacion').css("display", "none");
            $('#modalcedula').css("display", "block");
        });
        $("#boton_atras_validacion").click(function(){
            $('#modalcedula').css("display", "none");
            $('#modalvalidacion').css("display", "none");
            $('#modal_firma_contrato').css("display", "block");
        })
        $("#boton_atras").click(function(){
            $('#modal_firma_contrato').css("display", "none");
            $('#modalcedula').css("display", "none");
            $('#modalvalidacion').css("display", "block");
        })
    });

    $(document).ready(function(){
        $("#boton_validar").click(function(){
            console.log('hola')
        })
    })

});