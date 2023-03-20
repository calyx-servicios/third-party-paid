odoo.define('pos_xml_receipt.AbstractReceiptScreen', function (require) {
"use strict";

var SuperAbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;
var rpc = require('web.rpc');
const Registries = require('point_of_sale.Registries');


const AbstractReceiptScreen = (SuperAbstractReceiptScreen) =>
		class extends SuperAbstractReceiptScreen {
      async _printReceipt() {
          if (this.env.pos.proxy.printer) {
              if (this.env.pos.config.print_xml_receipt){
                return await this._printXML();
              }else{
                return await super._printReceipt();
              }
          } else {
              return await this._printWeb();
          }
      }
      async _printXML(){
				let vals = this.currentOrder.getOrderReceiptEnv();
				vals.env = this.env;
        const receipt = QWeb.render('XmlReceipt', vals);
        const printResult = await this.env.pos.proxy.printer.print_receipt_xml(receipt);
				if (printResult.successful) {
						return true;
				} else {
						const { confirmed } = await this.showPopup('ConfirmPopup', {
								title: printResult.message.title,
								body: 'Do you want to print using the web printer?',
						});
						if (confirmed) {
								// We want to call the _printWeb when the popup is fully gone
								// from the screen which happens after the next animation frame.
								await nextFrame();
								return await this._printWeb();
						}
						return false;
				}
      }
		}
	Registries.Component.extend(SuperAbstractReceiptScreen, AbstractReceiptScreen);

	return AbstractReceiptScreen;
});
