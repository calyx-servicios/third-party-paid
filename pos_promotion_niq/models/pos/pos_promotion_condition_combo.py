# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class PosPromotionConditionCombo(models.Model):

    _name = 'pos.promotion.condition.combo'

    promotion_id = fields.Many2one(
        comodel_name="pos.promotion", string="Promotion")

    state = fields.Selection(
        related='promotion_id.state', string='State', store=True)
    condition_product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('available_in_pos', '=', True)]")
    condition_qty = fields.Float('Qty Condition', default="1")
