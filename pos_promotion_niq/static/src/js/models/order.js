odoo.define('pos_promotion_niq.order', function (require) {
"use strict";

var core = require('web.core');
var models = require('point_of_sale.models');
var Order = models.Order;

var utils = require('web.utils');
var round_di = utils.round_decimals;
var round_pr = utils.round_precision;

var _t = core._t;
var _super = Order.prototype;

models.Order = Order.extend({
    initialize: function(attributes, options){
        _super.initialize.apply(this, arguments);

    },
    apply_promotion: function(){
        console.log("applied promotion");

        var promotions = this.pos.db.get_promotions();
        var promotions_on_product = promotions['on_product'];
        var promotions_on_amount = promotions['on_amount'];
        // clear before apply
        this.clear_promotion();
        this.apply_promotion_on_product(promotions_on_product);
        this.apply_promotion_on_amount(promotions_on_amount);

    },
    clear_promotion: function(){
        var self = this;
        _.each(self.get_orderlines(), function(line){
            line.clear_promotion();
        });
    },
    can_apply_promotion_for_this_pos(promotion){
        var can_apply = true;
        var promotion_pos_ids = promotion.pos_ids;
        var current_pos_id = this.pos.config.id;
        if (_.indexOf(promotion_pos_ids, current_pos_id) === -1){
            can_apply = false;
        }
        return can_apply;
    },
    check_expiration(promotion) {
        var start_date = promotion.start_date;
        var end_date = promotion.end_date;
        var mmstart_date = moment(start_date);
        var mmend_date = moment(end_date);
        var today = moment(moment(new Date()).format("YYYY-MM-DD"));
        var can_apply = false

        if (!!!start_date && !!!end_date) {
            can_apply = true
        }
        if (!!start_date && !!!end_date && mmstart_date <= today) {
            can_apply = true
        }
        if (!!!start_date && !!end_date && mmend_date >= today) {
            can_apply = true
        }
        if (!!start_date && !!end_date && mmstart_date <= today && mmend_date >= today) {
            can_apply = true
        }

        return can_apply;
    },
    /**
    // get lines of order
        // total amount = total amount of product (
        // - exclude which to be applied for standalone condition of this current promotion
        // - exclude which is a condition of another promotion
        // - exclude which added by other promotion (not promotion_id)
        // - exclude which was applied another amount promotion (not amount_promotion_id)
    **/
        get_lines_to_sum_amount: function(promotion){
            var sum_lines = _.filter(this.get_orderlines(), function(line){
                return !line.get_promotion_id() &&
                       !line.get_condition_promotion_id() &&
                       !line.get_amount_promotion_id()
            })
            return sum_lines;
        },
    /**
    // get lines of order
        // total amount = total amount of product (
        // - exclude which to be applied for standalone condition of this current promotion
        // - exclude which is a condition of another promotion
        // - exclude which added by other promotion (not promotion_id)
        // - exclude which was applied another amount promotion (not amount_promotion_id)
    **/
    get_lines_can_be_apply: function(promotion){
        var prod_promotions = this.pos.db.get_promo_product_by_promo_id(promotion.id);
        var will_apply_prod_ids = _.map(prod_promotions, function(prod_promotion){
                return prod_promotion.product_id[0];
            });
        var sum_lines = _.filter(this.get_orderlines(), function(line){
            return !line.get_promotion_id() &&
                   !line.get_condition_promotion_id() &&
                   !line.get_amount_promotion_id() &&
                _.indexOf(will_apply_prod_ids, line.product.id) === -1;
        })
        return sum_lines;
    },
    /**
    Compute to get check if can apply promotion amount for this other
    */
    can_applicable_promo_on_amount:function(promotion){
        var self = this;
        var order_lines = this.get_orderlines();
        var is_applicable = false;
        var total_amount = 0, apply_times = 0;

        var sum_lines = this.get_lines_to_sum_amount(promotion);

        // get total amount of all sum lines
        _.each(sum_lines, function(line){
            total_amount += line.get_price_with_tax();
        });

        // check if total_amount >= amount of order
        if (promotion.applicable_amount){
            apply_times = parseInt(total_amount / promotion.applicable_amount, 0);
        }
        return apply_times;

    },
    apply_promotion_on_amount: function(promotions){
        var self = this;
        var order_lines = this.get_orderlines();
        _.each(promotions, function(promotion){
            // check if this.promotion can apply for this pos
            var can_apply = self.can_apply_promotion_for_this_pos(promotion);
            can_apply = can_apply && self.check_expiration(promotion);
            if (!can_apply){
                // return immediately
                return can_apply;
            }

            var already_applied = false;
            var apply_times = self.can_applicable_promo_on_amount(promotion);
            if (apply_times){
                if (promotion.discount_total_amount > 0) {
                    _.each(self.get_orderlines(), function(line){
                        if (!line.get_promotion_id()
                            && !line.get_amount_promotion_id()
                            && !line.get_condition_promotion_id()){

                            line.set_promo_disc_percentage(promotion.discount_total_amount);
                            // mark line as condition of this promotion
                            line.set_amount_promotion_id(promotion.id);
                            // mark line as product was applied promotion
                            line.set_promotion_id(promotion.id);
                        }
                    })
                } else {

                    var prod_promotions = self.pos.db.get_promo_product_by_promo_id(promotion.id);
                    var order_product_ids = _.map(order_lines, function(line){
                        return line.product.id;
                    });
                    _.each(order_lines, function(line){
                        _.each(prod_promotions, function(prod_promo){
                            // if promotion is get free product, get free_qty on product_promotion line
                            // else for (%, amount, fixed_price), default is 1 time
                            var apply_qty = apply_times * (prod_promo.promotion_code === 'amount_get_free' && prod_promo.free_qty > 1 && prod_promo.free_qty || 1);
//                            apply_qty = Math.min(apply_qty, line.get_quantity());

                            if (line.product.id === prod_promo.product_id[0]
                                && apply_qty > 0
                                && !already_applied
                                && !line.get_promotion_id()) {

                                // split line if apply qty < current qty
                                if (apply_qty < line.get_quantity()){
                                    var origin_qty = line.get_quantity();
                                    var new_line = line.clone();
                                    self.add_orderline(new_line);

                                    line.set_quantity(apply_qty);

                                    new_line.set_quantity(origin_qty - apply_qty)
                                } else
                                if (apply_qty > line.get_quantity()){
                                    line.set_quantity(apply_qty);
                                }
                                line.set_product_promotion(prod_promo);
                                apply_qty -= line.get_quantity();

                                // set as already_applied
                                already_applied = true;
                            }
                        })
                    });

                }

                if (already_applied){
                    // set account_promotion_id = promotion_id for each line
                    // to mark these line as were applied on amount promotion,
                    // don't apply any amount promotion anymore.
                    var condition_lines = self.get_lines_can_be_apply(promotion);
                    _.each(condition_lines, function(line){
                        line.set_amount_promotion_id(promotion.id);
                    });
                }
            }
        });
    },
    apply_promotion_on_product: function(promotions){
        var self = this;
        var order_lines = this.get_orderlines();
        _.each(promotions, function(promotion){
            // check if this.promotion can apply for this pos
            var can_apply = self.can_apply_promotion_for_this_pos(promotion);
            can_apply = can_apply && self.check_expiration(promotion);
            if (!can_apply){
                // return immediately if this promotion is not OK
                return can_apply;
            }

            var prod_promotions = self.pos.db.get_promo_product_by_promo_id(promotion.id);
            var apply_tmpl_promotions = self.pos.db.get_promo_template_by_promo_id(promotion.id);
            var apply_categ_promotions = self.pos.db.get_promo_category_by_promo_id(promotion.id);

            // combo condition of promotion
            var combo_condition_prod_ids = self.get_combo_condition_product_ids(promotion).sort();

            // they can be selected line by line => single condition for each line
            var standalone_condition_prod_ids = self.get_standalone_condition_prod_ids(promotion);

            // product_ids of order
            var order_product_ids = self.get_order_product_ids(order_lines);

            /**
            There are 2 cases here to apply for BUY promotion:
                - 1. If promotion has buy condition, order must contain product in condition_product_ids list
                - 2. If promotion doesn't have condition, order can apply promotion as discount base on product
            */
            var standalone_condition_common_prod_ids = _.intersection(standalone_condition_prod_ids, order_product_ids).sort();

            // same for combo condition
            var combo_condition_common_prod_ids = _.intersection(combo_condition_prod_ids, order_product_ids).sort();


            // the main logic is here
            if (!_.isEmpty(combo_condition_prod_ids)) {

                // if exist standalone condition also, apply it
                if (!_.isEmpty(standalone_condition_prod_ids)){
                    self.apply_with_condition_standalone(promotion);
                }
                // if exist combo product product_ids
                if (_.isEqual(combo_condition_common_prod_ids.sort(), combo_condition_prod_ids.sort())) {
                    self.apply_with_condition_combo(promotion);
                }

            } else {

                    // if exist standalone condition also, apply it first
                    if (!_.isEmpty(standalone_condition_prod_ids)){
                        self.apply_with_condition_standalone(promotion);
                    } else {
                        self.apply_promotion_line_unlimit_times(prod_promotions);
                    }

                    // process for template promotion
                    self.apply_promotion_line_unlimit_times(apply_tmpl_promotions);

                    // process for category promotion
                    self.apply_promotion_line_unlimit_times(apply_categ_promotions);
            }

        });
    },
    apply_promotion_with_condition: function(promotion) {
        this.apply_with_condition_standalone(promotion);
        this.apply_with_condition_combo(promotion);
        this.apply_with_condition_total(promotion);
    },
    apply_with_condition_standalone: function(promotion){
        var self = this;
        var prod_promotions = self.pos.db.get_promo_product_by_promo_id(promotion.id);
        var standalone_condition_prod_ids = self.get_standalone_condition_prod_ids(promotion);

        // find all promotion line that exist condition_product = product of order line
        var promo_lines = _.filter(prod_promotions, function(line){
            return _.indexOf(standalone_condition_prod_ids, line.condition_product_id[0]) != -1;
        })
        var order_lines = this.get_orderlines();

        // for each promo line
        _.each(promo_lines, function(promo_line){
            _.each(order_lines, function(order_line){
                var apply_times = self.get_apply_time_standalone_condition(order_line, promo_line);
                // check each line with each condition
                if (apply_times){
                    // mark current line as condition_promotion_id to know this line already apply
                    order_line.set_condition_promotion_id(promo_line.promotion_id[0]);
                    // find apply_lines to apply this promotion
                    var apply_lines = self.find_apply_promotion_line(promo_line.product_id[0], promo_line.condition_product_id[0]);
                    apply_times = self.apply_promotion_line_limit_times(apply_lines, [promo_line], apply_times);

                }
            })
        })

    },
    apply_with_condition_combo: function(promotion){
        var self = this;
        var apply_times = [];
        var apply_lines = [];
        var condition_line_ids = [];
        var all_condition_ok = true;
        var combo_conditions = self.pos.db.get_promo_combo_condition_by_promo_id(promotion.id);

        for (var i=0; i < combo_conditions.length; i ++) {
            var condition = combo_conditions[i];
            condition.multiply_weight = 0;
            var condition_ok = false;
            _.each(self.get_orderlines(), function(order_line){
                // check each line with each condition
                if (order_line.product.id == condition.condition_product_id[0]
                    && order_line.get_quantity() >= condition.condition_qty
                    && condition.condition_qty > 0
                    && !order_line.get_promotion_id()
                    && !order_line.get_condition_promotion_id()
                    && condition.multiply_weight == 0){

                    // ok, process apply multiple time if enough
                    var multiply_weight = parseInt(order_line.get_quantity() / condition.condition_qty, 0);
                    if (multiply_weight > 0){

                        condition.multiply_weight = multiply_weight;
                        condition.order_line = order_line;
                        condition_ok = true;
                        apply_times.push(multiply_weight);
                        condition_line_ids.push(order_line.id);
                    }
                }
            })

            all_condition_ok = all_condition_ok && condition_ok;

            if (!all_condition_ok){
                break;
            }

        }

        if (!all_condition_ok){
            return;
        }
        // multiply_weight is the min multiply_weight of all condition
        var all_weights = _.map(combo_conditions, function(condition){ return condition.multiply_weight; })
        var multiply_number = _.min(all_weights);
        _.each(combo_conditions, function(condition){
            // split line if needed
            var qty_to_condition_ok = multiply_number * condition.condition_qty;
            var order_line = condition.order_line;
            // split line if current_line is > qty_to_condition_ok
            if (order_line.get_quantity() > qty_to_condition_ok){
                order_line.split_line(qty_to_condition_ok);
            }
            // mark order_line as condition of combo promotion
            order_line.set_condition_promotion_id(promotion.id);
        })

        apply_times = _.min(apply_times);
        if (apply_times > 0 && all_condition_ok){
            // find line to apply promotion
            var apply_lines = _.filter(self.get_orderlines(), function(order_line){
                // return _.indexOf(condition_line_ids, order_line.id) === -1
                //         && !order_line.get_promotion_id()
                //         && !order_line.get_condition_promotion_id()
                return !order_line.get_promotion_id();
            })

            var prod_promotions = self.pos.db.get_promo_product_by_promo_id(promotion.id);
            prod_promotions = _.filter(prod_promotions, function(promotion){ return !promotion.condition_product_id; })
            /**
             * Small case, apply lines will be condition product themself
             */
            apply_times = self.apply_promotion_line_combo_limit_times(apply_lines, prod_promotions, apply_times);

            var apply_tmpl_promotions = self.pos.db.get_promo_template_by_promo_id(promotion.id);
            apply_times = self.apply_promotion_line_limit_times(apply_lines, apply_tmpl_promotions, apply_times);

            var apply_categ_promotions = self.pos.db.get_promo_category_by_promo_id(promotion.id);
            apply_times = self.apply_promotion_line_limit_times(apply_lines, apply_categ_promotions, apply_times);

            // in case has apply_lines
            // and already apply product/ template/ category. But still exist apply_times,
            // => there is no promotion_line has product = apply_lines, auto add random the first line of prod_promotions if any
            if (!_.isEmpty(prod_promotions) && apply_times) {
                var promotion_line = prod_promotions[0];
                if (_.has(promotion_line, 'product_id')){
                    var product = this.pos.db.get_product_by_id(promotion_line.product_id[0]);
                    var line = new models.Orderline({}, {pos: this.pos, order: this, product: product})
                    self.add_orderline(line);
                    line.set_quantity(apply_times);
                    line.set_product_promotion(promotion_line);
                    apply_times = 0;
                }
            }

        };
    },
    /*** UTILS ******/
    get_apply_time_standalone_condition(order_line, promo_line){
        var apply_times = 0;
        var self = this;
        if (order_line.product.id == promo_line.condition_product_id[0]
            && order_line.get_quantity() >= promo_line.condition_qty
            && promo_line.condition_qty > 0
            && order_line.get_quantity() > 0
            && !order_line.get_promotion_id()
            && !order_line.get_condition_promotion_id()
        ) {
            var qty_each_time = _.indexOf(['prod_bxgy_free', 'amount_get_free'], promo_line.promotion_code) != -1 ? (promo_line.free_qty || 1) : 1;
            // ok, process apply multiple time if enough
            var apply_times = parseInt(order_line.get_quantity() * qty_each_time/promo_line.condition_qty);
            // split product if needed
            var applicable_qty = apply_times * promo_line.condition_qty;
            if (applicable_qty > 0 && applicable_qty < order_line.get_quantity()){
                var new_line = order_line.split_line(applicable_qty);

            }
        }
        return apply_times;
    },
    get_standalone_condition_prod_ids: function(promotion) {
        var prod_promotions = this.pos.db.get_promo_product_by_promo_id(promotion.id);

        // they can be selected line by line => single condition for each line
        var standalone_condition_prod_ids = _.map(prod_promotions, function(prod_promotion){
            return prod_promotion.condition_product_id[0];
        });

        standalone_condition_prod_ids = _.filter(standalone_condition_prod_ids, function(prod_id) { return prod_id; })
        return standalone_condition_prod_ids;
    },
    get_combo_condition_product_ids: function(promotion){
        // combo condition of promotion
        var combo_conditions = this.pos.db.get_promo_combo_condition_by_promo_id(promotion.id);

        var combo_condition_prod_ids = _.map(combo_conditions, function(condition){
            return condition.condition_product_id[0];
        });

        combo_condition_prod_ids = _.filter(combo_condition_prod_ids, function(prod_id) { return prod_id; })
        return combo_condition_prod_ids;
    },
    get_order_product_ids: function(order_lines){
        // product_ids of order
        var order_product_ids = _.map(order_lines, function(line){
            return line.product.id;
        });
        // sort for easier compare
        order_product_ids = order_product_ids.sort();
        return order_product_ids;
    },
    apply_promotion_line_limit_times: function(apply_lines, promotion_lines, apply_times){
        var self = this;
        // case (_.isEmpty(multi_condition_product_ids) && _.isEmpty(standalone_condition_prod_ids))
        if (!apply_times){
            console.log(">> apply_promotion_line: apply_time is:", apply_times);
            return false;
        }

        // if there is no apply_lines, auto add a line
        if (_.isEmpty(apply_lines)){
            for (var p=0; p < promotion_lines.length; p++) {
                var promotion_line = promotion_lines[p];
                if (_.has(promotion_line, 'product_id')){
                    var product = this.pos.db.get_product_by_id(promotion_line.product_id[0]);
                    var line = new models.Orderline({}, {pos: this.pos, order: this, product: product})
                    self.add_orderline(line);
                    line.set_quantity(apply_times);
                    line.set_product_promotion(promotion_line);
                    apply_times = 0;
                }
            }
        } else {
            var last_product_line = false;

            for (var i=0; i < apply_lines.length; i++) {
                var order_line = apply_lines[i];
                // break if there isn't appy_times anymore
                if (!apply_times){
                    break;
                }
                // check if this line is ok to apply
                if (!order_line.get_promotion_id()
                    && !order_line.get_condition_promotion_id()) {
                    // check if product is product list of promotion program
                    for (var p=0; p < promotion_lines.length; p++) {
                        var promotion_line = promotion_lines[p];

                        // break if there isn't any apply_times anymore
                        if (!apply_times){
                            break;
                        }

                        if ((_.has(promotion_line, 'product_id') && order_line.product.id === promotion_line.product_id[0])
                           || (_.has(promotion_line, 'category_id') && order_line.product.categ.id === promotion_line.category_id[0])
                           || (_.has(promotion_line, 'template_id') && order_line.product.product_tmpl_id === promotion_line.template_id[0])) {
                            // if product has apply_times < qty of line, split it
                            if (apply_times < order_line.get_quantity()){
                                var new_line = order_line.split_line(apply_times);
                            }
                            order_line.set_product_promotion(promotion_line);
                            apply_times -= order_line.get_quantity();

                            // mark last product line, use to set remain quantity
                            last_product_line = order_line;

                        }
                    }
                }
            };

            // if still exist remain apply_times, apply all remain for last line
            if (apply_times > 0 && last_product_line) {
                // get last element and distribute the remain apply_qties
                last_product_line.set_quantity(apply_times + last_product_line.get_quantity());
                apply_times = 0;
            }

        }

        return apply_times;
    },
    apply_promotion_line_combo_limit_times: function (apply_lines, promotion_lines, apply_times) {
        var freeqty_promo_lines = _.filter(promotion_lines, function (pl) {
            return pl.free_qty > 0 && !pl.fixed_price && !pl.disc_percentage && !pl.disc_amount;
        })
        if (!_.isEmpty(freeqty_promo_lines)) {
        this.apply_promotion_line_combo_limit_times_freeqty(apply_lines, promotion_lines, apply_times);
        } else {
        this.apply_promotion_line_combo_limit_times_discount(apply_lines, promotion_lines, apply_times);
        }
    },

    apply_promotion_line_combo_limit_times_freeqty: function (to_apply_lines, promotion_lines, apply_times){
        var self = this;

        var freeqty_promo_lines = _.filter(promotion_lines, function (pl) {
            return pl.free_qty > 0 && !pl.fixed_price && !pl.disc_percentage && !pl.disc_amount;
        })

        // only keep product in apply_lines that exist in promotion_lines
        var promotion_line_product_ids = _.map(promotion_lines, function(pl){ return pl.product_id[0]; })
        var applicable_lines = _.filter(to_apply_lines, function (order_line) {
            return _.indexOf(promotion_line_product_ids, order_line.product.id) != -1;
        })

        /**
         * Get apply time for array of products which to be applied promotion
         */
        var qty_apply_times = {}
        _.each(freeqty_promo_lines, function(pl){
            qty_apply_times[pl.product_id[0]] = pl.free_qty * apply_times;
        })

        if (!apply_times) {
            console.log(">> apply_promotion_line: apply_time is:", apply_times);
            return false;
        }

        // if there is no applicable_lines, auto add a line
        if (_.isEmpty(applicable_lines)) {
            for (var p = 0; p < freeqty_promo_lines.length; p++) {
                var promotion_line = freeqty_promo_lines[p];
                if (_.has(promotion_line, 'product_id')) {
                    var product = this.pos.db.get_product_by_id(promotion_line.product_id[0]);
                    var line = new models.Orderline({}, {
                        pos: this.pos,
                        order: this,
                        product: product
                    })
                    self.add_orderline(line);
                    line.set_quantity(qty_apply_times[product.id]);
                    line.set_product_promotion(promotion_line);
                    qty_apply_times[product.id] = 0;
                }
            }
        } else {

            for (var i = 0; i < applicable_lines.length; i++) {
                var order_line = applicable_lines[i];
                // break if there isn't appy_times anymore
                if (_.isEmpty(qty_apply_times)) {
                    break;
                }
                // check if this line is ok to apply
                if (!order_line.get_promotion_id()) {
                    // check if product is product list of promotion program
                    for (var p = 0; p < freeqty_promo_lines.length; p++) {
                        var promotion_line = freeqty_promo_lines[p];

                        // break if there isn't any apply_times anymore
                        if (_.isEmpty(qty_apply_times)) {
                            break;
                        }

                        if ((_.has(promotion_line, 'product_id') && order_line.product.id === promotion_line.product_id[0]) ||
                            (_.has(promotion_line, 'category_id') && order_line.product.categ.id === promotion_line.category_id[0]) ||
                            (_.has(promotion_line, 'template_id') && order_line.product.product_tmpl_id === promotion_line.template_id[0])) {
                            // if product has apply_times < qty of line, split it
                            var product_times = qty_apply_times[promotion_line.product_id[0]];
                            if (product_times < order_line.get_quantity()) {
                                order_line.split_line(product_times);
                            }
                            order_line.set_product_promotion(promotion_line);
                            qty_apply_times[promotion_line.product_id[0]] -= order_line.get_quantity();


                        }
                    }
                }
            };
        }
        apply_times = 0
        return apply_times;
    },
    apply_promotion_line_combo_limit_times_discount: function (to_apply_lines, promotion_lines, apply_times) {
        var self = this;

        var discount_promo_lines = _.filter(promotion_lines, function (pl) {
            return pl.fixed_price || pl.disc_percentage || pl.disc_amount
        })


        // only keep product in apply_lines that exist in promotion_lines
        var promotion_line_product_ids = _.map(promotion_lines, function (pl) {
            return parseInt(pl.product_id[0]);
        })
        var applicable_lines = _.filter(to_apply_lines, function (order_line) {
            return _.indexOf(promotion_line_product_ids, parseInt(order_line.product.id)) != -1;
        })

        // if there is no applicable_lines, auto add a line
        if (_.isEmpty(applicable_lines)) {
            for (var p = 0; p < promotion_lines.length; p++) {
                var promotion_line = promotion_lines[p];
                if (_.has(promotion_line, 'product_id')) {
                    var product = this.pos.db.get_product_by_id(promotion_line.product_id[0]);
                    var line = new models.Orderline({}, {
                        pos: this.pos,
                        order: this,
                        product: product
                    })
                    self.add_orderline(line);
                    line.set_quantity(apply_times);
                    line.set_product_promotion(promotion_line);
                }
            }
        } else {

            for (var i = 0; i < applicable_lines.length; i++) {
                var order_line = applicable_lines[i];

                // check if this line is ok to apply
                if (!order_line.get_promotion_id()) {
                    // check if product is product list of promotion program
                    for (var p = 0; p < discount_promo_lines.length; p++) {
                        var promotion_line = discount_promo_lines[p];

                        if ((_.has(promotion_line, 'product_id') && order_line.product.id === promotion_line.product_id[0]) ||
                            (_.has(promotion_line, 'category_id') && order_line.product.categ.id === promotion_line.category_id[0]) ||
                            (_.has(promotion_line, 'template_id') && order_line.product.product_tmpl_id === promotion_line.template_id[0])) {

                            order_line.set_product_promotion(promotion_line);
                        }
                    }
                }
            };

        }
        apply_times = 0;
        return apply_times;
    },
    apply_promotion_line_unlimit_times: function(promotion_lines){
        var order_lines = this.get_orderlines();
        // case (_.isEmpty(multi_condition_product_ids) && _.isEmpty(standalone_condition_prod_ids))
        _.each(order_lines, function(order_line){
            // check if this line is ok to apply
            if (!order_line.get_promotion_id()
                && !order_line.get_condition_promotion_id()) {
                // check if product is product list of promotion program
                _.each(promotion_lines, function(promotion_line){
                    if ((_.has(promotion_line, 'product_id') && order_line.product.id === promotion_line.product_id[0])
                        || (_.has(promotion_line, 'category_id') && order_line.product.categ.id === promotion_line.category_id[0])
                        || (_.has(promotion_line, 'template_id') && order_line.product.product_tmpl_id === promotion_line.template_id[0])) {

                        order_line.set_product_promotion(promotion_line);

                    }
                })
            }
        });
    },
    find_apply_promotion_line: function(product_id, condition_product_id=false){
        // find all line has this product_id
        var apply_lines = _.filter(this.get_orderlines(), function(order_line){
            return order_line.product.id == product_id
                    && order_line.product.id != condition_product_id
                    && !order_line.get_condition_promotion_id()
                    && !order_line.get_promotion_id()
                    && !order_line.get_amount_promotion_id()
        })
        return apply_lines;
    },
//    /** Receipt **/
    get_total_discount: function() {
        var res = round_pr(this.orderlines.reduce((function(sum, orderLine) {
            var unit_price = orderLine.get_unit_price();
            if (orderLine.has_promotion()){
                var discount = orderLine.compute_promo_unit_price(unit_price);
            } else {
                var discount = (orderLine.get_unit_price() * (1 - orderLine.get_discount()/100) * orderLine.get_quantity());
            }
            return sum + (orderLine.get_unit_price()  - discount);
        }), 0), this.pos.currency.rounding);
        return res;
    },
});

});
