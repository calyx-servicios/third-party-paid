odoo.define('pos_xml_receipt.Printer', function (require) {
  var printers = require('point_of_sale.Printer');
  var core = require('web.core');
  var utils = require('web.utils');

  printers.Printer.include({
    print_receipt_xml: async function(receipt) {
        if (receipt) {
            this.receipt_queue.push(receipt);
        }
        let sendPrintResult;
        while (this.receipt_queue.length > 0) {
            receipt = this.receipt_queue.shift();
            try {
                sendPrintResult = await this.send_printing_job_xml(receipt);
            } catch (error) {
                // Error in communicating to the IoT box.
                this.receipt_queue.length = 0;
                return this.printResultGenerator.IoTActionError();
            }
            // rpc call is okay but printing failed because
            // IoT box can't find a printer.
            if (sendPrintResult && sendPrintResult.result === false) {
                this.receipt_queue.length = 0;
                return this.printResultGenerator.IoTResultError();
            }
        }
        return this.printResultGenerator.Successful();
    },
    send_printing_job_xml: function (xml) {
        return this.connection.rpc('/hw_proxy/print_xml_receipt', {
                receipt: xml
        });
    },
  });



});
