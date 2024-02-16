odoo.define('pos_promotion_niq.DB', function (require) {
"use strict";
    var PosDB = require('point_of_sale.DB');

    PosDB.include({
        init: function(options){
            this._super(options);
            this.combo_conditions_by_promo_id = {};
            this.products_by_promo_id = {};
            this.templates_by_promo_id = {};
            this.categories_by_promo_id = {};
            this.promotions_by_id = {};
            this.promotions = {};
        },
        set_combo_conditions_by_promo_id: function(conditions){
            var self = this;

            _.each(conditions, function(condition){
                var promo_id = condition.promotion_id[0];
                self.combo_conditions_by_promo_id[promo_id] = self.combo_conditions_by_promo_id[promo_id] || [];
                self.combo_conditions_by_promo_id[promo_id].push(condition);
            })
        },
        set_promotion_by_id: function(promotions){
            var self = this;
            _.each(promotions, function(promotion){

                // set map id for each promotion
                self.promotions_by_id[promotion.id] = promotion;

                // group by promotion_group
                /*
                {
                    'on_product': [{'promotion': '1'}, {'promotion': '2'}],
                    'on_amount':[{'promotion': 3},{ 'promotion': 4}]
                }
                */
                self.promotions[promotion.promotion_group] = self.promotions[promotion.promotion_group] || [];
                self.promotions[promotion.promotion_group].push(promotion);
            });
        },
        /**
        add promotion.product to db
        **/
        set_promo_products_by_promo_id: function(product_promotions){
            var self = this;
            _.each(product_promotions, function(prod_promotion){
                var promo_id = prod_promotion.promotion_id[0];
                self.products_by_promo_id[promo_id] = self.products_by_promo_id[promo_id] || [];
                self.products_by_promo_id[promo_id].push(prod_promotion);
            })
        },
        /**
        add promotion.template to db
        **/
        set_promo_templates_by_promo_id: function(template_promotions){
            var self = this;
            _.each(template_promotions, function(template_promotion){
                var promo_id = template_promotion.promotion_id[0];
                self.templates_by_promo_id[promo_id] = self.templates_by_promo_id[promo_id] || [];
                self.templates_by_promo_id[promo_id].push(template_promotion);
            })
        },
        /**
        add promotion.category to db
        **/
        set_promo_categories_by_promo_id: function(category_promotions){
            var self = this;
            _.each(category_promotions, function(category_promotion){
                var promo_id = category_promotion.promotion_id[0];
                self.categories_by_promo_id[promo_id] = self.templates_by_promo_id[promo_id] || [];
                self.categories_by_promo_id[promo_id].push(category_promotion);
            })
        },

        /**
        Get all pos.promotion.product row base on promotion_id
        */
        get_promo_product_by_promo_id: function(promo_id){
            var prod_promos = this.products_by_promo_id[promo_id] || [];
            return prod_promos;
        },
        /**
        Get all pos.promotion.template row base on promotion_id
        */
        get_promo_template_by_promo_id: function(promo_id){
            var tmpl_promos = this.templates_by_promo_id[promo_id] || [];
            return tmpl_promos;
        },
        /**
        Get all pos.promotion.category row base on promotion_id
        */
        get_promo_category_by_promo_id: function(promo_id){
            var categ_promos = this.categories_by_promo_id[promo_id] || [];
            return categ_promos;
        },
        /**
        Get all pos.promotion.condition.combo row base on promotion_id
        */
        get_promo_combo_condition_by_promo_id: function(promo_id){
            var conditions = this.combo_conditions_by_promo_id[promo_id] || [];
            return conditions;
        },
        get_promotions: function(){
            return this.promotions;
        }

    });
});