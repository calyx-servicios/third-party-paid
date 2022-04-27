odoo.define('pos_promotion_niq.order_line', function (require) {
"use strict";

var core = require('web.core');
var models = require('point_of_sale.models');
var utils = require('web.utils');
var round_di = utils.round_decimals;
var round_pr = utils.round_precision;

var Orderline = models.Orderline;

var _t = core._t;
var _super = Orderline.prototype;

models.Orderline = Orderline.extend({
    initialize: function(attributes, options){
        /*
        initial values of orderline should run before call super
        to avoid re-defined value was set by init_from_JSON function in initialize step
        */
        this.promo_disc_percentage = 0;
        this.promo_disc_amount = 0;
        this.promo_fixed_price = 0;
        this.promo_get_free = 0;
        this.promotion_id = false; // => true if this line is applied from a promotion
        this.condition_promotion_id = false; // true if this line is a condition to apply promotion to another line
                                             //(used for on_product promotion, bxgy, bx discount y..)
        this.amount_promotion_id = false; // true if this line is a condition to apply promotion
                                          //to another line (used for on_amount promotion, discount by total amount of all un-discounted line)
        this.set_origin_price(0);

        // put super at the end because of setting initial value from init_from_JSON function
        _super.initialize.apply(this, arguments);
    },
    // sets a discount [0,100]%
    set_promo_disc_percentage: function(discount){
        var origin_price = this.get_origin_price() > 0 ? this.get_origin_price() : this.get_unit_price();
        var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
        this.set_discount(disc);
        this.set_origin_price(origin_price);
    },
    set_promo_disc_amount: function(disc_amount){
        var origin_price = this.get_origin_price() || this.get_unit_price();
        if (origin_price >= 0 && disc_amount >0) {
            this.promo_disc_amount = Math.min(Math.max(parseFloat(disc_amount) || 0, 0), origin_price);
            if (origin_price != this.get_origin_price()) {
                this.set_origin_price(origin_price);
            }
            this.set_unit_price(origin_price - this.get_promo_disc_amount() || 0)
        }
    },
    set_promo_get_free: function(free_qty) {
        var origin_price = this.get_origin_price() > 0 ? this.get_origin_price() : this.get_unit_price();
        this.promo_get_free = free_qty;
//        this.promo_fixed_price = 0;
        this.promo_disc_amount = origin_price;
        this.set_unit_price(0)
        this.set_origin_price(origin_price);
        // this.trigger('change', this);
    },
    set_promo_fixed_price: function(fixed_price){
        var origin_price = this.get_origin_price() > 0 ? this.get_origin_price() : this.get_unit_price();
        if (origin_price >= 0) {
            this.promo_fixed_price = Math.min(Math.max(parseFloat(fixed_price) || 0, 0), origin_price);
            this.set_unit_price(promo_fixed_price);
            // this.trigger('change', this);
            this.set_origin_price(origin_price);
        }

    },
    set_promotion_id: function(promotion_id){
        this.promotion_id = promotion_id;
    },
    set_amount_promotion_id: function(amount_promotion_id){
        this.amount_promotion_id = amount_promotion_id;
    },
    set_condition_promotion_id: function(promotion_id){
        this.condition_promotion_id = promotion_id;
    },
    set_origin_price: function(origin_price){
        this.origin_price = origin_price;
    },
    get_origin_price: function(){
        return this.origin_price;
    },
    get_promotion_id: function(){
        return this.promotion_id;
    },
    get_amount_promotion_id: function(){
        return this.amount_promotion_id;
    },
    get_condition_promotion_id: function(){
        return this.condition_promotion_id;
    },
    // get_base_price:    function(){
    //     var rounding = this.pos.currency.rounding;
    //     var unit_price = this.get_unit_price();
    //     unit_price = this.compute_promo_unit_price(unit_price);
    //     return round_pr(unit_price * this.get_quantity() * (1 - this.get_discount()/100), rounding);
    // },
    // compute_all: function(taxes, price_unit, quantity, currency_rounding, no_map_tax) {
    //     price_unit = this.compute_promo_unit_price(price_unit);
    //     return _super.compute_all.call(this, taxes, price_unit, quantity, currency_rounding, no_map_tax);
    // },
    compute_promo_unit_price: function(unit_price){
        if (this.get_promo_disc_amount()){
            unit_price -= this.get_promo_disc_amount() || 0;
        }
        else if (this.get_promo_get_free()) {
            // get promotion_fixed_price as 0
            unit_price = 0;
        }
        else if (this.get_promo_fixed_price()) {
            unit_price = this.get_promo_fixed_price();
        }
        else if (this.get_promo_disc_percentage()) {
            unit_price = unit_price * (1 - this.promo_disc_percentage/100);
        }
        var digits = this.pos.dp['Product Price'];
        // round and truncate to mimic _symbol_set behavior
        return unit_price;
//        return parseFloat(round_di(unit_price || 0, digits).toFixed(digits));
    },
    has_promotion: function(){
        return  this.get_promo_disc_amount() || this.get_promo_get_free() || this.get_promo_fixed_price() || this.get_promo_disc_percentage();
    },
//    // returns the discount [0,100]%
//    get_discount: function(){
//        return this.discount + this.promo_disc_percentage;
//    },
    get_promo_disc_amount: function(){
        return this.promo_disc_amount;
    },
    get_promo_disc_percentage: function(){
        return this.promo_disc_percentage;
    },
    get_promo_fixed_price: function(){
        return this.promo_fixed_price;
    },
    get_promo_get_free: function(){
        return this.promo_get_free;
    },
    split_line: function(qty_to_split){
        var new_line = this.clone();
        this.set_quantity(qty_to_split);
        this.order.add_orderline(new_line);
        new_line.set_quantity(new_line.get_quantity() - qty_to_split);
        return new_line;
    },
    set_product_promotion: function(prod_promo){
        if (prod_promo.disc_percentage > 0){
            this.set_promo_disc_percentage(prod_promo.disc_percentage)
            this.set_promotion_id(prod_promo.promotion_id[0]);

        } else if (prod_promo.disc_amount > 0) {
            this.set_promo_disc_amount(prod_promo.disc_amount);
            this.set_promotion_id(prod_promo.promotion_id[0]);
        } else if (prod_promo.fixed_price > 0) {
            this.set_promo_fixed_price(prod_promo.fixed_price);
            this.set_promotion_id(prod_promo.promotion_id[0]);
        } else if (prod_promo.free_qty > 0) {
            this.set_promo_get_free(prod_promo.free_qty);
            this.set_promotion_id(prod_promo.promotion_id[0]);
        }
    },
    clear_promotion: function(){
        this.promo_disc_percentage = 0;
        this.promo_disc_amount = 0;
        this.promo_fixed_price = 0;
        this.promo_get_free = 0;
        this.condition_promotion_id = false;
        this.promotion_id = false;
        this.amount_promotion_id = false;

        // reset unit_price to origin unit_price
        var origin_price = this.get_origin_price()
        if (origin_price > 0){
            this.set_unit_price(origin_price)
        }

        this.set_origin_price(0);

        this.trigger('change', this);
    },
    export_as_JSON: function() {
        var res = _super.export_as_JSON.call(this);
        _.extend(res, {
            promo_disc_percentage: this.get_promo_disc_percentage(),
            promo_disc_amount: this.get_promo_disc_amount(),
            promo_fixed_price: this.get_promo_fixed_price(),
            promo_get_free: this.get_promo_get_free(),
            promotion_id: this.get_promotion_id(),
            amount_promotion_id: this.get_amount_promotion_id(),
            condition_promotion_id: this.get_condition_promotion_id(),
            origin_price: this.get_origin_price()
        });
        return res;
    },
    init_from_JSON: function(json) {
        _super.init_from_JSON.call(this, json);
        // setting origin price first for next promotion
        this.set_origin_price(json.origin_price);

        // set custom promotion
        this.set_promotion_id(json.promotion_id);
        this.set_amount_promotion_id(json.amount_promotion_id);
        this.set_condition_promotion_id(json.condition_promotion_id);
        this.set_promo_disc_percentage(json.promo_disc_percentage);
        this.set_promo_disc_amount(json.promo_disc_amount);
        this.set_promo_fixed_price(json.promo_fixed_price);

    },
});


});
