odoo.define('pos_promotion_niq.pos', function (require) {
"use strict";

var core = require('web.core');
var models = require('point_of_sale.models');
var PosModel = models.PosModel;

var _super = PosModel.prototype;

models.PosModel = PosModel.extend({

    initialize: function(attributes, options){
        _super.initialize.apply(this, arguments);
    }
});

});
