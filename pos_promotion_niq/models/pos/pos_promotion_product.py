# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPromotionProduct(models.Model):

    _name = 'pos.promotion.product'

    @api.onchange('promotion_code')
    def default_qty(self):
        for record in self:
            print("promotion_code:", record.promotion_id.promotion_code)
            if not record.promotion_id.promotion_code:
                raise UserError("Please input the promotion information at the header first !.")
            if record.promotion_id.promotion_code.startswith('prod_bx'):
                record.condition_qty = 1
            if record.promotion_id.promotion_code.endswith('free'):
                record.free_qty = 1

    promotion_id = fields.Many2one(
        comodel_name="pos.promotion", string="Promotion")

    state = fields.Selection(
        related='promotion_id.state', string='State', store=True)
    promotion_code = fields.Char(related='promotion_id.promotion_code',
                                 string="Promotion Code",
                                 store=True)
    separator = fields.Char('Get', default="=>")
    condition_product_id = fields.Many2one(
        'product.product', 'Buy X',
        domain="[('available_in_pos', '=', True)]")
    condition_qty = fields.Float('Qty X')
    free_qty = fields.Float('Free Qty')
    product_id = fields.Many2one('product.product', 'Product',
                                 domain="[('available_in_pos', '=', True)]",
                                 )
    fixed_price = fields.Float('Fixed Price (0=Free)')
    disc_percentage = fields.Float('Disc. %')
    disc_amount = fields.Float('Disc. Amount')
