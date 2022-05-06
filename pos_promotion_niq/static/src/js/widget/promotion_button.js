odoo.define('pos_promotion_niq.promotion_button', function (require) {
"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');

var _t = core._t;

var PromotionButton = screens.ActionButtonWidget.extend({
    template: 'PromotionButton',
    button_click: function(){
        var order    = this.pos.get_order();
        order.apply_promotion();
    },
});

screens.define_action_button({
    'name': 'promotion_button',
    'widget': PromotionButton
});


});
