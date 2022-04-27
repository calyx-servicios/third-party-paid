odoo.define('pos_promotion_niq.init', function (require) {
"use strict";
    var models = require('point_of_sale.models');



    models.load_models([{
        model:  'pos.promotion.condition.combo',
        fields: [],
        loaded: function(self, promo_combo_conditions){
            self.db.set_combo_conditions_by_promo_id(promo_combo_conditions);
        }
    },{
        model:  'pos.promotion.product',
        fields: [],
        loaded: function(self, promo_products){
            self.db.set_promo_products_by_promo_id(promo_products);
        }
    },{
        model:  'pos.promotion.template',
        fields: [],
        loaded: function(self, promo_templates){
            self.db.set_promo_templates_by_promo_id(promo_templates);
        }
    },{
        model:  'pos.promotion.category',
        fields: [],
        loaded: function(self, promo_categories){
            self.db.set_promo_categories_by_promo_id(promo_categories);
        }
    },{
        model:  'pos.promotion',
        fields: [],
        domain: [['state', '=', 'active']],
        order: [{name:'priority'}],
        loaded: function(self, promotions){
            self.db.set_promotion_by_id(promotions);
        }
    }],{
        after: 'product.product'
    });
});