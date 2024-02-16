# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class SaleShop(models.Model):
    _name = "sale.shop"
    _description = "Sales Shop"

    name = fields.Char(string='Shop Name', size=120, required=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    shop_id = fields.Many2one('sale.shop', string='Shop')

    @api.model
    def update_order_shop_id(self):
        for order in self.search([]):
            order.shop_id = self.env.ref('sale_shop.sale_shop_1').id
