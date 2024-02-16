odoo.define('bi_website_portal_payments.pay_multiple_partial_payment', function(require) {
    "use strict";

    var core = require('web.core');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var request
    var _t = core._t;
    var invoice_data = false

    $(document).ready(function(){
        $("#pay_multiple_partial").click(function(ev){
            var invoice_ids = []
            var $form = $(ev.currentTarget).parents('form');
            $('.o_portal_my_doc_table input[type="checkbox"]:checked').each(function(){
                var id = $(this).attr('value');
                invoice_ids.push(id)
            });
            document.getElementById("invoice_ids").value = invoice_ids;
        });

        const createInvoiceForm = document.getElementById('createInvoiceForm');
        if(createInvoiceForm){
            createInvoiceForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(createInvoiceForm);
                const jsonObject = Object.fromEntries(formData.entries());
                const invoice = jsonObject['payment_invoice'];
                const amount = jsonObject['payment_amount1'];
                $.ajax({
                    type: 'POST',
                    url: window.location.origin + '/inovice/amount',
                    dataType: 'json',
                    data: jsonObject,
                    success: function (response) {
                        $('#pay_with_partial').modal();
                    },
                    error: function (data) {
                        console.error('ERROR ', data);
                    },
                    timeout: 30000,
                });
            });
        }

        const createInvoiceMultiForm = document.getElementById('createInvoiceMultiForm');
        if(createInvoiceMultiForm){
            createInvoiceMultiForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(createInvoiceMultiForm);
                const jsonObject = Object.fromEntries(formData.entries());
                $.ajax({
                    type: 'POST',
                    url: window.location.origin + '/inovices/amount',
                    dataType: 'json',
                    data: jsonObject,
                    success: function (response) {
                        $('#pay_with_multi_partial').modal();
                    },
                    error: function (data) {
                        console.error('ERROR ', data);
                    },
                    timeout: 30000,
                });
            });
        }
    });

    $(document).ready(function(){
        $("#amount").focusout(function(ev){
            
            var $form = $(ev.currentTarget).parents('form');
            
            var fistInput = document.getElementById("amount").value;
            var secondInput = document.getElementById("total_amount").value;

            if (parseFloat(fistInput) > parseFloat(secondInput)) 
            {
                document.getElementById("amount").value = null;
                document.getElementById("amount").style.borderColor = "red";
                alert('you can not pay more than amount');            
            }
            else{
                document.getElementById("amount").style.borderColor = null;
            }
        });

    });

    $(document).ready(function(){
        $("#amount1").focusout(function(ev){
            
            var $form = $(ev.currentTarget).parents('form');
            
            var fistInput = document.getElementById("amount1").value;
            var secondInput = document.getElementById("total_amount1").value;

            if (parseFloat(fistInput) > parseFloat(secondInput)) 
            {
                document.getElementById("amount1").value = null;
                document.getElementById("amount1").style.borderColor = "red";
                alert('you can not pay more than amount');            
            }
            else{
                document.getElementById("amount1").style.borderColor = null;
            }
        });

    });
});