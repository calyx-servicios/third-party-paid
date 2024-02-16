# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class PosPromotionCategory(models.Model):

    _name = 'pos.promotion.category'

    promotion_id = fields.Many2one(
        comodel_name="pos.promotion", string="Promotion")
    promotion_code = fields.Char(related='promotion_id.promotion_code',
                                 string="Promotion Code",
                                 store=True)

    state = fields.Selection(
        related='promotion_id.state', string='State', store=True)
    category_id = fields.Many2one('product.category', 'Category',
                                  required=True)
    fixed_price = fields.Float('Fixed Price')
    disc_percentage = fields.Float('Disc. %')
    disc_amount = fields.Float('Disc. Amount')